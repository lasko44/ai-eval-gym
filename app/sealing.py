"""Sealing: the hash chain over a cycle's claims, plus the git commit that
anchors it outside the database.

The whole project rests on a prediction being committed before the answer is
known, so two things have to hold.

1. The chain. Each claim's hash is sha256 over the previous claim's hash and
   that claim's own canonical fields, so editing a claim or reordering the
   claims changes every hash from that point on. The last claim's hash is the
   chain head, which is the one value that stands for the whole prediction.

2. The anchor. The head goes into seals/cycle-{id}.txt and that file is
   committed to git BEFORE the database transaction commits. Git supplies
   what the database cannot: an append-only history with its own timestamps,
   written by a tool outside this app. If any git step fails, the database
   rolls back and no sealed_hash is persisted, so a seal can never exist in
   the database without its commit. The seal commit's own SHA is then read
   back with rev-parse and stored on the cycle, so the teardown can name the
   exact commit rather than pointing vaguely at "the git history": a named
   commit is something a stranger can check, which is the entire reason for
   involving git at all. Sealing is refused on a detached HEAD, because a
   commit made there belongs to no branch and is lost at the next checkout.

Everything here resolves git and the seals directory from the process working
directory, not from a hardcoded project path, so the caller controls which
repository a seal lands in.
"""

import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Claim, Cycle

# Seeds the chain so the first claim's hash is not just a hash of its own
# fields, and so an empty chain and a one-claim chain cannot collide.
GENESIS = "genesis"

SEALS_DIRNAME = "seals"

# Every git step gets a wall-clock limit. Without one, a repository
# configured with commit.gpgsign=true (or a credential helper that wants a
# terminal) leaves git waiting on a prompt nobody can answer, and the seal
# route blocks forever while holding the open database transaction and its
# row locks on the flushed claims. A seal that cannot finish has to fail,
# not hang.
GIT_TIMEOUT_SECONDS = 30


class SealError(Exception):
    """A cycle could not be sealed.

    Raised instead of sealing when the cycle is in the wrong stage, has no
    claims, or when git cannot hold the seal. In every case the database is
    left exactly as it was.
    """


def _canonical_bytes(claim: Claim) -> bytes:
    """The one canonical serialization of a claim's meaning.

    Every field a user could edit to change what the prediction says is
    included. Each field is written as name:bytelength:value so no two
    different claims can produce the same bytes (a length prefix means a
    value containing a colon, a newline or another field's name cannot be
    mistaken for a field boundary).

    Floats go through repr(), which in CPython is the shortest string that
    round-trips back to the same float, so the bytes are stable across runs.
    """
    fields = (
        ("cycle_id", str(claim.cycle_id)),
        ("text", claim.text),
        ("metric", claim.metric),
        ("comparator", claim.comparator),
        ("threshold", repr(float(claim.threshold))),
        ("probability", repr(float(claim.probability))),
    )
    out = bytearray()
    for name, value in fields:
        value_bytes = value.encode("utf-8")
        out += f"{name}:{len(value_bytes)}:".encode("ascii")
        out += value_bytes
        out += b"\n"
    return bytes(out)


def _claim_hash(previous_hash: str, claim: Claim) -> str:
    digest = hashlib.sha256()
    digest.update(f"prev:{len(previous_hash)}:{previous_hash}\n".encode("ascii"))
    digest.update(_canonical_bytes(claim))
    return digest.hexdigest()


def chain_hashes(claims: list[Claim]) -> list[str]:
    """Hash every claim onto the one before it, in the order given.

    Returns one hash per claim. The last is the chain head.
    """
    hashes: list[str] = []
    previous = GENESIS
    for claim in claims:
        previous = _claim_hash(previous, claim)
        hashes.append(previous)
    return hashes


def _git(*args: str) -> str:
    """Run git in the current working directory, raising SealError if it fails."""
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise SealError(
            f"git {' '.join(args)} did not finish within "
            f"{GIT_TIMEOUT_SECONDS} seconds and was killed. A git step that "
            "hangs is almost always waiting on something interactive (a GPG "
            "passphrase for commit.gpgsign, or a credential helper wanting a "
            "terminal), and this one cannot be waited out: it runs inside the "
            "seal's open database transaction."
        ) from exc
    except OSError as exc:
        raise SealError(f"Could not run git: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise SealError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _require_git_repository() -> None:
    """Refuse to seal unless git can actually hold the seal commit.

    Two checks, not one. `git rev-parse --git-dir` only proves there is a
    repository here; it succeeds just as happily on a detached HEAD, and a
    detached HEAD is the worse case of the two. There, every step of
    seal_cycle reports success (git commit returns 0, the read-back finds
    the head, the database commits), and then the very next `git checkout`
    makes the seal file vanish from the tree and leaves the seal commit
    unreachable, to be destroyed by the next `git gc`. The teardown page
    would still be telling a reader to go and check a commit that no longer
    exists. HEAD gets detached by ordinary work: `git checkout <sha>` to
    read an old version, an interrupted rebase, a `git bisect`.

    `git symbolic-ref -q HEAD` is the detachment test: it prints the branch
    ref and exits 0 when HEAD is on a branch, and exits non-zero (quietly,
    because of -q) when HEAD is detached. _git turns that non-zero exit into
    a SealError, which is what the except below catches.
    """
    try:
        _git("rev-parse", "--git-dir")
    except SealError as exc:
        raise SealError(
            f"No usable git repository in {Path.cwd()}: a seal is only real "
            f"once git holds it. ({exc})"
        ) from exc

    try:
        _git("symbolic-ref", "-q", "HEAD")
    except SealError as exc:
        raise SealError(
            "HEAD is detached, so a seal commit would land on no branch and "
            "be lost at the next checkout. Check out a branch before sealing."
        ) from exc


def _require_clean_seal_file(seal_path: Path) -> None:
    """Refuse to seal over a seal file git does not already agree with.

    Dirty means git status reports anything at all for that path: an
    untracked file, a modified tracked file, or a staged change. A seal file
    sitting there uncommitted means either a previous seal failed halfway or
    someone wrote one by hand, and in both cases overwriting it would destroy
    the evidence of what happened. The tree has to be sorted out by a human
    first.
    """
    status = _git(
        "status", "--porcelain", "--untracked-files=all", "--", str(seal_path)
    ).strip()
    if status:
        raise SealError(
            f"{seal_path} has uncommitted changes in git ({status}). Commit or "
            "remove it before sealing: a seal file git does not hold is not a seal."
        )


def _require_committed_head(seal_path: Path, head: str) -> None:
    """Read the seal file back out of HEAD and check it holds this head.

    `git commit -- <pathspec>` commits the file's content as of commit time
    rather than whatever `git add` staged, so asking git what landed is the
    only way to know. This closes the window between writing the file and
    committing it: if anything rewrote the seal file in that window, the head
    in history would not be the head seal_cycle is about to return, and a
    seal whose committed head does not match the chain is worth nothing.

    The path is passed as HEAD:./<path> so git resolves it relative to the
    working directory, the same way the file was written.
    """
    committed = _git("show", f"HEAD:./{seal_path}")
    if head not in committed:
        raise SealError(
            f"The seal commit for {seal_path} does not contain the chain head "
            f"{head}. Something rewrote the seal file between writing it and "
            "committing it, so this seal cannot be trusted."
        )


def _discard_written_seal_file(seal_path: Path) -> None:
    """Undo seal_cycle's own write of a seal file git never took.

    Called only when seal_cycle created the file itself and no commit landed.
    Without this, one transient git failure (a pre-commit hook, a stale
    index.lock, a full disk) would leave an uncommitted seal file that
    _require_clean_seal_file then refuses for good, so that cycle could never
    be sealed again without someone cleaning the tree by hand. A seal file
    that was already there is left alone by the caller, which is what
    preserves the evidence of an earlier half-finished seal.

    Both steps are best effort on purpose: a failure here must not replace
    the real SealError the caller is about to see, and if cleanup does fail
    the tree is left in exactly the state not cleaning up at all would have
    left it in.
    """
    try:
        _git("reset", "-q", "--", str(seal_path))
    except SealError:
        pass
    try:
        seal_path.unlink(missing_ok=True)
    except OSError:
        pass


def _seal_file_body(
    cycle_id: int, sealed_at: datetime, claim_count: int, head: str
) -> str:
    return (
        f"cycle: {cycle_id}\n"
        f"sealed_at: {sealed_at.isoformat()}\n"
        f"claims: {claim_count}\n"
        f"chain_head: {head}\n"
    )


def seal_cycle(session: Session, cycle_id: int) -> str:
    """Seal a cycle's claims and return the chain head hash.

    Order matters and is the point of this function: validate, then write the
    seal file, then git add, then git commit, then read back what the commit
    actually holds, then record that commit's SHA on the cycle, and only
    then commit the database transaction. Any failure before that last
    commit rolls the session back, so no claim is ever left holding a
    sealed_hash that git cannot account for. A failure
    that leaves no commit behind also removes the seal file this call wrote,
    so one bad git run does not leave the cycle unsealable for good.
    """
    cycle = session.get(Cycle, cycle_id)
    if cycle is None:
        raise SealError(f"Cycle {cycle_id} does not exist.")
    if cycle.stage != "open":
        raise SealError(
            f"Cycle {cycle_id} is already {cycle.stage}. A seal is made once "
            "and never redone."
        )

    claims = (
        session.query(Claim)
        .filter(Claim.cycle_id == cycle_id)
        .order_by(Claim.id)
        .all()
    )
    if not claims:
        raise SealError(
            f"Cycle {cycle_id} has no claims. There is nothing to seal, and an "
            "empty prediction cannot be scored."
        )

    # Check git before touching the session, so the no-repository case never
    # even reaches the database.
    _require_git_repository()
    seal_path = Path(SEALS_DIRNAME) / f"cycle-{cycle_id}.txt"
    _require_clean_seal_file(seal_path)

    hashes = chain_hashes(claims)
    head = hashes[-1]
    sealed_at = datetime.now(UTC)
    for claim, claim_hash in zip(claims, hashes, strict=True):
        claim.sealed_hash = claim_hash
    cycle.stage = "sealed"
    cycle.sealed_at = sealed_at
    # Flush, do not commit: the rows are written inside the open transaction
    # so the database gets its chance to reject them, while the transaction
    # stays rollback-able until git has succeeded.
    session.flush()

    # Whether this call is the one that created the seal file decides what
    # may be cleaned up if git fails: seal_cycle undoes its own write and
    # never touches a file that was already there.
    seal_file_existed = seal_path.exists()
    committed = False

    try:
        seal_path.parent.mkdir(parents=True, exist_ok=True)
        seal_path.write_text(
            _seal_file_body(cycle_id, sealed_at, len(claims), head)
        )
        _git("add", "--", str(seal_path))
        _git(
            "commit",
            "-m",
            f"seal: cycle {cycle_id} claim chain head {head[:12]}",
            "--",
            str(seal_path),
        )
        committed = True
        _require_committed_head(seal_path, head)
        # Only knowable now: the commit has to exist before it has a SHA.
        # Recorded inside the same try, before the database transaction
        # commits, so a failure here still rolls the seal back and the
        # invariant "never a sealed_hash without its commit" is unchanged.
        cycle.sealed_commit = _git("rev-parse", "HEAD").strip()
    except SealError:
        session.rollback()
        if not seal_file_existed and not committed:
            # No commit landed, so nothing in history refers to this file and
            # removing it leaves the tree as it was found. Once a commit has
            # landed the file belongs to git, and deleting it would only make
            # the tree dirty and refuse the next attempt.
            _discard_written_seal_file(seal_path)
        raise
    except OSError as exc:
        session.rollback()
        if not seal_file_existed and not committed:
            _discard_written_seal_file(seal_path)
        raise SealError(f"Could not write the seal file {seal_path}: {exc}") from exc

    session.commit()
    return head

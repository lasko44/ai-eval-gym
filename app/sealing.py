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
   the database without its commit.

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
            ["git", *args], capture_output=True, text=True, check=False
        )
    except OSError as exc:
        raise SealError(f"Could not run git: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no output"
        raise SealError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _require_git_repository() -> None:
    try:
        _git("rev-parse", "--git-dir")
    except SealError as exc:
        raise SealError(
            f"No usable git repository in {Path.cwd()}: a seal is only real "
            f"once git holds it. ({exc})"
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
    seal file, then git add, then git commit, and only then commit the
    database transaction. Any failure before that last commit rolls the
    session back, so no claim is ever left holding a sealed_hash that git
    cannot account for.
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
    except SealError:
        # The seal file and any staged change are deliberately left where
        # they are. Git failing here means something needs a human's eyes,
        # and the next seal attempt refuses a dirty seal file on purpose.
        session.rollback()
        raise
    except OSError as exc:
        session.rollback()
        raise SealError(f"Could not write the seal file {seal_path}: {exc}") from exc

    session.commit()
    return head

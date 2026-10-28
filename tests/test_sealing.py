"""Claims and sealing.

Every test here that reaches a successful seal runs inside a throwaway git
repository created under tmp_path by the git_repo fixture. seal_cycle runs
git add and git commit against the process working directory, so a test that
sealed from the project tree would append a commit to the branch this project
is being built on.
"""

from pathlib import Path
import pytest

from app.models import Claim, Cycle
from app.sealing import (
    SealError,
    _require_committed_head,
    chain_hashes,
    seal_cycle,
)
from conftest import VALID_CLAIM, _git


def test_claim_requires_a_falsification_test(client, cycle):
    r = client.post(f"/cycles/{cycle.id}/claims", data={
        "text": "retrieval is bad on multi-hop", "metric": "", "comparator": "lt",
        "threshold": "", "probability": "0.7"})
    assert r.status_code == 422


@pytest.mark.parametrize("probability", ["0.0", "0.7", "1.0"])
def test_a_claim_with_a_falsification_test_is_accepted(
    client, session, cycle, probability
):
    r = client.post(
        f"/cycles/{cycle.id}/claims", data={**VALID_CLAIM, "probability": probability}
    )
    assert r.status_code == 303

    claim = session.query(Claim).one()
    assert claim.cycle_id == cycle.id
    assert claim.metric == "recall_at_5"
    assert claim.comparator == "lt"
    assert claim.threshold == 0.5
    assert claim.probability == float(probability)
    assert claim.sealed_hash is None


def test_the_predict_page_shows_the_claim_form_while_open(client, cycle):
    r = client.get(f"/cycles/{cycle.id}/predict")
    assert r.status_code == 200
    assert f'action="/cycles/{cycle.id}/claims"' in r.text
    assert f'action="/cycles/{cycle.id}/seal"' in r.text
    # The form collects the user's own words and suggests none of them.
    assert 'name="text"' in r.text
    assert "<textarea id=\"text\" name=\"text\" required></textarea>" in r.text


def test_the_predict_page_shows_the_hashes_and_no_form_once_sealed(
    client, session, sealed_cycle
):
    r = client.get(f"/cycles/{sealed_cycle.id}/predict")
    assert r.status_code == 200
    for claim in session.query(Claim).order_by(Claim.id).all():
        assert claim.sealed_hash in r.text
    assert f'action="/cycles/{sealed_cycle.id}/claims"' not in r.text
    assert f'action="/cycles/{sealed_cycle.id}/seal"' not in r.text


def test_sealing_chains_each_claim_hash(session, cycle_with_two_claims, git_repo):
    head = seal_cycle(session, cycle_with_two_claims.id)

    claims = session.query(Claim).order_by(Claim.id).all()
    assert all(c.sealed_hash for c in claims)
    assert claims[1].sealed_hash != claims[0].sealed_hash
    assert head == claims[-1].sealed_hash
    assert session.get(Cycle, cycle_with_two_claims.id).stage == "sealed"

    # A seal is only real once git holds it: the head hash must be in the
    # seal file as committed to HEAD, and the tree must be left clean.
    seal_in_head = _git(
        git_repo, "show", f"HEAD:seals/cycle-{cycle_with_two_claims.id}.txt"
    )
    assert head in seal_in_head
    assert _git(git_repo, "status", "--porcelain") == ""


def test_sealing_over_http_commits_the_chain(
    client, session, cycle_with_two_claims, git_repo
):
    cycle_id = cycle_with_two_claims.id

    r = client.post(f"/cycles/{cycle_id}/seal")
    assert r.status_code == 303
    assert r.headers["location"] == f"/cycles/{cycle_id}/predict"

    # The route owns its own session, so drop what this one already loaded.
    session.expire_all()
    claims = session.query(Claim).order_by(Claim.id).all()
    assert all(c.sealed_hash for c in claims)
    assert session.get(Cycle, cycle_id).stage == "sealed"
    committed = _git(git_repo, "show", f"HEAD:seals/cycle-{cycle_id}.txt")
    assert claims[-1].sealed_hash in committed


def test_sealing_over_http_refuses_a_cycle_with_no_claims(
    client, session, cycle, git_repo
):
    r = client.post(f"/cycles/{cycle.id}/seal")
    assert r.status_code == 409

    session.expire_all()
    assert session.get(Cycle, cycle.id).stage == "open"
    assert _git(git_repo, "log", "--oneline").count("\n") == 1


def test_claims_are_immutable_once_sealed(client, sealed_cycle):
    r = client.post(f"/cycles/{sealed_cycle.id}/claims", data=VALID_CLAIM)
    assert r.status_code == 409


def test_seal_fails_loudly_and_writes_nothing_without_git(
    session, cycle_with_two_claims, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SealError):
        seal_cycle(session, cycle_with_two_claims.id)
    assert session.query(Claim).filter(Claim.sealed_hash.isnot(None)).count() == 0


def test_seal_fails_loudly_when_the_seal_file_is_dirty(
    session, cycle_with_two_claims, git_repo
):
    cycle_id = cycle_with_two_claims.id
    seal_path = git_repo / "seals" / f"cycle-{cycle_id}.txt"
    seal_path.parent.mkdir()
    seal_path.write_text("a hash nobody committed\n")

    with pytest.raises(SealError):
        seal_cycle(session, cycle_id)
    assert session.query(Claim).filter(Claim.sealed_hash.isnot(None)).count() == 0
    assert seal_path.read_text() == "a hash nobody committed\n"

    # Same refusal when the seal file is tracked but has uncommitted edits.
    _git(git_repo, "add", "--", f"seals/cycle-{cycle_id}.txt")
    _git(git_repo, "commit", "-q", "-m", "a seal file from somewhere else")
    seal_path.write_text("edited after the commit\n")

    with pytest.raises(SealError):
        seal_cycle(session, cycle_id)
    assert session.query(Claim).filter(Claim.sealed_hash.isnot(None)).count() == 0


def test_a_failed_git_commit_rolls_the_seal_back(
    session, cycle_with_two_claims, git_repo_that_refuses_commits
):
    cycle_id = cycle_with_two_claims.id

    with pytest.raises(SealError):
        seal_cycle(session, cycle_id)

    assert session.query(Claim).filter(Claim.sealed_hash.isnot(None)).count() == 0
    cycle = session.get(Cycle, cycle_id)
    assert cycle.stage == "open"
    assert cycle.sealed_at is None
    # Only the fixture's own initial commit is in the repository.
    repo = git_repo_that_refuses_commits
    assert _git(repo, "log", "--oneline").count("\n") == 1

    # The failure must not wedge the cycle. No commit landed, so the seal
    # file this call wrote is gone and the tree is as it was found, which
    # means sealing works again as soon as the hook does not refuse it.
    assert not (repo / "seals" / f"cycle-{cycle_id}.txt").exists()
    assert _git(repo, "status", "--porcelain", "--untracked-files=all") == ""

    (repo / ".git" / "hooks" / "pre-commit").unlink()
    head = seal_cycle(session, cycle_id)
    claims = session.query(Claim).order_by(Claim.id).all()
    assert head == claims[-1].sealed_hash
    assert head in _git(repo, "show", f"HEAD:seals/cycle-{cycle_id}.txt")


def test_a_failed_seal_leaves_a_pre_existing_seal_file_alone(
    session, cycle_with_two_claims, git_repo
):
    """Cleanup undoes this call's own write, never a file already there.

    A committed seal file for a cycle that is somehow still open is evidence
    of something odd, so a failed seal must not quietly delete it.
    """
    cycle_id = cycle_with_two_claims.id
    seal_path = git_repo / "seals" / f"cycle-{cycle_id}.txt"
    seal_path.parent.mkdir()
    seal_path.write_text("an older seal, put here by hand\n")
    _git(git_repo, "add", "--", f"seals/cycle-{cycle_id}.txt")
    _git(git_repo, "commit", "-q", "-m", "an older seal file")

    hook = git_repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)

    with pytest.raises(SealError):
        seal_cycle(session, cycle_id)

    assert seal_path.exists()
    assert session.query(Claim).filter(Claim.sealed_hash.isnot(None)).count() == 0


def test_a_seal_commit_that_does_not_hold_the_head_is_refused(git_repo):
    """The read-back guard, checked against real git.

    _require_committed_head is reached in production through seal_cycle, but
    the window it closes (something rewriting the seal file between the write
    and the commit) cannot be opened from a test without faking git. This
    drives the guard itself against a real commit whose seal file holds a
    different head, which is the state it exists to catch.
    """
    seal_path = Path("seals") / "cycle-9.txt"
    (git_repo / "seals").mkdir()
    (git_repo / seal_path).write_text("chain_head: the-head-that-landed\n")
    _git(git_repo, "add", "--", str(seal_path))
    _git(git_repo, "commit", "-q", "-m", "a seal holding another head")

    _require_committed_head(seal_path, "the-head-that-landed")

    with pytest.raises(SealError):
        _require_committed_head(seal_path, "the-head-being-returned")


def test_the_chain_detects_editing_and_reordering(session, cycle_with_two_claims):
    claims = session.query(Claim).order_by(Claim.id).all()
    original = chain_hashes(claims)

    assert chain_hashes(list(reversed(claims))) != original

    claims[0].threshold = 0.6
    assert chain_hashes(claims)[0] != original[0]


def test_seal_refuses_a_detached_head_and_writes_nothing(
    session, cycle_with_two_claims, git_repo
):
    """A detached HEAD is the one git state that fakes a successful seal.

    `git rev-parse --git-dir` succeeds here, so the pre-fix code sealed
    normally: git commit returned 0, every claim got its sealed_hash, the
    read-back guard passed, and the cycle moved to sealed. The commit
    belonged to no branch, so the next checkout made seals/cycle-N.txt
    vanish from the tree and left the commit unreachable, for git gc to
    collect, while the teardown page still told readers to go and check it.
    That is worse than the no-git case, which at least fails loudly.

    Same shape as test_seal_fails_loudly_and_writes_nothing_without_git:
    SealError, and not one claim left holding a sealed_hash.
    """
    cycle_id = cycle_with_two_claims.id
    _git(git_repo, "checkout", "-q", "--detach", "HEAD")
    # Prove the precondition, so this test cannot pass just because the
    # checkout above quietly did nothing: on a branch, --abbrev-ref HEAD
    # prints the branch name, and it prints "HEAD" only when detached.
    assert _git(git_repo, "rev-parse", "--abbrev-ref", "HEAD").strip() == "HEAD"

    with pytest.raises(SealError) as raised:
        seal_cycle(session, cycle_id)
    assert "detached" in str(raised.value)

    assert session.query(Claim).filter(Claim.sealed_hash.isnot(None)).count() == 0
    cycle = session.get(Cycle, cycle_id)
    assert cycle.stage == "open"
    assert cycle.sealed_at is None
    assert cycle.sealed_commit is None

    # The refusal happens before git or the filesystem is touched, so the
    # repository is exactly as the fixture left it.
    assert _git(git_repo, "log", "--oneline").count("\n") == 1
    assert not (git_repo / "seals" / f"cycle-{cycle_id}.txt").exists()
    assert _git(git_repo, "status", "--porcelain", "--untracked-files=all") == ""


def test_a_successful_seal_records_the_commit_that_holds_it(
    session, cycle_with_two_claims, git_repo
):
    """The chain head alone is not checkable; the head plus a SHA is.

    "Committed somewhere in this project's git history" cannot be verified
    by a stranger. "Chain head X, committed in SHA Y" can, which is the
    whole reason this app involves git. This also makes a detached-HEAD
    style failure self-detecting in future: the recorded SHA is either
    reachable or it is not.
    """
    cycle_id = cycle_with_two_claims.id
    head = seal_cycle(session, cycle_id)

    cycle = session.get(Cycle, cycle_id)
    assert cycle.sealed_commit == _git(git_repo, "rev-parse", "HEAD").strip()
    # The recorded SHA is the commit that actually holds this chain head.
    assert head in _git(
        git_repo, "show", f"{cycle.sealed_commit}:seals/cycle-{cycle_id}.txt"
    )


def test_a_failed_seal_records_no_commit(
    session, cycle_with_two_claims, git_repo_that_refuses_commits
):
    """sealed_commit follows sealed_hash: both, or neither."""
    cycle_id = cycle_with_two_claims.id
    with pytest.raises(SealError):
        seal_cycle(session, cycle_id)
    assert session.get(Cycle, cycle_id).sealed_commit is None


def test_a_git_step_that_hangs_fails_the_seal_instead_of_blocking(
    session, cycle_with_two_claims, git_repo, monkeypatch
):
    """A hanging git step must not hold the seal route open forever.

    With commit.gpgsign=true and a passphrase prompt, or a credential helper
    that wants a tty, git waits for input nobody can give. The seal route
    would wait with it, holding the open database transaction and its row
    locks on the already-flushed claims.

    Driven against real git rather than a stubbed subprocess: a pre-commit
    hook that sleeps is exactly the shape of a commit that will not return.
    The timeout is turned down to one second for the test, so this costs
    about a second rather than thirty.
    """
    cycle_id = cycle_with_two_claims.id
    hook = git_repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nsleep 30\n")
    hook.chmod(0o755)
    monkeypatch.setattr("app.sealing.GIT_TIMEOUT_SECONDS", 1)

    with pytest.raises(SealError) as raised:
        seal_cycle(session, cycle_id)
    assert "did not finish within 1 seconds" in str(raised.value)

    # The usual invariant: no commit landed, so nothing is sealed.
    assert session.query(Claim).filter(Claim.sealed_hash.isnot(None)).count() == 0
    cycle = session.get(Cycle, cycle_id)
    assert cycle.stage == "open"
    assert cycle.sealed_commit is None
    assert _git(git_repo, "log", "--oneline").count("\n") == 1

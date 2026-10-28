"""Claims and sealing.

Every test here that reaches a successful seal runs inside a throwaway git
repository created under tmp_path by the git_repo fixture. seal_cycle runs
git add and git commit against the process working directory, so a test that
sealed from the project tree would append a commit to the branch this project
is being built on.
"""

import pytest

from app.models import Claim, Cycle
from app.sealing import SealError, chain_hashes, seal_cycle
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
    log = _git(git_repo_that_refuses_commits, "log", "--oneline")
    assert log.count("\n") == 1


def test_the_chain_detects_editing_and_reordering(session, cycle_with_two_claims):
    claims = session.query(Claim).order_by(Claim.id).all()
    original = chain_hashes(claims)

    assert chain_hashes(list(reversed(claims))) != original

    claims[0].threshold = 0.6
    assert chain_hashes(claims)[0] != original[0]

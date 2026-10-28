import pytest

from app.models import Claim
from app.scoring import resolve_claim, score_cycle


def _claim(**overrides):
    """A claim with no database row behind it, for resolve_claim's pure path.

    resolve_claim reads only metric, comparator and threshold, so a detached
    Claim is enough and keeps these tests free of fixtures.
    """
    fields = {
        "text": "multi-hop recall is poor",
        "metric": "recall_at_5",
        "comparator": "lt",
        "threshold": 0.5,
        "probability": 0.7,
    }
    fields.update(overrides)
    return Claim(**fields)


def test_a_claim_whose_metric_was_never_measured_is_unresolved():
    claim = Claim(metric="recall_at_5", comparator="lt", threshold=0.5, probability=0.7)
    assert resolve_claim(claim, {"ndcg_at_10": 0.8}) == "unresolved"


def test_a_claim_resolves_correct_when_the_measured_value_is_below_an_lt_threshold():
    # "recall_at_5 lt 0.5" predicts recall will come in BELOW 0.5, so 0.2
    # confirms it. If the comparator were applied the other way round
    # (threshold < measured) this would read "wrong" and every verdict in
    # the app would be inverted.
    assert resolve_claim(_claim(), {"recall_at_5": 0.2}) == "correct"


def test_a_claim_resolves_wrong_when_the_measured_value_is_above_an_lt_threshold():
    assert resolve_claim(_claim(), {"recall_at_5": 0.9}) == "wrong"


def test_a_gt_claim_resolves_correct_when_the_measured_value_is_above_it():
    claim = _claim(metric="flip_rate", comparator="gt", threshold=0.2)
    assert resolve_claim(claim, {"flip_rate": 0.5}) == "correct"
    assert resolve_claim(claim, {"flip_rate": 0.1}) == "wrong"


def test_the_inclusive_comparators_accept_a_value_equal_to_the_threshold():
    assert resolve_claim(_claim(comparator="lte"), {"recall_at_5": 0.5}) == "correct"
    assert resolve_claim(_claim(comparator="lt"), {"recall_at_5": 0.5}) == "wrong"
    gte = _claim(metric="flip_rate", comparator="gte", threshold=0.2)
    assert resolve_claim(gte, {"flip_rate": 0.2}) == "correct"
    assert resolve_claim(_claim(metric="flip_rate", comparator="gt", threshold=0.2),
                         {"flip_rate": 0.2}) == "wrong"


def test_an_unresolved_claim_never_counts_as_correct(
    session, sealed_cycle_with_unmeasured_claim
):
    score = score_cycle(session, sealed_cycle_with_unmeasured_claim.id)
    assert score.resolved == 0
    assert score.unresolved == 1
    assert score.brier is None


def test_coverage_is_the_share_of_claims_that_resolved(session, cycle_one_of_two_measured):
    assert score_cycle(session, cycle_one_of_two_measured.id).coverage == 0.5


def test_a_cycle_with_no_claims_has_zero_coverage_rather_than_a_zero_denominator(
    session, cycle
):
    score = score_cycle(session, cycle.id)
    assert score.coverage == 0.0
    assert score.resolved == 0
    assert score.unresolved == 0
    assert score.brier is None


def test_a_certain_claim_that_was_wrong_scores_the_maximum_penalty(
    session, cycle_certain_and_wrong
):
    assert score_cycle(session, cycle_certain_and_wrong.id).brier == 1.0


def test_a_certain_denial_that_turned_out_true_also_scores_the_maximum_penalty(
    session, cycle_certain_denial_that_resolved_correct
):
    # probability 0.0 on a claim that resolved correct is (0.0 - 1) ** 2 = 1.0,
    # the same maximum penalty as probability 1.0 on a claim that resolved
    # wrong. Pairing the outcome the wrong way round would score this 0.0 and
    # report a confidently wrong user as perfectly calibrated.
    score = score_cycle(session, cycle_certain_denial_that_resolved_correct.id)
    assert score.resolved == 1
    assert score.brier == 1.0


def test_a_well_stated_claim_that_came_true_scores_its_stated_confidence(
    session, cycle_one_of_two_measured
):
    # recall_at_5 was predicted below 0.5 at probability 0.7 and measured
    # 0.2, so the claim resolved correct and contributes (0.7 - 1) ** 2.
    # Pairing a correct claim with False instead would give (0.7 - 0) ** 2 =
    # 0.49, which is the inverted-Brier bug.
    score = score_cycle(session, cycle_one_of_two_measured.id)
    assert score.brier == pytest.approx((0.7 - 1.0) ** 2)


def test_the_latest_run_wins_when_two_runs_report_the_same_metric(
    client, session, sealed_cycle
):
    client.post(
        f"/cycles/{sealed_cycle.id}/runs",
        json={
            "notes": "before the harness was fixed",
            "measurements": {"recall_at_5": 0.9},
        },
    )
    client.post(
        f"/cycles/{sealed_cycle.id}/runs",
        json={
            "notes": "after the harness was fixed",
            "measurements": {"recall_at_5": 0.2},
        },
    )
    score = score_cycle(session, sealed_cycle.id)
    # 0.9 would resolve the lt 0.5 claim wrong, 0.2 resolves it correct. The
    # later run is the one that counts, so the Brier score is (0.7 - 1) ** 2
    # and not (0.7 - 0) ** 2.
    assert score.resolved == 1
    assert score.brier == pytest.approx((0.7 - 1.0) ** 2)


def test_scoring_a_cycle_that_does_not_exist_raises(session):
    with pytest.raises(ValueError):
        score_cycle(session, 999999)


def test_scoring_moves_the_cycle_to_scored(client, session, cycle_one_of_two_measured):
    r = client.post(f"/cycles/{cycle_one_of_two_measured.id}/score")
    assert r.status_code == 200
    session.refresh(cycle_one_of_two_measured)
    assert cycle_one_of_two_measured.stage == "scored"


def test_the_score_page_renders_the_computed_numbers(client, cycle_one_of_two_measured):
    r = client.post(f"/cycles/{cycle_one_of_two_measured.id}/score")
    assert r.status_code == 200
    assert "0.090" in r.text  # the Brier score over the one resolved claim
    assert "0.500" in r.text  # coverage: one of the two claims resolved


def test_scoring_an_unsealed_cycle_is_refused(client, cycle):
    r = client.post(f"/cycles/{cycle.id}/score")
    assert r.status_code == 409


def test_scoring_a_sealed_but_unmeasured_cycle_is_refused(client, sealed_cycle):
    # Scoring here would record two unresolved claims as a finding, when the
    # truth is that the harness has not run yet.
    r = client.post(f"/cycles/{sealed_cycle.id}/score")
    assert r.status_code == 409


def test_a_scored_cycle_can_be_scored_again(client, session, scored_cycle):
    r = client.post(f"/cycles/{scored_cycle.id}/score")
    assert r.status_code == 200
    session.refresh(scored_cycle)
    assert scored_cycle.stage == "scored"


def test_scoring_a_cycle_that_does_not_exist_404s(client):
    r = client.post("/cycles/999999/score")
    assert r.status_code == 404


def test_the_scored_cycle_fixture_carries_a_real_seal(scored_cycle):
    # The teardown page built in the next task reads the chain head from the
    # last claim, so the fixture it depends on has to be genuinely sealed.
    assert scored_cycle.stage == "scored"
    assert scored_cycle.claims[-1].sealed_hash


def test_the_score_page_says_so_when_nothing_resolved(
    client, sealed_cycle_with_unmeasured_claim
):
    r = client.post(f"/cycles/{sealed_cycle_with_unmeasured_claim.id}/score")
    assert r.status_code == 200
    assert "none (no claim resolved)" in r.text

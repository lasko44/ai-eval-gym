import pytest

from app.models import Cycle, HarnessRun, Measurement


def test_posting_a_run_stores_each_measurement(client, sealed_cycle, session):
    r = client.post(f"/cycles/{sealed_cycle.id}/runs",
                    json={"notes": "first run", "measurements": {"recall_at_5": 0.42}})
    assert r.status_code == 201
    assert session.query(Measurement).one().value == 0.42


def test_a_run_moves_the_cycle_to_measured(client, sealed_cycle, session):
    client.post(f"/cycles/{sealed_cycle.id}/runs", json={"notes": "", "measurements": {"recall_at_5": 0.42}})
    session.refresh(sealed_cycle)
    assert sealed_cycle.stage == "measured"


def test_a_run_is_refused_before_sealing(client, cycle):
    r = client.post(f"/cycles/{cycle.id}/runs", json={"notes": "", "measurements": {"recall_at_5": 0.9}})
    assert r.status_code == 409


def test_posting_a_run_against_a_nonexistent_cycle_404s(client):
    r = client.post("/cycles/999999/runs",
                     json={"notes": "", "measurements": {"recall_at_5": 0.9}})
    assert r.status_code == 404


def test_getting_runs_for_a_nonexistent_cycle_404s(client):
    r = client.get("/cycles/999999/runs")
    assert r.status_code == 404


def test_the_runs_page_renders_a_runs_notes(client, sealed_cycle):
    client.post(f"/cycles/{sealed_cycle.id}/runs",
                json={"notes": "first run", "measurements": {"recall_at_5": 0.42}})
    r = client.get(f"/cycles/{sealed_cycle.id}/runs")
    assert r.status_code == 200
    assert "first run" in r.text


def test_a_second_run_on_a_measured_cycle_is_accepted_and_stays_measured(
    client, sealed_cycle, session
):
    client.post(f"/cycles/{sealed_cycle.id}/runs",
                json={"notes": "", "measurements": {"recall_at_5": 0.42}})
    r = client.post(f"/cycles/{sealed_cycle.id}/runs",
                     json={"notes": "", "measurements": {"recall_at_5": 0.5}})
    assert r.status_code == 201
    session.refresh(sealed_cycle)
    assert sealed_cycle.stage == "measured"
    assert session.query(Measurement).count() == 2


def test_a_run_is_refused_once_scored(client, sealed_cycle, session):
    # Scoring is a later task and has no route of its own yet, so there is no
    # way to reach the scored stage through the app. The scored stage is set
    # directly on the model here, deliberately, to simulate the state a later
    # task will actually produce.
    sealed_cycle.stage = "scored"
    session.commit()

    r = client.post(f"/cycles/{sealed_cycle.id}/runs",
                     json={"notes": "", "measurements": {"recall_at_5": 0.9}})
    assert r.status_code == 409
    assert session.query(Measurement).count() == 0


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_a_non_finite_measurement_is_refused(client, session, sealed_cycle, token):
    """NaN and Infinity are accepted all the way to a false verdict.

    Every layer waves them through by default: Starlette's request.json()
    is json.loads, which parses these bare tokens, pydantic's float allows
    non-finite values unless told not to, and Postgres double precision
    stores them. The verdicts they produce are not errors, they are
    confident nonsense. A NaN loses every comparison, so every claim it
    touches resolves wrong. An Infinity wins every gt and gte, so those
    claims resolve correct and contribute a near-perfect Brier score. The
    bad value then persists into the published teardown as a measured
    finding.

    The body is sent as raw bytes rather than through httpx's json= so the
    exact wire token under test is what reaches the route, which is the
    thing that was never gated. A claim's threshold is already refused the
    same way (_claim_from_form), and app.metrics.retrieval already returns
    0.0 rather than 0/0; the measured value is the remaining door.
    """
    r = client.post(
        f"/cycles/{sealed_cycle.id}/runs",
        content=f'{{"notes": "harness run", "measurements": {{"recall_at_5": {token}}}}}',
        headers={"content-type": "application/json"},
    )

    assert r.status_code == 422
    # The refusal names the metric, so the author knows which one to fix.
    assert "recall_at_5" in r.text

    # Nothing was stored and the cycle did not move to measured, so this
    # cannot be scored as if a harness had reported something.
    assert session.query(Measurement).count() == 0
    assert session.query(HarnessRun).count() == 0
    assert session.get(Cycle, sealed_cycle.id).stage == "sealed"


def test_a_finite_measurement_is_still_accepted(client, session, sealed_cycle):
    """The negative counterpart: the finiteness gate must not reject real
    numbers. 0.0 is the value most likely to be caught by a sloppy check
    written as a truthiness test rather than math.isfinite.
    """
    r = client.post(
        f"/cycles/{sealed_cycle.id}/runs",
        json={"notes": "harness run", "measurements": {"recall_at_5": 0.0}},
    )
    assert r.status_code == 201
    assert session.query(Measurement).one().value == 0.0

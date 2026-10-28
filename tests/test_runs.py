from app.models import Measurement


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

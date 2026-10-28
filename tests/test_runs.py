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

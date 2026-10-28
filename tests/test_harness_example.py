"""The README's worked example harness, driven on the real path.

That example is the one page in this repository the author will copy on his
first real cycle, so a wrong import or a wrong signature in it is a defect in
the product and not in the prose. This file runs the example's body: the same
metric import, the same complete() call, the same session.commit() the spend
ledger depends on, and the same POST body shape. If the example stops
working, this test goes red.

Two substitutions, and nothing else:

- app.llm._send is stubbed. The real network call is covered by the one
  key-gated test in tests/test_llm_budget.py and must not be billed by every
  run of the suite.
- The run is posted through the ASGI client instead of httpx against
  127.0.0.1:8000, because the suite starts no server. It is the same route,
  the same validation and the same database either way.
"""

from types import SimpleNamespace

from app.db import SessionLocal
from app.llm import complete, current_month
from app.metrics import recall_at_k
from app.models import Cycle, HarnessRun, Measurement, SpendLedger


def test_the_readme_harness_example_measures_commits_and_posts(
    client, session, sealed_cycle, monkeypatch
):
    monkeypatch.setattr(
        "app.llm._send",
        lambda *a, **k: SimpleNamespace(
            content=[SimpleNamespace(type="text", text="yes")],
            usage=SimpleNamespace(input_tokens=40, output_tokens=16),
        ),
    )

    # The example's body, from "session = get_session()" onward. get_session()
    # is what the README calls; the session fixture hands over an equivalent
    # session bound to the same engine, so its tables are torn down after.
    harness_session = session
    recall = recall_at_k(["doc-7", "doc-2", "doc-9"], {"doc-2", "doc-4"}, 5)
    verdict = complete(
        harness_session,
        "Answer yes or no: did the answer use the second retrieved document?",
        model="claude-sonnet-5",
        max_tokens=16,
    )
    harness_session.commit()

    response = client.post(
        f"/cycles/{sealed_cycle.id}/runs",
        json={
            "notes": f"recall_at_5 over 3 retrieved docs; judge said {verdict.strip()}",
            "measurements": {"recall_at_5": recall},
        },
    )

    assert response.status_code == 201
    assert "id" in response.json()

    # The route owns its own session, so drop whatever this one still holds
    # before reading back what the route wrote.
    session.expire_all()

    # The metric's own answer: one of two relevant documents was retrieved.
    assert recall == 0.5
    assert session.query(Measurement).one().value == 0.5
    assert session.get(Cycle, sealed_cycle.id).stage == "measured"
    # The notes are the harness author's own words, carried through intact,
    # including the model's answer the example interpolates into them.
    assert session.query(HarnessRun).one().notes.endswith("judge said yes")

    # The commit obligation, proved from a second session rather than from
    # the one that wrote it. This is the part a harness author can forget:
    # complete() only flushes, so without the commit above the spend would
    # be invisible to every later cap check even though the money was spent.
    other = SessionLocal()
    try:
        row = other.query(SpendLedger).filter_by(month=current_month()).one()
        assert row.spent_cents > 0
    finally:
        other.close()

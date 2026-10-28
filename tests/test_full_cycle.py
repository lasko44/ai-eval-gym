"""The one test that drives a whole teardown cycle over real HTTP.

Every other test file in this project proves one route, or one route's
refusals, in isolation. This file is the proof that the routes compose: a
cycle is created, predicted on, sealed, measured, scored and read back, each
step through the real ASGI client, in the order a real user and a real
harness would actually produce.

This file takes the git_repo fixture, directly or through sealed_cycle-style
setup, on every test that seals. POST /cycles/{id}/seal runs a real git add
and git commit against the process working directory (see app/sealing.py),
and git_repo (defined in conftest.py) chdirs the process into a throwaway
repository under tmp_path for the duration of the test, so that commit can
never land in this project's own history. Skipping this fixture here would
mean every run of this test appends a commit to the branch this project is
built on.
"""

from conftest import VALID_CLAIM


def create_cycle(client, name, question):
    """Open a cycle and return its id.

    target_url is not part of the brief's call signature, but the route
    requires it (Form(...)), so a sensible placeholder is supplied here
    rather than pushed onto every caller. The new cycle's id is read off the
    Location header of the 303 redirect rather than followed into it, which
    is the cheapest way to learn the id without a second request.
    """
    response = client.post(
        "/cycles",
        data={
            "target_name": name,
            "target_url": "https://example.invalid/target",
            "question": question,
        },
    )
    assert response.status_code == 303
    location = response.headers["location"]
    return int(location.rsplit("/", 1)[-1])


def add_claim(client, cycle_id, *, text, metric, comparator, threshold, probability):
    """Submit one sealed-prediction claim as the predict form would."""
    response = client.post(
        f"/cycles/{cycle_id}/claims",
        data={
            "text": text,
            "metric": metric,
            "comparator": comparator,
            "threshold": str(threshold),
            "probability": str(probability),
        },
    )
    assert response.status_code == 303
    return response


def test_one_whole_cycle_over_http(client, git_repo):
    # --- Open the cycle and commit two claims while it is still open. ---
    cid = create_cycle(client, "example/rag-demo", "Is multi-hop retrieval any good?")

    add_claim(
        client,
        cid,
        text="multi-hop recall is poor",
        metric="recall_at_5",
        comparator="lt",
        threshold=0.5,
        probability=0.7,
    )
    add_claim(
        client,
        cid,
        text="reranking is absent so precision collapses",
        metric="precision_at_5",
        comparator="lt",
        threshold=0.3,
        probability=0.9,
    )

    # --- Predict-before-measure: a run cannot happen before the prediction
    # is sealed. Without this refusal the harness could peek at a claim and
    # then "measure" to match it, which is exactly what sealing exists to
    # prevent. ---
    premature_run = client.post(
        f"/cycles/{cid}/runs",
        json={"notes": "", "measurements": {"recall_at_5": 0.62}},
    )
    assert premature_run.status_code == 409

    # --- Measure-before-score: scoring reads harness runs, so it has
    # nothing to read yet and must refuse rather than report an empty score
    # as if nothing had been predicted. ---
    premature_score = client.post(f"/cycles/{cid}/score")
    assert premature_score.status_code == 409

    # --- Seal the prediction. This is the real git commit, landing in the
    # throwaway repository git_repo chdir'd into, never in this project. ---
    seal_response = client.post(f"/cycles/{cid}/seal")
    assert seal_response.status_code == 303

    # --- A sealed cycle takes no more claims. This is the whole point of
    # sealing: once the prediction is committed, it cannot be edited to
    # match whatever the harness later reports. ---
    claim_after_seal = client.post(f"/cycles/{cid}/claims", data=VALID_CLAIM)
    assert claim_after_seal.status_code == 409

    # --- Measure-before-score again, now from the sealed side: scoring
    # still has no run to read, so sealing alone does not unlock it. ---
    still_premature_score = client.post(f"/cycles/{cid}/score")
    assert still_premature_score.status_code == 409

    # --- The teardown is not available until the cycle is scored, even
    # though it is now sealed and could technically compute one. Showing a
    # score before POST /score has formally produced it would let a reader
    # see a result the cycle itself does not yet claim to have. ---
    premature_teardown = client.get(f"/cycles/{cid}/teardown")
    assert premature_teardown.status_code == 409

    # --- Run the harness. It measures recall_at_5 only; precision_at_5 is
    # never reported, so claim 2 has nothing to be resolved against. ---
    run_response = client.post(
        f"/cycles/{cid}/runs",
        json={"notes": "", "measurements": {"recall_at_5": 0.62}},
    )
    assert run_response.status_code == 201

    # --- Score the measured cycle. ---
    score_response = client.post(f"/cycles/{cid}/score")
    assert score_response.status_code == 200

    # --- Read the published teardown and check the arithmetic by hand,
    # against the brief's own numbers, rather than trusting whatever the
    # app under test produces.
    #
    # Claim 1: recall_at_5 lt 0.5 at probability 0.7. Measured 0.62.
    #   0.62 < 0.5 is False, so claim 1 resolves WRONG.
    # Claim 2: precision_at_5 lt 0.3 at probability 0.9. Never measured.
    #   No measurement for precision_at_5 exists, so claim 2 is UNRESOLVED
    #   and is excluded from the Brier computation entirely.
    # Exactly one of two claims resolved: resolved = 1, unresolved = 1,
    #   coverage = 1 / 2 = 0.5.
    # Brier score is the mean of (probability - outcome) ** 2 over resolved
    #   claims only. The single resolved pair is (0.7, False), i.e. outcome
    #   0.0, so brier = (0.7 - 0.0) ** 2 = 0.49.
    teardown = client.get(f"/cycles/{cid}/teardown")
    assert teardown.status_code == 200
    body = teardown.text

    # The two words the brief requires, kept verbatim. Neither word appears
    # anywhere in teardown.html's own markup, so each one only shows up here
    # because a real claim actually resolved that way.
    assert "wrong" in body
    assert "unresolved" in body

    # Tie each outcome word to the claim and the measured number it belongs
    # to, not just to its bare presence anywhere on the page.
    assert "recall_at_5 = 0.62" in body
    assert "Outcome: <strong>wrong</strong>" in body
    assert "Outcome: <strong>unresolved</strong>" in body

    # The hand-derived score numbers, exactly as score.html and teardown.html
    # render them ("%.3f"|format(...), and resolved/unresolved as bare ints).
    assert "<dt>Brier score</dt>\n        <dd>0.490</dd>" in body
    assert "<dt>Claims resolved</dt>\n        <dd>1</dd>" in body
    assert "<dt>Claims unresolved</dt>\n        <dd>1</dd>" in body
    assert "<dt>Coverage</dt>\n        <dd>0.500</dd>" in body

    # The markdown export is the same score read a second, independent way.
    markdown = client.get(f"/cycles/{cid}/teardown.md")
    assert markdown.status_code == 200
    assert markdown.headers["content-type"].startswith("text/markdown")
    assert "Outcome: **wrong**" in markdown.text
    assert "Outcome: **unresolved**" in markdown.text
    assert "Brier score: 0.490" in markdown.text
    assert "Coverage: 0.500" in markdown.text


def test_a_claim_with_no_metric_or_threshold_cannot_be_sealed(client):
    # A claim with no metric or no threshold has no falsification test
    # attached, so "retrieval is bad" alone is refused at 422 rather than
    # accepted and left permanently unresolvable. This is what makes a vague
    # prediction unsealable, not a stage check, so it is exercised here on
    # its own rather than folded into the full cycle above, and needs no
    # seal (so no git_repo) to demonstrate.
    cid = create_cycle(client, "example/rag-demo", "Is multi-hop retrieval any good?")

    no_metric = client.post(
        f"/cycles/{cid}/claims",
        data={
            "text": "retrieval is bad",
            "metric": "",
            "comparator": "lt",
            "threshold": "0.5",
            "probability": "0.7",
        },
    )
    assert no_metric.status_code == 422

    no_threshold = client.post(
        f"/cycles/{cid}/claims",
        data={
            "text": "retrieval is bad",
            "metric": "recall_at_5",
            "comparator": "lt",
            "threshold": "",
            "probability": "0.7",
        },
    )
    assert no_threshold.status_code == 422

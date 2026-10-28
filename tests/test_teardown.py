def test_teardown_shows_each_claim_with_its_outcome_and_the_measured_number(client, scored_cycle):
    # The brief's own text for this test asserts "0.42" in body, but the
    # scored_cycle fixture in conftest.py measures recall_at_5=0.2 and
    # flip_rate=0.1, never 0.42 (confirmed by grepping the whole repo: 0.42
    # only ever appears in test_runs.py's own manual POST bodies). Changing
    # the shared fixture is out of this task's scope and could affect other
    # tasks' tests, so this assertion is adapted to the fixture's real
    # values. Reported as a deviation from "verbatim" in task-6-report.md.
    #
    # Fix round 1, finding 1: "recall_at_5" in body and "0.2" in body are
    # each independently satisfied by the falsification-test line alone
    # (metric name; and 0.2 is also flip_rate's own threshold), so that
    # version would still pass even if the "Measured:" line were dropped
    # entirely or always printed "not measured". Asserting the concatenated
    # rendered pair "recall_at_5 = 0.2" ties the label to the value the way
    # both templates actually render it (teardown.html's
    # "<code>{{ metric }} = {{ measured }}</code>" and teardown.md.jinja's
    # backtick-quoted equivalent), so it can only pass if the measured value
    # is actually printed next to its own metric name.
    body = client.get(f"/cycles/{scored_cycle.id}/teardown").text
    assert "recall_at_5 = 0.2" in body and "wrong" in body


def test_teardown_shows_the_seal_hash_so_a_reader_can_check_the_commit(client, scored_cycle):
    assert scored_cycle.claims[-1].sealed_hash[:12] in client.get(f"/cycles/{scored_cycle.id}/teardown").text


def test_markdown_export_is_served_as_markdown(client, scored_cycle):
    r = client.get(f"/cycles/{scored_cycle.id}/teardown.md")
    assert r.headers["content-type"].startswith("text/markdown")


def test_markdown_export_body_includes_the_wrong_claim_with_its_measured_value_and_outcome(
    client, scored_cycle
):
    # Fix round 1, finding 2: the markdown tests in this file previously only
    # checked status_code and content-type, never r.text. A markdown route
    # returning an empty body with the right header, or one that rendered
    # the wrong claim's outcome, or one that silently dropped the wrong
    # claim entirely, would have passed every test in this file. This is the
    # export the user actually publishes, so "claims scored wrong are shown,
    # not hidden" has to be checked in the export's own body, not inferred
    # from the HTML page's tests.
    body = client.get(f"/cycles/{scored_cycle.id}/teardown.md").text
    assert "the judge flips when the two answers are swapped" in body
    assert "flip_rate = 0.1" in body
    assert "Outcome: **wrong**" in body


def test_teardown_is_refused_before_scoring(client, sealed_cycle):
    r = client.get(f"/cycles/{sealed_cycle.id}/teardown")
    assert r.status_code == 409


def test_markdown_export_is_refused_before_scoring(client, sealed_cycle):
    r = client.get(f"/cycles/{sealed_cycle.id}/teardown.md")
    assert r.status_code == 409


def test_teardown_md_route_is_not_swallowed_by_the_html_route_or_the_int_cycle_route(
    client, scored_cycle
):
    # /cycles/{id}/teardown.md must reach the markdown route, not be parsed
    # as a 404 against the int-typed /cycles/{cycle_id} route, and not render
    # the HTML page's content type.
    r = client.get(f"/cycles/{scored_cycle.id}/teardown.md")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    assert "text/html" not in r.headers["content-type"]


def test_the_run_page_offers_a_score_form_once_measured(client, sealed_cycle, session):
    # Fix round 1, finding 3: asserting only that the URL string appears
    # would pass equally if run.html rendered a plain <a href> link instead
    # of a POST form (a GET to that route would 405). Assert the actual
    # <form method="post" action="..."> markup, not a substring of the URL.
    client.post(f"/cycles/{sealed_cycle.id}/runs",
                json={"notes": "", "measurements": {"recall_at_5": 0.42}})
    r = client.get(f"/cycles/{sealed_cycle.id}/runs")
    assert f'<form method="post" action="/cycles/{sealed_cycle.id}/score">' in r.text


def test_the_run_page_does_not_offer_a_score_form_before_measuring(client, sealed_cycle):
    # Fix round 1, finding 4: the positive case above has no negative
    # counterpart, so a regression that removed run.html's
    # {% if cycle.stage in ("measured", "scored") %} gate (making the form
    # always render) would not be caught. sealed_cycle is sealed but not yet
    # measured, which is exactly the stage the gate is meant to exclude.
    r = client.get(f"/cycles/{sealed_cycle.id}/runs")
    assert f'action="/cycles/{sealed_cycle.id}/score"' not in r.text


def test_the_cycle_page_links_to_teardown_once_scored(client, scored_cycle):
    r = client.get(f"/cycles/{scored_cycle.id}")
    assert f'/cycles/{scored_cycle.id}/teardown' in r.text


def test_the_cycle_page_does_not_link_to_teardown_before_scoring(client, sealed_cycle):
    # Fix round 1, finding 4: the negative counterpart to the test above, so
    # a regression that removed cycle.html's
    # {% if cycle.stage == "scored" %} gate (making the teardown link always
    # render) would not be caught. sealed_cycle is sealed, not scored.
    r = client.get(f"/cycles/{sealed_cycle.id}")
    assert f'/cycles/{sealed_cycle.id}/teardown' not in r.text


def test_the_cycle_page_links_to_runs(client, cycle):
    r = client.get(f"/cycles/{cycle.id}")
    assert f'/cycles/{cycle.id}/runs' in r.text

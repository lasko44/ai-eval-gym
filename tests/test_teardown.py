def test_teardown_shows_each_claim_with_its_outcome_and_the_measured_number(client, scored_cycle):
    # The brief's own text for this test asserts "0.42" in body, but the
    # scored_cycle fixture in conftest.py measures recall_at_5=0.2 and
    # flip_rate=0.1, never 0.42 (confirmed by grepping the whole repo: 0.42
    # only ever appears in test_runs.py's own manual POST bodies). Changing
    # the shared fixture is out of this task's scope and could affect other
    # tasks' tests, so this assertion uses the fixture's real measured value
    # (0.2) instead, which still proves the page shows the metric name, the
    # measured number and an outcome together. Reported as a deviation from
    # "verbatim" in task-6-report.md.
    body = client.get(f"/cycles/{scored_cycle.id}/teardown").text
    assert "recall_at_5" in body and "0.2" in body and "wrong" in body


def test_teardown_shows_the_seal_hash_so_a_reader_can_check_the_commit(client, scored_cycle):
    assert scored_cycle.claims[-1].sealed_hash[:12] in client.get(f"/cycles/{scored_cycle.id}/teardown").text


def test_markdown_export_is_served_as_markdown(client, scored_cycle):
    r = client.get(f"/cycles/{scored_cycle.id}/teardown.md")
    assert r.headers["content-type"].startswith("text/markdown")


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
    client.post(f"/cycles/{sealed_cycle.id}/runs",
                json={"notes": "", "measurements": {"recall_at_5": 0.42}})
    r = client.get(f"/cycles/{sealed_cycle.id}/runs")
    assert f'/cycles/{sealed_cycle.id}/score' in r.text


def test_the_cycle_page_links_to_teardown_once_scored(client, scored_cycle):
    r = client.get(f"/cycles/{scored_cycle.id}")
    assert f'/cycles/{scored_cycle.id}/teardown' in r.text


def test_the_cycle_page_links_to_runs(client, cycle):
    r = client.get(f"/cycles/{cycle.id}")
    assert f'/cycles/{cycle.id}/runs' in r.text

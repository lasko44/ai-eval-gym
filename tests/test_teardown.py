"""The teardown page and its markdown export.

Every fixture here carries a real seal, which means a real git commit in the
throwaway repository the git_repo fixture creates, so nothing in this file
commits to the project's own repository.
"""

import re

from app.models import HarnessRun
from conftest import _git


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


# C1(b) and C2 below. Both are about what the published artifact lets a
# reader check for themselves: the seal names the commit that holds it, and
# every harness run is listed so a measurement that was replaced is still
# visible rather than gone.


def test_teardown_names_the_commit_that_holds_the_seal(client, scored_cycle, git_repo):
    """A named commit is checkable; "somewhere in the git history" is not.

    scored_cycle seals through app.sealing in the throwaway git_repo, so the
    recorded SHA is a real commit in that repository, and the test compares
    the rendered value against git's own answer rather than against itself.
    """
    sha = _git(git_repo, "rev-parse", "HEAD").strip()
    assert scored_cycle.sealed_commit == sha

    page = client.get(f"/cycles/{scored_cycle.id}/teardown").text
    export = client.get(f"/cycles/{scored_cycle.id}/teardown.md").text
    for body in (page, export):
        assert sha in body
        # The reader is given the command, not told to go and look.
        assert f"git show {sha}" in body


def test_teardown_renders_honestly_when_no_seal_commit_was_recorded(
    client, session, scored_cycle
):
    """The demo cycle in the development database is exactly this row.

    sealed_commit is nullable because cycles sealed before the column
    existed have no SHA to find. Neither output may print "None" or raise
    for those: both have to say plainly that no commit is recorded here.
    """
    scored_cycle.sealed_commit = None
    session.commit()

    page = client.get(f"/cycles/{scored_cycle.id}/teardown")
    export = client.get(f"/cycles/{scored_cycle.id}/teardown.md")
    assert page.status_code == 200
    assert export.status_code == 200
    for body in (page.text, export.text):
        assert "sealed before the app began recording" in body
        assert f"git log -- seals/cycle-{scored_cycle.id}.txt" in body
        # Not "in commit `None`", and not an empty backtick pair either.
        assert "None" not in body
        assert "in commit" not in body


def test_teardown_shows_every_run_so_a_rewritten_measurement_is_visible(
    client, session, sealed_cycle
):
    """Two runs reporting the same metric: both have to be in the artifact.

    This is the C2 shape, driven the way an author would actually do it. The
    thresholds are on the predict page and the measured values on the runs
    page, so an author can read "recall_at_5 lt 0.5" against a measured
    0.62, know that claim resolved wrong, and post a second run reporting
    0.2 so it resolves correct instead. Latest-run-wins is the correct rule
    and is deliberately unchanged here; what was missing was any trace of
    the first run in the published artifact, which made an overwritten
    cycle indistinguishable from one whose harness ran once and got 0.2.

    Asserting the value next to its own marker, rather than just the number
    somewhere in the body, is what makes this test real: "recall_at_5 = 0.2"
    on its own is already printed by the claims section as the measured
    value, so a template that listed no runs at all would still satisfy a
    bare substring check.
    """
    cycle_id = sealed_cycle.id
    client.post(
        f"/cycles/{cycle_id}/runs",
        json={"notes": "first harness run, before the fix", "measurements": {"recall_at_5": 0.62}},
    )
    client.post(
        f"/cycles/{cycle_id}/runs",
        json={"notes": "second harness run, after the fix", "measurements": {"recall_at_5": 0.2}},
    )
    assert client.post(f"/cycles/{cycle_id}/score").status_code == 200

    page = client.get(f"/cycles/{cycle_id}/teardown").text
    export = client.get(f"/cycles/{cycle_id}/teardown.md").text

    runs = session.query(HarnessRun).order_by(HarnessRun.id).all()
    assert len(runs) == 2

    # Both runs, each with its own notes and its own created_at, in both
    # outputs.
    for body in (page, export):
        for run in runs:
            assert run.notes in body
            assert str(run.created_at) in body

    # Both values, each next to the marker that says whether it is the one
    # the score used. The HTML wraps the value in <code> and puts the marker
    # on its own line, so match across the whitespace.
    assert re.search(
        r"recall_at_5 = 0\.62</code>\s*\(superseded by a later run\)", page
    ), page
    assert re.search(r"recall_at_5 = 0\.2</code>\s*\(scored\)", page), page

    assert "`recall_at_5 = 0.62` (superseded by a later run)" in export
    assert "`recall_at_5 = 0.2` (scored)" in export

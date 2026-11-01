"""The way in: the introduction, the guided tour, and the tooltips.

A newcomer meets the app through these, so they are the one part of the
interface where being broken is invisible to the person who built it. He
already knows what a probe is.

Two properties matter more than the copy. The tour has to walk the REAL
pages, because a tour built from screenshots goes stale the first time the
interface moves and nothing fails when it does. And a mistyped ?tour= value
has to drop the panel rather than break the page it was meant to explain.
"""

import re

import pytest

import app.tour as guide
import app.units as curriculum

ROUTES = {"/", "/units", "/review", "/cycles", "/glossary", "/start"}


# --- the tour is pinned to pages that exist ---

def test_every_step_points_at_a_route_that_serves(client):
    """A step naming a dead route is a tour that walks into a wall."""
    for index, step in enumerate(guide.STEPS, start=1):
        response = client.get(f"{step.route}")
        assert response.status_code == 200, (
            f"step {index} ({step.slug}) points at {step.route}, which "
            f"returned {response.status_code}"
        )


def test_every_step_renders_its_panel_on_its_own_route(client):
    for index, step in enumerate(guide.STEPS, start=1):
        joiner = "&" if "?" in step.route else "?"
        body = client.get(f"{step.route}{joiner}tour={index}").text
        assert 'class="tour"' in body, f"step {index} rendered no panel"
        assert f"Step {index} of {len(guide.STEPS)}" in body
        assert step.title in body


def test_the_steps_chain_forwards_and_backwards():
    last = len(guide.STEPS)
    assert guide.previous_link(1) is None, "step 1 offers a step before it"
    assert guide.next_link(last) is None, "the last step offers a step after it"
    for index in range(1, last):
        assert f"tour={index + 1}" in guide.next_link(index)
    for index in range(2, last + 1):
        assert f"tour={index - 1}" in guide.previous_link(index)


def test_a_step_link_keeps_any_parameter_the_route_already_carries():
    """Three steps sit on a locked unit, which needs anyway=1 to open.

    Losing it would send a reader mid-tour to a lock screen explaining why
    they cannot see the thing the tour is pointing at.
    """
    for index, step in enumerate(guide.STEPS, start=1):
        if "?" not in step.route:
            continue
        link = guide.next_link(index - 1) if index > 1 else None
        if link is None:
            continue
        assert "?" in link and "&tour=" in link, (
            f"the link to step {index} dropped {step.route}'s own parameter"
        )


# --- a bad parameter is harmless ---

@pytest.mark.parametrize("value", ["99", "0", "-1", "abc", "", "1.5", "<script>"])
def test_a_nonsense_tour_value_drops_the_panel_and_serves_the_page(client, value):
    response = client.get("/", params={"tour": value})
    assert response.status_code == 200, f"?tour={value!r} broke the page"
    assert 'class="tour"' not in response.text


def test_number_rejects_what_is_not_a_step():
    assert guide.number(None) is None
    assert guide.number("abc") is None
    assert guide.number(0) is None
    assert guide.number(len(guide.STEPS) + 1) is None
    assert guide.number(1) == 1
    assert guide.number("1") == 1


def test_the_panel_offers_a_way_out_on_every_step(client):
    """A tour with no exit is a modal, and this one is not even modal."""
    for index, step in enumerate(guide.STEPS, start=1):
        joiner = "&" if "?" in step.route else "?"
        body = client.get(f"{step.route}{joiner}tour={index}").text
        assert "Close the tour" in body, f"step {index} cannot be dismissed"


# --- the introduction ---

def test_start_page_serves_and_sends_a_reader_somewhere(client):
    body = client.get("/start").text
    assert f"/units/{curriculum.UNITS[0].slug}" in body, (
        "the introduction does not link to the first unit"
    )
    assert "/?tour=1" in body, "the introduction does not offer the tour"
    assert curriculum.SYSTEM.name in body


def test_start_is_reachable_from_every_page(client):
    for path in ROUTES:
        assert 'href="/start"' in client.get(path).text, (
            f"{path} does not offer the introduction, so it is found by luck"
        )


# --- tooltips ---

def test_every_tip_is_one_sentence_a_person_can_read():
    """Two sentences in a tip means the control is doing two things."""
    for key, text in guide.TIPS.items():
        assert text.strip(), f"{key} has no text"
        assert len(text) <= 240, f"{key} is too long for a tooltip: {len(text)}"
        assert text[0].isupper(), f"{key} does not start with a capital"
        assert text.rstrip().endswith("."), f"{key} does not end in a full stop"


def test_no_tip_repeats_a_glossary_definition():
    """The glossary owns course terms; tips own interface controls.

    A term with two homes drifts, and the one nobody is looking at goes
    stale first.
    """
    from app.glossary import TERMS

    glossary_terms = {term.term.lower() for term in TERMS}
    overlap = glossary_terms & set(guide.TIPS)
    assert not overlap, (
        f"{sorted(overlap)} is explained in both app/glossary.py and "
        "app/tour.py. Keep it in one of them."
    )


@pytest.mark.parametrize(
    "path,expected",
    [("/", "rank"), ("/", "calibration_score"), ("/", "streak"), ("/start", "fixture")],
)
def test_tips_reach_the_rendered_page(client, path, expected):
    body = client.get(path).text
    assert 'class="stat-label tip"' in body or "data-tip" in body
    fragment = guide.TIPS[expected].split(".")[0][:40]
    assert fragment in body, f"the {expected} tip never reached {path}"


def test_a_tip_is_reachable_without_a_mouse(client):
    """Hover alone would hide every explanation from the keyboard."""
    body = client.get("/").text
    for match in re.finditer(r'<[^>]*data-tip="[^"]*"[^>]*>', body):
        assert "tabindex=" in match.group(0), (
            f"a tooltip is mouse-only: {match.group(0)[:90]}"
        )


def test_the_tooltip_shows_on_focus_as_well_as_hover():
    from pathlib import Path

    css = (Path(__file__).resolve().parent.parent
           / "app" / "templates" / "base.html").read_text()
    rule = re.search(r"\.tip:hover::after[^{]*\{", css)
    assert rule, "no tooltip reveal rule at all"
    assert ":focus" in rule.group(0), (
        "the tooltip reveals on hover only, so a keyboard never sees it"
    )


def test_the_tour_and_tips_need_no_javascript():
    """No build step, no script tag. The tour is a query parameter.

    If this ever fails, the tour stopped working for anybody with scripting
    off and started needing a toolchain this project does not have.
    """
    from pathlib import Path

    templates = (Path(__file__).resolve().parent.parent / "app" / "templates")
    offenders = [
        path.name
        for path in templates.glob("*.html")
        if "<script" in path.read_text().lower()
    ]
    assert not offenders, f"a script tag appeared in {offenders}"

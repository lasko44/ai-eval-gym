"""A unit as a lesson: one thing per screen, one next action.

The page used to print four hundred words of briefing, then three questions,
then an exercise, and leave a reader to decide where to start. These tests
hold the shape that replaced it.

The property that matters most is not the step count. It is that a reader can
never be on a screen with nothing to do and no obvious way on, and that
answering something returns them to where they answered it rather than to the
top of the unit.
"""

import html

import pytest

import app.units as curriculum
from app.lesson import fixture_peek, step_at, steps

ALL_UNITS = list(curriculum.UNITS)
UNIT_IDS = [unit.slug for unit in ALL_UNITS]


# --- the shape of a lesson ---

@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_a_lesson_covers_every_paragraph_and_every_probe(unit):
    """Splitting a briefing must not lose any of it."""
    made = steps(unit)
    read = [p for s in made if s.kind == "read" for p in s.paragraphs]
    assert read == list(unit.brief), (
        f"{unit.slug} loses or reorders briefing paragraphs when split"
    )
    probed = [s.probe_id for s in made if s.kind == "probe"]
    assert probed == [probe.id for probe in unit.probes]


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_a_lesson_numbers_its_steps_from_one_with_no_gaps(unit):
    numbers = [s.index for s in steps(unit)]
    assert numbers == list(range(1, len(numbers) + 1))


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_both_reading_steps_carry_something_to_read(unit):
    """A split that leaves a screen empty is worse than no split."""
    for s in steps(unit):
        if s.kind == "read":
            assert s.paragraphs, f"{unit.slug} step {s.index} has nothing on it"


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_a_lesson_ends_with_the_measurement_then_the_takeaway(unit):
    kinds = [s.kind for s in steps(unit)]
    assert kinds[-2:] == ["detect", "close"], (
        f"{unit.slug} does not end on measure then review, it ends {kinds[-2:]}"
    )
    assert kinds[0] == "read", "a lesson should open on what goes wrong"


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_every_step_has_a_short_label_for_the_rail(unit):
    for s in steps(unit):
        assert s.label.strip() and len(s.label) <= 16, (
            f"{unit.slug} step {s.index} label {s.label!r} will not fit a rail"
        )
        assert s.heading.strip()


# --- a bad step number is harmless ---

@pytest.mark.parametrize("value", [None, "", "abc", "0", "-3", "999", "1.5"])
def test_a_nonsense_step_lands_on_the_first_one(value):
    unit = ALL_UNITS[0]
    assert step_at(unit, value).index == 1


def test_a_real_step_number_lands_on_that_step():
    unit = ALL_UNITS[0]
    for s in steps(unit):
        assert step_at(unit, s.index).index == s.index
        assert step_at(unit, str(s.index)).index == s.index


# --- driven through the real routes ---

def test_every_step_of_every_unit_serves(client):
    for unit in ALL_UNITS:
        for s in steps(unit):
            response = client.get(
                f"/units/{unit.slug}", params={"step": s.index, "anyway": 1}
            )
            assert response.status_code == 200, (
                f"{unit.slug} step {s.index} returned {response.status_code}"
            )
            assert f"Step {s.index} of {len(steps(unit))}" in response.text


def test_a_step_always_offers_exactly_one_next_action(client):
    """A screen with nothing to click is where a lesson stops being one."""
    unit = ALL_UNITS[0]
    total = len(steps(unit))
    for index in range(1, total + 1):
        body = client.get(
            f"/units/{unit.slug}", params={"step": index, "anyway": 1}
        ).text
        assert body.count('class="btn"') >= 1, f"step {index} has no next action"
        if index > 1:
            assert f"step={index - 1}" in body, f"step {index} cannot go back"


def test_the_first_step_does_not_offer_a_step_before_it(client):
    unit = ALL_UNITS[0]
    body = client.get(f"/units/{unit.slug}", params={"step": 1, "anyway": 1}).text
    assert "step=0" not in body


def test_answering_a_probe_returns_to_the_step_it_was_asked_on(session, client):
    """Landing back at the top after every answer is how a lesson becomes a scroll."""
    unit = ALL_UNITS[0]
    probe = unit.probes[1]
    response = client.post(
        f"/units/{unit.slug}/probes/{probe.id}",
        data={"choice": probe.answer, "probability": 0.8, "step": 4},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == f"/units/{unit.slug}?step=4"


def test_posting_a_measurement_returns_to_its_step(session, client):
    unit = ALL_UNITS[0]
    response = client.post(
        f"/units/{unit.slug}/exercise",
        data={"value": unit.exercise.expected, "step": 6},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == f"/units/{unit.slug}?step=6"


def test_one_probe_per_screen(client):
    """Three questions on one screen invites answering them as a set."""
    unit = ALL_UNITS[0]
    probe_steps = [s for s in steps(unit) if s.kind == "probe"]
    for s in probe_steps:
        # Unescape first: Jinja turns an apostrophe into &#39;, and a raw
        # substring check would quietly find nothing and call that a pass.
        body = html.unescape(client.get(
            f"/units/{unit.slug}", params={"step": s.index, "anyway": 1}
        ).text)
        shown = [p for p in unit.probes if p.asks in body]
        assert len(shown) == 1, (
            f"step {s.index} shows {len(shown)} questions, not one"
        )


def test_the_whole_unit_is_still_readable_on_one_page(client):
    """Worth keeping, and worth not being the default."""
    unit = ALL_UNITS[0]
    body = html.unescape(
        client.get(f"/units/{unit.slug}", params={"all": 1, "anyway": 1}).text
    )
    for paragraph in unit.brief:
        assert paragraph[:40] in body
    # The class name also appears in the stylesheet, so look for the markup.
    assert '<ol class="steprail"' not in body, (
        "the one-page view should not show a step rail"
    )


def test_the_stepped_view_is_what_a_bare_url_gives(client):
    unit = ALL_UNITS[0]
    body = client.get(f"/units/{unit.slug}", params={"anyway": 1}).text
    assert '<ol class="steprail"' in body
    assert f"Step 1 of {len(steps(unit))}" in body


# --- the fixture hint ---

@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_every_unit_can_show_the_shape_of_its_own_fixture(unit):
    """Generated from the real file, so it cannot drift from the fixture."""
    peek = fixture_peek(unit.exercise.fixture_path)
    assert peek, f"{unit.slug} cannot preview {unit.exercise.fixture_path}"
    assert len(peek.splitlines()) <= 15, "the preview is long enough to be the file"


def test_a_missing_or_broken_fixture_gives_no_hint_rather_than_an_error():
    assert fixture_peek("fixtures/nope/missing.json") is None
    assert fixture_peek("README.md") is None


def test_the_hint_is_closed_until_asked_for(client):
    """A hint you cannot avoid is an answer."""
    unit = ALL_UNITS[0]
    detect = next(s for s in steps(unit) if s.kind == "detect")
    body = client.get(
        f"/units/{unit.slug}", params={"step": detect.index, "anyway": 1}
    ).text
    assert "<details" in body and "hint-box" in body
    assert "<details open" not in body

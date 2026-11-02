"""Structural checks over the whole curriculum.

Units are authored content written one file at a time, so these tests are the
gate that every unit passes regardless of who wrote it. They check the things
that would otherwise be caught by a reader noticing, which is not a gate at all:
a probe whose correct answer is not one of its options, a fixture the unit
refers to that does not exist, an exercise whose expected value cannot be
reached, two units claiming the same slug.

They deliberately do not check the prose. Whether a briefing is any good is a
judgement, and judgement does not belong in a test.
"""

import html
import importlib
import json
import re
from pathlib import Path

import pytest

import app.units as curriculum
from app.units.types import Unit

REPO_ROOT = Path(__file__).resolve().parent.parent
EM_DASH = "\u2014"  # the character itself, written as an escape

ALL_UNITS = list(curriculum.UNITS)
UNIT_IDS = [unit.slug for unit in ALL_UNITS]


def test_the_curriculum_is_not_empty():
    assert ALL_UNITS, "No units were discovered. Check app/units/ for a module exporting UNIT."


def test_slugs_are_unique():
    slugs = [unit.slug for unit in ALL_UNITS]
    assert len(slugs) == len(set(slugs)), f"Duplicate slug in {slugs}"


def test_numbers_are_unique():
    numbers = [unit.number for unit in ALL_UNITS]
    assert len(numbers) == len(set(numbers)), f"Duplicate number in {sorted(numbers)}"


def test_units_are_ordered_by_number():
    numbers = [unit.number for unit in ALL_UNITS]
    assert numbers == sorted(numbers)


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_no_unit_claims_a_reading_time(unit: Unit):
    """A reading time was invented once and copied into every unit.

    Nobody measured it. This test stops it coming back by any name.
    """
    for field in ("minutes", "duration", "reading_time", "time"):
        assert not hasattr(unit, field), (
            f"{unit.slug} carries {field!r}. If nobody measured it, do not ship it."
        )


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_unit_has_the_parts_a_unit_needs(unit: Unit):
    assert unit.title.strip()
    assert unit.failure.strip()
    assert unit.detection.strip()
    assert len(unit.brief) >= 3, "A briefing shorter than three paragraphs is a stub."
    assert all(paragraph.strip() for paragraph in unit.brief)
    assert unit.probes, "A unit with no probes is an article."
    assert unit.sources, "Every claim traces to a source, so every unit names its own."


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_every_probe_is_answerable(unit: Unit):
    """The correct answer has to be one of the options, and options have to be distinct.

    A probe whose answer key matches no option is unanswerable: it marks every
    attempt wrong, which would quietly punish him for the author's typo.
    """
    for probe in unit.probes:
        keys = [choice.key for choice in probe.choices]
        assert len(keys) >= 2, f"{unit.slug}/{probe.id} needs at least two options"
        assert len(keys) == len(set(keys)), f"{unit.slug}/{probe.id} has a duplicate option key"
        assert probe.answer in keys, (
            f"{unit.slug}/{probe.id} answers {probe.answer!r}, "
            f"which is not one of {keys}"
        )
        labels = [choice.label.strip().lower() for choice in probe.choices]
        assert len(labels) == len(set(labels)), f"{unit.slug}/{probe.id} has two identical options"
        assert probe.asks.strip()
        assert probe.because.strip(), (
            f"{unit.slug}/{probe.id} has no explanation, so being wrong teaches nothing"
        )


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_probe_ids_are_unique_within_a_unit(unit: Unit):
    ids = [probe.id for probe in unit.probes]
    assert len(ids) == len(set(ids)), f"{unit.slug} has a duplicate probe id in {ids}"


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_the_exercise_fixture_exists_and_is_readable(unit: Unit):
    """The fixture is the exercise. A unit that points at a missing file is broken."""
    path = REPO_ROOT / unit.exercise.fixture_path
    assert path.is_file(), f"{unit.slug} refers to {unit.exercise.fixture_path}, which is not there"
    with path.open() as handle:
        json.load(handle)


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_the_exercise_can_be_passed_and_failed(unit: Unit):
    """The tolerance has to admit the expected answer and reject a wrong one.

    A tolerance of zero would make floating point the examiner, and a tolerance
    wide enough to accept anything would make the check meaningless. This pins
    both ends.
    """
    exercise = unit.exercise
    assert exercise.tolerance > 0, f"{unit.slug} would fail its own expected answer"
    assert abs(exercise.expected - exercise.expected) <= exercise.tolerance

    span = max(abs(exercise.expected), 1.0)
    clearly_wrong = exercise.expected + span
    assert abs(clearly_wrong - exercise.expected) > exercise.tolerance, (
        f"{unit.slug} would accept {clearly_wrong}, so its tolerance is too wide"
    )
    assert exercise.asks.strip()
    assert exercise.starter.strip()
    assert exercise.because.strip()
    assert exercise.metric.strip()


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_the_fixture_actually_produces_the_expected_answer(unit: Unit):
    """Run the unit's own reference solution against its own fixture.

    Without this, `expected` is a number somebody typed next to a file, and
    the test above only compares it to itself. That is the exact failure this
    curriculum teaches a reader to catch, shipped inside the curriculum.

    A unit opts in by defining `solve(data)` in its module, taking the parsed
    fixture and returning the number the exercise asks for. A unit without one
    is skipped rather than failed, so this can be adopted unit by unit, but
    the skip is visible in the run and is a debt rather than a pass.

    `data` is whatever the fixture parses to, which is usually a dict and in
    at least one unit a list. A solve() should annotate what its own fixture
    actually holds rather than copying the common case.
    """
    module = importlib.import_module(f"app.units.{unit.slug.replace('-', '_')}")
    solve = getattr(module, "solve", None)
    if solve is None:
        pytest.skip(f"{unit.slug} has no solve(), so its expected value is unverified")

    with (REPO_ROOT / unit.exercise.fixture_path).open() as handle:
        data = json.load(handle)

    measured = solve(data)
    assert abs(measured - unit.exercise.expected) <= unit.exercise.tolerance, (
        f"{unit.slug} ships expected={unit.exercise.expected} but its fixture "
        f"measures {measured}. Regenerate the fixture or correct the unit; do "
        "not widen the tolerance."
    )


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_no_em_dash_anywhere_in_the_unit(unit: Unit):
    """A house rule, and the one most easily broken by prose written at speed."""
    blobs = [unit.title, unit.failure, unit.detection, *unit.brief, *unit.sources]
    for probe in unit.probes:
        blobs += [probe.asks, probe.because, *(c.label for c in probe.choices)]
    blobs += [
        unit.exercise.asks,
        unit.exercise.fixture_note,
        unit.exercise.starter,
        unit.exercise.because,
    ]
    offenders = [blob for blob in blobs if EM_DASH in blob]
    assert not offenders, f"{unit.slug} contains an em dash in: {offenders[:1]}"


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_the_briefing_carries_a_number(unit: Unit):
    """Every unit is built on measurements, so the briefing should contain some.

    This is a weak check on purpose: it catches a briefing written entirely from
    assertion, which is exactly the writing this project exists to teach him to
    distrust.
    """
    joined = " ".join(unit.brief)
    assert re.search(r"\d", joined), f"{unit.slug}'s briefing contains no figure at all"


def test_every_unit_page_renders(client):
    """Drives the real routes, because a unit that 500s is not a unit.

    `anyway=1` bypasses the part lock. On a clean database only part 1 is
    unlocked, so without it this would only ever prove that the first five
    units render, and a 500 in unit 14 would ship unnoticed. The lock itself
    is tested in tests/test_progress.py, where it belongs.
    """
    listing = html.unescape(client.get("/units").text)
    for unit in ALL_UNITS:
        assert unit.title in listing
        response = client.get(f"/units/{unit.slug}?anyway=1")
        assert response.status_code == 200, (
            f"/units/{unit.slug} returned {response.status_code}"
        )
        # Strip tags, then unescape, then compare. Two things sit between the
        # briefing and the page: Jinja escapes an apostrophe to &#39;, and
        # app/define.py wraps the first use of a glossary term in an anchor,
        # which lands mid-sentence. Comparing raw markup against raw prose
        # would make this fail on correct copy, which is the worst kind of
        # test to keep.
        rendered = html.unescape(re.sub(r"<[^>]+>", "", response.text))
        assert unit.brief[0][:40] in rendered


def test_a_locked_unit_hides_its_contents_and_says_what_it_needs(client):
    """The lock has to actually withhold the unit, or it is decoration.

    Unit 01 is in part 1 and always open. The last unit is in the final part,
    so on a clean database it is locked and must say which part it is waiting
    on rather than quietly rendering.
    """
    assert client.get(f"/units/{ALL_UNITS[0].slug}").status_code == 200

    last = ALL_UNITS[-1]
    locked = client.get(f"/units/{last.slug}")
    assert locked.status_code == 200
    assert last.brief[0][:40] not in locked.text, (
        f"{last.slug} is locked but rendered its briefing anyway."
    )
    assert "Locked" in locked.text
    assert f"/units/{last.slug}?anyway=1" in locked.text, (
        "A lock with no way past it is a wall, and this course has one reader."
    )


def test_an_unknown_unit_404s(client):
    assert client.get("/units/no-such-unit").status_code == 404


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_the_metric_is_named_like_a_function_not_described(unit: Unit):
    """`metric` is an identifier a reader types, not a sentence.

    It names the thing being computed, and it lines up with `app.metrics`
    where one exists. A prose description there reads fine on the page and
    breaks the moment anybody tries to grep for it.
    """
    name = unit.exercise.metric
    assert re.fullmatch(r"[a-z][a-z0-9_]*", name), (
        f"{unit.slug} names its metric {name!r}. Use a lower_snake_case "
        "identifier, as every other unit does."
    )

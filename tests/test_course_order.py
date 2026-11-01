"""The course order, and the pages that present it.

A flat list of units needs no tests beyond the ones in test_units.py. A course
does, because a course makes a promise a list does not: that unit 07 comes
after unit 06 for a reason, and that you can start at 01 and walk to the end
without being asked to use something nobody taught you yet.

Nothing here judges whether the order is the right one. That is a judgement.
These tests check that the order the curriculum claims is the order it ships:
no gaps in the numbering, no unit outside a part, no part out of sequence, and
the same ordering on every page that shows it.
"""

import re

import pytest

import app.units as curriculum
from app.units.parts import PARTS

ALL_UNITS = list(curriculum.UNITS)
UNIT_IDS = [unit.slug for unit in ALL_UNITS]
PART_IDS = [part.slug for part in PARTS]


def test_unit_numbers_run_from_one_with_no_gaps():
    numbers = [unit.number for unit in ALL_UNITS]
    assert numbers == list(range(1, len(numbers) + 1)), (
        f"Unit numbers are {numbers}. A course numbered with a gap tells a "
        "reader a unit is missing when it is not."
    )


def test_part_numbers_run_from_one_with_no_gaps():
    numbers = [part.number for part in PARTS]
    assert numbers == list(range(1, len(numbers) + 1)), f"Part numbers are {numbers}."


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_every_unit_names_a_part_that_exists(unit):
    assert curriculum.part_of(unit) is not None, (
        f"{unit.slug} names part {unit.part!r}, which is not in parts.py."
    )


@pytest.mark.parametrize("part", PARTS, ids=PART_IDS)
def test_no_part_is_empty(part):
    units = dict(curriculum.COURSE)[part]
    assert units, (
        f"Part {part.number} ({part.slug}) has no units. An empty part on the "
        "course page reads as a section somebody forgot to write."
    )


def test_units_never_leave_a_part_and_come_back():
    """Walking 1 to 15 should pass through each part exactly once.

    This is what makes the numbering and the grouping the same statement. If a
    unit in part 2 is numbered after a unit in part 3, the course page and the
    syllabus page disagree about what comes next.
    """
    walked = [unit.part for unit in ALL_UNITS]
    seen = []
    for part in walked:
        if not seen or seen[-1] != part:
            seen.append(part)
    assert len(seen) == len(set(seen)), (
        f"The course leaves a part and returns to it: {seen}."
    )


def test_the_parts_run_in_their_declared_order():
    walked = [unit.part for unit in ALL_UNITS]
    first_seen = []
    for part in walked:
        if part not in first_seen:
            first_seen.append(part)
    assert first_seen == [part.slug for part in PARTS], (
        f"Units run through the parts as {first_seen}, but parts.py declares "
        f"{[p.slug for p in PARTS]}."
    )


@pytest.mark.parametrize("part", PARTS, ids=PART_IDS)
def test_a_part_says_what_it_builds_on(part):
    """The sentence is the argument for the order, so it cannot be blank."""
    assert part.purpose.strip(), f"Part {part.number} has no purpose."
    assert part.builds_on.strip(), f"Part {part.number} does not say what it builds on."
    assert part.role_asks, (
        f"Part {part.number} names nothing the role asks for, so a reader "
        "cannot tell why it is in a course aimed at that job."
    )


def test_the_course_home_shows_every_part_and_unit_in_order(client):
    response = client.get("/")
    assert response.status_code == 200, response.text
    body = response.text

    for part in PARTS:
        assert part.title in body, f"Part {part.number} is missing from the course home."
    for unit in ALL_UNITS:
        assert f"/units/{unit.slug}" in body, f"{unit.slug} is not linked from the course home."

    found = [m.group(1) for m in re.finditer(r'href="/units/([a-z-]+)"', body)]
    ordered = [slug for slug in dict.fromkeys(found) if slug in set(UNIT_IDS)]
    assert ordered == UNIT_IDS, (
        f"The course home lists units as {ordered}, not in course order."
    )


def test_the_syllabus_lists_units_in_course_order(client):
    body = client.get("/units").text
    found = [m.group(1) for m in re.finditer(r'href="/units/([a-z-]+)"', body)]
    ordered = [slug for slug in dict.fromkeys(found) if slug in set(UNIT_IDS)]
    assert ordered == UNIT_IDS, f"The syllabus lists units as {ordered}."


def test_the_course_home_points_at_the_first_unfinished_unit(client):
    """With no progress recorded, the next step is unit 01."""
    body = client.get("/").text
    assert "Start here" in body
    assert f'/units/{ALL_UNITS[0].slug}' in body


def test_the_course_home_stops_saying_start_once_there_is_progress(client):
    """One answered probe means the reader has started, finished or not.

    The first version keyed this off finished units, so a reader three probes
    into unit 01 was still told to start here.
    """
    unit = ALL_UNITS[0]
    response = client.post(
        f"/units/{unit.slug}/probes/{unit.probes[0].id}",
        data={"choice": unit.probes[0].answer, "probability": "0.8"},
        follow_redirects=False,
    )
    assert response.status_code in (200, 303), response.text

    body = client.get("/").text
    assert "Pick up where you left off" in body
    assert "Start here" not in body


def test_a_unit_page_says_where_it_sits_and_what_comes_next(client):
    second = ALL_UNITS[1]
    body = client.get(f"/units/{second.slug}").text
    part = curriculum.part_of(second)
    assert f"Part {part.number} of {len(PARTS)}" in body
    assert f"/units/{ALL_UNITS[0].slug}" in body, "No link back to the previous unit."
    assert f"/units/{ALL_UNITS[2].slug}" in body, "No link on to the next unit."


def test_the_first_unit_has_no_previous_and_the_last_has_no_next(client):
    first = client.get(f"/units/{ALL_UNITS[0].slug}").text
    assert "Back to" not in first, "Unit 01 offers a previous unit that does not exist."

    last = client.get(f"/units/{ALL_UNITS[-1].slug}").text
    assert "Next:" not in last, "The last unit offers a next unit that does not exist."
    assert "/cycles" in last, "The last unit does not hand the reader on to a cycle."


def test_the_cycles_list_moved_to_its_own_route(client):
    """The front page is the course now. Cycles kept its content, not its path."""
    assert client.get("/cycles").status_code == 200
    assert "Cycles" in client.get("/cycles").text


# --- the chain between units ---
# Part.builds_on earns a part its place. Without the same field on a unit, the
# units inside a part are an unordered bag of failure modes and the course is
# a reference work again. These hold the unit-level chain to the same rule.

@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_every_unit_says_what_it_builds_on(unit):
    assert unit.builds_on.strip(), (
        f"{unit.slug} does not say what it needs from the units before it. A "
        "unit that cannot write that sentence is in the wrong place, and the "
        "order should change rather than the sentence."
    )


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_no_unit_builds_on_a_unit_the_reader_has_not_reached(unit):
    """A dependency pointing forwards is a dependency nobody can follow."""
    cited = {int(n) for n in re.findall(r"\bunits? (\d{2})\b", unit.builds_on.lower())}
    ahead = {n for n in cited if n >= unit.number}
    assert not ahead, (
        f"{unit.slug} is unit {unit.number:02d} and claims to build on "
        f"{sorted(ahead)}, which the reader has not reached yet."
    )


def test_the_first_unit_declares_itself_the_start():
    first = ALL_UNITS[0]
    assert "nothing" in first.builds_on.lower(), (
        f"{first.slug} is unit 01, so its builds_on has to say it depends on "
        "nothing rather than leaving a reader looking for a missing unit."
    )


WRITTEN_NUMBERS = re.compile(
    r"\b(fifteen|sixteen|seventeen|eighteen|nineteen|twenty|twenty-one|twenty-two)"
    r"\s+(units?|parts?|fixtures?)\b",
    re.I,
)


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_no_unit_writes_the_course_length_into_its_prose(unit):
    """A spelled-out count goes stale the next time a unit is added.

    It already did: unit 01 said "the seventeen units after this one" while
    there were twenty-one. The count belongs to the course, which can count
    itself, so no unit should carry a copy of it.
    """
    blobs = [unit.title, unit.failure, unit.detection, unit.builds_on, *unit.brief]
    for probe in unit.probes:
        blobs += [probe.asks, probe.because, *(c.label for c in probe.choices)]
    blobs += [unit.exercise.asks, unit.exercise.fixture_note, unit.exercise.because]
    offenders = [m.group(0) for b in blobs for m in WRITTEN_NUMBERS.finditer(b)]
    assert not offenders, (
        f"{unit.slug} writes the course length into its prose: {offenders}. "
        "Say 'every unit after this one' instead, and let the course count."
    )

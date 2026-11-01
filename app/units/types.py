"""Shared shapes for a curriculum unit.

The curriculum itself is one module per unit in this package. See __init__.py
for the registry and judges.py for a worked example.

A unit is four steps, in this order, and the order is the whole point:

A unit is not an article. It is four steps, in this order, and the order is the
whole point:

1. BRIEF    what goes wrong in production, with the measured numbers
2. PREDICT  calibration probes you answer with a confidence, before any answer
            is shown, so being confidently wrong costs you the same way it does
            in a teardown
3. DETECT   a fixture shipped with the unit, and a measurement you implement
            yourself and post back, checked against a known label
4. REVIEW   what you got right, where your confidence was off, and the primary
            source if you want to go further

The content comes from docs/research/engineering-failure-modes.md, which carries
verified numbers and citations. Nothing here is invented: every figure in a
briefing traces to a source listed on the unit.

Units are data, not database rows, because they are authored content that ships
with the app. What the user produces (probe answers, exercise results) is stored,
because that is his record.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Part:
    """One part of the course: a group of units you take together.

    Parts exist because a long flat list of units is a reference work, not a
    course. A reader needs to know what a group of units is for, and why it
    comes after the one before it rather than at the end.

    The count is deliberately not written here. It has changed three times and
    every hardcoded copy of it went stale in a different file.

    `builds_on` is the sentence that earns the order. If a part cannot say what
    it needs from the part before it, the order is arbitrary and should change.

    `role_asks` is what the target role expects of this part, in plain words.
    It is a description rather than a quotation: the posting itself is not
    stored in this repository, so nothing here is presented as its exact text.
    """

    slug: str
    number: int
    title: str
    purpose: str
    builds_on: str
    role_asks: tuple[str, ...]


@dataclass(frozen=True)
class Choice:
    key: str
    label: str


@dataclass(frozen=True)
class Probe:
    """One calibration probe. A question, options, and the answer it hides.

    `because` is shown only after he commits, and it explains why the answer is
    what it is rather than just asserting it.
    """

    id: str
    asks: str
    choices: tuple[Choice, ...]
    answer: str
    because: str


@dataclass(frozen=True)
class Exercise:
    """The hands-on half. He implements the detection and posts the number.

    The app does not run his code: the fixture is a file in the repo, he writes
    the measurement himself, and posts the result the same way a harness posts a
    cycle run. `expected` is the known label, and `tolerance` allows for
    floating point rather than for sloppiness.
    """

    asks: str
    fixture_path: str
    fixture_note: str
    starter: str
    metric: str
    expected: float
    tolerance: float
    because: str


@dataclass(frozen=True)
class Unit:
    """One unit of the curriculum.

    There is deliberately no reading time on this type. An earlier version
    carried one, and nobody had measured it: the number was invented and then
    copied into every unit. A figure with no measurement behind it is the exact
    thing these units teach a reader to catch, so it has no place in them.

    If a reader ever needs an estimate of effort, give them something counted,
    such as the number of probes.

    `part` is the slug of the Part this unit belongs to, and `number` is its
    place in the whole course. The two are kept consistent by a test rather
    than by care: unit numbers run 1 upward with no gaps, and they never cross
    a part boundary out of order.
    """

    slug: str
    number: int
    part: str
    title: str
    failure: str
    detection: str
    brief: tuple[str, ...]
    probes: tuple[Probe, ...]
    exercise: Exercise
    sources: tuple[str, ...] = field(default_factory=tuple)
    builds_on: str = ""
    """What this unit needs from the units before it, in one sentence.

    `Part.builds_on` earns a part its place in the order. Without the same
    field on a unit, the units inside a part are an unordered bag: nothing in
    the data says unit 05 needs unit 04, so a reader meets a pile of separate
    failure modes and no course.

    The rule is the same one the parts follow. If a unit cannot say what it
    needs from the ones before it, it is in the wrong place, and the order
    changes rather than the sentence. Unit 01 is the exception and says so,
    because something has to be first.

    tests/test_course_order.py holds this to the numbering, so a unit cannot
    claim to build on something a reader has not reached yet.
    """

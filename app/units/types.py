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
    slug: str
    number: int
    title: str
    failure: str
    detection: str
    minutes: int
    brief: tuple[str, ...]
    probes: tuple[Probe, ...]
    exercise: Exercise
    sources: tuple[str, ...] = field(default_factory=tuple)

"""Checkpoints: the measurement broken into the steps you actually take.

One exercise per unit means one moment of feedback. You either reach the
number or you do not, and a wrong answer tells you nothing about which of the
four decisions behind it went the other way. A course that checks you once per
lesson is a quiz with extra steps.

So a measurement is broken into the quantities you have to settle on the way
to it. For the judge unit that is: how many pairs are there, how many flipped,
and what share is that. Each is checked on its own, each is a number you can
print from the fixture, and the order of them is the order the thinking goes.

These live here rather than on the unit for one reason: a checkpoint is a
property of the measurement, not of the writing, and keeping them apart means
adding one never risks a unit's prose, its figures or its sources. The key is
the unit slug.

Every `expected` here is computed from the real fixture, never typed. The
test for this module recomputes each one and fails if a fixture changes
underneath it.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Checkpoint:
    """One quantity on the way to the answer.

    `asks` is the question in plain words. `expected` is the number, with a
    `tolerance` that allows for floating point and not for sloppiness.
    `because` says what settling this one tells you, and is shown after.
    """

    asks: str
    expected: float
    tolerance: float
    because: str


# Keyed by unit slug. A unit with no entry simply has no checkpoints, which
# is a gap rather than an error, and tests/test_checkpoints.py reports which
# units are still in that state.
CHECKPOINTS: dict[str, tuple[Checkpoint, ...]] = {}


def for_unit(slug: str) -> tuple[Checkpoint, ...]:
    return CHECKPOINTS.get(slug, ())


def covered() -> set[str]:
    return {slug for slug, steps in CHECKPOINTS.items() if steps}

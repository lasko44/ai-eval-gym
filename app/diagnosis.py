"""Name the mistake behind a wrong number, instead of saying it is wrong.

"That does not match" is where the learning stops. A measurement is a chain
of small decisions, and a number that misses almost always misses because one
of them went a particular way. Telling somebody which one is the difference
between an exercise and a guessing game.

Most wrong answers in this course are not random. They are one of a handful
of misreadings that recur across every unit, because they come from the shape
of the arithmetic rather than from the subject:

  the count instead of the rate      37 where 0.185 was wanted
  the rate instead of the count      0.185 where 37 was wanted
  the complement                     0.815, having measured agreement when
                                     the question asked about disagreement
  a percentage for a fraction        18.5 where 0.185 was wanted
  the mean where a tail was asked    a number near the average of a spread

So those are detected arithmetically, with no per-unit authoring, and they
cover the common cases on day one. A unit may add its own entries for the
mistakes that are particular to its subject, and those are the ones worth
writing by hand.

Nothing here tells the reader the answer. Each message names the decision
that went the other way and hands the question back.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Misreading:
    """One wrong answer worth recognising, and what it means."""

    name: str
    says: str


def _close(a: float, b: float, tolerance: float) -> bool:
    return abs(a - b) <= max(tolerance, abs(b) * 1e-9)


def diagnose(
    got: float,
    expected: float,
    tolerance: float,
    *,
    population: int | None = None,
    extra: tuple[tuple[float, Misreading], ...] = (),
) -> Misreading | None:
    """What the reader probably did, or None when it is not recognisable.

    `population` is the row count of the fixture, which is what turns a rate
    into a count and back. `extra` lets a unit name the misreadings specific
    to its own subject, checked before the generic ones because a unit knows
    its own ground better.

    Returning None is the honest answer most of the time. A number that is
    simply off by an unrecognisable amount gets no explanation, because a
    guess at the cause is worse than silence here: it sends somebody to fix
    the thing you named rather than the thing they did.
    """
    for value, reading in extra:
        if _close(got, value, tolerance):
            return reading

    if _close(got, 1 - expected, tolerance):
        return Misreading(
            "the complement",
            "That is one minus the answer. You measured the cases that "
            "agreed, or stayed, or passed, where the question asks about the "
            "ones that did the opposite.",
        )

    if _close(got, expected * 100, max(tolerance * 100, 0.01)):
        return Misreading(
            "a percentage where a fraction was asked",
            "That is the right measurement reported as a percentage. The "
            "fixture's label is a fraction between 0 and 1.",
        )

    if _close(got, expected / 100, tolerance / 100 or 1e-9):
        return Misreading(
            "a fraction where a percentage was asked",
            "That is the right measurement divided by a hundred.",
        )

    if population:
        if population and _close(got, expected * population, max(tolerance * population, 0.5)):
            return Misreading(
                "the count instead of the rate",
                f"That is how many rows, out of {population}. The question "
                "asks what share of them, so it needs dividing by the "
                "number you looked at.",
            )
        if expected and _close(got, population / expected if expected else 0, 0.5):
            return Misreading(
                "the denominator and the numerator swapped",
                "That is the reciprocal of the answer, scaled by the row "
                "count. Check which quantity is on top.",
            )

    if expected and _close(got, -expected, tolerance):
        return Misreading(
            "the sign",
            "The size is right and the direction is not. Check which of the "
            "two quantities you subtracted from which.",
        )

    if expected and _close(got, expected * 2, tolerance * 2):
        return Misreading(
            "double counting",
            "That is twice the answer. A pair, a both-ways comparison or a "
            "two-sided test is probably being counted once per side.",
        )

    if expected and _close(got, expected / 2, max(tolerance, abs(expected) * 1e-6)):
        return Misreading(
            "half the answer",
            "That is half of it. Something is being counted once where it "
            "happens on both sides, or a denominator is twice what it "
            "should be.",
        )

    return None


def fixture_population(data) -> int | None:
    """How many rows a fixture holds, for the count-versus-rate check.

    A list is its own length. A dict is the length of its longest list,
    which is the row count in every fixture shape this course ships. Anything
    else returns None rather than a number that would be wrong.
    """
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        lengths = [len(v) for v in data.values() if isinstance(v, list)]
        return max(lengths) if lengths else None
    return None

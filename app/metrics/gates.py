"""Release-gate metrics: whether a pass/fail threshold survives being asked
the same question twice.

A gate turns a score into a decision, and a decision is only worth as much as
its stability. These functions measure the decision, not the score, because a
suite whose score wobbles by a tenth of a point is harmless until a threshold
is drawn through the middle of the wobble.
"""


def gate_flip_rate(scores: list[float], threshold: float) -> float:
    """Fraction of identical runs whose gate verdict contradicts the majority.

    Typical use: `scores` is the same unchanged eval suite run many times, and
    `threshold` is the number the release gate compares against. A run passes
    when its score is greater than or equal to the threshold, matching the way
    a gate is normally written. The result is the share of runs that would have
    decided the opposite of what most runs decided.

    0.0 means every run agreed, so the gate is reading signal. Anything above
    0.0 means the gate is partly reading noise, and the value is the rate at
    which it contradicts itself on identical input. The maximum is 0.5, the
    perfect coin flip, reached when the runs split evenly.

    An empty list returns 0.0: no runs cannot disagree. A single run also
    returns 0.0, since one verdict is unanimous by itself, which is exactly the
    false confidence this metric exists to expose.
    """
    if not scores:
        return 0.0
    passing = sum(1 for s in scores if s >= threshold)
    minority = min(passing, len(scores) - passing)
    return minority / len(scores)

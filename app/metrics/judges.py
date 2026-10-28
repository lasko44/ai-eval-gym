"""Judge-stability metrics: does an evaluator's verdict change when something
about the evaluation that should not matter changes, such as swapping the
order two candidates were shown in.
"""


def flip_rate(first: list[str], swapped: list[str]) -> float:
    """Positionwise disagreement rate between two equal-length orderings.

    Typical use: `first` is a judge's verdicts in one presentation order
    and `swapped` is the same judge's verdicts with something swapped (for
    example, which candidate was shown first). flip_rate is the fraction of
    positions where the two verdicts differ: for ["A", "A", "B"] against
    ["A", "B", "B"], positions 0 and 2 agree and position 1 disagrees, so
    the rate is 1/3.

    The two lists must be the same length: comparing "position i" only
    means something when both sequences have a position i, so a length
    mismatch raises ValueError rather than guessing an alignment (zipping
    to the shorter length, for example, would silently ignore the judge's
    remaining verdicts).

    Two empty sequences return 0.0: there are no positions to disagree on,
    so there are zero disagreements out of zero comparisons, which this
    treats as perfect agreement rather than raising a division error.
    """
    if len(first) != len(swapped):
        raise ValueError(
            f"flip_rate requires equal-length sequences, got {len(first)} and "
            f"{len(swapped)}"
        )
    if not first:
        return 0.0
    disagreements = sum(1 for a, b in zip(first, swapped) if a != b)
    return disagreements / len(first)

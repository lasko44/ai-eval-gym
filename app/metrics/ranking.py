"""Rank-agreement metrics: when two scorings of the same candidates disagree
about the numbers, do they still agree about the order.

The distinction matters because the two questions have different answers and
different consequences. A scoring that inflates every candidate by the same
amount is useless for "how good is it" and perfectly sound for "which one do
we ship". Reporting one when you measured the other is a whole class of
mistake.
"""


def _average_ranks(scores: list[float]) -> list[float]:
    """Ranks of `scores`, smallest first, with ties sharing their mean rank.

    Ties have to share a rank rather than take an arbitrary order, because the
    order within a tie is an artifact of how the list happened to be built. Two
    candidates on 0.5 occupying ranks 3 and 4 get 3.5 each, so neither is
    credited with beating the other.
    """
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    position = 0
    while position < len(order):
        run_end = position
        while (
            run_end + 1 < len(order)
            and scores[order[run_end + 1]] == scores[order[position]]
        ):
            run_end += 1
        shared = (position + run_end) / 2 + 1
        for index in order[position : run_end + 1]:
            ranks[index] = shared
        position = run_end + 1
    return ranks


def rank_correlation(first: list[float], second: list[float]) -> float:
    """Spearman rank correlation between two scorings of the same candidates.

    Typical use: `first` is every model's score under your normal evaluation
    and `second` is the same models scored a second way (on paraphrased items,
    on a held-out twin, by a different judge). The result says whether the two
    scorings put the models in the same order, and says nothing at all about
    whether they agree on the scores themselves.

    Returns 1.0 for identical orderings, -1.0 for exactly reversed ones, and
    0.0 for no monotonic relationship. Position i of each list must describe
    the same candidate, so the lists must be equal length and a mismatch raises
    ValueError rather than truncating to the shorter one.

    Fewer than two candidates returns 0.0. One candidate cannot be in an order,
    so there is no agreement to report and none is invented.

    When every candidate in a list ties, that list carries no ordering, so the
    result is 0.0 rather than a division error.
    """
    if len(first) != len(second):
        raise ValueError(
            f"rank_correlation requires equal-length sequences, got "
            f"{len(first)} and {len(second)}"
        )
    n = len(first)
    if n < 2:
        return 0.0

    a = _average_ranks(first)
    b = _average_ranks(second)
    mean = (n + 1) / 2
    da = [x - mean for x in a]
    db = [y - mean for y in b]

    covariance = sum(x * y for x, y in zip(da, db))
    spread_a = sum(x * x for x in da) ** 0.5
    spread_b = sum(y * y for y in db) ** 0.5
    if spread_a == 0 or spread_b == 0:
        return 0.0
    return covariance / (spread_a * spread_b)

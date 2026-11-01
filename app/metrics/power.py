"""Power metrics: how big a difference an eval set of a given size can even
see.

Every other metric in this package answers "what did I measure". These answer
"could I have measured it", which has to come first and almost never does. An
eval set has a floor below which it returns noise with a decimal point on it,
and that floor is set by the item count before anybody runs anything.
"""

from statistics import NormalDist


def minimum_detectable_effect(
    n: int,
    baseline: float,
    power: float = 0.80,
    alpha: float = 0.05,
) -> float:
    """Smallest accuracy difference an eval of `n` items can reliably detect.

    Typical use: you have a 120-item eval set, your current model scores 0.78,
    and a candidate scores 0.81. Before celebrating the 3 points, ask this
    function what the smallest difference is that 120 items could have
    distinguished from noise. If the answer is larger than 0.03, the 3 points
    is not a result.

    `baseline` is the current accuracy, which sets the variance: a system at
    0.5 is noisier per item than one at 0.95, so the same item count buys less
    resolution in the middle. `power` is the chance of detecting a real
    difference of exactly this size, conventionally 0.80. `alpha` is the
    false-positive rate, conventionally 0.05, two-sided.

    This uses the normal approximation for two independent proportions. An
    eval that scores both models on the SAME items is paired, and pairing is
    more sensitive, so the real floor is somewhat below what this returns.
    That is the safe direction to be wrong in for a gate: the number here is a
    floor on the floor, and a difference below it is noise under any analysis.

    Raises ValueError on an item count below 1, a baseline outside [0, 1], or
    a power or alpha outside (0, 1), because each of those produces a
    confident number from a meaningless question.
    """
    if n < 1:
        raise ValueError(f"minimum_detectable_effect needs at least 1 item, got {n}")
    if not 0.0 <= baseline <= 1.0:
        raise ValueError(f"baseline must be within [0, 1], got {baseline}")
    if not 0.0 < power < 1.0:
        raise ValueError(f"power must be within (0, 1), got {power}")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be within (0, 1), got {alpha}")

    normal = NormalDist()
    z_alpha = normal.inv_cdf(1 - alpha / 2)
    z_power = normal.inv_cdf(power)
    variance = 2 * baseline * (1 - baseline) / n
    return (z_alpha + z_power) * variance**0.5

"""Calibration metrics: not "was the prediction right" but "was the stated
confidence justified by how often calls like it actually come true".
"""


def brier_score(pairs: list[tuple[float, bool]]) -> float:
    """Mean squared error between stated probability and actual outcome.

    Each pair is (probability_predicted, outcome_happened). The outcome is
    scored as 1.0 if it happened and 0.0 if it did not, and the score is
    the average of (probability - outcome) ** 2 across all pairs.

    0.0 means perfect calibration (every call matched its stated
    confidence exactly). 1.0 is the worst possible score: maximally
    confident and completely wrong. A score of 0.0 or 1.0 for a single
    pair at probability 0.0 or 1.0 is an exact value, not an edge case to
    special-case: both ends of the probability scale are ordinary, valid
    input.

    An empty list raises ValueError instead of returning 0.0. A Brier score
    of 0.0 means "perfectly calibrated", and this app exists to tell a user
    the truth about their calibration, so reporting a perfect score for "no
    predictions were made" would be the one lie this measuring instrument
    must never tell. Callers that need to represent "nothing resolved yet"
    should use a separate optional value (for example brier: float | None)
    rather than calling this function with an empty list.

    A probability outside the closed interval [0.0, 1.0] raises ValueError.
    Probabilities outside that range are not a different, still-meaningful
    calibration claim: they are malformed input, and silently clamping them
    would hide a bug in the caller's harness instead of surfacing it.
    """
    if not pairs:
        raise ValueError(
            "brier_score requires at least one prediction; an empty list "
            "has nothing to measure calibration against"
        )
    for probability, _ in pairs:
        if not 0.0 <= probability <= 1.0:
            raise ValueError(
                f"probability {probability!r} is outside the valid range [0.0, 1.0]"
            )
    squared_errors = (
        (probability - (1.0 if outcome else 0.0)) ** 2 for probability, outcome in pairs
    )
    return sum(squared_errors) / len(pairs)

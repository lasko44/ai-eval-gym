"""Scoring: what the sealed prediction turned out to be worth.

This is the step the rest of the app exists to reach. A claim was sealed
before the harness ran, so by the time the measurements arrive there is no
way to quietly move the goalposts, and the score here is the honest answer
to "how good is this person at reading an AI system's weaknesses".

Three numbers come out of a cycle, and they say different things.

Brier score: the calibration number, the mean of (probability - outcome) ** 2
over the claims that actually resolved. 0.0 is perfect, 1.0 is the worst
possible. Low is good. It punishes confidence that was not earned in both
directions: being sure of something false and being sure something is not a
problem when it is.

coverage: the share of the sealed claims the harness actually put to the
test. A beautiful Brier score over one claim out of six says far more about
what was measured than about what was predicted, so coverage is reported
next to it rather than hidden.

resolved and unresolved: the counts behind coverage. An unresolved claim is
one whose metric no harness run reported. It is never scored as correct and
never enters the Brier computation at all, because a prediction nothing
tested is not a prediction that came true.
"""

import operator
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.metrics import brier_score
from app.models import Claim, Cycle

CORRECT = "correct"
WRONG = "wrong"
UNRESOLVED = "unresolved"

# The comparator each claim stores, as the function that applies it. Every
# one of these is called with the MEASURED value first and the claim's
# threshold second, because a claim reads "metric comparator threshold":
# "recall_at_5 lt 0.5" is the prediction that the measured recall comes in
# below 0.5. Swapping the operands would invert every verdict in the app
# while still producing output that looks entirely reasonable.
_COMPARISONS = {
    "lt": operator.lt,
    "lte": operator.le,
    "gt": operator.gt,
    "gte": operator.ge,
}


@dataclass(frozen=True)
class CycleScore:
    """One cycle's score. See this module's docstring for what each means.

    brier is None, never 0.0, when no claim resolved: 0.0 is a perfect
    calibration score, and reporting one for a cycle that measured nothing
    would be the single most flattering lie this app could tell.
    """

    brier: float | None
    resolved: int
    unresolved: int
    coverage: float


def resolve_claim(claim: Claim, measurements: dict[str, float]) -> str:
    """Return "correct", "wrong" or "unresolved" for one claim.

    measurements maps metric name to measured value. A claim whose metric is
    not in there is "unresolved": the harness never measured the thing the
    claim is about, so the claim was neither confirmed nor refuted.

    Otherwise the claim's comparator is applied with the measured value on
    the left and the claim's threshold on the right, which is the direction
    the claim is written in.
    """
    if claim.metric not in measurements:
        return UNRESOLVED
    # A comparator outside COMPARATORS raises KeyError here on purpose. There
    # is no sensible verdict for a claim whose falsification test cannot be
    # applied, and guessing one would report a verdict that was never tested.
    compare = _COMPARISONS[claim.comparator]
    measured = measurements[claim.metric]
    return CORRECT if compare(measured, float(claim.threshold)) else WRONG


def _latest_measurements(cycle: Cycle) -> dict[str, float]:
    """Every metric this cycle has measured, with the latest run winning.

    A cycle can be measured more than once: the loop is predict, measure,
    score, and a user who fixes their harness and runs it again means the
    newer number. cycle.runs is ordered by id, so iterating in that order
    and letting later runs overwrite earlier ones per metric name is
    latest-wins.
    """
    values: dict[str, float] = {}
    for run in cycle.runs:
        for measurement in run.measurements:
            values[measurement.metric] = measurement.value
    return values


def score_cycle(session: Session, cycle_id: int) -> CycleScore:
    """Score one cycle's sealed claims against what its harness measured.

    Each claim is resolved, the resolved ones are scored for calibration,
    and the unresolved ones are counted but kept out of the Brier score.

    The pairs handed to brier_score are (stated probability, did it turn out
    true). A claim that resolved correct pairs with True and one that
    resolved wrong pairs with False. That direction is the whole meaning of
    the number: reversed, a well-calibrated user would be told they are
    badly calibrated, and a badly calibrated one would be congratulated.
    """
    cycle = session.get(Cycle, cycle_id)
    if cycle is None:
        raise ValueError(
            f"Cycle {cycle_id} does not exist, so there is nothing to score."
        )

    measurements = _latest_measurements(cycle)
    pairs: list[tuple[float, bool]] = []
    resolved = 0
    unresolved = 0
    for claim in cycle.claims:
        verdict = resolve_claim(claim, measurements)
        if verdict == UNRESOLVED:
            unresolved += 1
            continue
        resolved += 1
        pairs.append((float(claim.probability), verdict == CORRECT))

    total = resolved + unresolved
    return CycleScore(
        # Guarded rather than passed through: brier_score raises on an empty
        # list by design, and "nothing resolved" is reported as None.
        brier=brier_score(pairs) if pairs else None,
        resolved=resolved,
        unresolved=unresolved,
        # A cycle with no claims at all has nothing to cover, so 0.0 rather
        # than a division by zero.
        coverage=resolved / total if total else 0.0,
    )

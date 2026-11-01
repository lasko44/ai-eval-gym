"""Progression: what he has earned, what is still locked, and how honest his
confidence has been.

This module invents no data. Every number here is derived from rows already
written by ProbeAttempt and ExerciseAttempt, so progression can be rebuilt from
the database at any time and there is no second source of truth to drift.

Three deliberate choices, because a scoreboard teaches whatever it rewards.

First, **the first attempt is the only one that counts for calibration**. A
probe answered after reading the explanation is not a prediction, so counting
it would reward rereading and call it learning.

Second, **parts unlock in order**. Part.builds_on and Unit.builds_on claim the
course has a spine. A reader who can open part 5 on day one proves the claim
was decorative. The lock is what makes the sentence true.

Third, **completion and calibration are scored separately and never added
together**. Doing the work and knowing the thing are different, and a single
blended number lets a reader buy one with the other. Rank comes from mastery.
Calibration stands alone and can be bad while rank is high, which is exactly
the state a reader needs to be able to see.
"""

from dataclasses import dataclass, field

from app.models import ExerciseAttempt, ProbeAttempt

# Rank is earned by mastering whole parts, so it tracks how far through the
# system a reader can actually work rather than how many pages they opened.
RANKS: tuple[str, ...] = (
    "Visitor",
    "Observer",
    "Analyst",
    "Reviewer",
    "Auditor",
    "Examiner",
    "Teardown lead",
)


@dataclass(frozen=True)
class UnitProgress:
    """One unit's state, from the attempts on record."""

    slug: str
    probes_total: int
    probes_answered: int
    exercise_passed: bool
    first_attempt_correct: int

    @property
    def mastered(self) -> bool:
        """Every probe committed and the detection implemented and posted.

        Mastery is not "got them right". A probe you were wrong about still
        counts, because the probe's job is to extract a prediction, and the
        cost of being wrong is paid in the calibration score instead. Making
        mastery require correctness would push a reader to guess the option
        that looks safest rather than the one they believe.
        """
        return self.probes_answered >= self.probes_total and self.exercise_passed

    @property
    def started(self) -> bool:
        return self.probes_answered > 0 or self.exercise_passed


@dataclass(frozen=True)
class Calibration:
    """How well stated confidence matched what actually happened."""

    predictions: int
    brier: float | None
    score: int | None
    overconfidence: float | None
    buckets: tuple[tuple[str, int, float, float], ...] = field(default_factory=tuple)

    @property
    def verdict(self) -> str:
        if self.score is None:
            return "No predictions yet."
        if self.overconfidence is None:
            return "Not enough predictions to judge."
        if self.overconfidence > 0.10:
            return "Overconfident. You are surer than you are right."
        if self.overconfidence < -0.10:
            return "Underconfident. You know more than you are claiming."
        return "Well calibrated. Your confidence is carrying real information."


def unit_progress(session, unit) -> UnitProgress:
    """Attempts on record for one unit, reduced to its state."""
    attempts = (
        session.query(ProbeAttempt)
        .filter(ProbeAttempt.unit_slug == unit.slug)
        .order_by(ProbeAttempt.created_at.asc(), ProbeAttempt.id.asc())
        .all()
    )
    first_by_probe: dict[str, ProbeAttempt] = {}
    for attempt in attempts:
        first_by_probe.setdefault(attempt.probe_id, attempt)

    passed = (
        session.query(ExerciseAttempt)
        .filter(
            ExerciseAttempt.unit_slug == unit.slug,
            ExerciseAttempt.correct.is_(True),
        )
        .first()
        is not None
    )

    return UnitProgress(
        slug=unit.slug,
        probes_total=len(unit.probes),
        probes_answered=len(first_by_probe),
        exercise_passed=passed,
        first_attempt_correct=sum(1 for a in first_by_probe.values() if a.correct),
    )


def _first_attempts(session) -> list[ProbeAttempt]:
    """One attempt per probe, the earliest, across the whole course."""
    attempts = (
        session.query(ProbeAttempt)
        .order_by(ProbeAttempt.created_at.asc(), ProbeAttempt.id.asc())
        .all()
    )
    seen: dict[tuple[str, str], ProbeAttempt] = {}
    for attempt in attempts:
        seen.setdefault((attempt.unit_slug, attempt.probe_id), attempt)
    return list(seen.values())


def calibration(session) -> Calibration:
    """Brier score over first attempts, plus where the confidence went wrong.

    `score` is the Brier score turned into something a person can read: 100 is
    perfect, 0 is maximally confident and maximally wrong. It is presentation
    only, and `brier` is kept beside it so the real number is never lost.

    `overconfidence` is the gap between mean stated confidence and the share
    actually correct. Positive means claiming more certainty than the record
    supports. This is the single most useful number on the page, because it is
    the one a reader can act on tomorrow.
    """
    attempts = _first_attempts(session)
    if not attempts:
        return Calibration(predictions=0, brier=None, score=None, overconfidence=None)

    brier = sum((a.probability - (1.0 if a.correct else 0.0)) ** 2 for a in attempts)
    brier /= len(attempts)

    mean_confidence = sum(a.probability for a in attempts) / len(attempts)
    share_correct = sum(1 for a in attempts if a.correct) / len(attempts)

    edges = ((0.0, 0.6, "50 to 60"), (0.6, 0.8, "60 to 80"), (0.8, 1.01, "80 to 100"))
    buckets = []
    for low, high, label in edges:
        inside = [a for a in attempts if low <= a.probability < high]
        if not inside:
            continue
        buckets.append(
            (
                label,
                len(inside),
                sum(a.probability for a in inside) / len(inside),
                sum(1 for a in inside if a.correct) / len(inside),
            )
        )

    return Calibration(
        predictions=len(attempts),
        brier=brier,
        score=round((1 - brier) * 100),
        overconfidence=(
            mean_confidence - share_correct if len(attempts) >= 5 else None
        ),
        buckets=tuple(buckets),
    )


def track_record_at(session, probability: float, width: float = 0.1) -> dict | None:
    """How often first answers near this confidence turned out right.

    Shown beside a probe the moment it is answered, because that is where the
    lesson is cheap. A calibration table on the home page tells you that you
    are overconfident in general. This tells you that the last nine times you
    said eighty percent you were right five times, while you are still looking
    at the question you just said it about.

    `width` is the half-window, so 0.1 pools everything within ten points.
    Pooling is necessary: nobody answers the same probability often enough for
    an exact match to say anything, and a readout built on two attempts would
    be the error this course exists to teach.

    Returns None below five comparable attempts, rather than a number that
    cannot carry the claim.
    """
    nearby = [
        a
        for a in _first_attempts(session)
        if abs(a.probability - probability) <= width
    ]
    if len(nearby) < 5:
        return None
    correct = sum(1 for a in nearby if a.correct)
    return {
        "claimed": probability,
        "attempts": len(nearby),
        "correct": correct,
        "actual": correct / len(nearby),
        "overconfident": (correct / len(nearby)) + 0.1 < probability,
    }


def streak(session) -> int:
    """Consecutive first attempts correct, counting back from the latest.

    Correctness rather than calibration, because a streak has to be legible at
    a glance and a run of well-calibrated wrong answers is not something to
    celebrate on a card.
    """
    attempts = sorted(
        _first_attempts(session), key=lambda a: (a.created_at, a.id), reverse=True
    )
    run = 0
    for attempt in attempts:
        if not attempt.correct:
            break
        run += 1
    return run


def review_queue(session, course) -> list[dict]:
    """Probes whose first answer was wrong, worst miss first.

    A course that shows you the explanation once and never asks again teaches
    recognition, not recall. You read "of course, position bias", feel it
    land, and cannot reproduce it a week later.

    Ordering is by how wrong the prediction was, not by when it happened. A
    probe you were 95 percent sure of and got wrong is a belief that needs
    correcting; one you guessed at and missed is a gap you already knew about.
    The first is more urgent and the squared error says so, which is the same
    arithmetic the Brier score uses on the rest of the course.

    Re-answering never touches the calibration score, because that reads first
    attempts only. Review is free to practise against, which is the point: a
    reader who cannot revisit a miss without damaging a number will avoid the
    miss.
    """
    by_unit = {unit.slug: unit for _, units in course for unit in units}
    misses = []
    for attempt in _first_attempts(session):
        if attempt.correct:
            continue
        unit = by_unit.get(attempt.unit_slug)
        if unit is None:
            continue
        probe = next((p for p in unit.probes if p.id == attempt.probe_id), None)
        if probe is None:
            continue
        misses.append(
            {
                "unit": unit,
                "probe": probe,
                "said": attempt.probability,
                "chose": attempt.choice,
                "error": (attempt.probability - 0.0) ** 2,
                "confident": attempt.probability >= 0.8,
            }
        )
    return sorted(misses, key=lambda m: m["error"], reverse=True)


def part_states(session, course) -> list[dict]:
    """Every part with its units, mastery count, and whether it is unlocked.

    A part opens when the one before it is fully mastered. Part 1 is always
    open. This is Part.builds_on enforced rather than asserted: a reader cannot
    reach the retrieval units until the instrument units are behind them.
    """
    states = []
    previous_complete = True
    for part, units in course:
        progress = [unit_progress(session, unit) for unit in units]
        mastered = sum(1 for p in progress if p.mastered)
        states.append(
            {
                "part": part,
                "units": list(zip(units, progress)),
                "mastered": mastered,
                "total": len(units),
                "complete": bool(units) and mastered == len(units),
                "unlocked": previous_complete,
            }
        )
        previous_complete = states[-1]["complete"]
    return states


def rank(states: list[dict]) -> tuple[str, int, int]:
    """Current rank, parts mastered, and parts remaining to the next rank."""
    complete = sum(1 for s in states if s["complete"])
    name = RANKS[min(complete, len(RANKS) - 1)]
    remaining = 0 if complete >= len(states) else 1
    return name, complete, remaining


def badges(session, course) -> list[dict]:
    """Specific things done, named for the skill rather than the activity.

    A badge for "finished part 2" restates the progress bar. These name a
    capability a hiring manager would recognise, which is the only reason to
    put a badge on a page a single person looks at.
    """
    cal = calibration(session)
    states = part_states(session, course)
    all_progress = [p for s in states for _, p in s["units"]]

    passed = sum(1 for p in all_progress if p.exercise_passed)
    answered = sum(p.probes_answered for p in all_progress)

    earned = [
        {
            "name": "Instrument checked",
            "detail": "Mastered every unit in part 1 before measuring anything else.",
            "earned": states[0]["complete"] if states else False,
        },
        {
            "name": "Honest under pressure",
            "detail": "20 predictions on record with no sign of overconfidence.",
            "earned": (
                cal.predictions >= 20
                and cal.overconfidence is not None
                and abs(cal.overconfidence) <= 0.10
            ),
        },
        {
            "name": "Implementer",
            "detail": "Wrote and posted five detections that matched a known label.",
            "earned": passed >= 5,
        },
        {
            "name": "Full sweep",
            "detail": "Posted a passing detection for every unit in the course.",
            "earned": passed >= len(all_progress) and all_progress != [],
        },
        {
            "name": "Committed",
            "detail": "Answered 40 probes before seeing any of their explanations.",
            "earned": answered >= 40,
        },
    ]
    return earned

"""FastAPI application: routes only. Business logic stays in models/services
as later tasks add them.
"""

import math
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator

from app import glossary as vocabulary
from app import path as career
from app import progress as progression
from app import lesson as lessons
from app import runner as sandbox
from app import tour as guide
from app import units as curriculum
from app.db import get_session
from app.metrics import brier_score
from app.models import (
    COMPARATORS,
    Claim,
    Cycle,
    ExerciseAttempt,
    HarnessRun,
    Measurement,
    ProbeAttempt,
)
from app.scoring import _latest_measurements, resolve_claim, score_cycle
from app.sealing import SealError, seal_cycle

# Schema creation does not happen here. Run `python -m app.initdb` once
# against a fresh database before starting the app. Tests manage their own
# create/drop in conftest.py and do not depend on this either.
app = FastAPI(title="AI Eval Gym")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.globals["TOUR"] = guide


@app.get("/cycles")
def list_cycles(request: Request):
    session = get_session()
    try:
        cycles = session.query(Cycle).order_by(Cycle.id).all()
        return templates.TemplateResponse(
            request, "cycles.html", {"cycles": cycles}
        )
    finally:
        session.close()


@app.post("/cycles")
def create_cycle(
    target_name: str = Form(...),
    target_url: str = Form(...),
    question: str = Form(...),
):
    session = get_session()
    try:
        cycle = Cycle(
            target_name=target_name,
            target_url=target_url,
            question=question,
            stage="open",
        )
        session.add(cycle)
        session.commit()
        session.refresh(cycle)
        cycle_id = cycle.id
    finally:
        session.close()
    return RedirectResponse(url=f"/cycles/{cycle_id}", status_code=303)


@app.get("/cycles/{cycle_id}")
def show_cycle(request: Request, cycle_id: int):
    session = get_session()
    try:
        cycle = session.get(Cycle, cycle_id)
        if cycle is None:
            raise HTTPException(status_code=404, detail="Cycle not found")
        return templates.TemplateResponse(
            request, "cycle.html", {"cycle": cycle}
        )
    finally:
        session.close()


@app.get("/cycles/{cycle_id}/predict")
def show_prediction(request: Request, cycle_id: int):
    session = get_session()
    try:
        cycle = session.get(Cycle, cycle_id)
        if cycle is None:
            raise HTTPException(status_code=404, detail="Cycle not found")
        return templates.TemplateResponse(
            request,
            "predict.html",
            {"cycle": cycle, "comparators": COMPARATORS},
        )
    finally:
        session.close()


def _claim_from_form(
    cycle_id: int,
    text: str,
    metric: str,
    comparator: str,
    threshold: str,
    probability: str,
) -> Claim:
    """Build a Claim from raw form values, or raise 422.

    The form fields arrive as strings and are checked here rather than by
    FastAPI's own coercion so that every refusal says which part of the
    prediction is missing. A claim with no metric or no threshold has no
    falsification test attached, so it is refused: that refusal is what makes
    "retrieval is bad" impossible to seal.
    """
    text = text.strip()
    metric = metric.strip()
    comparator = comparator.strip()
    threshold = threshold.strip()
    probability = probability.strip()

    if not text:
        raise HTTPException(status_code=422, detail="A claim needs its own text.")
    if not metric:
        raise HTTPException(
            status_code=422,
            detail="A claim needs a metric, or there is no way to be shown wrong.",
        )
    if not threshold:
        raise HTTPException(
            status_code=422,
            detail="A claim needs a threshold, or there is no way to be shown wrong.",
        )
    if comparator not in COMPARATORS:
        raise HTTPException(
            status_code=422,
            detail=f"comparator must be one of: {', '.join(COMPARATORS)}.",
        )

    try:
        threshold_value = float(threshold)
    except ValueError:
        raise HTTPException(
            status_code=422, detail="threshold must be a number."
        ) from None
    if not math.isfinite(threshold_value):
        raise HTTPException(
            status_code=422, detail="threshold must be a finite number."
        )

    try:
        probability_value = float(probability)
    except ValueError:
        raise HTTPException(
            status_code=422, detail="probability must be a number."
        ) from None
    if not 0.0 <= probability_value <= 1.0:
        raise HTTPException(
            status_code=422,
            detail="probability must be between 0 and 1 inclusive.",
        )

    return Claim(
        cycle_id=cycle_id,
        text=text,
        metric=metric,
        comparator=comparator,
        threshold=threshold_value,
        probability=probability_value,
    )


@app.post("/cycles/{cycle_id}/claims")
def add_claim(
    cycle_id: int,
    text: str = Form(...),
    metric: str = Form(...),
    comparator: str = Form(...),
    threshold: str = Form(...),
    probability: str = Form(...),
):
    session = get_session()
    try:
        cycle = session.get(Cycle, cycle_id)
        if cycle is None:
            raise HTTPException(status_code=404, detail="Cycle not found")
        if cycle.stage != "open":
            # Refused, not ignored: a sealed prediction is the whole point.
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cycle {cycle_id} is {cycle.stage}. Its claims can no longer "
                    "be added to or edited."
                ),
            )
        session.add(
            _claim_from_form(cycle_id, text, metric, comparator, threshold, probability)
        )
        session.commit()
    finally:
        session.close()
    return RedirectResponse(url=f"/cycles/{cycle_id}/predict", status_code=303)


class RunPayload(BaseModel):
    """The JSON body a harness run posts.

    This is the one route in the app a machine calls rather than a browser
    form, so it takes JSON instead of the Form(...) fields used everywhere
    else.
    """

    notes: str
    measurements: dict[str, float]

    @field_validator("measurements")
    @classmethod
    def _measurements_must_be_finite(
        cls, value: dict[str, float]
    ) -> dict[str, float]:
        """Refuse NaN and Infinity, which otherwise score claims silently.

        Both reach this far by default and neither is caught downstream.
        Starlette's request.json() is json.loads, which accepts the bare
        NaN, Infinity and -Infinity tokens, pydantic's float allows them
        unless told not to, and Postgres double precision stores them. From
        there they resolve claims for real: a NaN loses every comparison, so
        every claim it touches resolves wrong, while an Infinity wins every
        gt and gte, so those claims resolve correct with a near-perfect
        Brier contribution. The bad value then persists into the published
        teardown as though a harness had measured it.

        The threshold side of a claim is already gated the same way in
        _claim_from_form, and the metrics in app.metrics.retrieval go out of
        their way to return 0.0 instead of 0/0, so this is the one remaining
        door. A harness that cannot produce a number has not measured
        anything, so the answer is a 422.

        HTTPException, not ValueError, and the difference is not cosmetic.
        A ValueError raised here becomes a pydantic validation error whose
        payload includes the offending input value, and FastAPI's default
        handler renders that payload with Starlette's JSONResponse, which
        calls json.dumps(allow_nan=False). Serializing a NaN or an Infinity
        then raises, so the client gets a 500 from the error handler instead
        of the 422 the refusal was meant to be. Established by probe, not
        assumed. Raising HTTPException instead keeps the non-finite value
        out of the response body entirely: pydantic lets an exception that
        is not a ValueError or AssertionError propagate untouched, and
        FastAPI's own HTTPException handler turns it into a 422 carrying
        just this message. That also makes the refusal read the same way as
        every other 422 in this file.
        """
        for metric, measured in value.items():
            if not math.isfinite(measured):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"measurement {metric!r} is {measured}, which is not "
                        "a finite number. A harness that cannot produce a "
                        "number has not measured anything: fix the harness "
                        "rather than reporting NaN or Infinity, because a "
                        "non-finite value resolves claims as if it were a "
                        "real measurement."
                    ),
                )
        return value


@app.get("/cycles/{cycle_id}/runs")
def show_runs(request: Request, cycle_id: int):
    session = get_session()
    try:
        cycle = session.get(Cycle, cycle_id)
        if cycle is None:
            raise HTTPException(status_code=404, detail="Cycle not found")
        return templates.TemplateResponse(
            request, "run.html", {"cycle": cycle}
        )
    finally:
        session.close()


@app.post("/cycles/{cycle_id}/runs", status_code=201)
def create_run(cycle_id: int, payload: RunPayload):
    session = get_session()
    try:
        cycle = session.get(Cycle, cycle_id)
        if cycle is None:
            raise HTTPException(status_code=404, detail="Cycle not found")
        if cycle.stage not in ("sealed", "measured"):
            # Refused, not ignored: predict-before-measure only holds if a
            # run cannot happen before the prediction is sealed, and a
            # scored cycle is final, the same way a seal is made once and
            # never redone.
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cycle {cycle_id} is {cycle.stage}. A harness run "
                    "requires a sealed prediction first, and a scored cycle "
                    "cannot be measured again."
                ),
            )
        run = HarnessRun(cycle_id=cycle_id, notes=payload.notes)
        session.add(run)
        session.flush()
        for metric, value in payload.measurements.items():
            session.add(Measurement(run_id=run.id, metric=metric, value=float(value)))
        cycle.stage = "measured"
        session.commit()
        run_id = run.id
    finally:
        session.close()
    return {"id": run_id}


@app.post("/cycles/{cycle_id}/seal")
def seal(cycle_id: int):
    session = get_session()
    try:
        seal_cycle(session, cycle_id)
    except SealError as exc:
        # One status for every refusal to seal. Each case (wrong stage, no
        # claims, no git repository, a dirty seal file) is a reason this cycle
        # cannot be sealed as it stands, and the message says which.
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    finally:
        session.close()
    return RedirectResponse(url=f"/cycles/{cycle_id}/predict", status_code=303)


@app.post("/cycles/{cycle_id}/score")
def score(request: Request, cycle_id: int):
    """Score a measured cycle and render the result.

    This renders score.html directly instead of redirecting to a page of its
    own, because the score is derived entirely from rows that already exist:
    there is nothing new to read back, and nothing is stored beyond the move
    to the scored stage.
    """
    session = get_session()
    try:
        cycle = session.get(Cycle, cycle_id)
        if cycle is None:
            raise HTTPException(status_code=404, detail="Cycle not found")
        if cycle.stage not in ("measured", "scored"):
            # Refused, not scored as all-unresolved: a cycle whose harness has
            # not run yet has no verdicts in it, and recording one would dress
            # "nothing was measured" up as a finding. A cycle already scored
            # may be scored again, because scoring is deterministic and reads
            # the same rows every time.
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cycle {cycle_id} is {cycle.stage}. Scoring requires a "
                    "harness run to measure the sealed claims against."
                ),
            )
        result = score_cycle(session, cycle_id)
        cycle.stage = "scored"
        session.commit()
        return templates.TemplateResponse(
            request, "score.html", {"cycle": cycle, "score": result}
        )
    finally:
        session.close()


def _require_scored_for_teardown(cycle: Cycle, cycle_id: int) -> None:
    """Refuse the teardown routes unless the cycle has been scored.

    A teardown without a score is not a teardown, and computing one on
    demand here would let a reader see a score before the cycle is formally
    scored through POST /cycles/{id}/score, blurring the predict-measure-
    score ordering the rest of the app protects. score_cycle itself has no
    stage guard, so this check is what keeps it from ever being called on an
    open, sealed or measured cycle.
    """
    if cycle.stage != "scored":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cycle {cycle_id} is {cycle.stage}. The teardown is only "
                "available once this cycle has been scored."
            ),
        )


def _run_rows(cycle: Cycle) -> list[dict]:
    """Every harness run on this cycle, in order, marking what scored.

    A cycle can be measured more than once, and app.scoring's
    _latest_measurements takes latest-run-wins per metric, so a second run
    reporting the same metric silently replaces the first run's number in
    the score. That rule is correct (a fixed harness means the newer
    number), but it leaves the measurement side rewritable with nothing in
    the published artifact to show it: the thresholds are visible on the
    predict page and the measured values on the runs page, so an author can
    see a claim resolved wrong and post a second run that resolves it
    correct instead. The seal makes the prediction tamper-evident; this
    listing is what makes the measurement tamper-evident, to the author and
    to any reader of the teardown.

    scored is True for exactly the measurement latest-run-wins actually
    picked for that metric. It is computed by the same iteration order
    _latest_measurements uses (runs by id, measurements within a run by
    id), with the last one seen winning, so the two can only ever agree.
    Every other reading of that metric is marked superseded and still
    printed with its value, because the displaced number is the
    information a reader needs in order to notice an overwrite.
    """
    scoring_measurement_id: dict[str, int] = {}
    for run in cycle.runs:
        for measurement in run.measurements:
            scoring_measurement_id[measurement.metric] = measurement.id

    return [
        {
            "run": run,
            "measurements": [
                {
                    "measurement": measurement,
                    "scored": scoring_measurement_id.get(measurement.metric)
                    == measurement.id,
                }
                for measurement in run.measurements
            ],
        }
        for run in cycle.runs
    ]


def _teardown_context(session, cycle: Cycle) -> dict:
    """Everything the teardown page and its markdown export both render.

    measurements comes from app.scoring's own latest-value-per-metric
    helper, reused here rather than rebuilt, so this page's idea of "the
    measured value" can never drift from what score_cycle itself scored
    against. Each claim's outcome uses resolve_claim directly, for the same
    reason: one place decides correct, wrong or unresolved.

    Claims scored wrong are included in this list exactly like the others,
    in cycle.claims order (the sealed order), not sorted, filtered or
    flagged apart. Whether the published markdown keeps them is the
    reader's decision, made by exporting or not, not a decision this
    function makes for them.

    runs carries every harness run, not only the latest, for the same
    reason: see _run_rows. Nothing in this context is an interpretation of
    how the author did. It is their claim text, their notes and the
    numbers.
    """
    measurements = _latest_measurements(cycle)
    claims = [
        {
            "claim": claim,
            "measured": measurements.get(claim.metric),
            "outcome": resolve_claim(claim, measurements),
        }
        for claim in cycle.claims
    ]
    score = score_cycle(session, cycle.id)
    return {
        "cycle": cycle,
        "claims": claims,
        "score": score,
        "runs": _run_rows(cycle),
    }


@app.get("/cycles/{cycle_id}/teardown")
def show_teardown(request: Request, cycle_id: int):
    session = get_session()
    try:
        cycle = session.get(Cycle, cycle_id)
        if cycle is None:
            raise HTTPException(status_code=404, detail="Cycle not found")
        _require_scored_for_teardown(cycle, cycle_id)
        context = _teardown_context(session, cycle)
        return templates.TemplateResponse(request, "teardown.html", context)
    finally:
        session.close()


@app.get("/cycles/{cycle_id}/teardown.md")
def export_teardown_markdown(cycle_id: int):
    session = get_session()
    try:
        cycle = session.get(Cycle, cycle_id)
        if cycle is None:
            raise HTTPException(status_code=404, detail="Cycle not found")
        _require_scored_for_teardown(cycle, cycle_id)
        context = _teardown_context(session, cycle)
        markdown = templates.get_template("teardown.md.jinja").render(context)
        return Response(content=markdown, media_type="text/markdown")
    finally:
        session.close()


# Units. The curriculum surface: read the failure, commit a prediction about it
# with a confidence, then implement the detection against a fixture and post the
# number. Probe calibration is tracked separately from teardown calibration, on
# purpose: probes are cheap and numerous and would otherwise dominate a pooled
# headline number.


def _first_attempt_per_probe(session, slug):
    """The first commit for each probe is the one that counts.

    Answering again after reading the explanation is allowed, because rereading
    a unit is useful, but it is not a prediction and it does not replace the
    original.
    """
    rows = (
        session.query(ProbeAttempt)
        .filter(ProbeAttempt.unit_slug == slug)
        .order_by(ProbeAttempt.id)
        .all()
    )
    first = {}
    for row in rows:
        first.setdefault(row.probe_id, row)
    return first


def _unit_progress(session, unit):
    first = _first_attempt_per_probe(session, unit.slug)
    pairs = [(a.probability, a.correct) for a in first.values()]
    passed = (
        session.query(ExerciseAttempt)
        .filter(ExerciseAttempt.unit_slug == unit.slug, ExerciseAttempt.correct.is_(True))
        .first()
        is not None
    )
    return {
        "answered": len(first),
        "total": len(unit.probes),
        "right": sum(1 for a in first.values() if a.correct),
        "brier": brier_score(pairs) if pairs else None,
        "exercise_passed": passed,
        "attempts": first,
    }


def _course_rows(session):
    """The whole course, grouped by part, with progress on every unit.

    One query pass per unit, built once here so the course home and the
    syllabus cannot disagree about what is finished.
    """
    groups = []
    for part, units in curriculum.COURSE:
        rows = [
            {"unit": unit, "progress": _unit_progress(session, unit)}
            for unit in units
        ]
        groups.append({"part": part, "rows": rows})
    return groups


def _is_finished(progress) -> bool:
    """A unit is finished when every probe is answered and the detection passed.

    Reading the briefing is not a step this app can observe, so it is not one
    this app claims to have measured.
    """
    return progress["answered"] == progress["total"] and progress["exercise_passed"]


def _course_state(groups):
    """Where the reader is, counted rather than estimated."""
    rows = [row for group in groups for row in group["rows"]]
    answered = sum(row["progress"]["answered"] for row in rows)
    probes = sum(row["progress"]["total"] for row in rows)
    pairs = [
        (a.probability, a.correct)
        for row in rows
        for a in row["progress"]["attempts"].values()
    ]
    next_row = next((row for row in rows if not _is_finished(row["progress"])), None)
    return {
        "units_finished": sum(1 for row in rows if _is_finished(row["progress"])),
        "units_total": len(rows),
        "probes_answered": answered,
        "probes_total": probes,
        "detections_passed": sum(
            1 for row in rows if row["progress"]["exercise_passed"]
        ),
        "brier": brier_score(pairs) if pairs else None,
        "next_unit": next_row["unit"] if next_row else None,
        "next_part": curriculum.part_of(next_row["unit"]) if next_row else None,
    }


def _game(session):
    """The progression layer, derived fresh from the attempts on record.

    Kept beside _course_state rather than folded into it. That one counts what
    has been opened; this one decides what has been earned, and the two use
    different rules on purpose: progression counts only first attempts.
    """
    states = progression.part_states(session, curriculum.COURSE)
    name, complete, _ = progression.rank(states)
    locked = next((s for s in states if not s["unlocked"]), None)
    return {
        "rank": name,
        "rank_index": complete,
        "ranks": progression.RANKS,
        "parts_complete": complete,
        "parts_total": len(states),
        "states": states,
        "calibration": progression.calibration(session),
        "streak": progression.streak(session),
        "badges": progression.badges(session, curriculum.COURSE),
        "first_locked": locked["part"] if locked else None,
    }


def _part_is_locked(session, unit) -> dict | None:
    """The part a reader still owes before this unit opens, or None.

    Returns the blocking part rather than a boolean so the page can say what
    to go and do, which is the only version of a lock that teaches anything.
    """
    states = progression.part_states(session, curriculum.COURSE)
    for index, state in enumerate(states):
        if state["part"].slug != unit.part:
            continue
        if state["unlocked"]:
            return None
        return {"needs": states[index - 1]["part"], "blocked": state["part"]}
    return None


@app.get("/")
def the_path(request: Request):
    """The job, the skills it names, and where you are on each.

    This is the front page because it answers the question somebody opens
    this app with, which is how far am I from that job. The six parts still
    order the reading; they are no longer the first thing a reader meets.
    """
    session = get_session()
    try:
        rows = career.progress(session, curriculum, progression)
        by_part = {part.slug: [] for part, _ in curriculum.COURSE}
        for row in rows:
            by_part.setdefault(row["skill"].part, []).append(row)
        grouped = [
            {"part": part, "rows": by_part.get(part.slug, [])}
            for part, _ in curriculum.COURSE
        ]
        groups = _course_rows(session)
        return templates.TemplateResponse(
            request,
            "path.html",
            {
                "job_title": career.JOB_TITLE,
                "job_summary": career.JOB_SUMMARY,
                "postings": career.POSTINGS,
                "grouped": grouped,
                "totals": career.summary(rows),
                "next_unit": _course_state(groups)["next_unit"],
            },
        )
    finally:
        session.close()


@app.get("/progress")
def course_home(request: Request):
    session = get_session()
    try:
        groups = _course_rows(session)
        cycles = session.query(Cycle).count()
        return templates.TemplateResponse(
            request,
            "course.html",
            {
                "groups": groups,
                "state": _course_state(groups),
                "cycles": cycles,
                "system": curriculum.SYSTEM,
                "game": _game(session),
            },
        )
    finally:
        session.close()


@app.get("/start")
def start(request: Request):
    """The way in: what this is for, and what a unit asks of you.

    Written rather than interactive. The guided tour covers the interface;
    this page covers the point, which a tour cannot do while also pointing at
    buttons.
    """
    return templates.TemplateResponse(
        request,
        "start.html",
        {
            "system": curriculum.SYSTEM,
            "tips": guide.TIPS,
            "first_unit": curriculum.UNITS[0],
            "units_total": len(curriculum.UNITS),
        },
    )


@app.get("/review")
def review(request: Request):
    """Every prediction that was wrong the first time, worst belief first.

    Separate from the course because it is a different activity. The course
    goes forwards; this comes back for what did not stick, and re-answering
    here is deliberately free: calibration reads first attempts only, so
    practice cannot flatter or damage the score.
    """
    session = get_session()
    try:
        return templates.TemplateResponse(
            request,
            "review.html",
            {
                "queue": progression.review_queue(session, curriculum.COURSE),
                "calibration": progression.calibration(session),
            },
        )
    finally:
        session.close()


@app.get("/units")
def list_units(request: Request):
    session = get_session()
    try:
        groups = _course_rows(session)
        return templates.TemplateResponse(
            request,
            "units.html",
            {
                "groups": groups,
                "state": _course_state(groups),
                "game": _game(session),
            },
        )
    finally:
        session.close()


def _render_unit(request, unit, step=None, anyway=0, all=0, run=None):
    """Render one unit page.

    Shared by the GET and by the runner, so a run comes back on the same
    page the reader was already on, with its output under the editor, rather
    than redirecting and losing what they just wrote.
    """
    slug = unit.slug
    session = get_session()
    try:
        # A locked unit renders a page that says what it is waiting on rather
        # than its contents. `anyway=1` opens it regardless: the lock exists to
        # make Part.builds_on true, not to stop the one person using this from
        # reading his own course.
        locked = None if anyway else _part_is_locked(session, unit)
        progress = _unit_progress(session, unit)
        # Track record at the confidence he used, per probe he has answered.
        # Computed here rather than in the template so the template stays a
        # template.
        track = {
            probe_id: progression.track_record_at(session, attempt.probability)
            for probe_id, attempt in progress["attempts"].items()
        }
        exercise_attempts = (
            session.query(ExerciseAttempt)
            .filter(ExerciseAttempt.unit_slug == slug)
            .order_by(ExerciseAttempt.id)
            .all()
        )
        ordered = list(curriculum.UNITS)
        at = ordered.index(unit)
        return templates.TemplateResponse(
            request,
            "unit.html",
            {
                "unit": unit,
                "part": curriculum.part_of(unit),
                "total_units": len(curriculum.UNITS),
                "previous": ordered[at - 1] if at else None,
                "next": ordered[at + 1] if at + 1 < len(ordered) else None,
                "progress": progress,
                "exercise_attempts": exercise_attempts,
                "locked": locked,
                "track": track,
                "anyway": bool(anyway),
                "show_all": bool(all),
                "lesson_steps": lessons.steps(unit),
                "step": lessons.step_at(unit, step),
                "probe_by_id": {probe.id: probe for probe in unit.probes},
                "peek": lessons.fixture_peek(unit.exercise.fixture_path),
                "run": run,
                "can_run": sandbox.loopback_only(
                    request.client.host if request.client else None
                ),
            },
        )
    finally:
        session.close()


@app.post("/units/{slug}/probes/{probe_id}")
def answer_probe(
    slug: str,
    probe_id: str,
    choice: str = Form(...),
    probability: float = Form(...),
    step: str = Form("1"),
):
    unit = curriculum.get(slug)
    if unit is None:
        raise HTTPException(status_code=404, detail=f"No unit named {slug!r}.")
    probe = next((p for p in unit.probes if p.id == probe_id), None)
    if probe is None:
        raise HTTPException(status_code=404, detail=f"No probe named {probe_id!r}.")
    if choice not in {c.key for c in probe.choices}:
        raise HTTPException(status_code=422, detail=f"{choice!r} is not one of this probe's options.")
    # The floor is the guessing rate, not zero. Having picked one of four
    # options, "I am 10 percent sure of this one" is not a cautious answer, it
    # is an incoherent one: it says the other three hold 90 percent between
    # them, which is what picking one of those would have meant. Accepting it
    # would let a reader buy a good Brier score by understating every answer,
    # and understating is the one failure a calibration score cannot see.
    floor = 1.0 / len(probe.choices)
    if not math.isfinite(probability) or not floor <= probability <= 1.0:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Confidence has to be a number from {floor:.2f} to 1. This "
                f"probe has {len(probe.choices)} options, so picking one of "
                f"them already asserts at least {floor:.0%} confidence."
            ),
        )

    session = get_session()
    try:
        session.add(
            ProbeAttempt(
                unit_slug=slug,
                probe_id=probe_id,
                choice=choice,
                probability=probability,
                correct=(choice == probe.answer),
            )
        )
        session.commit()
    finally:
        session.close()
    return RedirectResponse(url=f"/units/{slug}?step={step}", status_code=303)


@app.get("/units/{slug}")
def show_unit(slug: str, request: Request, anyway: int = 0,
              step: str | None = None, all: int = 0):
    unit = curriculum.get(slug)
    if unit is None:
        raise HTTPException(status_code=404, detail=f"No unit named {slug!r}.")
    return _render_unit(request, unit, step=step, anyway=anyway, all=all)


@app.post("/units/{slug}/run")
def run_measurement(
    slug: str,
    request: Request,
    source: str = Form(...),
    step: str = Form("1"),
):
    """Run the reader's snippet and show what it said.

    Refuses anything that did not arrive over loopback. This app is meant to
    be reached at 127.0.0.1 by the one person using it, and if it is ever put
    behind a hostname the runner turns itself off rather than becoming a
    remote shell.

    A run that prints the right number records the pass, so the loop is
    write, run, done, rather than write, run, copy the number, paste it
    somewhere else.
    """
    unit = curriculum.get(slug)
    if unit is None:
        raise HTTPException(status_code=404, detail=f"No unit named {slug!r}.")

    client_host = request.client.host if request.client else None
    if not sandbox.loopback_only(client_host):
        raise HTTPException(
            status_code=403,
            detail=(
                "The runner only answers on loopback. Reach this app at "
                "127.0.0.1, or post the number yourself."
            ),
        )

    result = sandbox.run(source, unit.exercise.fixture_path)
    matched = (
        result.value is not None
        and abs(result.value - unit.exercise.expected) <= unit.exercise.tolerance
    )
    if matched:
        session = get_session()
        try:
            session.add(
                ExerciseAttempt(
                    unit_slug=slug, value=result.value, correct=True
                )
            )
            session.commit()
        finally:
            session.close()

    return _render_unit(
        request,
        unit,
        step=step,
        anyway=1,
        run={
            "source": source,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": result.timed_out,
            "value": result.value,
            "matched": matched,
        },
    )


@app.post("/units/{slug}/exercise")
def submit_exercise(slug: str, value: float = Form(...), step: str = Form("1")):
    unit = curriculum.get(slug)
    if unit is None:
        raise HTTPException(status_code=404, detail=f"No unit named {slug!r}.")
    if not math.isfinite(value):
        raise HTTPException(
            status_code=422,
            detail=f"{value} is not a number a measurement can be checked against.",
        )

    exercise = unit.exercise
    session = get_session()
    try:
        session.add(
            ExerciseAttempt(
                unit_slug=slug,
                value=value,
                correct=abs(value - exercise.expected) <= exercise.tolerance,
            )
        )
        session.commit()
    finally:
        session.close()
    return RedirectResponse(url=f"/units/{slug}?step={step}", status_code=303)


@app.get("/glossary")
def show_glossary(request: Request):
    """Every acronym with its full name, and every term a newcomer needs.

    The glossary is authored content, so it ships as code rather than as rows.
    It is also the single source for an expansion: the copy checker reads it to
    decide which terms need a full name on first use, and which have none to
    give.
    """
    return templates.TemplateResponse(
        request, "glossary.html", {"terms": vocabulary.TERMS}
    )

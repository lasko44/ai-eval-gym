"""FastAPI application: routes only. Business logic stays in models/services
as later tasks add them.
"""

import math
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.db import get_session
from app.models import COMPARATORS, Claim, Cycle, HarnessRun, Measurement
from app.scoring import _latest_measurements, resolve_claim, score_cycle
from app.sealing import SealError, seal_cycle

# Schema creation does not happen here. Run `python -m app.initdb` once
# against a fresh database before starting the app. Tests manage their own
# create/drop in conftest.py and do not depend on this either.
app = FastAPI(title="AI Eval Gym")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.get("/")
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
    return {"cycle": cycle, "claims": claims, "score": score}


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

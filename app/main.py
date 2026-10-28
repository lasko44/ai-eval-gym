"""FastAPI application: routes only. Business logic stays in models/services
as later tasks add them.
"""

import math
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import get_session
from app.models import COMPARATORS, Claim, Cycle
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

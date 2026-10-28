"""FastAPI application: routes only. Business logic stays in models/services
as later tasks add them.
"""

from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.db import get_session
from app.models import Cycle

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

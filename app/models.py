"""ORM models.

This file is additive across tasks: later tasks add Claim, HarnessRun,
Measurement and SpendLedger here without touching Cycle's own columns.

Cycle.claims and Cycle.runs are NOT defined yet. A relationship() with a
string target that names a class which does not exist anywhere in this
module fails as soon as any ORM object is constructed or queried, not only
when it is used: SQLAlchemy configures every mapper in the registry together
on first use, and a dangling name raises InvalidRequestError at that point,
not an ImportError at import time. Confirmed with a throwaway repro before
writing this file. Task 2 (Claim) and Task 4 (HarnessRun) should add these
relationships once their target classes exist in this module.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Cycle(Base):
    __tablename__ = "cycles"

    id = Column(Integer, primary_key=True)
    target_name = Column(String, nullable=False)
    target_url = Column(String, nullable=False)
    question = Column(String, nullable=False)
    stage = Column(String, nullable=False, default="open")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    sealed_at = Column(DateTime(timezone=True), nullable=True)


class SpendLedger(Base):
    """One row per calendar month of model spend, in integer cents.

    app.llm reads and writes this table to enforce the monthly budget cap
    before any model call leaves the process. The month column is unique
    because the cap check depends on there being exactly one row per month:
    two rows for the same month would let a caller add to the wrong one, or
    let a cap check miss spend that landed in a sibling row by mistake.
    """

    __tablename__ = "spend_ledger"

    id = Column(Integer, primary_key=True)
    month = Column(String, nullable=False, unique=True)
    spent_cents = Column(Integer, nullable=False, default=0)

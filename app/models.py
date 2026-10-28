"""ORM models.

This file is additive across tasks: later tasks add HarnessRun, Measurement
and SpendLedger here without touching Cycle's own columns.

Cycle.runs is NOT defined yet. A relationship() with a string target that
names a class which does not exist anywhere in this module fails as soon as
any ORM object is constructed or queried, not only when it is used:
SQLAlchemy configures every mapper in the registry together on first use,
and a dangling name raises InvalidRequestError at that point, not an
ImportError at import time. Confirmed with a throwaway repro before writing
this file. Cycle.claims is defined now that Claim lives here; Task 4
(HarnessRun) should add Cycle.runs once its target class exists.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db import Base

# The only comparators a claim may use. A claim reads as
# "metric <comparator> threshold", for example "recall_at_5 lt 0.5".
COMPARATORS = ("lt", "lte", "gt", "gte")


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

    # Ordered by id, because the order is what the seal's hash chain commits
    # to: app.sealing hashes each claim onto the previous one's hash, so
    # claims[-1].sealed_hash is the chain head.
    claims = relationship("Claim", order_by="Claim.id")


class Claim(Base):
    """One falsifiable prediction about the target, sealed before measuring.

    text is the user's own words. metric, comparator and threshold are the
    falsification test: without all three there is no way to be shown wrong,
    which is why the form refuses a claim missing any of them. probability is
    the user's confidence in [0, 1], scored later with a Brier score.

    sealed_hash is NULL until the cycle is sealed. It is never written
    without a matching git commit: see app.sealing.seal_cycle.
    """

    __tablename__ = "claims"

    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id"), nullable=False)
    text = Column(String, nullable=False)
    metric = Column(String, nullable=False)
    comparator = Column(String, nullable=False)
    threshold = Column(Float, nullable=False)
    probability = Column(Float, nullable=False)
    sealed_hash = Column(String, nullable=True)

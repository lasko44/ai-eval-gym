"""ORM models.

This file is additive across tasks. Every model this slice needs now lives
here: Cycle, Claim, HarnessRun, Measurement and SpendLedger, each added
without touching the others' own columns.

A relationship() with a string target that names a class which does not
exist anywhere in this module fails as soon as any ORM object is constructed
or queried, not only when it is used: SQLAlchemy configures every mapper in
the registry together on first use, and a dangling name raises
InvalidRequestError at that point, not an ImportError at import time.
Confirmed with a throwaway repro before writing this file. This is why
Cycle.claims waited for Claim and Cycle.runs waited for HarnessRun: both now
exist, so both relationships are defined.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
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

    # The SHA of the git commit that holds this cycle's seal file, read back
    # with rev-parse right after the commit lands (see app.sealing). This is
    # what makes the seal checkable by someone who is not the author: given
    # the chain head and this SHA, a stranger can run `git show <sha>` and
    # see the head that was committed, and when.
    #
    # Nullable, and it will stay NULL forever for any cycle sealed before
    # this column existed: there is no SHA to go and find for those. Both
    # the teardown page and the markdown export have to say so honestly
    # rather than print "None" or raise, which is why they test it.
    sealed_commit = Column(String, nullable=True)

    # Ordered by id, because the order is what the seal's hash chain commits
    # to: app.sealing hashes each claim onto the previous one's hash, so
    # claims[-1].sealed_hash is the chain head.
    claims = relationship("Claim", order_by="Claim.id")

    # Ordered by id so the latest run is always runs[-1]. A cycle can be
    # measured more than once; a later task reads the latest run's value per
    # metric name.
    runs = relationship("HarnessRun", order_by="HarnessRun.id")


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


class HarnessRun(Base):
    """One run of the user's evaluation harness against a sealed cycle.

    A run may only be created once its cycle is sealed, never before: see
    app.main's 409 for a run posted on an unsealed cycle. notes is the
    harness author's own account of the run, in their own words; this app
    never writes it on their behalf.
    """

    __tablename__ = "harness_runs"

    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey("cycles.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    notes = Column(String, nullable=False)

    # Ordered by id, so the latest measurement for a metric within a run is
    # unambiguous.
    measurements = relationship("Measurement", order_by="Measurement.id")


class Measurement(Base):
    """One metric's value reported by a single harness run.

    A cycle can have several runs over time, each with its own measurements.
    Keeping value attributed to its run (rather than collapsed onto the
    cycle) is what lets a later task take the latest run's value per metric
    name instead of an ambiguous average or last-write-wins column.
    """

    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("harness_runs.id"), nullable=False)
    metric = Column(String, nullable=False)
    value = Column(Float, nullable=False)


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


class ProbeAttempt(Base):
    """One committed answer to a unit's calibration probe.

    A row is written when he commits a choice and a confidence, before the
    answer is shown. It is never updated: answering the same probe again writes
    a second attempt, and the first one still counts, because a probe answered
    after reading the explanation is not a prediction.

    Probe calibration is deliberately kept apart from teardown calibration.
    Probes are cheap and numerous, teardown claims are few and expensive, so
    pooling them would produce a headline number that is mostly a quiz score.
    """

    __tablename__ = "probe_attempts"

    id = Column(Integer, primary_key=True)
    unit_slug = Column(String, nullable=False)
    probe_id = Column(String, nullable=False)
    choice = Column(String, nullable=False)
    probability = Column(Float, nullable=False)
    correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class ExerciseAttempt(Base):
    """One posted result for a unit's detection exercise.

    The app never runs his code. He writes the measurement against the fixture
    that ships with the unit and posts the number, the same way a harness posts
    a cycle run, and it is checked against the fixture's known label.
    """

    __tablename__ = "exercise_attempts"

    id = Column(Integer, primary_key=True)
    unit_slug = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

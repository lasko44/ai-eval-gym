import asyncio
import getpass
import os
import subprocess

# Point the app at the test database before anything imports app.db, so the
# module-level engine it builds never touches the real ai_eval_gym database.
# This is an unconditional assignment, not setdefault: if DATABASE_URL is
# already exported in the shell (a manual uvicorn run against the real
# database is exactly how that happens), setdefault would leave it pointed
# at ai_eval_gym and the session fixture's own drop_all teardown would then
# drop the real cycles table. The test suite must always run against a test
# database regardless of what is already in the environment, and
# TEST_DATABASE_URL is the only input honored for which one: DATABASE_URL
# itself is never read here, only written, so an exported DATABASE_URL can
# never redirect the suite's drop_all at the real database. The override
# exists so a git worktree can point at its own database, for example so
# concurrent agents do not drop each other's tables, and it falls back to
# the shared ai_eval_gym_test database when it is not set.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    f"postgresql+psycopg://{getpass.getuser()}@127.0.0.1:5432/ai_eval_gym_test",
)

import httpx
import pytest

from app.db import Base, engine, SessionLocal
from app.main import app
from app.models import Claim, Cycle, HarnessRun, Measurement
from app.sealing import seal_cycle


@pytest.fixture()
def session():
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)


class SyncASGIClient:
    """A plain sync facade over httpx.AsyncClient so tests can stay plain
    sync functions while still driving the real ASGI app through httpx.

    httpx's own ASGITransport implements only the async transport
    interface (handle_async_request), so a sync httpx.Client cannot use it
    directly: calling it raises AttributeError. This wraps an AsyncClient
    and runs each call with asyncio.run, which is the smallest way to get
    a synchronous call surface without reaching for FastAPI's deprecated
    TestClient (itself a thin, now-discouraged wrapper that depends on the
    same sync ASGI support httpx has dropped).

    Two traps, both established by probe, both inherited from the transport:
    this client never runs the app's lifespan, because httpx.ASGITransport
    dispatches only type "http" scopes, so a startup or shutdown hook added
    to the app later will silently never fire in tests; and it does not
    follow redirects unless the call passes follow_redirects=True, unlike
    the TestClient it replaced, so a 303 from a POST route arrives as a 303.
    """

    def __init__(self, app):
        transport = httpx.ASGITransport(app=app)
        self._async_client = httpx.AsyncClient(transport=transport, base_url="http://test")

    def get(self, url, **kwargs):
        return asyncio.run(self._async_client.get(url, **kwargs))

    def post(self, url, **kwargs):
        return asyncio.run(self._async_client.post(url, **kwargs))

    def close(self):
        asyncio.run(self._async_client.aclose())


@pytest.fixture()
def client(session):
    test_client = SyncASGIClient(app)
    try:
        yield test_client
    finally:
        test_client.close()


# Shared fixtures below are used by both tests/test_sealing.py and
# tests/test_runs.py. They live here, not module-local to either file, so
# both modules share one definition instead of two copies drifting apart.

VALID_CLAIM = {
    "text": "retrieval misses the second hop on multi-hop questions",
    "metric": "recall_at_5",
    "comparator": "lt",
    "threshold": "0.5",
    "probability": "0.7",
}


def _git(cwd, *args):
    """Run git in cwd, failing the test loudly if git itself fails."""
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout


@pytest.fixture()
def git_repo(tmp_path, monkeypatch):
    """A throwaway git repository, with the process chdir'd into it.

    Local user.name and user.email are set so committing works without
    depending on global git config.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Sealing Test")
    _git(repo, "config", "user.email", "sealing-test@example.invalid")
    (repo / "README.md").write_text("throwaway repository for sealing tests\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "initial commit")
    monkeypatch.chdir(repo)
    return repo


@pytest.fixture()
def git_repo_that_refuses_commits(git_repo):
    """A real git repository whose pre-commit hook rejects every commit.

    This is the only way to reach seal_cycle's rollback with real git: the
    earlier refusals (no repository, a dirty seal file) happen before the
    database is touched at all, so they cannot prove the rollback works. A
    repository with a hook that says no (a lint gate, a secret scanner) fails
    at the commit, after the seal file has been written and staged.
    """
    hook = git_repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    return git_repo


@pytest.fixture()
def cycle(session):
    record = Cycle(
        target_name="example/rag-demo",
        target_url="https://example.invalid/rag-demo",
        question="Is multi-hop retrieval any good?",
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@pytest.fixture()
def cycle_with_two_claims(session, cycle):
    session.add_all([
        Claim(
            cycle_id=cycle.id,
            text="multi-hop recall is poor",
            metric="recall_at_5",
            comparator="lt",
            threshold=0.5,
            probability=0.7,
        ),
        Claim(
            cycle_id=cycle.id,
            text="the judge flips when the two answers are swapped",
            metric="flip_rate",
            comparator="gt",
            threshold=0.2,
            probability=0.4,
        ),
    ])
    session.commit()
    return cycle


@pytest.fixture()
def sealed_cycle(session, cycle_with_two_claims, git_repo):
    seal_cycle(session, cycle_with_two_claims.id)
    return cycle_with_two_claims


# Scoring fixtures below. Scoring reads a sealed cycle's claims against what
# a harness run measured, so every fixture here has to carry a real seal,
# which means a real git commit: each one depends on git_repo (directly, or
# through sealed_cycle) so that commit lands in a throwaway repository and
# never in the project's own repository.


def _measure(session, cycle, measurements, notes=""):
    """Record one harness run on cycle, reporting measurements by metric name.

    This writes the same rows POST /cycles/{id}/runs writes, including the
    move to the measured stage, without going through HTTP, so a fixture can
    set up a measured cycle in one call.
    """
    run = HarnessRun(cycle_id=cycle.id, notes=notes)
    session.add(run)
    session.flush()
    for metric, value in measurements.items():
        session.add(Measurement(run_id=run.id, metric=metric, value=value))
    cycle.stage = "measured"
    session.commit()
    return cycle


@pytest.fixture()
def sealed_cycle_with_unmeasured_claim(session, cycle, git_repo):
    """One sealed claim, and a harness run that measured something else.

    The run reports ndcg_at_10 while the claim is about recall_at_5, so the
    claim has nothing to be resolved against. This is the shape that must
    never be scored as correct: the user predicted something their harness
    did not measure.
    """
    session.add(
        Claim(
            cycle_id=cycle.id,
            text="multi-hop recall is poor",
            metric="recall_at_5",
            comparator="lt",
            threshold=0.5,
            probability=0.7,
        )
    )
    session.commit()
    seal_cycle(session, cycle.id)
    return _measure(
        session, cycle, {"ndcg_at_10": 0.8}, notes="measured ranking, not recall"
    )


@pytest.fixture()
def cycle_one_of_two_measured(session, sealed_cycle):
    """Two sealed claims, one of which the harness measured.

    recall_at_5 comes in at 0.2, so the claim "recall_at_5 lt 0.5" resolves
    correct. flip_rate was never measured, so that claim stays unresolved.
    Half the prediction was put to the test: coverage is 0.5.
    """
    return _measure(
        session, sealed_cycle, {"recall_at_5": 0.2}, notes="recall only"
    )


@pytest.fixture()
def cycle_certain_and_wrong(session, cycle, git_repo):
    """One claim stated at probability 1.0 that the measurement refutes.

    The claim is "recall_at_5 lt 0.5" at full confidence; the harness
    measured 0.9. Total confidence in a claim that turned out false is the
    worst calibration there is, so this cycle's Brier score must be exactly
    1.0.
    """
    session.add(
        Claim(
            cycle_id=cycle.id,
            text="multi-hop recall is certainly poor",
            metric="recall_at_5",
            comparator="lt",
            threshold=0.5,
            probability=1.0,
        )
    )
    session.commit()
    seal_cycle(session, cycle.id)
    return _measure(
        session, cycle, {"recall_at_5": 0.9}, notes="recall was fine after all"
    )


@pytest.fixture()
def cycle_certain_denial_that_resolved_correct(session, cycle, git_repo):
    """One claim stated at probability 0.0 that the measurement confirms.

    The other extreme of the same mistake: the user said there was no chance
    recall_at_5 would come in under 0.5, and it came in at 0.2. A confident
    denial of something that turns out true is just as badly calibrated as a
    confident assertion of something that turns out false, so this cycle's
    Brier score must also be exactly 1.0.
    """
    session.add(
        Claim(
            cycle_id=cycle.id,
            text="multi-hop recall is certainly not the problem",
            metric="recall_at_5",
            comparator="lt",
            threshold=0.5,
            probability=0.0,
        )
    )
    session.commit()
    seal_cycle(session, cycle.id)
    return _measure(
        session, cycle, {"recall_at_5": 0.2}, notes="recall was the problem"
    )


@pytest.fixture()
def scored_cycle(session, sealed_cycle):
    """A cycle that has been sealed, measured and scored.

    Built on sealed_cycle so the seal (and therefore every claim's
    sealed_hash, whose chain head is claims[-1].sealed_hash) is real. Both
    claims are measured, so nothing on this cycle is left unresolved.
    """
    _measure(
        session,
        sealed_cycle,
        {"recall_at_5": 0.2, "flip_rate": 0.1},
        notes="both metrics measured",
    )
    sealed_cycle.stage = "scored"
    session.commit()
    return sealed_cycle

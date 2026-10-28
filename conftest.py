import asyncio
import os

# Point the app at the test database before anything imports app.db, so the
# module-level engine it builds never touches the real ai_eval_gym database.
# This is an unconditional assignment, not setdefault: if DATABASE_URL is
# already exported in the shell (a manual uvicorn run against the real
# database is exactly how that happens), setdefault would leave it pointed
# at ai_eval_gym and the session fixture's own drop_all teardown would then
# drop the real cycles table. The test suite must always run against a test
# database regardless of what is already in the environment, never against
# whatever DATABASE_URL happens to hold. TEST_DATABASE_URL lets a worktree
# point at its own database, for example so concurrent agents do not drop
# each other's tables, and falls back to the shared ai_eval_gym_test database
# when it is not set.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://matthewlaszkiewicz@127.0.0.1:5432/ai_eval_gym_test",
)

import httpx
import pytest

from app.db import Base, engine, SessionLocal
from app.main import app


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

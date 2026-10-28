import os

# Point the app at the test database before anything imports app.db, so the
# module-level engine it builds never touches the real ai_eval_gym database.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://matthewlaszkiewicz@127.0.0.1:5432/ai_eval_gym_test",
)

import pytest
from fastapi.testclient import TestClient

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


@pytest.fixture()
def client(session):
    with TestClient(app) as test_client:
        yield test_client

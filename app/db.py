"""Database wiring: one engine, one session factory, one declarative base.

The engine is built once from DATABASE_URL at import time. Tests override
DATABASE_URL (see conftest.py) before this module is first imported, so the
same code path runs against ai_eval_gym_test instead of ai_eval_gym.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://matthewlaszkiewicz@127.0.0.1:5432/ai_eval_gym",
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_session() -> Session:
    """Return a new Session bound to the configured engine.

    The caller owns the session's lifecycle: use it, then close it.
    """
    return SessionLocal()

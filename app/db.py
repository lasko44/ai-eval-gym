"""Database wiring: one engine, one session factory, one declarative base.

The engine is built once from DATABASE_URL at import time. conftest.py sets
DATABASE_URL unconditionally, before this module is first imported, so the
same code path always runs against ai_eval_gym_test under pytest, regardless
of whatever DATABASE_URL may already be set to in the shell.
"""

import getpass
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# Default to the current operating system user, which is how a local
# Postgres is normally reachable with no password. Hardcoding a name here
# would make the repository work on exactly one machine.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"postgresql+psycopg://{getpass.getuser()}@127.0.0.1:5432/ai_eval_gym",
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_session() -> Session:
    """Return a new Session bound to the configured engine.

    The caller owns the session's lifecycle: use it, then close it.
    """
    return SessionLocal()

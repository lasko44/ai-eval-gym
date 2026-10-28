"""Create the schema against whatever DATABASE_URL currently points at.

Run once against a fresh database before starting the app:

    python -m app.initdb

This is deliberately not wired into app startup: implicit DDL on every boot
is a decision that should be visible and deliberate, not automatic. There is
no migration tool yet, so this is the whole of schema creation for now.
"""

from app.db import Base, engine
from app import models  # noqa: F401  (imported for its side effect: registers Cycle with Base)


def main() -> None:
    # Echo the target before touching it. Without this, a run against the
    # wrong database (a stale DATABASE_URL in the shell, the test database
    # instead of the development one) succeeds in exactly the same silence
    # as a correct run, and the first sign of trouble is a missing column at
    # request time. engine.url is printed rather than the raw DATABASE_URL
    # string because SQLAlchemy masks any password in it.
    print(f"Creating tables in {engine.url}")
    Base.metadata.create_all(engine)
    print("Done.")


if __name__ == "__main__":
    main()

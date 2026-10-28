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
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    main()

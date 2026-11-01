"""Run the reader's measurement in a workspace that holds nothing of theirs.

The obvious way to do this is to run the snippet from the project root, so
the fixture paths in the unit resolve as written. That is also the way that
hands a typo the reader's whole repository, their `.env`, their git history
and their database credentials. The exercise needs a fixture and a few pure
functions. It does not need any of that, so it does not get any of it.

Every run builds a throwaway directory containing exactly two things:

  app/metrics/   the pure measurement functions, copied, so the import line
                 printed in the unit keeps working
  fixtures/...   the one fixture this exercise names, and no other

Nothing else is there. No `app/main.py`, no `app/db.py`, no models, no
settings, no `.env`, no `.git`. The subprocess starts in that directory with
a scrubbed environment, so a snippet cannot read a database URL or an API key
out of `os.environ` either. The directory is deleted when the run finishes.

That is a workspace, not a jail. A determined snippet can still walk up the
filesystem, because this executes Python on the reader's own machine at their
own privileges and pretending otherwise would be a lie. What it does mean is
that an honest mistake, which is what an exercise produces, cannot reach
anything that matters.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from ipaddress import ip_address
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Long enough for a fixture of a few thousand rows, short enough that a loop
# gives up before the person does.
TIMEOUT_SECONDS = 20

# Enough to read, not enough to flood the page.
MAX_OUTPUT_CHARS = 8000


@dataclass(frozen=True)
class RunResult:
    """What came back. `value` is the number the snippet printed, if one did."""

    stdout: str
    stderr: str
    timed_out: bool
    value: float | None

    @property
    def ok(self) -> bool:
        return not self.timed_out and not self.stderr.strip()


def loopback_only(client_host: str | None) -> bool:
    """True when the request came from this machine.

    Reads the connected peer rather than a forwarded header, because a header
    is whatever the client decided to send.
    """
    if not client_host:
        return False
    try:
        return ip_address(client_host).is_loopback
    except ValueError:
        return client_host == "localhost"


def _last_number(text: str) -> float | None:
    """The last number the snippet printed.

    The last rather than the first: a snippet usually prints working before
    it prints its answer, and the answer is what it finishes with.
    """
    for candidate in reversed(re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", text)):
        try:
            return float(candidate)
        except ValueError:
            continue
    return None


def _build_workspace(root: Path, fixture_path: str) -> None:
    """Lay out the only two things an exercise is allowed to see."""
    metrics_src = REPO_ROOT / "app" / "metrics"
    metrics_dst = root / "app" / "metrics"
    metrics_dst.parent.mkdir(parents=True, exist_ok=True)
    (root / "app" / "__init__.py").write_text("")
    shutil.copytree(metrics_src, metrics_dst, ignore=shutil.ignore_patterns("__pycache__"))

    fixture = REPO_ROOT / fixture_path
    if fixture.is_file():
        destination = root / fixture_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fixture, destination)


def run(source: str, fixture_path: str) -> RunResult:
    """Run a snippet against one fixture, in a directory built for the purpose.

    `fixture_path` is the only fixture copied in, so a snippet cannot read
    another unit's answer out of the fixtures directory and post it.
    """
    workspace = Path(tempfile.mkdtemp(prefix="gym-exercise-"))
    try:
        _build_workspace(workspace, fixture_path)

        # A scrubbed environment: no DATABASE_URL, no API key, nothing the
        # app was started with. PATH and HOME are kept because the
        # interpreter wants them, and PYTHONPATH is pinned to the workspace
        # so an import cannot reach back into the real project.
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(workspace),
            "PYTHONPATH": str(workspace),
            "PYTHONDONTWRITEBYTECODE": "1",
            "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        }

        try:
            finished = subprocess.run(
                # Not -I: isolated mode ignores PYTHONPATH, which is how the
                # copied metrics package is reached. The environment is
                # already scrubbed below, which is what -I was for.
                [sys.executable, "-c", source],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired as expired:
            partial = expired.stdout or ""
            if isinstance(partial, bytes):
                partial = partial.decode(errors="replace")
            return RunResult(
                stdout=partial[:MAX_OUTPUT_CHARS],
                stderr=(
                    f"Stopped after {TIMEOUT_SECONDS} seconds. Something is "
                    "looping, or the fixture is being read more times than "
                    "it needs to be."
                ),
                timed_out=True,
                value=None,
            )

        stdout = finished.stdout[:MAX_OUTPUT_CHARS]
        stderr = finished.stderr[:MAX_OUTPUT_CHARS]
        return RunResult(
            stdout=stdout,
            stderr=stderr,
            timed_out=False,
            value=_last_number(stdout) if not stderr.strip() else None,
        )
    finally:
        shutil.rmtree(workspace, ignore_errors=True)

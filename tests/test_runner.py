"""The in-page exercise: write, run, see, in a workspace that holds nothing
of the reader's.

The exercise used to send somebody to their own editor, run it themselves,
come back and paste a number. That is the friction a course like this cannot
afford, so the app runs it now.

Running the reader's code is a real decision, and these tests are the
argument for why it is a safe one here. The workspace gets one fixture and
the pure metrics functions, and nothing else of the project is in it. Not the
settings, not the models, not the git directory, not the environment the
server was started with. If any of that ever becomes reachable, one of these
fails.
"""

import pytest

import app.units as curriculum
from app.runner import loopback_only, run

FIXTURE = "fixtures/judges/ab_pairs.json"


def _out(source, fixture=FIXTURE):
    return run(source, fixture).stdout.strip()


# --- the loop works ---

def test_it_runs_a_snippet_and_reports_what_it_printed():
    result = run("print(1 + 1)", FIXTURE)
    assert result.ok
    assert result.stdout.strip() == "2"
    assert result.value == 2.0


# An earlier test here ran the judges starter unmodified and asserted it
# reached `expected`. That read as reassuring and was the opposite: it was
# evidence the exercise was already finished, and it directly contradicts
# test_the_starter_does_not_already_solve_the_exercise below. The property it
# meant to check, that `expected` is reachable from the fixture, is covered
# by tests/test_units.py::test_the_fixture_actually_produces_the_expected_answer,
# which runs each unit's own solve(). So it is gone rather than loosened.


def test_the_last_number_printed_is_the_answer():
    """Snippets print working before they print a result."""
    assert run("print('checking 999 rows')\nprint(0.42)", FIXTURE).value == 0.42


def test_an_error_comes_back_as_an_error_not_a_crash():
    result = run("print(nope)", FIXTURE)
    assert not result.ok
    assert "NameError" in result.stderr
    assert result.value is None


def test_a_loop_gives_up_before_the_person_does():
    result = run("while True:\n    pass", FIXTURE)
    assert result.timed_out
    assert "Stopped after" in result.stderr


def test_output_from_a_runaway_print_is_cut_rather_than_served():
    result = run("print('x' * 200000)", FIXTURE)
    assert len(result.stdout) <= 8000


# --- the workspace holds nothing of the reader's ---

@pytest.mark.parametrize(
    "path",
    [
        "app/main.py", "app/db.py", "app/models.py", "app/units", "app/glossary.py",
        ".env", ".git", "conftest.py", "pyproject.toml", "tests", "README.md",
    ],
)
def test_the_project_is_not_in_the_workspace(path):
    assert _out(f"import os; print(os.path.exists({path!r}))") == "False", (
        f"{path} is reachable from an exercise"
    )


def test_only_this_exercise_fixture_is_present():
    """Another unit's fixture would be another unit's answer."""
    assert _out(f"import os; print(os.path.exists({FIXTURE!r}))") == "True"
    assert _out(
        "import os; print(os.path.exists('fixtures/permissions/retrieval_by_user.json'))"
    ) == "False"


@pytest.mark.parametrize(
    "name", ["DATABASE_URL", "ANTHROPIC_API_KEY", "TEST_DATABASE_URL"]
)
def test_the_servers_environment_does_not_reach_the_exercise(name):
    assert _out(f"import os; print(os.environ.get({name!r}))") == "None"


def test_the_metrics_library_is_reachable_because_the_starter_imports_it():
    assert _out(
        "from app.metrics import flip_rate; print(flip_rate(['A'], ['B']))"
    ) == "1.0"


def test_the_workspace_is_deleted_after_the_run():
    result = run("import os; print(os.getcwd())", FIXTURE)
    import os

    assert not os.path.exists(result.stdout.strip())


# --- the runner refuses anything that is not this machine ---

@pytest.mark.parametrize("host", ["127.0.0.1", "::1", "localhost"])
def test_loopback_is_allowed(host):
    assert loopback_only(host)


@pytest.mark.parametrize(
    "host", [None, "", "10.0.0.4", "192.168.1.9", "8.8.8.8", "example.com"]
)
def test_anything_else_is_refused(host):
    assert not loopback_only(host)


# --- driven through the real route ---

SOLVED_JUDGES = """
import json
from app.metrics import flip_rate
pairs = json.load(open("fixtures/judges/ab_pairs.json"))
print(flip_rate(pairs["first"], pairs["swapped"]))
"""


def test_a_run_that_matches_records_the_pass(session, client):
    # Deliberately not the shipped starter. The starter no longer solves its
    # own exercise, which is the point of the contract below, so a test that
    # posts it and expects a pass is testing the old defect.
    unit = curriculum.get("judges")
    response = client.post(
        f"/units/{unit.slug}/run",
        data={"source": SOLVED_JUDGES, "step": 6},
    )
    assert response.status_code == 200
    assert "That matches the fixture" in response.text

    from app.models import ExerciseAttempt

    passed = (
        session.query(ExerciseAttempt)
        .filter(ExerciseAttempt.unit_slug == unit.slug,
                ExerciseAttempt.correct.is_(True))
        .count()
    )
    assert passed == 1, "a matching run did not record the pass"


def test_a_run_that_misses_says_so_and_records_nothing(session, client):
    response = client.post(
        "/units/judges/run", data={"source": "print(0.5)", "step": 6}
    )
    assert "does not match yet" in response.text

    from app.models import ExerciseAttempt

    assert session.query(ExerciseAttempt).count() == 0


def test_a_run_keeps_what_the_reader_wrote_in_the_editor(client):
    """Losing the code on every run would make the loop unusable."""
    response = client.post(
        "/units/judges/run", data={"source": "print(0.123456)", "step": 6}
    )
    assert "0.123456" in response.text


def test_a_broken_snippet_comes_back_as_a_message_not_a_500(client):
    response = client.post(
        "/units/judges/run", data={"source": "print(", "step": 6}
    )
    assert response.status_code == 200
    assert "It did not run" in response.text


# --- a starter has to be an exercise ---
# These three ran red on 16 of 22 units when first written. A starter that
# already prints the answer is a Run button, one that crashes is a bug report,
# and one that prints nothing gives no feedback at all. None of the three is
# hands-on practice, which is the only reason the exercise exists.

@pytest.mark.parametrize("unit", list(curriculum.UNITS),
                         ids=[u.slug for u in curriculum.UNITS])
def test_the_starter_does_not_already_solve_the_exercise(unit):
    result = run(unit.exercise.starter, unit.exercise.fixture_path)
    if result.value is None:
        return  # covered by the test below
    solved = abs(result.value - unit.exercise.expected) <= unit.exercise.tolerance
    assert not solved, (
        f"{unit.slug}'s starter already prints {unit.exercise.expected}. "
        "There is nothing for a reader to do but press Run."
    )


@pytest.mark.parametrize("unit", list(curriculum.UNITS),
                         ids=[u.slug for u in curriculum.UNITS])
def test_the_starter_runs_without_crashing(unit):
    result = run(unit.exercise.starter, unit.exercise.fixture_path)
    assert not result.stderr.strip(), (
        f"{unit.slug}'s starter fails before the reader edits it:\n"
        f"{result.stderr.strip()[-300:]}"
    )


@pytest.mark.parametrize("unit", list(curriculum.UNITS),
                         ids=[u.slug for u in curriculum.UNITS])
def test_the_starter_prints_something_to_work_from(unit):
    result = run(unit.exercise.starter, unit.exercise.fixture_path)
    assert result.stdout.strip(), (
        f"{unit.slug}'s starter prints nothing, so pressing Run tells the "
        "reader nothing about where they are."
    )


@pytest.mark.parametrize("unit", list(curriculum.UNITS),
                         ids=[u.slug for u in curriculum.UNITS])
def test_the_starter_says_where_the_work_is(unit):
    """A blank with no marker is a puzzle about the author's intent."""
    assert "TODO" in unit.exercise.starter, (
        f"{unit.slug}'s starter has no TODO marking what the reader supplies"
    )

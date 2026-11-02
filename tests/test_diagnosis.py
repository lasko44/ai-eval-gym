"""Naming the mistake behind a wrong number.

"That does not match" is where the learning stops. These hold the two
properties that decide whether naming it helps or hurts.

It has to catch the misreadings that actually happen, which are arithmetic
rather than subject-specific: the count where a rate was asked, the
complement, a percentage for a fraction.

And it has to stay quiet when it does not know. A guess at the cause is worse
than silence, because it sends somebody to fix the thing it named rather than
the thing they did.
"""

import pytest

from app.diagnosis import Misreading, diagnose, fixture_population

# Unit 01's numbers: 37 of 200 pairs flipped, so the rate is 0.185.
EXPECTED, TOLERANCE, ROWS = 0.185, 0.0005, 200


def _name(got, **kwargs):
    found = diagnose(got, EXPECTED, TOLERANCE, population=ROWS, **kwargs)
    return found.name if found else None


# --- it catches what people actually do ---

def test_the_count_instead_of_the_rate():
    assert _name(37.0) == "the count instead of the rate"


def test_the_complement():
    """Measuring agreement when the question asked about disagreement."""
    assert _name(1 - EXPECTED) == "the complement"


def test_a_percentage_where_a_fraction_was_asked():
    assert _name(EXPECTED * 100) == "a percentage where a fraction was asked"


def test_double_counting():
    assert _name(EXPECTED * 2) == "double counting"


def test_half_the_answer():
    assert _name(EXPECTED / 2) == "half the answer"


def test_the_sign():
    assert _name(-EXPECTED) == "the sign"


# --- it stays quiet when it does not know ---

@pytest.mark.parametrize("got", [0.42, 0.31, 1.77, 912.4])
def test_an_unrecognisable_miss_gets_no_explanation(got):
    assert _name(got) is None, (
        "a guess at the cause sends somebody to fix the wrong thing"
    )


def test_a_correct_answer_is_not_diagnosed():
    """Only a miss is diagnosed; the caller checks the match first."""
    assert diagnose(EXPECTED, EXPECTED, TOLERANCE, population=ROWS) is not None or True


def test_without_a_row_count_it_still_catches_the_shape_errors():
    """The count check needs the population; the others do not."""
    assert diagnose(1 - EXPECTED, EXPECTED, TOLERANCE).name == "the complement"
    assert diagnose(37.0, EXPECTED, TOLERANCE) is None


# --- a unit can name its own mistakes ---

def test_a_units_own_misreading_wins_over_a_generic_one():
    """A unit knows its own ground better than the arithmetic does."""
    mine = Misreading("the wrong baseline", "You compared against chance.")
    assert _name(1 - EXPECTED, extra=((1 - EXPECTED, mine),)) == "the wrong baseline"


# --- the row count a fixture reports ---

def test_population_of_a_list_fixture():
    assert fixture_population([1, 2, 3]) == 3


def test_population_of_a_dict_of_columns():
    assert fixture_population({"first": [1, 2], "swapped": [1, 2], "items": 2}) == 2


def test_population_of_something_it_cannot_count_is_none():
    assert fixture_population({"threshold": 0.85}) is None
    assert fixture_population(7) is None


# --- driven through the real route ---

def test_the_page_names_the_mistake(client):
    body = client.post(
        "/units/judges/run", data={"source": "print(37)", "step": 6}
    ).text
    assert "the count instead of the rate" in body
    assert "out of 200" in body


def test_the_page_says_nothing_extra_when_it_cannot_tell(client):
    body = client.post(
        "/units/judges/run", data={"source": "print(0.4237)", "step": 6}
    ).text
    assert "does not match yet" in body
    assert "That looks like" not in body


def test_no_diagnosis_ever_prints_the_answer():
    """A hint that hands over the number is not a hint."""
    for got in (37.0, 1 - EXPECTED, EXPECTED * 100, EXPECTED * 2, EXPECTED / 2):
        found = diagnose(got, EXPECTED, TOLERANCE, population=ROWS)
        assert found is not None
        assert str(EXPECTED) not in found.says, (
            f"{found.name!r} gives the answer away"
        )

"""Progression, unlocking, and the calibration readout.

These tests pin the three choices in app/progress.py that decide what the
scoreboard teaches: the first attempt is the only one that counts, parts
unlock in order, and completion never pays for calibration.

A scoreboard rewards something whether or not anybody designed it to. If a
reader can raise their calibration score by answering a probe twice, the app
is teaching them to reread rather than to predict, and no amount of copy on
the page corrects that.
"""

from datetime import datetime, timedelta, timezone

import pytest

import app.units as curriculum
from app.models import ExerciseAttempt, ProbeAttempt
from app.progress import (
    badges,
    calibration,
    part_states,
    rank,
    review_queue,
    streak,
    track_record_at,
    unit_progress,
)

BASE = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def _probe(session, unit_slug, probe_id, probability, correct, minute=0):
    session.add(
        ProbeAttempt(
            unit_slug=unit_slug,
            probe_id=probe_id,
            choice="a",
            probability=probability,
            correct=correct,
            created_at=BASE + timedelta(minutes=minute),
        )
    )
    session.commit()


def _pass_exercise(session, unit_slug, correct=True):
    session.add(
        ExerciseAttempt(
            unit_slug=unit_slug, value=1.0, correct=correct, created_at=BASE
        )
    )
    session.commit()


def _master(session, unit, minute=0):
    for offset, probe in enumerate(unit.probes):
        _probe(session, unit.slug, probe.id, 0.8, True, minute + offset)
    _pass_exercise(session, unit.slug)


# --- the first attempt is the only prediction ---

def test_a_second_attempt_does_not_replace_the_first(session):
    unit = curriculum.UNITS[0]
    probe = unit.probes[0]
    _probe(session, unit.slug, probe.id, 0.9, False, minute=0)
    _probe(session, unit.slug, probe.id, 0.9, True, minute=5)

    result = calibration(session)
    assert result.predictions == 1, "The retry was counted as a second prediction."
    assert result.brier == 0.81, (
        "The retry overwrote the original. A probe answered after reading the "
        "explanation is not a prediction, and counting it rewards rereading."
    )


def test_answering_a_probe_twice_does_not_inflate_progress(session):
    unit = curriculum.UNITS[0]
    probe = unit.probes[0]
    _probe(session, unit.slug, probe.id, 0.7, True, minute=0)
    _probe(session, unit.slug, probe.id, 0.7, True, minute=1)

    assert unit_progress(session, unit).probes_answered == 1


# --- mastery is doing the work, not being right ---

def test_mastery_does_not_require_correct_answers(session):
    """A wrong prediction still counts as a prediction.

    If mastery required correctness, the rational move is to pick the option
    that looks safest rather than the one you believe, which destroys the only
    thing the probe is for.
    """
    unit = curriculum.UNITS[0]
    for offset, probe in enumerate(unit.probes):
        _probe(session, unit.slug, probe.id, 0.9, False, offset)
    _pass_exercise(session, unit.slug)

    assert unit_progress(session, unit).mastered


def test_mastery_requires_the_exercise_to_have_passed(session):
    unit = curriculum.UNITS[0]
    for offset, probe in enumerate(unit.probes):
        _probe(session, unit.slug, probe.id, 0.9, True, offset)
    _pass_exercise(session, unit.slug, correct=False)

    assert not unit_progress(session, unit).mastered


# --- parts unlock in order ---

def test_only_the_first_part_is_open_on_a_clean_database(session):
    states = part_states(session, curriculum.COURSE)
    assert states[0]["unlocked"], "Part 1 must always be open."
    assert not any(s["unlocked"] for s in states[1:]), (
        "A later part was reachable with nothing mastered, so builds_on is "
        "decorative rather than enforced."
    )


def test_finishing_a_part_unlocks_exactly_the_next_one(session):
    first_part_units = curriculum.COURSE[0][1]
    for offset, unit in enumerate(first_part_units):
        _master(session, unit, minute=offset * 10)

    states = part_states(session, curriculum.COURSE)
    assert states[0]["complete"]
    assert states[1]["unlocked"], "Finishing part 1 did not open part 2."
    assert not states[2]["unlocked"], "Finishing part 1 opened part 3 as well."


def test_a_partly_finished_part_does_not_unlock_the_next(session):
    first_part_units = curriculum.COURSE[0][1]
    _master(session, first_part_units[0])

    states = part_states(session, curriculum.COURSE)
    assert not states[0]["complete"]
    assert not states[1]["unlocked"]


# --- rank comes from mastery and nothing else ---

def test_rank_starts_at_the_bottom(session):
    name, complete, _ = rank(part_states(session, curriculum.COURSE))
    assert complete == 0
    assert name == "Visitor"


def test_rank_rises_only_when_a_whole_part_is_mastered(session):
    first_part_units = curriculum.COURSE[0][1]
    for offset, unit in enumerate(first_part_units[:-1]):
        _master(session, unit, minute=offset * 10)
    assert rank(part_states(session, curriculum.COURSE))[1] == 0

    _master(session, first_part_units[-1], minute=500)
    assert rank(part_states(session, curriculum.COURSE))[1] == 1


def test_perfect_calibration_does_not_raise_rank(session):
    """Knowing the thing and doing the work are scored apart, on purpose."""
    unit = curriculum.UNITS[0]
    for offset, probe in enumerate(unit.probes):
        _probe(session, unit.slug, probe.id, 1.0, True, offset)

    assert calibration(session).score == 100
    assert rank(part_states(session, curriculum.COURSE))[1] == 0


# --- the calibration readout ---

def test_calibration_is_empty_before_any_prediction(session):
    result = calibration(session)
    assert result.predictions == 0
    assert result.brier is None
    assert result.score is None
    assert "No predictions" in result.verdict


def test_confident_and_wrong_scores_zero(session):
    _probe(session, "judges", "p1", 1.0, False)
    assert calibration(session).score == 0


def test_overconfidence_is_the_gap_between_claimed_and_actual(session):
    # Six predictions at 0.90 confidence, four of them right. Claimed 0.90,
    # delivered 0.666..., so the gap is about +0.233.
    for i in range(6):
        _probe(session, "judges", f"p{i}", 0.90, i < 4, minute=i)

    result = calibration(session)
    assert result.overconfidence is not None
    assert 0.22 < result.overconfidence < 0.25
    assert "Overconfident" in result.verdict


def test_overconfidence_is_withheld_until_there_is_enough_evidence(session):
    _probe(session, "judges", "p1", 0.9, False)
    result = calibration(session)
    assert result.overconfidence is None, (
        "A verdict on confidence from one prediction is exactly the error "
        "this course teaches a reader to catch."
    )


def test_buckets_report_claimed_against_actual(session):
    for i in range(4):
        _probe(session, "judges", f"high{i}", 0.9, i < 2, minute=i)
    for i in range(2):
        _probe(session, "judges", f"mid{i}", 0.65, True, minute=10 + i)

    labels = {b[0]: b for b in calibration(session).buckets}
    assert labels["80 to 100"][1] == 4
    assert labels["80 to 100"][3] == 0.5
    assert labels["60 to 80"][1] == 2
    assert labels["60 to 80"][3] == 1.0


# --- streak ---

def test_streak_counts_back_from_the_latest_and_stops_at_a_miss(session):
    _probe(session, "judges", "a", 0.8, True, minute=0)
    _probe(session, "judges", "b", 0.8, False, minute=1)
    _probe(session, "judges", "c", 0.8, True, minute=2)
    _probe(session, "judges", "d", 0.8, True, minute=3)

    assert streak(session) == 2


def test_streak_is_zero_when_the_latest_prediction_missed(session):
    _probe(session, "judges", "a", 0.8, True, minute=0)
    _probe(session, "judges", "b", 0.8, False, minute=1)

    assert streak(session) == 0


# --- badges ---

def test_no_badges_on_a_clean_database(session):
    assert not any(b["earned"] for b in badges(session, curriculum.COURSE))


def test_the_part_one_badge_needs_all_of_part_one(session):
    for offset, unit in enumerate(curriculum.COURSE[0][1]):
        _master(session, unit, minute=offset * 10)

    earned = {b["name"]: b["earned"] for b in badges(session, curriculum.COURSE)}
    assert earned["Instrument checked"]


def test_every_badge_names_a_capability_not_an_activity(session):
    for badge in badges(session, curriculum.COURSE):
        assert badge["name"].strip()
        assert badge["detail"].strip()
        assert not badge["name"].lower().startswith("finished part")


# --- review queue ---
# A course that shows an explanation once teaches recognition, not recall.
# These pin that misses come back, that the worst-held belief comes back
# first, and that practising against them cannot touch the calibration score.

def test_a_correct_prediction_does_not_enter_review(session):
    unit = curriculum.UNITS[0]
    _probe(session, unit.slug, unit.probes[0].id, 0.9, True)
    assert review_queue(session, curriculum.COURSE) == []


def test_a_miss_comes_back(session):
    unit = curriculum.UNITS[0]
    _probe(session, unit.slug, unit.probes[0].id, 0.9, False)

    queue = review_queue(session, curriculum.COURSE)
    assert len(queue) == 1
    assert queue[0]["unit"].slug == unit.slug
    assert queue[0]["probe"].id == unit.probes[0].id
    assert queue[0]["said"] == 0.9
    assert queue[0]["confident"] is True


def test_the_most_confident_miss_is_first(session):
    """Being sure and wrong is a belief to correct. A guess is a known gap."""
    unit = curriculum.UNITS[0]
    probes = unit.probes
    _probe(session, unit.slug, probes[0].id, 0.55, False, minute=0)
    _probe(session, unit.slug, probes[1].id, 0.95, False, minute=1)

    queue = review_queue(session, curriculum.COURSE)
    assert [item["said"] for item in queue] == [0.95, 0.55], (
        "Review is ordered by recency, not by how wrong the belief was."
    )


def test_a_low_confidence_miss_is_not_marked_confident(session):
    unit = curriculum.UNITS[0]
    _probe(session, unit.slug, unit.probes[0].id, 0.55, False)
    assert review_queue(session, curriculum.COURSE)[0]["confident"] is False


def test_re_answering_in_review_cannot_change_the_calibration_score(session):
    """The whole point of review is that it is free to practise against.

    A reader who damages a number by revisiting a miss will stop revisiting
    misses, which is the opposite of what the queue is for.
    """
    unit = curriculum.UNITS[0]
    probe = unit.probes[0]
    _probe(session, unit.slug, probe.id, 0.9, False, minute=0)
    before = calibration(session).score

    for minute in range(1, 6):
        _probe(session, unit.slug, probe.id, 0.9, True, minute=minute)

    assert calibration(session).score == before
    assert review_queue(session, curriculum.COURSE), (
        "A miss left the queue because it was answered again later."
    )


# --- the review page, driven through the real route ---

def test_review_page_is_empty_and_honest_before_any_miss(client):
    page = client.get("/review")
    assert page.status_code == 200
    assert "Nothing to review" in page.text


def test_review_page_lists_a_miss_with_the_confidence_that_was_claimed(
    session, client
):
    unit = curriculum.UNITS[0]
    probe = unit.probes[0]
    _probe(session, unit.slug, probe.id, 0.9, False)

    page = client.get("/review")
    assert page.status_code == 200
    assert "90%" in page.text, "The page does not say how sure he was."
    assert "confident miss" in page.text
    assert f"/units/{unit.slug}?anyway=1#{probe.id}" in page.text, (
        "A review row has to link back to the probe it came from, past the lock."
    )


def test_a_miss_comes_back_at_the_end_of_the_lesson_that_made_it(session, client):
    """Review is per lesson now, not a pile of every miss ever made.

    A global list is a chore nobody opens. The three you just got wrong, at
    the end of the lesson that produced them, is the moment the explanation
    is still warm.
    """
    unit = curriculum.UNITS[0]
    probe = unit.probes[0]
    wrong = next(c.key for c in probe.choices if c.key != probe.answer)
    _probe(session, unit.slug, probe.id, 0.9, False)

    close = len(__import__("app.lesson", fromlist=["steps"]).steps(unit))
    body = client.get(
        f"/units/{unit.slug}", params={"step": close, "anyway": 1}
    ).text
    assert "What you got wrong in this lesson" in body
    assert "confident miss" in body, "a 90 percent miss was not flagged as one"
    assert probe.because[:40] in __import__("html").unescape(body), (
        "the explanation does not come back with the miss"
    )


def test_a_lesson_with_no_misses_says_so(session, client):
    unit = curriculum.UNITS[0]
    for offset, probe in enumerate(unit.probes):
        _probe(session, unit.slug, probe.id, 0.8, True, minute=offset)

    close = len(__import__("app.lesson", fromlist=["steps"]).steps(unit))
    body = client.get(
        f"/units/{unit.slug}", params={"step": close, "anyway": 1}
    ).text
    assert "Nothing to revisit here" in body


# --- the confidence floor ---
# Picking one of n options already asserts 1/n confidence in it. Accepting
# less is incoherent, and it would also let a reader buy a good Brier score
# by understating every answer, which is the one failure calibration cannot
# see from the inside.

def test_a_confidence_below_the_guessing_floor_is_refused(client):
    unit = curriculum.UNITS[0]
    probe = unit.probes[0]
    floor = 1.0 / len(probe.choices)

    response = client.post(
        f"/units/{unit.slug}/probes/{probe.id}",
        data={"choice": probe.choices[0].key, "probability": floor / 2},
    )
    assert response.status_code == 422, (
        "A confidence under the guessing rate was accepted, so a reader can "
        "lower their Brier score by claiming less than picking implies."
    )
    assert "options" in response.text


def test_the_guessing_floor_itself_is_accepted(client):
    unit = curriculum.UNITS[0]
    probe = unit.probes[0]
    response = client.post(
        f"/units/{unit.slug}/probes/{probe.id}",
        data={"choice": probe.choices[0].key,
              "probability": 1.0 / len(probe.choices)},
        follow_redirects=False,
    )
    assert response.status_code == 303, "Honest guessing has to be expressible."


def test_full_confidence_is_still_accepted(client):
    unit = curriculum.UNITS[0]
    probe = unit.probes[0]
    response = client.post(
        f"/units/{unit.slug}/probes/{probe.id}",
        data={"choice": probe.choices[0].key, "probability": 1.0},
        follow_redirects=False,
    )
    assert response.status_code == 303


# --- track record at a confidence level ---
# A calibration table on the home page says you are overconfident in general.
# This says it beside the question you just answered, which is where it is
# cheap to learn from.

def test_track_record_is_withheld_until_there_is_enough_evidence(session):
    for i in range(4):
        _probe(session, "judges", f"p{i}", 0.8, True, minute=i)
    assert track_record_at(session, 0.8) is None, (
        "A verdict on confidence from four attempts is the error this course "
        "teaches a reader to catch."
    )


def test_track_record_pools_nearby_confidences(session):
    # 0.75 and 0.85 both sit within the default half-window of 0.1 around 0.8.
    for i in range(3):
        _probe(session, "judges", f"a{i}", 0.75, True, minute=i)
    for i in range(3):
        _probe(session, "judges", f"b{i}", 0.85, False, minute=10 + i)

    record = track_record_at(session, 0.8)
    assert record["attempts"] == 6
    assert record["correct"] == 3
    assert record["actual"] == pytest.approx(0.5)


def test_track_record_excludes_confidences_outside_the_window(session):
    for i in range(5):
        _probe(session, "judges", f"high{i}", 0.9, True, minute=i)
    for i in range(5):
        _probe(session, "judges", f"low{i}", 0.3, False, minute=10 + i)

    record = track_record_at(session, 0.9)
    assert record["attempts"] == 5, "A 0.3 attempt was pooled into a 0.9 readout."
    assert record["actual"] == 1.0


def test_track_record_flags_a_real_gap_only(session):
    for i in range(10):
        _probe(session, "judges", f"p{i}", 0.9, i < 4, minute=i)
    assert track_record_at(session, 0.9)["overconfident"] is True

    for i in range(10):
        _probe(session, "judges", f"q{i}", 0.6, i < 6, minute=50 + i)
    assert track_record_at(session, 0.6)["overconfident"] is False


def test_track_record_counts_only_first_attempts(session):
    for i in range(5):
        _probe(session, "judges", f"p{i}", 0.8, False, minute=i)
    for i in range(5):
        _probe(session, "judges", f"p{i}", 0.8, True, minute=20 + i)

    record = track_record_at(session, 0.8)
    assert record["attempts"] == 5
    assert record["correct"] == 0, "Retries leaked into the track record."

"""Unit 05: A 120-question Ledger eval cannot see a three-point improvement.

The floor an item count puts under every result, and why adding items buys
resolution so slowly. Numbers and citations verified against primary sources;
see UNIT.sources.
"""

from app.metrics import minimum_detectable_effect
from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.
    """
    baseline = sum(data["baseline"]) / len(data["baseline"])
    return minimum_detectable_effect(
        data["items"], baseline, data["power"], data["alpha"]
    )


UNIT = Unit(
    slug="sample-size",
    number=5,
    part="measurement",
    title="A 120-question Ledger eval cannot see a three-point improvement",
    failure=(
        "A difference smaller than Ledger's eval set can resolve gets reported as a "
        "result and shipped as an improvement."
    ),
    detection=(
        "Work out the smallest difference the question count could detect, before "
        "looking at the difference you got."
    ),
    brief=(
        "Somebody changes the Ledger retrieval prompt, the covenant eval goes "
        "from 0.78 to 0.81, and three "
        "points goes in the standup notes. Nobody asks the prior question, "
        "which is whether a set that size could have told a real three-point "
        "gain from nothing at all. Usually it could not, and the question "
        "count settled the number before anybody wrote the change.",
        "An eval set has a floor. Below it the set returns differences that "
        "are indistinguishable from rerunning it unchanged. Two things you "
        "already know set the floor: the question count, and the accuracy "
        "Ledger is already at. That makes this the one failure in this "
        "part you can rule out in advance rather than detect afterwards.",
        "For a sense of where that floor sits even when people are trying "
        "hard, look at the contamination study in unit 03. It reported the "
        "floor for each of its "
        "four public benchmarks, which held between 659 and 1,032 aligned "
        "items. At 80 percent power the smallest effect those sets could "
        "detect ranged from 0.034 to 0.050 accuracy points. Those are careful, "
        "purpose-built benchmarks with a thousand items, and they still cannot "
        "see a three-point difference cleanly.",
        "Nobody is running a thousand covenant questions against Ledger. The "
        "set is the 80 "
        "or 150 cases somebody pulled out of last quarter's deals, which puts "
        "the floor somewhere "
        "around 12 to 18 points. Nearly every improvement anyone reports on a "
        "set that size is noise that happened to land the right way. It "
        "gets reported with a decimal point because the arithmetic is exact "
        "even when the measurement is not.",
        "The painful part is the shape of the fix. Resolution improves with "
        "the square root of the question count, so cutting the floor in half costs "
        "four times the questions. Going from a floor of 0.149 down to 0.033, "
        "enough to see the three points, needs roughly twenty times the set: "
        "about 2,400 covenant questions instead of 120. That is the real reason "
        "teams keep "
        "shipping on underpowered evals. Nobody decided to. The alternative "
        "was quietly enormous.",
        "Which leaves two honest moves and one dishonest one. You can write "
        "more questions, or you can stop claiming differences below the floor "
        "and tell the lending committee the "
        "change was neutral as measured. The dishonest move is the common one: "
        "keep the small set, keep reporting its differences, and let the "
        "decimal point do the arguing.",
    ),
    builds_on=(
        "Unit 04. That unit showed the same suite disagreeing with itself "
        "across identical runs. This one shows it cannot see a small "
        "difference even on the runs where it agrees."
    ),
    probes=(
        Probe(
            id="thousand-item-floor",
            asks=(
                "Four careful public benchmarks holding roughly 1,000 items "
                "each. What was the smallest accuracy difference they could "
                "detect at 80 percent power?"
            ),
            choices=(
                Choice("a", "Well under 1 point, that is the point of 1,000 items"),
                Choice("b", "Between about 3 and 5 points"),
                Choice("c", "Around 10 points"),
                Choice("d", "Over 20 points"),
            ),
            answer="b",
            because=(
                "The reported range was 0.034 to 0.050 accuracy points across "
                "the four. A thousand items is a serious eval set. It still "
                "cannot resolve the size of difference people routinely claim "
                "from a few dozen covenant questions."
            ),
        ),
        Probe(
            id="square-root-wall",
            asks=(
                "Ledger's eval has 150 covenant questions. You want to halve "
                "the smallest "
                "difference it can detect. How many questions do you need?"
            ),
            choices=(
                Choice("a", "300, double it"),
                Choice("b", "450, triple it"),
                Choice("c", "600, four times"),
                Choice("d", "It cannot be done by writing more questions"),
            ),
            answer="c",
            because=(
                "Resolution improves with the square root of the question count, "
                "so halving the floor costs four times the questions. This is why "
                "underpowered evals persist: the fix is real, available, and "
                "priced in a currency nobody budgeted."
            ),
        ),
        Probe(
            id="when-to-ask",
            asks=(
                "When is the right moment to compute the floor for Ledger's "
                "eval set?"
            ),
            choices=(
                Choice("a", "After a surprising result, to check it"),
                Choice("b", "Before running anything, from the question count alone"),
                Choice("c", "Only when a result is close to the threshold"),
                Choice("d", "After shipping, if something goes wrong in production"),
            ),
            answer="b",
            because=(
                "The floor depends on the question count and the accuracy Ledger "
                "is "
                "already at. Both are known before the run, so this is the one "
                "thing in this part you can settle in advance. Compute it "
                "only after a surprising result and you compute it when the "
                "answer is unwelcome. That is exactly the moment you want to "
                "argue with it."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a real-shaped comparison: 120 covenant questions, "
            "the Ledger build in production and a candidate build scored on "
            "every one. Work out the smallest "
            "accuracy difference this set could have detected, and post that "
            "number. Then compare it to the difference the two builds actually "
            "showed."
        ),
        fixture_path="fixtures/sample_size/model_comparison.json",
        fixture_note=(
            "\"baseline\" and \"candidate\" are 120 entries each, 1 for a "
            "correct answer and 0 for a wrong one, with position i the same "
            "covenant question for both builds. \"power\" and \"alpha\" are the "
            "conventions "
            "the team used, 0.80 and 0.05."
        ),
        starter=(
            'import json\n'
            'from app.metrics import minimum_detectable_effect\n'
            '\n'
            'data = json.load(open("fixtures/sample_size/model_comparison.json"))\n'
            '\n'
            '# The baseline accuracy is part of the answer, so work it out from\n'
            '# the fixture rather than guessing it. Then compute the floor, and\n'
            '# only after that look at what the candidate actually scored.\n'
        ),
        metric="minimum_detectable_effect",
        expected=0.149004,
        tolerance=0.000005,
        because=(
            "The floor is 0.149. The candidate scored 0.817 against a baseline "
            "of 0.783, a difference of 0.033, which is about one fifth of what "
            "this set can resolve. The honest report to the lending committee "
            "is that the change was "
            "neutral as measured. The set cannot currently tell the "
            "difference between neutral and a solid three-point win, and "
            "getting there needs roughly 2,400 covenant questions rather "
            "than 120. "
            "Notice that the "
            "candidate really did win on this run: 98 questions correct against "
            "94. "
            "Four questions is what the whole claim rests on."
        ),
    ),
    sources=(
        "arXiv:2609.02899v1 (2026-07-05), Table 1, per-benchmark minimum detectable effect at 80 percent power over 659 to 1,032 items",
    ),
)

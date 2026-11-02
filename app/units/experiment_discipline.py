"""Unit 02: the Ledger A/B test somebody stopped when it looked good.

Peeking inflation under continuous monitoring, and the gap between an
improving offline score and an improving online metric. Numbers and
citations verified against primary sources; see UNIT.sources.
"""

import math

from app.units.types import Choice, Exercise, Probe, Unit


def _two_proportion_p_value(control: int, treatment: int, n: int) -> float:
    """Two-sided p value for two proportions, pooled standard error.

    `n` is the per-arm sample size at this checkpoint, cumulative from the
    start, and the two counts are the conversions in each arm at that point.
    Identical arms give a standard error of zero, which is agreement rather
    than significance, so it returns 1.0 instead of dividing by it.
    """
    pooled = (control + treatment) / (2 * n)
    standard_error = (pooled * (1 - pooled) * 2 / n) ** 0.5
    if standard_error == 0:
        return 1.0
    z = (treatment / n - control / n) / standard_error
    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key. There is no app.metrics function for this one:
    the peeking rule itself is what is being measured.
    """
    checkpoints = data["checkpoints"]
    experiments = data["experiments"]
    declared = 0
    for experiment in experiments:
        for index, n in enumerate(checkpoints):
            p = _two_proportion_p_value(
                experiment["control"][index], experiment["treatment"][index], n
            )
            if p < 0.05:
                declared += 1
                break
    return declared / len(experiments)


UNIT = Unit(
    slug="experiment-discipline",
    number=2,
    part="measurement",
    title="The Ledger A/B test somebody stopped when it looked good",
    failure=(
        "A team watches a dashboard and stops the Ledger prompt test early because "
        "the new prompt "
        "looks ahead. It ships on a p value that never had a real 5 percent error rate."
    ),
    detection=(
        "Fix the sample size before the test starts, and measure your own process "
        "against simulated null data to find the real false positive rate."
    ),
    brief=(
        "A team puts a new retrieval prompt into Ledger behind an A/B test, to see "
        "whether it pulls the amendments in more often. Someone opens the "
        "dashboard every morning to watch how often an underwriter sends an "
        "answer back for a second look. On day "
        "nine the "
        "new prompt pulls ahead and crosses the 5 percent line. The team calls it "
        "a win and ships the prompt that afternoon. Nobody had fixed a sample "
        "size before the test started.",

        "A fixed sample test holds its 5 percent error rate at exactly one "
        "sample size, the one set before the test starts. Checking the result "
        "after every new batch of data is not the same test run once. It is a "
        "new test run again, with its own small chance of a false cross. Each "
        "look adds another chance for noise alone to clear the bar. Stack "
        "enough looks together and the real false positive rate climbs far "
        "past the number printed on the dashboard.",

        "Evan Miller ran the simplest version of this experiment, to measure "
        "the damage directly. Both arms convert at the same 50 percent rate, so "
        "the treatment carries no real effect at all. He checked the result "
        "after every single visitor, up to a cap of 150. He stopped the "
        "instant the p value crossed 0.05. Checked that way, a nominal 5 "
        "percent test declared a false winner 26.1 percent of the time, more "
        "than five times the printed number.",

        "The same inflation shows up in work built for commercial A/B testing "
        "platforms, not just toy simulations. Ramesh Johari, Leo Pekelis, and "
        "David Walsh published a direct measurement of it in 2015. Even at "
        "10,000 samples, a size common in real online tests, they found that "
        "type I error can easily increase fivefold. A nominal 5 percent test "
        "becomes something closer to 25 percent, simply because someone kept "
        "looking. Nothing about the data changed, only the number of times a "
        "person checked it changed.",

        "The fix is not more willpower about not looking. The fix is to plan "
        "for looking before the test starts. A power calculation sets one "
        "sample size in advance, counted in covenant questions, and the team "
        "holds to it. When a team must "
        "look early anyway, it should use a method built for that. A group "
        "sequential design and an always valid confidence sequence both qualify.",

        "A group sequential design spends a fixed slice of the total error "
        "budget at each planned look. The looks then add up to 5 percent "
        "instead of multiplying past it. Alpha spending functions, such as the "
        "O'Brien-Fleming boundary, cap how much of that budget an early look "
        "can spend. An always valid method, built on the same "
        "sequential math, computes a p value that stays correct at any point "
        "someone chooses to stop.",

        "The detection is cheap, which is what makes skipping it indefensible. "
        "Build many simulated Ledger experiments where the new prompt carries "
        "no real "
        "effect at all. Run the decision rule the team actually plans to use "
        "against every one of them. Count how often that rule declares a "
        "winner anyway. That fraction is the true false positive rate of the "
        "process, not the number printed on a textbook page.",

        "A second trap sits next to this one, and it catches teams who did "
        "everything else right. A rise in Ledger's offline eval score does not "
        "mean the live metric will follow it. That live metric is how often an "
        "underwriter sends an answer back. The engineers who built the "
        "YouTube recommendation system said so directly: live A/B results are "
        "not always correlated with offline experiments. At Microsoft, "
        "researchers reported that only about one third of tested ideas "
        "actually helped the metric they targeted. State which metric decides "
        "before the test starts, offline or online, and then run the real "
        "test to find out.",
    ),
    builds_on=(
        "Unit 01. A judge you have shown to be stable is still worth "
        "nothing if you stop the run at the moment it says what you hoped."
    ),
    probes=(
        Probe(
            id="stopped-early-p-value",
            asks=(
                "A team checked its dashboard every day for three weeks. It "
                "stopped the Ledger prompt test the moment it saw p less than "
                "0.05 on day "
                "nine. What does that p value establish?"
            ),
            choices=(
                Choice("a", "That the new prompt beat the shipped one at a real 5 percent error rate"),
                Choice("b", "Very little, since repeated looks can push a true 5 percent test well past 25 percent"),
                Choice("c", "That the new prompt has no effect at all"),
                Choice("d", "That the team should have waited for a bigger sample before checking anything"),
            ),
            answer="b",
            because=(
                "A single p value crossed once, at a size fixed in advance, "
                "means what the textbook says it means. Checked at nine "
                "separate points and stopped at the first crossing, it means "
                "almost nothing of the kind. Evan Miller measured this "
                "directly: checking continuously under a true null pushed a "
                "nominal 5 percent test up to 26.1 percent. Johari, Pekelis, "
                "and Walsh found the same pattern at 10,000 samples, where "
                "type I error can increase fivefold. The dashboard number was "
                "honest, but the question it answered was the wrong one."
            ),
        ),
        Probe(
            id="method-for-peeking",
            asks=(
                "A team wants to check the Ledger prompt test every day without "
                "breaking the "
                "5 percent guarantee of that test. What should it do?"
            ),
            choices=(
                Choice("a", "Nothing, the extra looks average out over time"),
                Choice("b", "Fix one single look at the very end and ignore every earlier number"),
                Choice("c", "Pick a method built for repeated looks, such as a group sequential design or an always valid confidence sequence"),
                Choice("d", "Lower the threshold to p less than 0.01 and keep checking as often as it likes"),
            ),
            answer="c",
            because=(
                "A fixed sample test only holds its 5 percent rate at the one "
                "size it was built for. Checking it every day and stopping at "
                "the first crossing is a different test with a much higher "
                "real error rate. A group sequential design plans the looks "
                "in advance and spends a fixed slice of the error budget at "
                "each one. An always valid method computes a p value built to "
                "stay correct no matter when someone decides to stop. Neither "
                "method removes the cost of checking early, both just make "
                "that cost honest."
            ),
        ),
        Probe(
            id="offline-online-gap",
            asks=(
                "Ledger's offline eval score improves after a prompt change, "
                "and you have not run an online test yet. What does the "
                "improved offline score establish about the live metric?"
            ),
            choices=(
                Choice("a", "That the live metric will improve by roughly the same amount"),
                Choice("b", "Nothing on its own, since offline and online results are known to diverge"),
                Choice("c", "That the new prompt is ready to ship without an online test"),
                Choice("d", "That the offline metric is wrong whenever it disagrees with intuition"),
            ),
            answer="b",
            because=(
                "An improving offline number says something true about the "
                "offline number and nothing certain about the live one. The "
                "engineers who built the YouTube recommendation system said so "
                "directly: live A/B results are not always correlated with "
                "offline experiments. At Microsoft, researchers reported that "
                "only about one third of tested ideas actually helped the "
                "metric they targeted, despite looking promising enough to "
                "test. The two numbers answer different questions. A team has "
                "to decide which one actually gets to decide, and then run "
                "the real test to find out."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of 3,500 simulated Ledger prompt tests "
            "where the new prompt carries no real effect at all. Apply the "
            "stated peeking rule at the five checkpoints in each experiment. "
            "Work out what share of these null experiments would have "
            "declared a winner. Post that share."
        ),
        fixture_path="fixtures/experiment_discipline/ab_peeking.json",
        fixture_note=(
            "The fixture holds 3,500 experiments, each with a control arm on "
            "the shipped prompt and a treatment arm on the new one. An "
            "underwriter sends an answer back for a second look at the same 20 "
            "percent rate in both arms, so the real effect "
            "is zero. The fixture checks each arm at five checkpoints: 200, "
            "400, 600, 800, and 1,000 answers, with every count cumulative "
            "from the start. At each checkpoint, in order, compare the "
            "cumulative treatment and control rates with a two-proportion "
            "z-test and a pooled standard error. The rule is two sided, so declare a winner the "
            "moment any checkpoint produces a p value under 0.05, and stop "
            "looking at that experiment. An experiment that never crosses "
            "0.05 at any of the five checkpoints counts as no winner."
        ),
        starter=(
            'import json\n'
            'import math\n'
            '\n'
            'data = json.load(open("fixtures/experiment_discipline/ab_peeking.json"))\n'
            'checkpoints = data["checkpoints"]\n'
            'experiments = data["experiments"]\n'
            '\n'
            '\n'
            'def p_value(control, treatment, n):\n'
            '    """Two-sided two-proportion z test, pooled standard error."""\n'
            '    pooled = (control + treatment) / (2 * n)\n'
            '    standard_error = (pooled * (1 - pooled) * 2 / n) ** 0.5\n'
            '    if standard_error == 0:\n'
            '        return 1.0\n'
            '    z = (treatment / n - control / n) / standard_error\n'
            '    return 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))\n'
            '\n'
            '\n'
            'print("null experiments:", len(experiments))\n'
            'print("checkpoints, answers per arm:", checkpoints)\n'
            '\n'
            'last = len(checkpoints) - 1\n'
            'one_look = [\n'
            '    e\n'
            '    for e in experiments\n'
            '    if p_value(e["control"][last], e["treatment"][last], checkpoints[last])\n'
            '    < 0.05\n'
            ']\n'
            'print("checked ONCE, at the final checkpoint, winners declared:",\n'
            '      len(one_look) / len(experiments))\n'
            '\n'
            '# TODO: nobody ran it that way. The team looked at every checkpoint and\n'
            '# shipped the first time a look came in under 0.05. Decide what that\n'
            '# rule counts as a declared winner, apply it to these experiments, and\n'
            '# print the share. The real effect in every one of them is zero, so\n'
            '# whatever comes out is the error rate the process actually had.\n'
        ),
        metric="peeking_false_positive_rate",
        expected=0.1469,
        tolerance=0.004,
        because=(
            "Checked only once, at the final checkpoint of 1,000 answers per "
            "arm, this fixture's own false positive rate comes out at 0.0489, "
            "almost exactly the nominal 5 percent. Checked at all five "
            "checkpoints, and stopped at the first one to cross 0.05, the "
            "same fixture declares a winner 0.1469 of the time. That is "
            "nearly three times the advertised rate. Nothing in the fixture "
            "changed between those two measurements, only the rule applied to "
            "it did. That gap is the whole lesson. A p value is honest only "
            "about the rule that produced it, never about the rule you wish "
            "you had used."
        ),
    ),
    sources=(
        "evanmiller.org/how-not-to-run-an-ab-test.html (read 2026-10-29), "
        "continuous monitoring simulation at a 50 percent baseline conversion "
        "rate with zero true effect, checking after every visitor up to 150 "
        "and stopping at the first p under 0.05, reporting a 26.1 percent "
        "false positive rate against a nominal 5 percent test",
        "arXiv:1512.04922 (2015-12-15), Johari, Pekelis, and Walsh, Always "
        "Valid Inference: Bringing Sequential Analysis to A/B Testing, "
        "reporting that continuous monitoring at 10,000 samples can increase "
        "type I error fivefold, and defining the always valid p value and "
        "the mSPRT used to avoid it",
        "dl.acm.org/doi/10.1145/2959100.2959190 (RecSys 2016), Covington, "
        "Adams, and Sargin, Deep Neural Networks for YouTube Recommendations, "
        "stating that live A/B results are not always correlated with "
        "offline experiments",
        "Kohavi and Thomke, The Surprising Power of Online Experiments, "
        "Harvard Business Review, September-October 2017, reporting that "
        "about one third of tested ideas at Microsoft proved effective, one "
        "third showed no difference, and one third had a negative impact",
    ),
)

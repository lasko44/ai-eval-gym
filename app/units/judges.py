"""Unit 01: LLM judges that flip when you swap the order.

Position bias and the raw-versus-chance-corrected agreement gap. Numbers and
citations verified against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


UNIT = Unit(
    slug="judges",
    number=1,
    title="LLM judges that flip when you swap the order",
    failure="A judge scores the same pair differently depending on which answer it sees first.",
    detection="Run every pair in both orders and measure the flip rate.",
    brief=(
        "Once you have more than a handful of outputs to evaluate, hand grading stops "
        "scaling. Almost everyone reaches for the same thing: another model as the "
        "judge. You show it two answers, ask which is better, and treat the verdict as "
        "a measurement.",
        "It is not a measurement until you have shown it is stable. A judge has "
        "preferences that have nothing to do with quality, and the loudest one is "
        "position. Show it answer A then answer B and it picks A. Swap them and it "
        "picks the other one. Nothing about the answers changed.",
        "The study measured this across 21 general-purpose LLM judges drawn from nine "
        "providers, over 541,000 judgments. Position "
        "bias ranged from 0.002 to 0.192 depending on the judge, so at the bad end "
        "nearly one verdict in five turns on ordering alone. If you did not swap the "
        "order, that noise went straight into your eval numbers and you shipped on it.",
        "There is a second trap in the same place, and it catches more people. You "
        "check your judge against human labels, get something like 80 percent "
        "agreement, and call it validated. But two raters flipping coins agree half "
        "the time, so raw agreement counts luck as skill. In the same study, "
        "correcting for chance cut agreement by a cohort mean of 38.6 points on "
        "MT-Bench, where the range across the 21 judges was 33.8 to 41.3. A judge "
        "you believed was in the eighties can be in the forties once you remove "
        "coincidence.",
        "How large that correction gets is not a constant, and assuming it is will "
        "mislead you in the other direction. The same study measured a mean "
        "deflation of 23.7 points on JudgeBench and 10.4 points on RewardBench. It "
        "attributes the difference to the label distribution of each benchmark. The "
        "more lopsided the labels, the more agreement you get for free, and the "
        "bigger the correction. So the number to carry is not 39, it is that raw "
        "agreement always flatters a judge by an amount you cannot guess without "
        "computing it.",
        "The detection is cheap, which is what makes skipping it indefensible. Run "
        "every comparison twice, once in each order, and count how often the verdict "
        "changes. That fraction is your flip rate, and it is an upper bound on how "
        "much of your eval is noise. Report it next to any number your judge "
        "produced, and report chance-corrected agreement rather than raw agreement "
        "when you validate against humans.",
    ),
    probes=(
        Probe(
            id="worst-bias",
            asks=(
                "Across 21 general-purpose LLM judges and 541,000 judgments, the worst "
                "position bias measured was roughly what share of verdicts flipping "
                "on order alone?"
            ),
            choices=(
                Choice("a", "Under 2 percent, it is a rounding error"),
                Choice("b", "Around 5 percent"),
                Choice("c", "Around 19 percent, nearly one in five"),
                Choice("d", "Over 40 percent, worse than a coin"),
            ),
            answer="c",
            because=(
                "Measured bias ran from 0.002 at the best judge to 0.192 at the worst, "
                "so the spread between judges is two orders of magnitude. The useful "
                "lesson is not the number, it is that you cannot know which end your "
                "judge sits at without swapping the order yourself. A judge someone "
                "else validated tells you nothing about yours."
            ),
        ),
        Probe(
            id="kappa-gap",
            asks=(
                "Your judge agrees with human labels 80 percent of the time on an "
                "MT-Bench style pairwise set. You correct for agreement that would "
                "happen by chance. What happens to the number?"
            ),
            choices=(
                Choice("a", "It barely moves, chance correction is a formality"),
                Choice("b", "It drops a few points, call it 75 percent"),
                Choice("c", "It drops by something near 39 points, into the forties"),
                Choice("d", "It goes up, since chance correction rewards consistency"),
            ),
            answer="c",
            because=(
                "On MT-Bench the cohort mean deflation was 38.6 points, with every one of "
                "the 21 judges landing between 33.8 and 41.3. The mechanism is simple. "
                "On a two way choice, two raters who both guess agree half the time, so "
                "much of your 80 percent can be coincidence. Note the scoping in the "
                "question, because it is doing real work. The same study found a mean "
                "deflation of only 10.4 points on RewardBench, whose label distribution "
                "is different. Had the question not named the benchmark, no single "
                "number would have been defensible, which is the habit worth taking "
                "from this probe."
            ),
        ),
        Probe(
            id="what-it-proves",
            asks=(
                "You swap the order on every pair and measure a flip rate of 0.02. "
                "What have you established?"
            ),
            choices=(
                Choice("a", "The judge is reliable, so you can trust the eval numbers"),
                Choice("b", "The judge is stable under ordering, which says nothing yet about whether it agrees with humans"),
                Choice("c", "The judge has bias, since any flip rate above zero disqualifies it"),
                Choice("d", "Nothing, flip rate is only meaningful above 100 pairs"),
            ),
            answer="b",
            because=(
                "A low flip rate buys you consistency, not correctness. A judge can be "
                "perfectly stable and perfectly wrong. It will give you the same "
                "verdict every time, and that verdict can still disagree with every "
                "human who looks at it. Reliability and validity are separate "
                "properties and you need evidence for both. This is the distinction "
                "that the phrase 'we validated our judge' usually hides."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of 200 judge calls, each scored once "
            "in each order. Measure how often the verdict changed, and post the number."
        ),
        fixture_path="fixtures/judges/ab_pairs.json",
        fixture_note=(
            "Two lists of 200 verdicts each. The first is what the judge said with the "
            "answers in their original order, the second is the same 200 comparisons "
            "with the two answers exchanged. Each entry is the winner, \"A\" or \"B\"."
        ),
        starter=(
            'import json\n'
            'from app.metrics import flip_rate\n'
            '\n'
            'pairs = json.load(open("fixtures/judges/ab_pairs.json"))\n'
            '\n'
            '# flip_rate is already in the library. Work out what to pass it,\n'
            '# and what the number means once you have it.\n'
            'print(flip_rate(pairs["first"], pairs["swapped"]))\n'
        ),
        metric="flip_rate",
        expected=0.185,
        tolerance=0.0005,
        because=(
            "Swapping the order changed 37 of the 200 verdicts, so the flip "
            "rate is 0.185. That is at the ugly end of the published range. A judge "
            "behaving like this contributes more noise to your eval than most of "
            "the differences you are trying to detect with it. Any A/B result "
            "it produced under about 20 points is unreadable."
        ),
    ),
    sources=(
        "arXiv:2606.19544 (2026-06-17), 21 judges, 541k judgments, position bias and chance-corrected agreement",
        "hamel.dev/blog/posts/evals-faq (2026-09-18), on why judge validation is where eval work actually goes",
    ),
)

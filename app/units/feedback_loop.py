"""Unit 06: A Ledger eval set frozen at launch stays green while quality falls.

Why a suite nobody adds to tests the bugs you already fixed, and what the
drifting question mix does to the score it reports. Numbers and citations
verified against primary sources; see UNIT.sources.

The measurement is inline rather than in app/metrics, because it is one set of
rates weighted by two different mixes, and that reads better beside the thing
it teaches.
"""

from collections import Counter

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.

    The fixture parses to a dict with two lists, "launch_suite" and
    "production". Accuracy per category is measured once, on the production
    records, and then scored under two question mixes: the launch suite's and
    the live one. Holding the rates still is the whole instrument, because it
    leaves the mix as the only thing that can move the answer.
    """
    live = data["production"]
    suite = data["launch_suite"]

    live_count = Counter(record["category"] for record in live)
    live_correct = Counter()
    for record in live:
        live_correct[record["category"]] += record["correct"]
    accuracy = {name: live_correct[name] / live_count[name] for name in live_count}

    suite_count = Counter(case["category"] for case in suite)

    on_launch_mix = sum(
        suite_count[name] / len(suite) * accuracy[name] for name in suite_count
    )
    on_live_mix = sum(
        live_count[name] / len(live) * accuracy[name] for name in live_count
    )
    return on_launch_mix - on_live_mix


UNIT = Unit(
    slug="feedback-loop",
    number=6,
    part="measurement",
    title="A Ledger eval set frozen at launch stays green while quality falls",
    failure=(
        "Ledger's covenant suite has not gained a case since launch. It tests "
        "the bugs somebody already fixed, while the questions underwriters "
        "ask move away from it."
    ),
    detection=(
        "Measure accuracy per category on live traffic. Score those same "
        "rates twice, under the launch suite's mix of categories and under "
        "the current one. The difference is what the frozen mix is worth."
    ),
    brief=(
        "The posting asks its owner to build the evaluation and feedback loop. "
        "That means offline evals, tracing, regression gates in continuous "
        "integration, and production failures and user edits turning into new "
        "eval cases. The first three feel like the work and the fourth reads "
        "like housekeeping. It is the opposite. The first three are an "
        "instrument, and the fourth is the only thing that keeps the "
        "instrument pointed at the system people are using.",
        "Seegmiller and Preum measured what happens when it is not. They took "
        "real prompts submitted to a deployed assistant and built 192 "
        "settings from them. Each setting pairs one training distribution "
        "with a later or different one, along three axes: time, user group "
        "and geography. They trained 81 models on 4.68 million training "
        "prompts and evaluated on 57.6 thousand prompts. Their headline "
        "figure is a 73 percent average loss.",
        "Read what that number measures before you use it. It is not a 73 "
        "point fall in a score. For each setting they also trained an oracle, "
        "a model fitted to prompts from the evaluation bucket itself. They "
        "then compared the two models answer by answer, and a judge model "
        "picked the winner. The 73 percent is the share of those comparisons "
        "the stale model lost, averaged over 192 settings and three model "
        "families, with ties counted apart. The figure says the stale model "
        "lost, not how far any score fell.",
        "The spread inside that average is the useful part. Along the time "
        "axis the loss rate was 44 percent against a win rate of 37 percent, "
        "which is close to a tie. Along the user group and geography axes it "
        "was 87 and 88 percent, with win rates of 2 percent and 1 percent. "
        "Their worked example takes one model trained on the first four time "
        "buckets and evaluates it on the seventh. It lost 53 percent of the "
        "comparisons and tied 15 percent. A new population of users hurt far "
        "more than the calendar did.",
        "Vela and colleagues show the structural half of the problem. They "
        "ran 4 standard model types over 32 longitudinal datasets from "
        "weather, hospital operations, airlines and finance. That is 128 "
        "pairs, and quality degraded in 91 percent of them. Their measure is "
        "a ratio: error on a later test set over error on a test set from "
        "training time. Near zero lag that ratio sits close to 1.0, which is "
        "the sentence to sit with. A suite written at launch is the "
        "denominator, so the one number it cannot report is its own "
        "staleness.",
        "That is why the intake matters more than the gate. A production "
        "failure and an underwriter edit are the only supply of cases from "
        "the distribution Ledger serves now. An edit arrives already "
        "labelled, with a right answer from somebody accountable for it. "
        "Without that intake the suite ages at whatever rate the question mix "
        "moves. The gate still passes, because a gate only ever reports on "
        "the cases it holds.",
        "So measure the mix, not only the score. Take accuracy per category "
        "from live traffic, then score those same rates under two mixes, the "
        "launch suite's and the current one. If the two disagree, the suite "
        "reports a distribution nobody asks about any more. The gap between "
        "them is the number to put in front of the stakeholder who still "
        "trusts the gate.",
    ),
    builds_on=(
        "Units 01 to 05. Those five earn a suite its credibility. You "
        "checked the judge, nobody stopped the run early, and the set is "
        "clean. The gate reads a spread, and the item count can see the "
        "effect. None of that survives the questions themselves changing."
    ),
    probes=(
        Probe(
            id="what-73-percent-measures",
            asks=(
                "A paper reports a 73 percent average loss for models whose "
                "training prompts came from an earlier or different "
                "population. What did they actually measure?"
            ),
            choices=(
                Choice("a", "The models answered 73 percent fewer questions correctly"),
                Choice("b", "Their score fell to 27 percent of its original value"),
                Choice(
                    "c",
                    "They lost 73 percent of head-to-head comparisons against a "
                    "model fitted to the current prompts",
                ),
                Choice(
                    "d",
                    "73 percent of the evaluation prompts were unlike the "
                    "training ones",
                ),
            ),
            answer="c",
            because=(
                "It is a pairwise loss rate. They compared each stale model "
                "answer by answer against an oracle fitted to prompts from "
                "the evaluation bucket itself. A judge model picked a winner, "
                "and ties counted as a third category. The figure is the "
                "average share of those comparisons the stale model lost, "
                "over 192 settings and three model families. That tells you "
                "it lost, and not by how much. The per-axis numbers matter "
                "for the same reason: 44 percent along time, 87 and 88 "
                "percent across user groups and regions."
            ),
        ),
        Probe(
            id="what-a-green-suite-rules-out",
            asks=(
                "Ledger's launch suite has run on every build for six months "
                "and the score has not moved. What has it ruled out?"
            ),
            choices=(
                Choice(
                    "a",
                    "That quality has fallen, since the suite covers the "
                    "system end to end",
                ),
                Choice(
                    "b",
                    "Only that the launch cases still pass, which is not a "
                    "claim about current traffic",
                ),
                Choice(
                    "c",
                    "That the question mix drifted, because drift would have "
                    "shown in the score",
                ),
                Choice(
                    "d",
                    "That the model changed, which is the only thing that "
                    "could lower quality",
                ),
            ),
            answer="b",
            because=(
                "A frozen suite is a fixed set of inputs, so a flat score is "
                "evidence about those inputs and nothing else. Vela and "
                "colleagues make the shape of it explicit. Their degradation "
                "measure divides error on a later test set by error on a test "
                "set from training time. Near zero lag the ratio sits close "
                "to 1.0. Degradation turned up in 91 percent of their 128 "
                "model and dataset pairs. A test set from training time is "
                "the one place it cannot appear."
            ),
        ),
        Probe(
            id="what-to-do-with-an-edit",
            asks=(
                "An underwriter corrects one of Ledger's covenant answers in "
                "the interface. What is the cheapest correct thing to do with "
                "that correction?"
            ),
            choices=(
                Choice("a", "Open a bug, fix the retrieval, and close it"),
                Choice(
                    "b",
                    "Add it to the eval set as a case, with the underwriter's "
                    "answer as the label",
                ),
                Choice(
                    "c",
                    "Log it for the quarterly review, so the trend can be "
                    "read in aggregate",
                ),
                Choice(
                    "d",
                    "Add it to the fine-tuning set, since it is a labelled "
                    "example",
                ),
            ),
            answer="b",
            because=(
                "The correction is the one thing production gives you that an "
                "eval set cannot buy. It is an input from the current "
                "distribution, with a right answer from somebody accountable "
                "for it. If you fix the bug and close it, the next regression "
                "in that clause is invisible all over again. Use it as "
                "training data and it is worth nothing as a test, for the "
                "reason unit 03 gives. The quarterly review is exactly the "
                "lag both cited papers measure, and it answers after the "
                "quarter it would have saved."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships Ledger's 240 case launch suite, rescored against "
            "the build in production, beside 3600 labelled live questions "
            "from the quarter six months after launch. Measure accuracy per "
            "category on the live questions. Then score those same rates "
            "twice, under the launch suite's mix and under the live mix, and "
            "report the difference."
        ),
        fixture_path="fixtures/feedback_loop/production_drift.json",
        fixture_note=(
            "\"launch_suite\" holds 240 cases, each with a question "
            "\"category\" and a \"correct\" flag from the latest run against "
            "the current build. \"production\" holds 3600 live underwriter "
            "questions in the same shape, labelled from underwriter "
            "corrections and a sampled review. One live category has no case "
            "in the launch suite at all. Every label came from a seeded "
            "Bernoulli draw, and the file carries the seed."
        ),
        starter=(
            'import json\n'
            'from collections import Counter\n'
            '\n'
            'data = json.load(open("fixtures/feedback_loop/production_drift.json"))\n'
            '\n'
            '# Accuracy per category, measured ONCE, on the production records.\n'
            '# Then weight those rates two ways: by the launch suite\'s count\n'
            '# per category, and by the live count per category. Subtract.\n'
            '# Holding the rates still is the point. Anything that moves is\n'
            '# the mix.\n'
            '#\n'
            '# Score the launch suite on its own "correct" flags too, and keep\n'
            '# that number beside the live score. One of the three is what the\n'
            '# gate reports.\n'
        ),
        metric="frozen_mix_gap",
        expected=0.153509,
        tolerance=0.0005,
        because=(
            "The launch suite scores 0.888 on its own cases, which is the "
            "number the gate reports. Live traffic scores 0.704, and 0.154 of "
            "that 0.184 gap is the question mix alone. Only 0.030 of it comes "
            "from the suite's own cases, which run easier inside each "
            "category, exactly as cases written off fixed bugs would. The "
            "counts show the driver. Single clause lookups were 132 of the "
            "240 launch cases and are now 792 of 3600 live questions, while "
            "amendment stacking went from 36 cases to 1116 questions at 0.625 "
            "accuracy. Restricted payment builder questions, 432 of them at "
            "0.461, have no case in the suite at all, so nothing in the gate "
            "can move while they fail."
        ),
    ),
    sources=(
        "arXiv:2604.17650v1 (2026-04-19), Seegmiller and Preum, Measuring Distribution Shift in User Prompts and Its Effects on LLM (Large Language Model) Performance, fetched 2026-11-01: 192 post-deployment prompt shift settings, 81 models trained on 4.68 million prompts, evaluation on 57.6 thousand prompts, and the 73 percent average loss rate, which Table 2 and Table 6 define as the share of head-to-head comparisons a model trained on shifted prompts loses to an oracle model trained on prompts from the evaluation bucket. Per-axis loss rates of 0.4435 over time, 0.8723 across user groups and 0.8820 across regions, with win rates of 0.3706, 0.0180 and about 0.01, and the worked example in Section 2.2 of a model trained on months 0 to 3 losing 53 percent and tying 15 percent on month 7",
        "Vela, Sharp, Zhang, Nguyen, Hoang and Pianykh, Temporal quality degradation in AI models, Scientific Reports vol 12 article 11654 (2022), Digital Object Identifier (DOI) 10.1038/s41598-022-15245-z, fetched 2026-11-01 from the open-access copy on PubMed Central at pmc.ncbi.nlm.nih.gov: 4 standard model types over 32 longitudinal datasets from weather, hospital operations, airlines and finance for 128 pairs, degradation observed in 91 percent of them, and the relative error measure defined in Materials and methods as error on a test set produced after training divided by error on a test set produced at training time, close to 1.0 at near zero lag",
    ),
)

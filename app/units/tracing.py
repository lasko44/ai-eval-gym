"""Unit 07: the Ledger score fell, and the score cannot say which step fell.

An aggregate number detects a regression and localises nothing. Without a
per-step record graded on the step's own label, a ranking failure and a model
regression produce the same drop, so the team retrains the part it knows how
to change. Numbers and citations verified against primary sources; see
UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit

STEPS = ("retrieve", "rank", "read", "answer")


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.

    The fixture parses to a dict holding "steps" and "releases". Each release
    is a list of one record per request, and each record holds a 1 or 0 for
    every step. The metric is computed inline here on purpose: app/metrics/ is
    the shared library, and a one-unit measurement does not belong in it.
    """
    steps = tuple(data["steps"])
    conditional: dict[str, dict[str, float]] = {}
    for release, records in data["releases"].items():
        rates = {}
        for position, step in enumerate(steps):
            earlier = steps[:position]
            eligible = [
                record
                for record in records
                if all(record["steps"][name] == 1 for name in earlier)
            ]
            rates[step] = sum(r["steps"][step] for r in eligible) / len(eligible)
        conditional[release] = rates

    return max(
        conditional["baseline"][step] - conditional["candidate"][step]
        for step in steps
    )


UNIT = Unit(
    slug="tracing",
    number=7,
    part="measurement",
    title="The Ledger score fell, and the score cannot say which step fell",
    failure=(
        "A release drops the covenant score. The team holds one number for the "
        "whole pipeline, so it retrains the model when the ranking step was at "
        "fault."
    ),
    detection=(
        "Grade every step of every request against that step's own label. "
        "Count only the requests where every earlier step was right, then "
        "compare the two releases step by step."
    ),
    brief=(
        "A release goes out and the Ledger covenant score falls. On the "
        "fixture this unit ships it falls from 0.6233 to 0.4817, and nothing "
        "in that pair of numbers says what moved it. The candidate release "
        "carried a new embedding model, a rebuilt index, a changed reranker "
        "and two prompt edits. The score ranks none of them. What happens next "
        "is usually a rollback or a retrain of the model, because the model is "
        "the part a team knows how to change.",
        "Finding the step is a harder problem than finding the drop, and "
        "somebody has measured how much harder. The Who&When dataset holds "
        "failure logs from 127 multi-agent systems, each a group of large "
        "language model (LLM) agents. Every log names the agent and the step "
        "responsible for that failure, which gives 184 distinct attribution "
        "tasks. The authors ran three automated attribution methods over it. "
        "The best one named the responsible agent 53.5 percent of the time. "
        "The same method named the decisive step 14.2 percent of the time, and "
        "some methods scored below random.",
        "The shape of that gap is the part to sit with. On the "
        "algorithm-generated half of the set, reading the whole trace in one "
        "pass named the agent best, at 54.33 percent. On that same half it "
        "named the step 12.50 percent of the time, against a random baseline "
        "of 19.06 percent. Walking the trace one step at a time reversed both "
        "numbers, to 35.20 percent on the agent and 25.51 percent on the step. "
        "So localisation is not a property of owning a trace. It is a property "
        "of how the trace gets read, and the reading that summarises best "
        "localises worst.",
        "A second group measured what per-step grading buys you. They split a "
        "web agent into three stages, planning, grounding, and action "
        "selection, and scored each stage on its own over 490 recorded "
        "actions. Their strongest configuration scored 74.44 on finding the "
        "relevant element and 70.17 on predicting the next action. Turning "
        "that prediction into a concrete action scored 62.87. Choosing one "
        "action from the candidates scored 54.29 with their own strategy and "
        "48.78 with a first-valid heuristic. The planning step sat 15.88 "
        "points above the last step, and an end-to-end score reports the last "
        "step only.",
        "Per-step numbers carry a trap of their own, and the fixture carries "
        "it too. Grade each step over every request and the candidate release "
        "reads as a comprehension problem: the read step falls from 0.7050 to "
        "0.5833. Grade each step only on the requests where every earlier step "
        "was right and the read step goes up instead, from 0.8305 to 0.8407. "
        "Both numbers are arithmetic. The first one counts requests where the "
        "ranking step gave the reader the wrong clause, so it books the "
        "ranking loss on the reader's line. A step graded on a broken input "
        "reports its input and not itself.",
        "Graded that way, the step rates compose exactly. Multiply the four "
        "conditional rates and the end-to-end accuracy comes back, 0.6233 for "
        "the baseline and 0.4817 for the candidate. That identity is what "
        "gives a drop an address. The ranking step lost 0.2107 of its own "
        "conditional accuracy while the other three moved by less than 0.014 "
        "in either direction. It also shows why an aggregate understates: the "
        "end-to-end score fell 0.1417, which is the ranking loss after the "
        "three healthy steps have diluted it.",
        "So the instrument is one record per request per step, carrying that "
        "step's outcome against that step's own label. A span name and a "
        "duration cannot do the job, because a grader has nothing to compare "
        "them to. The governance part reaches a different ask later: an audit "
        "trace has to answer why Ledger said one thing to one underwriter in "
        "March. The question here is which step owns a loss you have already "
        "measured. One set of records can serve both, and a team holding only "
        "latency and token counts has neither.",
    ),
    builds_on=(
        "Unit 04. A step-level comparison only earns attention once the "
        "aggregate drop beats the spread an unchanged suite produces on "
        "its own. Unit 04 is where you learn to measure that spread "
        "first."
    ),
    probes=(
        Probe(
            id="what-an-aggregate-drop-licenses",
            asks=(
                "Ledger's covenant score falls from 0.62 to 0.48 after a "
                "release that changed the embedding model, the index, the "
                "reranker and two prompts. What has the score established?"
            ),
            choices=(
                Choice("a", "The model regressed, since the model is the only part that produces the answer"),
                Choice("b", "That something in the release cost accuracy, and nothing about which of the four changes it was"),
                Choice("c", "That retrieval is at fault, because a drop that large cannot come from generation"),
                Choice("d", "Nothing at all, because a single score is not a measurement"),
            ),
            answer="b",
            because=(
                "The score is a real measurement and it is one number over the "
                "whole pipeline. It detects the regression and ranks none of "
                "the four candidate causes, because every one of them lands on "
                "the same number. Naming the model, or naming retrieval, is a "
                "guess dressed as a finding. Calling the score worthless goes "
                "too far the other way: detection is exactly what it is good "
                "for."
            ),
        ),
        Probe(
            id="one-pass-versus-step-by-step",
            asks=(
                "Two methods ran over the Who&When failure logs. One read the "
                "whole trace in a single pass. The other walked it one step at "
                "a time. How did the two compare?"
            ),
            choices=(
                Choice("a", "The one-pass read won on both the agent and the step, since it sees the whole context"),
                Choice("b", "The step-by-step walk won on both, since it looks at everything in more detail"),
                Choice("c", "The one-pass read named the agent better and named the step worse than a random baseline"),
                Choice("d", "Neither beat a random baseline on either question"),
            ),
            answer="c",
            because=(
                "On the algorithm-generated half of the set, the one-pass read "
                "reached 54.33 percent on the agent and 12.50 percent on the "
                "step. Random scored 19.06 percent on the step. The "
                "step-by-step walk came in at 35.20 percent on the agent and "
                "25.51 percent on the step. Neither method wins both "
                "questions, so the way a trace is read decides which question "
                "it can answer."
            ),
        ),
        Probe(
            id="grading-a-step-on-a-broken-input",
            asks=(
                "Graded over every request, Ledger's read step falls from "
                "0.705 to 0.583 across two releases. Graded only on requests "
                "where retrieve and rank were both right, it rises from 0.831 "
                "to 0.841. Which reading supports a claim about the reader?"
            ),
            choices=(
                Choice("a", "The first, since it covers every request and throws nothing away"),
                Choice("b", "The second, since the first one counts requests where the ranking step gave the reader the wrong clause"),
                Choice("c", "Neither, because two numbers that disagree cancel each other out"),
                Choice("d", "Both, since they measure the same step and the gap is a rounding artefact"),
            ),
            answer="b",
            because=(
                "Give a reader the wrong clause and it answers wrongly, and "
                "that failure belongs to whatever picked the clause. Counting "
                "it against the reader books an upstream loss on a downstream "
                "line. That is how one broken step smears itself across every "
                "step after it. Keeping only the requests with a clean prefix "
                "costs sample size and buys the one version of the number that "
                "is about the reader."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships 600 covenant questions put to two Ledger "
            "releases, with a 1 or a 0 for each of the four pipeline steps. "
            "Work out each release's end-to-end accuracy, then each step's "
            "conditional accuracy. Post the largest fall in any single step's "
            "conditional accuracy, baseline minus candidate."
        ),
        fixture_path="fixtures/tracing/step_traces.json",
        fixture_note=(
            "\"releases\" holds two lists, \"baseline\" and \"candidate\", of "
            "600 records each, and the same 600 covenant questions went to "
            "both. Each record carries \"steps\", with a 1 or a 0 for retrieve, "
            "rank, read and answer, in that order. A 1 means that step "
            "produced the right thing for that question, graded against the "
            "step's own label. End to end, a question is right only when all "
            "four steps score 1. A step's conditional accuracy is its mean "
            "over the records where every earlier step scored 1. Retrieve "
            "therefore covers all 600 records and answer covers far fewer, and "
            "only one step changed between the two releases."
        ),
        starter=(
            'import json\n'
            '\n'
            'data = json.load(open("fixtures/tracing/step_traces.json"))\n'
            'steps = data["steps"]\n'
            'releases = data["releases"]\n'
            '\n'
            'print("steps, in pipeline order:", steps)\n'
            'for release, records in releases.items():\n'
            '    print(release, "requests:", len(records))\n'
            '\n'
            'for release, records in releases.items():\n'
            '    end_to_end = sum(\n'
            '        1 for record in records\n'
            '        if all(record["steps"][step] == 1 for step in steps)\n'
            '    ) / len(records)\n'
            '    print(release, "end to end:", round(end_to_end, 4))\n'
            '    for step in steps:\n'
            '        rate = (sum(record["steps"][step] for record in records)\n'
            '                / len(records))\n'
            '        print("  ", step, "over every request:", round(rate, 4))\n'
            '\n'
            '# TODO: each rate above counts every request, including the ones\n'
            '# where an earlier step had already handed this step the wrong\n'
            '# clause, so an upstream loss lands on a downstream line. Decide\n'
            '# which requests a given step may fairly be judged on, grade all\n'
            '# four steps that way in both releases, and report the largest\n'
            '# fall from baseline to candidate on any single step.\n'
        ),
        metric="largest_step_regression",
        expected=0.2107,
        tolerance=0.0005,
        because=(
            "The rank step is the whole regression: its conditional accuracy "
            "goes from 0.8773 to 0.6667, a fall of 0.2107. Retrieve and read "
            "both come out slightly higher in the candidate release, and "
            "answer gives up 0.0096. End to end the score fell only 0.1417, "
            "from 0.6233 to 0.4817, a third less than the broken step's own "
            "fall. Grade the steps over every record instead of over a clean "
            "prefix and the picture inverts. The read step appears to fall "
            "0.1217 and the answer step 0.0667, which reads as a generation "
            "problem and sends a team at the model. The model never changed "
            "between these two releases, and the reranker did."
        ),
    ),
    sources=(
        "arxiv.org/abs/2505.00212, Which Agent Causes Task Failures and When? "
        "On Automated Failure Attribution of LLM Multi-Agent Systems, Zhang et "
        "al., version 3 dated 2025-06-02 (fetched 2026-11-01), for the "
        "Who&When dataset of failure logs from 127 systems giving 184 "
        "attribution tasks, the best method reaching 53.5 percent on the agent "
        "and 14.2 percent on the step, and Table 1 for 54.33 and 12.50 on the "
        "one-pass read, 35.20 and 25.51 on the step-by-step walk, and 29.10 "
        "and 19.06 for the random baseline",
        "arxiv.org/abs/2509.14382, Detecting Pipeline Failures through "
        "Fine-Grained Analysis of Web Agents, Roeder et al., 2025-09-17 "
        "(fetched 2026-11-01), for the three-stage split of an agent pipeline, "
        "the 490 recorded actions it was scored over, and Table 2 for 74.44, "
        "70.17, 62.87, 54.29 and 48.78 across the stages of its strongest "
        "configuration",
        "fixtures/tracing/step_traces.json, generated with a fixed seed, for "
        "every figure in this unit about Ledger itself",
    ),
)

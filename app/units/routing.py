"""Unit 14: Ledger's router evaluated on synthetic questions, and the coverage illusion.

Two failures that compound into one. A synthetic eval set drifts from the
questions underwriters actually ask in ways that are invisible from inside the
eval, and the router deciding whether Ledger chases amendments gets scored
against chance instead of against what a perfect decision would have bought.
Numbers and citations verified against the primary source; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.
    """
    outcome_of = {"cheap": "outcome_cheap", "escalate": "outcome_escalate"}
    oracle = sum(
        query[outcome_of[query["oracle_decision"]]] - query["outcome_cheap"]
        for query in data["queries"]
    )
    router = sum(
        query[outcome_of[query["router_decision"]]] - query["outcome_cheap"]
        for query in data["queries"]
    )
    return router / oracle


UNIT = Unit(
    slug="routing",
    number=14,
    part="agents",
    title="A router for Ledger evaluated on synthetic questions, and the coverage illusion",
    failure=(
        "The team tunes and scores the router in front of Ledger's expensive "
        "path, the amendment chase, on a synthetic eval set. Its accuracy "
        "number then ships, but nobody ever checks it against the questions "
        "underwriters actually ask, or against what a perfect router could "
        "have captured."
    ),
    detection=(
        "Run the same metric on synthetic questions and on real logged "
        "underwriter questions, then compare them. Score the router against "
        "an oracle ceiling, rather than against chance."
    ),
    brief=(
        "Somebody has to write the eval set for Ledger before it has ever "
        "answered a real underwriter. So they generate plausible-looking "
        "covenant questions by hand or with an LLM (Large Language Model), "
        "and call it representative. The questions are "
        "not wrong exactly, they read like things an underwriter would ask.",
        "The problem is that nobody who writes synthetic questions writes "
        "them in the actual proportions underwriters hit Ledger with. "
        "Nobody sits down to invent a boring question about a clause "
        "nobody ever amended, the way an underwriter asks one by accident. "
        "A synthetic set skews toward the "
        "examples worth writing, which are disproportionately the hard, "
        "multi-amendment ones. A router trained or threshold-tuned against "
        "that set learns the wrong base rate before it ever sees a real "
        "question.",
        "This drift is invisible from inside the eval because the eval "
        "has no way to notice its own distribution is wrong. Every metric "
        "you can compute on a synthetic set, accuracy, precision, "
        "whatever, comes back looking healthy, because the set is "
        "internally consistent with itself. The only way to see the gap "
        "is to step outside the eval and run the identical metric on "
        "logged underwriter questions. Nobody runs that comparison by "
        "default. Doing it requires admitting the number you already "
        "shipped might have been measuring the wrong population the "
        "whole time.",
        "A production retrieval system of the same shape as Ledger "
        "measured exactly this gap. On the "
        "synthetic query set its designers built, over 90 percent of "
        "queries appeared to need an expensive LLM-driven query "
        "augmentation step before retrieval would work. On real logged "
        "user queries from the same deployment, only 27.8 percent "
        "actually needed it. The synthetic set was not a small "
        "miscalibration. It was off by more than a factor of three on "
        "the one number that decides how often the expensive path should "
        "fire.",
        "The second half of the mistake is scoring the router in "
        "isolation once you do have a real number to tune against. The "
        "raw accuracy of a router, 60 percent, 80 percent, whatever it "
        "is, tells you almost nothing on its own. It says nothing about "
        "how much the decision it is making changes the answer an "
        "underwriter reads.",
        "The fix is an oracle ceiling. Compute what a router with "
        "perfect foresight on every single question would have achieved, "
        "and call that the maximum available benefit. Then measure what "
        "fraction of that benefit the real router actually captured.",
        "In the same production system, the researchers tried four "
        "separate machine learning routing approaches against this exact "
        "setup. The best of them reached at most 13.4 percent "
        "augmentation-free routing. A simple cost-ascending cascade "
        "reached 72.2 percent instead. That cascade defers to the "
        "expensive step only when a cheap step actually comes back "
        "empty. For Ledger that shape means looking up the clause first, "
        "and chasing amendments only when the lookup comes back thin.",
        "Now be careful with those two numbers, because the obvious move "
        "here is the mistake. It is tempting to notice that 72.2 is one "
        "minus the 27.8 percent augmentation-need rate and conclude the "
        "cascade hit the ceiling. That is not a ceiling. It is the "
        "observed rate of the cascade itself, restated as subtraction, "
        "and comparing a number to itself always flatters it.",
        "The paper computes a real ceiling on answer quality instead: "
        "the score a router with perfect per-query foresight would "
        "reach. Against that real ceiling, the cascade closes about 30 "
        "percent of the available gap. Every pre-retrieval method tested "
        "closes at most 2.2 percent of it. So the cascade is better by "
        "roughly thirteen times, not by the five times the tautology "
        "suggests, and it is nowhere near the ceiling. The honest "
        "headline is that both approaches leave most of the available "
        "quality on the table.",
        "The reason pre-retrieval routing failed here is structural. It "
        "is not a modeling problem you fix with more data. Whether a "
        "covenant question needs the amendment chase is a fact the "
        "search itself reveals. It reveals that fact only after the "
        "clause lookup has come back and somebody has read what it "
        "returned. "
        "Ledger's router must decide before that lookup happens, so it "
        "has to predict something it cannot yet observe.",
        "The practical habit this teaches has two parts. First, never "
        "trust the number from the router until you have run it against "
        "logged underwriter questions, instead of the set used to tune "
        "it. Second, "
        "never report that number without the oracle ceiling next to it. "
        "An 80 percent accurate router on a decision that barely changes "
        "the answer "
        "is worth less than a 60 percent accurate router. The second "
        "router decides something that changes the answer a lot. Raw "
        "accuracy cannot tell those two cases apart.",
    ),
    builds_on=(
        "Parts 2 and 3. A router decides whether to retrieve at all, so you "
        "can only score it against a retrieval path you can already "
        "measure without it."
    ),
    probes=(
        Probe(
            id="synthetic-vs-real",
            asks=(
                "Ledger's synthetic eval set says over 90 percent of questions "
                "need an "
                "expensive augmentation step before retrieval. The production "
                "system in the briefing ran that same measurement on its own "
                "logged queries. What did they show?"
            ),
            choices=(
                Choice("a", "About the same, synthetic sets are usually representative"),
                Choice("b", "Somewhat lower, around 70 percent"),
                Choice("c", "27.8 percent, off by more than a factor of three"),
                Choice("d", "Zero, the expensive step was never needed at all"),
            ),
            answer="c",
            because=(
                "The synthetic set implied queries needed augmentation over 90 "
                "percent of the time, while the real rate under the deferral "
                "policy of that deployment was 27.8 percent. The gap did not show "
                "up as a modeling error. It showed up only when someone ran the "
                "identical metric on both populations and compared them. That is "
                "the whole point: an eval built for Ledger cannot tell you it is "
                "measuring the wrong distribution."
            ),
        ),
        Probe(
            id="what-router-accuracy-establishes",
            asks=(
                "You measure Ledger's router at 60 percent accuracy on whether a "
                "question needs the amendment chase. "
                "What has that number, by itself, established?"
            ),
            choices=(
                Choice("a", "The router is unreliable, since 60 percent is close to a coin flip"),
                Choice("b", "The router is adding real value, since it beats random chance"),
                Choice("c", "Almost nothing, because accuracy alone says nothing about how much the scored decision actually matters"),
                Choice("d", "The router is better than a cascade, since cascades do not have an accuracy figure"),
            ),
            answer="c",
            because=(
                "A router can be 80 percent accurate on a decision that barely "
                "changes the answer either way. Or it can be 60 percent accurate "
                "on a decision that swings whether Ledger ever reads the "
                "amendment that governs. Raw accuracy "
                "cannot distinguish those two situations. The oracle ceiling "
                "captures the question accuracy alone cannot answer. It asks what "
                "a perfect router would have bought you, and what fraction of "
                "that your router actually captured. Without that denominator, "
                "the accuracy figure is not wrong, it is just not informative."
            ),
        ),
        Probe(
            id="router-vs-cascade",
            asks=(
                "In the production system described in the briefing, what share "
                "of augmentation-free routing did the best of four ML (Machine "
                "Learning) routers reach at most? Compare that to a simple "
                "cost-ascending cascade, the shape Ledger takes when it chases "
                "amendments only after a thin clause lookup."
            ),
            choices=(
                Choice("a", "13.4 percent for the best router, versus 72.2 percent for the cascade"),
                Choice("b", "72.2 percent for the best router, versus 13.4 percent for the cascade"),
                Choice("c", "They tied at roughly 45 percent each"),
                Choice("d", "The router beat the cascade by a wide margin"),
            ),
            answer="a",
            because=(
                "The best ML router reached at most 13.4 percent augmentation-free "
                "routing. The cost-ascending cascade, which defers the expensive "
                "step until a cheap step actually comes back empty rather than "
                "predicting need in advance, reached 72.2 percent. Resist reading "
                "72.2 as the ceiling just because it is one minus 27.8: that is "
                "just the rate of the cascade itself, restated, not an "
                "independent benchmark. Measured against the actual quality "
                "ceiling in the paper, the cascade closes about 30 percent of the "
                "gap, and the best pre-retrieval router closes about 2.2 percent. "
                "Both leave most of it unclaimed. The router loses because the "
                "fact it must predict is only observable after retrieval has "
                "already happened."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of 240 underwriter questions. For each "
            "question you have "
            "the decision of Ledger's router and the decision of the oracle, the "
            "one "
            "that actually maximizes outcome. You also have the measured "
            "answer quality under each path, the cheap clause lookup or the "
            "amendment chase. Compute the total "
            "benefit the oracle achieved and the total benefit the router "
            "achieved, each relative to always taking the cheap path. Then post "
            "the benefit of the router as a fraction of the benefit of the "
            "oracle. That fraction is the share of the achievable headroom the "
            "router actually captured."
        ),
        fixture_path="fixtures/routing/router_vs_oracle.json",
        fixture_note=(
            "One list, \"queries\", of 240 entries. Each entry has an id, "
            "router_decision, and oracle_decision, each \"cheap\" or "
            "\"escalate\". It also has outcome_cheap and outcome_escalate, the "
            "measured answer quality the question would get under each path. The "
            "oracle "
            "always picks whichever path actually scores higher for that "
            "question. "
            "Ledger's router makes its decision without that foresight, the way "
            "a real router has to."
        ),
        starter=(
            'import json\n'
            '\n'
            'data = json.load(open("fixtures/routing/router_vs_oracle.json"))\n'
            'queries = data["queries"]\n'
            '\n'
            'print("questions:", len(queries))\n'
            'print("router chased amendments on:",\n'
            '      sum(1 for q in queries if q["router_decision"] == "escalate"))\n'
            'print("oracle chased amendments on:",\n'
            '      sum(1 for q in queries if q["oracle_decision"] == "escalate"))\n'
            'print("router agreed with the oracle on:",\n'
            '      sum(1 for q in queries if q["router_decision"] == q["oracle_decision"]))\n'
            'for q in queries[:3]:\n'
            '    print(q["id"], "router:", q["router_decision"],\n'
            '          "oracle:", q["oracle_decision"],\n'
            '          "quality cheap:", q["outcome_cheap"],\n'
            '          "quality escalated:", q["outcome_escalate"])\n'
            '\n'
            '# TODO: the agreement count printed above is the obvious scoreboard,\n'
            '# and it is the wrong one, because the two paths are not equally far\n'
            '# apart on every question. Decide what each decision was worth against\n'
            '# always taking the cheap path, then print what the router earned as a\n'
            '# share of what the oracle earned. This arithmetic is not in\n'
            '# app.metrics: work it out the way a harness would.\n'
        ),
        metric="oracle_benefit_captured",
        expected=0.3663,
        tolerance=0.0005,
        because=(
            "The total benefit of the oracle over the 240 questions, summed as "
            "outcome under its decision minus outcome_cheap, is about 14.07. "
            "The total benefit of the router under the same accounting is "
            "about 5.15. The router captured roughly 36.6 percent of the "
            "achievable benefit of the oracle. That overshoot, chasing "
            "amendments on "
            "45 percent of questions when only 24 percent needed it, left the "
            "router missing questions that genuinely needed the chase. It is "
            "the same pattern the ML routers in the production system showed "
            "against their real traffic. A router tuned without seeing the "
            "questions underwriters actually ask ends up both wasteful and "
            "incomplete at the "
            "same time."
        ),
    ),
    sources=(
        "arXiv:2605.27220 (2026-05-26), The Coverage Illusion: From Pre-retrieval "
        "Routing Failure to Post-retrieval Cascades in a Production RAG System, "
        "a study of retrieval-augmented generation (RAG) routing, "
        "synthetic implies augmentation needed for over 90 percent of queries versus "
        "27.8 percent on real logs, best ML router reaches at most 13.4 percent "
        "augmentation-free routing versus 72.2 percent for a cost-ascending cascade",
    ),
)

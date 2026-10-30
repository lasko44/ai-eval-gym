"""Unit 06: routers evaluated on synthetic queries, and the coverage illusion.

Two failures that compound into one. A synthetic eval set drifts from real
traffic in ways that are invisible from inside the eval, and a router placed
in front of an expensive path gets scored against chance instead of against
what a perfect decision would have bought. Numbers and citations verified
against the primary source; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


UNIT = Unit(
    slug="routing",
    number=6,
    title="Routers evaluated on synthetic queries, and the coverage illusion",
    failure=(
        "Teams tune and score a router in front of an expensive path on a "
        "synthetic eval set. Its accuracy number then ships, but nobody "
        "ever checks it against real traffic, or against what a perfect "
        "router could have captured."
    ),
    detection=(
        "Run the same metric on synthetic queries and on real logged "
        "queries, then compare them. Score the router against an oracle "
        "ceiling, rather than against chance."
    ),
    minutes=25,
    brief=(
        "Somebody has to write the eval set before a router has ever seen "
        "production traffic. So they generate plausible-looking queries by "
        "hand or with an LLM, and call it representative. The queries are "
        "not wrong exactly, they read like things a user would type.",
        "The problem is that nobody who writes synthetic queries writes "
        "them in the actual proportions real users hit a system with. "
        "Nobody sits down to invent a boring, easy query the way a real "
        "user types one by accident. A synthetic set skews toward the "
        "examples worth writing, which are disproportionately the hard, "
        "interesting ones. A router trained or threshold-tuned against "
        "that set learns the wrong base rate before it ever sees a real "
        "request.",
        "This drift is invisible from inside the eval because the eval "
        "has no way to notice its own distribution is wrong. Every metric "
        "you can compute on a synthetic set, accuracy, precision, "
        "whatever, comes back looking healthy, because the set is "
        "internally consistent with itself. The only way to see the gap "
        "is to step outside the eval and run the identical metric on "
        "logged production queries. Nobody runs that comparison by "
        "default. Doing it requires admitting the number you already "
        "shipped might have been measuring the wrong population the "
        "whole time.",
        "A production retrieval system measured exactly this gap. On the "
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
        "how much the decision it is making actually matters.",
        "The fix is an oracle ceiling. Compute what a router with "
        "perfect foresight on every single query would have achieved, "
        "and call that the maximum available benefit. Then measure what "
        "fraction of that benefit your real router actually captured.",
        "In the same production system, the researchers tried four "
        "separate machine learning routing approaches against this exact "
        "setup. The best of them reached at most 13.4 percent "
        "augmentation-free routing. A simple cost-ascending cascade "
        "reached 72.2 percent instead. That cascade defers to the "
        "expensive step only when a cheap step actually comes back "
        "empty.",
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
        "query needs augmentation is a fact that search alone reveals, "
        "only after you have searched the index and seen what came back. "
        "A router must decide before that search happens, so it has to "
        "predict something it cannot yet observe.",
        "The practical habit this teaches has two parts. First, never "
        "trust the number from a router until you have run it against "
        "logged traffic, instead of the set used to tune it. Second, "
        "never report that number without the oracle ceiling next to it. "
        "An 80 percent accurate router on a decision that barely matters "
        "is worth less than a 60 percent accurate router on a decision "
        "that matters a lot. Raw accuracy cannot tell those two cases "
        "apart.",
    ),
    probes=(
        Probe(
            id="synthetic-vs-real",
            asks=(
                "A synthetic eval set says over 90 percent of queries need an "
                "expensive augmentation step before retrieval. Someone then "
                "measures real logged queries from the same deployment the same "
                "way. What did they show?"
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
                "the whole point: the eval itself cannot tell you it is measuring "
                "the wrong distribution."
            ),
        ),
        Probe(
            id="what-router-accuracy-establishes",
            asks=(
                "You measure a router at 60 percent accuracy on its routing decision. "
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
                "changes the outcome either way. Or it can be 60 percent accurate "
                "on a decision that swings the result enormously. Raw accuracy "
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
                "of augmentation-free routing did the best of four ML routing "
                "approaches reach at most? Compare that to a simple "
                "cost-ascending cascade."
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
            "This unit ships a fixture of 240 queries. For each query you have "
            "the decision of the router and the decision of the oracle, the one "
            "that actually maximizes outcome. You also have the measured "
            "outcome under each path, cheap or escalate. Compute the total "
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
            "measured quality the query would get under each path. The oracle "
            "always picks whichever path actually scores higher for that query. "
            "The router makes its decision without that foresight, the way a "
            "real router has to."
        ),
        starter=(
            'import json\n'
            '\n'
            'data = json.load(open("fixtures/routing/router_vs_oracle.json"))\n'
            'queries = data["queries"]\n'
            '\n'
            '# For each query, work out the outcome under the oracle\'s decision and\n'
            '# under the router\'s decision, each relative to outcome_cheap as the\n'
            '# baseline of doing nothing special. Sum each across all queries to get\n'
            '# the oracle\'s total benefit and the router\'s total benefit, then report\n'
            '# router_total / oracle_total. This arithmetic is not in app.metrics:\n'
            '# work it out yourself the way a harness would.\n'
        ),
        metric="router captured fraction of oracle benefit",
        expected=0.3663,
        tolerance=0.0005,
        because=(
            "The total benefit of the oracle over the 240 queries, summed as "
            "outcome under its decision minus outcome_cheap, is about 14.07. "
            "The total benefit of the router under the same accounting is "
            "about 5.15. The router captured roughly 36.6 percent of the "
            "achievable benefit of the oracle. That overshoot, escalating on "
            "45 percent of queries when only 24 percent needed it, left the "
            "router missing queries that genuinely needed escalation. It is "
            "the same pattern the ML routers in the production system showed "
            "against their real traffic. A router tuned without seeing the "
            "real distribution ends up both wasteful and incomplete at the "
            "same time."
        ),
    ),
    sources=(
        "arXiv:2605.27220 (2026-05-26), The Coverage Illusion: From Pre-retrieval "
        "Routing Failure to Post-retrieval Cascades in a Production RAG System, "
        "synthetic implies augmentation needed for over 90 percent of queries versus "
        "27.8 percent on real logs, best ML router reaches at most 13.4 percent "
        "augmentation-free routing versus 72.2 percent for a cost-ascending cascade",
    ),
)

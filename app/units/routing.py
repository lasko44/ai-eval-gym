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
        "A router in front of an expensive path is tuned and scored on a synthetic "
        "eval set, and its accuracy number ships without ever being checked against "
        "real traffic or against what a perfect router could have captured."
    ),
    detection=(
        "Run the same metric on synthetic queries and on real logged queries and "
        "compare, then score the router against an oracle ceiling rather than "
        "against chance."
    ),
    minutes=25,
    brief=(
        "Somebody has to write the eval set before a router has ever seen production "
        "traffic, so they generate plausible-looking queries by hand or with an LLM "
        "and call it representative. The queries are not wrong exactly, they read "
        "like things a user would type. The problem is that nobody who writes "
        "synthetic queries writes them in the actual proportions real users hit a "
        "system with, because nobody sits down to invent a boring, easy query the "
        "way a real user types one by accident. A synthetic set skews toward the "
        "examples worth writing, which are disproportionately the hard, interesting "
        "ones, and a router trained or threshold-tuned against that set learns the "
        "wrong base rate before it ever sees a real request.",
        "This drift is invisible from inside the eval because the eval has no way to "
        "notice its own distribution is wrong. Every metric you can compute on a "
        "synthetic set, accuracy, precision, whatever, comes back looking healthy, "
        "because the set is internally consistent with itself. The only way to see "
        "the gap is to step outside the eval and run the identical metric on logged "
        "production queries, which is a comparison nobody runs by default because it "
        "requires admitting the number you already shipped might have been measuring "
        "the wrong population the whole time.",
        "A production retrieval system measured exactly this gap. On the synthetic "
        "query set its designers built, over 90 percent of queries appeared to need "
        "an expensive LLM-driven query augmentation step before retrieval would work. "
        "On real logged user queries from the same deployment, only 27.8 percent "
        "actually needed it. The synthetic set was not a small miscalibration, it was "
        "off by more than a factor of three on the one number that decides how often "
        "the expensive path should fire.",
        "The second half of the mistake is scoring the router in isolation once you "
        "do have a real number to tune against. A router's raw accuracy, 60 percent, "
        "80 percent, whatever it is, tells you almost nothing on its own, because it "
        "says nothing about how much the decision it is making actually matters. The "
        "fix is an oracle ceiling: compute what a router with perfect foresight on "
        "every single query would have achieved, call that the maximum available "
        "benefit, and then measure what fraction of that benefit your real router "
        "actually captured. In the same production system, four separate machine "
        "learning routing approaches were tried against this exact setup, and the "
        "best of them reached at most 13.4 percent augmentation-free routing, while a "
        "simple cost-ascending cascade that defers to the expensive step only when a "
        "cheap step actually comes back empty reached 72.2 percent, which is the same "
        "number as one minus the real 27.8 percent augmentation-need rate. That "
        "cascade was, in effect, hitting the oracle ceiling. The best router was "
        "capturing roughly a fifth of it.",
        "The reason pre-retrieval routing failed here is structural, not a modeling "
        "problem you fix with more data: whether a query needs augmentation is a fact "
        "that is only revealed after you have searched the index and seen what came "
        "back, so a router asked to decide before that search is being asked to "
        "predict something it cannot yet observe. The practical habit this teaches is "
        "to never trust a router's number until you have run it against logged "
        "traffic instead of the set it was tuned on, and never report that number "
        "without the oracle ceiling next to it, because an 80 percent accurate router "
        "on a decision that barely matters is worth less than a 60 percent accurate "
        "router on a decision that matters a lot, and raw accuracy cannot tell those "
        "two cases apart.",
    ),
    probes=(
        Probe(
            id="synthetic-vs-real",
            asks=(
                "A synthetic eval set says over 90 percent of queries need an "
                "expensive augmentation step before retrieval. Real logged queries "
                "from the same deployment are then measured the same way. What did "
                "they show?"
            ),
            choices=(
                Choice("a", "About the same, synthetic sets are usually representative"),
                Choice("b", "Somewhat lower, around 70 percent"),
                Choice("c", "27.8 percent, off by more than a factor of three"),
                Choice("d", "Zero, the expensive step was never needed at all"),
            ),
            answer="c",
            because=(
                "The synthetic set implied augmentation was needed for over 90 "
                "percent of queries, while the real log rate under the same "
                "deployment's deferral policy was 27.8 percent. The gap did not show "
                "up as a modeling error, it showed up only when the identical metric "
                "was run on both populations and compared, which is the whole point: "
                "the eval itself cannot tell you it is measuring the wrong "
                "distribution."
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
                Choice("c", "Almost nothing, because accuracy alone says nothing about how much the decision being scored actually matters"),
                Choice("d", "The router is better than a cascade, since cascades do not have an accuracy figure"),
            ),
            answer="c",
            because=(
                "A router can be 80 percent accurate on a decision that barely "
                "changes the outcome either way, or 60 percent accurate on a decision "
                "that swings the result enormously, and raw accuracy cannot "
                "distinguish those two situations. The question accuracy alone cannot "
                "answer is captured by the oracle ceiling: what a perfect router would "
                "have bought you, and what fraction of that your router actually "
                "captured. Without that denominator, the accuracy figure is not "
                "wrong, it is just not informative."
            ),
        ),
        Probe(
            id="router-vs-cascade",
            asks=(
                "In the production system described in the briefing, the best of "
                "four ML routing approaches reached at most what share of "
                "augmentation-free routing, compared to a simple cost-ascending "
                "cascade?"
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
                "routing. The cost-ascending cascade, which defers the expensive step "
                "until a cheap step actually comes back empty rather than predicting "
                "need in advance, reached 72.2 percent, the same figure as one minus "
                "the real 27.8 percent augmentation-need rate, meaning it was "
                "effectively hitting the oracle ceiling. The router was not close, "
                "because the fact a router needs to predict is only observable after "
                "retrieval has already happened."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "A fixture of 240 queries is shipped with this unit. For each query you "
            "have the router's decision, the oracle's decision (the one that "
            "actually maximizes outcome), and the measured outcome under each path, "
            "cheap or escalate. Compute, relative to always taking the cheap path, "
            "the total benefit the oracle achieved and the total benefit the router "
            "achieved, then post the router's benefit as a fraction of the oracle's "
            "benefit, the fraction of the achievable headroom the router actually "
            "captured."
        ),
        fixture_path="fixtures/routing/router_vs_oracle.json",
        fixture_note=(
            "One list, \"queries\", of 240 entries. Each entry has an id, "
            "router_decision and oracle_decision (each \"cheap\" or \"escalate\"), "
            "and outcome_cheap and outcome_escalate, the measured quality the query "
            "would get under each path. The oracle always picks whichever path "
            "actually scores higher for that query; the router's decision was made "
            "without that foresight, the way a real router has to."
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
            "The oracle's total benefit over the 240 queries, summed as outcome "
            "under its decision minus outcome_cheap, is about 14.07. The router's "
            "total benefit under the same accounting is about 5.15. The router "
            "captured roughly 36.6 percent of the oracle's achievable benefit, "
            "despite choosing to escalate on 45 percent of queries when only about "
            "24 percent of them actually needed it in this fixture. That overshoot, "
            "escalating more often than necessary while still missing a chunk of the "
            "queries that genuinely needed it, is the same pattern the production "
            "system's ML routers showed against their real traffic: a router tuned "
            "without seeing the real distribution ends up both wasteful and "
            "incomplete at the same time."
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

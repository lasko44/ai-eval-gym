"""Unit 16: the mean latency no underwriter experiences.

Heavy-tailed service latency and the fan-out amplification Ledger creates every
time it chases several clauses at once. Numbers and citations
verified against primary sources; see UNIT.sources.
"""

import math
import statistics

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.
    """
    latencies = sorted(data["request_latencies_ms"])
    n = len(latencies)
    rank = max(1, min(n, math.ceil(0.99 * n)))
    p99 = latencies[rank - 1]
    return p99 / statistics.fmean(latencies)


UNIT = Unit(
    slug="latency-tails",
    number=16,
    part="serving",
    title="The mean latency no underwriter experiences",
    failure=(
        "The team reports mean latency and calls Ledger fast, while a "
        "meaningful share of real underwriter questions wait far longer than "
        "that number "
        "suggests."
    ),
    detection=(
        "Report p50, p95, and p99 together with the load behind them. Then "
        "reason about how a parallel clause lookup raises the chance of "
        "hitting the tail."
    ),
    brief=(
        "The team reports a mean latency of 200 milliseconds and calls "
        "Ledger fast. No underwriter experiences that mean. A served model "
        "carries a latency distribution heavy on the right, so most questions "
        "finish quickly while a meaningful share wait far longer. The mean "
        "blends both groups into one comfortable number. Jeffrey Dean and "
        "Luiz Barroso open their 2013 study of this problem by noting that a "
        "response within about 100 milliseconds feels fluid to a user. A "
        "mean of 200 milliseconds already hides whether most underwriters "
        "ever clear that bar.",
        "The mechanism is simple, and the study proves it with real "
        "numbers. Picture a server that typically answers in 10 "
        "milliseconds but carries a one-second latency at its 99th "
        "percentile. A single clause lookup against that server leaves one "
        "request in 100 "
        "slow. Fan the same question out to 100 such servers in parallel and "
        "wait for every reply, and the math changes completely. The paper "
        "shows that 63 percent of those 100-way requests now take more "
        "than one second. Even a rarer fault, one slow call in 10,000, "
        "turns almost one request in five slow once 2,000 servers sit "
        "behind the fan-out.",
        "The same paper measures this effect inside one real Google "
        "service. A root server sends a query out to a very large number "
        "of leaf servers and waits on every answer. One random leaf alone "
        "finishes within 10 milliseconds at its 99th percentile. Waiting "
        "for 95 percent of the leaves to answer pushes that number to 70 "
        "milliseconds. Waiting for all of them pushes it to 140 "
        "milliseconds, so the slowest 5 percent of leaves account for half "
        "of the full fan-out tail. Ledger waits on every clause it asked "
        "for, which is the same shape.",
        "A model-serving system needs two separate numbers, not one "
        "blended average, and vLLM names them directly. One is time to "
        "first token, the wait before the first token streams back. The "
        "other is time per output token, the pace once generation starts. "
        "The formula divides the time after that first token by the "
        "remaining tokens the call produces. An underwriter watching an "
        "answer appear feels the first number, because it sets how long the "
        "screen stays blank. An overnight re-read of a whole portfolio feels "
        "the second number, because it runs to "
        "completion with nobody watching the stream.",
        "Averaging across both kinds of work on one dashboard hides which "
        "one actually has the problem. A 2026 benchmark of 10,000 client-side "
        "probes per model and provider pairing per region shows the scale "
        "of that hiding. "
        "One tested model posts a median time to first token of 0.85 "
        "seconds and a 95th-percentile time of 1.83 seconds. Another posts "
        "1.12 seconds at the median and 2.41 seconds at the 95th "
        "percentile. Across the full benchmark the 95th percentile ran "
        "about 2.1 times the median on average. A single average over that "
        "spread tells a reader almost nothing about what a slow question "
        "feels like.",
        "The fix costs little against the risk it removes. Report p50, "
        "p95, and p99 together, and name the load that produced them, "
        "because a latency number with no load proves nothing. Then reason "
        "about fan-out directly. When one answer waits on N parallel clause "
        "lookups, "
        "the chance that one lookup lands in the tail rises with N. That "
        "holds even when each lookup alone is usually fast. For Ledger, "
        "keep time to first token and time per output token on "
        "separate axes rather than one merged average.",
        "A reader who sees only the mean has no way to tell a healthy "
        "Ledger from one running on luck. The percentiles and the load "
        "together turn a vague claim of fast into a number someone else "
        "can check.",
    ),
    builds_on=(
        "Unit 15. Cost and latency fall out of the same serving decisions. "
        "Both get reported as means by people who would never accept a "
        "mean from unit 02."
    ),
    probes=(
        Probe(
            id="mean-establishes",
            asks=(
                "Ledger's dashboard reports a mean request latency of 220 "
                "milliseconds. What does this number establish about what an "
                "underwriter waits?"
            ),
            choices=(
                Choice(
                    "a",
                    "That Ledger answers nearly every question within about "
                    "220 milliseconds",
                ),
                Choice(
                    "b",
                    "Very little by itself, since the mean hides a long "
                    "right tail that a meaningful share of underwriters wait "
                    "inside",
                ),
                Choice(
                    "c",
                    "That the p99 latency also sits near 220 milliseconds",
                ),
                Choice("d", "That Ledger meets a typical latency target"),
            ),
            answer="b",
            because=(
                "A mean blends the fast majority with the slow tail into "
                "one number, so it tells you nothing about either group "
                "alone. The source table makes this concrete. One random "
                "leaf server finishes at 10 milliseconds at its 99th "
                "percentile, but a full fan-out pushes that figure to 140 "
                "milliseconds. A dashboard that only plots the mean would "
                "show neither value. Treat a bare mean the same way you "
                "treat an unvalidated judge score, a number with no shape "
                "behind it."
            ),
        ),
        Probe(
            id="fan-out-63",
            asks=(
                "Each of 100 parallel clause lookups has a 1 percent chance "
                "alone of taking over one second. One Ledger answer waits on "
                "all "
                "100 of them. About what share of questions take over one "
                "second?"
            ),
            choices=(
                Choice("a", "About 1 percent, matching the per-lookup rate"),
                Choice("b", "About 10 percent"),
                Choice("c", "About 63 percent"),
                Choice(
                    "d",
                    "About 99 percent, since 100 lookups guarantee a slow one",
                ),
            ),
            answer="c",
            because=(
                "The source paper runs this exact case. One minus 0.99 "
                "raised to the 100th power equals about 0.634, so 63 "
                "percent of the fanned-out questions clear one second. A "
                "rare 1 percent fault at the component level becomes the "
                "common case at the answer level once enough parallel "
                "lookups carry the same small risk. The paper also reports a "
                "sparser fault, one slow call in 10,000, turning into "
                "roughly one slow request in five once 2,000 servers sit "
                "behind the call."
            ),
        ),
        Probe(
            id="ttft-vs-total",
            asks=(
                "One model server handles both Ledger's interactive "
                "underwriter questions and an "
                "overnight batch re-read of a portfolio. A dashboard reports "
                "one "
                "average latency across both. What does that average hide?"
            ),
            choices=(
                Choice(
                    "a", "Nothing, an average always represents both workloads fairly"
                ),
                Choice(
                    "b",
                    "That an underwriter feels time to first token, while a "
                    "batch job only feels total completion time",
                ),
                Choice(
                    "c", "That the batch job is the one slowing the average down"
                ),
                Choice(
                    "d",
                    "That time to first token stops mattering once a server "
                    "handles batch work",
                ),
            ),
            answer="b",
            because=(
                "vLLM tracks these as two separate numbers for exactly this "
                "reason. Time to first token covers the wait before the "
                "first token streams back, and it sets how long the "
                "underwriter's screen stays blank. Time per output token "
                "covers the pace after that, and a batch job nobody watches "
                "lives or dies on that number instead. Blend the two into "
                "one average, and you lose the ability to tell which half "
                "of the traffic actually has a problem."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships 300 end-to-end latencies for Ledger answers, in "
            "milliseconds. Each one already reflects a 4-way fan-out, the "
            "slowest of 4 parallel backend calls made for that question. "
            "Compute the ratio of p99 to the mean, using the nearest-rank "
            "percentile method the fixture names, and post that ratio as a "
            "single unitless number."
        ),
        fixture_path="fixtures/latency_tails/serving_latencies.json",
        fixture_note=(
            "Each question fans out to 4 parallel backend calls, for "
            "example the clause lookup plus three amendment lookups. "
            "The recorded value is the slowest of the 4. The load field "
            "names the load that produced the fixture. The fixture also "
            "states its percentile method directly: nearest-rank, sort "
            "ascending, and take the value at position ceil(p multiplied "
            "by n), counting ranks from 1."
        ),
        starter=(
            'import json\n'
            'import math\n'
            'import statistics\n'
            '\n'
            'data = json.load(open("fixtures/latency_tails/serving_latencies.json"))\n'
            'latencies = sorted(data["request_latencies_ms"])\n'
            'n = len(latencies)\n'
            '\n'
            '# Nearest-rank percentile: sort ascending, take the value at the\n'
            '# ceil(p * n)-th position (1-indexed). This is the convention the\n'
            '# fixture was computed with, named in fixture_note. A linear\n'
            '# interpolation percentile lands close on a sample this size,\n'
            '# but use nearest-rank to match the posted expected value.\n'
            'def percentile(sorted_values, p):\n'
            '    rank = max(1, min(n, math.ceil(p * n)))\n'
            '    return sorted_values[rank - 1]\n'
            '\n'
            'mean_latency = statistics.fmean(latencies)\n'
            'p99 = percentile(latencies, 0.99)\n'
            'print(p99 / mean_latency)\n'
        ),
        metric="p99_to_mean_ratio",
        expected=5.4953,
        tolerance=0.05,
        because=(
            "The mean of the 300 answer latencies is about 262 "
            "milliseconds, which reads as healthy on a dashboard that "
            "shows only that number. The p99 is about 1,442 milliseconds, "
            "more than five times the mean. A single slow backend lookup "
            "happens on only about 4 percent of component calls. With 4 "
            "parallel lookups per question, though, at least one slow lookup "
            "lands in about 14 percent of questions. That is the fan-out "
            "math from the briefing acting on real numbers in this "
            "fixture. It is why the mean told you almost nothing about "
            "what an underwriter waits."
        ),
    ),
    sources=(
        "Dean, J. and Barroso, L.A., The Tail at Scale, Communications of "
        "the Association for Computing Machinery (ACM), Vol 56 No 2, pages 74 "
        "to 80, February 2013, Digital Object Identifier (DOI) "
        "10.1145/2408776.2408794, fetched 2026-10-29, Table 1 and the "
        "100-server and 2,000-server fan-out figures",
        "docs.vllm.ai design/metrics page, definitions of "
        "time_to_first_token_seconds and request_time_per_output_token_seconds, "
        "fetched 2026-10-29",
        "digitalapplied.com, AI Model Latency Benchmarks 2026: TTFT and TPS "
        "Data, on time to first token (TTFT) and tokens per second (TPS), "
        "the publisher's own client-side probes rather than an audited "
        "benchmark, 10,000 probes per model and provider pairing per region "
        "across four regions, measured April 2026, 1,024-token input and "
        "256-token output, fetched 2026-10-29",
    ),
)

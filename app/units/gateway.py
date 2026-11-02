"""Unit 18: the gateway in front of Ledger disappears into the metrics behind it.

Multi-provider routing, failover, caching, rate limiting and token handling all
change the answer an underwriter reads, and none of them owns a metric. Numbers
and citations verified against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.

    The fixture is a dict with a "requests" list, one row per underwriter
    question that reached the gateway.
    """
    rows = data["requests"]
    failures = [row for row in rows if not row["served_correct"]]
    caused = [row for row in failures if row["primary_replay_correct"]]
    return len(caused) / len(failures)


UNIT = Unit(
    slug="gateway",
    number=18,
    part="serving",
    title="The gateway in front of Ledger disappears into the metrics behind it",
    failure=(
        "The gateway reports a cache hit rate, a failover count and a request "
        "volume, and all three look healthy. The answer quality it cost "
        "Ledger surfaces as a model regression, over a clean model-side log."
    ),
    detection=(
        "Replay a sample of real questions fresh against the primary "
        "provider, then attribute every wrong or missing answer to the path "
        "that served it."
    ),
    brief=(
        "Ledger does not talk to a model, it talks to a gateway in front of "
        "two large language model (LLM) providers. That gateway holds the "
        "provider keys and caches answers. It picks a provider, fails over "
        "when one is sick, and refuses a request when traffic arrives too "
        "fast. Every one of those decisions can change the answer an "
        "underwriter reads, and none of them carries a metric. The dashboard "
        "above the gateway reports answer quality for Ledger, and the "
        "dashboard below it reports model latency and token counts. The "
        "gateway sits between the two and reports neither.",
        "Start with the caching that works, because it is genuinely good. "
        "Claude's prompt caching documentation prices a cache read at 0.1 "
        "times the base input token price. A cache write costs 1.25 times "
        "that price at the five minute cache lifetime, and 2 times it at the "
        "one hour lifetime. Run the arithmetic on a credit agreement that two "
        "questions share: one write plus one read costs 1.35, against 2 for "
        "two uncached calls. The rate limit page of the same vendor adds a "
        "second effect, since cache read tokens do not count toward its "
        "input token limit. Its worked example pairs a 2,000,000 input token "
        "per minute limit with an 80 percent hit rate, and processes "
        "10,000,000 input tokens per minute.",
        "A semantic cache is a different machine wearing the same word. It "
        "returns a stored answer when a new question is merely similar to an "
        "old one. For an amended credit agreement that can mean the answer "
        "to a different covenant, with citations under it that still look "
        "right. The vCache paper measures the price of that convenience, and "
        "defines its error rate as false positives over all prompts. On a "
        "benchmark of open-ended preference prompts, a static threshold of "
        "0.99 gave a 2.5 percent error rate at a 37 percent hit rate. "
        "Loosening it to 0.98 bought 53 percent hits at 4.1 percent error, "
        "and 0.97 bought 67 percent hits at 5.2 percent error.",
        "So the headline a gateway team reports, a hit rate that nearly "
        "doubled, is the same move that doubled its wrong answers. The same "
        "work found the error rate of a fixed threshold rising as more "
        "prompts arrive, because prompt diversity grows and the threshold "
        "does not. A threshold of 0.99 still gave 1.7 percent error after "
        "150,000 web search queries. Its authors conclude that no static "
        "threshold below 1.0 keeps the error rate bounded as diversity "
        "rises. The speed on offer is real, which is what makes this hard to "
        "argue against. On 45,000 classification prompts the same cache cut "
        "one run from 240 to 160 minutes, at a 40.2 percent hit rate and 1.4 "
        "percent error.",
        "Failover is the next decision nobody measures. A gateway that fails "
        "over has swapped the thing that answers, and it records the swap as "
        "a success. One 2026 study crossed three instruction-tuned "
        "open-weight models with five inference frameworks, six benchmarks "
        "and four generation modes. It held the weights and the data fixed. "
        "Under greedy decoding, with no sampling noise left to blame, the "
        "most affected model diverged significantly from the baseline "
        "framework on 14 of 16 configurations. Its per-item answers flipped "
        "on up to 48 percent of one benchmark and 40 percent of another.",
        "Providers differ in the other direction too. A measurement study of "
        "hosted open-weight endpoints found slow response rates by provider "
        "from below 0.3 percent to near 5 percent. That threshold belongs to "
        "the measurement system and is not public, so read the spread as a "
        "ranking rather than a rate. Rate limiting is the quietest of the "
        "three. A refused request returns a 429, never reaches a model, and "
        "leaves no line in any model-side log. Published limits apply per "
        "minute to requests and to tokens, and the vendor warns that a burst "
        "inside the nominal budget can still fail.",
        "The fix is attribution rather than a better gateway metric. Replay "
        "a sample of real questions fresh against the primary provider, "
        "uncached and unthrottled. Then split every wrong or missing answer "
        "by the path that served it. Report the hit rate beside the "
        "difficulty of the questions it hit, answer quality for each "
        "provider, and the share of requests the gateway refused. Unit 14 "
        "scored a routing decision an agent makes, against what a perfect "
        "decision would have bought. This unit sits one layer under that "
        "one, and asks which component owns the regression somebody is about "
        "to blame on the model.",
    ),
    builds_on=(
        "Unit 17. Latency, cost and hit rate are the three numbers a gateway "
        "reports about itself, and unit 17 is where one blended number stops "
        "counting as evidence."
    ),
    probes=(
        Probe(
            id="hit-rate-as-a-win",
            asks=(
                "A team loosens the similarity threshold on Ledger's "
                "semantic cache from 0.99 to 0.97, and reports the hit rate "
                "rising from 37 percent to 67 percent. On the benchmark "
                "those two figures come from, what else moved?"
            ),
            choices=(
                Choice("a", "Nothing else, since a higher hit rate is a pure saving"),
                Choice(
                    "b",
                    "The false hit rate roughly doubled, from 2.5 percent to "
                    "5.2 percent of all prompts",
                ),
                Choice(
                    "c",
                    "The false hit rate fell, because more hits means more "
                    "confident matches",
                ),
                Choice("d", "Only latency moved, and it improved"),
            ),
            answer="b",
            because=(
                "The source measures both numbers at each threshold on the "
                "same benchmark. At 0.99 the cache returned a wrong stored "
                "answer for 2.5 percent of all prompts, at 0.98 for 4.1 "
                "percent, and at 0.97 for 5.2 percent. The hit rate and the "
                "error rate are the same dial read from two ends. Reporting "
                "one without the other reports half a trade. For Ledger the "
                "wrong half is specific. A question about an amended "
                "covenant comes back with the answer stored for a similar "
                "one, and its citations still look right."
            ),
        ),
        Probe(
            id="failover-logged-as-success",
            asks=(
                "Ledger's gateway failed over to the fallback provider for "
                "58 of one day's 500 questions, and logged every one of them "
                "as a success. What has that log established about the "
                "answers those underwriters read?"
            ),
            choices=(
                Choice(
                    "a",
                    "That they matched the primary provider, since every "
                    "request succeeded",
                ),
                Choice(
                    "b",
                    "Nothing, because a success log records delivery rather "
                    "than the answer",
                ),
                Choice(
                    "c",
                    "That they were worse, since a fallback is always a "
                    "weaker model",
                ),
                Choice(
                    "d",
                    "That published benchmark scores from the provider "
                    "already answer it",
                ),
            ),
            answer="b",
            because=(
                "A success means a response came back, and says nothing "
                "about what it said. The cited study held the weights and "
                "the data fixed and changed only the serving framework. "
                "Under greedy decoding the most affected model diverged "
                "significantly on 14 of 16 configurations, with per-item "
                "answers flipping on up to 48 percent of one benchmark. "
                "Option c overreaches in the opposite direction, because a "
                "fallback provider is not reliably worse, it is reliably "
                "different. Either way the gateway owns a quiet model swap, "
                "and only a replay against the primary path can price it."
            ),
        ),
        Probe(
            id="clean-model-log",
            asks=(
                "Underwriters report that Ledger sometimes gives up on a "
                "question and returns nothing at all. The model-side log for "
                "the same window shows no errors and no unusual latency. "
                "Where does the missing answer live?"
            ),
            choices=(
                Choice("a", "In the model, which must be failing silently"),
                Choice(
                    "b",
                    "In the rate limiter of the gateway, since a refused "
                    "request returns a 429 and never reaches a model",
                ),
                Choice(
                    "c",
                    "In the retrieval layer, which returned no clauses to "
                    "read",
                ),
                Choice(
                    "d",
                    "Nowhere, because a clean model log proves every request "
                    "got an answer",
                ),
            ),
            answer="b",
            because=(
                "The gateway rejects a rate-limited request before any model "
                "sees it. The model-side log is clean precisely because the "
                "work never happened. Published limits apply per minute to "
                "requests, to input tokens and to output tokens. The "
                "documentation warns that a limit of 60 requests per minute "
                "can mean 1 request per second in practice. A burst well "
                "inside the monthly budget therefore fails. To the "
                "underwriter that refusal is indistinguishable from a wrong "
                "answer, and to the dashboard it is invisible."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships one business day of Ledger's gateway log, 500 "
            "underwriter questions. Each row names what served the question, "
            "whether the underwriter got the right answer, and what a fresh "
            "replay against the primary provider answered. Count every "
            "question Ledger got wrong or never answered. Then post the "
            "fraction of those failures that the gateway caused, meaning the "
            "fresh replay came back right."
        ),
        fixture_path="fixtures/gateway/gateway_requests.json",
        fixture_note=(
            "One list, \"requests\", of 500 rows. Each row has an id, "
            "amendments (how many amendments touch the clause in question), "
            "served_by, served_correct and primary_replay_correct. served_by "
            "is one of semantic_cache, primary, fallback, or refused. A "
            "refused row is a request the rate limiter of the gateway "
            "rejected, so no model saw it and served_correct is false. "
            "primary_replay_correct is the audit: the same question replayed "
            "fresh against the primary provider, uncached and unthrottled. A "
            "row the gateway forwarded to the primary provider reproduces "
            "what the underwriter saw, so its two columns agree."
        ),
        starter=(
            'import json\n'
            '\n'
            'data = json.load(open("fixtures/gateway/gateway_requests.json"))\n'
            'rows = data["requests"]\n'
            '\n'
            'by_path = {}\n'
            'for row in rows:\n'
            '    by_path[row["served_by"]] = by_path.get(row["served_by"], 0) + 1\n'
            '\n'
            'print("questions in the log:", len(rows))\n'
            'print("rows by the path that served them:", by_path)\n'
            'print("questions Ledger answered correctly:",\n'
            '      sum(1 for row in rows if row["served_correct"]))\n'
            'print("questions a fresh primary replay answered correctly:",\n'
            '      sum(1 for row in rows if row["primary_replay_correct"]))\n'
            '\n'
            '# TODO: those last two counts are the gap no model dashboard shows.\n'
            '# Decide which rows count as a question Ledger failed, remembering\n'
            '# that a refused request is a failure the underwriter felt. Then\n'
            '# decide which of those failures the gateway itself caused rather\n'
            '# than the model, using the replay as the baseline. Print the\n'
            '# second as a share of the first.\n'
            '#\n'
            '# Once that number is out, the same rows answer two more questions\n'
            '# worth asking: how the gateway-caused failures split across\n'
            '# served_by, and how the amendment counts compare between the\n'
            '# questions the cache answered and the ones it forwarded.\n'
        ),
        metric="gateway_attributable_failure_share",
        expected=0.4571,
        tolerance=0.0005,
        because=(
            "Served accuracy over the 500 questions is 0.790, and a fresh "
            "primary replay of the same questions scores 0.858. The gateway "
            "cost Ledger about 7 points of answer quality, and no model-side "
            "dashboard shows that gap. Of the 105 wrong or missing answers, "
            "48 came back right on the replay, which is 45.7 percent of "
            "every failure. Those 48 split three ways: 20 refusals, 16 wrong "
            "answers from the fallback provider, and 12 false hits from the "
            "semantic cache. The cache meanwhile reads as a win, with a 30.4 "
            "percent hit rate and accuracy of 0.908 on a hit against 0.796 "
            "on a forwarded question. Its hits carry 0.78 amendments on "
            "average against 1.92 for the ones it forwards, so it answers "
            "the easy half and takes the credit."
        ),
    ),
    sources=(
        "arXiv:2502.03771, vCache: Verified Semantic Prompt Caching, "
        "accepted at the International Conference on Learning "
        "Representations 2026, read as extracted text 2026-11-01. Error rate "
        "defined as false positives over all prompts. Table 3 static global "
        "threshold results, 0.99 giving 2.5 percent error at a 37 percent "
        "hit rate, 0.98 giving 4.1 percent at 53 percent, and 0.97 giving "
        "5.2 percent at 67 percent. Appendix F.1 for the 0.99 threshold "
        "still at 1.7 percent error after 150,000 search queries, and Table "
        "2 for 240 minutes falling to 160 minutes at a 40.2 percent hit rate "
        "and a 1.4 percent error rate over 45,000 prompts",
        "arXiv:2608.04714 (2026-08-05), What We Observe as LLM Behavior Can "
        "Be a Side-effect of Inference Backend, fetched 2026-11-01. Three "
        "instruction-tuned models crossed with five inference frameworks, "
        "six benchmarks and four generation modes. Table 1 and section 4.1 "
        "for significant divergence on 14 of 16 configurations under greedy "
        "decoding, and for per-item disagreement reaching 48 percent and 40 "
        "percent",
        "platform.claude.com/docs/en/build-with-claude/prompt-caching, "
        "fetched 2026-11-01, cache read at 0.1 times the base input token "
        "price, cache write at 1.25 times for the five minute lifetime and 2 "
        "times for the one hour lifetime, and a minimum cacheable prompt "
        "length of 512 to 4,096 tokens depending on the model",
        "platform.claude.com/docs/en/api/rate-limits, fetched 2026-11-01, "
        "per-minute limits on requests, input tokens and output tokens, a "
        "429 on exceeding one of them, cache read tokens excluded from the "
        "input token limit on most models, the worked 2,000,000 limit with "
        "an 80 percent hit rate giving 10,000,000 input tokens per minute, "
        "and the warning that a limit of 60 requests per minute can mean 1 "
        "request per second",
        "arXiv:2605.02821 (2026-05-07), When Is the Same Model Not the Same "
        "Service? A Measurement Study of Hosted Open-Weight LLM APIs, "
        "fetched 2026-11-01, section 5.6 for slow response rates by provider "
        "from below 0.3 percent to near 5 percent, measured against the "
        "undisclosed threshold of the measurement system",
    ),
)

"""Unit 15: cost per call hides what Ledger actually costs.

Batch size, context length, and the input to output token ratio each move the
bill in a way a single per-call number cannot show, and a lender pays per
answered question rather than per model call. Numbers and citations
verified against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.
    """
    price_in = data["price_per_input_token_usd"]
    price_out = data["price_per_output_token_usd"]
    per_resolved = []
    for point in data["points"]:
        cost = sum(
            row["input_tokens"] * price_in + row["output_tokens"] * price_out
            for row in point["requests"]
        )
        resolved = sum(1 for row in point["requests"] if row["resolved"])
        per_resolved.append(cost / resolved)
    return max(per_resolved) / min(per_resolved)


UNIT = Unit(
    slug="inference-economics",
    number=15,
    part="serving",
    title="Cost per call hides what Ledger actually costs",
    failure=(
        "The team reports cost per call, or tokens per call, and calls Ledger "
        "cheap. Both numbers hide batch size, context length, and the "
        "share of questions that get answered. A deployment that looks cheap "
        "per call can cost far more "
        "per underwriter question it actually answers."
    ),
    detection=(
        "Measure cost per resolved question at more than one operating point, "
        "sweeping batch size and context length, and report the curve."
    ),
    brief=(
        "A dashboard that reports cost per call invites a quick read. The number "
        "is small, so Ledger is cheap. That read skips every setting that "
        "produced the number. It skips how many questions ran together, how "
        "long the retrieved context was, and how many of those calls actually "
        "ended in an answer. "
        "Two deployments of Ledger can show the same cost per call. They can "
        "still differ by "
        "several times in what each one costs to answer one underwriter.",
        "Context length sets a memory ceiling that a per-call number cannot "
        "show. Ledger has a long context by construction: a clause plus "
        "every amendment that touched it. Every layer and every attention head "
        "keeps a key and a value "
        "for each token in the context. That cache grows with context length "
        "and with how many questions run at once. NVIDIA's inference "
        "optimization guide gives the formula directly. Total cache bytes "
        "equal batch size times sequence length times two times layer count "
        "times hidden size times the byte width of one value.",
        "Its worked example is a 7 billion parameter Llama 2 model, one "
        "request, a 4,096 token sequence, 32 layers, and a hidden size of "
        "4,096, in 16 bit precision. That comes to roughly 2 gigabytes of "
        "cache for one request alone, before a single model weight loads.",
        "The same source explains why two phases of a single call behave "
        "differently, and that difference is not a detail. Reading the clause "
        "package Ledger retrieved is a large matrix to matrix operation. It "
        "keeps the GPU "
        "(Graphics Processing Unit) "
        "busy, so that phase is compute bound. Writing the answer one token at "
        "a time is closer to a "
        "matrix to vector operation. The GPU sits idle there while it waits on "
        "memory. Databricks states the same finding directly, that this later "
        "phase is memory bound.",
        "Databricks also measured the trade both "
        "phases create under load. One A100 running MPT-7B (MosaicML "
        "Pretrained Transformer) moved from 0.9 "
        "requests per second at batch size 1 to 33 requests per second at "
        "batch size 64. "
        "That move is a 14 fold gain in throughput, bought at a 4 fold rise "
        "in latency. The underwriter waiting on an answer is the one who "
        "pays that rise.",
        "Batching is also where most of the throughput on a GPU gets won or "
        "lost. Two measured benchmarks show how much is at stake. The "
        "PagedAttention paper behind vLLM reports a 2 to 4 times throughput "
        "gain over FasterTransformer and Orca, at the same latency. That gain "
        "grows for longer sequences and larger models, which is the direction "
        "a clause package pushes. Anyscale measured the "
        "same idea end to end on one A100 serving OPT-13B (Open Pre-trained "
        "Transformer). Continuous "
        "batching and vLLM's memory handling together reached up to 23 times "
        "the throughput of naive static batching, against roughly 8 times "
        "for continuous batching alone.",
        "Change the batch size, and the dollars per GPU hour you deliver can "
        "move by an order of magnitude.",
        "The input to output token ratio sets a third knob, and published "
        "pricing shows it is not a footnote. Claude's current pricing page "
        "lists Opus, Sonnet, and Haiku each at a fixed 1 to 5 ratio between an "
        "input token and an output token. Sonnet charges 2 dollars against 10 "
        "dollars per million tokens as one example. Ledger sits on the long "
        "prompt side of that ratio: a clause package goes in, a paragraph with "
        "citations comes out. That costs differently from the reverse shape. "
        "That holds even when the total token "
        "count printed on a dashboard is identical.",
        "None of these three knobs show up in a per-call average, and a "
        "fourth number hides with them. A call can time out, or return an "
        "answer the underwriter rejects because the citation does not hold. "
        "That call still consumed prefill and some decode "
        "before it failed, and the bill still arrives. Cost per call divides by "
        "every call made. Cost per resolved question divides by every question "
        "Ledger actually answered. It rises exactly when failures rise, "
        "which a flat-looking per-call number will never show.",
        "The fix is not a smarter single number, it is more than one "
        "measurement. Hold the question mix fixed and sweep batch size and "
        "context "
        "length, computing cost per resolved question at each point. Report the "
        "curve, and name the operating point behind any number you quote. A "
        "lender asking what Ledger costs is asking which knob moves the cost "
        "of an answered question, not what one call costs in isolation.",
    ),
    builds_on=(
        "Unit 14. Retries are where the token bill actually comes from, so "
        "cost per call means nothing until you know how many calls one "
        "underwriter question takes."
    ),
    probes=(
        Probe(
            id="kv-cache-formula",
            asks=(
                "NVIDIA's inference optimization guide gives a worked key and "
                "value cache figure. The figure covers a 7 billion parameter "
                "Llama 2 model, one request, a 4,096 token sequence, 32 layers, "
                "hidden size 4,096, and 16 bit precision. What does that cache "
                "come to, and which inputs drive the formula behind it?"
            ),
            choices=(
                Choice("a", "Roughly 2 gigabytes, driven by batch size, sequence length, layer count, and hidden size together"),
                Choice("b", "A fixed 500 megabytes regardless of sequence length, since the cache size is set by the model weights"),
                Choice("c", "Roughly 2 gigabytes, driven only by the number of model parameters"),
                Choice("d", "Under 50 megabytes, since the cache holds only the current token"),
            ),
            answer="a",
            because=(
                "The formula is batch size times sequence length times two "
                "times layer count times hidden size times the byte width of "
                "one value. At batch size 1, a 4,096 token sequence, 32 layers, "
                "and hidden size 4,096 in 16 bit precision, that comes to "
                "roughly 2 gigabytes for one request. Doubling batch size or "
                "sequence length roughly doubles the cache, and the model's "
                "parameter count does not appear in the formula at all. A long "
                "clause package is therefore a memory decision, not only a "
                "price decision."
            ),
        ),
        Probe(
            id="prefill-vs-decode",
            asks=(
                "Databricks measured MPT-7B on one A100. Throughput moved "
                "from 0.9 requests per second at batch size 1 to 33 requests "
                "per second at batch size 64. That is a 14 fold gain bought "
                "at a 4 fold rise in latency. What does that pair of numbers "
                "establish about the batch size Ledger should run?"
            ),
            choices=(
                Choice("a", "That batch size 64 is strictly better, since throughput rose more than latency did"),
                Choice("b", "That batch size has no real effect, since both numbers moved together"),
                Choice("c", "That the right batch size depends on the latency an underwriter can accept, since more throughput came with a real cost"),
                Choice("d", "That the GPU was compute bound at batch size 1, which is why throughput rose so much"),
            ),
            answer="c",
            because=(
                "A 14 fold throughput gain at a 4 fold rise in latency is a "
                "trade, not a free win. Decode is memory bound, so a larger "
                "batch lets more questions share the same memory traffic and "
                "raises throughput. Each question now waits behind more work, "
                "so its own latency rises. Choosing a batch size means "
                "choosing a point on that curve for the latency an underwriter "
                "will tolerate. It does not mean finding the batch size with "
                "the biggest throughput number."
            ),
        ),
        Probe(
            id="cost-per-call-looks-cheap",
            asks=(
                "Ledger's team reports cost per call of 0.35 cents on the "
                "production "
                "endpoint and calls the system cheap. What does that single "
                "number establish on its own?"
            ),
            choices=(
                Choice("a", "That the system is cheap at any load, since cost per call is the measure that matters"),
                Choice("b", "Very little, since it says nothing about batch size, context length, or how many of those calls actually ended in an answered question"),
                Choice("c", "That the system is cheaper than a competitor whose cost per call is higher"),
                Choice("d", "That the model choice, not the serving setup, is the main cost driver"),
            ),
            answer="b",
            because=(
                "Cost per call divides total spend by every call made, resolved "
                "or not, at whatever batch size and context length happened to "
                "be running. The same figure could sit behind a Ledger that "
                "answers 96 percent of the questions put to it, or one that "
                "answers 25 "
                "percent. A failed call still consumes prefill and some "
                "decode, and it still gets billed. Cost per resolved question, "
                "measured at a named operating point, is the number that "
                "would tell the difference apart."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of request traces at four operating "
            "points, 200 requests each, all serving the same underwriter "
            "question mix. Compute "
            "cost per resolved question at each point, using the published "
            "per-token prices in the fixture. Remember that a call which did "
            "not end in an answer was still billed. Post the ratio between the "
            "most "
            "expensive operating point and the cheapest, as a plain "
            "multiplier. A multiplier of 3.0 would mean the worst point costs "
            "three times as much per answered question as the best."
        ),
        fixture_path="fixtures/inference_economics/operating_points.json",
        fixture_note=(
            "Four operating points, each naming a batch size and a configured "
            "context window, with 200 request rows. Every row is one "
            "underwriter question and carries "
            "input_tokens, output_tokens, latency_ms, and resolved. A row with "
            "resolved false is a question Ledger did not answer, and the bill "
            "still covers it. The file "
            "also carries price_per_input_token_usd and "
            "price_per_output_token_usd, the two prices to cost every call, "
            "resolved or not."
        ),
        starter=(
            'import json\n'
            '\n'
            'fixture = json.load(open("fixtures/inference_economics/operating_points.json"))\n'
            'price_in = fixture["price_per_input_token_usd"]\n'
            'price_out = fixture["price_per_output_token_usd"]\n'
            '\n'
            '# For each point, cost every request (resolved or not), then divide\n'
            '# total cost by the count of resolved requests. Compare cost per call\n'
            '# against cost per resolved request before you pick the ratio to post.\n'
            'for point in fixture["points"]:\n'
            '    rows = point["requests"]\n'
            '    print(point["label"], len(rows))\n'
        ),
        metric="cost_per_resolved_ratio",
        expected=3.8186,
        tolerance=0.001,
        because=(
            "Cost per call sits within about 2 percent across all four "
            "points, near 0.35 cents. Every point serves the same question "
            "mix, so "
            "the token counts per request barely move. Cost per resolved "
            "question runs from about 0.36 cents at the smallest batch and "
            "context window to about 1.37 cents at the widest, a ratio of "
            "3.82. The "
            "share of questions answered drops from 96 percent to 26 percent "
            "across the "
            "same four points. That drop, not the token count, moves "
            "what a lender pays per answer. A dashboard built only on cost per "
            "call would "
            "have shown almost no change at all."
        ),
    ),
    sources=(
        "developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization, "
        "NVIDIA, key and value cache formula and a worked Llama 2 7B figure, "
        "and the compute bound prefill against memory bound decode distinction",
        "databricks.com/blog/llm-inference-performance-engineering-best-practices, "
        "Databricks, MPT-7B throughput and latency across batch sizes on one A100, "
        "and the compute bound against memory bound phase distinction",
        "arXiv:2309.06180, Kwon et al., Efficient Memory Management for Large "
        "Language Model Serving with PagedAttention, the vLLM paper, 2 to 4 times "
        "throughput over FasterTransformer and Orca at matched latency",
        "anyscale.com/blog/continuous-batching-llm-inference, Anyscale, up to 23 "
        "times throughput over naive static batching for OPT-13B on one A100",
        "claude.com/pricing, fetched 2026-10-29, the 1 to 5 input to output token "
        "price ratio held across the current Claude model lineup",
    ),
)

"""Unit 10: cost per call hides what a system actually costs.

Batch size, context length, and the input to output token ratio each move the
bill in a way a single per-call number cannot show. Numbers and citations
verified against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


UNIT = Unit(
    slug="inference-economics",
    number=10,
    title="Cost per call hides what a system actually costs",
    failure=(
        "A team reports cost per call, or tokens per call, and calls the system "
        "cheap. Both numbers hide batch size, context length, and the "
        "resolution rate. A system that looks cheap per call can cost far more "
        "per unit of work it actually delivers."
    ),
    detection=(
        "Measure cost per resolved request at more than one operating point, "
        "sweeping batch size and context length, and report the curve."
    ),
    brief=(
        "A dashboard that reports cost per call invites a quick read. The number "
        "is small, so the system is cheap. That read skips every setting that "
        "produced the number. It skips how many requests ran together, how "
        "long the context was, and how many of those calls actually finished. "
        "Two systems can show the same cost per call. They can still differ by "
        "several times in what each one costs to deliver a finished answer.",
        "Context length sets a memory ceiling that a per-call number cannot "
        "show. Every layer and every attention head keeps a key and a value "
        "for each token in the context. That cache grows with context length "
        "and with how many requests run at once. NVIDIA's inference "
        "optimization guide gives the formula directly. Total cache bytes "
        "equal batch size times sequence length times two times layer count "
        "times hidden size times the byte width of one value.",
        "Its worked example is a 7 billion parameter Llama 2 model, one "
        "request, a 4,096 token sequence, 32 layers, and a hidden size of "
        "4,096, in 16 bit precision. That comes to roughly 2 gigabytes of "
        "cache for one request alone, before a single model weight loads.",
        "The same source explains why two phases of a single call behave "
        "differently, and that difference is not a detail. Processing the "
        "prompt is a large matrix to matrix operation, so it keeps the GPU "
        "busy and is compute bound. Generating each new token is closer to a "
        "matrix to vector operation, so the GPU sits idle while it waits on "
        "memory. Databricks states the same finding directly, that this later "
        "phase is memory bound. Databricks also measured the trade both "
        "phases create under load. One A100 running MPT-7B moved from 0.9 "
        "requests per second at batch size 1 to 33 requests per second at "
        "batch size 64.",
        "That move is a 14 fold gain in throughput, bought at a 4 fold rise "
        "in latency.",
        "Batching is also where most of the throughput on a GPU gets won or "
        "lost. Two measured benchmarks show how much is at stake. The "
        "PagedAttention paper behind vLLM reports a 2 to 4 times throughput "
        "gain over FasterTransformer and Orca, at the same latency. That gain "
        "grows for longer sequences and larger models. Anyscale measured the "
        "same idea end to end on one A100 serving OPT-13B. Continuous "
        "batching and vLLM's memory handling together reached up to 23 times "
        "the throughput of naive static batching, against roughly 8 times "
        "for continuous batching alone.",
        "Change the batch size, and the dollars per GPU hour you deliver can "
        "move by an order of magnitude.",
        "The input to output token ratio sets a third knob, and published "
        "pricing shows it is not a footnote. Claude's current pricing page "
        "lists Opus, Sonnet, and Haiku each at a fixed 1 to 5 ratio between an "
        "input token and an output token. Sonnet charges 2 dollars against 10 "
        "dollars per million tokens as one example. A workload with a short "
        "prompt and a long answer costs differently from a workload with a "
        "long prompt and a short answer. That holds even when the total token "
        "count printed on a dashboard is identical.",
        "None of these three knobs show up in a per-call average, and a "
        "fourth number hides with them. A call that times out, or returns an "
        "answer the caller rejects, still consumed prefill and some decode "
        "before it failed. The bill still arrives. Cost per call divides by "
        "every call made. Cost per resolved request divides by every call "
        "that actually finished the job. It rises exactly when failures rise, "
        "which a flat-looking per-call number will never show.",
        "The fix is not a smarter single number, it is more than one "
        "measurement. Hold the workload fixed and sweep batch size and context "
        "length, computing cost per resolved request at each point. Report the "
        "curve, and name the operating point behind any number you quote. A "
        "Director asking for the cost of a workload is asking which knob moves "
        "it, not what one call costs in isolation.",
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
                "parameter count does not appear in the formula at all."
            ),
        ),
        Probe(
            id="prefill-vs-decode",
            asks=(
                "Databricks measured MPT-7B on one A100. Throughput moved "
                "from 0.9 requests per second at batch size 1 to 33 requests "
                "per second at batch size 64. That is a 14 fold gain bought "
                "at a 4 fold rise in latency. What does that pair of numbers "
                "establish about the batch size you should choose?"
            ),
            choices=(
                Choice("a", "That batch size 64 is strictly better, since throughput rose more than latency did"),
                Choice("b", "That batch size has no real effect, since both numbers moved together"),
                Choice("c", "That the right batch size depends on the latency a caller can accept, since more throughput came with a real cost"),
                Choice("d", "That the GPU was compute bound at batch size 1, which is why throughput rose so much"),
            ),
            answer="c",
            because=(
                "A 14 fold throughput gain at a 4 fold rise in latency is a "
                "trade, not a free win. Decode is memory bound, so a larger "
                "batch lets more requests share the same memory traffic and "
                "raises throughput. Each request now waits behind more work, "
                "so its own latency rises. Choosing a batch size means "
                "choosing a point on that curve for the latency your callers "
                "will tolerate. It does not mean finding the batch size with "
                "the biggest throughput number."
            ),
        ),
        Probe(
            id="cost-per-call-looks-cheap",
            asks=(
                "A team reports cost per call of 0.35 cents on their production "
                "endpoint and calls the system cheap. What does that single "
                "number establish on its own?"
            ),
            choices=(
                Choice("a", "That the system is cheap at any load, since cost per call is the measure that matters"),
                Choice("b", "Very little, since it says nothing about batch size, context length, or how many of those calls actually resolved"),
                Choice("c", "That the system is cheaper than a competitor whose cost per call is higher"),
                Choice("d", "That the model choice, not the serving setup, is the main cost driver"),
            ),
            answer="b",
            because=(
                "Cost per call divides total spend by every call made, resolved "
                "or not, at whatever batch size and context length happened to "
                "be running. The same figure could sit behind a system that "
                "resolves 96 percent of calls, or one that resolves 25 "
                "percent. A failed call still consumes prefill and some "
                "decode, and it still gets billed. Cost per resolved request, "
                "measured at a named operating point, is the number that "
                "would tell the difference apart."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of request traces at four operating "
            "points, 200 requests each, all serving the same task. Compute "
            "cost per resolved request at each point, using the published "
            "per-token prices in the fixture. Remember that a call which did "
            "not resolve was still billed. Post the ratio between the most "
            "expensive operating point and the cheapest, as a plain "
            "multiplier. A multiplier of 3.0 would mean the worst point costs "
            "three times as much per resolved request as the best."
        ),
        fixture_path="fixtures/inference_economics/operating_points.json",
        fixture_note=(
            "Four operating points, each naming a batch size and a configured "
            "context window, with 200 request rows. Every row carries "
            "input_tokens, output_tokens, latency_ms, and resolved. The file "
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
            "points, near 0.35 cents. Every point serves the same task, so "
            "the token counts per request barely move. Cost per resolved "
            "request runs from about 0.36 cents at the smallest batch and "
            "context window. It runs up to about 1.37 cents at the largest "
            "batch and the widest context window, a ratio of 3.82. The "
            "resolved rate drops from 96 percent to 26 percent across the "
            "same four points, and that drop, not the token count, moves "
            "the real cost. A dashboard built only on cost per call would "
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

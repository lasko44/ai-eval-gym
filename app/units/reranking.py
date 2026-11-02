"""Unit 08: missing rerankers, and why recall at one k hides them.

A retrieval pipeline can find the right documents and still fail, because
finding them and ranking them near the top are two different jobs, done by
two different stages. Numbers and citations verified against primary
sources; see UNIT.sources.
"""

from app.metrics import recall_at_k
from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.
    """
    queries = data["queries"]
    at_5 = [
        recall_at_k(query["retrieved"], set(query["relevant"]), 5) for query in queries
    ]
    at_150 = [
        recall_at_k(query["retrieved"], set(query["relevant"]), 150)
        for query in queries
    ]
    return sum(at_150) / len(at_150) - sum(at_5) / len(at_5)


UNIT = Unit(
    slug="reranking",
    number=8,
    part="retrieval",
    title="Missing rerankers, and the recall number that hides them",
    failure=(
        "Ledger's first-stage search finds the operative clause somewhere in its "
        "candidate set. But it ranks that clause so badly that the small top-k window "
        "the answer gets written from never sees it."
    ),
    detection=(
        "Measure recall at a small k and a large k on the same set of underwriter "
        "questions. The gap between the two names whether the fault is ordering or "
        "coverage."
    ),
    brief=(
        "Most evals of Ledger retrieval stop at one number: recall at whatever k the "
        "prompt holds, usually five or ten chunks of a credit agreement. The number "
        "comes back reasonable, nothing alarms anyone, and the pipeline ships. "
        "What that single number cannot tell you is whether the clauses that answer "
        "the underwriter's question were absent from the candidate set entirely. Or "
        "the clauses were present in the set and simply buried below the cutoff where "
        "nobody looked. Those are different failures with different "
        "fixes, and a single recall@k conflates them into one reassuring digit.",
        "Ledger's retrieval stack has two jobs stacked on top of each other, and "
        "most pipelines only do the first one. An embedding search (or BM25, or "
        "both) casts a wide net cheaply over the credit agreement and its "
        "amendments. It scores every candidate chunk against the question using a "
        "single vector or a bag-of-words signal. That signal is good at getting "
        "plausible clauses into a large candidate set, but it is weak at ordering "
        "them precisely. It never looks at the question and a specific clause "
        "together.",
        "A reranker, typically a cross-encoder, takes a smaller candidate set and "
        "scores each question-clause pair jointly. That is far more expensive per "
        "pair, but far more accurate at ordering. Skip that second stage and Ledger "
        "is good at finding and bad at sorting. Recall at a "
        "small k is exactly the measurement that sorting quality controls.",
        "Anthropic measured this directly on a mixed set of codebases, fiction, and "
        "research papers. It reported the fraction of queries where the right chunk "
        "missed the top 20 results entirely (one minus recall at 20). Basic "
        "embedding search alone missed the top 20 5.7 percent of the time. Adding "
        "context to each chunk before embedding it brought that down to 3.7 "
        "percent. Adding a BM25 signal alongside the contextual embeddings brought "
        "it to 2.9 percent. Reranking on top of that full stack brought it to 1.9 "
        "percent, a 67 percent relative reduction from the baseline.",
        "Isolate just the contribution of the reranker itself. It still cut the "
        "failure rate nearly by a third on top of everything the better embeddings "
        "and BM25 had already fixed. That part is attributable to ordering rather "
        "than to finding.",
        "That effect is not limited to the pipeline of one vendor, and it does not "
        "depend on the corpus looking anything like a loan file. The BEIR "
        "(Benchmarking Information Retrieval) "
        "benchmark tests retrieval across eighteen unrelated domains with no "
        "domain-specific tuning. It found that adding a cross-encoder reranker on "
        "top of plain BM25 beat BM25 alone on sixteen of those eighteen datasets. "
        "The average improvement was roughly 11 percent in nDCG at 10.",
        "BM25 is not even a neural embedding, which is the point. The lift from "
        "reranking comes from scoring the query and the document together at the "
        "final stage. That step helps regardless of what produced the candidate "
        "set underneath it.",
        "The gap between recall at a small k and recall at a large k is what turns "
        "this from a vague suspicion into a measurement. If recall at a large k "
        "(say 150) is much higher than recall at a small k (say 5), the operative "
        "clauses are in Ledger's candidate set. A reranker could move them up, and "
        "adding one is likely to close most of that gap.",
        "If both numbers are low, the clauses are not in the candidate set at "
        "all, no matter how far down you look. A reranker cannot fix that. It can "
        "only reorder what the first stage already retrieved. It cannot retrieve an "
        "amendment that was never there. Reporting a single recall@k erases this "
        "distinction completely. Reporting both numbers, and the gap between them, "
        "is what tells you which of two very different fixes Ledger actually needs.",
    ),
    builds_on=(
        "All of part 1. Recall at ten scores a set of queries, so it "
        "inherits every limit you just measured. A two-point gain on "
        "forty queries is not a gain."
    ),
    probes=(
        Probe(
            id="contextual-retrieval-numbers",
            asks=(
                "In the contextual retrieval measurements from Anthropic, basic "
                "embedding search alone missed the top 20 chunks on about 5.7 "
                "percent of queries. What did that failure rate drop to with the "
                "full stack: contextual embeddings, contextual BM25, and reranking "
                "together?"
            ),
            choices=(
                Choice("a", "0.2 percent, reranking removes failures almost entirely"),
                Choice("b", "1.9 percent"),
                Choice("c", "3.7 percent, reranking barely moves it past contextual embeddings alone"),
                Choice("d", "5.7 percent stays the same, reranking only reorders, never reduces top-20 misses"),
            ),
            answer="b",
            because=(
                "5.7 percent dropped to 1.9 percent with the full stack, a 67 percent "
                "relative reduction. That number bundles three separate improvements "
                "together: better embeddings, BM25 added alongside them, and "
                "reranking on top. Isolated on its own, reranking still cut what was "
                "left (2.9 percent) by close to a third. That part is attributable "
                "to ordering rather than to finding. Option d is the trap: "
                "reranking does only reorder. But moving a result from rank 21 or "
                "lower into the top 20 is exactly what reduces a top-20 miss rate."
            ),
        ),
        Probe(
            id="what-reranking-can-do",
            asks=(
                "You add a cross-encoder reranker on top of Ledger's existing "
                "retrieval pipeline, and it scores the candidates that pipeline "
                "returned against the question. What can it do, mechanically?"
            ),
            choices=(
                Choice("a", "Increase recall at any k, including very large k"),
                Choice("b", "Reorder the candidates the first stage already retrieved. It cannot add clauses the first stage never found"),
                Choice("c", "Replace the need for a first-stage retriever entirely"),
                Choice("d", "Reduce the size of the embedding index needed in production"),
            ),
            answer="b",
            because=(
                "A reranker only sees the candidate set handed to it by the stage "
                "before it. So recall at a k large enough to cover that whole "
                "candidate set is a ceiling the reranker cannot push past. If the "
                "amendment that rewrote the clause is not in the first 150 "
                "candidates, no amount of rescoring surfaces it. This is also why "
                "cross-encoders are not run over an entire corpus directly. Scoring "
                "the question against every chunk of every credit agreement jointly "
                "does not scale. So a cheap first stage has to narrow the field "
                "before the expensive, accurate stage gets to rank it."
            ),
        ),
        Probe(
            id="interpreting-the-gap",
            asks=(
                "You measure recall@5 = 0.20 and recall@100 = 0.85 for Ledger on the "
                "same set of underwriter questions. What have you established?"
            ),
            choices=(
                Choice("a", "The embedding model is poor quality, so you should swap it"),
                Choice("b", "The clauses are mostly being found but ranked badly: this is a reranking problem, not an embedding problem"),
                Choice("c", "Production should raise k to 100 so underwriters see the right clauses"),
                Choice("d", "Nothing is conclusive. A 65-point gap could mean anything without more data"),
            ),
            answer="b",
            because=(
                "A large gap between a small-k and a large-k recall, with the large-k "
                "number high, means the first stage is doing its job. The clauses "
                "that answer the question are present in the candidate set. Swapping "
                "the embedding model (option a) targets the wrong stage and risks "
                "making no difference, since the embeddings already found 85 percent "
                "of what mattered. Raising k in production (option c) does not fix "
                "anything either, since the prompt Ledger answers from still only "
                "reads the first handful of chunks. It would just hand the same "
                "badly-ordered list to a bigger context window. The fix that matches "
                "this signature is a reranking stage between retrieval and the prompt."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of 180 underwriter questions put to Ledger. "
            "Each question has a list of 150 retrieved chunk ids, in the order the "
            "pipeline returned them. It also has the set of chunk ids that genuinely "
            "carry the answer. Compute recall@5 and recall@150 for every question, "
            "average each across all 180 questions, and post the gap: mean "
            "recall@150 minus mean recall@5."
        ),
        fixture_path="fixtures/reranking/retrieval_results.json",
        fixture_note=(
            "A JSON (JavaScript Object Notation) object with one key, \"queries\", "
            "holding a list of 180 entries. "
            "Each entry has \"query_id\", \"retrieved\" (150 chunk ids, in the "
            "order the pipeline returned), and \"relevant\" (3 to 5 chunk ids, the "
            "clauses that answer that question). This unit generated the "
            "fixture so that the relevant clauses are almost all present somewhere "
            "in the 150 retrieved. But their position within that list is close to "
            "random, the signature of a retriever with no reranking stage."
        ),
        starter=(
            'import json\n'
            'from app.metrics import recall_at_k\n'
            '\n'
            'data = json.load(open("fixtures/reranking/retrieval_results.json"))\n'
            'queries = data["queries"]\n'
            'first = queries[0]\n'
            '\n'
            'print("underwriter questions:", len(queries))\n'
            'print("candidates returned per question:", len(first["retrieved"]))\n'
            'print("clauses that carry the answer, first question:",\n'
            '      len(first["relevant"]))\n'
            'print("where they landed in the returned order:",\n'
            '      sorted(first["retrieved"].index(chunk) + 1\n'
            '             for chunk in first["relevant"]\n'
            '             if chunk in first["retrieved"]))\n'
            '\n'
            'window = 5\n'
            'in_window = [\n'
            '    recall_at_k(query["retrieved"], set(query["relevant"]), window)\n'
            '    for query in queries\n'
            ']\n'
            'print("mean recall at the k the answer is written from:",\n'
            '      round(sum(in_window) / len(in_window), 4))\n'
            '\n'
            '# TODO: that one rate cannot say whether the operative clauses are\n'
            '# absent from the candidate set or merely sorted below the window\n'
            '# the answer is written from. Decide the second k that settles it,\n'
            '# measure the same 180 questions there, and report the gap between\n'
            '# the two means. recall_at_k() does the arithmetic once you decide\n'
            '# what to hand it.\n'
        ),
        metric="recall_at_k",
        expected=0.8357,
        tolerance=0.0005,
        because=(
            "Mean recall@5 across the 180 questions is about 0.078 and mean "
            "recall@150 is about 0.914, for a gap of about 0.836. Recall@150 being "
            "over 0.9 means Ledger's retriever is finding almost every clause that "
            "matters. Recall@5 under 0.08 means almost none of it survives into the "
            "small window the answer gets written from. That combination, a high "
            "ceiling and a low floor on the same questions, is what a missing "
            "reranker looks like in a measurement. It is not just a sentence."
        ),
    ),
    sources=(
        "anthropic.com/news/contextual-retrieval (2024-09-19), top-20 retrieval "
        "failure rate table: basic embeddings 5.7%, +contextual embeddings 3.7%, "
        "+contextual BM25 2.9%, +reranking 1.9%",
        "arXiv:2104.08663 (2021-04-17), BEIR benchmark: BM25+cross-encoder reranking "
        "beat plain BM25 on 16 of 18 zero-shot datasets, ~11% average nDCG@10 gain",
    ),
)

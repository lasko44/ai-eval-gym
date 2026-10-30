"""Unit 02: missing rerankers, and why recall at one k hides them.

A retrieval pipeline can find the right documents and still fail, because
finding them and ranking them near the top are two different jobs, done by
two different stages. Numbers and citations verified against primary
sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


UNIT = Unit(
    slug="reranking",
    number=2,
    title="Missing rerankers, and the recall number that hides them",
    failure=(
        "A retrieval pipeline finds the right documents somewhere in its candidate "
        "set. But it ranks them so badly that a small top-k context window never sees "
        "most of them."
    ),
    detection=(
        "Measure recall at a small k and a large k on the same query set. The gap "
        "between the two names whether the fault is ordering or coverage."
    ),
    minutes=20,
    brief=(
        "Most retrieval evals stop at one number: recall at whatever k you plan to "
        "feed the model, usually five or ten chunks. The number comes back "
        "reasonable, nothing alarms anyone, and the pipeline ships. What that single "
        "number cannot tell you is whether the documents you wanted were absent from "
        "the candidate set entirely. Or the documents were present in the set and "
        "simply buried below the cutoff where nobody looked. Those are different failures with different "
        "fixes, and a single recall@k conflates them into one reassuring digit.",
        "The usual retrieval stack has two jobs stacked on top of each other, and "
        "most pipelines only do the first one. An embedding search (or BM25, or "
        "both) casts a wide net cheaply. It scores every candidate against the "
        "query using a single vector or a bag-of-words signal. That signal is good "
        "at getting plausible documents into a large candidate set, but it is weak "
        "at ordering them precisely. It never looks at the query and a specific "
        "document together.",
        "A reranker, typically a cross-encoder, takes a smaller candidate set and "
        "scores each query-document pair jointly. That is far more expensive per "
        "pair, but far more accurate at ordering. Skip that second stage and you "
        "get a pipeline that is good at finding and bad at sorting. Recall at a "
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
        "That effect is not limited to the pipeline of one vendor. The BEIR "
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
        "(say 150) is much higher than recall at a small k (say 5), the right "
        "documents are in your candidate set. A reranker could move them up, and "
        "adding one is likely to close most of that gap.",
        "If both numbers are low, the documents are not in the candidate set at "
        "all, no matter how far you look. A reranker cannot fix that. It can only "
        "reorder what the first stage already retrieved. It cannot retrieve what "
        "was never there. Reporting a single recall@k erases this distinction "
        "completely. Reporting both numbers, and the gap between them, is what "
        "tells you which of two very different fixes you actually need.",
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
                "You add a cross-encoder reranker on top of an existing retrieval "
                "pipeline, and it scores the existing candidates from that pipeline "
                "against the query. What can it do, mechanically?"
            ),
            choices=(
                Choice("a", "Increase recall at any k, including very large k"),
                Choice("b", "Reorder the candidates the first stage already retrieved. It cannot add documents the first stage never found"),
                Choice("c", "Replace the need for a first-stage retriever entirely"),
                Choice("d", "Reduce the size of the embedding index needed in production"),
            ),
            answer="b",
            because=(
                "A reranker only sees the candidate set handed to it by the stage "
                "before it. So recall at a k large enough to cover that whole "
                "candidate set is a ceiling the reranker cannot push past. If the "
                "right document is not in the first 150 candidates, no amount of "
                "rescoring surfaces it. This is also why cross-encoders are not run "
                "over an entire corpus directly. Scoring every query against every "
                "document jointly does not scale. So a cheap first stage has to "
                "narrow the field before the expensive, accurate stage gets to rank "
                "it."
            ),
        ),
        Probe(
            id="interpreting-the-gap",
            asks=(
                "You measure recall@5 = 0.20 and recall@100 = 0.85 for a retrieval "
                "pipeline on the same query set. What have you established?"
            ),
            choices=(
                Choice("a", "The embedding model is poor quality, so you should swap it"),
                Choice("b", "The documents are mostly being found but ranked badly: this is a reranking problem, not an embedding problem"),
                Choice("c", "Production should raise k to 100 so users see the right documents"),
                Choice("d", "Nothing is conclusive. A 65-point gap could mean anything without more data"),
            ),
            answer="b",
            because=(
                "A large gap between a small-k and a large-k recall, with the large-k "
                "number high, means the first stage is doing its job. The relevant "
                "documents are present in the candidate set. Swapping the embedding "
                "model (option a) targets the wrong stage and risks making no "
                "difference, since the embeddings already found 85 percent of what "
                "mattered. Raising k in production (option c) does not fix anything "
                "either, since the model prompt still only reads the first handful of "
                "chunks. It would just hand the same badly-ordered list to a bigger "
                "context window. The fix that matches this signature is a reranking "
                "stage between retrieval and the prompt."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of 180 queries. Each query has a "
            "list of 150 retrieved document ids, in the order the pipeline returned "
            "them. It also has the set of document ids that are genuinely relevant "
            "to that query. Compute recall@5 and recall@150 for every query, "
            "average each across all 180 queries, and post the gap: mean recall@150 "
            "minus mean recall@5."
        ),
        fixture_path="fixtures/reranking/retrieval_results.json",
        fixture_note=(
            "A JSON object with one key, \"queries\", holding a list of 180 entries. "
            "Each entry has \"query_id\", \"retrieved\" (150 document ids, in the "
            "order the pipeline returned), and \"relevant\" (3 to 5 document ids, "
            "the true positives for that query). This unit generated the fixture "
            "so that the relevant documents are almost all present somewhere in "
            "the 150 retrieved. But their position within that list is close to "
            "random, the signature of a retriever with no reranking stage."
        ),
        starter=(
            'import json\n'
            'from app.metrics import recall_at_k\n'
            '\n'
            'data = json.load(open("fixtures/reranking/retrieval_results.json"))\n'
            'queries = data["queries"]\n'
            '\n'
            '# recall_at_k(retrieved, relevant, k) wants relevant as a set.\n'
            '# Compute recall@5 and recall@150 for each query, average each across\n'
            '# all 180 queries, then work out what to post: not a single recall\n'
            '# value on its own, the gap between the two.\n'
        ),
        metric="recall_at_k",
        expected=0.8357,
        tolerance=0.0005,
        because=(
            "Mean recall@5 across the 180 queries is about 0.078 and mean recall@150 "
            "is about 0.914, for a gap of about 0.836. Recall@150 being over 0.9 "
            "means the retriever is finding almost everything that matters. "
            "Recall@5 under 0.08 means almost none of it survives into a small "
            "top-k window. That combination, a high ceiling and a low floor on the "
            "same query set, is what a missing reranker looks like in a "
            "measurement. It is not just a sentence."
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

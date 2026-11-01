"""Unit 09: a recall number with no throughput beside it.

A vector index benchmark that reports recall at ten alone, with no queries
per second, no memory figure, and no parameter setting beside it. Numbers
and citations verified against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key. There is no app.metrics function for this one:
    holding recall equal before comparing throughput is the whole measurement.
    """
    indexes = {entry["name"]: entry for entry in data["indexes"]}
    for hnsw in indexes["hnsw"]["runs"]:
        for ivf in indexes["ivf_pq"]["runs"]:
            if hnsw["recall_at_10"] == ivf["recall_at_10"]:
                return float(
                    ivf["queries_per_second"] - hnsw["queries_per_second"]
                )
    raise ValueError(
        "no HNSW run and IVF run in this fixture share a recall_at_10, so "
        "there is no equal-recall pair to compare throughput at"
    )


UNIT = Unit(
    slug="index-tradeoff",
    number=9,
    part="retrieval",
    title="A recall number with no throughput beside it",
    failure=(
        "A team benchmarks the vector index behind Ledger, reports recall at "
        "ten, and picks the index. Recall alone hides what the index paid to "
        "reach that number."
    ),
    detection=(
        "Sweep the index parameter. Measure recall and queries per second "
        "together at each setting on Ledger's own query load. Compare two "
        "indexes at equal recall, not at whichever setting each one happens "
        "to report."
    ),
    brief=(
        "A team benchmarks the index that serves Ledger and reports one "
        "number: recall at ten over the chunked credit agreements. The index "
        "looks accurate, so the team ships it. That number, "
        "alone, says nothing about what the index paid to reach it. Every "
        "approximate index trades accuracy for speed through at least one "
        "parameter. The same index can report almost any recall you want, if "
        "you pay for it in latency or in memory. A recall number with no "
        "throughput, no memory figure, and no parameter setting beside it "
        "hides a choice somebody already made for you.",
        "HNSW (Hierarchical Navigable Small World) builds a graph of links "
        "between vectors, layered so a search "
        "can jump far before it narrows in. Three parameters control it, and "
        "a vendor dashboard will use all three without explaining any of "
        "them. M sets the maximum number of links per vector. The reference "
        "implementation recommends a range of 2 to 100, with 12 to 48 "
        "typical for most data.",
        "ef_construction sets the search width used to build the graph. A "
        "larger value buys a better graph, at the cost of a longer build. "
        "ef, often called ef_search, sets the search width used at query "
        "time. Raise it, and you trade speed for accuracy, with no change "
        "to the graph at all.",
        "IVF (Inverted File) takes a different approach. It first clusters "
        "every vector into "
        "partitions, called lists, with a coarse quantizer. A search then "
        "checks only the lists closest to the query, and nprobe sets how "
        "many of them it checks. FAISS (Facebook AI Similarity Search) "
        "defaults nprobe to 1, so a search "
        "touches only the single nearest list unless you raise it. Raising "
        "nprobe checks more lists, and recall and query latency both rise "
        "together. Lowering nprobe is the fast, lossy version of the same "
        "index, available at query time, with no rebuild required.",
        "Memory is the third axis, and a vendor pitching Ledger rarely "
        "reports it next to recall and speed. FAISS documents a memory "
        "formula for HNSW. It "
        "costs about four bytes per dimension for the stored vector, plus "
        "about eight bytes for every one of the M links each vector keeps. "
        "Multiply that per-vector figure by the vector count for the index "
        "total. A product-quantized IVF index instead stores a short code "
        "per vector and never keeps the full vector around. At a million "
        "vectors in 128 dimensions, that difference separates a few "
        "hundred megabytes from a few dozen.",
        "The fix is to sweep the parameter, ef_search or nprobe, and "
        "record recall and queries per second together at every setting. "
        "ANN-Benchmarks (Approximate Nearest Neighbor) is the public benchmark "
        "built for exactly this "
        "problem. It plots every algorithm the same way: recall against "
        "queries per second, across a full range of each algorithm's "
        "parameter settings. Its own paper describes the result as a "
        "Pareto frontier over all the runs of an algorithm. That frontier "
        "is the accuracy-speed curve a single number tries to hide. "
        "Reading that curve lets you compare two candidate indexes for "
        "Ledger at the same recall, instead of at whichever setting each one "
        "happens to report.",
        "That curve also has a knee: a point past which a small gain in "
        "recall starts to cost a large drop in throughput. Push an index "
        "past its knee and you pay a steep latency bill for an accuracy gain "
        "no underwriter will ever notice. Stop well short of it, and you "
        "leave accuracy on the table for free. A build-versus-buy choice "
        "sits between a managed vector database and a self-hosted index. It "
        "lives or dies on where that knee sits for Ledger's own loan "
        "documents and its own query load. A vendor's one headline recall "
        "figure will not tell you.",
    ),
    builds_on=(
        "Unit 08. Reranking fixes the ordering of whatever the index "
        "handed it, and the index decides what there is to order. You "
        "cannot score either one until you hold the other still."
    ),
    probes=(
        Probe(
            id="recall-alone",
            asks=(
                "A vendor pitching the index for Ledger reports: our index "
                "reaches recall at ten of 0.978. No queries per second, no "
                "memory figure, and no parameter setting appear anywhere "
                "near that number. What does the figure, by itself, "
                "establish?"
            ),
            choices=(
                Choice("a", "The index is production ready, since 0.978 is a high recall"),
                Choice("b", "Nothing about cost. It is one point on a curve that trades recall for speed and memory, and the other two axes are missing"),
                Choice("c", "The index beats any other index at the same task"),
                Choice("d", "The figure proves the index needs no further tuning"),
            ),
            answer="b",
            because=(
                "Every approximate index can reach almost any recall you "
                "name, given enough latency or memory to spend on it. A "
                "recall figure with no throughput or memory beside it does "
                "not tell you whether that spend was small or enormous. It "
                "tells you the vendor picked one operating point and did not "
                "show you the rest of the curve. The number is not wrong, it "
                "is simply incomplete, and incomplete in the direction that "
                "flatters the index."
            ),
        ),
        Probe(
            id="equal-recall-reversal",
            asks=(
                "Two indexes are on the table for Ledger. Index A's best "
                "setting reaches recall 0.97 at 900 queries "
                "per second. Index B's default setting reaches recall 0.80 "
                "at 3000 queries per second. The team picks index A for its "
                "higher recall. Pushed up to recall 0.97, index B still "
                "sustains 1200 queries per second. What does this show?"
            ),
            choices=(
                Choice("a", "Index A was the right pick, since it has the higher raw recall number"),
                Choice("b", "At equal recall, index B is faster than index A. The raw-recall comparison picked the slower index by judging it against the wrong setting of its rival"),
                Choice("c", "Index B's low default recall of 0.80 proves it is the worse index overall"),
                Choice("d", "Queries per second stops mattering once recall passes 0.95"),
            ),
            answer="b",
            because=(
                "Comparing index A's best setting to index B's default "
                "setting compares two different operating points, not two "
                "indexes. Once you push both to the same recall, index B "
                "sustains 1200 queries per second against index A's 900. "
                "The team's original pick was the slower index, and the "
                "raw-recall comparison never surfaced that because it never "
                "held recall equal in the first place."
            ),
        ),
        Probe(
            id="query-time-vs-build-time",
            asks=(
                "You want Ledger's HNSW index to answer underwriter "
                "questions faster at the same recall, without rebuilding "
                "the index over every credit agreement again. Which "
                "parameter do you change, and why can you change it without "
                "a rebuild?"
            ),
            choices=(
                Choice("a", "M, since it sets the number of links and you can edit a live graph directly"),
                Choice("b", "ef_construction, since it is read again on every query"),
                Choice("c", "ef (ef_search), since it only sets the search width read at query time and never touches the stored graph"),
                Choice("d", "None of them. Every HNSW parameter requires a full rebuild to change"),
            ),
            answer="c",
            because=(
                "The build step bakes in M and ef_construction. M fixes how "
                "many links each vector keeps. ef_construction sets how "
                "carefully the graph chose those links. Changing either one "
                "means building a new graph. ef (ef_search) stays fresh on "
                "every query, and it just sets how wide that one search "
                "looks. Raising or lowering it trades speed for accuracy on "
                "an existing index, with nothing to rebuild."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture that sweeps two candidate indexes "
            "for Ledger over the same one million chunk collection of "
            "credit agreements and amendments. It sweeps HNSW over "
            "ef_search and IVF with product quantization over nprobe, plus "
            "one exhaustive flat baseline. Find the HNSW setting and the "
            "IVF setting that reach the same recall at ten. Post the gap "
            "between them: the IVF queries per second at that setting, "
            "minus the HNSW queries per second at that setting."
        ),
        fixture_path="fixtures/index_tradeoff/index_sweep.json",
        fixture_note=(
            "A JSON (JavaScript Object Notation) object. It holds \"dataset\" "
            "(vector count, dimension, and k) "
            "and \"indexes\", a list of three entries named flat, hnsw, and "
            "ivf_pq. Each entry has a memory_mb figure computed from the "
            "published HNSW and product-quantization memory formulas, and "
            "\"runs\": a list of settings. Each run has param_value, hits, "
            "n_queries, recall_at_10, and queries_per_second. The fixture "
            "builds one HNSW run and one IVF run to land on the exact same "
            "recall_at_10. That lets you compare the two candidates for "
            "Ledger at equal recall, without interpolating between the two "
            "curves."
        ),
        starter=(
            'import json\n'
            '\n'
            'data = json.load(open("fixtures/index_tradeoff/index_sweep.json"))\n'
            'indexes = {entry["name"]: entry for entry in data["indexes"]}\n'
            'hnsw_runs = indexes["hnsw"]["runs"]\n'
            'ivf_runs = indexes["ivf_pq"]["runs"]\n'
            '\n'
            '# Find the hnsw run and the ivf_pq run whose recall_at_10 match.\n'
            '# This arithmetic is not in app.metrics: work it out yourself the\n'
            '# way a harness would. Once you have the matching pair, post\n'
            '# ivf queries_per_second minus hnsw queries_per_second.\n'
        ),
        metric="qps_gap_at_equal_recall",
        expected=255.0,
        tolerance=1.0,
        because=(
            "HNSW at ef_search=300 and IVF at nprobe=128 both land on "
            "recall_at_10 = 0.971, the same hit count out of 10000 "
            "underwriter questions by construction. At that matched recall, "
            "HNSW sustains 974 queries per second and IVF sustains 1229, a "
            "gap of 255 in IVF's favor. A team comparing HNSW's own best "
            "setting, recall 0.978, against IVF's low default setting, "
            "recall 0.704, would have picked HNSW on recall alone. HNSW "
            "also costs about 610 megabytes on this fixture against IVF's "
            "38. The index that looked better at a glance is the slower, "
            "heavier one once you hold recall equal. Ledger would have paid "
            "for that on every underwriter question."
        ),
    ),
    sources=(
        "arXiv:1603.09320 (2016-03-30), Malkov and Yashunin, Efficient and "
        "robust approximate nearest neighbor search using Hierarchical "
        "Navigable Small World graphs, the layered proximity graph this "
        "unit measures",
        "github.com/nmslib/hnswlib, ALGO_PARAMS.md (the HNSW reference "
        "implementation): M recommended 2 to 100, 12 to 48 typical, memory "
        "roughly M times 8 to 10 bytes per element, ef_construction trades "
        "build time for graph quality, ef trades query speed for accuracy "
        "and cannot go below k",
        "github.com/facebookresearch/faiss wiki, Guidelines-to-choose-an-index: "
        "nprobe sets how many inverted lists an IVF search visits and "
        "defaults to 1, HNSW memory is d*4 + M*2*4 bytes per vector, a "
        "product-quantized index stores m bytes per vector for an m-byte code",
        "arXiv:1807.05614 (2018-07-13), ANN-Benchmarks: a benchmarking tool "
        "for approximate nearest neighbor algorithms, which sweeps a range "
        "of parameter settings per algorithm and plots the Pareto frontier "
        "of recall against queries per second, plus index build time and "
        "index size",
    ),
)

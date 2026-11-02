"""Unit 10: an aggregate score that hides a multi-hop collapse.

One retrieval pass per question looks fine until you segment by how many
facts the question needs chained together. Numbers and citations verified
against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key. There is no app.metrics function for this one:
    the segmentation is the whole measurement.
    """
    rows = data["results"]
    single = [row for row in rows if row["hop_count"] == 1]
    multi = [row for row in rows if row["hop_count"] >= 2]
    single_accuracy = sum(1 for row in single if row["correct"]) / len(single)
    multi_accuracy = sum(1 for row in multi if row["correct"]) / len(multi)
    return single_accuracy - multi_accuracy


UNIT = Unit(
    slug="multi-hop",
    number=10,
    part="retrieval",
    title="An aggregate score that hides a multi-hop collapse",
    failure=(
        "Ledger does one retrieval pass per question. A question whose answer "
        "spans the original clause and the amendments that rewrote it fails "
        "badly. Ledger can only find the amendment once it knows which clause "
        "to look for, and a single pass never goes back for it."
    ),
    detection=(
        "Segment the eval set by hop count, the number of documents an answer "
        "has to chain, and report per-segment accuracy, never one aggregate."
    ),
    brief=(
        "A single retrieval pass works like this: embed the underwriter's "
        "question, fetch the k nearest chunks, hand them to the model, done. "
        "That is fine when the answer lives in one document. It breaks down the "
        "moment the answer needs two clauses chained together. The query you "
        "embedded came from the original question, not from the intermediate "
        "clause you have not found yet.",
        "Ask whether the borrower can make a distribution. The restricted "
        "payments covenant in the credit agreement permits one only under a "
        "leverage test, and a later amendment rewrote the ratio that test "
        "uses. A single pass has to retrieve the amended ratio before it knows "
        "which section the amendment touched. The index stores that amendment "
        "under its own heading and its own effective date, not under the words "
        "of the covenant it replaced. So nothing in the query vector points at "
        "it. The retriever never misread the question: the question itself "
        "asked for the wrong thing, because Ledger could not know the right "
        "thing yet.",
        "A controlled ablation of an agentic retrieval-augmented pipeline "
        "isolated exactly this. The test ran on 5,000 HotpotQA distractor "
        "questions, using a local 7B model with no proprietary API "
        "(Application Programming Interface) calls. "
        "Capping the retrieval loop at a single step cost 7.1 points of "
        "exact match against the same pipeline allowed two to five "
        "iterations. That was the single largest drop of any component "
        "tested, about four times the 1.7 point drop from removing the "
        "cross-encoder reranker entirely.",
        "Two iterations recovered to within 0.3 points of the five-step "
        "pipeline. The damage is almost entirely about whether the loop "
        "runs more than once, not about how many times beyond that. The "
        "single-pass baseline in the same study trailed the full pipeline "
        "by 10.1 points of exact match overall. That baseline differs from "
        "the capped loop above: it also drops query decomposition and "
        "reranking, rather than only the extra iterations.",
        "HotpotQA distractor questions are themselves a mostly two-hop "
        "benchmark, so that whole 10-point gap sits inside questions a "
        "one-pass system was never built to answer. A second, separate "
        "study measured what happens hop by hop rather than pass by pass. "
        "The study ran an iterative hop-by-hop retrieval pipeline over the "
        "MuSiQue development set, 2,417 questions and 6,404 individual hop "
        "evaluations. The rate at which the needed fact was actually present "
        "in context fell sharply hop by hop. It dropped from 68.5 percent "
        "at the first hop to 43.7 percent at the second, 30.7 percent at "
        "the third, and 18.5 percent at the fourth.",
        "The paper explains this with the same mechanism as above. Later "
        "hops ask about entities that only become known during earlier "
        "reasoning steps, so the system cannot retrieve their supporting "
        "evidence ahead of time. Even a pipeline that does loop back degrades hop "
        "over hop, because retrieval at each hop depends on the previous "
        "hop having actually resolved. For Ledger, the first hop is the "
        "original clause and every hop after it is an amendment that moved "
        "that clause. A pipeline that never loops back at "
        "all is the hop 1 number repeated forever, dressed up as an answer "
        "to hop 3.",
        "None of this shows up if the only thing reported is one accuracy "
        "number over the whole eval set. Questions answerable from the credit "
        "agreement alone usually outnumber the ones that span an amendment "
        "chain, often by a wide "
        "margin. A system that is excellent on the easy majority and "
        "terrible on the hard minority can post an aggregate that looks "
        "perfectly respectable.",
        "Here is the arithmetic. The next four numbers are a worked "
        "illustration, not a measurement from either study above. Suppose "
        "70 percent of questions are single-hop and the system gets 90 "
        "percent of those right, while it gets only 35 percent of the "
        "multi-hop 30 percent right. The blended score lands around 73 "
        "percent, a number nobody would flag in a release review of Ledger. "
        "That score sits on top of a segment that fails most of the time. "
        "The failing segment is the one thing Ledger exists to do: read a "
        "clause together with the amendments that changed it.",
        "The general instinct this is training is bigger than retrieval. "
        "Any aggregate computed over a mixed population can hide the "
        "subpopulation where a system actually fails. That happens as long "
        "as the subpopulation is small enough, or the majority is doing "
        "well enough to carry the average.",
        "The question to ask of any reported number is not just what it "
        "measures, but what it is an average over. What segments make up "
        "this population? Do they fail at different rates? Would the number "
        "survive a split along the axis that actually explains why the "
        "system fails?",
        "Hop count is the axis for this unit. It will not be the axis next "
        "time, and knowing to ask the question is worth more than "
        "memorizing this one.",
    ),
    builds_on=(
        "Units 08 and 09. Both measure a single retrieval pass. Ledger's "
        "answer usually needs the original clause and the amendments that "
        "changed it, which is more passes than one."
    ),
    probes=(
        Probe(
            id="single-pass-penalty",
            asks=(
                "In the HotpotQA component ablation, how much exact match "
                "did a single-pass retrieval loop lose against the same "
                "pipeline allowed two to five iterations? How did that loss "
                "compare to removing the reranker instead?"
            ),
            choices=(
                Choice("a", "0.7 points, about half the 1.7 point drop from the reranker"),
                Choice("b", "7.1 points, roughly four times the 1.7 point drop from the reranker"),
                Choice("c", "7.1 points, but smaller than the reranker drop once you factor in latency"),
                Choice("d", "No measurable difference, the loop only helps on latency, not accuracy"),
            ),
            answer="b",
            because=(
                "Capping the loop at one step (steps-1) cost 7.1 EM (Exact Match) "
                "relative "
                "to the full pipeline. That was the largest single-component "
                "drop measured, versus 1.7 EM for removing the cross-encoder "
                "reranker entirely. The gap tells you where the accuracy of "
                "the pipeline actually lives. The ability to go back for a "
                "second fact matters roughly four times more than how well "
                "the first pass ranks results."
            ),
        ),
        Probe(
            id="hop-by-hop-degradation",
            asks=(
                "A separate study used an iterative pipeline that retrieves "
                "again at each step. It measured how often the needed fact "
                "was actually present in context at each hop of a multi-hop "
                "question. What did that rate do from hop 1 to hop 4?"
            ),
            choices=(
                Choice("a", "Stayed roughly flat near 65 percent, since the pipeline retrieves fresh at every hop"),
                Choice("b", "Rose slightly, since later hops have more accumulated context to work from"),
                Choice("c", "Fell from 68.5 percent at hop 1 to 18.5 percent at hop 4"),
                Choice("d", "Dropped to zero after hop 2, since MuSiQue questions never go past two hops"),
            ),
            answer="c",
            because=(
                "Fact presence fell from 68.5 percent at hop 1 to 43.7 at "
                "hop 2, 30.7 at hop 3, and 18.5 at hop 4. That happened even "
                "with a pipeline that loops back and retrieves again at "
                "each step. The mechanism is that each later hop depends on "
                "the answer from an earlier hop, so error early in the "
                "chain compounds forward. A pipeline that never loops back "
                "at all does not even get the benefit of that partial "
                "recovery."
            ),
        ),
        Probe(
            id="aggregate-mix",
            asks=(
                "Ledger, a RAG (Retrieval-Augmented Generation) system like "
                "any other, reports 73 percent overall accuracy on a mixed "
                "eval set and nobody flags it in review. What does the "
                "general lesson of this unit say you should ask before "
                "accepting that number?"
            ),
            choices=(
                Choice("a", "Nothing further, 73 percent clears most teams' informal bar for shipping"),
                Choice("b", "What population makes up the aggregate, and whether a segment within it is failing at a much worse rate than the headline number suggests"),
                Choice("c", "Whether 73 percent is statistically significant against a 50 percent baseline"),
                Choice("d", "Whether the eval set is large enough, since aggregate accuracy is always trustworthy above a few hundred examples"),
            ),
            answer="b",
            because=(
                "An aggregate blends whatever subpopulations make up the "
                "eval set. A majority that is doing well can carry an "
                "average over a minority that is doing badly. Accuracy of "
                "90 percent on 70 percent of questions, combined with 35 "
                "percent accuracy on the remaining 30 percent, blends to "
                "about 73 percent. That number gives no hint that one in "
                "three questions on the harder segment gets barely better "
                "than chance. This is not specific to amendments: it is true "
                "of any aggregate over any mixed population, which is the "
                "transferable part of this lesson."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of 320 Ledger answers, each tagged "
            "with how many documents the answer had to chain and whether "
            "Ledger got it right. Compute accuracy for the single-hop "
            "questions (hop_count 1) and accuracy for the multi-hop "
            "questions (hop_count 2 or more). Post the gap: single-hop "
            "accuracy minus multi-hop accuracy."
        ),
        fixture_path="fixtures/multi_hop/eval_results.json",
        fixture_note=(
            "A list of 320 rows under \"results\", each with an id, a "
            "hop_count (1, 2, or 3), and whether Ledger answered it "
            "correctly. 220 of the 320 are single-hop, answerable from the "
            "credit agreement alone, so the aggregate over "
            "all 320 skews toward however Ledger does on the easy "
            "majority. The per-hop accuracies are synthetic, produced with a "
            "fixed seed for this unit. They match the documented pattern of "
            "steep degradation after hop 1, rather than reproducing the "
            "exact figures of any one paper."
        ),
        starter=(
            'import json\n'
            '\n'
            'fixture = json.load(open("fixtures/multi_hop/eval_results.json"))\n'
            'results = fixture["results"]\n'
            '\n'
            'print("answers scored:", len(results))\n'
            'print("one row looks like:", results[0])\n'
            'for hops in sorted({row["hop_count"] for row in results}):\n'
            '    rows = [row for row in results if row["hop_count"] == hops]\n'
            '    print("  hop_count", hops, "| questions:", len(rows))\n'
            'print("aggregate accuracy over all of them:",\n'
            '      round(sum(1 for row in results if row["correct"])\n'
            '            / len(results), 4))\n'
            '\n'
            '# TODO: that aggregate is an average over a mixed population, and\n'
            '# the dashboard reports it alone. Decide which split of these\n'
            '# questions explains where Ledger actually fails, score each side\n'
            '# of that split on its own, and report the gap between the two.\n'
        ),
        metric="single_hop_minus_multi_hop_accuracy",
        expected=0.55,
        tolerance=0.0005,
        because=(
            "Single-hop accuracy is 198/220, 0.9, multi-hop accuracy (hop "
            "counts 2 and 3 combined) is 35/100, 0.35, and the gap is 0.55. "
            "The aggregate over all 320 questions is 0.728. That is what a "
            "dashboard reporting one number would show: a system that looks "
            "like it gets roughly three questions in four right. In fact "
            "Ledger fails on nearly two in three of the questions that "
            "needed an amendment read together with the clause it rewrote. "
            "The aggregate is not wrong. It "
            "is just an average over a population where that average hides "
            "the thing worth knowing."
        ),
    ),
    sources=(
        "arXiv:2606.21553 (2026-06-19), component ablation of an agentic RAG "
        "pipeline on 5,000 HotpotQA distractor questions, steps-1 vs full "
        "pipeline and no-reranker ablations",
        "arXiv:2609.17043, fact presence by hop depth on MuSiQue's "
        "development set under an iterative hop-by-hop retrieval pipeline",
    ),
)

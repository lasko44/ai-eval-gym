"""Unit 07: an aggregate score that hides a multi-hop collapse.

One retrieval pass per question looks fine until you segment by how many
facts the question needs chained together. Numbers and citations verified
against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


UNIT = Unit(
    slug="multi-hop",
    number=7,
    title="An aggregate score that hides a multi-hop collapse",
    failure=(
        "A system does one retrieval pass per question. Questions needing two "
        "or three facts chained together fail badly, because the second fact "
        "can only be found once the first one is known, and a single pass "
        "never goes back for it."
    ),
    detection=(
        "Segment the eval set by hop count and report per-segment accuracy, "
        "never one aggregate."
    ),
    minutes=25,
    brief=(
        "A single retrieval pass works like this: embed the question, fetch "
        "the k nearest passages, hand them to the model, done. That is fine "
        "when the answer lives in one document. It breaks down the moment a "
        "question needs two facts chained together, because the query you "
        "embedded was built from the original question, not from the "
        "intermediate fact you have not found yet. Ask who directed the film "
        "that won best picture the year a given actor was born, and a single "
        "pass has to retrieve for 'the film that won best picture the year X "
        "was born' before it knows which year that is. The passage naming "
        "the director is indexed under the film's title, not under the "
        "actor's birth year, so nothing in the query vector points at it. "
        "The retriever was never wrong about what it was asked to find. It "
        "was asked to find the wrong thing, because the right thing could not "
        "be known yet.",
        "A controlled ablation of an agentic retrieval-augmented pipeline on "
        "5,000 HotpotQA distractor questions, run on a local 7B model with no "
        "proprietary API calls, isolated exactly this. Capping the retrieval "
        "loop at a single step cost 7.1 points of exact match against the "
        "same pipeline allowed two to five iterations, the single largest "
        "drop of any component tested, about four times the 1.7 point drop "
        "from removing the cross-encoder reranker entirely. Two iterations "
        "recovered to within 0.3 points of the five-step pipeline, so the "
        "damage is almost entirely about whether the loop runs more than "
        "once, not about how many times beyond that. The single-pass "
        "baseline in the same study trailed the full pipeline by 10.1 points "
        "of exact match overall, and HotpotQA's distractor questions are "
        "themselves a mostly two-hop benchmark, so that whole 10-point gap "
        "sits inside questions a one-pass system was never built to answer.",
        "A second, separate study measured what happens hop by hop rather "
        "than pass by pass. Running an iterative hop-by-hop retrieval "
        "pipeline over MuSiQue's development set, 2,417 questions and 6,404 "
        "individual hop evaluations, the rate at which the needed fact was "
        "actually present in context fell from 68.5 percent at the first hop "
        "to 43.7 percent at the second, 30.7 percent at the third, and 18.5 "
        "percent at the fourth. The paper's own explanation is the same "
        "mechanism as above, stated plainly: later hops ask about entities "
        "that only become known during earlier reasoning steps, so their "
        "supporting evidence cannot be retrieved ahead of time. Even a "
        "pipeline that does loop back degrades hop over hop, because each "
        "hop's retrieval depends on the previous hop having actually "
        "resolved. A pipeline that never loops back at all is the hop 1 "
        "number repeated forever, dressed up as an answer to hop 3.",
        "None of this shows up if the only thing reported is one accuracy "
        "number over the whole eval set. Single-hop questions usually "
        "outnumber multi-hop ones in a realistic mix, often by a wide "
        "margin, so a system that is excellent on the easy majority and "
        "terrible on the hard minority can post an aggregate that looks "
        "perfectly respectable. The arithmetic is ordinary: if 70 percent of "
        "questions are single-hop and the system gets 90 percent of those "
        "right while getting only 35 percent of the multi-hop 30 percent "
        "right, the blended score lands around 73 percent, a number nobody "
        "would flag in a release review, built on top of a segment that is "
        "failing most of the time it is asked to do the one thing multi-hop "
        "retrieval exists for.",
        "The general instinct this is training is bigger than retrieval. Any "
        "aggregate computed over a mixed population can hide the "
        "subpopulation where a system actually fails, as long as that "
        "subpopulation is small enough or the majority is doing well enough "
        "to carry the average. The question to ask of any reported number is "
        "not just what it measures but what it is an average over: what "
        "segments make up this population, do they fail at different rates, "
        "and would the number you are looking at survive being split along "
        "the axis that actually explains the system's failures. Hop count is "
        "this unit's axis. It will not be the axis next time, and knowing to "
        "ask the question is worth more than memorizing this one.",
    ),
    probes=(
        Probe(
            id="single-pass-penalty",
            asks=(
                "In the HotpotQA component ablation, capping the retrieval "
                "loop at a single pass cost how much exact match compared to "
                "the same pipeline with two to five iterations, and how did "
                "that compare to removing the reranker instead?"
            ),
            choices=(
                Choice("a", "0.7 points, about half the reranker's 1.7 point drop"),
                Choice("b", "7.1 points, roughly four times the reranker's 1.7 point drop"),
                Choice("c", "7.1 points, but less than the reranker's drop once latency is accounted for"),
                Choice("d", "No measurable difference, the loop only helps on latency, not accuracy"),
            ),
            answer="b",
            because=(
                "Capping the loop at one step (steps-1) cost 7.1 EM relative "
                "to the full pipeline, the largest single-component drop "
                "measured, versus 1.7 EM for removing the cross-encoder "
                "reranker entirely. The gap tells you where the pipeline's "
                "accuracy actually lives: the ability to go back for a second "
                "fact matters roughly four times more than how well the first "
                "pass is ranked."
            ),
        ),
        Probe(
            id="hop-by-hop-degradation",
            asks=(
                "A separate study measured how often the needed fact was "
                "actually present in context at each hop of a multi-hop "
                "question, using an iterative pipeline that does retrieve "
                "again at each step. What did that rate do from hop 1 to "
                "hop 4?"
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
                "hop 2, 30.7 at hop 3, and 18.5 at hop 4, even with a "
                "pipeline that loops back and retrieves again at each step. "
                "The mechanism is that a later hop's query depends on an "
                "earlier hop's answer, so any error or gap earlier in the "
                "chain compounds forward. A pipeline that never loops back at "
                "all does not even get the benefit of that partial recovery."
            ),
        ),
        Probe(
            id="aggregate-mix",
            asks=(
                "A RAG system reports 73 percent overall accuracy on a mixed "
                "eval set and nobody flags it in review. What does this unit's "
                "general lesson say you should ask before accepting that "
                "number?"
            ),
            choices=(
                Choice("a", "Nothing further, 73 percent clears most teams' informal bar for shipping"),
                Choice("b", "What population the aggregate is averaged over, and whether a segment within it is failing at a much worse rate than the headline number suggests"),
                Choice("c", "Whether 73 percent is statistically significant against a 50 percent baseline"),
                Choice("d", "Whether the eval set is large enough, since aggregate accuracy is always trustworthy above a few hundred examples"),
            ),
            answer="b",
            because=(
                "An aggregate blends whatever subpopulations make up the eval "
                "set, and a majority that is doing well can carry an average "
                "over a minority that is doing badly. 90 percent accuracy on "
                "70 percent of questions and 35 percent accuracy on the "
                "remaining 30 percent blends to about 73 percent, a number "
                "that gives no hint that one in three questions on the harder "
                "segment is being answered correctly barely better than "
                "chance. This is not specific to hop count: it is true of any "
                "aggregate over any mixed population, which is the transferable "
                "part of this lesson."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "A fixture of 320 question results is shipped with this unit, "
            "each tagged with how many hops it needs and whether the system "
            "got it right. Compute accuracy for the single-hop questions "
            "(hop_count 1) and accuracy for the multi-hop questions "
            "(hop_count 2 or more), and post the gap: single-hop accuracy "
            "minus multi-hop accuracy."
        ),
        fixture_path="fixtures/multi_hop/eval_results.json",
        fixture_note=(
            "A list of 320 rows under \"results\", each with an id, a "
            "hop_count (1, 2, or 3), and whether the system answered it "
            "correctly. 220 of the 320 are single-hop, so the aggregate over "
            "all 320 skews toward however the system does on the easy "
            "majority. The per-hop accuracies are synthetic, generated with a "
            "fixed seed for this unit, shaped to match the documented pattern "
            "of steep degradation after hop 1 rather than reproduced from any "
            "one paper's exact figures."
        ),
        starter=(
            'import json\n'
            '\n'
            'fixture = json.load(open("fixtures/multi_hop/eval_results.json"))\n'
            'results = fixture["results"]\n'
            '\n'
            '# This metric is not in app.metrics. Split results into single-hop\n'
            '# (hop_count == 1) and multi-hop (hop_count >= 2), compute accuracy\n'
            '# for each group, and work out single-hop accuracy minus multi-hop\n'
            '# accuracy. Print the overall aggregate accuracy too and compare it\n'
            '# to the gap.\n'
            'for row in results[:5]:\n'
            '    print(row)\n'
        ),
        metric="single_hop_minus_multi_hop_accuracy",
        expected=0.55,
        tolerance=0.0005,
        because=(
            "Single-hop accuracy is 198/220, 0.9. Multi-hop accuracy (hop "
            "counts 2 and 3 combined) is 35/100, 0.35. The gap is 0.55. The "
            "aggregate over all 320 questions is 0.728, which is what a "
            "dashboard reporting one number would show: a system that looks "
            "like it is getting roughly three questions in four right, when "
            "it is actually failing on nearly two in three of the questions "
            "that needed more than one fact chained together. The aggregate "
            "is not wrong, it is just averaging over a population where that "
            "average hides the thing worth knowing."
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

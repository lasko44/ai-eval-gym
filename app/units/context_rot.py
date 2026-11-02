"""Unit 12: context rot, where more context makes the answer worse.

Context length as a confound, held apart from distractor count and task
difficulty. Numbers and citations verified against primary sources; see
UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.
    """
    rows = sorted(data["results"], key=lambda row: row["length_tokens"])
    shortest = rows[0]["correct"] / rows[0]["total"]
    longest = rows[-1]["correct"] / rows[-1]["total"]
    return shortest - longest


UNIT = Unit(
    slug="context-rot",
    number=12,
    part="context",
    title="Context rot, where more context makes the answer worse",
    failure=(
        "A team stops curating what goes into Ledger's prompt because the context "
        "window is large enough to hold the whole credit agreement. Accuracy then "
        "drops as the context grows, even though the operative clause never left "
        "the context."
    ),
    detection="Sweep context length with the question and the operative clause held fixed, then measure accuracy at each length.",
    brief=(
        "A long context window reads like a solved problem. If the model can hold "
        "a hundred thousand tokens, the obvious move is to stop being careful about "
        "what Ledger retrieves. Pour the whole credit agreement and every amendment "
        "into the prompt and let the model sort it out. That instinct is the failure "
        "mode this unit trains you to catch, because the model does not sort it out "
        "for free.",
        "It is surprising precisely because the operative clause is sitting right "
        "there in the context the whole time. Nothing is missing. You did not fail "
        "to retrieve the clause, you included it. But Ledger still gets the covenant "
        "question wrong more often as you add more of the agreement around it. "
        "Intuition says a model that can see the clause should use it regardless of "
        "what else is on the page. Measured behavior disagrees with that intuition.",
        "The Chroma context rot report ran 18 models, five from Anthropic, seven "
        "from OpenAI, three from Google and three from Alibaba. It used a "
        "LongMemEval task that compared two prompts. One was a focused prompt "
        "holding only the roughly 300 tokens directly relevant to the question. "
        "The other was a full prompt of roughly 113,000 tokens, containing that "
        "same relevant material plus everything else. Every model family tested "
        "scored lower on the full prompt than on the focused one.",
        "The same report also found that even a single distractor sentence "
        "measurably lowers accuracy against a needle-only baseline. The drop "
        "compounds as you add more distractors. A credit agreement is full of "
        "distractors: the covenant next door, the defined term that almost "
        "matches, the schedule that repeats a clause. A second, independent "
        "measurement "
        "points the same way. The RULER benchmark put GPT-4 (Generative "
        "Pre-trained Transformer) at 96.6 percent "
        "accuracy at a 4,000 token context, and at 81.2 percent at 128,000 tokens. "
        "That is a 15.4 point drop with nothing about the task itself changed.",
        "Length is not the only axis that matters, and a third primary source shows "
        "why isolating it is hard. Liu et al.'s Lost in the Middle experiment held "
        "length fixed at 20 documents and moved only the position of the one "
        "relevant document. GPT-3.5-Turbo scored 75.8 percent with the relevant "
        "document first, 63.2 percent last, and 53.8 percent in the middle. That "
        "middle score sits below the closed-book accuracy of the model itself: "
        "56.1 percent, with no documents at all. Stuffing the context did not just "
        "fail to help, it did worse than giving the model nothing.",
        "That result used a fixed length, so it is a position effect, not a length "
        "effect. Conflating the two is exactly the mistake this unit is built to "
        "stop you from making.",
        "That is also why holding the operative clause fixed is the whole trick, not "
        "a detail. A sweep of Ledger's context length could change which clause "
        "carries the answer, or move that clause to a new position. It could also "
        "swap in a harder covenant question at longer lengths. Any of those changes "
        "could cause a drop in accuracy, and you would no longer know which one did "
        "it.",
        "Keep the question and the operative clause byte-for-byte identical across "
        "every length. Change only the pages of the agreement padded around it. Then "
        "you can attribute "
        "whatever accuracy change you measure to length alone. That is the "
        "difference between a chart that supports a claim and a chart that "
        "happens to look like it does.",
    ),
    builds_on=(
        "Unit 11. Multi-hop retrieval is how the prompt gets long in the "
        "first place. This unit is what the length costs once it is long."
    ),
    probes=(
        Probe(
            id="model-count",
            asks=(
                "The Chroma context rot report ran its LongMemEval comparison, a "
                "focused ~300 token prompt against a full ~113,000 token prompt. "
                "Across how many models did it run, and what did it find about "
                "which ones degraded?"
            ),
            choices=(
                Choice("a", "4 models, and only the smaller open-weight ones degraded"),
                Choice("b", "18 models across four providers, and every model family scored lower on the full prompt"),
                Choice("c", "18 models, but the degradation only showed up past 500,000 tokens"),
                Choice("d", "1 model, so the result does not generalize across providers"),
            ),
            answer="b",
            because=(
                "The report tested 5 Anthropic, 7 OpenAI, 3 Google and 3 Alibaba "
                "models, 18 in total. Every family scored lower on the full "
                "113,000 token prompt than on the focused 300 token prompt holding "
                "the same relevant content. The scale of the test is what makes the "
                "finding hard to dismiss as a quirk of one model."
            ),
        ),
        Probe(
            id="below-closed-book",
            asks=(
                "In Liu et al.'s Lost in the Middle experiment, GPT-3.5-Turbo scored "
                "53.8 percent when the one relevant document sat in the middle of 20 "
                "documents. Its closed-book accuracy, answering with no documents at "
                "all, was 56.1 percent. What does that comparison show?"
            ),
            choices=(
                Choice("a", "Nothing, closed-book accuracy is not a meaningful baseline"),
                Choice("b", "That the model ignored the context entirely and guessed"),
                Choice("c", "That giving the model the relevant document, badly placed, scored worse than giving it nothing"),
                Choice("d", "That 20 documents is too few to see a position effect"),
            ),
            answer="c",
            because=(
                "53.8 percent with the answer present but buried in the middle is "
                "below 56.1 percent with no documents supplied. Context did not just "
                "fail to help in that position, it actively hurt. That is a "
                "stronger claim than 'the model did not notice'. It is the kind of "
                "number that should make you suspicious of Ledger adding retrieved "
                "material without checking where the useful part lands."
            ),
        ),
        Probe(
            id="confound",
            asks=(
                "You sweep Ledger's context length from 2,000 to 100,000 tokens. At "
                "each length you also swap in a new operative clause and move it to "
                "a new position in the context. That is what Ledger's real retrieval "
                "pipeline would actually do at that length. Accuracy drops as length "
                "increases. What can you conclude?"
            ),
            choices=(
                Choice("a", "That length alone caused the drop, since length is what you varied"),
                Choice("b", "Nothing about length specifically, since which clause carries the answer and where it sits changed along with it"),
                Choice("c", "That position caused it and length is irrelevant"),
                Choice("d", "That the result is invalid, so you should discard it entirely"),
            ),
            answer="b",
            because=(
                "You changed three things at once: length, which clause carries the "
                "answer, and where it sits. Any of the three could be driving the "
                "drop, or some combination could be. The measurement is not wasted, "
                "it describes the behavior of the real pipeline, but it cannot support "
                "a claim about length specifically. That claim needs the version where "
                "the question and the operative clause are identical at every length "
                "and only the padding around them changes."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of Ledger accuracy trials at 5 context "
            "lengths, 200 trials per length. The covenant question and the "
            "operative clause stay fixed across every length. Compute the accuracy "
            "at each length. Then post the accuracy drop from the shortest length "
            "(500 tokens) to the longest length (113,000 tokens), expressed as a "
            "proportion (0.25 would mean a 25 percentage point drop)."
        ),
        fixture_path="fixtures/context_rot/length_sweep.json",
        fixture_note=(
            "A list of 5 rows, one per context length in length_tokens, each with "
            "correct and total out of 200 trials. The question and the operative "
            "clause are identical across every row, only the surrounding pages of "
            "the credit agreement differ."
        ),
        starter=(
            'import json\n'
            '\n'
            'fixture = json.load(open("fixtures/context_rot/length_sweep.json"))\n'
            'rows = sorted(fixture["results"], key=lambda row: row["length_tokens"])\n'
            '\n'
            'print("context lengths swept:", [row["length_tokens"] for row in rows])\n'
            'print("trials at each length:", [row["total"] for row in rows])\n'
            'print("correct at each length:", [row["correct"] for row in rows])\n'
            '\n'
            '# TODO: the question and the operative clause are identical in every\n'
            '# row, so the only thing separating one row from another is how much\n'
            '# text surrounds that clause. Decide what to measure at each length,\n'
            '# pick the two lengths that bracket the sweep, and print the fall from\n'
            '# the shorter of them to the longer as a proportion. This one is not in\n'
            '# app.metrics: the arithmetic is yours.\n'
        ),
        metric="accuracy_drop",
        expected=0.275,
        tolerance=0.0005,
        because=(
            "Accuracy runs 183/200 at 500 tokens (0.915) down to 128/200 at 113,000 "
            "tokens (0.64), a drop of 0.275. Every row shares the same question and "
            "the same operative clause. So the only thing that changed between rows "
            "is how much of the agreement surrounds that clause. A drop of this size "
            "with nothing else different is the signature this unit is about. Ledger "
            "had the clause the whole time and used it less reliably as the pages "
            "around it piled up."
        ),
    ),
    sources=(
        "trychroma.com/research/context-rot (2025-07-14), 18 models, LongMemEval focused vs full prompt, distractor sweep",
        "arXiv:2307.03172 (2023-07-06), Liu et al., Lost in the Middle, position accuracy for GPT-3.5-Turbo over 20 documents",
        "arXiv:2404.06654, RULER benchmark, GPT-4 accuracy at 4k vs 128k tokens",
    ),
)

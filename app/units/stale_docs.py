"""Unit 04: stale documents that poison a correct answer.

Retrieval handing a model a superseded passage instead of, or alongside, the
current one, and the model following it even though its own weights had the
right answer. Numbers and citations verified against primary sources; see
UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


UNIT = Unit(
    slug="stale-docs",
    number=4,
    title="Stale documents that poison a correct answer",
    failure=(
        "Retrieval hands the model an out-of-date passage and it abandons a "
        "correct answer it already had in its weights to follow the passage."
    ),
    detection=(
        "Build a knowledge-reversal set, ask each question with and without "
        "retrieval, and measure how often a previously correct answer flips "
        "to the stale one."
    ),
    brief=(
        "Teams usually sell retrieval as a fix for an outdated model. "
        "Training freezes the weights, so at inference time you hand the "
        "model a fresh passage, and it answers from that passage instead of "
        "from memory. The failure this unit covers is what happens when the "
        "passage you hand it is not fresh. The index holds a superseded "
        "version of a document, alongside or instead of the current one, "
        "because nobody deleted it when the new one shipped. The model had "
        "the right answer sitting in its weights the whole time. Retrieval "
        "handed it the wrong one anyway, and it followed the wrong one.",
        "This failure deserves its own unit rather than a line item under "
        "general retrieval noise, for one reason. Almost every team adds an "
        "instruction to cut down on hallucination: answer only from the "
        "provided context, or some version of it. Teams write that "
        "instruction to stop the model from making things up when the "
        "context is silent or thin. It says nothing about whether the "
        "context is current. A model cannot tell an officially authoritative "
        "passage from one that is authoritative only because an instruction "
        "told it to always trust the context. The instruction meant to make "
        "the system faithful to its sources instead makes it faithful to "
        "whichever source retrieval hands it, stale or not.",
        "A paper built exactly for this, Stale-Document Poisoning: When "
        "Outdated Retrieval Overrides Correct Model Answers (arXiv:2609.31342), "
        "constructed a benchmark of 317 verified knowledge reversals. Each "
        "reversal covers a question whose correct answer changed at a later "
        "date, across medicine, law, software or API behavior, and platform "
        "policy. For each reversal, the researchers first confirmed the "
        "model answered correctly with no retrieval at all. They then "
        "retrieved the superseded version of the document for the same "
        "question.",
        "Measured this way, stale retrieval overturned a previously correct "
        "answer 30 percent of the time for one model and 37 percent of the "
        "time for another. Neither model had any instruction telling it to "
        "trust the context. Add an explicit instruction to follow the "
        "retrieved document, and those rates jumped to 66 percent and 75 "
        "percent. Across all four models and domains they tested, poisoning "
        "ranged from 17 to 91 percent. The model followed matched "
        "up-to-date evidence correctly 97 to 100 percent of the time "
        "instead, so it is not simply bad at using retrieved context in "
        "general. It is bad specifically when that context is wrong and it "
        "has been told to trust it.",
        "None of this would mean anything without the comparison to the "
        "no-retrieval case. That comparison is the part of the method worth "
        "remembering, more than any single percentage. If you only ever "
        "test the model with the stale document in context, a wrong answer "
        "is ambiguous. Maybe the model never knew the right answer, maybe "
        "it was always going to get this question wrong, or maybe the "
        "question is just hard. Ask the same question twice, once cold and "
        "once with the stale passage retrieved, then count only the cases "
        "where the cold answer was right. That isolates the thing you "
        "actually care about: how often retrieval took a correct model and "
        "broke it.",
        "That is also exactly why a plain accuracy number on a RAG system "
        "under-reports this failure. A system can hold steady or even "
        "improve on overall accuracy while quietly destroying a "
        "double-digit share of the cases it used to get right. That happens "
        "because the gains on genuinely stale-sensitive questions and the "
        "losses on this failure mode land in the same aggregate number.",
        "The fix direction the same paper points at is not to drop the "
        "faithfulness instruction. An unconstrained model still hallucinates "
        "when context is missing or thin, so dropping the instruction is "
        "not the answer. Instead, the fix is to make retrieval and the "
        "prompt temporally aware. Surface the date each document took "
        "effect. Prefer the most recent version when more than one exists "
        "in the index. Tell the model explicitly when older evidence "
        "stopped applying, rather than asking it to treat every retrieved "
        "passage as equally current.",
        "The detection, though, has to come first. You cannot prioritize "
        "fixing a failure mode you have never measured. The measurement is "
        "cheap, once you have a set of questions whose answers changed at a "
        "known date.",
    ),
    probes=(
        Probe(
            id="instruction-effect",
            asks=(
                "A team adds the instruction 'answer only using the provided "
                "context' specifically to reduce hallucination. What does the "
                "stale-document research say this does to the rate at which a "
                "stale retrieved passage overturns an answer the model already "
                "had right?"
            ),
            choices=(
                Choice("a", "Lowers it, since the model now sticks closer to the evidence"),
                Choice("b", "Leaves it unchanged, the instruction only affects unretrieved questions"),
                Choice("c", "Roughly doubles it, from the 30-37 percent range to 66-75 percent"),
                Choice("d", "Eliminates it, since the instruction forces the model to check the date of the document"),
            ),
            answer="c",
            because=(
                "Without any instruction to trust the context, stale retrieval "
                "overturned a previously correct answer 30 to 37 percent of the "
                "time depending on the model. Telling the model to answer only "
                "from the provided context pushed that to 66 to 75 percent. "
                "Teams write that instruction to stop the model from inventing "
                "facts when context is thin. It has no way to also mean unless "
                "the context has gone stale instead. So it ends up making the "
                "model a more reliable transmitter of whatever the index "
                "happens to contain, current or not."
            ),
        ),
        Probe(
            id="why-the-comparison",
            asks=(
                "You want to measure stale-document poisoning. Why ask every "
                "question twice, once with no retrieval and once with a stale "
                "passage retrieved, instead of checking accuracy on the "
                "retrieval condition alone?"
            ),
            choices=(
                Choice("a", "Running it twice doubles the sample size, which is the only reason"),
                Choice("b", "Without the no-retrieval baseline you cannot tell poisoning apart from the model simply not knowing the answer"),
                Choice("c", "The no-retrieval condition is the control group required by statute for any RAG eval"),
                Choice("d", "There is no reason, a single accuracy number over the retrieval condition captures the same thing"),
            ),
            answer="b",
            because=(
                "A wrong answer with the stale document in context is "
                "ambiguous: the model might never have known the right "
                "answer, independent of retrieval. Restrict the poisoned "
                "count to questions the model answered correctly cold. Then "
                "check whether retrieval flipped that specific answer to the "
                "stale one. That isolates retrieval as the cause, rather "
                "than ordinary model error. This is the same reason the "
                "primary source only counted an item as poisoned when the "
                "model had gotten it right without retrieval first."
            ),
        ),
        Probe(
            id="aggregate-accuracy-hides-it",
            asks=(
                "The overall accuracy of a RAG system stays flat across a "
                "release. Based on how stale-document poisoning behaves, "
                "what should you conclude about whether the system got "
                "worse at handling superseded documents?"
            ),
            choices=(
                Choice("a", "Nothing, flat aggregate accuracy rules out any regression on any slice"),
                Choice("b", "It improved, since flat accuracy under more retrieval load implies stability"),
                Choice("c", "You cannot conclude it from the aggregate: gains elsewhere can offset a real increase in stale-document flips, which is why this needs its own measurement"),
                Choice("d", "It must have worsened, since any new retrieval source increases poisoning risk by definition"),
            ),
            answer="c",
            because=(
                "Poisoning measured in the primary source ranged from 17 to "
                "91 percent, depending on model and domain. Over that same "
                "range, the model still followed matched up-to-date evidence "
                "correctly 97 to 100 percent of the time. That gap means the "
                "failure concentrates on a specific, measurable subset of "
                "questions, rather than showing up evenly. A flat or even "
                "improving aggregate can hide that subset getting worse, "
                "because unrelated gains land in the same total. The "
                "knowledge-reversal flip rate is a separate number for "
                "exactly this reason: it will not average itself away."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of 150 knowledge-reversal questions. "
            "Each question has the correct answer and what the model said "
            "with no retrieval at all. It also has what the model said when "
            "retrieval pulled a stale passage for the same question. "
            "Restrict to the questions the model answered correctly with no "
            "retrieval. Then measure how often the with-retrieval answer "
            "flipped to the stale one, and post that rate."
        ),
        fixture_path="fixtures/stale_docs/knowledge_reversals.json",
        fixture_note=(
            "Four parallel lists of 150 entries each hold the data. "
            "\"correct\" is the right answer to each question. \"stale\" is "
            "the superseded answer the retrieved passage would support. "
            "\"baseline\" is what the model answered with no retrieval. "
            "\"with_stale_retrieval\" is what the model answered when "
            "retrieval pulled the stale passage for the same question. Not "
            "every baseline answer is correct on its own: that is ordinary "
            "model error, and it is not what this exercise measures."
        ),
        starter=(
            'import json\n'
            'from app.metrics import flip_rate\n'
            '\n'
            'data = json.load(open("fixtures/stale_docs/knowledge_reversals.json"))\n'
            'correct = data["correct"]\n'
            'baseline = data["baseline"]\n'
            'with_retrieval = data["with_stale_retrieval"]\n'
            '\n'
            '# flip_rate compares two equal-length lists position by position.\n'
            '# The measurement only counts a question where the model got it\n'
            '# right with no retrieval in the first place, so narrow all three\n'
            '# lists down to those positions before you call it, then compare\n'
            '# the correct answer at each one to the with-retrieval answer at\n'
            '# the same position.\n'
        ),
        metric="flip_rate",
        expected=0.3359375,
        tolerance=0.0005,
        because=(
            "The model answered 128 of the 150 questions correctly with no "
            "retrieval at all. Of those 128, retrieval flipped 43 to the "
            "stale answer once it pulled the superseded passage, for a flip "
            "rate of 0.3359375. That sits inside the 30 to 37 percent range "
            "the primary source measured with no instruction telling the "
            "model to trust the context. This fixture models that exact "
            "condition. This fixture excludes on purpose the 22 questions "
            "the model got wrong even cold. A wrong answer there was never "
            "going to tell you anything about retrieval, since the model "
            "did not have the right answer to lose."
        ),
    ),
    sources=(
        "arXiv:2609.31342 (2026-09-25), Stale-Document Poisoning: When Outdated "
        "Retrieval Overrides Correct Model Answers, 317 knowledge reversals, "
        "30-37 percent flip rate with no instruction, 66-75 percent with an "
        "instruction to follow the context, 17-91 percent across all models "
        "and domains, 97-100 percent compliance on up-to-date evidence",
        "arXiv:2109.05052 (2021-09-10), Longpre et al., Entity-Based Knowledge "
        "Conflicts in Question Answering, on substituting a document's named "
        "entity to force a conflict between parametric and contextual "
        "knowledge, and the factors that drive over-reliance on one or the "
        "other",
    ),
)

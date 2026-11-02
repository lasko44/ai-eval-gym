"""Unit 04: A Ledger release gate that reads one run depends on how busy the
server was.

Why identical input gives different output at temperature 0, and what that
does to a threshold in continuous integration. Numbers and citations verified
against primary sources; see UNIT.sources.
"""

from app.metrics import gate_flip_rate
from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.
    """
    scores = [sum(run) / len(run) for run in data["runs"]]
    return gate_flip_rate(scores, data["threshold"])


UNIT = Unit(
    slug="release-gates",
    number=4,
    part="measurement",
    title="A Ledger release gate that reads one run depends on how busy the server was",
    failure=(
        "The gate ships or blocks a Ledger release on a score that moves between "
        "identical runs of an unchanged covenant suite."
    ),
    detection=(
        "Run the covenant suite many times with nothing changed, and measure how "
        "often "
        "the verdict, not the score, comes out the other way."
    ),
    brief=(
        "Putting the Ledger covenant eval in continuous integration feels like "
        "the moment the "
        "work becomes engineering. A number, a threshold, a build that goes "
        "red. The postings ask for it directly, and it is the right instinct. "
        "It is also where a quiet assumption gets built into your release "
        "process. The assumption is that running the same suite against the "
        "same Ledger build twice gives the same answer.",
        "It does not. Thinking Machines Lab sampled 1,000 completions at "
        "temperature 0 from a 235-billion-parameter open-weight model, 1,000 "
        "tokens each, and got 80 unique completions. The most common one "
        "appeared 78 times out of 1,000. Temperature 0 is greedy decoding, so "
        "there is no sampling to blame.",
        "The shape of the divergence is the part worth sitting with. All 1,000 "
        "completions were identical for the first 102 tokens. Every one of "
        "them produced the words \"Feynman was born on May 11, 1918, in\". "
        "Then 992 continued with \"Queens, New York\" and 8 continued with "
        "\"New York City\". One token went a different way and the texts "
        "separated from there.",
        "The cause is not randomness, which is why turning the temperature "
        "down does not help. A graphics processing unit (GPU) kernel splits a "
        "sum into chunks, and how it splits depends on the batch size. Batch "
        "size depends on how many other requests were in flight. Floating "
        "point addition is not associative, so a different split gives a "
        "different last bit. Unrelated traffic on the same server therefore "
        "moves "
        "Ledger's eval score. That is a dependency nobody wrote down "
        "and nobody can see in the diff.",
        "It is fixable and the fix has a price. With batch-invariant kernels "
        "all 1,000 completions came back identical. On an 8-billion-parameter "
        "model running 1,000 sequences of 90 to 110 output tokens, the default "
        "serving path took 26 seconds. The first deterministic version took "
        "55, and a better attention kernel brought it to 42.",
        "So a gate needs a distribution rather than a reading. Run the covenant "
        "suite "
        "unchanged enough times to see its spread, then put the threshold "
        "outside that spread. A threshold inside it is a coin weighted by "
        "server load. It blocks good Ledger releases at some rate and waves "
        "a build that misreads amendments through at some other rate. "
        "Something you are not measuring sets both "
        "rates.",
    ),
    builds_on=(
        "Unit 03. Before a release can hang on a score you need to know "
        "what the score measures. Unit 03 is where you learn part of it "
        "may be memorisation rather than skill."
    ),
    probes=(
        Probe(
            id="why-it-differs",
            asks=(
                "You ask Ledger the same covenant question twice. Same prompt, "
                "same model, temperature 0, two different answers. "
                "What is the usual cause?"
            ),
            choices=(
                Choice("a", "Leftover sampling randomness that temperature 0 misses"),
                Choice("b", "The batch size changed, so the arithmetic changed"),
                Choice("c", "The model was silently updated between calls"),
                Choice("d", "A cache returned a stale completion"),
            ),
            answer="b",
            because=(
                "Temperature 0 removes sampling entirely, so there is nothing "
                "random left to blame. Kernels split their sums differently at "
                "different batch sizes, and floating point addition is not "
                "associative. The batch size tracks how many other requests "
                "are in flight. The measured result was 80 unique completions "
                "from 1,000 identical requests."
            ),
        ),
        Probe(
            id="what-it-costs",
            asks=(
                "The determinism fix exists. Roughly what did it cost on the "
                "published benchmark?"
            ),
            choices=(
                Choice("a", "Nothing measurable, it is a correctness fix"),
                Choice("b", "Under 10 percent more wall-clock time"),
                Choice("c", "Roughly 1.5 to 2 times slower"),
                Choice("d", "More than 10 times slower, it is impractical"),
            ),
            answer="c",
            because=(
                "The same workload went from 26 seconds on the default path to "
                "55 seconds deterministic, and to 42 seconds once the attention "
                "kernel improved. That is real but affordable, which matters: "
                "it means determinism is a decision you are making, whether or "
                "not you know you are making it."
            ),
        ),
        Probe(
            id="where-to-put-it",
            asks=(
                "You rerun Ledger's unchanged covenant suite 40 times. Scores "
                "land between "
                "0.833 and 0.877. Where does the gate threshold go?"
            ),
            choices=(
                Choice("a", "At the mean, around 0.854, the best estimate"),
                Choice("b", "Below 0.833, outside the observed spread"),
                Choice("c", "At 0.85, a round number inside the range"),
                Choice("d", "At the maximum, 0.877, to hold the highest bar"),
            ),
            answer="b",
            because=(
                "Any threshold inside the spread splits identical runs into "
                "passes and failures, which is the definition of a gate reading "
                "noise. The mean is the worst choice of all, since it sits "
                "where the runs are densest and so flips most often. Putting it "
                "below the floor costs sensitivity, and buying sensitivity back "
                "means shrinking the spread, not moving the line into it."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships 40 runs of the same unchanged suite of 300 "
            "covenant questions, "
            "plus the threshold the team actually gated on. Score each run, "
            "then post the fraction of runs whose ship or block verdict "
            "contradicts what most runs decided."
        ),
        fixture_path="fixtures/release_gates/repeated_runs.json",
        fixture_note=(
            "\"runs\" holds 40 lists of 300 entries, each 1 for a correct "
            "answer and 0 for a wrong one. Every run is the same covenant suite "
            "against "
            "the same Ledger build, rescored. \"threshold\" is the number the "
            "release "
            "gate compared against."
        ),
        starter=(
            'import json\n'
            'from app.metrics import gate_flip_rate\n'
            '\n'
            'data = json.load(open("fixtures/release_gates/repeated_runs.json"))\n'
            'runs = data["runs"]\n'
            'threshold = data["threshold"]\n'
            '\n'
            'scores = [sum(run) / len(run) for run in runs]\n'
            'print("identical runs:", len(runs))\n'
            'print("covenant questions per run:", len(runs[0]))\n'
            'print("gate threshold:", threshold)\n'
            'print("lowest score :", min(scores))\n'
            'print("highest score:", max(scores))\n'
            'print("spread       :", max(scores) - min(scores))\n'
            '\n'
            '# TODO: that spread is the score moving, and it reads as tight. What\n'
            '# ships or blocks is the verdict, not the score. Decide which quantity\n'
            '# says how often these identical runs would have decided the opposite\n'
            '# of what most of them decided, and print it. gate_flip_rate will do\n'
            '# the counting once you decide what to hand it.\n'
        ),
        metric="gate_flip_rate",
        expected=0.25,
        tolerance=0.0005,
        because=(
            "Ten of the 40 runs land below the threshold and 30 above, so one "
            "run in four decides the opposite of the rest. Nothing changed "
            "between them: same covenant suite, same Ledger build, same "
            "questions. The scores "
            "themselves only span 0.833 to 0.877, a spread of 0.043, which "
            "reads as tight. Then you notice the gate was set at 0.85, right "
            "through the middle of it. The score looks stable and the decision "
            "is a coin flip, and only one of those is what ships."
        ),
    ),
    sources=(
        "thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference, 1,000 completions at temperature 0 giving 80 unique outputs, batch invariance, and the deterministic-kernel cost",
    ),
)

"""Unit 03: An eval set that leaked into training inflates every Ledger score
and still picks the right winner.

The difference between "how good is it" and "which one do we ship", and why
contamination wrecks one of those and leaves the other standing. Numbers and
citations verified against primary sources; see UNIT.sources.
"""

from app.metrics import rank_correlation
from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.
    """
    names = sorted(data["models"])
    original = [
        sum(data["models"][name]["original"]) / len(data["models"][name]["original"])
        for name in names
    ]
    paraphrased = [
        sum(data["models"][name]["paraphrased"])
        / len(data["models"][name]["paraphrased"])
        for name in names
    ]
    return rank_correlation(original, paraphrased)


UNIT = Unit(
    slug="eval-contamination",
    number=3,
    part="measurement",
    title="Contamination inflates every Ledger score and still picks the right winner",
    failure=(
        "Covenant questions from the eval set leaked into training. Every "
        "absolute Ledger score on that "
        "set is too high, and nobody can say by how much."
    ),
    detection=(
        "Ask the same covenant questions a second time in reworded form, then "
        "compare "
        "the scores and the ordering separately."
    ),
    brief=(
        "You inherit the eval set somebody built for Ledger. The numbers look "
        "good, you put one in front of the lending committee, "
        "and somebody asks whether those covenant questions leaked into "
        "training. The "
        "usual reaction is to treat the whole set as worthless and start over. "
        "That reaction throws away the half of it that still worked.",
        "A 2026 study separated the two questions people collapse into one: "
        "whether contamination inflates absolute scores, and whether it "
        "reorders the models. It used per-instance responses from 47 publicly "
        "released models, plus 74 models deliberately fine-tuned with a known "
        "dose of contamination, across four public benchmarks. The measurement "
        "is a within-item contrast: score each original item, then score a "
        "semantically equivalent paraphrase of the same item. The paraphrase "
        "tests the same skill, so what is left is memorisation.",
        "First they checked the instrument against ground truth, which is the "
        "step most people skip. It recovered the injected contamination in "
        "proportion to the dose, a corrected effect of +0.187 accuracy points "
        "for test-set leakage. It also never flagged the negative control, a "
        "model trained only on the legitimate training split, which came in at "
        "-0.012. The instrument works.",
        "Then the result that should change what you do. The rank correlation "
        "between a standard leaderboard and a paraphrase-controlled one was "
        "0.997. Analysed one benchmark at a time rather than pooled, it ran "
        "from 0.976 to 0.990, so the agreement is not an artifact of lumping "
        "them together. Out of 188 model-by-benchmark cases, 3 showed "
        "contamination that differed enough between models to matter, and only "
        "when corroborated against two independent references.",
        "The reason is that contamination among these models is largely "
        "uniform. It lifts everybody. A leaderboard is a set of differences, "
        "and a constant added to every entry changes none of them. Reordering "
        "needs differential contamination, one model having memorised more "
        "than its peers. The study's sensitivity analysis puts the amount "
        "needed at roughly 0.16 accuracy points, several times the 0.035 it "
        "actually observed at the 95th percentile.",
        "So the honest reading is narrow and worth saying out loud. If you "
        "quoted an absolute Ledger score to the lending committee, that "
        "number was wrong. If you used the same eval set to choose which "
        "Ledger build ships, that choice was probably sound. Most teams get this exactly "
        "backwards: they abandon the comparison, which survived, and keep "
        "repeating the headline number, which did not.",
    ),
    builds_on=(
        "Units 01 and 02. A grader you trust and a run you did not stop "
        "early are what it takes. Only then do you notice that the "
        "remaining problem is the eval set itself."
    ),
    probes=(
        Probe(
            id="which-claim-breaks",
            asks=(
                "You learn Ledger's eval set leaked into training. Which of your two "
                "claims took the real damage?"
            ),
            choices=(
                Choice("a", "The ranking of the three Ledger builds you compared"),
                Choice("b", "The accuracy figure you gave the lending committee"),
                Choice("c", "Both, equally"),
                Choice("d", "Neither, people overstate leakage"),
            ),
            answer="b",
            because=(
                "Contamination in the models studied was largely uniform, so it "
                "moved every score up together and left the differences between "
                "them intact. The measured rank correlation between normal and "
                "paraphrase-controlled scoring was 0.997. The absolute number is "
                "the casualty, and it is the one most people keep quoting."
            ),
        ),
        Probe(
            id="what-reorders",
            asks=(
                "What has to be true before contamination actually changes which "
                "Ledger build comes first?"
            ),
            choices=(
                Choice("a", "Enough of the covenant question set leaked, in absolute terms"),
                Choice("b", "One build memorised more of it than its rivals did"),
                Choice("c", "The question set is more than two years old"),
                Choice("d", "The builds come from different model families"),
            ),
            answer="b",
            because=(
                "Uniform contamination is a constant added to every score, and a "
                "constant cannot reorder anything. Only differential "
                "contamination moves ranks, and it was found in 3 of 188 "
                "model-by-benchmark cases. The level needed to meaningfully "
                "disturb the order was about 0.16 accuracy points against an "
                "observed 95th percentile of 0.035."
            ),
        ),
        Probe(
            id="what-to-do",
            asks=(
                "You rerun Ledger on reworded twins of every covenant question. "
                "Mean accuracy drops about 12 "
                "points and the ordering barely moves. What is the right call?"
            ),
            choices=(
                Choice("a", "Bin the covenant question set and write a new one"),
                Choice("b", "Keep the comparison, restate the absolute number"),
                Choice("c", "Report the original scores, the drop is wording noise"),
                Choice("d", "Report both numbers and let the lending committee choose"),
            ),
            answer="b",
            because=(
                "That is the exact signature of uniform contamination, which is "
                "the common case. The comparison is the part that held, so it is "
                "the part you keep. Binning the set discards working evidence, "
                "and re-reporting the inflated figure repeats the one claim the "
                "rerun just falsified. Option (d) sounds even-handed and is not. "
                "The two numbers answer different questions, so handing over both "
                "without saying which is which moves your problem to the committee."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships 12 Ledger builds scored on 200 covenant questions, "
            "each question paired with "
            "a reworded twin. Work out each build's accuracy under both "
            "scorings, rank the builds under each, and post the rank correlation "
            "between the two orderings."
        ),
        fixture_path="fixtures/eval_contamination/paraphrase_pairs.json",
        fixture_note=(
            "Twelve Ledger builds under \"models\". Each holds two lists of 200 "
            "entries, \"original\" and \"paraphrased\", scored 1 for a correct "
            "answer and 0 for a wrong one. Position i is the same covenant "
            "question in both lists. It appears once in the wording the eval "
            "set shipped with and once "
            "in a reworded form that turns on the same clause."
        ),
        starter=(
            'import json\n'
            'from app.metrics import rank_correlation\n'
            '\n'
            'data = json.load(open("fixtures/eval_contamination/paraphrase_pairs.json"))\n'
            'names = sorted(data["models"])\n'
            '\n'
            '# rank_correlation takes two scores-per-candidate lists, aligned by\n'
            '# position. Turn the per-item 1s and 0s into one accuracy per model\n'
            '# first, and keep both lists in the same model order.\n'
            '# Then look at the two means as well, and notice they disagree with\n'
            '# the correlation about how bad the problem is.\n'
        ),
        metric="rank_correlation",
        expected=0.993007,
        tolerance=0.0005,
        because=(
            "The rank correlation is 0.993, and only 2 of the 12 builds move at "
            "all. Meanwhile mean accuracy falls from 0.690 to 0.574, an "
            "inflation of 0.116, which is close to the +0.187 the study "
            "recovered from deliberately dosed models. Both numbers come from "
            "the same 2,400 gradings. One of them says the covenant question "
            "set is badly "
            "compromised, and the other says your choice of which Ledger "
            "build to ship stands. "
            "They are both right, because they are answers to different "
            "questions."
        ),
    ),
    sources=(
        "arXiv:2609.02899v1 (2026-07-05), Xiao and Cheng, 47 public models and 74 dosed models over four benchmarks, paraphrase-controlled leaderboards",
    ),
)

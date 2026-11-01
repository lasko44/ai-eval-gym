"""Unit 21: the fairness metrics on Ledger's decisions cannot all hold at once.

Demographic parity, equalized odds and calibration within groups, applied to
the credit decisions Ledger's answers feed, and the proof that a model cannot
satisfy all three when the compared groups have different base rates. Numbers
and citations verified against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: list) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.

    This fixture's parsed form is a flat list of records rather than a mapping,
    so `data` is that list.
    """
    threshold = 0.5

    def error_rates(group: list) -> tuple[float, float]:
        positives = [r for r in group if r["label"] == 1]
        negatives = [r for r in group if r["label"] == 0]
        false_positives = sum(1 for r in negatives if r["score"] >= threshold)
        false_negatives = sum(1 for r in positives if r["score"] < threshold)
        return false_positives / len(negatives), false_negatives / len(positives)

    a_fpr, a_fnr = error_rates([r for r in data if r["group"] == "group_a"])
    b_fpr, b_fnr = error_rates([r for r in data if r["group"] == "group_b"])
    return max(abs(a_fpr - b_fpr), abs(a_fnr - b_fnr))


UNIT = Unit(
    slug="fairness-metrics",
    number=21,
    part="governance",
    title="The fairness metrics on Ledger's decisions cannot all hold at once",
    failure=(
        "The credit model Ledger feeds passes the fairness metric the team "
        "happens to pick. An examiner picks a different metric, and the same "
        "model fails. Both measurements are correct, and the model never "
        "changed."
    ),
    detection=(
        "Compute demographic parity, equalized odds and calibration within "
        "groups on the same borrower predictions. Report the gap each one "
        "shows, every time, next to the others."
    ),
    brief=(
        "Ledger's answers feed credit decisions, so the lender has to show "
        "that the model behind those decisions treats two groups of "
        "borrowers fairly. Someone picks a fairness metric, runs it "
        "against the model, and the model passes. A second reviewer picks "
        "a different metric, runs it against the same model, and the model "
        "fails. Neither reviewer made an error. The two metrics measure "
        "different properties of the model. When the two groups have "
        "different base rates, several common fairness metrics cannot all "
        "hold true for the same model.",
        "Demographic parity asks a simple question. Does the model "
        "approve the same share of borrowers in each group? It compares "
        "the selection rate, the fraction of each group that crosses the "
        "decision line. It calls the model fair when that share is equal "
        "across groups. It says nothing about whether the model approved "
        "the right borrowers in either group. A model can hit demographic "
        "parity exactly "
        "while making far more mistakes in one group than the other.",
        "Equalized odds asks a different question. Among the borrowers "
        "who will actually perform, does the model approve them at the "
        "same rate in each group? Among the borrowers who will actually "
        "default, does the model decline them at the same rate in each "
        "group? Formally this means equal false positive rates across "
        "groups, and equal false negative rates across groups. "
        "Chouldechova calls this error rate balance, and later work calls "
        "it equalized odds.",
        "Calibration within groups asks a third question. Among the "
        "borrowers the model scores at, say, seventy percent, does "
        "seventy percent of each group actually perform? A well calibrated "
        "score means the same thing in both groups. A given number from "
        "the model carries the same real-world likelihood wherever it is "
        "read. Chouldechova's definition states the probability of the "
        "true outcome, given the score and given the group, is the same "
        "for every value of the score. A model can be well calibrated in "
        "each group and still fail both of the other two tests.",
        "Kleinberg, Mullainathan and Raghavan studied exactly this "
        "conflict in a widely cited paper. They define calibration within "
        "groups the same way Chouldechova does. They add two further "
        "conditions they call balance for the negative class and balance "
        "for the positive class. Balance for the negative class requires "
        "that people who will not default receive the same average score "
        "in both groups. Balance for the positive class requires the same "
        "thing for the people who will default. Together these two "
        "conditions generalize the idea of equal error rates across "
        "groups.",
        "Their main result is a theorem, not an opinion. A risk "
        "assignment can satisfy calibration and both balance conditions "
        "at the same time only in two narrow cases. The first is perfect "
        "prediction, where the model already knows the true outcome for "
        "everyone. The second is equal base rates, where both groups "
        "share exactly the same underlying rate of the outcome in "
        "question.",
        "Outside those two cases, every risk assignment "
        "violates at least one of the three conditions. This holds no "
        "matter what method built the risk assignment. It can be a human "
        "underwriter, a scorecard, a machine learning model, or an "
        "underwriter acting on what Ledger told them the covenants say.",
        "Chouldechova ran the same analysis on real data from the COMPAS "
        "(Correctional Offender Management Profiling for Alternative "
        "Sanctions) recidivism tool, the data ProPublica made public. Her "
        "dataset held 6,150 defendants, 3,696 of one race and 2,454 of "
        "another. She found the COMPAS score met the calibration test "
        "within each group. She also found it met predictive parity, "
        "equal accuracy among people flagged high risk, at every "
        "threshold of four or above. At those same thresholds, the false "
        "positive rate and the false negative rate differed sharply "
        "between the two groups. The two groups did not share the same "
        "base rate of the outcome, so calibration and equal error rates "
        "could not both hold.",
        "None of this makes COMPAS, or Ledger, or any other model, "
        "dishonest. It tells you that the three fairness tests encode "
        "different values, and a model cannot satisfy all three unless the "
        "underlying population cooperates.",
        "Your job as the engineer is "
        "not to search for the one metric Ledger happens to pass. "
        "State which definition the lender must meet, before you run any "
        "numbers. Then compute the other two anyway, and report the gap "
        "each one shows. Put all three next to each other, and let "
        "someone accountable for the credit decision choose the tradeoff "
        "on purpose instead of by accident. An examiner who arrives later "
        "will pick the metric, and they will not pick yours.",
    ),
    builds_on=(
        "Units 01 and 20. A fairness metric is a grader somebody chose, so "
        "it carries the same selection problem as the judge in unit 01 and "
        "the filter in unit 20."
    ),
    probes=(
        Probe(
            id="passes-one-metric",
            asks=(
                "The credit model Ledger feeds hits exact calibration "
                "within each of two borrower groups. Reviewer A calls it "
                "fair. What has this established about equalized odds and "
                "demographic parity?"
            ),
            choices=(
                Choice(
                    "a",
                    "Nothing about either one, since calibration does not "
                    "guarantee equal selection rates or equal error rates "
                    "across groups",
                ),
                Choice(
                    "b",
                    "That the model is fully fair, since a passing metric "
                    "proves every other metric also passes",
                ),
                Choice(
                    "c",
                    "That equalized odds also holds, since a calibrated "
                    "score must automatically equalize error rates",
                ),
                Choice(
                    "d",
                    "That demographic parity must fail, since calibration "
                    "and demographic parity can never hold together",
                ),
            ),
            answer="a",
            because=(
                "Calibration within groups is a claim about accuracy "
                "conditional on the score, not about overall approval "
                "shares or error rates. It says the score means the same "
                "thing in each group. Demographic parity and equalized "
                "odds measure different properties, the share of each "
                "borrower group approved and the error rates within each "
                "group. "
                "Kleinberg, Mullainathan and Raghavan proved all three "
                "conditions can coexist only with perfect prediction or "
                "with equal base rates between groups. Passing one test "
                "alone buys you nothing about the other two in the "
                "general case."
            ),
        ),
        Probe(
            id="when-all-three-hold",
            asks=(
                "A single model sits behind the lender's decisions. Under "
                "what condition can demographic parity, equalized "
                "odds and calibration within groups all hold at once for "
                "that model?"
            ),
            choices=(
                Choice(
                    "a",
                    "Only when the model gets complex enough, since more "
                    "features always resolve the conflict",
                ),
                Choice(
                    "b",
                    "Only when the two borrower groups share the same base "
                    "rate, or the model predicts every outcome perfectly",
                ),
                Choice(
                    "c",
                    "Always, as long as the model trains on enough deals "
                    "from both groups",
                ),
                Choice(
                    "d",
                    "Never, the three conditions are opposite in every "
                    "possible case",
                ),
            ),
            answer="b",
            because=(
                "Kleinberg, Mullainathan and Raghavan's Theorem 1.1 names "
                "exactly two cases where all three conditions hold "
                "together. The first is perfect prediction, where the "
                "model already knows the true outcome for everyone and "
                "assigns a score of zero or one. The second is equal base "
                "rates, where the two borrower groups share the same "
                "underlying rate of the outcome. Outside those two narrow cases, "
                "every risk assignment must violate at least one of the "
                "three conditions. More data or a better model does not "
                "escape this, since the theorem holds for any method that "
                "produces a risk assignment."
            ),
        ),
        Probe(
            id="both-correct",
            asks=(
                "The lender's team and an examiner compute two different "
                "fairness metrics on the same unchanged model and reach "
                "opposite conclusions about whether it is fair. Both "
                "computations are correct. What does this mean for the "
                "engineer evaluating the system?"
            ),
            choices=(
                Choice(
                    "a",
                    "One of them made an arithmetic error, since two "
                    "correct metrics cannot disagree",
                ),
                Choice(
                    "b",
                    "Fairness metrics encode different values and can "
                    "conflict by design. The engineer must name the "
                    "standard the lender follows, and report the rest as "
                    "a measured tradeoff",
                ),
                Choice(
                    "c",
                    "The model needs retraining, since a fair model "
                    "cannot fail any fairness metric",
                ),
                Choice(
                    "d",
                    "The examiner is wrong, since demographic parity "
                    "is the only fairness metric that matters in lending",
                ),
            ),
            answer="b",
            because=(
                "Demographic parity, equalized odds and calibration "
                "within groups are three different mathematical claims. "
                "A model can satisfy any one of them while failing the "
                "other two. That is especially true when the two borrower "
                "groups in the comparison have different base rates. Neither side "
                "made an error, and neither metric is the single correct "
                "one. The engineer's job is to pick, in advance and out "
                "loud, which definition the lender must meet. Then the "
                "engineer measures and reports the other two as the cost "
                "of that choice."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships 2000 predictions from the credit model "
            "Ledger feeds, split between two borrower groups with "
            "different base rates. Each row carries a score "
            "from zero to one and a true outcome label. Compute "
            "demographic parity, equalized odds and calibration within "
            "groups for both groups, using a decision threshold of 0.5. "
            "Post the equalized odds gap: the larger of the false "
            "positive rate gap and the false negative rate gap between "
            "the two groups."
        ),
        fixture_path="fixtures/fairness_metrics/model_predictions.json",
        fixture_note=(
            "A flat list of 2000 borrower records. Each record has a "
            "group field, group_a or group_b. It also has a score between "
            "zero and one, and a true outcome label of zero or one. The "
            "two groups have different base rates, group_a lower and "
            "group_b higher. Use 0.5 as the decision threshold. A score "
            "at or above 0.5 counts as a positive prediction."
        ),
        starter=(
            'import json\n'
            '\n'
            'records = json.load(open("fixtures/fairness_metrics/model_predictions.json"))\n'
            'group_a = [r for r in records if r["group"] == "group_a"]\n'
            'group_b = [r for r in records if r["group"] == "group_b"]\n'
            '\n'
            'threshold = 0.5\n'
            '\n'
            'def rates(group):\n'
            '    pred_pos = sum(1 for r in group if r["score"] >= threshold)\n'
            '    tp = sum(1 for r in group if r["score"] >= threshold and r["label"] == 1)\n'
            '    fn = sum(1 for r in group if r["score"] < threshold and r["label"] == 1)\n'
            '    fp = sum(1 for r in group if r["score"] >= threshold and r["label"] == 0)\n'
            '    tn = sum(1 for r in group if r["score"] < threshold and r["label"] == 0)\n'
            '    return {\n'
            '        "demographic_parity": pred_pos / len(group),\n'
            '        "fpr": fp / (fp + tn),\n'
            '        "fnr": fn / (fn + tp),\n'
            '    }\n'
            '\n'
            'a = rates(group_a)\n'
            'b = rates(group_b)\n'
            'print("group_a:", a)\n'
            'print("group_b:", b)\n'
            'print("demographic_parity_gap:", abs(a["demographic_parity"] - b["demographic_parity"]))\n'
            '\n'
            '# Calibration within groups: for every score that appears in the\n'
            '# fixture, does the fraction of positive labels at that score match\n'
            '# between group_a and group_b? Check every score, not just one.\n'
            '\n'
            '# Your job: the number to post is the equalized odds gap, the\n'
            '# larger of the false positive rate gap and the false negative\n'
            '# rate gap between group_a and group_b.\n'
            '# equalized_odds_gap = ?\n'
        ),
        metric="equalized_odds_gap",
        expected=0.462335,
        tolerance=0.0005,
        because=(
            "The model is well calibrated, the same fraction of each "
            "group shows the positive outcome within every score bucket, "
            "so the calibration gap is zero. Demographic parity still "
            "fails by a wide margin, a gap of 0.55, since group_a and "
            "group_b enter with very different base rates. Equalized "
            "odds fails too, and the false negative rate gap, about "
            "0.4623, is the number this exercise asks you to post. This "
            "is exactly what Kleinberg, Mullainathan and Raghavan "
            "proved. Outside perfect prediction or equal base rates, "
            "calibration, demographic parity and equalized odds cannot "
            "all hold together, and this fixture hits neither escape "
            "case. The lender has to name which one of the three the "
            "decisions Ledger feeds are held to, and report the other two "
            "as the price."
        ),
    ),
    sources=(
        "arXiv:1609.05807 (2016-11-17v2), Kleinberg, Mullainathan and "
        "Raghavan, Theorem 1.1: calibration within groups, balance for "
        "the negative class and balance for the positive class cannot "
        "all hold except with perfect prediction or equal base rates",
        "arXiv:1703.00056 (2017-02-28), Chouldechova, predictive parity "
        "and error rate balance are mutually exclusive when base rates "
        "differ, worked on the ProPublica COMPAS data, n=6150, 3696 "
        "African-American and 2454 Caucasian defendants",
    ),
)

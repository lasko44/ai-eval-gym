"""Unit 07: a uniform Ledger eval set holds none of the failure it exists to
catch.

Why 200 cases drawn at random from production can look representative and
still contain zero instances of the rare failure that costs money. Numbers and
citations verified against primary sources, see UNIT.sources. The one piece of
arithmetic in the briefing is derived in the briefing rather than cited,
because a probability of missing a class is a calculation and not a finding.

The measurement is inline rather than in app/metrics, because it is one rate
and one exponent, and it reads better beside the thing it teaches.
"""

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.

    The fixture parses to a dict. "requests" is the raw quarter of traffic,
    one record per underwriter question, each with a "category" and an
    "outcome". "planned_sample_size" is the size of set the team drew. The
    rate comes from the full traffic, and the exponent is the planned size,
    which treats the 200 cases as independent draws at that rate.
    """
    requests = data["requests"]
    planned = data["planned_sample_size"]
    expensive = sum(1 for record in requests if record["outcome"] == "missed_breach")
    rate = expensive / len(requests)
    return (1.0 - rate) ** planned


UNIT = Unit(
    slug="sampling",
    number=7,
    part="measurement",
    title="A uniform Ledger eval set holds none of the failure it exists to catch",
    failure=(
        "Somebody drew 200 Ledger questions at random from a quarter of "
        "traffic. The set matches production on every count anybody checked, "
        "and the failure that costs money appears in it zero times."
    ),
    detection=(
        "Measure the rate of the expensive failure in the raw traffic, before "
        "anybody samples it. Then work out the chance that a draw of the "
        "planned size contains none of it."
    ),
    brief=(
        "The posting asks for eval dataset design, so at some point you draw a "
        "set out of raw traffic. A uniform draw feels like the honest default. "
        "It carries no opinion about what matters, it matches the mix "
        "underwriters actually ask, and it gives an unbiased estimate of the "
        "overall score. All three of those claims hold. None of them says the "
        "set can see the failure you are afraid of.",
        "Production failures arrive in a long tail, and somebody has counted "
        "one. Microsoft collected hundreds of thousands of incidents across "
        "its generative cloud services from June 2020 to February 2024. It "
        "then classified the high severity ones, the incidents that carried a "
        "full root cause analysis. Degraded performance accounted for 49.8 "
        "percent of those, and deployment failure for 35.7 percent. Invalid "
        "inference, where the service "
        "returns an answer with no error and the answer is wrong, accounted "
        "for 14.5 percent. Inside that, a content filter malfunction was 3.8 "
        "percent of incidents, and a bug in the filter code was 2.2 percent "
        "of all root causes.",
        "The thin end of that tail is not the cheap end. In the same study, "
        "humans rather than monitors reported 38.3 percent of these "
        "incidents, against 13.7 percent for the rest of the cloud. The "
        "monitors that did fire carried an 11.0 percent false alarm rate, "
        "against 3.8 percent elsewhere. Time to mitigate ran 1.83 times "
        "longer, and a quick fix closed only 22.4 percent of them, against "
        "54.7 percent elsewhere. A class your instruments cannot see is the "
        "one that stays open longest.",
        "Now the arithmetic, which is a calculation rather than a citation. "
        "Treat each case you draw as an independent draw that hits the class "
        "at rate p. One case misses it with probability 1 minus p, so n cases "
        "all miss it with probability (1 minus p) to the power n. Put one "
        "request in 250 into the class, so p is 0.004, and draw 200 cases. "
        "The natural logarithm of 0.996 is minus 0.004008, times 200 is minus "
        "0.8016, and the exponential of that is 0.449. Close to half of all "
        "such sets contain none of the class, and the expected count in a set "
        "is 0.8.",
        "Sample size cannot rescue that cheaply, and the variance says why. "
        "Marchant and Rubinstein work out what a uniform draw buys for two "
        "measures. For accuracy, the variance of the estimate falls as the "
        "quantity accuracy times one minus accuracy, over the number of "
        "labels. For recall on a rare class, the same expression divides by "
        "the number of labels times epsilon, the frequency of that class. The "
        "labels you need therefore scale as one over epsilon. Their own "
        "example is a class at one in a million, which needs a million labels "
        "in expectation before one instance turns up.",
        "Stratify instead, and expect the gain to depend on the strata. "
        "Fogliato and colleagues compared survey designs for estimating the "
        "accuracy of an image classifier. Stratified random sampling with "
        "proportional allocation beat simple random sampling on mean squared "
        "error whatever they stratified on. The annotation saving was about "
        "10 times on one task, about 5 times on a second, and nothing at all "
        "on a third. So the strata have to track the thing you intend to "
        "measure, and a stratum nobody draws from buys nothing.",
        "That leaves the judgment, and it is a question about purpose rather "
        "than method. A representative set answers what Ledger scores on "
        "traffic like this quarter. A useful set answers whether Ledger still "
        "misses a breach a waiver buried. One set does both jobs badly, so "
        "decide which one you are drawing for, write it down, and keep the "
        "other set beside it. The set you hand a stakeholder and the set that "
        "gates a release were never the same set.",
    ),
    builds_on=(
        "Units 05 and 06. Unit 05 sized a set so a real effect could clear "
        "the noise, and unit 06 kept new cases arriving from live traffic. "
        "Both of them assume somebody already chose which cases to draw. That "
        "choice is this unit, and it decides what the set can see at all."
    ),
    probes=(
        Probe(
            id="chance-of-a-blind-set",
            asks=(
                "One Ledger request in 250 lands in the failure class that "
                "costs money. You draw 200 cases uniformly at random. What is "
                "the chance the set contains none of that class?"
            ),
            choices=(
                Choice("a", "About 1 percent, because 200 cases is a real sample"),
                Choice("b", "About 20 percent"),
                Choice("c", "About 45 percent"),
                Choice("d", "About 80 percent, because the class is rare"),
            ),
            answer="c",
            because=(
                "A rate of one in 250 makes p 0.004, and each draw misses the "
                "class with probability 0.996. Two hundred draws all miss it "
                "with probability 0.996 to the power 200. The natural "
                "logarithm of 0.996 is minus 0.004008, times 200 is minus "
                "0.8016, and the exponential of that is 0.449. The expected "
                "count in the set is 0.8 cases, which is the number that "
                "misleads people. An average of 0.8 and a coin flip on "
                "whether the set holds any at all are the same fact."
            ),
        ),
        Probe(
            id="what-uniform-buys",
            asks=(
                "You draw labels uniformly and report two numbers from one "
                "set: overall accuracy, and recall on a class at one in a "
                "thousand requests. How do the label counts compare for the "
                "same precision?"
            ),
            choices=(
                Choice("a", "The same, since both come from one set"),
                Choice(
                    "b",
                    "Recall needs roughly 10 times more labels than accuracy",
                ),
                Choice(
                    "c",
                    "Recall needs roughly 1,000 times more labels than accuracy",
                ),
                Choice(
                    "d",
                    "Recall needs fewer labels, because it ignores the common "
                    "cases",
                ),
            ),
            answer="c",
            because=(
                "Marchant and Rubinstein give both variances for a uniform "
                "draw. Accuracy falls as accuracy times one minus accuracy, "
                "over the number of labels. Recall divides the same "
                "expression by the number of labels times epsilon, the "
                "frequency of the class. So the label count scales as one "
                "over epsilon, which is 1,000 here. That is why they call "
                "uniform sampling impractical under extreme imbalance. A set "
                "drawn for the headline number cannot also carry the rare one."
            ),
        ),
        Probe(
            id="two-jobs-one-set",
            asks=(
                "You need the headline accuracy number for a stakeholder, and "
                "a set that can catch a missed covenant breach. What do you "
                "ship?"
            ),
            choices=(
                Choice(
                    "a",
                    "One uniform set, drawn large enough to cover the rare "
                    "class",
                ),
                Choice(
                    "b",
                    "Two sets: a uniform one for the headline, and one "
                    "stratified toward the rare class for the gate",
                ),
                Choice(
                    "c",
                    "One set with the rare class oversampled, reported as a "
                    "plain average",
                ),
                Choice(
                    "d",
                    "One uniform set now, and revisit it when more traffic "
                    "arrives",
                ),
            ),
            answer="b",
            because=(
                "Each set answers one question well, and growing the uniform "
                "set costs more than anybody will pay. At one in 250, a 95 "
                "percent chance of one case takes 748 cases. That count is "
                "the natural logarithm of 0.05 over the natural logarithm of "
                "0.996, which is 747.4, rounded up. Oversampling inside one "
                "set and "
                "then reporting a plain average breaks the headline instead, "
                "since the average no longer describes production. Waiting "
                "for traffic leaves the gate blind in the meantime. Two sets, "
                "each honest about its own job, is the cheap answer."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a quarter of raw Ledger traffic. It holds 7200 "
            "underwriter questions with the category and the outcome of each, "
            "and the 200 request ids the team drew uniformly from it. Measure "
            "the rate of the expensive failure across the whole quarter. Then "
            "report the chance that a uniform draw of the planned size "
            "contains none of it. Treat the 200 cases as independent draws at "
            "the rate you measured."
        ),
        fixture_path="fixtures/sampling/raw_traffic.json",
        fixture_note=(
            "\"requests\" holds 7200 Ledger requests in arrival order, with "
            "nothing sampled or filtered out. Each one carries a question "
            "\"category\" and an \"outcome\". An \"ok\" outcome is a correct "
            "answer, and a \"wrong_but_flagged\" outcome is a wrong answer "
            "Ledger marked as low confidence. A \"missed_breach\" outcome is "
            "a confidently wrong answer that permits a distribution the "
            "amendments forbid. \"uniform_sample\" holds the 200 request ids "
            "the team drew uniformly, and \"planned_sample_size\" is the size "
            "they planned for. Every category and every outcome comes from a "
            "generator seeded with the value in the file."
        ),
        starter=(
            'import json\n'
            'from collections import Counter\n'
            '\n'
            'data = json.load(open("fixtures/sampling/raw_traffic.json"))\n'
            'requests = data["requests"]\n'
            'planned = data["planned_sample_size"]\n'
            'drawn = data["uniform_sample"]\n'
            'by_id = {record["id"]: record for record in requests}\n'
            '\n'
            'print("requests in the quarter:", len(requests))\n'
            'print("outcomes across the quarter:",\n'
            '      dict(Counter(record["outcome"] for record in requests)))\n'
            '\n'
            'per_category = Counter(record["category"] for record in requests)\n'
            'for name, count in per_category.most_common():\n'
            '    ok = sum(1 for record in requests\n'
            '             if record["category"] == name and record["outcome"] == "ok")\n'
            '    print("  ", name, "| requests:", count,\n'
            '          "| share of traffic:", round(count / len(requests), 4),\n'
            '          "| correct:", round(ok / count, 4))\n'
            '\n'
            'drawn_outcomes = Counter(by_id[one]["outcome"] for one in drawn)\n'
            'print("planned set size:", planned, "| ids drawn:", len(drawn))\n'
            'print("outcomes in the drawn set:", dict(drawn_outcomes))\n'
            'print("accuracy in the drawn set:",\n'
            '      round(drawn_outcomes["ok"] / len(drawn), 4))\n'
            'print("accuracy across the quarter:",\n'
            '      round(sum(1 for r in requests if r["outcome"] == "ok")\n'
            '            / len(requests), 4))\n'
            'print("missed breaches in the drawn set:",\n'
            '      drawn_outcomes["missed_breach"])\n'
            '\n'
            '# TODO: the drawn set matches the quarter on accuracy to within a\n'
            '# fifth of a point, and it holds none of the one outcome anybody\n'
            '# would lose money over. Decide whether that set was unlucky or\n'
            '# typical, which means deciding what to measure: pick the outcome\n'
            '# class the set exists to catch, measure its rate in the full\n'
            '# quarter rather than in the set, and report the chance that a\n'
            '# uniform draw of the planned size shows none of it.\n'
        ),
        metric="rare_class_miss_probability",
        expected=0.573310,
        tolerance=0.0005,
        because=(
            "Twenty of the 7200 requests are a missed breach, a rate of "
            "0.002778. Each draw misses that class with probability 0.997222, "
            "and 200 independent draws all miss it with probability 0.5733. "
            "So the set was not unlucky, it was the common case, and it also "
            "looked fine at 0.915 accuracy against 0.91375. Category coverage "
            "would not have saved it either. The draw held 1 waiver "
            "supersession and 3 intercreditor override requests, the two "
            "categories that carry every missed breach, and none of those 4 "
            "failed that way. Drawing without replacement from the quarter "
            "gives 0.5688 rather than 0.5733, which changes no decision."
        ),
    ),
    sources=(
        "arXiv:2504.08865v2 (2025-08-14), Yan, Chen, Ma, Wen, Lu, Zhang, Xu, Wang, Bansal, Rajmohan, Lin, Zhang and Zhang, An Empirical Study of Production Incidents in Generative AI Cloud Services, fetched 2026-11-01: hundreds of thousands of generative-service incidents at Microsoft collected from June 2020 to February 2024, of which Section 3 takes the high severity subset carrying a root cause analysis for the detailed classification. Section 5 gives the symptom split of that subset as degraded performance 49.8 percent, deployment failure 35.7 percent and invalid inference 14.5 percent, with response quality degradation at 10.7 percent and content filter malfunction at 3.8 percent inside it. Section 6 gives the root cause of content filter bugs at 2.2 percent. Table 1 gives human-reported detection at 38.3 percent against 13.7 percent for other services and monitor false alarm rates of 11.0 against 3.8 percent, a time to mitigate 1.83 times longer, and ad hoc fixes closing 22.4 percent against 54.7 percent elsewhere",
        "arXiv:2006.06963v2 (2021-06-02), Marchant and Rubinstein, Needle in a Haystack: Label-Efficient Evaluation under Extreme Class Imbalance, fetched 2026-11-01: Example 2 and Example 3 of Section 2.3 derive the variance of the passive (uniform) estimator as the measure times one minus the measure over the label count for accuracy, and the same expression divided by the label count times epsilon for recall, where epsilon is the relative frequency of the positive class, so the labels needed scale as one over epsilon. Section 1 states 1 minority instance to every 1 million or more majority instances, and a million labels in expectation before one minority instance appears. Table 3 lists 7 test pools from 20,000 to 676,267 instances, and Section 5.3 reports passive and stratified sampling at least one order of magnitude worse in mean squared error than the biased methods on one of them, over 1000 repeats",
        "Fogliato, Patil, Monfort and Perona (Amazon Web Services and California Institute of Technology), A Framework for Efficient Model Evaluation through Stratification, Sampling, and Estimation, European Conference on Computer Vision 2024, fetched 2026-11-01 from ecva.net/papers/eccv_2024/papers_ECCV/papers/12117.pdf: Figure 1 measures the annotation saving of stratified sampling over simple random sampling at about 10 times on one classification task, about 5 times on a second and none on a third, and Proposition 1 with Figure 2 report stratified random sampling with proportional allocation at lower mean squared error than simple random sampling whatever the stratification features, with relative efficiency ranging from about 10 times to no gain",
    ),
)

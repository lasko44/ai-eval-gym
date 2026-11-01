import math

import pytest

from app.metrics import (
    brier_score,
    flip_rate,
    gate_flip_rate,
    minimum_detectable_effect,
    ndcg_at_k,
    precision_at_k,
    rank_correlation,
    recall_at_k,
)


# --- recall_at_k ---
# Fraction of the TRUE relevant set that shows up in the first k retrieved
# items. The denominator is always the full count of relevant documents,
# never clamped to k, because recall answers "how much of what matters did
# we find", and that question does not get easier just because k is small.

def test_recall_at_k_counts_only_the_first_k():
    assert recall_at_k(["a", "b", "c"], {"a", "c"}, k=2) == 0.5


def test_recall_at_k_with_no_relevant_documents_is_zero_not_nan():
    assert recall_at_k(["a"], set(), k=1) == 0.0


def test_recall_at_k_with_k_larger_than_retrieved_uses_what_was_retrieved():
    # Only one document was ever retrieved, so asking for k=5 can only ever
    # look at that one document. It is relevant, so recall is complete.
    assert recall_at_k(["a"], {"a", "b"}, k=5) == 0.5


def test_recall_at_k_with_k_zero_or_negative_is_zero():
    assert recall_at_k(["a", "b"], {"a"}, k=0) == 0.0
    assert recall_at_k(["a", "b"], {"a"}, k=-1) == 0.0


# --- precision_at_k ---
# Fraction of what was actually examined (the first k retrieved items, or
# fewer if the retriever returned fewer than k) that turned out relevant.
# Precision answers "how much of what we looked at was good", so the
# denominator is what was actually looked at, not the k the caller asked
# for.

def test_precision_at_k_counts_only_the_first_k():
    # "c" is relevant but sits outside the first two retrieved, so it
    # cannot count toward precision over those first two.
    assert precision_at_k(["a", "b", "c"], {"c"}, k=2) == 0.0


def test_precision_at_k_with_no_relevant_documents_is_zero_not_nan():
    assert precision_at_k(["a"], set(), k=1) == 0.0


def test_precision_at_k_with_k_larger_than_retrieved_divides_by_what_was_retrieved():
    # Only one document exists to look at, so precision is computed over
    # that one document, not diluted by the unfilled k=5 slots.
    assert precision_at_k(["a"], {"a"}, k=5) == 1.0


def test_precision_at_k_with_k_zero_or_negative_is_zero():
    assert precision_at_k(["a", "b"], {"a"}, k=0) == 0.0
    assert precision_at_k(["a", "b"], {"a"}, k=-1) == 0.0


# --- ndcg_at_k ---
# Graded, position-discounted retrieval quality, normalized against the
# best achievable ordering of the relevance grades on hand. A log2(rank + 1)
# discount is applied with rank counted from 1 (the first retrieved item),
# so the top-ranked item gets discount log2(2) == 1, i.e. no discount at
# all, and the discount grows with every position after that.

def test_ndcg_at_k_of_the_ideal_ordering_is_one():
    # Retrieved order already matches descending relevance order, so the
    # achieved DCG equals the best-possible (ideal) DCG exactly.
    assert ndcg_at_k(["a", "b", "c"], {"a": 3, "b": 2, "c": 1}, k=3) == pytest.approx(1.0)


def test_ndcg_at_k_of_the_worst_binary_ordering_is_zero():
    # The one relevant document ("a") is retrieved second, but k=1 only
    # looks at the first slot, which holds the irrelevant document.
    assert ndcg_at_k(["b", "a"], {"a": 1, "b": 0}, k=1) == 0.0


def test_ndcg_at_k_with_no_relevance_grades_is_zero_not_nan():
    assert ndcg_at_k(["a"], {}, k=1) == 0.0


def test_ndcg_at_k_with_k_zero_or_negative_is_zero():
    assert ndcg_at_k(["a", "b"], {"a": 1, "b": 1}, k=0) == 0.0
    assert ndcg_at_k(["a", "b"], {"a": 1, "b": 1}, k=-1) == 0.0


def test_ndcg_at_k_gives_partial_credit_for_a_merely_good_ordering():
    # The boundary cases above (ideal order == 1.0, worst binary order ==
    # 0.0) are both invariant to a whole class of discount-formula bugs:
    # swapping log2(rank + 1) for log2(rank + 2) consistently in DCG and
    # IDCG still yields 1.0 and 0.0 in those two cases. This case pins the
    # actual discount convention with a value that is not a boundary.
    #
    # Expected value is derived directly from the DCG/IDCG definition
    # below (not by calling ndcg_at_k and reading off its answer).
    # Retrieved order is b, a, c with relevance b=2, a=3, c=1:
    #   DCG  = 2/log2(2) + 3/log2(3) + 1/log2(4)
    # The ideal order is a, b, c (relevance 3, 2, 1):
    #   IDCG = 3/log2(2) + 2/log2(3) + 1/log2(4)
    # DCG = 2 + 1.892789... + 0.5 = 4.392789...
    # IDCG = 3 + 1.261860... + 0.5 = 4.761860...
    # NDCG = DCG / IDCG, approximately 0.922495.
    dcg = 2 / math.log2(2) + 3 / math.log2(3) + 1 / math.log2(4)
    idcg = 3 / math.log2(2) + 2 / math.log2(3) + 1 / math.log2(4)
    expected = dcg / idcg

    assert ndcg_at_k(["b", "a", "c"], {"a": 3, "b": 2, "c": 1}, k=3) == pytest.approx(expected)


def test_ndcg_at_k_ignores_relevance_grades_outside_the_cutoff():
    # len(relevance) == 3 but k == 2, so the ideal normalizer must be built
    # from only the top 2 grades (10 and 1, a tie between "a" and "b"), not
    # all 3. Retrieved is already in that ideal top-2 order, so a correctly
    # truncated IDCG equals DCG exactly and NDCG == 1.0. A bug that
    # normalized against all 3 grades instead of the top k would inflate
    # IDCG (adding a 1/log2(4) term that does not belong) and push this
    # below 1.0, which pytest.approx(1.0) would catch.
    assert ndcg_at_k(["c", "a", "b"], {"a": 1, "b": 1, "c": 10}, k=2) == pytest.approx(1.0)


# --- brier_score ---
# Mean squared error between a stated probability and the binary outcome
# (1.0 if it happened, 0.0 if it did not). 0.0 is perfect calibration, 1.0
# is maximally wrong and maximally confident.

def test_brier_score_of_a_confident_correct_call_is_zero():
    assert brier_score([(1.0, True)]) == 0.0


def test_brier_score_of_a_confident_wrong_call_is_one():
    assert brier_score([(1.0, False)]) == 1.0


def test_brier_score_of_an_empty_list_raises():
    # 0.0 would read as "perfectly calibrated", which is the one answer
    # that must never be given when nothing was actually predicted.
    with pytest.raises(ValueError):
        brier_score([])


def test_brier_score_accepts_the_probability_zero_boundary():
    # 0.0 is a legitimate, maximally confident "it will not happen" call
    # and must work without a division error or a spurious rejection.
    assert brier_score([(0.0, False)]) == 0.0
    assert brier_score([(0.0, True)]) == 1.0


def test_brier_score_rejects_probabilities_outside_the_unit_interval():
    with pytest.raises(ValueError):
        brier_score([(1.5, True)])
    with pytest.raises(ValueError):
        brier_score([(-0.1, False)])


def test_brier_score_averages_across_multiple_pairs():
    # Every other brier_score test above uses exactly one pair, where a
    # sum and a mean are the same number. This pins the averaging itself:
    # a regression that summed instead of averaging, or that only looked
    # at one of the pairs, would still pass every single-pair test here
    # but would be wrong for every real multi-prediction harness run.
    #
    # Hand-derived: (0.5 - 1) ** 2 = 0.25, (0.9 - 0) ** 2 = 0.81.
    # Mean of the two squared errors is (0.25 + 0.81) / 2 = 0.53.
    assert brier_score([(0.5, True), (0.9, False)]) == pytest.approx(0.53)


# --- flip_rate ---
# Positionwise disagreement rate between two equal-length orderings (for
# example, the same ranking run twice with two items swapped). There is no
# defined notion of "position i" when the two sequences have different
# lengths, so that case raises rather than guessing an alignment.

def test_flip_rate_counts_disagreements_between_orderings():
    assert flip_rate(["A", "A", "B"], ["A", "B", "B"]) == pytest.approx(1 / 3)


def test_flip_rate_with_mismatched_lengths_raises():
    with pytest.raises(ValueError):
        flip_rate(["A", "B"], ["A", "B", "C"])


def test_flip_rate_of_identical_orderings_is_zero():
    assert flip_rate(["A", "B", "C"], ["A", "B", "C"]) == 0.0


def test_flip_rate_of_empty_sequences_is_zero():
    assert flip_rate([], []) == 0.0


# Spearman rank correlation between two scorings of the same candidates. It
# answers "same order?" and deliberately not "same scores?", which is the
# whole reason a contaminated leaderboard can be wrong about every number and
# still right about the winner.

def test_rank_correlation_of_identical_orderings_is_one():
    assert rank_correlation([0.1, 0.2, 0.3], [0.4, 0.5, 0.6]) == pytest.approx(1.0)


def test_rank_correlation_ignores_a_uniform_shift():
    scores = [0.30, 0.55, 0.42, 0.71]
    inflated = [s + 0.12 for s in scores]
    assert rank_correlation(scores, inflated) == pytest.approx(1.0)


def test_rank_correlation_of_a_reversed_ordering_is_minus_one():
    assert rank_correlation([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]) == pytest.approx(-1.0)


def test_rank_correlation_with_one_pair_swapped_is_below_one():
    rho = rank_correlation([1.0, 2.0, 3.0, 4.0], [1.0, 2.0, 4.0, 3.0])
    assert 0.0 < rho < 1.0


def test_rank_correlation_gives_tied_candidates_the_same_rank():
    # Both lists hold the same ties, so the orderings agree completely. If
    # ties took list order instead of a shared rank this would not be 1.0.
    assert rank_correlation([1.0, 1.0, 2.0], [5.0, 5.0, 9.0]) == pytest.approx(1.0)


def test_rank_correlation_with_mismatched_lengths_raises():
    with pytest.raises(ValueError):
        rank_correlation([1.0, 2.0], [1.0, 2.0, 3.0])


def test_rank_correlation_of_fewer_than_two_candidates_is_zero():
    assert rank_correlation([1.0], [2.0]) == 0.0
    assert rank_correlation([], []) == 0.0


def test_rank_correlation_when_every_candidate_ties_is_zero_not_nan():
    result = rank_correlation([1.0, 1.0, 1.0], [3.0, 1.0, 2.0])
    assert result == 0.0
    assert not math.isnan(result)


# Share of identical runs whose gate verdict contradicts the majority. This
# measures the decision rather than the score, because a wobbling score is
# harmless until a threshold is drawn through the middle of the wobble.

def test_gate_flip_rate_of_unanimous_runs_is_zero():
    assert gate_flip_rate([0.90, 0.91, 0.93], 0.82) == 0.0
    assert gate_flip_rate([0.70, 0.71, 0.69], 0.82) == 0.0


def test_gate_flip_rate_counts_the_minority_verdict():
    # Three pass, one fails, so one run in four contradicts the majority.
    assert gate_flip_rate([0.83, 0.84, 0.85, 0.81], 0.82) == pytest.approx(0.25)


def test_gate_flip_rate_of_an_even_split_is_one_half():
    assert gate_flip_rate([0.83, 0.81], 0.82) == pytest.approx(0.5)


def test_gate_flip_rate_treats_a_score_on_the_threshold_as_passing():
    # A gate is normally written >=, so a run landing exactly on the number
    # passes. If this flipped, the metric would disagree with the gate it is
    # supposed to be measuring.
    assert gate_flip_rate([0.82, 0.83], 0.82) == 0.0


def test_gate_flip_rate_of_a_single_run_is_zero():
    # One verdict is unanimous by itself. That is the false confidence this
    # metric exists to expose, not a defect in it.
    assert gate_flip_rate([0.5], 0.82) == 0.0


def test_gate_flip_rate_of_no_runs_is_zero():
    assert gate_flip_rate([], 0.82) == 0.0


def test_gate_flip_rate_never_exceeds_one_half():
    for scores in ([0.9] * 3 + [0.1] * 7, [0.9] * 7 + [0.1] * 3, [0.9, 0.1]):
        assert gate_flip_rate(scores, 0.5) <= 0.5


# Smallest accuracy difference an eval of n items can distinguish from noise.
# This is the question that has to be asked before the result, not after it.

def test_minimum_detectable_effect_shrinks_as_items_are_added():
    small = minimum_detectable_effect(100, 0.78)
    large = minimum_detectable_effect(10_000, 0.78)
    assert large < small


def test_minimum_detectable_effect_follows_the_square_root_of_n():
    # Four times the items halves the detectable effect, which is the whole
    # reason buying resolution by adding items gets expensive so fast.
    at_n = minimum_detectable_effect(250, 0.5)
    at_4n = minimum_detectable_effect(1000, 0.5)
    assert at_4n == pytest.approx(at_n / 2, rel=1e-9)


def test_minimum_detectable_effect_is_worst_at_fifty_percent():
    middle = minimum_detectable_effect(500, 0.50)
    assert middle > minimum_detectable_effect(500, 0.80)
    assert middle > minimum_detectable_effect(500, 0.20)


def test_minimum_detectable_effect_at_a_certain_baseline_is_zero():
    # A system that is always right has no item-level variance, so there is
    # nothing to separate from noise. Zero is the honest answer, not an error.
    assert minimum_detectable_effect(500, 1.0) == 0.0


def test_minimum_detectable_effect_widens_as_power_rises():
    assert minimum_detectable_effect(500, 0.5, power=0.95) > minimum_detectable_effect(
        500, 0.5, power=0.80
    )


def test_minimum_detectable_effect_rejects_meaningless_questions():
    with pytest.raises(ValueError):
        minimum_detectable_effect(0, 0.5)
    with pytest.raises(ValueError):
        minimum_detectable_effect(100, 1.5)
    with pytest.raises(ValueError):
        minimum_detectable_effect(100, 0.5, power=1.0)
    with pytest.raises(ValueError):
        minimum_detectable_effect(100, 0.5, alpha=0.0)


def test_minimum_detectable_effect_matches_the_textbook_constant():
    # At 80 percent power and alpha 0.05 two-sided the multiplier is
    # 1.959964 + 0.841621 = 2.801585. Pinning it catches a silently swapped
    # z-value, which would move every number this unit teaches.
    n, p = 1000, 0.5
    expected = 2.801585 * (2 * p * (1 - p) / n) ** 0.5
    assert minimum_detectable_effect(n, p) == pytest.approx(expected, rel=1e-5)

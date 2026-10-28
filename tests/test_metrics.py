import pytest

from app.metrics import brier_score, flip_rate, ndcg_at_k, precision_at_k, recall_at_k


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

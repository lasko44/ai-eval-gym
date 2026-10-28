"""Retrieval metrics: how good is the first k results a retriever returned.

Both recall and precision start from the same two inputs: an ordered list of
retrieved document ids, and some notion of which documents were actually
good. They answer two different questions, though:

- recall_at_k: of everything that was relevant, how much did we find?
- precision_at_k: of what we looked at, how much was relevant?

ndcg_at_k extends the idea to graded relevance (not just relevant/irrelevant)
and rewards putting the best documents first, not merely including them
somewhere in the top k.
"""

import math


def _top_k_slice(items: list[str], k: int) -> list[str]:
    """Return the first k items, treating k <= 0 as "look at nothing".

    A negative k would silently drop items from the end under normal list
    slicing (items[:-1] skips the last item rather than returning an empty
    list), which is not what a caller asking for "the top -1 results" could
    possibly mean. Clamping k to zero first makes k <= 0 behave the same
    way as "I asked for zero results": an empty slice, not a crash and not
    a surprising slice from the wrong end. k larger than len(items) needs no
    special handling: Python slicing already returns the whole list in that
    case, which is the right answer for "use what was actually retrieved".
    """
    return items[: max(k, 0)]


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Fraction of the relevant documents that appear in the first k retrieved.

    The denominator is the full count of relevant documents, not k and not
    the number retrieved. Recall asks "how much of what mattered did we
    find", and that question's answer does not change just because k is
    small: missing a relevant document because it was ranked 3rd and k was
    2 still counts against you.

    An empty relevant set returns 0.0 rather than raising or returning NaN
    (0/0), so a harness run against a slice of data with no relevance
    labels degrades to a visible, obviously-wrong-looking zero instead of
    crashing the whole run.
    """
    if not relevant:
        return 0.0
    top_k = _top_k_slice(retrieved, k)
    hits = sum(1 for doc in top_k if doc in relevant)
    return hits / len(relevant)


def precision_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    """Fraction of the first k retrieved documents that are relevant.

    The denominator is the number of documents actually examined, which is
    min(k, len(retrieved)): if the retriever only returned 3 documents and
    k is 10, precision is computed over those 3, not diluted by 7 slots
    that were never filled. Dividing by k itself would punish a retriever
    for returning fewer results than asked for, which is a different
    failure than returning the wrong results.

    An empty relevant set, or k <= 0 (nothing was looked at), returns 0.0
    rather than raising or dividing by zero.
    """
    if not relevant:
        return 0.0
    top_k = _top_k_slice(retrieved, k)
    denominator = min(max(k, 0), len(retrieved))
    if denominator == 0:
        return 0.0
    hits = sum(1 for doc in top_k if doc in relevant)
    return hits / denominator


def ndcg_at_k(retrieved: list[str], relevance: dict[str, float], k: int) -> float:
    """Normalized Discounted Cumulative Gain at k.

    Rewards graded relevance (not just "relevant or not") and rewards
    putting the best documents earlier, not merely including them
    somewhere in the top k.

    Discount convention used here: rank is counted from 1 for the first
    retrieved item, and each item's relevance is divided by log2(rank + 1).
    The top position (rank 1) therefore divides by log2(2) == 1, i.e. gets
    no discount at all, and every later position is discounted more. This
    is the standard positional-discount formulation (as opposed to the
    exponential 2**relevance - 1 gain variant, which this implementation
    does not use: relevance grades are used directly as the gain).

    DCG@k is computed from the actual retrieved order. IDCG@k (the
    normalizer) is computed from the best possible ordering of the
    relevance grades available, which is simply those grades sorted from
    highest to lowest, discounted the same way, truncated to k: this is
    the maximum DCG@k achievable by any ordering of the known-relevant
    documents, even ones this retrieval did not return. NDCG@k is DCG@k
    divided by IDCG@k, so a perfect ordering scores 1.0.

    An empty relevance dict means there is nothing to normalize against
    (IDCG would be 0), so this returns 0.0 rather than raising or dividing
    by zero. Documents in `retrieved` that have no entry in `relevance`
    are treated as having relevance 0.0, same as an explicit 0.
    """
    if not relevance:
        return 0.0

    k_eff = max(k, 0)
    top_k = _top_k_slice(retrieved, k)

    dcg = sum(
        relevance.get(doc, 0.0) / math.log2(rank + 1)
        for rank, doc in enumerate(top_k, start=1)
    )

    ideal_grades = sorted(relevance.values(), reverse=True)[:k_eff]
    idcg = sum(
        grade / math.log2(rank + 1)
        for rank, grade in enumerate(ideal_grades, start=1)
    )

    if idcg == 0:
        return 0.0
    return dcg / idcg

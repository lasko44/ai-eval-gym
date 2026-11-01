"""The one system this whole course evaluates.

A course that ships one fixture per unit, each about a different unnamed
system, teaches that many separate tricks. The reader finishes it holding a bag of gotchas and
no method, because nothing ever had to work together.

So there is one system under evaluation, described here once, and every unit
measures a different part of the same thing. Unit 01 asks whether the judge
scoring its answers can be trusted. Unit 09 asks whether its index can reach
the right document. Unit 16 asks what a p95 of its latency costs a person
waiting. Same system, different instrument, and the order is the order you
would actually have to measure it in.

It is deliberately a lender's system rather than a chatbot. The governance
part has to prove things to somebody who can issue a fine, and that is only a
real constraint when the system is doing something a regulator cares about.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemUnderEvaluation:
    """The target. Not a product to build, a system to take apart."""

    name: str
    what_it_does: str
    why_it_is_hard: tuple[str, ...]
    what_you_are_handed: tuple[str, ...]


SYSTEM = SystemUnderEvaluation(
    name="Ledger",
    what_it_does=(
        "Ledger answers questions about private credit loan documents. An "
        "underwriter asks whether a borrower's covenant package permits a "
        "distribution. Ledger retrieves the relevant clauses from the credit "
        "agreement and its amendments, then reads them together. It answers "
        "in plain words, with citations back to the source pages."
    ),
    why_it_is_hard=(
        "The answer usually lives in more than one document. Lenders amend a "
        "credit agreement repeatedly, so the operative language is the "
        "original clause as three later amendments left it. Retrieve only the "
        "original and Ledger gives a confidently wrong answer that reads "
        "correct.",
        "Nobody can check every answer. The whole point is to save an "
        "underwriter from reading 400 pages, so if a human verifies the "
        "output the system has delivered nothing. That is what forces the "
        "evaluation to carry the weight.",
        "Being wrong is expensive and slow to surface. A missed covenant "
        "breach does not page anybody. It shows up in a quarterly review, or "
        "in an audit, long after somebody swapped out the model that produced "
        "it.",
    ),
    what_you_are_handed=(
        "A running system somebody else built, with no tests you trust.",
        "A stakeholder who already believes it works, because the demo was "
        "good.",
        "A deadline that assumes evaluation is a week of work.",
    ),
)

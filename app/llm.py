"""The capped model client.

This is the only place in the app that is allowed to call a real LLM. The
user's harness code imports complete() whenever an evaluation needs a model
call, for example an LLM-as-judge metric, instead of calling the anthropic
SDK directly.

The cap exists because this is a learning project on a personal budget: the
monthly ceiling is MONTHLY_CEILING_CENTS (five thousand cents, fifty dollars,
by default). It is enforced here, in code, before any request leaves the
process. A model cannot be told "stay under budget" in its own prompt and be
trusted to obey; the only trustworthy enforcement point is the one line of
code that decides whether to call the network at all.

How the cap actually works:
  1. Before sending anything, estimate the worst case cost of the request:
     every one of max_tokens billed at the (more expensive) output rate,
     plus the input cost of the prompt. This is deliberately pessimistic.
     A check against the *expected* cost (for example, assuming the model
     stops early) is not a cap, because the model is free to use all of
     max_tokens.
  2. If the month's spend-so-far plus that worst case would cross the
     ceiling, raise BudgetExceeded and stop. _send is never called.
  3. Only if the check passes does _send make the real call.
  4. After the call returns, record the *actual* cost from the response's
     real token usage, not the estimate. The estimate's job is only to
     decide whether to go ahead; it is never written to the ledger.

_send is the single private function that performs the actual network call.
Every test in tests/test_llm_budget.py replaces it with a stub, which is
what makes it safe to run this test file as often as you like without
spending real money, and it is also the one place a real integration test
can point at to prove the live API path actually works.
"""

import os
from datetime import UTC, datetime

import anthropic

from app.models import SpendLedger

# The monthly ceiling, read from the environment with a $50.00 default.
# There is no config module in this project yet (see app/db.py and
# app/models.py for the same pattern), so this constant lives here, next to
# the only code that enforces it.
MONTHLY_CEILING_CENTS = int(os.environ.get("MONTHLY_CEILING_CENTS", "5000"))

# Per-token pricing, in cents per million tokens, so every cost computation
# below stays in integer arithmetic (money here is always integer cents,
# never a float). Rates are taken from the claude-api skill's pricing table
# (cached 2026-06-24), not from memory, because a wrong output rate would
# silently break the cap: claude-sonnet-5 is $2.00 / 1M input tokens and
# $10.00 / 1M output tokens, i.e. 200 and 1000 cents per million tokens.
PRICING_CENTS_PER_MILLION_TOKENS = {
    "claude-sonnet-5": {"input": 200, "output": 1000},
}


class BudgetExceeded(Exception):
    """Raised when a request's worst-case cost would cross the monthly
    ceiling. Raised before any network call, never returned as a value, so
    a caller cannot accidentally ignore it the way it might ignore a
    falsy return.
    """


def current_month() -> str:
    """The current calendar month as YYYY-MM, in UTC.

    This is the SpendLedger key. Using UTC (rather than local time) means
    the month a request is billed against does not depend on which machine
    or timezone the harness happens to run in.
    """
    return datetime.now(UTC).strftime("%Y-%m")


def _pricing_for(model: str) -> dict:
    try:
        return PRICING_CENTS_PER_MILLION_TOKENS[model]
    except KeyError:
        raise ValueError(
            f"no pricing configured for model {model!r}. Add its input and "
            "output rates to PRICING_CENTS_PER_MILLION_TOKENS in app/llm.py "
            "before using it for a billed call: without a rate, the cap has "
            "nothing to check the request against."
        ) from None


def _cost_cents(tokens: int, cents_per_million_tokens: int) -> int:
    """tokens billed at cents_per_million_tokens, rounded up to the next
    whole cent. Rounding up (never down) matters here: this function feeds
    both the worst-case estimate and the actual recorded spend, and rounding
    down would let a long run of small requests quietly undercount.
    """
    return -(-(tokens * cents_per_million_tokens) // 1_000_000)


def _estimate_input_tokens(prompt: str) -> int:
    """A local, offline estimate of how many tokens the prompt will cost as
    input. This cannot be the real tokenizer: the real count comes from
    Anthropic's count_tokens endpoint, which is itself a network call, and
    the entire point of this estimate is to run before anything reaches the
    network. Anthropic's own documentation gives roughly 4 characters per
    token for English text as a rule of thumb; dividing by 4 and rounding up
    leans conservative, which is the right direction for a cap (overcounting
    input tokens makes the check stricter, never looser).
    """
    return max(1, -(-len(prompt) // 4))


def _worst_case_cost_cents(prompt: str, model: str, max_tokens: int) -> int:
    """The worst case cost of a request: the input cost of the prompt, plus
    every one of max_tokens billed at the output rate. This is the number
    the cap checks against. The model is free to use its full max_tokens
    budget, so checking against anything less (an "expected" or average
    cost) would not actually cap spend, only the common case of it.
    """
    rates = _pricing_for(model)
    input_cost = _cost_cents(_estimate_input_tokens(prompt), rates["input"])
    output_cost = _cost_cents(max_tokens, rates["output"])
    return input_cost + output_cost


def _actual_cost_cents(usage, model: str) -> int:
    """The real cost of a completed call, from the response's own reported
    token counts. This is what gets written to the ledger, never the
    worst-case estimate: the estimate's only job is the go/no-go decision
    before the call, not the amount recorded after it.
    """
    rates = _pricing_for(model)
    return _cost_cents(usage.input_tokens, rates["input"]) + _cost_cents(
        usage.output_tokens, rates["output"]
    )


def _extract_text(response) -> str:
    for block in response.content:
        if getattr(block, "type", None) == "text":
            return block.text
    return ""


def _send(prompt: str, *, model: str, max_tokens: int):
    """The one function in this module that actually calls the Anthropic
    API. Every other function here only decides whether and how to call
    this one. Keeping the real call behind a single, narrow function is
    what makes it possible to stub out the network in tests: tests replace
    app.llm._send and nothing else.

    Reads credentials from the ANTHROPIC_API_KEY environment variable via
    the SDK's default client construction; no key is ever hardcoded here.
    """
    client = anthropic.Anthropic()
    return client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )


def complete(session, prompt: str, *, model: str, max_tokens: int) -> str:
    """Run a capped model call and return its text.

    session is the caller's own SQLAlchemy session, and every database
    operation here (finding or creating this month's ledger row, checking
    the cap, and recording actual spend) happens inside that same session
    without complete() ever calling session.commit() itself. That is what
    makes the row creation, the cap check and the spend write transactional
    together: they all land or all roll back as one unit with whatever the
    caller does next, so two concurrent callers reading the same ledger row
    cannot both see a stale "under budget" state and both go ahead. The
    SELECT ... FOR UPDATE below (via with_for_update) additionally holds a
    row lock on an existing ledger row for the duration of the caller's
    transaction, so a second caller checking the same month's row blocks
    until the first one commits or rolls back, rather than racing it.

    Raises BudgetExceeded, before _send is ever called, when the worst-case
    cost of this request would push the month's spend past
    MONTHLY_CEILING_CENTS.
    """
    month = current_month()

    row = session.query(SpendLedger).filter_by(month=month).with_for_update().one_or_none()
    if row is None:
        # No ledger row for this month yet. This must create one, not
        # assume zero and wave the request through: an assumed zero is not
        # a real spend check, it is skipping the check for the first call
        # of every month.
        row = SpendLedger(month=month, spent_cents=0)
        session.add(row)
        session.flush()

    worst_case_cents = _worst_case_cost_cents(prompt, model, max_tokens)
    if row.spent_cents + worst_case_cents > MONTHLY_CEILING_CENTS:
        raise BudgetExceeded(
            f"this request could cost up to {worst_case_cents} cents; "
            f"{row.spent_cents} of {MONTHLY_CEILING_CENTS} cents already "
            f"spent in {month}"
        )

    response = _send(prompt, model=model, max_tokens=max_tokens)

    row.spent_cents += _actual_cost_cents(response.usage, model)
    session.flush()

    return _extract_text(response)

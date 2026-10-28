"""Tests for the capped model client in app.llm.

Every test that would otherwise send a real request stubs app.llm._send,
which is the one function in the module that actually talks to the network.
That keeps this file from ever billing a real API call just by running
`pytest`. The one exception is the real-service test at the bottom, which
is skipped unless ANTHROPIC_API_KEY is set, and makes exactly one minimal
call when it does run.

Ruling 1 overrides the task brief's literal test bodies: complete() takes
the session as its first argument, because the cap check and the spend
write have to happen inside the caller's transaction, and a module-level
implicit session could not be rolled back between tests or made safe under
concurrent callers.
"""

import os
from types import SimpleNamespace

import pytest

from app.models import SpendLedger
from app.llm import BudgetExceeded, complete, current_month


def _fake_response(input_tokens: int, output_tokens: int, text: str = "ok"):
    """Build an object that looks enough like an anthropic Message to drive
    complete()'s response handling: a .content list of text blocks, and a
    .usage with real token counts. complete() reads both by attribute, the
    same way it would read a real anthropic.types.Message, so this stand-in
    exercises the same code path a real response would.
    """
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


def test_a_request_that_would_cross_the_ceiling_raises_before_calling(session, monkeypatch):
    # Fix for review finding 2: the brief's literal body hardcodes
    # month="2026-10". complete() keys on current_month(), so that string
    # only matches "today" while the real calendar is still in October
    # 2026; from November 1 onward complete() would find no row, create
    # one at 0 cents, pass the (still-worst-case) check, and call the
    # stubbed _send, which returns None, failing the test on an unrelated
    # AttributeError instead of raising BudgetExceeded. Seeding with
    # current_month() keeps the test pinned to "this month" forever.
    session.add(SpendLedger(month=current_month(), spent_cents=4990))
    session.commit()
    called = []
    monkeypatch.setattr("app.llm._send", lambda *a, **k: called.append(1))
    with pytest.raises(BudgetExceeded):
        complete(session, "hi", model="claude-sonnet-5", max_tokens=100_000)
    assert called == []


def test_max_tokens_is_billed_at_the_output_rate_not_the_input_rate(session, monkeypatch):
    # Review finding 5: the previous ceiling test could not tell the output
    # rate from the input rate. At 100_000 max_tokens, a (wrong)
    # implementation that billed max_tokens at the input rate ($2.00 / 1M,
    # 200 cents/million) would estimate 21 cents total (1 cent for the
    # prompt's own input cost, plus 20 cents for 100_000 tokens at the
    # input rate), so 4950 + 21 = 4971 cents stays under the 5000 ceiling
    # and the request would wrongly be allowed. Billing max_tokens at the
    # output rate ($10.00 / 1M, 1000 cents/million), which is correct,
    # estimates 101 cents (1 cent for the prompt plus 100 cents for
    # 100_000 tokens at the output rate), so 4950 + 101 = 5051 cents
    # crosses the ceiling and must raise. This discriminates between the
    # two: it only passes if max_tokens is actually billed at the output
    # rate.
    session.add(SpendLedger(month=current_month(), spent_cents=4950))
    session.commit()
    called = []
    monkeypatch.setattr("app.llm._send", lambda *a, **k: called.append(1))
    with pytest.raises(BudgetExceeded):
        complete(session, "hi", model="claude-sonnet-5", max_tokens=100_000)
    assert called == []


def test_a_cheap_request_under_the_ceiling_proceeds_and_records_spend(session, monkeypatch):
    # Review finding 6: nothing in this file previously covered the
    # "allowed" path near the ceiling, so an inverted comparison in
    # complete() (refusing when it should allow) would pass every other
    # test here. Seed the ledger just under the ceiling with a cheap
    # request that must be allowed, and confirm _send is actually called
    # and the resulting spend is recorded.
    session.add(SpendLedger(month=current_month(), spent_cents=4990))
    session.commit()
    monkeypatch.setattr("app.llm._send", lambda *a, **k: _fake_response(1, 1))

    result = complete(session, "hi", model="claude-sonnet-5", max_tokens=1)

    assert result == "ok"
    assert session.query(SpendLedger).filter_by(month=current_month()).one().spent_cents > 4990


def test_a_month_with_no_ledger_row_is_created_not_assumed_zero(session, monkeypatch):
    # Ruling 2: this test stubs _send too, even though the brief's original
    # version called complete() with nothing stubbed. Running it unstubbed
    # would send a real billed request every time this file runs.
    monkeypatch.setattr("app.llm._send", lambda *a, **k: _fake_response(500, 500))

    complete(session, "hi", model="claude-sonnet-5", max_tokens=10)

    assert session.query(SpendLedger).filter_by(month=current_month()).one().spent_cents > 0


FAKE_RESPONSE_COST_CENTS = 12


@pytest.fixture()
def fake_response(monkeypatch):
    """Stub _send to return a response whose real usage costs exactly
    FAKE_RESPONSE_COST_CENTS cents at claude-sonnet-5 output pricing
    ($10.00 / 1M output tokens), with zero input tokens so the number is
    exact and not affected by the input side of the estimate.

    12 cents = 12,000 output tokens * 1000 cents-per-million-tokens / 1e6.

    This is the pre-flight ruling's replacement for the brief's invalid
    `fake_response_costing_cents(12)` call-as-fixture syntax: a normal
    fixture, parametrised by the module constant above rather than by a
    pytest call argument.
    """
    response = _fake_response(input_tokens=0, output_tokens=12_000)
    monkeypatch.setattr("app.llm._send", lambda *a, **k: response)
    return response


def test_actual_usage_is_recorded_after_the_call(session, fake_response):
    complete(session, "hi", model="claude-sonnet-5", max_tokens=10)
    assert session.query(SpendLedger).one().spent_cents == FAKE_RESPONSE_COST_CENTS


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; skipping the real API call",
)
def test_complete_against_the_real_api_returns_text_and_records_spend(session):
    """Drive complete() itself, end to end, against the live API.

    This test used to call _send directly and then re-implement text
    extraction inline, which proved only that client.messages.create
    returns something with a .content. Everything between the cap check and
    the returned string was therefore exercised only against the
    SimpleNamespace stand-ins this repo writes: _actual_cost_cents reading
    the response's real usage attribute names, the ledger write, and
    _extract_text. Calling complete() is what proves those against a real
    response, and it is what would catch a renamed usage field in a future
    SDK instead of agreeing with whatever the stub says.

    One minimal call: at max_tokens=16 the worst case is well under a cent.

    The commit is the caller's obligation, not complete()'s (see its
    docstring), so this test commits the way a real harness must. The
    session fixture drops the tables afterwards, so the recorded cent does
    not outlive the test.
    """
    before = (
        session.query(SpendLedger).filter_by(month=current_month()).one_or_none()
    )
    before_cents = before.spent_cents if before else 0

    text = complete(
        session, "Reply with a single word.", model="claude-sonnet-5", max_tokens=16
    )
    session.commit()

    assert text.strip() != ""
    after = session.query(SpendLedger).filter_by(month=current_month()).one()
    assert after.spent_cents > before_cents

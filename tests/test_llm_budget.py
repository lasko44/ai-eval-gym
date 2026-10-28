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
    session.add(SpendLedger(month="2026-10", spent_cents=4990))
    session.commit()
    called = []
    monkeypatch.setattr("app.llm._send", lambda *a, **k: called.append(1))
    with pytest.raises(BudgetExceeded):
        complete(session, "hi", model="claude-sonnet-5", max_tokens=100_000)
    assert called == []


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
def test_send_against_the_real_api_returns_nonempty_text():
    """Proves _send actually works against the live API, not just against
    the stub every other test in this file substitutes for it. Makes
    exactly one minimal call (max_tokens=16) and only runs when a real key
    is configured.
    """
    from app.llm import _send

    response = _send("Reply with a single word.", model="claude-sonnet-5", max_tokens=16)

    text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    assert text.strip() != ""

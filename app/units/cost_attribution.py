"""Unit 19: the Ledger invoice is one number, so nobody can cut it.

Unit 16 settled the denominator, cost per resolved underwriter question rather
than cost per call. This unit settles the owner: which use case and which team
caused the spend, what to do with shared infrastructure that no single caller
asked for, and how to make a chargeback number reconcile to the invoice.
Numbers and citations verified against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.

    The fixture is a dict holding one month of billed calls, a price table, and
    the shared infrastructure line items that no single call caused.
    """
    price = data["prices_usd_per_token"]

    def cost(call: dict) -> float:
        return (
            call["input_tokens"] * price["input"]
            + call["cache_write_tokens"] * price["cache_write"]
            + call["cache_read_tokens"] * price["cache_read"]
            + call["output_tokens"] * price["output"]
        )

    shared = sum(data["shared_infrastructure_usd"].values())
    calls = data["calls"]
    total = shared + sum(cost(call) for call in calls)
    untagged = sum(cost(call) for call in calls if call["use_case"] is None)
    return (shared + untagged) / total


UNIT = Unit(
    slug="cost-attribution",
    number=19,
    part="serving",
    title="The Ledger invoice is one number, so nobody can cut it",
    failure=(
        "The team reports one monthly spend figure for Ledger. Nobody can act "
        "on it, because the figure names no use case and no team. The shared "
        "cache, the index, the retries and the untagged batch traffic all "
        "disappear into it, and so does the question of who caused them."
    ),
    detection=(
        "Measure what share of the invoice has no single use case behind it. "
        "Report that share first. Then check that the allocated amounts plus "
        "that share add back to the invoice total."
    ),
    brief=(
        "The invoice arrives as one number. Unit 16 fixed the denominator, so "
        "the figure is already cost per resolved underwriter question rather "
        "than cost per call. This unit is about the numerator, and about whose "
        "it is. A lender told that Ledger cost 120.22 dollars last month has "
        "learned nothing it can act on. Nobody cuts a number nobody owns.",
        "The FinOps Foundation treats this as a capability with a target "
        "rather than a reporting preference. Its maturity model asks for at "
        "least 70 percent of cost allocated to a known owner at the first "
        "level. The second level asks for 85 percent and the third for more "
        "than 90 percent. Its allocation capability names the measurement: the "
        "share of cost that nobody can categorize or allocate directly. So the "
        "first number on the dashboard is not spend. It is the share of spend "
        "nobody can name an owner for.",
        "Shared infrastructure is where most of that share comes from, and a "
        "prompt cache is the clean example. Published Claude pricing charges a "
        "five minute cache write at 1.25 times the base input price, and a one "
        "hour write at 2 times it. A cache read costs 0.1 times that price, "
        "and 0.05 times it on the current Opus and Sonnet tiers. On the Sonnet "
        "tier those three rates are 2 dollars, 2.50 dollars and 0.10 dollars "
        "per million tokens. So warming a clause package costs 25 times what "
        "each later call pays to read it.",
        "Attribute that strictly by call, and the use case that arrived first "
        "subsidises every use case after it. Pure timing decided that, and "
        "timing is not a fact about the use case. The FinOps Foundation names "
        "one defensible alternative, informed ignore. That is a deliberate "
        "decision to budget a shared item centrally rather than allocate it "
        "out of each cost center. Leaving it in the unexplained remainder is "
        "not defensible, and that is what usually happens.",
        "The distribution of callers is never flat either, which decides who "
        "you need to talk to. Microsoft measured every application on Azure "
        "Functions across its entire infrastructure for two weeks in July "
        "2019. The 18.6 percent most popular applications accounted for 99.6 "
        "percent of all function invocations. Another 81 percent of "
        "applications averaged at most one invocation per minute. That "
        "measurement counts invocations rather than dollars, so take the shape "
        "and not the figure. A flat per-team split across a distribution like "
        "that bills the quiet majority for traffic they never sent.",
        "Retries carry the same problem one layer down. A failed call still "
        "gets a bill, and so does the retry after it. Both land on whichever "
        "use case was unlucky enough to hit the failure. In this unit's "
        "fixture the retries are 4.65 percent of the whole invoice, and they "
        "spread very unevenly. The heaviest use case carries 9.35 percent of "
        "its own bill in retries, and another carries 2.72 percent. A gateway "
        "failover has the same shape, because the use case whose request met a "
        "degraded provider pays for the reroute.",
        "Finance accepts a chargeback number for one reason, and it is "
        "arithmetic. The invoicing and chargeback capability of the FinOps "
        "Foundation asks you to validate chargeback data against the costs the "
        "invoice implies. It also tracks the variance between what the cost "
        "tooling says and what the general ledger actually charged. So the "
        "allocated amounts plus a named, deliberate unallocated amount have to "
        "add to the invoice total. A model whose parts do not add up to the "
        "bill gets one rejection and then nobody reads it again."
    ),
    builds_on=(
        "Unit 16. Cost per resolved question gives you a number worth owning, "
        "and only then is it worth asking which use case and which team owns "
        "it."
    ),
    probes=(
        Probe(
            id="who-pays-the-cache-write",
            asks=(
                "Ledger caches a borrower's clause package. The first question "
                "of the morning pays a cache write, and every question after "
                "it pays a cache read. Published pricing puts a five minute "
                "write at 1.25 times the base input price and a read at 0.1 "
                "times it. Who should carry the write in a chargeback model?"
            ),
            choices=(
                Choice("a", "The use case whose call warmed it, because that call is where the write landed"),
                Choice("b", "Nobody, because a cache write is an artifact of the cache rather than real spend"),
                Choice("c", "The readers of that package, or a named central line, because one call's timing decided who got the bill"),
                Choice("d", "The platform team, because the platform team chose to turn caching on"),
            ),
            answer="c",
            because=(
                "On the Sonnet tier a five minute write runs 2.50 dollars per "
                "million tokens against 0.10 dollars for a hit. So the warming "
                "call carries 25 times the bill of each reading call. In this "
                "unit's fixture the calls that warmed the cache cost 4.75 "
                "times an average cache hit. Who asked first decides which use "
                "case gets that bill, and that is not a fact about the use "
                "case. Spread it over the readers, or budget it centrally and "
                "say so, which the FinOps Foundation calls informed ignore."
            ),
        ),
        Probe(
            id="flat-split-across-a-long-tail",
            asks=(
                "Ledger serves eight named use cases. Finance proposes "
                "dividing the monthly invoice into eight equal shares, on the "
                "grounds that every use case shares the same infrastructure. "
                "What does that method get wrong?"
            ),
            choices=(
                Choice("a", "Nothing, because an even split is the only defensible method for a shared bill"),
                Choice("b", "Only the period, because a month is too short a window to divide"),
                Choice("c", "The shape of the demand, because a few use cases drive nearly all the spend and the rest pay for traffic they never sent"),
                Choice("d", "The direction, because an even split always overcharges the largest use case"),
            ),
            answer="c",
            because=(
                "Caller demand concentrates hard, and Microsoft measured how "
                "hard on Azure Functions over two weeks. The 18.6 percent most "
                "popular applications accounted for 99.6 percent of all "
                "invocations. Another 81 percent of applications averaged at "
                "most one invocation per minute. The fixture in this unit has "
                "the same shape. The top use case carries 44.7 percent of the "
                "attributed spend, and the four smallest carry 9.3 percent "
                "between them. An even split moves money from the cause to the "
                "bystanders, and the bystanders are the ones who dispute the "
                "whole report."
            ),
        ),
        Probe(
            id="what-finance-accepts",
            asks=(
                "Your allocation model assigns 82.90 dollars of Ledger spend "
                "to named use cases. The provider invoice for the same month "
                "is 120.22 dollars. What do you take to finance?"
            ),
            choices=(
                Choice("a", "The 82.90 dollars, because that is the part you can defend line by line"),
                Choice("b", "The 82.90 dollars scaled up by the ratio, so the per-use-case figures add to the invoice"),
                Choice("c", "The 82.90 dollars allocated plus a named 37.32 dollars of shared and untagged spend, so the parts add to the invoice"),
                Choice("d", "The invoice total alone, with per-use-case figures held back until tagging improves"),
            ),
            answer="c",
            because=(
                "The chargeback capability of the FinOps Foundation asks you "
                "to validate chargeback data against the costs the invoice "
                "implies. It also tracks the variance between the cost tooling "
                "and the general ledger. A report that stops at 82.90 dollars "
                "leaves 37.32 dollars unexplained, so finance has to find the "
                "difference itself. Grossing the figures up hides the same gap "
                "inside numbers that now look precise and measure nothing. A "
                "named shared and untagged line reconciles to the invoice. It "
                "also turns the 31 percent that nobody owns into the next "
                "piece of work."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships one month of Ledger gateway telemetry: 2,223 "
            "billed calls, plus the shared infrastructure line items for the "
            "same month. The published per-token prices to cost them with are "
            "in the file. Cost every call and every shared line, then post the "
            "share of the month's total spend that has no single use case "
            "behind it. Post it as a fraction, so 0.25 would mean a quarter of "
            "the invoice has no named owner."
        ),
        fixture_path="fixtures/cost_attribution/monthly_spend.json",
        fixture_note=(
            "\"calls\" holds 2,223 billed calls, each with a use_case and a "
            "team. Both are null when the call came through a shared service "
            "account with no caller identity on it. Each call also "
            "carries input_tokens, cache_read_tokens, cache_write_tokens, "
            "output_tokens, an attempt number, a question_id, and resolved. A "
            "retry shares its question_id with the call it retried. "
            "\"shared_infrastructure_usd\" holds the line items no single call "
            "caused: the nightly clause cache warm, the amendment "
            "re-embedding job, and the index host. \"prices_usd_per_token\" "
            "prices all four token kinds, and \"invoice_total_usd\" is the "
            "provider total to check your own against."
        ),
        starter=(
            'import json\n'
            '\n'
            'data = json.load(open("fixtures/cost_attribution/monthly_spend.json"))\n'
            'price = data["prices_usd_per_token"]\n'
            'calls = data["calls"]\n'
            'shared = data["shared_infrastructure_usd"]\n'
            '\n'
            '# Costing one call is arithmetic rather than judgment, so here it\n'
            '# is. A cache write is priced very differently from a cache read,\n'
            '# which is the whole point.\n'
            'def cost(call):\n'
            '    return sum(\n'
            '        call[f"{kind}_tokens"] * price[kind]\n'
            '        for kind in ("input", "output", "cache_read", "cache_write")\n'
            '    )\n'
            '\n'
            'print("billed calls:", len(calls))\n'
            'print("calls carrying no use_case at all:",\n'
            '      sum(1 for call in calls if call["use_case"] is None))\n'
            'print("shared infrastructure lines:", shared)\n'
            'print("every call costed and added up:",\n'
            '      round(sum(cost(call) for call in calls), 6))\n'
            'print("provider invoice total:", data["invoice_total_usd"])\n'
            '\n'
            '# TODO: the last two numbers printed above do not agree, and the\n'
            '# difference is the question. Decide which of the money billed this\n'
            '# month has no single use case behind it, and what the denominator\n'
            '# has to be for a share a lender would be shown. Reconcile that\n'
            '# denominator against invoice_total_usd before you trust the\n'
            '# fraction, then print the share.\n'
            '#\n'
            '# Two more findings fall out of the same costed calls once that\n'
            '# number is out: which use case spends the most of what IS\n'
            '# attributable, and how much of each use case is retries rather\n'
            '# than first attempts.\n'
        ),
        metric="unattributable_spend_share",
        expected=0.310433,
        tolerance=0.0005,
        because=(
            "The month bills 120.22 dollars, and 37.32 of that has no single "
            "owner, which is 31.04 percent. Shared infrastructure is 25.95 "
            "percent of the invoice and the untagged calls another 5.09 "
            "percent, from only 97 of the 2,223 calls. The FinOps Foundation "
            "maturity model asks for at least 70 percent allocated to a known "
            "owner at its first level, and this month sits under it. Two more "
            "findings fall out of the same pass. The 138 calls that warmed the "
            "cache rather than read it are 6.21 percent of the calls and 17.71 "
            "percent of the invoice. And the top spender is a background "
            "portfolio sweep at 44.68 percent of attributed spend, against "
            "25.82 percent for the covenant checks that sold the product."
        ),
    ),
    sources=(
        "platform.claude.com/docs/en/build-with-claude/prompt-caching, fetched "
        "2026-11-01, cache write at 1.25 times base input for a five minute "
        "lifetime and 2 times for a one hour lifetime, cache reads at 0.1 times "
        "base input and 0.05 times on the current Opus and Sonnet tiers, with "
        "the Sonnet per-million prices of 2 dollars input, 2.50 dollars write "
        "and 0.10 dollars hit",
        "finops.org/framework/maturity-model, FinOps Foundation, at least 70 "
        "percent of cost allocated to a known owner at the first maturity "
        "level, at least 85 percent at the second, more than 90 percent at the "
        "third",
        "finops.org/framework/capabilities/allocation, FinOps Foundation, the "
        "percentage of cost that cannot be categorized and allocated directly, "
        "shared cost strategy, and informed ignore as a deliberate central "
        "budget decision",
        "finops.org/framework/capabilities/invoicing-chargeback, FinOps "
        "Foundation, validate that chargeback data aligns with costs expected "
        "from the invoice plus any added costs, and the general ledger recharge "
        "variance measure",
        "usenix.org/system/files/atc20-shahrad.pdf, Shahrad et al., Serverless "
        "in the Wild, measured over Azure Functions across the entire "
        "infrastructure from 15 to 28 July 2019: the 18.6 percent most popular "
        "applications represent 99.6 percent of all function invocations, and "
        "81 percent of applications average at most one invocation per minute",
    ),
)

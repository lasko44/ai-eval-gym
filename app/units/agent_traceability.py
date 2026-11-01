"""Unit 22: the trace that cannot answer why Ledger said it.

A trace that looks healthy by volume can still fail the one question an
examiner actually asks: why did Ledger say that, for this borrower, in March.
Monitoring and an audit trail are different things, and a team can have the
first without the second. Numbers and citations verified against primary
sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.
    """
    required_keys = (
        "gen_ai.response.model_version",
        "app.prompt.version",
        "gen_ai.tool.call.arguments",
        "app.retrieval.document_ids",
        "app.policy.threshold_applied",
        "app.identity.authorized_by",
    )
    traces = data["traces"]
    present = 0
    for trace in traces:
        merged: dict = {}
        for span in trace["spans"]:
            merged.update(span.get("attributes", {}))
        present += sum(1 for key in required_keys if key in merged)
    return present / (len(traces) * len(required_keys))


UNIT = Unit(
    slug="agent-traceability",
    number=22,
    part="governance",
    title="The trace that cannot answer why Ledger said it",
    failure=(
        "Ledger's trace proves a retrieval ran. It does not record which clauses the "
        "model read or which amendment version was operative. It does not record who "
        "asked. Nobody can explain one specific answer after the fact."
    ),
    detection=(
        "Pick one answer Ledger already gave, reconstruct it from its trace alone, "
        "and count how many required fields are missing."
    ),
    brief=(
        "The team instruments Ledger and the dashboards light up. Latency holds "
        "steady, token counts flow in by model, and the error rate sits near zero "
        "across thousands of questions a day. By every number the team tracks, the "
        "system looks healthy. Then a quarterly review turns up a distribution "
        "Ledger said the covenants permitted and they did not. Somebody asks "
        "why Ledger answered that way for this borrower in March. Nobody on the "
        "team can answer from the trace alone.",
        "The gap is not a missing dashboard. The OpenTelemetry GenAI semantic "
        "conventions are the emerging standard for instrumenting these systems. They "
        "define exactly what a span normally records. That list holds the operation "
        "name, the agent id, the model name, the tool name, token counts, and "
        "duration. Every one of those fields describes volume and health. None of "
        "them names the clauses the retriever returned, the amendment version that "
        "was operative, or the exact model build that produced one answer.",
        "The conventions go further, and for good reason. Three attributes would "
        "carry the prompt and the tool arguments: gen_ai.input.messages, "
        "gen_ai.output.messages, and gen_ai.tool.call.arguments. Each one carries a "
        "warning that it is likely to hold personal data. The specification says "
        "instrumentation should not capture this content by default, and should only "
        "turn it on when a team opts in.",
        "That default is correct for privacy and it creates the exact trap this "
        "lender walks into. Borrower documents are confidential, so leaving content "
        "capture off is the obvious call. The team follows the convention, passes its "
        "own privacy review, and still has no record of which clauses the model read "
        "when it answered. Compliant with the privacy standard and "
        "unable to answer the examiner are not opposites. A team can hold both at "
        "once without noticing until an auditor asks.",
        "This is not a hypothetical worry for lenders. The Institute of "
        "International Finance (IIF) and EY ran a survey together. Their "
        "October "
        "2025 IIF-EY Annual "
        "Survey Report on AI Use in Financial Services asked 61 institutions what "
        "concerns them most about agentic systems. Model drift led at 69 percent. "
        "Second, at 55 percent, was the inability to explain how one specific agent "
        "action took place. Among firms already running these systems, that is the "
        "number two named risk, not a corner case.",
        "Model risk guidance written for ordinary statistical models makes the same "
        "point without mentioning AI at all. The Federal Reserve and the Office of "
        "the Comptroller of the Currency wrote the guidance known as SR "
        "(Supervision and Regulation) letter 11-7. It says "
        "documentation must give enough detail for an unfamiliar reader to follow how "
        "a model operates, its limits, and its key assumptions. A trace that only the "
        "engineer who built Ledger can interpret fails that bar before an AI "
        "model ever enters the picture. The examiner reading it is the unfamiliar "
        "reader the guidance has in mind.",
        "The detection is cheap and it does not need the running system. Pick one "
        "answer Ledger already gave and reconstruct it from its trace alone. Use no "
        "access to the system and no conversation with the person who built it. Fix "
        "a short list "
        "of required fields: the model version, the prompt version, and the tool "
        "inputs. Add the retrieved document identifiers, the policy or threshold that "
        "applied, and the identity that asked. Count how many of "
        "those fields the trace actually carries.",
        "That count turns a claim into a number. Saying Ledger is observable "
        "because the dashboard is full is an assertion. Saying 34 percent of the "
        "required fields are present across 30 completed actions is a measurement. "
        "Saying that not one of the 30 is fully reconstructable is another.",
        "Capture "
        "model and prompt versions, retrieved clause identifiers, and the asking "
        "identity outside the raw-content opt in. Do that before an audit finds "
        "the gap. A newer model will have replaced the one that answered in March "
        "before anybody asks about it. Its trace is all that is left.",
    ),
    builds_on=(
        "Every unit before it. An audit is the claim that those "
        "measurements actually happened, on the system in front of you. "
        "The trace is the only thing that can support that claim."
    ),
    probes=(
        Probe(
            id="dashboard-does-not-answer-why",
            asks=(
                "A dashboard shows steady latency, token counts broken out by model, "
                "and a 0.2 percent error rate across ten thousand Ledger questions "
                "this week. A quarterly review disputes one covenant answer Ledger "
                "gave. What does the dashboard establish about answering why that "
                "one answer came out the way it did?"
            ),
            choices=(
                Choice("a", "It proves Ledger is observable enough to answer the question"),
                Choice("b", "It shows the system is healthy by volume and says nothing about any single answer's inputs or operative clauses"),
                Choice("c", "It proves the trace captured the exact prompt and the clauses the retriever returned"),
                Choice("d", "Nothing, since a dashboard has no relationship to an audit question"),
            ),
            answer="b",
            because=(
                "A healthy dashboard and an answerable decision are different claims. "
                "Latency, token counts, and error rate describe Ledger in "
                "aggregate across many questions, and none of them applies to one "
                "answer. A single answer needs other fields, such as the clauses the "
                "retriever returned or the identity that asked. None of those fields "
                "show up on a volume dashboard. A dashboard is still useful, so the "
                "extreme answer that it tells you nothing goes too far in the other "
                "direction."
            ),
        ),
        Probe(
            id="content-capture-default",
            asks=(
                "A compliance reviewer asks whether Ledger's trace captures the "
                "exact prompt and tool arguments by default. Ledger follows the "
                "OpenTelemetry GenAI semantic conventions. What does the "
                "specification actually say?"
            ),
            choices=(
                Choice("a", "Ledger captures content by default, so the question is already answered"),
                Choice("b", "The specification requires content capture for any system that touches borrower data"),
                Choice("c", "Content attributes carry a sensitive-data warning, and instrumentation should not capture them by default, only on opt in"),
                Choice("d", "The specification leaves the default position undefined"),
            ),
            answer="c",
            because=(
                "The relevant attributes are gen_ai.input.messages, "
                "gen_ai.output.messages, and gen_ai.tool.call.arguments. Each one "
                "carries a note that it is likely to hold personal data. The "
                "specification states that instrumentation should not capture them by "
                "default and should offer an opt in instead. A team that never flips "
                "that opt in is following the specification correctly and still "
                "cannot show an examiner which clauses the model read."
            ),
        ),
        Probe(
            id="ran-is-not-why",
            asks=(
                "A trace shows an execute_tool span for every step of one answer "
                "Ledger returned, each with a status of ok and a recorded duration. "
                "What has this established about the answer itself?"
            ),
            choices=(
                Choice("a", "The tools ran and finished without error, and nothing here says which clauses, amendment version, or asking identity produced the answer"),
                Choice("b", "The answer is fully auditable, since the trace logs every tool call in the chain"),
                Choice("c", "Ledger checked the asker's entitlement, because it checks entitlement before any tool runs"),
                Choice("d", "The answer used the current model version, since the trace is recent"),
            ),
            answer="a",
            because=(
                "A span with status ok records that a function call completed. It "
                "does not record the arguments the model chose or which amendment "
                "the retriever pulled. It does not record who asked for the answer, "
                "unless a separate field carries each of those. Treating a clean run "
                "of tool spans as proof of an auditable answer is the exact "
                "confusion this unit exists to break."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of 30 completed actions from the same "
            "lender's servicing agent, each a full trace of spans. For every trace, "
            "check whether each of the 6 required audit fields in fixture_note is "
            "present anywhere in its spans. Compute the share of all 180 checks, 30 "
            "traces times 6 fields, that come back present, and post that number."
        ),
        fixture_path="fixtures/agent_traceability/action_traces.json",
        fixture_note=(
            "30 traces, each a completed action such as a fee waiver or a credit "
            "limit increase. They come from the servicing agent next to Ledger "
            "rather than Ledger itself, because an examiner wants the same field "
            "list either way. Each one carries a list of spans, "
            "and a field can "
            "appear on any span, so merge all span attributes before you check one "
            "trace. The 6 required fields are model version "
            "(gen_ai.response.model_version), prompt version (app.prompt.version), "
            "and tool inputs (gen_ai.tool.call.arguments). The other 3 are the "
            "retrieved document identifiers, "
            "the policy or threshold that applied, and the identity that authorized "
            "the action. Those three use the keys app.retrieval.document_ids, "
            "app.policy.threshold_applied, and app.identity.authorized_by."
        ),
        starter=(
            'import json\n'
            '\n'
            'fixture = json.load(open("fixtures/agent_traceability/action_traces.json"))\n'
            'traces = fixture["traces"]\n'
            '\n'
            'required_keys = [\n'
            '    "gen_ai.response.model_version",\n'
            '    "app.prompt.version",\n'
            '    "gen_ai.tool.call.arguments",\n'
            '    "app.retrieval.document_ids",\n'
            '    "app.policy.threshold_applied",\n'
            '    "app.identity.authorized_by",\n'
            ']\n'
            '\n'
            '# For each trace, merge every span\'s attributes into one dict, then count\n'
            '# how many of required_keys show up in it. Sum that across all 30 traces\n'
            '# and divide by 30 times len(required_keys).\n'
            'present = 0\n'
            'total = 0\n'
            '# ... your measurement here ...\n'
            'print(present / total)\n'
        ),
        metric="field_coverage_rate",
        expected=0.3444,
        tolerance=0.0005,
        because=(
            "62 of the 180 checks come back present, for a field coverage rate of "
            "0.3444. Look at the other side of that same count. Not one of the 30 "
            "traces carries all 6 required fields. So zero of 30 actions are fully "
            "reconstructable, even though every span in every trace reports a clean "
            "status of ok. Ledger can be free of errors by every metric on the "
            "dashboard and still unable to answer one why question. Health and "
            "auditability each rest on different fields entirely."
        ),
    ),
    sources=(
        "OpenTelemetry GenAI semantic conventions, gen-ai-spans.md, "
        "open-telemetry/semantic-conventions-genai repository (fetched 2026-10-29), "
        "on gen_ai.input.messages, gen_ai.output.messages, and gen_ai.tool.call.arguments "
        "carrying a sensitive-data warning and not being captured by default",
        "NIST (National Institute of Standards and Technology) AI 100-1, "
        "Artificial Intelligence Risk Management Framework (AI RMF 1.0), "
        "2023-01-26, Section 3.5, on explainable systems lending themselves to "
        "documentation, audit, and governance",
        "Federal Reserve and Office of the Comptroller of the Currency, SR 11-7, "
        "Supervisory Guidance on Model Risk Management, 2011-04-04, on documentation "
        "detailed enough for parties unfamiliar with a model to understand it",
        "IIF-EY Annual Survey Report on AI Use in Financial Services, 2025-10, 61 "
        "participating institutions, on the inability to explain how a specific agent "
        "action was generated ranking second among agentic AI risks at 55 percent",
    ),
)

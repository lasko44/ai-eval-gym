"""Unit 16: the trace that cannot answer why.

An agent trace that looks healthy by volume can still fail the one question a
regulator actually asks: why did the system take this specific action, for
this specific customer. Monitoring and an audit trail are different things,
and a team can have the first without the second. Numbers and citations
verified against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


UNIT = Unit(
    slug="agent-traceability",
    number=16,
    title="The trace that cannot answer why",
    failure=(
        "The trace proves a tool ran. It does not record which inputs the model saw "
        "or which policy applied. It does not record which identity authorized the "
        "action. Nobody can explain one specific decision after the fact."
    ),
    detection=(
        "Pick one completed action, reconstruct it from its trace alone, and count how "
        "many required fields are missing."
    ),
    brief=(
        "A team instruments an agent and the dashboards light up. Latency holds steady, "
        "token counts flow in by model, and the error rate sits near zero across "
        "thousands of calls a day. By every number the team tracks, the system looks "
        "healthy. Then a customer disputes one fee the agent waived, and somebody asks "
        "why the agent did that for this customer on this day. Nobody on the team can "
        "answer from the trace alone.",
        "The gap is not a missing dashboard. The OpenTelemetry GenAI semantic "
        "conventions are the emerging standard for instrumenting these systems. They "
        "define exactly what a span normally records. That list holds the operation "
        "name, the agent id, the model name, the tool name, token counts, and "
        "duration. Every one of those fields describes volume and health. None of "
        "them names the policy that applied or the exact model build that produced "
        "one decision.",
        "The conventions go further, and for good reason. Three attributes would "
        "carry the prompt and the tool arguments: gen_ai.input.messages, "
        "gen_ai.output.messages, and gen_ai.tool.call.arguments. Each one carries a "
        "warning that it is likely to hold personal data. The specification says "
        "instrumentation should not capture this content by default, and should only "
        "turn it on when a team opts in.",
        "That default is correct for privacy and it creates the exact trap a bank "
        "walks into. A team can follow the convention and leave content capture off. "
        "It can pass its own privacy review. It can still have no record of what the "
        "model saw when it made one decision. Compliant with the privacy standard and "
        "unable to answer the regulator are not opposites. A team can hold both at "
        "once without noticing until an auditor asks.",
        "This is not a hypothetical worry for banks. The October 2025 IIF-EY Annual "
        "Survey Report on AI Use in Financial Services asked 61 institutions what "
        "concerns them most about agentic systems. Model drift led at 69 percent. "
        "Second, at 55 percent, was the inability to explain how one specific agent "
        "action took place. Among firms already running these systems, that is the "
        "number two named risk, not a corner case.",
        "Model risk guidance written for ordinary statistical models makes the same "
        "point without mentioning AI at all. The Federal Reserve and the Office of "
        "the Comptroller of the Currency wrote the guidance known as SR 11-7. It says "
        "documentation must give enough detail for an unfamiliar reader to follow how "
        "a model operates, its limits, and its key assumptions. A trace that only the "
        "engineer who built the system can interpret fails that bar before an AI "
        "model ever enters the picture.",
        "The detection is cheap and it does not need the running system. Pick one "
        "completed action and reconstruct it from its trace alone. Use no access to "
        "the agent and no conversation with the person who built it. Fix a short list "
        "of required fields: the model version, the prompt version, and the tool "
        "inputs. Add the retrieved document identifiers, the policy or threshold that "
        "applied, and the identity that authorized the action. Count how many of "
        "those fields the trace actually carries.",
        "That count turns a claim into a number. Saying a system is observable "
        "because the dashboard is full is an assertion. Saying 34 percent of the "
        "required fields are present across 30 completed actions is a measurement. "
        "Saying that not one of the 30 is fully reconstructable is another. Capture "
        "model and prompt versions, policy decisions, and authorizing identities "
        "outside the raw-content opt in, rather than waiting for an audit to find the "
        "gap.",
    ),
    probes=(
        Probe(
            id="dashboard-does-not-answer-why",
            asks=(
                "A dashboard shows steady latency, token counts broken out by model, "
                "and a 0.2 percent error rate across ten thousand agent calls this "
                "week. A customer disputes one fee waiver the agent approved. What "
                "does the dashboard establish about answering why that one action "
                "happened?"
            ),
            choices=(
                Choice("a", "It proves the system is observable enough to answer the question"),
                Choice("b", "It shows the system is healthy by volume and says nothing about any single decision's inputs or policy"),
                Choice("c", "It proves the trace captured the exact prompt and the policy that applied"),
                Choice("d", "Nothing, since a dashboard has no relationship to an audit question"),
            ),
            answer="b",
            because=(
                "A healthy dashboard and an answerable decision are different claims. "
                "Latency, token counts, and error rate describe the system in "
                "aggregate across many calls, and none of them applies to one action. "
                "A single decision needs other fields, such as the policy that "
                "applied or the identity that authorized it. None of those fields "
                "show up on a volume dashboard. A dashboard is still useful, so the "
                "extreme answer that it tells you nothing goes too far in the other "
                "direction."
            ),
        ),
        Probe(
            id="content-capture-default",
            asks=(
                "A compliance reviewer asks whether your agent trace captures the "
                "exact prompt and tool arguments by default. The system follows the "
                "OpenTelemetry GenAI semantic conventions. What does the "
                "specification actually say?"
            ),
            choices=(
                Choice("a", "The system captures content by default, so the question is already answered"),
                Choice("b", "The specification requires content capture for any system that touches customer data"),
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
                "cannot show a regulator what the model saw."
            ),
        ),
        Probe(
            id="ran-is-not-why",
            asks=(
                "A trace shows an execute_tool span for every step of one approved "
                "transaction, each with a status of ok and a recorded duration. What "
                "has this established about the decision behind the transaction?"
            ),
            choices=(
                Choice("a", "The tools ran and finished without error, and nothing here says which inputs, policy, or authorization produced the decision"),
                Choice("b", "The decision is fully auditable, since the trace logs every tool call in the chain"),
                Choice("c", "The system authorized the decision, because it checks authorization before any tool runs"),
                Choice("d", "The decision used the current model version, since the trace is recent"),
            ),
            answer="a",
            because=(
                "A span with status ok records that a function call completed. It "
                "does not record the arguments the model chose or the policy the "
                "system checked. It does not record who signed off on the result, "
                "unless a separate field carries each of those. Treating a clean run "
                "of tool spans as proof of an auditable decision is the exact "
                "confusion this unit exists to break."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of 30 completed agent actions, each a full "
            "trace of spans. For every trace, check whether each of the 6 required "
            "audit fields in fixture_note is present anywhere in its spans. Compute "
            "the share of all 180 checks, 30 traces times 6 fields, that come back "
            "present, and post that number."
        ),
        fixture_path="fixtures/agent_traceability/action_traces.json",
        fixture_note=(
            "30 traces, each a completed bank-agent action such as a fee waiver or a "
            "credit limit increase. Each one carries a list of spans, and a field can "
            "appear on any span, so merge all span attributes before you check one "
            "trace. The 6 required fields are the model version, the prompt version, "
            "and the tool inputs. The other 3 are the retrieved document identifiers, "
            "the policy or threshold that applied, and the identity that authorized "
            "the action. Their exact attribute keys are gen_ai.response.model_version, "
            "app.prompt.version, and gen_ai.tool.call.arguments for the first three "
            "fields. The other three use app.retrieval.document_ids, "
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
            "status of ok. A system can be free of errors by every metric on the "
            "dashboard and still unable to answer one why question. Health and "
            "auditability each rest on different fields entirely."
        ),
    ),
    sources=(
        "OpenTelemetry GenAI semantic conventions, gen-ai-spans.md, "
        "open-telemetry/semantic-conventions-genai repository (fetched 2026-10-29), "
        "on gen_ai.input.messages, gen_ai.output.messages, and gen_ai.tool.call.arguments "
        "carrying a sensitive-data warning and not being captured by default",
        "NIST AI 100-1, Artificial Intelligence Risk Management Framework (AI RMF 1.0), "
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

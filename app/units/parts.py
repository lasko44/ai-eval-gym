"""The six parts of the course, in the order you take them.

The order is not a filing system. Each part names what it needs from the part
before it, and that sentence is the argument for where it sits. A part that
cannot say what it builds on has not earned its place, and the order should
change rather than the sentence.

The arc follows the path a request travels. You start by fixing the instrument,
because every later measurement is read through it. Then retrieval, then what
the retrieved text does to the answer, then the agent loop around both, then
what the whole thing costs to serve, then the things a regulated lender has to
prove about it.

`role_asks` describes what the target roles expect of each part. The postings
themselves are not stored in this repository, so these are descriptions rather
than quotations.

The target is a hands-on staff or senior engineer on a fintech AI platform
team, drawn from three real postings: a staff engineer owning an AI control
plane (gateway, agent runtime, retrieval, evaluation and cost), a staff
engineer designing evaluation frameworks for non-deterministic systems at
scale, and a staff engineer owning an eval platform beside its cost telemetry.

An earlier version of this file was written against a Director posting at a
bank. That source was right about the domain and wrong about the level: it
asked for fleet right-sizing and cross-team architecture, which is not the job
being trained for here. The domain stayed, the altitude dropped.
"""

from app.units.types import Part

PARTS: tuple[Part, ...] = (
    Part(
        slug="measurement",
        number=1,
        title="Trust your measurement first",
        purpose=(
            "Make the instrument honest before you point it at anything. A "
            "biased grader and a test you can stop early will both hand you a "
            "number that feels earned and is not."
        ),
        builds_on=(
            "Nothing. This part comes first because every number in the five "
            "parts after it is read through the habits you build here."
        ),
        role_asks=(
            "Eval dataset design",
            "Judge scoring, and showing the judge itself is stable",
            "Regression gates in continuous integration",
            "Evaluation frameworks for non-deterministic systems at scale",
            "Experimentation",
        ),
    ),
    Part(
        slug="retrieval",
        number=2,
        title="Retrieval: can Ledger even reach the right clause",
        purpose=(
            "Find out whether the documents that answer the question reach the "
            "model at all, and what the index paid to put them there."
        ),
        builds_on=(
            "Part 1. Recall at k and queries per second are both measurements, "
            "and both are easy to report at the one setting that flatters them."
        ),
        role_asks=(
            "Chunking, embedding and indexing pipelines",
            "Vector and search backends, and the unified retrieval layer "
            "over them",
            "Retrieval as one component of an AI control plane, measured "
            "separately from the rest",
        ),
    ),
    Part(
        slug="context",
        number=3,
        title="Context: what the retrieved text does to the answer",
        purpose=(
            "Retrieval can succeed and still make the answer worse. Measure "
            "what the model does with the passage once it has it."
        ),
        builds_on=(
            "Part 2. You cannot tell a context problem from a retrieval "
            "problem until you can measure whether retrieval worked."
        ),
        role_asks=(
            "Context engineering",
            "Structured outputs that survive a long prompt",
            "Retrieval-augmented generation, judged on the answer rather "
            "than on the retrieval",
        ),
    ),
    Part(
        slug="agents",
        number=4,
        title="Agents: loops, routing, and the cost of autonomy",
        purpose=(
            "An agent decides when to retrieve and when to try again. Both "
            "decisions get scored against the wrong baseline, and both spend "
            "money while nobody is watching."
        ),
        builds_on=(
            "Parts 2 and 3. An agent is a loop around retrieval and "
            "generation, so its failures read as retrieval failures until you "
            "can measure each layer on its own."
        ),
        role_asks=(
            "Agentic systems, tool calling, and Model Context Protocol "
            "server and client integrations",
            "Model routing, and the agent runtime the routing sits inside",
            "Observability deep enough to explain an agent's decisions, not "
            "just its outputs",
        ),
    ),
    Part(
        slug="serving",
        number=5,
        title="Serving: what it costs and how it feels",
        purpose=(
            "Price the thing per unit of work it delivers, and report the "
            "latency a real user waits through rather than the average."
        ),
        builds_on=(
            "Part 4. Cost per resolved request needs a resolution rate, and "
            "the agent loop is where the unresolved requests come from."
        ),
        role_asks=(
            "The gateway: multi-provider routing, failover, caching, rate "
            "limiting and token optimisation",
            "Cost allocation and chargeback, attributed to the use case "
            "rather than to the model",
            "Usage telemetry a finance team can read",
            "Latency and throughput as a person experiences them",
        ),
    ),
    Part(
        slug="governance",
        number=6,
        title="Risk, fairness and audit",
        purpose=(
            "What a regulated lender has to prove, and the measurements that "
            "let you prove it instead of asserting it."
        ),
        builds_on=(
            "All five parts. Every claim here is a claim about a system you "
            "can already measure. Nothing in this part works as an opinion."
        ),
        role_asks=(
            "Role-based access control, agent identity, and least-privilege "
            "access to enterprise data",
            "Audit logging good enough to answer why, not only whether",
            "Multi-layer safety architectures, measured rather than asserted",
            "Responsible AI: fairness metrics, evaluation protocols and audit "
            "readiness",
        ),
    ),
)

BY_SLUG = {part.slug: part for part in PARTS}


def get(slug: str) -> Part | None:
    return BY_SLUG.get(slug)

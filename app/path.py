"""The career path: the job, the skills it names, and where you are on each.

A course organised by system layer tells you what to read next. It does not
tell you what you are becoming able to do, and it cannot answer the question
somebody actually opens this with: how far am I from that job.

So the top of the app is the path. The job comes first, then the postings it
is drawn from, then the skills those postings name, and under each skill the
units that teach it. The six parts still group the content, because the order
of the reading is a real argument. They are no longer the thing a reader
meets first.

Three things this file refuses to do, because each would make the page a
sales pitch rather than a map.

It does not invent a skill. Every `Skill.name` here is already in
`parts.py:role_asks`, drawn from a real posting, and a test holds the two to
each other.

It does not claim coverage it does not have. A skill with no unit yet says so
and stays on the page, because what is missing is as much a part of an honest
map as what is finished.

It does not merge the postings into an average. They are listed separately
with their own bands, so a reader can see which one is reachable rather than
a blended number none of them pays.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Posting:
    """One real job advert the course is built against."""

    employer: str
    title: str
    band: str
    asks_for: str
    source: str


POSTINGS: tuple[Posting, ...] = (
    Posting(
        employer="Fanatics Commerce",
        title="Staff Software Engineer, AI/ML Platform",
        band="190,000 to 237,500 dollars base, plus equity",
        asks_for=(
            "Owns the whole control plane: gateway, agent runtime, retrieval, "
            "evaluation and cost. Names eval dataset design, tracing, judge "
            "scoring and regression testing as required skills, and asks for "
            "8 years with 2 on an AI platform."
        ),
        source="job-boards.greenhouse.io/fanaticscommerce/jobs/4398095009",
    ),
    Posting(
        employer="Plaid",
        title="Staff Software Engineer, AI Integrations",
        band="not posted",
        asks_for=(
            "Designs evaluation frameworks that measure correctness, "
            "reliability and safety for non-deterministic systems at scale, "
            "and builds the observability to debug them. Asks for 8 years."
        ),
        source="jobs.fintech.io/companies/plaid/jobs/82247882",
    ),
    Posting(
        employer="SoFi",
        title="Staff Software Engineer, AI Developer Experience",
        band="not posted",
        asks_for=(
            "Owns the eval platform beside the cost telemetry: usage "
            "reporting, cost allocation and chargeback. Asks for a bachelor's "
            "degree and 3 to 4 years, the lowest bar of the three."
        ),
        source="zapply.jobs/jobs/83c8b15f-55f0-494a-bc74-2bdb48705580",
    ),
)

JOB_TITLE = "Staff engineer on a fintech AI platform team"
JOB_SUMMARY = (
    "Hands-on, not a director. The common thread across all three postings is "
    "evaluation: designing the eval set, scoring with a judge you have shown "
    "to be stable, gating a release on it, and tracing a regression to the "
    "component that caused it. Everything else they ask for hangs off that."
)


@dataclass(frozen=True)
class Skill:
    """One thing a posting asks you to be able to do.

    `units` names the units that teach it. An empty tuple is honest rather
    than embarrassing: it says the course does not cover this yet, and the
    page says so in those words.
    """

    name: str
    part: str
    units: tuple[str, ...] = field(default_factory=tuple)


# Every name below appears in parts.py role_asks. The mapping from skill to
# units is the authored part: a part groups units by the order you read them,
# and a skill groups them by what they make you able to do, which is a
# different cut of the same 22 units.
SKILLS: tuple[Skill, ...] = (
    Skill("Judge scoring, and showing the judge itself is stable",
          "measurement", ("judges",)),
    Skill("Experimentation",
          "measurement", ("experiment-discipline", "sample-size")),
    Skill("Eval dataset design",
          "measurement", ("eval-contamination", "sample-size", "feedback-loop")),
    Skill("Regression gates in continuous integration",
          "measurement", ("release-gates",)),
    Skill("Evaluation frameworks for non-deterministic systems at scale",
          "measurement", ("release-gates", "tracing")),

    Skill("Chunking, embedding and indexing pipelines",
          "retrieval", ("reranking",)),
    Skill("Vector and search backends, and the unified retrieval layer over them",
          "retrieval", ("index-tradeoff",)),
    Skill("Retrieval as one component of an AI control plane, measured separately from the rest",
          "retrieval", ("multi-hop",)),

    Skill("Context engineering",
          "context", ("context-rot",)),
    Skill("Retrieval-augmented generation, judged on the answer rather than on the retrieval",
          "context", ("stale-docs",)),
    Skill("Structured outputs that survive a long prompt",
          "context", ()),

    Skill("Model routing, and the agent runtime the routing sits inside",
          "agents", ("routing",)),
    Skill("Agentic systems, tool calling, and Model Context Protocol server and client integrations",
          "agents", ("retry-loops",)),
    Skill("Observability deep enough to explain an agent's decisions, not just its outputs",
          "agents", ("tracing", "agent-traceability")),

    Skill("The gateway: multi-provider routing, failover, caching, rate limiting and token optimisation",
          "serving", ("gateway",)),
    Skill("Latency and throughput as a person experiences them",
          "serving", ("latency-tails",)),
    Skill("Cost allocation and chargeback, attributed to the use case rather than to the model",
          "serving", ("inference-economics", "cost-attribution")),
    Skill("Usage telemetry a finance team can read",
          "serving", ("cost-attribution",)),

    Skill("Role-based access control, agent identity, and least-privilege access to enterprise data",
          "governance", ("permissions",)),
    Skill("Multi-layer safety architectures, measured rather than asserted",
          "governance", ("guardrails",)),
    Skill("Responsible AI: fairness metrics, evaluation protocols and audit readiness",
          "governance", ("fairness-metrics",)),
    Skill("Audit logging good enough to answer why, not only whether",
          "governance", ("agent-traceability",)),
)


def progress(session, curriculum, progression) -> list[dict]:
    """Every skill with the units that teach it and how far along they are.

    A skill counts as earned when every unit that teaches it is mastered,
    which is the same bar the rest of the app uses: every prediction
    committed and a detection that matched. Being right is not the bar,
    because it is not the bar anywhere else either.
    """
    part_unlocked = {
        state["part"].slug: state["unlocked"]
        for state in progression.part_states(session, curriculum.COURSE)
    }

    rows = []
    for skill in SKILLS:
        units = [curriculum.get(slug) for slug in skill.units]
        units = [unit for unit in units if unit is not None]
        states = [progression.unit_progress(session, unit) for unit in units]
        done = sum(1 for state in states if state.mastered)
        rows.append({
            "skill": skill,
            "units": list(zip(units, states)),
            "done": done,
            "total": len(units),
            "covered": bool(units),
            "earned": bool(units) and done == len(units),
            "unlocked": part_unlocked.get(skill.part, False),
        })
    return rows


def summary(rows: list[dict]) -> dict:
    """The one line at the top: how many of the job's skills you can claim."""
    covered = [row for row in rows if row["covered"]]
    return {
        "earned": sum(1 for row in covered if row["earned"]),
        "covered": len(covered),
        "total": len(rows),
        "uncovered": len(rows) - len(covered),
    }

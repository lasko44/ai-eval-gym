# Curriculum map: Director, AI Engineer

The posting names a technical surface. This file maps each line of it to a unit
that trains the matching detection skill, and marks what exists today.

One honest note first. The role asks for eight years of AI and ML work plus
three years of people leadership. The gap is years and leadership, not
knowledge, and no curriculum closes that. The posting is still the best
syllabus available, because it states what a senior AI engineer is expected to
measure. Treat it as the target for the skills, not for the application.

## The course order

The order is by system layer, not by the posting's own sequence. Each part
names what it needs from the part before it, and that sentence lives in
`app/units/parts.py` next to the part itself. `tests/test_course_order.py`
holds the numbering to it: units run 1 upward with no gaps, and they never
leave a part and come back.

| Part | Units | What the role asks for |
| --- | --- | --- |
| 1. Trust your measurement first | 01 judges, 02 experiment discipline | Model evaluation. Experimentation. |
| 2. Retrieval: can the right context even be reached | 03 reranking, 04 index tradeoff, 05 multi-hop | Similarity search and vector databases. Model evaluation. |
| 3. Context: what the retrieved text does to the answer | 06 context rot, 07 stale documents | Model evaluation. |
| 4. Agents: loops, routing, and the cost of autonomy | 08 routing, 09 retry loops | Agentic AI systems and workflows. Observability. |
| 5. Serving: what it costs and how it feels | 10 inference economics, 11 latency tails | Large language model inference. Right-sizing models, instance counts and hardware types. Foundation model optimization. |
| 6. Risk, fairness and audit | 12 permissions, 13 guardrails, 14 fairness metrics, 15 agent traceability | Guardrails. Responsible AI. Observability and governance. |

## Why the order is what it is

**Part 1 comes first** because every number in the five parts after it is read
through the habits built there. A biased grader and a test somebody can stop
early both produce a number that feels earned and is not.

**Part 2 before part 3** because a context problem and a retrieval problem look
identical until you can measure whether retrieval worked at all.

**Part 4 after parts 2 and 3** because an agent is a loop around retrieval and
generation. Its failures read as retrieval failures until each layer can be
measured on its own.

**Part 5 after part 4** because cost per resolved request needs a resolution
rate, and the agent loop is where unresolved requests come from.

**Part 6 last** because every claim in it is a claim about a system you can
already measure. Nothing there works as an opinion.

## Still to build

Five units are named on the syllabus page and not written. Each needs primary
sources before it ships.

| Would be | Part | What it would train |
| --- | --- | --- |
| Model documentation and audit readiness | 6 | A completeness check against a fixed schema, scored, so a gap is a number rather than a feeling. |
| Build versus buy | 4 or 6 | A decision scored against stated criteria rather than preference. |
| Fine tune against prompt against retrieval | 3 | The three approaches measured on one task, at one cost. |
| Third-party model validation | 6 | Research already in this repository reports this as a policy that 58 percent have and 32 percent execute. |
| Override criteria for an agent | 4 | Research already in this repository reports 19 percent of surveyed banks have not written these down at all. |

One more is worth its own shape: the widely repeated claim that 95 percent of
AI pilots fail. It comes from a 2025 MIT Media Lab Project NANDA report, The
GenAI Divide: State of AI in Business. Secondary write-ups disagree about its
sample, and MIT later restricted access to the report. Nobody here has read the
primary document, so nothing quotes a figure from its methodology. Taking it
apart uses the same muscle as a retrieval pipeline, but the exercise is a
document critique rather than a measurement, so it needs a different kind of
check from the units above.

# Curriculum map: Director, AI Engineer (Capital One IFX)

The posting names a technical surface. This file maps each line of it to a unit
that trains the matching detection skill, and marks what exists today.

One honest note first. The role asks for eight years of AI and ML work plus
three years of people leadership. The gap is years and leadership, not
knowledge, and no curriculum closes that. The posting is still the best
syllabus available, because it states what a senior AI engineer is expected to
measure. Treat it as the target for the skills, not for the application.

## What the posting asks for, and what covers it

| The posting says | Unit | State |
| --- | --- | --- |
| Model evaluation | 01 judges | built |
| Model evaluation | 02 reranking | built |
| Model evaluation | 03 context rot | built |
| Model evaluation | 04 stale documents | built |
| Guardrails | 09 guardrails | built |
| Similarity search and VectorDBs | 02 reranking, partly | partial |
| Observability | 08 retry loops, partly | partial |
| Agentic AI systems and workflows | 08 retry loops, partly | partial |
| LLM inference | 10 inference economics | to build |
| Right-size models, instance counts, hardware types, given context length and token counts | 10 inference economics | to build |
| Foundation model optimization: scalability, cost, latency, throughput | 11 latency tails | to build |
| Similarity search and VectorDBs | 12 index tradeoff | to build |
| Experimentation | 13 experiment discipline | to build |
| Responsible AI: fairness metrics | 14 fairness metrics conflict | to build |
| Responsible AI: evaluation protocols, documentation, audit readiness | 15 model documentation | to build |
| Observability, and governance | 16 agent action traceability | to build |
| High judgment build versus buy decisions | 17 build versus buy | to build |

## The six units to build first

Each one trains a measurement that a Director would expect a senior engineer to
run without being asked.

**10. Inference economics.** A team reports cost per call and calls the system
cheap. Cost per call hides batch size, context length and the ratio of input to
output tokens. The detection is cost per resolved request, measured across
several batch sizes and context lengths. The posting names this almost word for
word: right-size models, instance counts and hardware types given context
length, token inputs and token outputs.

**11. Latency tails.** A team reports mean latency. The mean hides the tail, and
a customer feels the tail. The detection is p50, p95 and p99 reported together,
with the load that produced them.

**12. Index tradeoff.** A team picks an index and reports recall. Recall alone
hides what the index cost in queries per second. The detection is a recall
against throughput curve across index parameters, and the knee named.

**13. Experiment discipline.** A team watches an A/B test and stops it when it
looks good. That inflates the false positive rate. The detection is a sample
size fixed in advance, and a measurement of how often repeated looks produce a
false win.

**14. Fairness metrics conflict.** A bank must show a model is fair. Demographic
parity, equalized odds and calibration cannot all hold at once when base rates
differ between groups. The detection is all three computed on the same
predictions, with the conflict shown rather than hidden. This one matters most
for a lender, and the conflict is a mathematical result, not an opinion.

**15. Model documentation and audit readiness.** A reviewer asks what data
trained a model, what it was tested on, and who approved it. The detection is a
completeness check against a fixed schema, scored, so a gap is a number rather
than a feeling.

**16. Agent action traceability.** A regulator asks why one agent action
happened. The detection is reconstruction from the trace alone, and a count of
what the trace does not carry. Research already in this repository puts this at
55 percent of surveyed banks naming it as a problem.

## After those

17. Build versus buy, scored against stated criteria rather than preference.
18. Fine tune against prompt against retrieval, measured on one task.
19. Third-party model validation, which research in this repository reports as a
    policy that 58 percent have and 32 percent execute.
20. Override criteria for an agent, which 19 percent of surveyed banks have not
    written down at all.

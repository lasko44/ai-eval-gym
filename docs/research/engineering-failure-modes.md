# Production LLM failure modes, with detection methods
Recon 2026-10-28. Source: technical/engineering agent. Citations verified by that agent
against primary sources except where flagged. Kept because the numbers cannot be
reconstructed from memory and the design doc needs them.

## Candidate curriculum units (failure mode -> detection skill)

| # | Failure mode | Key number | Detection |
| --- | --- | --- | --- |
| 1 | Single-vector embedding capacity ceiling | 512d breaks ~500K docs; 1024d ~4M; 4096d ~250M | recall@k vs corpus size, query set fixed |
| 2 | No reranker | top-20 failure 5.7% -> 1.9% with full stack | recall@150 vs recall@5; gap names the fault |
| 3 | Chunks unintelligible without doc context | contextual embeddings -35% failure | sample 50 chunks, can a human answer from chunk alone |
| 4 | Retrieval coverage unmeasurable | Re:CAP recovers 9-29% gold docs BM25 misses | adversarial coverage audit; track recoverable-but-not-retrieved |
| 5 | Context rot | 18/18 models degrade; 1 distractor measurable; 20-40% drop 300tok vs 113k | sweep context length, answer chunk fixed |
| 6 | Stale-document poisoning | flips 30-37% of correct answers; 66-75% with "follow the context" | knowledge-reversal set, ask with and without retrieval |
| 7 | Query rewriting degrades well-formed queries | -9.0% nDCG@10 on FiQA, +5.1% TREC-COVID | A/B vs raw query, segmented by intent, never aggregate |
| 8 | Coverage illusion + pre-retrieval routing fails | synthetic says 90% need LLM aug, real logs say 27.8%; router at 13.4% of 33.6% oracle | same metric on synthetic vs real logs |
| 9 | Single-pass retrieval in multi-hop | -7.1 EM, 4x the reranker's -1.7 | segment eval set by hop count |
| 10 | Semantic cache poisoning | 91.6% / 80.2% / 30.0% attack success undefended | log matched cache key + similarity; shadow-eval diff job |
| 11 | Runaway retry loops | 63 incidents / 21 frameworks; root cause is ownership bugs | tokens per resolved task; monotonic context growth; cap at gateway |
| 12 | Indirect prompt injection via retrieved content | +32% malicious IPI content Nov25-Feb26 | index-time invisible-text scan; egress URL allowlist |
| 13 | ConfusedPilot / ACL above retrieval | n/a | diff retrieved chunk IDs across users, NOT answers |
| 14 | Guardrail evasion | up to 100% on 6 production systems | mutate blocked corpus; report bypass AND false-positive rate |
| 15 | LLM-as-judge reliability without validity | position bias 0.002-0.192; raw agreement overstates kappa by ~39pp | swap A/B, measure flip rate; report chance-corrected agreement |
| 16 | Citations that resolve but do not support | factual accuracy 24-77%; -42% as tool calls 2->150 | re-fetch cited span, entailment check; cap tool depth |
| 17 | Observability that exports PII | OTel GenAI makes content opt-in, off by default | can you reconstruct a bad answer from the trace alone |

## Primary sources
- arXiv:2508.21038 (2025-08-28) embedding capacity limit / LIMIT benchmark
- anthropic.com/news/contextual-retrieval (2024-09-19) reranking + contextual chunks table
- arXiv:2609.24122 (2026-09-21) Re:CAP retrieval coverage audit
- trychroma.com/research/context-rot (2025-07-14) 18 models, context degradation
- arXiv:2609.31342 (2026-09-25) stale-document poisoning, 317 knowledge reversals
- arXiv:2603.13301 (2026-03-02) query rewriting per-dataset degradation
- arXiv:2605.27220 (2026-05-26) coverage illusion, cost-ascending cascade beats router
- arXiv:2606.21553 (2026-06-19) component ablation, retrieval loop -7.1 EM
- arXiv:2609.35908 (2026-09-28) semantic cache poisoning
- arXiv:2606.04056 (2026-06-02) 63 budget-overrun incidents, 21 frameworks
- CSA research note (2026-04-26) indirect prompt injection in the wild
- arXiv:2408.04870 (2024-08-09) ConfusedPilot
- arXiv:2504.11168 (2025-04-15) guardrail evasion
- arXiv:2606.19544 (2026-06-17) 21 judges, 541k judgments
- arXiv:2605.06635 (2026-05-07) deep research citation accuracy
- arXiv:2401.05856 (2024-01-11) Seven Failure Points when engineering RAG
- hamel.dev/blog/posts/evals-faq (2026-09-18) eval practice, 60-80% time on error analysis

## The contradiction worth teaching
"95% of AI pilots fail" traces to MIT Project NANDA (July 2025): 52 executive interviews,
153 conference surveys, 300 public deployments, self-described "directionally accurate",
published by a group selling agentic infrastructure. Thesis is organizational. The 2026
engineering literature locates failures at instrumented, fixable layers instead. Believing
the first staffs change management; believing the second builds an eval harness.

## Do not repeat (agent could not verify)
"73% of RAG failures are retrieval"; "naive RAG wrong context ~40%"; the $47,218 weekend
agent incident; "3-7% of semantic cache hits return the wrong answer"; a16z observability
incident multiples; "55% of injection incidents are indirect". Blog claims, no primary source.

Real but secondary: Cursor support-bot incident (Apr 2025, incidentdatabase.ai/cite/1039),
the cleanest teaching case for a missing abstain-and-escalate path.

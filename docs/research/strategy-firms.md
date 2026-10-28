# Strategy firms: diagnosis vs prescription
Recon 2026-10-28, McKinsey / BCG / Bain / WEF agent.

## The correction that matters

**No consulting firm says AI deployments fail for engineering reasons.** All four say
organizational, several explicitly:

- Bain, Technology Report 2026 (2026-09-29): "The most prominent barriers to AI adoption
  today are organizational, not technical."
- BCG (2026-04-15): most health care AI has struggled to scale "not because of technology
  limitations" but because AI was layered onto unsuitable workflows.
- BCG 10/20/70: 10% of value from algorithms, 20% from data, 70% from operating model.
- McKinsey (2026-08): security and risk concerns lead, "well ahead of regulatory
  uncertainty or technical limitations."
- WEF agents playbook (2026-05): "The answer is not primarily technical. It is
  organizational."

**Two things save the premise anyway, and the curriculum must use this framing:**

1. When these reports say "not technical" they almost always mean **"not model quality."**
   They are right about that, and it is not the claim the gym rests on.
2. **Every one of them then specifies software.** WEF turns "authorization" into
   enforcement points, IAM-scoped tool access, policy-as-code checkpoints, rate limits,
   versioned evaluation evidence. BCG calls its red-teaming and privilege-escalation
   problems "solvable engineering problems."

**The defensible line: their diagnosis is organizational, their prescription is
architectural, and here is the architecture they specify.** Claiming the firms blame
engineering is citing them against themselves, and a reader who checks will catch it.

One real exception: **telecom**, where Bain's own diagnosis is technical debt.

## The two best sentences in the corpus

- "Risk in agent deployments is often architectural rather than purely model-driven. The
  same underlying agent can present different risk profiles depending on orchestration,
  tools access, memory and the gating of consequential events." (WEF, 2026-05)
- "For most health systems building toward an AI-first future, the AI is the easy part of
  the technical challenge. The data foundation is the hard part... the data foundation is
  where most programs fail silently." (BCG, 2026-05)

## Prescribed architecture, which is the curriculum

1. **Release gates with numeric thresholds.** ServiceNow requires 80-95% task completion
   before go-live. BforeAI promotes a challenger only when it beats production and clears
   >90%. WEF: "evaluation evidence must be versioned and attributable to a specific system
   configuration," with a regression baseline tied to that configuration.
2. **Grounding verified as a pipeline stage**, not assumed. A Quality Evaluator Agent
   rejects and re-plans on "lack of factual grounding" (BCG + Google Cloud, 2026-01).
3. **Cost measured per accepted task, not per token.** "A model can cost 80% less per call
   and still lose money if it triples failure-rate or sends more work to human reviewers"
   (Bain, 2026-09-29). Full measure includes model spend, tool and runtime costs, retries
   and human review.
4. **Routing to the smallest sufficient model.** AT&T at 8 billion tokens a day; super
   agents routing to smaller domain models gave 90% cost reduction and 3x throughput
   (Bain, 2026-09-29).
5. **Intent recognition as its own component**, separate from the handler.
6. **Agents permissioned as first-class principals**, with intent as a fourth IAM
   dimension beyond principal/resource/action (BCG, 2026-05).
7. **Guardrails enforced structurally, because prompts are overridable.** BCG, 2026-05:
   "Instructions embedded in a model's configuration can be manipulated or overridden by
   adversarial inputs; structural controls enforced by the platform cannot."
8. **Agent registry, conflict detection, decommissioning.** "Unregistered agents do not
   run in production." Pilot agents never formally concluded keep running.
9. **Observability means reconstructing a decision end to end**: knowledge sources, tools,
   checkpoints, approvals, outcome.
10. **Human escalation as a designed path carrying state.** Bain: most agents "operate
    episodically, losing context between sessions."

## Caveats, important
- **Every McKinsey figure is search-summary sourced.** mckinsey.com timed out on every
  fetch. The valuable one, a bank gating at accuracy >=80% and run-to-run consistency
  >=70%, was never read at source. Verify before citing.
- **bain.com returned 403 on every path.** Only Technology Report 2025 was read in full.
  Roughly half the Bain dates are search-engine relative ages.
- BCG HTML and PDF assets were read directly; those quotes are solid. The banking PDF
  (2026-01) is Indonesia-scoped; its architecture generalizes, its statistics do not.
- WEF `reports.weforum.org` PDFs were read directly and are the strongest primary material.
- **No firm publishes a regulated accuracy threshold.** Every numeric gate found is one
  company's own choice. These are the wrong sources for that.

## Domain recommendation
Primary: **financial crime compliance** (AML/KYC/transaction monitoring), the only domain
where all four converge and where published release gates exist.
Regulated counterpart: **health care provider operations**. Bain's sharpest number is
provider clinical workflows at 2.9x ROI with only 4% autonomous, against revenue cycle
management at 67% autonomous. That gap is where grounding and escalation are unsolved.

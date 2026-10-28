# AI Eval Gym: design

Status: draft for approval. Date: 2026-10-28. Working name.

## The shape, in one page

Matt can build AI systems. He cannot yet stand next to one and say where it breaks,
what it costs, and what he would fix first. That is the gap this closes.

The mechanism is a **teardown cycle**, repeated:

1. A real AI system, written by someone else, in whatever language it is in.
2. Matt reads it and writes a **sealed prediction**: where it fails, and how confident
   he is in each call. Sealed means timestamped and not editable afterwards.
3. He builds a small evaluation harness that measures the thing he predicted.
4. He runs it and gets a number.
5. The system scores his prediction against the measurement and updates a running
   calibration score.
6. He publishes the teardown, with the numbers in it.

The sealed prediction is the whole design. Dunning-Kruger is a calibration problem, and
calibration only moves when a guess is committed before the answer is known. Everything
else in this project exists to make step 2 happen honestly and step 5 happen
automatically.

He writes **evaluation code, not application code**. That is a much smaller surface than
building pipelines, and it is the thing the market is currently short of.

## Intent, and the why

The stated problem, in his words: "I have built a lot of things but don't know if I can
accurately evaluate their strengths, weaknesses, shortcomings, risks, improvements. I am
not a SME. I feel like I am in the Dunning-Kruger effect right now."

Two things follow that are easy to get wrong:

- **More building does not fix this.** He has shipped GEOSource, the merik agents,
  merik-cms, SlideCrisp, Strut and household-docs. A sixth system teaches the same
  lesson the first five did. The missing reps are evaluative, not constructive.
- **A sandbox built FOR him reproduces the problem.** He opened this conversation saying
  "you did everything, I could not explain it." If this project ships as a polished
  platform he did not build and cannot explain, it has failed on its own terms, however
  well it works.

The resolution: Claude builds the gym, Matt builds the muscle. The scaffolding,
the scoring, the storage and the UI are Claude's. Every prediction, every eval harness
and every teardown writeup is Matt's, and none of it is generated for him.

## Prior art and current state

- `~/Projects/ai-foundations` (June 2026): an *AI Foundations* deck he built and
  presented. It covers next-token prediction, context as a flat token sequence, prompts
  as prefixes that bias a distribution, tool use as text in and text out, agents as
  loops, pretraining versus post-training, and failure modes. **This establishes that the
  conceptual foundations are already in place.** The curriculum therefore starts at
  detection and measurement, and teaches no fundamentals.
- Seven years of Laravel. His own read is that this caps him. The design's read is that
  the cap is not the language: it is seven years of problems that had a known-correct
  answer, where "does it work" was a yes or no. AI systems are probabilistic and "is this
  good" is a measurement. The habit is the cap, not the syntax.
- MCP and developer-workflow standardization at his day job. Relevant because the first
  cycle should pay off there.

## Goals

1. **Calibration becomes a number that moves.** His predicted failure modes converge with
   measured ones over cycles, and the convergence is visible as a score.
2. **A public artifact per cycle**, each reading as "this person can evaluate systems,"
   which is a rarer and more senior signal than "this person built a chatbot."
3. **Transfer to his current job**, starting with cycle 01.
4. **Fluency reading AI systems across stacks**, since the material is other people's
   code in other people's languages.

## Non-goals

- Teaching Python syntax. He will read and write Python; learning the language is not an
  objective and no time is budgeted for it.
- Building production RAG applications from scratch. He writes harnesses, not pipelines.
- A course, a video library, or anything consumed passively.
- Hunting a market opportunity. He raised consulting white papers as a source of
  material; that is what they are used for here. The business-idea version of that is a
  separate project, deliberately deferred.

## Anti-goals

These would mean failure even if the software works:

- **He ends up with a gym he cannot explain.** The original failure, reproduced.
- **It becomes a content treadmill.** Reading papers and feeling productive without a
  single committed prediction is the failure mode this design is most exposed to.
- **Claude writes the predictions or the teardowns.** The artifacts are worthless, to him
  and to a hiring manager, if they are not his.
- **Teardowns that are opinion without measurement.** A portfolio of critique with no
  numbers reads as a commentator, not an engineer.
- **Calibration score that only goes up.** If the scoring is generous it is decorative.
  It must be able to tell him he was badly wrong, in a way that stings.

## Constraints

- **Python 3.12, FastAPI, Postgres with pgvector, pytest, OpenTelemetry.** Postgres
  because he already knows it from Strut.
- **No LangChain, no LlamaIndex.** Frameworks are what let someone ship a system they
  cannot explain. Where the gym needs retrieval internals, they are written out.
- Solo, evenings and weekends. No hard deadline, but he wants to be interviewing before
  long, so early cycles must produce something showable.
- Must be useful at his current job, not only for interviews.
- House rules apply: real-path tests, branch per change, no em dashes, integer cents if
  money ever appears.

## The curriculum

The units come from the engineering literature rather than from a syllabus. Research
notes with full citations are in `docs/research/engineering-failure-modes.md`. Each unit
is one failure mode paired with its detection method, which is the skill being trained.

Representative units, with the numbers that make them real:

| Unit | Failure | Detection skill |
| --- | --- | --- |
| Reranking | top-20 retrieval failure 5.7% falls to 1.9% with the full stack | report recall at two values of k; the gap names the fault |
| Stale documents | superseded evidence flips 30-37% of correct answers, 66-75% when told to follow context | build a knowledge-reversal set, ask with and without retrieval |
| Routing | a production router captured 13.4% of a 33.6% oracle ceiling | compare the same metric on synthetic versus real logged queries |
| Multi-hop | removing the retrieval loop costs -7.1 EM, four times the reranker | segment the eval set by hop count |
| Judges | position bias 0.002 to 0.192; raw agreement overstates kappa by ~39pp | swap A/B order, measure flip rate, report chance-corrected agreement |
| Permissions | ACLs are checked above retrieval, so the prompt has already escaped the check | diff retrieved chunk IDs across users, never answers |
| Context | all 18 frontier models degrade with length; one distractor is measurable | sweep context length with the answer chunk fixed |
| Abstention | the Cursor support bot invented a policy because it had no way to decline | measure abstention rate and treat zero as an incident |

A ninth unit is the one with the most career leverage and it is not technical:
**the "95% of AI pilots fail" claim** traces to 52 executive interviews and
conference-floor surveys, self-described by its authors as directionally accurate, and
published by a group selling the remedy. Learning to take that apart, and to notice that
the engineering literature locates failures somewhere else entirely, is the same muscle
as taking apart a retrieval pipeline.

## The premise, corrected by the research

The obvious framing for this project would be "AI pilots fail, learn why." That framing is
stale. Accenture (2026-05-26) has 64% past pilots into production; Deloitte (2026-01-21)
has 25% of organizations running 40% or more of their pilots in production, against 5% a
year earlier; KPMG (2026-09-24) has 62% building or deploying agents.

The accurate 2026 problem is narrower and better: **shipped agents are running ahead of the
controls around them.** IBM/IBV (2026-06-08, 2,000 C-level executives across 33
geographies) reports 77% saying adoption outpaces governance, two-thirds of CIOs and CTOs
accountable for systems they do not fully control, and an average of 54 agent incidents a
year requiring human correction, 17% of them taking four hours or more to contain and 37%
causing data exposure.

That is an engineering problem, and it is exactly the kind of thing a person who can
evaluate systems gets hired to fix.

**One honesty constraint on how this is described.** The strategy firms do not say
deployments fail for engineering reasons. Bain's 2026 Technology Report says the opposite
in plain words: "The most prominent barriers to AI adoption today are organizational, not
technical." What they are ruling out when they say "technical" is almost always *model
quality*, and they are right about that. But every one of them then prescribes software:
policy-as-code checkpoints, IAM-scoped tool access, agent registries, versioned evaluation
evidence, structural guardrails. BCG calls its own red-teaming and privilege-escalation
problems "solvable engineering problems."

So the line this project uses, and the one a teardown may claim, is: **their diagnosis is
organizational, their prescription is architectural, and here is the architecture they
specify.** Claiming the firms blame engineering would be citing them against themselves,
and a reader who checks would catch it. Research notes: `docs/research/strategy-firms.md`.

## The domain for practice material

Research notes are in `docs/research/industry-domains.md`.

**Health plan prior authorization is the best practice ground found**, because CMS turned
the workflow into pass/fail requirements with a clock on them:

- Standard decisions within 7 calendar days, expedited within 72 hours, effective
  2026-01-01.
- From 2026-03-31, plans must publicly report average turnaround time plus denial, appeal
  and overturn rates.
- **Denials may only be made by licensed clinicians.** The model may approve; it may never
  deny.

That last line is a hard routing boundary with a legal consequence, which is the single
most useful shape a practice problem can have. The work underneath it is retrieval over a
policy corpus, a deterministic rule check, mandatory escalation, published metrics, and
HIPAA-constrained permission-aware retrieval. Nothing about it is invented.

Banking is the second domain, and supplies the richest named failure modes: 69% of
financial institutions name model drift the top agentic risk, 55% name inability to explain
how a specific action was generated, and on overrides, 40% fire when a confidence score
falls below a limit while **19% have no formal criteria at all**.

**One cycle must be a data problem.** Accenture (2026-05-26) puts only 7% of companies at
the data readiness needed to scale, with 72% lacking trusted data of the right quality. A
curriculum that is all prompt-and-eval would miss what actually blocks deployment.

## The first build is a thin slice of the real GUI

An earlier draft had cycle 01 running by hand in markdown. Matt rejected that: "I do not
want this to be a doc, I need interactive projects through a GUI, I do not learn through a
doc." He is right, and the rejection is recorded here because the reasoning behind the
original call still applies.

That reasoning: the largest risk in this project is Claude building a platform Matt never
opens. The markdown spike was a cheap way to test the loop before committing to the build.

The replacement keeps the risk control without the markdown. **The first build is a
working vertical slice of the real interface, sized to run exactly one teardown cycle end
to end, and nothing more.** One cycle, one sealed prediction, one harness run, one score,
one published teardown. No unit library, no calibration curve, no multi-cycle views.

The gate stays, it just moves: the rest of the platform is built after cycle 01 has run
through the slice and he says the loop was worth repeating.

## The platform, once the first cycle earns it

A local FastAPI application with a plain web UI that holds:

- **Cycles.** Target system, the question under test, current stage.
- **Sealed predictions.** Written before measurement, timestamped, immutable after
  sealing. Confidence recorded per claim so scoring can be probabilistic.
- **Harness runs.** The eval code he wrote, its output, the measured numbers.
- **Scoring.** Prediction against measurement, producing a Brier score so overconfidence
  and underconfidence are distinguishable. A running calibration curve across cycles.
- **Units.** The curriculum above, each with symptom, detection method and primary
  sources. The "quizzes" he asked for live here, and they are calibration probes with
  confidence attached, not trivia.
- **Teardowns.** The published writeup per cycle, exportable.

## Decisions made during the builder check

These were gaps a reviewing engineer found. They are Claude's calls, not Matt's, and are
marked as such so he can overrule any of them on reading.

**A prediction is a claim, a probability, and its own falsification test.** At seal time
each claim must name the metric and the number that would make it false: not "this breaks
on multi-hop queries" but "recall@5 is below 0.50 on the multi-hop slice, 70% confident."
This is what makes step 5 automatic and what stops generous grading. A sealed claim the
harness never measures scores as **unresolved**, counts against a coverage metric, and
never counts as correct. Vague claims are therefore self-punishing, which is the point.

**Sealing is a hash chain committed to git.** Each sealed prediction is hashed into an
append-only table, and the hash is committed. Commit history makes the ordering externally
checkable, so a reader does not have to take his word that the prediction predated the
measurement. A local row he could edit would prove nothing to anyone but himself.

**Claude ships a shared eval library; Matt writes the per-cycle harness.** Metric
implementations (recall@k, nDCG, Brier, judge flip rate), dataset loaders and a run
harness are scaffolding and are Claude's. The per-cycle harness that decides what to
measure and how is Matt's. Claude may review and debug his harness code. Claude never
writes a prediction or a teardown, and never suggests what the answer is before he seals.

**The platform itself is held to the anti-goal.** It stays small, and every module gets a
short written walkthrough. A gym he cannot explain fails on its own terms even if it runs.

**Gold labels are Matt's work, not generated.** Eval sets for cycle 02 come from public
CMS and LCD material, never synthesized, and he writes the labels by hand. The practice
literature puts 60-80% of eval development time in error analysis and hand annotation of
at least 30 traces, and the research notes already record what happens when a synthetic
set stands in for real traffic: synthetic said 90% of queries needed augmentation, real
logs said 27.8%. Hand labelling is not overhead here, it is the exercise.

**Probe calibration and teardown calibration are scored separately.** Unit probes are
cheap and numerous, teardown claims are few and expensive; pooling them would produce a
headline number that is mostly a quiz score. Both are shown, teardown calibration leads,
and no curve is displayed until 20 claims have resolved.

**The manual cycle gets templates only.** For cycle 01 Claude produces a prediction
template, a sealing convention and a scoring rubric, all markdown. No application code
before the gate clears.

## What is left to the builder

- UI specifics beyond "plain and fast."
- Exact schema.
- Which repositories seed the cycles after the first two.
- How harnesses are sandboxed when running third-party code.
- Whether teardowns publish to a static site or somewhere else.

## Cycle order

1. **Cycle 01: an open-source AI repository.** A real RAG or agent project on GitHub.
   Chosen over a work system because it is publishable immediately, keeps employer code
   and data off external APIs entirely, and is genuinely someone else's code, so a
   prediction about it is a prediction rather than a memory. The first portfolio artifact
   therefore lands at the end of cycle 01 rather than cycle 02.
2. **Cycle 02: prior authorization.** The hard-requirements domain above.
3. **Cycle 03: a data problem**, per the Accenture caution.

## Models and spend

**Anthropic API on Matt's own key, hard ceiling $50 per month, enforced inside the gym.**

The cap is enforced at the gym's own gateway, per request and per session, not as an
instruction in a prompt. The research notes catalogue 63 production budget-overrun
incidents across 21 orchestration frameworks whose root causes were ownership bugs letting
cost-bearing values escape their controls; a cap that lives in a prompt is advice, not a
limit. The gym tracks tokens per resolved task and alarms on monotonic context growth,
because a monthly spend dashboard cannot catch something that bills out over a weekend.

A frontier model was chosen over a local one so measured numbers stay comparable to the
cited literature. A teardown that says "recall@5 was 0.42" means something next to
published figures only if it was measured against a comparable model.

## Still Matt's to decide, before the first publish

**Does the published teardown include the misses and the running calibration score?**
Claude's recommendation is yes: a badly wrong call followed by the correction is the
senior signal, and a teardown showing only hits reads as marketing. But this is a
reputation decision and his alone. It changes the export format and whether publishing
needs per-claim redaction, so it must be answered before cycle 01 publishes, not before
building starts.

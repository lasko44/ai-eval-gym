# Industry domains with checkable requirements
Recon 2026-10-28, Big Four / Accenture / IBM IBV agent. All free/public.
Every PwC item in the source report was flagged unverified (PwC returns 403 to automated
fetch), so nothing from PwC is used here.

## The premise correction that matters most

"AI pilots never reach production" was true for 2024 and early 2025 and is stale for 2026.
- Accenture, 2026-05-26: 64% have moved beyond pilots into production across multiple
  functions or started enterprise-wide efforts.
- Deloitte, 2026-01-21 (3,235 leaders, 24 countries): 25% have moved 40%+ of pilots into
  production, 54% expect to within 3-6 months. A year earlier only 5% had scaled 70%+.
- KPMG, 2026-09-24: 62% building or deploying agents, up from 53% a quarter earlier.

**The honest 2026 framing: shipped agents are running ahead of the controls around them.**
- IBM/IBV 2026-06-08 (2,000 C-level, 33 geographies): 77% say adoption outpaces governance;
  two-thirds of CIOs/CTOs accountable for systems they do not fully control; only 11%
  ready for the next year's agent scale. Average 54 agent incidents needing human
  correction per year; 17% high severity (4+ hours to contain); 37% caused data exposure;
  33% cascading failures.
- Deloitte 2026-01-21: ~75% plan agentic AI within two years, only 21% have a mature
  governance model.
- Accenture 2025: 74% paused at least one AI project over risk concerns.

This is a MORE engineering-shaped problem, not less. It is the right premise for the gym.

## Domain 1: Health plan prior authorization (best hard-requirement source)

CMS Interoperability and Prior Authorization Final Rule gives pass/fail requirements:
- Standard decisions within **7 calendar days** (down from 14). Expedited **72 hours**.
  Effective 2026-01-01.
- From **2026-03-31**, plans must publicly report average turnaround time plus denial,
  appeal and overturn rates.
- **"Denials will only be made by licensed clinicians."** AI is augmentation only. A lack
  of clinical evidence identified by AI is not a valid reason for denial.

Why this is near-perfect practice material: the model may approve but may never deny, so
there is a hard, testable routing boundary; the work is RAG over a policy corpus plus a
deterministic rule check; there is an SLA clock; and the metrics are ones you must publish.
HIPAA applies, so permission-aware retrieval is not optional.

Adoption: 70% of health plans prioritize utilization management, prior auth and claims.
Source: Deloitte 2026-01-15, Deloitte 2026-02-11.

## Domain 2: Banking and capital markets (richest named failure modes)

- Model drift / behavioral shift: **69%** name it the top agentic risk (IIF-EY 2025-10-16).
- Inability to explain how a specific action was generated: **55%**. Not model
  explainability in the abstract, tracing one agent action.
- Third-party model validation gap: **58%** have a policy requiring full internal-standard
  review of vendor models, only **32%** can confirm they execute it.
- Override triggers, with the distribution: conflicts with regulation 52%, risk threshold
  exceeded 47%, **confidence or quality score below limit 40%**, business judgment 24%,
  and **19% have no formal criteria at all** (KPMG Banking Q2 2026).
- Cost visibility: only **31%** of banks say AI operating costs are fully visible.
- Deloitte prescribes the observability primitives by name: unique agent IDs, output
  tagging, immutable tool-use logs, real-time monitoring, continuous permission checks,
  and detection of prompt injection or instruction tampering.

## Domain 3: Insurance (a regulator writing your model registry spec)

NAIC Big Data and AI Working Group is building an AI systems evaluation tool, four
exhibits: A quantifies models new/updated/retired, B governance, C high-risk models,
D data collection and review. Pilot with state departments planned 2026. Insurers remain
fully responsible for third-party data and models. Source: EY NAIC Bulletin 2026-01-29.

Exhibit A is a model registry with lifecycle state. C is per-model risk tiering. D is
dataset provenance. Four buildable artifacts with a named consumer.

## Domain 4: EU AI Act high-risk

Obligation list: risk management system, data governance, quality management and technical
documentation, transparency/accuracy/cybersecurity, information to deployers, human
oversight, and **automatically generated logs over the system lifetime**. Technical
documentation must describe datasets including origin, characteristics and preprocessing.

**Timeline slipped.** Annex III high-risk obligations moved from 2026-08-02 to
**2027-12-02** under the AI Omnibus (Deloitte UK 2026-06-01). A lot of secondary writing
still says August 2026 and is wrong.

## The caution to design around

Both Accenture and Deloitte put the bottleneck at **data, not modeling or serving**.
Accenture 2026-05-26: only **7%** of companies are data-ready to scale advanced AI, 72%
lack trusted data of the right quality with standardized governance, 80%+ delay or alter
AI initiatives over data risk. KPMG APAC health: "data readiness, not model quality,
determines impact."

**Design consequence: exercises that are all prompt-and-eval with no data plumbing will
not match what actually blocks deployment.** At least one cycle must be a data problem.

## Primary sources
- EY/IIF Global Bank Risk Management Survey, 2026-02
- 2025 IIF-EY Annual Survey on AI Use in Financial Services, 2025-10-16
- KPMG AI Quarterly Pulse, Banking Q2 2026 (fielded 2026-04-28 to 05-25, 204 US C-suite)
- KPMG Q3 2026 AI Pulse, 2026-09-24
- Deloitte, Managing the new wave of risks from AI agents in banking, 2026-03-05
- Deloitte UK, Agentic AI in Banking: Building the Auditable Bank, 2026-08-31
- Deloitte, AI Could Help Health Plans Simplify Prior Auth, 2026-01-15
- Deloitte, health care agentic adoption, 2026-02-11
- Deloitte UK, The AI Omnibus, 2026-06-01
- EY NAIC Bulletin Fall 2025 update, 2026-01-29
- IBM/IBV with Oxford Economics, 2026-06-08 and EMEA study 2026-10-14
- Accenture, AI-ready data, 2026-05-26

## Do not repeat
All PwC figures (403 on fetch, search-summary only). The "95% of pilots fail" number is
not IBM's; IBM attributes it to the MIT report and its own figures are ~25% of initiatives
delivering expected ROI and 16% scaled enterprise-wide.

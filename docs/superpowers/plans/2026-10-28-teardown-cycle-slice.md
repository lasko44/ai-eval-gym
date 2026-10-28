# Teardown Cycle Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local web app that runs one teardown cycle end to end: create a cycle, seal predictions before measuring, record harness results, get scored against those predictions, and publish the teardown.

**Architecture:** FastAPI serving server-rendered Jinja2 templates, no JS build step, backed by Postgres via SQLAlchemy. Predictions are sealed with a hash chain whose head is committed to git, so ordering is externally checkable. Scoring resolves each sealed claim against a measured metric value and produces a Brier score. The app makes no model calls itself; a capped client is provided for the user's harness code to import.

**Tech Stack:** Python 3.13, FastAPI, Jinja2, SQLAlchemy, Postgres, pytest, httpx, Anthropic SDK.

**Spec:** `docs/superpowers/specs/2026-10-28-ai-eval-gym-design.md`

## Environment (verified 2026-10-28)

- Postgres 17 at `127.0.0.1:5432`, user `matthewlaszkiewicz`, no password. Binaries are at
  `/opt/homebrew/opt/postgresql@17/bin`, which is NOT on the default PATH; prepend it.
- Databases `ai_eval_gym` and `ai_eval_gym_test` already exist.
- `DATABASE_URL` default: `postgresql+psycopg://matthewlaszkiewicz@127.0.0.1:5432/ai_eval_gym`,
  and the test database is the same URL with `_test` appended to the database name.
- Repository is already a git repo on branch `feat/teardown-cycle-slice`. Do not re-init.
- No `uv`. Use `python3.13 -m venv .venv` and pip.

## Global Constraints

- Python 3.13 (the only interpreter on this machine; the spec's 3.12 is a floor, not a pin). No LangChain, no LlamaIndex, at any point.
- No em dash (U+2014) in any file, including comments, templates and commit messages.
- Server-rendered HTML only. No frontend framework and no build step: the user must be able to read and explain every file in this app.
- Work happens on a branch off `main`, never on `main` directly.
- The app never writes a prediction, a claim or a teardown narrative on the user's behalf.
- Model spend ceiling is $50.00 per month, enforced in code before a request is sent, never as prompt text.
- Money and spend are integer cents (`*_cents`) throughout.

## Review Focus

- **Editing or deleting a claim after its cycle is sealed** must be refused, not silently applied. Pinned in Task 2.
- **A sealed claim whose metric never appears in any harness run** must score as `unresolved` and must never count as correct. Pinned in Task 5.
- **A probability of exactly 0.0 or 1.0** must score without a division error and must produce the maximum penalty when wrong. Pinned in Task 5.
- **Sealing with no git repository, or with the seal file already dirty,** must fail loudly before any database write, so a seal is never recorded without its commit. Pinned in Task 2.
- **A spend request that would cross the monthly ceiling** must raise before the API call, and a request arriving with no recorded month must not be treated as zero spent and allowed through. Pinned in Task 7.

---

### Task 1: Project skeleton and cycle creation

**Files:**
- Create: `pyproject.toml`, `app/__init__.py`, `app/db.py`, `app/models.py`, `app/main.py`, `app/templates/base.html`, `app/templates/cycles.html`, `app/templates/cycle.html`
- Test: `tests/test_cycles.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `app.models.Cycle` with columns `id: int`, `target_name: str`, `target_url: str`, `question: str`, `stage: str` (one of `open`, `sealed`, `measured`, `scored`), `created_at: datetime`, `sealed_at: datetime | None`. `app.db.get_session() -> Session`. FastAPI app object `app.main.app`. Routes `GET /`, `POST /cycles`, `GET /cycles/{id}`.

- [ ] **Step 1: Write the failing test**

```python
def test_create_cycle_then_see_it_on_its_page(client):
    r = client.post("/cycles", data={
        "target_name": "llama_index_rag_demo",
        "target_url": "https://github.com/example/repo",
        "question": "Is retrieval any good on multi-hop questions?",
    }, follow_redirects=True)
    assert r.status_code == 200
    assert "llama_index_rag_demo" in r.text
    assert "multi-hop" in r.text

def test_new_cycle_starts_open(client, session):
    client.post("/cycles", data={"target_name": "x", "target_url": "u", "question": "q"})
    assert session.query(Cycle).one().stage == "open"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cycles.py -v`
Expected: FAIL, no module named `app`.

- [ ] **Step 3: Implement the skeleton**

`app/db.py` exposes an engine built from `DATABASE_URL` and `get_session()`. `app/models.py` defines `Cycle` as above. `app/main.py` mounts Jinja2 templates and implements the three routes; `POST /cycles` redirects to `GET /cycles/{id}`. `conftest.py` provides `client` (httpx against the app) and `session` fixtures against a test database, with tables created and dropped per test.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cycles.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml app tests conftest.py
git commit -m "feat: create a teardown cycle and view it"
```

---

### Task 2: Claims and sealing

**Files:**
- Create: `app/sealing.py`, `app/templates/predict.html`
- Modify: `app/models.py`, `app/main.py`
- Test: `tests/test_sealing.py`

**Interfaces:**
- Consumes: `Cycle` from Task 1.
- Produces: `app.models.Claim` with `id: int`, `cycle_id: int`, `text: str`, `metric: str`, `comparator: str` (one of `lt`, `lte`, `gt`, `gte`), `threshold: float`, `probability: float`, `sealed_hash: str | None`. `app.sealing.seal_cycle(session, cycle_id) -> str` returning the chain head hash. `app.sealing.SealError`. Routes `POST /cycles/{id}/claims`, `POST /cycles/{id}/seal`.

- [ ] **Step 1: Write the failing tests**

```python
def test_claim_requires_a_falsification_test(client, cycle):
    r = client.post(f"/cycles/{cycle.id}/claims", data={
        "text": "retrieval is bad on multi-hop", "metric": "", "comparator": "lt",
        "threshold": "", "probability": "0.7"})
    assert r.status_code == 422

def test_sealing_chains_each_claim_hash(session, cycle_with_two_claims):
    head = seal_cycle(session, cycle_with_two_claims.id)
    claims = session.query(Claim).order_by(Claim.id).all()
    assert all(c.sealed_hash for c in claims)
    assert claims[1].sealed_hash != claims[0].sealed_hash
    assert head == claims[-1].sealed_hash

def test_claims_are_immutable_once_sealed(client, sealed_cycle):
    r = client.post(f"/cycles/{sealed_cycle.id}/claims", data=VALID_CLAIM)
    assert r.status_code == 409

def test_seal_fails_loudly_and_writes_nothing_without_git(session, cycle_with_two_claims, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SealError):
        seal_cycle(session, cycle_with_two_claims.id)
    assert session.query(Claim).filter(Claim.sealed_hash.isnot(None)).count() == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_sealing.py -v`
Expected: FAIL, `seal_cycle` not defined.

- [ ] **Step 3: Implement `Claim` and `seal_cycle(session, cycle_id) -> str`**

Each claim's hash is `sha256` over the previous claim's hash plus the claim's own canonical fields, so reordering or editing breaks the chain. `seal_cycle` writes the head hash and timestamp to `seals/cycle-{id}.txt`, runs `git add` and `git commit`, and only then commits the database transaction; any git failure raises `SealError` and rolls back. The claim form rejects an empty `metric` or `threshold` with 422, which is what makes a vague prediction impossible to seal.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_sealing.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app tests seals
git commit -m "feat: seal claims into a git-committed hash chain"
```

---

### Task 3: Metrics library

**Files:**
- Create: `app/metrics/__init__.py`, `app/metrics/retrieval.py`, `app/metrics/calibration.py`, `app/metrics/judges.py`
- Test: `tests/test_metrics.py`

**Interfaces:**
- Produces: `recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float`, `precision_at_k(...) -> float`, `ndcg_at_k(retrieved: list[str], relevance: dict[str, float], k: int) -> float`, `brier_score(pairs: list[tuple[float, bool]]) -> float`, `flip_rate(first: list[str], swapped: list[str]) -> float`.

- [ ] **Step 1: Write the failing tests**

```python
def test_recall_at_k_counts_only_the_first_k():
    assert recall_at_k(["a", "b", "c"], {"a", "c"}, k=2) == 0.5

def test_recall_at_k_with_no_relevant_documents_is_zero_not_nan():
    assert recall_at_k(["a"], set(), k=1) == 0.0

def test_brier_score_of_a_confident_correct_call_is_zero():
    assert brier_score([(1.0, True)]) == 0.0

def test_brier_score_of_a_confident_wrong_call_is_one():
    assert brier_score([(1.0, False)]) == 1.0

def test_flip_rate_counts_disagreements_between_orderings():
    assert flip_rate(["A", "A", "B"], ["A", "B", "B"]) == pytest.approx(1 / 3)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_metrics.py -v`
Expected: FAIL, no module named `app.metrics`.

- [ ] **Step 3: Implement the five functions**

Pure functions, no database and no I/O. An empty relevant set returns 0.0 rather than raising or returning NaN, so a harness against an unlabelled slice degrades visibly instead of crashing.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_metrics.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/metrics tests/test_metrics.py
git commit -m "feat: add retrieval, calibration and judge metrics"
```

---

### Task 4: Harness run capture

**Files:**
- Create: `app/templates/run.html`
- Modify: `app/models.py`, `app/main.py`
- Test: `tests/test_runs.py`

**Interfaces:**
- Consumes: `Cycle` from Task 1.
- Produces: `app.models.HarnessRun` with `id`, `cycle_id`, `created_at`, `notes: str`, and `app.models.Measurement` with `id`, `run_id`, `metric: str`, `value: float`. Route `POST /cycles/{id}/runs` accepting a JSON body `{"notes": str, "measurements": {metric: value}}`.

- [ ] **Step 1: Write the failing tests**

```python
def test_posting_a_run_stores_each_measurement(client, sealed_cycle, session):
    r = client.post(f"/cycles/{sealed_cycle.id}/runs",
                    json={"notes": "first run", "measurements": {"recall_at_5": 0.42}})
    assert r.status_code == 201
    assert session.query(Measurement).one().value == 0.42

def test_a_run_moves_the_cycle_to_measured(client, sealed_cycle, session):
    client.post(f"/cycles/{sealed_cycle.id}/runs", json={"notes": "", "measurements": {"recall_at_5": 0.42}})
    session.refresh(sealed_cycle)
    assert sealed_cycle.stage == "measured"

def test_a_run_is_refused_before_sealing(client, cycle):
    r = client.post(f"/cycles/{cycle.id}/runs", json={"notes": "", "measurements": {"recall_at_5": 0.9}})
    assert r.status_code == 409
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_runs.py -v`
Expected: FAIL, 404 on the route.

- [ ] **Step 3: Implement the models and the route**

Refusing a run on an unsealed cycle is the mechanism that enforces predict-before-measure; it is a 409, not a redirect.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_runs.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app tests/test_runs.py
git commit -m "feat: record harness runs against a sealed cycle"
```

---

### Task 5: Scoring

**Files:**
- Create: `app/scoring.py`, `app/templates/score.html`
- Modify: `app/main.py`
- Test: `tests/test_scoring.py`

**Interfaces:**
- Consumes: `Claim` (Task 2), `Measurement` (Task 4), `brier_score` (Task 3).
- Produces: `app.scoring.resolve_claim(claim, measurements: dict[str, float]) -> str` returning `"correct"`, `"wrong"` or `"unresolved"`; `app.scoring.score_cycle(session, cycle_id) -> CycleScore` with fields `brier: float | None`, `resolved: int`, `unresolved: int`, `coverage: float`. Route `POST /cycles/{id}/score`.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_claim_whose_metric_was_never_measured_is_unresolved():
    claim = Claim(metric="recall_at_5", comparator="lt", threshold=0.5, probability=0.7)
    assert resolve_claim(claim, {"ndcg_at_10": 0.8}) == "unresolved"

def test_an_unresolved_claim_never_counts_as_correct(session, sealed_cycle_with_unmeasured_claim):
    score = score_cycle(session, sealed_cycle_with_unmeasured_claim.id)
    assert score.resolved == 0
    assert score.unresolved == 1
    assert score.brier is None

def test_coverage_is_the_share_of_claims_that_resolved(session, cycle_one_of_two_measured):
    assert score_cycle(session, cycle_one_of_two_measured.id).coverage == 0.5

def test_a_certain_claim_that_was_wrong_scores_the_maximum_penalty(session, cycle_certain_and_wrong):
    assert score_cycle(session, cycle_certain_and_wrong.id).brier == 1.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_scoring.py -v`
Expected: FAIL, no module named `app.scoring`.

- [ ] **Step 3: Implement `resolve_claim` and `score_cycle`**

`resolve_claim` looks the claim's metric up among the cycle's measurements, returning `"unresolved"` when absent, and otherwise applies the claim's comparator to its threshold. `score_cycle` computes the Brier score over resolved claims only, returns `None` when none resolved, and reports coverage as resolved over total.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_scoring.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app tests/test_scoring.py
git commit -m "feat: score sealed claims against measurements"
```

---

### Task 6: Teardown page

**Files:**
- Create: `app/templates/teardown.html`
- Modify: `app/main.py`
- Test: `tests/test_teardown.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `GET /cycles/{id}/teardown` rendering the cycle, and `GET /cycles/{id}/teardown.md` returning the same as markdown with `Content-Type: text/markdown`.

- [ ] **Step 1: Write the failing tests**

```python
def test_teardown_shows_each_claim_with_its_outcome_and_the_measured_number(client, scored_cycle):
    body = client.get(f"/cycles/{scored_cycle.id}/teardown").text
    assert "recall_at_5" in body and "0.42" in body and "wrong" in body

def test_teardown_shows_the_seal_hash_so_a_reader_can_check_the_commit(client, scored_cycle):
    assert scored_cycle.claims[-1].sealed_hash[:12] in client.get(f"/cycles/{scored_cycle.id}/teardown").text

def test_markdown_export_is_served_as_markdown(client, scored_cycle):
    r = client.get(f"/cycles/{scored_cycle.id}/teardown.md")
    assert r.headers["content-type"].startswith("text/markdown")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_teardown.py -v`
Expected: FAIL, 404.

- [ ] **Step 3: Implement both routes**

The page lists every claim with its probability, its falsification test, the measured value and its outcome, then the Brier score and coverage, then the seal hash. Claims scored `wrong` are shown, not hidden; whether the published copy includes them is the user's decision and is made by exporting or not exporting, not by the app filtering.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_teardown.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app tests/test_teardown.py
git commit -m "feat: render and export the teardown"
```

---

### Task 7: Capped model client

**Files:**
- Create: `app/llm.py`
- Modify: `app/models.py`
- Test: `tests/test_llm_budget.py`

**Interfaces:**
- Produces: `app.models.SpendLedger` with `id`, `month: str` (`YYYY-MM`), `spent_cents: int`. `app.llm.BudgetExceeded`. `app.llm.complete(prompt: str, *, model: str, max_tokens: int) -> str`, which estimates worst-case cost, refuses before calling when the ceiling would be crossed, and records actual usage after.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_request_that_would_cross_the_ceiling_raises_before_calling(session, monkeypatch):
    session.add(SpendLedger(month="2026-10", spent_cents=4990)); session.commit()
    called = []
    monkeypatch.setattr("app.llm._send", lambda *a, **k: called.append(1))
    with pytest.raises(BudgetExceeded):
        complete("hi", model="claude-sonnet-5", max_tokens=100_000)
    assert called == []

def test_a_month_with_no_ledger_row_is_created_not_assumed_zero(session):
    complete("hi", model="claude-sonnet-5", max_tokens=10)
    assert session.query(SpendLedger).filter_by(month=current_month()).one().spent_cents > 0

def test_actual_usage_is_recorded_after_the_call(session, fake_response_costing_cents(12)):
    complete("hi", model="claude-sonnet-5", max_tokens=10)
    assert session.query(SpendLedger).one().spent_cents == 12
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_llm_budget.py -v`
Expected: FAIL, no module named `app.llm`.

- [ ] **Step 3: Implement the ledger and `complete`**

The ceiling is `MONTHLY_CEILING_CENTS = 5000`, read from config. The check happens against the worst case (`max_tokens` all billed at output rate) before the request leaves, because a check against expected cost is not a cap. Spend is stored in integer cents.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_llm_budget.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/llm.py tests/test_llm_budget.py
git commit -m "feat: cap model spend before the request is sent"
```

---

### Task 8: End to end through the real path

**Files:**
- Test: `tests/test_full_cycle.py`

**Interfaces:**
- Consumes: every route above.

- [ ] **Step 1: Write the failing test**

```python
def test_one_whole_cycle_over_http(client):
    cid = create_cycle(client, "example/rag-demo", "Is multi-hop retrieval any good?")
    add_claim(client, cid, text="multi-hop recall is poor", metric="recall_at_5",
              comparator="lt", threshold=0.5, probability=0.7)
    add_claim(client, cid, text="reranking is absent so precision collapses",
              metric="precision_at_5", comparator="lt", threshold=0.3, probability=0.9)
    client.post(f"/cycles/{cid}/seal")
    assert client.post(f"/cycles/{cid}/claims", data=VALID_CLAIM).status_code == 409
    client.post(f"/cycles/{cid}/runs", json={"notes": "", "measurements": {"recall_at_5": 0.62}})
    client.post(f"/cycles/{cid}/score")
    body = client.get(f"/cycles/{cid}/teardown").text
    assert "wrong" in body        # predicted below 0.5, measured 0.62
    assert "unresolved" in body   # precision_at_5 was never measured
```

- [ ] **Step 2: Run it and fix whatever breaks**

Run: `pytest tests/test_full_cycle.py -v`
Expected: PASS once the route interactions line up. This test is the one that proves the slice, so it drives the real HTTP path and never calls internals directly.

- [ ] **Step 3: Commit**

```bash
git add tests/test_full_cycle.py
git commit -m "test: drive one whole teardown cycle over http"
```

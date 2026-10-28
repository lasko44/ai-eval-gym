# AI Eval Gym

A local, single-user web app for running **teardown cycles** against someone
else's AI system.

One cycle is four steps, in this order and no other:

1. **Predict.** Write falsifiable claims about where the target will fail.
   Each claim carries a metric, a comparator, a threshold and your own
   confidence from 0 to 1.
2. **Seal.** The claims are hashed into a chain, the chain head is written to
   `seals/cycle-<id>.txt`, and that file is committed to git before the
   database transaction commits. After this, the claims cannot be edited.
3. **Measure.** Your own evaluation harness runs and posts its numbers to the
   cycle.
4. **Score.** Every sealed claim is resolved against the measurements and the
   cycle gets a Brier score (calibration) plus coverage (how much of the
   prediction was actually tested).

The ordering is the whole point. A prediction committed before the answer is
known is the only kind that can move your calibration, which is why the seal
is a real git commit rather than a database flag.

Each module's docstring explains that module. This file covers the parts no
docstring can: how to install it, how to run it, and how to write the harness.

## Install

Python 3.13 and Postgres 17. No npm, no build step, no frontend framework:
the pages are server-rendered Jinja2 templates.

```sh
cd /Users/matthewlaszkiewicz/Projects/ai-eval-gym
python3.13 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## Database

Postgres is reached at `127.0.0.1:5432` as the local user, with no password.
**The Homebrew Postgres 17 binaries are not on `PATH`**, so reach for them by
full path or put them on `PATH` for the shell:

```sh
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
```

Two databases: `ai_eval_gym` for real work, `ai_eval_gym_test` for the test
suite. Create them once if they do not exist:

```sh
createdb -h 127.0.0.1 ai_eval_gym
createdb -h 127.0.0.1 ai_eval_gym_test
```

### Creating the schema

There is no migration tool. `app/initdb.py` is the whole of schema creation,
and it must be run once against each database before the app or the suite can
use it:

```sh
.venv/bin/python -m app.initdb
```

It prints the database it is about to create tables in, so read that line: a
run against the wrong database would otherwise succeed in exactly the same
silence as a correct one. It points at `ai_eval_gym` unless `DATABASE_URL`
says otherwise.

**Run it again whenever a model gains a column.** `create_all` adds missing
tables but will not alter an existing one, so a brand new column on an
existing table needs either a re-run against a dropped table or a hand-written
`ALTER TABLE`. The test database looks after itself: the `session` fixture in
`conftest.py` creates and drops every table around each test.

## Running the app

From the project root, always:

```sh
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open <http://127.0.0.1:8000/>.

### Two things about that command that are not conveniences

**Start it from the project root.** `app/sealing.py` resolves both git and the
`seals/` directory from the **process working directory**, deliberately, so
the caller decides which repository a seal lands in. Started from somewhere
else, a seal either commits into an unrelated repository or fails outright,
and the launch directory is therefore part of the integrity story rather than
a detail. The teardown page tells a reader to go and check a specific commit;
that commit has to be in this project's repository.

**Keep it bound to `127.0.0.1`.** There is no authentication anywhere in this
app, by design, because it is a single-user tool on one machine. Served on
`0.0.0.0`, anything on the local network could post a harness run into a
sealed cycle, and the measurement side of someone else's cycle is exactly what
must not be writable by someone else.

A related note on git: sealing is **refused on a detached HEAD**, because a
commit made there belongs to no branch and is lost at the next checkout. If
you have been reading an old version with `git checkout <sha>`, are part way
through a rebase, or are in the middle of a `git bisect`, check out a branch
before sealing.

## Writing a harness

A harness is your own Python script. It is not part of this app and this app
never writes one for you. It imports what it needs from `app`, measures
whatever it measures, and posts its results.

Two imports matter:

- `app.metrics` holds the pure measurement functions: `recall_at_k`,
  `precision_at_k`, `ndcg_at_k`, `brier_score`, `flip_rate`. No database, no
  I/O: plain data in, a number out.
- `app.llm.complete` is the **only** sanctioned way to call a model. It
  enforces a monthly spend ceiling (`MONTHLY_CEILING_CENTS`, $50.00 by
  default) in code, before any request leaves the process.

### A worked example

Save this as `harness.py` in the project root and run it with
`.venv/bin/python harness.py` while the app is running:

```python
import httpx

from app.db import get_session
from app.llm import complete
from app.metrics import recall_at_k

CYCLE_ID = 1  # the cycle whose prediction you have already sealed

session = get_session()
try:
    # Your own measurement. Nothing here touches the database.
    recall = recall_at_k(["doc-7", "doc-2", "doc-9"], {"doc-2", "doc-4"}, 5)

    # Every model call goes through complete(), never the SDK directly.
    verdict = complete(
        session,
        "Answer yes or no: did the answer use the second retrieved document?",
        model="claude-sonnet-5",
        max_tokens=16,
    )

    # Required. See "complete() does not commit" below.
    session.commit()
finally:
    session.close()

response = httpx.post(
    f"http://127.0.0.1:8000/cycles/{CYCLE_ID}/runs",
    json={
        "notes": f"recall_at_5 over 3 retrieved docs; judge said {verdict.strip()}",
        "measurements": {"recall_at_5": recall},
    },
)
response.raise_for_status()
print(response.json())
```

`POST /cycles/<id>/runs` is the one route a machine calls rather than a
browser, so it takes JSON rather than a form. It answers:

- **201** with the new run's id on success.
- **409** if the cycle is not `sealed` or `measured`. A run before the seal
  would break predict-before-measure, and a run after scoring would let you
  see the score and then adjust the measurement.
- **422** if any measured value is not a finite number. `NaN` and `Infinity`
  are refused by name: a `NaN` loses every comparison and a `-Infinity` or
  `Infinity` wins whole classes of them, so either one resolves claims as
  though it were a real finding. A harness that cannot produce a number has
  not measured anything.

### complete() does not commit, and that is your job

`complete()` records the real cost of the call on the caller's session with
`flush()`, never `commit()`. This is not a safety net: by the time it returns,
a real billed request has already been made and that charge cannot be rolled
back.

**If the caller never commits, the recorded spend is lost even though the
money was spent.** The ledger then stays at zero, every later cap check reads
zero spent, and the $50.00 ceiling is never enforced across calls. One
forgotten `session.commit()` in a harness disables the budget cap for the
month.

So: commit promptly after a successful `complete()`, exactly as the example
above does.

The API key is read from `ANTHROPIC_API_KEY` by the SDK's default client
construction. No key is ever hardcoded or committed.

### Measuring more than once

A cycle may be measured repeatedly, and scoring takes **latest run wins** per
metric name, because a harness you fixed and re-ran means the newer number.

The teardown page and the markdown export list **every** run, in order, with
each run's timestamp, its notes and its own measurements, and they mark which
reading the score actually used. A value that a later run replaced is still
printed, labelled as superseded. That is deliberate: the seal makes the
prediction tamper-evident to a stranger, and the run list is what does the
same for the measurement. An overwrite is visible in the published artifact
rather than invisible.

## Tests

```sh
.venv/bin/python -m pytest -v
```

`conftest.py` pins the suite to `ai_eval_gym_test` unconditionally, and never
reads `DATABASE_URL` for that choice, so an exported `DATABASE_URL` cannot
point the suite's `drop_all` at real data. Set `TEST_DATABASE_URL` to use a
different test database (one worktree per database, for instance).

Every test that seals does so inside a throwaway git repository under
`tmp_path`, so no test ever appends a commit to this project's own branch.

One test is skipped unless `ANTHROPIC_API_KEY` is set: it is the only one that
makes a real, billed API call, and it drives `complete()` end to end at
`max_tokens=16`, which is well under a cent. Run the suite once with a key set
to prove the live path, including the token counts the ledger is written from.

## Reading the published teardown

A teardown is only available once the cycle is `scored`:
`/cycles/<id>/teardown` for the page, `/cycles/<id>/teardown.md` for the
export you publish.

The export names the chain head and the exact commit SHA that holds the seal
file, so a reader who has this repository can run `git show <sha>` and check
for themselves that the prediction predates the measurement. Cycles sealed
before the app recorded that SHA say so plainly instead of naming a commit.

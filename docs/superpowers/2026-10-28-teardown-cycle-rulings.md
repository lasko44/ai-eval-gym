# Decisions taken on Matt's behalf while executing the teardown cycle slice

Date: 2026-10-28. Plan: `plans/2026-10-28-teardown-cycle-slice.md`.

The plan was executed by a controller dispatching one implementer and one reviewer per
task. Where the plan, a task brief or a review left something undecided, the controller
ruled rather than stopping to ask, and every ruling was recorded with what it would cost
if wrong. This file is that record, preserved because the execution workspace it came
from is scratch and gets deleted. Read it to find anything you would have decided
differently.

60 rulings.

1. work on branch `feat/teardown-cycle-slice` in the primary tree, no worktree. This is a brand new repo with no other work in flight, so the tree is already isolated. Cost if wrong: none beyond needing a worktree later if parallel work starts.

2. Python 3.13.11, the only interpreter present; the spec's "3.12" is a floor not a pin. Cost if wrong: a 3.13 incompatibility in a dependency, discovered at install time.

3. Postgres 17 at 127.0.0.1:5432 (binaries off-PATH at /opt/homebrew/opt/postgresql@17/bin), databases ai_eval_gym and ai_eval_gym_test created. Cost if wrong: none, they are new and empty.

4. CONFLICT 1, score_cycle builds its measurements dict from ALL runs on the cycle, latest run winning per metric name. Reason: the spec's loop is predict, measure, score, and a user who re-runs a fixed harness means the newer number. Cost if wrong: a stale value scores a claim, visible on the teardown page where both runs are listed.

5. GAP (T2 to T6): add `Cycle.claims` and `Cycle.runs` relationships in T1's models, ordered by id. Reason: three later tasks assume them. Cost if wrong: none, additive.

6. GAP (T5 stage): POST /cycles/{id}/score sets stage to "scored". Reason: T1 defines the value and nothing else sets it. Cost if wrong: none.

7. CONFLICT 2: `complete()` takes an explicit first parameter `session: Session`, so the budget check and the ledger write share the caller's transaction. Reason: a module-level implicit session cannot be tested or rolled back, and the cap must be transactional with the spend write. Signature becomes `complete(session, prompt: str, *, model: str, max_tokens: int) -> str`. Cost if wrong: harness code has to pass a session it already has.

8. CONFLICT 3: T7's third test becomes a fixture named `fake_response` parametrised to cost 12 cents, injected normally. Reason: the plan's syntax does not parse. Cost if wrong: none, the assertion is unchanged.

9. no TodoWrite tool in the resumed session, so this ledger is the only progress record. Cost if wrong: none, the skill treats the ledger as authoritative anyway.

10. the Cycle.claims / Cycle.runs relationships I ordered in pre-flight are deferred to the tasks that introduce their targets. Reason: the implementer produced a SQLAlchemy repro showing a relationship to a non-existent class raises InvalidRequestError on first ORM use, registry-wide, which would have broken Task 1's own tests. Task 2 adds Cycle.claims, Task 4 adds Cycle.runs. Cost if wrong: none, the relationships land one task later than planned.

11. Important 3 is fixed by moving create_all out of app startup into an explicit `python -m app.initdb` entry point, not by deleting it. Reason: implicit DDL against a real database on every boot is the defect, but the slice still needs a one-command way to create the schema and the plan names no migration tool. Cost if wrong: one extra module, and a later migration tool replaces it.

12. the conftest-changes-on-disk report from two agents is closed with no action. Reason: the working tree is clean at d00069e on two independent controller checks, and the file mtime falls inside the reviewing agent's own run, so both agents were observing edits they made while experimenting and reverted. Cost if wrong: a real editor reappears later, and the next clean-tree check catches it.

13. commit 7537689 was authored by the TASK REVIEWER, not the implementer. Timestamp 16:15:49 falls inside the review agent's run, and it rewrote conftest.py to use an ASGI transport instead of the deprecated TestClient. This is a process breach: a reviewer reviews, it does not edit or commit. It also explains both agents' reports of conftest.py changing on disk and supersedes the earlier no-action ruling on that. Decision: KEEP the commit rather than revert it, because it is inside the d00069e..692cfc6 range the scoped re-review already covers, so it gets the review it skipped, and it incidentally closes deferred minor 5. The re-review is told to scrutinise it specifically. Cost if wrong: an unreviewed-by-design change sits in history, caught by the re-review or the final whole-branch review.

14. every future reviewer dispatch carries an explicit prohibition on editing, writing or committing files. Reason: the task-reviewer template does not state it and this reviewer assumed otherwise. Cost if wrong: none.

15. 7537689 stays on the branch rather than being reverted, subject to review. Reason: it removes a deprecated dependency the project would have had to remove anyway, and reverting it means re-fixing a deferred minor later. Cost if wrong: the facade it introduces is load-bearing for every remaining task's HTTP tests, so a latent defect in it multiplies. That is exactly what the re-review below is scoped to catch.

16. single working tree, no worktree, now that one controller owns the plan. Reason: the collision is resolved by there being one driver, and a worktree costs setup for a solo run. Cost if wrong: a future second session can write into this tree again, so any further parallel work moves to ../ai-eval-gym-wt/<branch> first.

17. 7537689 entered the branch unreviewed, so it is reviewed now as part of the fix round re-review rather than taken on trust. Reason: the house rule is that a change is not verified until a test or review has driven it, and a green 2-test suite does not exercise event loop reuse across calls. Cost if wrong: a round trip on a commit that turns out to be fine.

18. the two fixture traps the re-review flagged are carried into Task 2's dispatch as docstring lines rather than a dedicated fix dispatch. Reason: both are forward-looking with no present defect, the change is two comment lines, and Task 2's implementer is already editing conftest.py to add claim fixtures. Cost if wrong: two lines land one task later than ideal. Trap 1: SyncASGIClient does not run the app's lifespan (ASGITransport dispatches only http scopes), so a later startup hook would silently never fire in tests. Trap 2: requests do not follow redirects unless asked, unlike the TestClient it replaced.

19. seal_cycle resolves both the seals/ directory and the git repository from the process working directory, and every sealing test chdirs into a throwaway git repo under tmp_path. Reason: the pre-flight scan missed this. The brief's own test_sealing_chains_each_claim_hash calls seal_cycle with no isolation, and seal_cycle runs git add plus git commit, so as written the suite would append a commit to feat/teardown-cycle-slice on every run, corrupting the branch this plan is being built on. Using cwd keeps the brief's declared signature seal_cycle(session, cycle_id) -> str intact, matches the no-git test's use of monkeypatch.chdir, and still does the right thing in production, where the user runs the app from the repo root and the seal commit lands in the project repo as the spec requires. Cost if wrong: sealing depends on cwd, so a future daemon or service run from elsewhere needs an explicit root parameter.

20. Task 2 also adds the Cycle.claims relationship deferred from pre-flight, since Claim now exists. Reason: the pre-flight ruling named Task 2 as its home. Cost if wrong: none, additive.

21. Task 2 must cover the dirty-seal-file case the brief's four tests omit. Reason: the plan's Review Focus pins "sealing with no git repository, or with the seal file already dirty, must fail loudly before any database write" to this task, and only the no-git half is tested. Cost if wrong: a fifth test beyond the brief's four, which is scope the Review Focus mandates.

22. Tasks 3 and 7 come off the critical path and run in parallel worktrees; Tasks 2, 4, 5, 6, 8 stay sequential. Reason: the brief file lists show Task 3 shares no file with any other task (app/metrics/* plus its own test, pure functions, no database) and Task 7 shares only an additive row in models.py. The rest genuinely chain: Task 5 consumes Claim from 2, Measurement from 4 and brier_score from 3, Task 6 consumes 5, Task 8 consumes every route. Cost if wrong: one merge per parallel branch, and the parallel branches rebase before merging.

23. parallel work goes in git worktrees at ../ai-eval-gym-wt/<branch>, not in the shared tree. Reason: two controllers writing one tree is the failure this session already had once today, and the house worktree hygiene (named path, reaped on merge, rebased before PR) exists for exactly this. Cost if wrong: worktree teardown to remember at merge time.

24. a parallel agent may run ONLY its own test file, never `pytest tests/`. Reason: the

25. brier_score([]) raises ValueError rather than returning 0.0. Reason: 0.0 is a perfect Brier score, so returning it for "nothing was predicted" would report flawless calibration to a user whose whole purpose is finding out whether he is calibrated. Task 5 declares `brier: float | None` and represents nothing-resolved as None. Carry into Task 5's dispatch. Cost if wrong: Task 5 must guard the empty case, which it already has a field for.

26. flip_rate raises ValueError on length mismatch, and recall_at_k, precision_at_k and ndcg_at_k all return 0.0 on an empty relevance set. Reason: the brief pins the 0.0 rule for recall and gives the reason (an unlabelled slice must degrade visibly, not crash); the other two follow for consistency. A positionwise disagreement rate over unequal lengths has no defined answer. Cost if wrong: none, all five are tested.

27. Task 3 also implements and tests precision_at_k and ndcg_at_k, which the brief declares in Interfaces but gives no tests for. Reason: the house rule is that nothing counts as verified until a test drives it. Cost if wrong: two tests beyond the brief's five.

28. Task 7's three brief tests are rewritten to pass `session` as complete()'s first argument. Reason: the pre-flight CONFLICT 2 ruling changed the signature to complete(session, prompt, *, model, max_tokens) so the cap check and the spend write share one transaction, but the brief's verbatim test bodies still call complete("hi", model=...), which cannot work against the ruled signature. The ruling stands and the tests follow it. Cost if wrong: three test call sites differ from the brief text.

29. every test in tests/test_llm_budget.py stubs app.llm._send, including the brief's second test, which as written stubs nothing. Reason: that test calls complete() and asserts spend was recorded, so as literally written it would send a real billed request to the Anthropic API on every single test run, against a project whose entire spend ceiling is $50 per month. A test suite that spends money is a defect. Cost if wrong: the HTTP boundary itself is not covered by the stubbed tests, which the next ruling addresses.

30. Task 7 adds one real-service test, skipped unless ANTHROPIC_API_KEY is set, that makes a single minimal real call to prove _send works against the live API. Reason: the house rule is that a green test on a mocked layer is not proof, and that where a real dependency cannot run unconfigured, a test must run when it IS available and skip when it is not. Everything except _send is real code under test in the other tests. Cost if wrong: one tiny real API charge of well under a cent when a key is present.

31. MONTHLY_CEILING_CENTS lives as a module constant in app/llm.py, initialized from the environment with a 5000 default, and no new config module is created. Reason: the brief says "read from config" but names only app/llm.py and app/models.py in its Files block, and this project has no config layer yet. Cost if wrong: a later task that needs shared config extracts it.

32. Task 7's worktree changes conftest.py to honor a TEST_DATABASE_URL override and runs against its own database ai_eval_gym_test_t7. Reason: Task 7 needs the database, and the single shared ai_eval_gym_test cannot serve two concurrent suites that create_all and drop_all per test. This also closes the deferred Task 1 minor about the hardcoded test URL. Cost if wrong: a small conftest.py merge against Task 2's docstring edit, in a different region of the file.

33. Task 7's implementer must load the claude-api skill for model ids and pricing rather than recalling them. Reason: the worst-case cost estimate is the entire cap mechanism, so a wrong output rate silently breaks the ceiling, and pricing is not something to answer from memory. Cost if wrong: none, the skill is the authority.

34. Task 2's added GET /cycles/{id}/predict route and cycle.html link are accepted despite being absent from the brief's Interfaces block. Reason: the brief requires creating predict.html, and a template nothing renders is dead code, so the GET route is the minimum needed to make a required file reachable. Cost if wrong: one route arrives a task earlier than the plan implies.

35. Task 4 moves cycle, cycle_with_two_claims, sealed_cycle, git_repo, git_repo_that_refuses_commits, _git and VALID_CLAIM from tests/test_sealing.py into conftest.py. Reason: Task 4's brief uses the cycle and sealed_cycle fixtures, but Task 2 defined them module-local, where another test file cannot see them. Cost if wrong: Task 4 must also run test_sealing.py to prove the move broke nothing, which it is instructed to do.

36. Task 4 makes the same TEST_DATABASE_URL conftest change as Task 7 and commits it, rather than coordinating. Reason: both branches need their own database to run concurrently, the change is textually identical on both sides, and resolving it at merge is choosing one copy. Cost if wrong: one trivial merge resolution.

37. reviewer Minor 4 (read the committed seal file back before committing the database) is promoted into fix round 1 rather than deferred. Reason: `git commit -- <path>` commits the working tree rather than the index, so the window between writing the file and committing it is unverified in production code, and this is an integrity property of the one mechanism the entire project rests on. The implementer is already editing that exact region for Important 2, so the marginal cost is near zero. Cost if wrong: a few lines of read-back and one more git invocation per seal.

38. reviewer Minor 5 (seed the chain with cycle.question instead of the literal "genesis") is deferred to the final review, not promoted. Reason: it is a real latent integrity gap, but it changes the canonical serialization that this review just verified collision-free across five attack shapes, and altering the integrity core is a decision for the whole-branch review rather than a fix round. It is latent today because no cycle-edit route exists. Cost if wrong: the question remains editable after sealing until that review rules on it.

39. merges of the parallel branches are deferred until the main checkout has no agent working in it. Reason: Task 2's fix round is editing the main tree right now, and merging would move HEAD and add files underneath a live implementer. Task 3's branch touches only app/metrics/* and tests/test_metrics.py, so the merge itself is conflict-free whenever it runs. Cost if wrong: the merges queue up and run back to back instead of as each branch lands.

40. Important 3 takes the minimum fix (docstring stating the caller's obligation) and NOT the reviewer's stronger transactional redesign. Reason: the pre-call row is flushed but uncommitted in the caller's transaction, so a separate session committing an UPDATE to that row would block on the uncommitted row lock, and a deadlock in the spend path would be worse than a documented obligation. The cap still holds within a transaction because the flushed spent_cents accumulates. Cost if wrong: a real charge can go unrecorded if a caller rolls back after a successful call, leaving a later cap check reading a stale total. Flagged for the final review to decide properly.

41. reviewer Minors 4, 5 and 6 are promoted into fix round 1. Reason: 5 and 6 decide whether the cap is actually tested rather than merely present (the existing ceiling test does not discriminate the output rate from the input rate, and nothing catches an inverted comparison), and 4 is an internal contradiction where _extract_text takes the first text block while the task's own real-service test joins all of them. Cost if wrong: three small additions to a file the implementer is already editing.

42. Task 4's added GET /cycles/{id}/runs read-only list is accepted as scope, consistent with the identical ruling made for Task 2's GET /cycles/{id}/predict. Reason: the brief requires creating run.html but names no route that renders it, and a template nothing renders is dead code. Cost if wrong: one read-only route arrives earlier than the plan implies. The implementer's own statement that the route has no automated test is left to the reviewer to rate, not pre-judged.

43. POST /cycles/{id}/score is refused with 409 on a cycle whose stage is open or sealed, and a cycle already at scored may be re-scored and stays scored. Reason: the brief is silent, and scoring before measuring would record an all-unresolved result as though it were a finding; this mirrors the 409 that refuses a run on an unsealed cycle. Re-scoring is harmless because scoring is deterministic. Cost if wrong: one more guard clause than the brief asked for.

44. coverage is 0.0 when a cycle has no claims, rather than raising on a zero denominator. Reason: 0/0 is undefined and 0.0 communicates nothing-resolved truthfully. Cost if wrong: a cycle with no claims reports 0.0 coverage rather than an error.

45. Task 5's new fixtures go in conftest.py and must include a scored_cycle fixture built on the existing sealed_cycle. Reason: Task 6 reads scored_cycle.claims[-1].sealed_hash, and building it on sealed_cycle inherits the git_repo chdir isolation so no test can commit into this repo. Cost if wrong: Task 6 builds its own and the two drift.

46. Task 5's concern (POST /score renders score.html directly instead of redirecting 303 to a GET page that does not exist, breaking the redirect-after-POST shape the other POST routes use) is deferred to the final review, not fixed now. Reason: Task 6 adds GET /cycles/{id}/teardown which renders the scored cycle, so a separate GET score page may be redundant, and the right answer is probably for the POST to redirect to the teardown page rather than to a new page nobody needs. Deciding that before Task 6 exists would be guessing. Re-posting is harmless because scoring is deterministic and writes only the stage change. Cost if wrong: a browser refresh re-posts.

47. both teardown routes require stage `scored` and refuse with 409 otherwise. Reason: a teardown without a score is not a teardown, and computing one on demand would let the user see a score before the cycle is formally scored, blurring the predict-measure-score ordering the design exists to protect. Matches the app's existing 409 vocabulary. The teardown link only appears once scored, so the 409 guards hand-typed URLs. Cost if wrong: a GET returning 409 is unusual, and the final review may prefer a rendered not-ready state instead.

48. Task 6 adds the minimum navigation to make a cycle walkable in a browser (a score form gated on stage, a cycle-to-runs link, and a teardown link once scored) and redesigns nothing. Reason: the loop is currently unwalkable without curl, which makes the app unusable for its own purpose. Cost if wrong: three small template edits land in the task that needed them rather than in a dedicated one.

49. no stage guard is added inside app/scoring.py. Reason: that file belongs to Task 5 and is already reviewed and approved, and Task 6's own 409 guard keeps callers on the right side of it. Cost if wrong: a future caller outside these routes can still score an unscored cycle directly.

50. Task 6's concern 1 (the brief's test asserts "0.42" but the shared scored_cycle fixture measures recall_at_5=0.2 and flip_rate=0.1) is handled as follows. The deviation itself was unavoidable since the fixture genuinely has no 0.42, and editing the shared fixture was correctly out of scope. BUT the controller verified the substituted "0.2" is ambiguous: it is both recall_at_5's measured value and flip_rate's threshold, so the assertion would pass even if the Measured line never rendered. Also verified by grep that the templates contain no literal "wrong", so that part of the assertion is not vacuous: flip_rate gt 0.2 measured at 0.1 genuinely resolves wrong. Passed to the reviewer as a named risk without pre-judging severity. Cost if wrong: none, the facts were verified before dispatch.

51. Task 6's concern 2 (reusing the private app.scoring._latest_measurements across a module boundary) is accepted and is not a finding. Reason: two implementations of the latest-run-wins rule that must agree is worse than one private import. Cost if wrong: a cross-module private dependency, which the final review may prefer to promote to a public name.

52. reviewer Minors 1 and 2 are promoted into this fix round. Reason: Minor 1's test would pass if a POST form were replaced by a plain link, which would 405 in a browser; and Minor 2's missing negative cases mean the stage gating has no test behind it, and that gating is a controller ruling rather than a brief requirement, so a ruling with no test is just a comment. The implementer is already in that file. Cost if wrong: three small test additions.

53. Task 8's test MUST take the git_repo fixture. Reason: the brief's signature is test_one_whole_cycle_over_http(client) with no git repo, but its body posts to /cycles/{id}/seal, which performs a real git add and git commit against the process working directory. As literally written the test would append a commit to feat/teardown-cycle-slice on every run. This is the identical hazard caught in Task 2's pre-flight, recurring because Task 8's brief was written independently. Cost if wrong: none, every other sealing test already depends on git_repo.

54. Task 8 asserts a status code on every request, not only the 409 and the final body. Reason: Task 5's review flagged exactly this pattern, where an unasserted POST that silently began failing left the test green while proving nothing. Cost if wrong: a few more assertions.

55. Task 8 asserts the computed numbers, not only that the words "wrong" and "unresolved" appear. Reason: this is the only test that composes the whole slice, and asserting brier 0.49 and coverage 0.5 end to end is what turns it from a smoke test into a proof that would catch a scoring inversion across the route boundary. Hand-derived from the brief's own values: claim 1 is recall_at_5 lt 0.5 at p=0.7 measured 0.62, so 0.62 < 0.5 is false and it resolves wrong, pair (0.7, False) giving (0.7-0)^2 = 0.49; claim 2 is precision_at_5 lt 0.3 at p=0.9 never measured, so unresolved and excluded; one resolved of two gives coverage 0.5. Cost if wrong: if the app disagrees with the derivation, that is a real defect and the implementer was told to report it rather than adjust the expectation.

56. Task 8 writes create_cycle and add_claim in its own test file, not conftest.py. Reason: the brief uses both but defines neither, and no other task needs them. Cost if wrong: two helpers move to conftest later if another task wants them.

57. the reviewer's Declined To Judge list is accepted in full. Every item is a spec feature the plan explicitly scopes out of this slice (calibration curve, multi-cycle views, the Units curriculum, pgvector, OpenTelemetry, harness sandboxing, publish destination) or a non-requirement (visual design, test speed). Cost if wrong: none, they are scoped out rather than dropped.

58. ONE exception worth surfacing to the user: the plan NARROWED the spec's "spend caps per request and per session, not only per month" to the monthly ceiling alone. max_tokens bounds a single request as a side effect. That is a plan-versus-spec narrowing, not an implementation defect, and it stays narrowed for this slice. Cost if wrong: a single runaway session inside one month can consume the whole monthly ceiling.

59. no ruff or lint gate is added in this fix wave despite the reviewer noting its absence. Reason: it is new tooling nobody asked for, and turning a linter on across 32 new files would surface a wave of findings that have nothing to do with the two Criticals. Cost if wrong: style drift until a gate is added deliberately.

60. the restyle is sequenced AFTER the final fix wave and its scoped re-review, not alongside. Reason: the fix wave is editing teardown.html and score.html right now for the C2 audit trail, and two writers in one tree is the exact failure this session already had once today. Cost if wrong: the restyle starts a few minutes later.


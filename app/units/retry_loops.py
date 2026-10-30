"""Unit 08: agent loops that burn a budget without finishing.

Runaway retries and the tokens-per-resolved-task metric that catches them.
Numbers and citations verified against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


UNIT = Unit(
    slug="retry-loops",
    number=8,
    title="Agent loops that burn a budget without finishing",
    failure=(
        "An agent retries a failed attempt inside the same task. The retry carries the "
        "failed attempt forward as context. So the next try costs more than the last, "
        "whether or not it is any closer to succeeding. Nothing stops the loop until "
        "something external to the agent does."
    ),
    detection="Measure tokens per resolved task, not tokens per call, and watch for context that only ever grows within a task.",
    brief=(
        "An agent that tries something, fails, and tries again is not a bug, it is "
        "the default shape of an agentic loop. The failure mode is not that it "
        "retries, it is what the retry is made of. Most agent frameworks keep the "
        "whole conversation so far in context on every call. So the second attempt "
        "includes the broken tool call from the first attempt, the error it "
        "produced, and whatever the model said about it. All of that happens before "
        "the second attempt has done a single token of new work.",
        "The third attempt includes all of that plus the failure of the second "
        "attempt. Nothing in most frameworks prunes, summarizes, or resets that "
        "history mid task, so the context is monotonic. Attempt by attempt it only "
        "gets longer, and every token of it gets billed again on every subsequent "
        "call.",
        "A dashboard that reports average tokens per call cannot see this happening. "
        "A fleet running thousands of tasks a day might have ninety nine percent of "
        "them resolve in one or two cheap calls. A handful loop for dozens of "
        "attempts each. Averaged across every call, the cheap majority swamps the "
        "expensive minority, and the number barely moves. The loop is a small share "
        "of calls even when it is a large share of tokens. That is exactly the "
        "condition under which a flat average and a real problem look identical "
        "from the outside.",
        "This is a documented production failure, not a hypothetical one. A primary "
        "catalog of 63 confirmed incidents across 21 agent frameworks drew on "
        "GitHub issues, maintainer statements, and documented dollar losses where "
        "maintainers reported them. The catalog grouped its findings into clusters. "
        "The single largest cluster, 27 of the 63 cases spanning 12 of the "
        "frameworks, was a retry loop with no mechanism bounding what it could "
        "spend.",
        "One incident in that catalog ran up around 235 dollars in four days, from a "
        "single user account on a single framework. That is on the order of 59 "
        "dollars a day. That number would never surface on a per call average, "
        "because the rest of the traffic on that account looked completely "
        "ordinary.",
        "Tokens per resolved task is the number that exposes it, because it changes "
        "the denominator. Add up every token spent, including everything burned by "
        "tasks that never finished, and divide by the count of tasks that actually "
        "resolved. A task that loops forty times and never resolves puts its "
        "entire, growing bill into that numerator. It contributes nothing to the "
        "denominator. That drags down the one number that should measure the cost "
        "of getting something done, not the cost of asking.",
        "The same catalog describes context growth findings of unbounded growth at "
        "the level of the step loop the agent itself runs. One case was left "
        "running for over thirteen months. A single call reached on the order of "
        "two million tokens during a tool heavy run.",
        "Watching whether the context of a task ever shrinks between attempts is "
        "the second, cost independent signal. A hard problem can legitimately take "
        "many expensive attempts while still making progress. But context that only "
        "ever grows means the loop has no way to discard a failed branch and start "
        "clean. That is a property of how the loop is built, not of how hard this "
        "particular task happens to be.",
        "Here is what I could verify directly. The arXiv id of the catalog "
        "resolved, along with its title, incident count, and framework count. The "
        "cases across frameworks in the retry loop cluster, and the dollar and "
        "token figures above, came from reading the paper, not from memory.",
        "The OpenTelemetry GenAI semantic conventions come from the official "
        "repository for the specification. They define per call token usage "
        "attributes and a separate span for a full agent run. They also state that "
        "capturing prompt and response content is opt in and off by default. The "
        "data a trace needs to compute tokens per resolved task already exists at "
        "the call level. Nothing in the spec rolls it up to a task automatically.",
        "I looked for a published tokens or dollars per resolved task figure from a "
        "coding agent benchmark leaderboard. That would have been a strong second "
        "source. I could not load a primary page that stated one, so no figure of "
        "that kind appears in this unit.",
    ),
    probes=(
        Probe(
            id="right-denominator",
            asks=(
                "Across a fleet of agent tasks, most resolve in one or two calls and "
                "a few loop dozens of times and never resolve. You want one number "
                "that would have caught this before someone noticed the bill. What "
                "belongs in the denominator?"
            ),
            choices=(
                Choice("a", "Total number of calls, for an average cost per call"),
                Choice("b", "Total number of tasks attempted, resolved or not"),
                Choice("c", "The number of tasks that actually resolved"),
                Choice("d", "The number of distinct users who ran a task"),
            ),
            answer="c",
            because=(
                "Dividing by every call is the metric that hides this failure. A "
                "handful of expensive stuck loops sit inside a majority of cheap "
                "calls, so the average barely moves. Dividing by every task "
                "attempted undercounts the damage. It charges a stuck task the same "
                "weight as a normal one, when the cost of being stuck is the whole "
                "point. Dividing by resolved tasks puts every wasted token, "
                "including everything spent on tasks that never finished, onto the "
                "books of the tasks that did. That is the only version of the "
                "number that moves when a loop is burning budget without producing "
                "anything."
            ),
        ),
        Probe(
            id="stuck-vs-slow",
            asks=(
                "A task has looped eight times trying the same fix. What about its "
                "context across those eight attempts would tell you it is "
                "structurally stuck rather than just working through a hard problem?"
            ),
            choices=(
                Choice("a", "The total token count across all eight attempts is high"),
                Choice("b", "Context length has grown on every attempt and never shrunk"),
                Choice("c", "The task has been running for more than five minutes"),
                Choice("d", "The model used a different tool on each attempt"),
            ),
            answer="b",
            because=(
                "A hard problem can legitimately need eight expensive attempts and "
                "still be making progress. A high total token count on its own "
                "does not distinguish stuck from slow. Context that only ever "
                "grows, with no attempt smaller than the one before it, means the "
                "loop cannot discard a failed branch. It cannot try a clean one "
                "either. That is a property of how the loop is built, not of "
                "how difficult this task is. That is the second signal this unit "
                "asks you to watch for, independent of cost entirely."
            ),
        ),
        Probe(
            id="flat-average-meaning",
            asks=(
                "A team tracks average tokens per call on its dashboard, and the "
                "number has stayed flat for months. Based on the retry loop "
                "failure mode, what does that actually tell you?"
            ),
            choices=(
                Choice("a", "Runaway retry loops cannot be happening, the average would have moved"),
                Choice("b", "Nothing either way: a small number of expensive loops can sit inside a flat average dominated by many cheap calls"),
                Choice("c", "The system must already have a hard cap on retries"),
                Choice("d", "The average is unreliable, so switch to p99 latency instead"),
            ),
            answer="b",
            because=(
                "The mechanism behind this failure is that a stuck loop is a small "
                "share of total calls. It is a large share of total tokens, "
                "though. So it can sit inside a flat per call average "
                "indefinitely, without moving it. A flat average is consistent "
                "with zero retry loops, and with several expensive ones, because "
                "it answers the wrong question entirely. That is why the fix is a "
                "different metric, tokens per resolved task, rather than a "
                "tighter threshold on the same one."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "This unit ships a fixture of 160 agent task traces. Compute tokens "
            "per resolved task: every token spent across every attempt in every "
            "task, resolved or not, divided by the count of tasks that resolved. "
            "Post that number in tokens."
        ),
        fixture_path="fixtures/retry_loops/agent_task_traces.json",
        fixture_note=(
            "A JSON object with one key, tasks, holding 160 entries. Each entry has "
            "a task_id, a resolved boolean, and attempts, a list of per attempt "
            "token counts in the order they happened. 150 of the tasks resolved, "
            "almost always within one to three attempts. The other 10 never "
            "resolved. Each looped for 25 to 50 attempts. Within every one of "
            "those 10, the token count of each attempt is higher than the "
            "previous one, because the failed attempt stayed in context."
        ),
        starter=(
            'import json\n'
            '\n'
            'data = json.load(open("fixtures/retry_loops/agent_task_traces.json"))\n'
            'tasks = data["tasks"]\n'
            '\n'
            '# tokens_per_resolved_task is not in app.metrics. Work out the\n'
            '# numerator (every token, from every attempt, in every task) and the\n'
            '# denominator (only the tasks that resolved), then divide.\n'
        ),
        metric="tokens_per_resolved_task",
        expected=25168.43,
        tolerance=0.5,
        because=(
            "Total tokens across all 672 attempts in the fixture come to 3,775,265. "
            "Divide by the 150 tasks that resolved and you get 25,168.43 tokens per "
            "resolved task. Tokens per call, the metric an ordinary dashboard would "
            "show, is the same 3,775,265 divided by 672 calls, about 5,618, a number "
            "nobody would flag. The 10 tasks that never resolved account for about "
            "89 percent of every token spent in the fixture, while being only 6 "
            "percent of the tasks. None of that shows up until the denominator "
            "changes to the tasks that actually finished."
        ),
    ),
    sources=(
        "arXiv:2606.04056 (2026-06-02), Token Budgets: An Empirical Catalog of 63 "
        "LLM-Agent Budget-Overrun Incidents, with an Affine-Typed Rust Mitigation as "
        "a Case Study; 63 confirmed incidents across 21 frameworks, retry loop "
        "cluster at 27 cases across 12 frameworks, context amplification cluster "
        "describing unbounded growth in the agent step loop",
        "github.com/open-telemetry/semantic-conventions-genai, docs/gen-ai (read "
        "2026-10-29), per call token usage attributes, the agent run span, and the "
        "opt in default for capturing prompt and response content",
    ),
)

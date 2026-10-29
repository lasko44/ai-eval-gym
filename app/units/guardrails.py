"""Unit 09: a guardrail reported as a single number.

Static blocked-corpus testing and one-sided catch-rate reporting. Numbers and
citations verified against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


UNIT = Unit(
    slug="guardrails",
    number=9,
    title="A guardrail reported as a single number",
    failure=(
        "A content filter's catch rate is measured against the same blocked "
        "corpus it was tuned on, and reported with no false-positive rate "
        "next to it."
    ),
    detection=(
        "Mutate the blocked corpus before measuring bypass rate, and report "
        "it paired with the false-positive rate on benign traffic."
    ),
    minutes=25,
    brief=(
        "A team adds a content filter or policy classifier in front of a model, "
        "runs it against a blocked-prompt test set they already assembled, and "
        "watches it catch nearly all of them. That catch rate becomes the "
        "headline number, and the project gets marked solved. The test set is "
        "the problem: it is exactly the set of inputs someone already thought "
        "to write down as bad, so a filter that pattern-matches or keyword-"
        "matches that exact wording will score close to perfect on it and tell "
        "you nothing about anything it has not already seen in that form.",
        "The second problem sits on the same line as the first. Catch rate is "
        "one side of a ledger with two sides, and reporting only one side "
        "makes the number meaningless on its own: a filter that blocks every "
        "single request also catches 100 percent of the blocked set, and "
        "nobody would call that filter working. Bypassing LLM Guardrails "
        "(arXiv:2504.11168, 2025-04-15) tested six deployed guardrail systems, "
        "Azure Prompt Shield, Meta Prompt Guard, ProtectAI Prompt Injection "
        "Detection v1 and v2, NVIDIA NeMo Guard Jailbreak Detect, and Vijil "
        "Prompt Injection, with character obfuscation such as homoglyphs, "
        "zero-width characters and emoji smuggling, and with adversarial "
        "word-substitution attacks. The single worst technique, emoji "
        "smuggling, reached a 100 percent attack success rate for both "
        "prompt-injection and jailbreak categories, averaged across the six "
        "systems; per-system averages for character injection ranged from "
        "Vijil at roughly 88 to 92 percent down to Meta Prompt Guard at "
        "roughly 70 to 73 percent. What that paper never once reports, for "
        "any of the six systems, is what any of this costs on ordinary "
        "traffic. Every number in it is a bypass rate. It is, itself, the "
        "exact one-sided report this unit is teaching you to refuse to accept.",
        "The fix for the static-corpus half of the problem is to stop testing "
        "the filter against the inputs it already knows about and start "
        "testing it against mutated versions of them: paraphrases, obfuscated "
        "characters, synonym swaps, reordered clauses, anything that keeps the "
        "same intent while changing the surface form. The same paper's numbers "
        "make the case without needing a second study: an adversarial word-"
        "substitution technique averaged a 46 to 48 percent attack success "
        "rate across the six systems, and one system that looked reasonably "
        "solid against its original blocked set lost most of that margin once "
        "the inputs were obfuscated rather than copied verbatim. A filter "
        "tuned and tested against one fixed corpus is proving it has "
        "memorized that corpus, not that it generalizes to anything an "
        "attacker bothers to reword.",
        "The fix for the one-sided-number half is to report the false-"
        "positive rate next to the bypass rate every time, because the two "
        "move together and a number for one without the other hides a "
        "decision somebody made for you. Push the filter's threshold to catch "
        "more and the false-positive rate rises as ordinary requests get "
        "rejected alongside attacks; loosen it to stop annoying real users and "
        "the bypass rate rises with it. SoK: Evaluating Jailbreak Guardrails "
        "for Large Language Models (arXiv:2506.10597, 2025-06-12) builds this "
        "pairing directly into its evaluation framework, scoring every "
        "guardrail it tests on both an attack-success measure and a false-"
        "positive measure against a held-out benign set, rather than "
        "publishing either alone; in its own tables, a guardrail called Llama "
        "Guard let through roughly 23 percent of jailbreak attempts at the "
        "operating point it tested. Read next to a false-positive rate, that "
        "number says something about a tradeoff that was chosen. Read alone, "
        "it says nothing about whether the choice was a good one.",
        "What is verified here: the six named systems, the 100 percent emoji-"
        "smuggling result and the per-system character-injection averages all "
        "come from a direct read of the paper's own tables, as does the "
        "observation that the paper reports no false-positive data at all. "
        "The 46 to 48 percent adversarial-substitution average is from the "
        "same source. The pairing of a bypass number with a false-positive "
        "number as a deliberate evaluation framework is verified from the SoK "
        "paper's own description of itself, including the 23 percent figure "
        "it reports for Llama Guard. One number this briefing does not use is "
        "an exact false-positive percentage for any specific guardrail: a "
        "secondary summary of the SoK paper quoted one, but the paper's own "
        "text places that data point only in a figure, and a number that "
        "could not be read directly off the source does not belong here.",
    ),
    probes=(
        Probe(
            id="catch-rate-alone",
            asks=(
                "A content filter is evaluated against its own blocked-prompt "
                "test set and blocks all 500 of them: a 100 percent catch "
                "rate. What has this established?"
            ),
            choices=(
                Choice("a", "The filter is production ready and should ship as is"),
                Choice(
                    "b",
                    "Nothing on its own: a filter that blocks everything also "
                    "scores 100 percent here, and the test set is exactly what "
                    "someone already thought to write down as bad",
                ),
                Choice("c", "The filter's false-positive rate is acceptably low"),
                Choice("d", "The filter will catch roughly the same share of novel attacks"),
            ),
            answer="b",
            because=(
                "A 100 percent catch rate on a static, already-known blocked set "
                "is consistent with two very different filters: one that "
                "discriminates well, and one that simply rejects everything, "
                "including legitimate users. The number alone cannot tell "
                "those apart. You would need the false-positive rate to rule "
                "out the second filter, and you would need a mutated version "
                "of the corpus to say anything about attacks nobody has "
                "already enumerated for you."
            ),
        ),
        Probe(
            id="static-corpus",
            asks=(
                "You keep the blocked corpus the filter was tuned against and "
                "rerun it every release to confirm the catch rate stays high. "
                "What does a stable catch rate under this test fail to tell you?"
            ),
            choices=(
                Choice("a", "Nothing, a stable score on the same corpus is sufficient evidence the filter still works"),
                Choice(
                    "b",
                    "Whether the filter catches anything that is not already "
                    "in the exact form it was tuned against, such as "
                    "paraphrases, obfuscated characters or reworded attacks",
                ),
                Choice("c", "Whether the filter runs fast enough in production"),
                Choice("d", "Whether the filter's training data has grown stale"),
            ),
            answer="b",
            because=(
                "Measured results on exactly this corpus-mutation question show "
                "the gap: character-obfuscation and word-substitution attacks "
                "reached attack success rates from the high 40s up to 100 "
                "percent against systems whose catch rate on the original, "
                "unmutated strings looked solid. Rerunning the same corpus "
                "verbatim only proves the filter has not regressed on inputs "
                "it has already memorized, which says nothing about inputs an "
                "attacker bothers to reword."
            ),
        ),
        Probe(
            id="missing-half",
            asks=(
                "A report states: 'Attack X evades Guardrail Y with a 92 "
                "percent success rate.' Nothing else is stated. What is "
                "missing before this number means anything operationally?"
            ),
            choices=(
                Choice("a", "Nothing, 92 percent bypass is disqualifying on its own"),
                Choice(
                    "b",
                    "The false-positive rate at the same operating point, "
                    "since lowering bypass without it is cheap: reject "
                    "everything and bypass drops toward zero while usability "
                    "drops with it",
                ),
                Choice("c", "The exact wording of the prompts used in attack X"),
                Choice("d", "Whether Guardrail Y is open source"),
            ),
            answer="b",
            because=(
                "This is the exact blind spot found in the primary source for "
                "this unit: a paper that reports six systems' bypass rates in "
                "detail and never once states what any of those systems did to "
                "benign traffic. A bypass rate without a paired false-positive "
                "rate describes an operating point nobody chose on purpose, "
                "and the fix purpose-built evaluation frameworks now use is to "
                "score both together against the same benign set rather than "
                "publish either alone."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "A fixture ships classifier outcomes for 320 mutated variants of "
            "a blocked corpus (paraphrase, homoglyph swap, unicode tag "
            "smuggling, synonym substitution, case perturbation) and 400 "
            "benign requests, all run through the same filter at one fixed "
            "operating point. The bypass rate at this point is already fixed "
            "by the data: 156 of the 320 mutated items got through, for a "
            "bypass rate of 0.4875. Compute the other half of the pair, the "
            "false-positive rate on the benign set at that same operating "
            "point, and post it."
        ),
        fixture_path="fixtures/guardrails/mutated_outcomes.json",
        fixture_note=(
            "Two labeled lists. mutated_blocked has 320 entries, each a "
            "mutated variant of something that belongs in a blocked corpus, "
            "with a mutation category and a caught boolean recording whether "
            "the filter still caught it. benign has 400 entries, each an "
            "ordinary request with a topic category and a flagged boolean "
            "recording whether the filter blocked it anyway."
        ),
        starter=(
            'import json\n'
            '\n'
            'data = json.load(open("fixtures/guardrails/mutated_outcomes.json"))\n'
            'mutated_blocked = data["mutated_blocked"]\n'
            'benign = data["benign"]\n'
            '\n'
            '# app.metrics has precision_at_k and recall_at_k, but those score a\n'
            '# ranked retrieval list against a relevant-document set. There is no\n'
            '# ranking here, and no retrieval: each pool is an independent\n'
            '# labeled outcome, caught or not, flagged or not. That makes this a\n'
            '# confusion-matrix question, not a retrieval one, so compute it\n'
            '# directly from the counts.\n'
            '\n'
            'bypassed = sum(1 for item in mutated_blocked if not item["caught"])\n'
            'bypass_rate = bypassed / len(mutated_blocked)\n'
            'print("bypass_rate:", bypass_rate)\n'
            '\n'
            '# Your job: the other half of the pair.\n'
            '# false_positive_rate = ?\n'
        ),
        metric="false_positive_rate",
        expected=0.07,
        tolerance=0.0005,
        because=(
            "28 of the 400 benign requests were blocked, for a false-positive "
            "rate of 0.07. Read on its own, 0.4875 looks like a filter that is "
            "failing outright, and 0.07 looks like a filter that is mostly "
            "leaving real users alone. Read together, you have a filter that "
            "is bad on both sides of the same operating point: bypassed by "
            "nearly half of the mutated attacks it was supposed to catch, "
            "while still rejecting 7 percent of ordinary traffic it was never "
            "supposed to touch. precision_at_k and recall_at_k do not fit this "
            "question because they are built for a ranked list scored against "
            "a relevant-document set, and there is no ranking in either pool "
            "here, only independent binary outcomes."
        ),
    ),
    sources=(
        "arXiv:2504.11168 (2025-04-15), Bypassing LLM Guardrails: An Empirical "
        "Analysis of Evasion Attacks against Prompt Injection and Jailbreak "
        "Detection Systems, six guardrail systems, emoji smuggling 100% ASR, "
        "no false-positive data reported",
        "arXiv:2506.10597 (2025-06-12), SoK: Evaluating Jailbreak Guardrails "
        "for Large Language Models, Security-Efficiency-Utility framework "
        "pairing attack-success rate with a benign-set false-positive rate, "
        "Llama Guard ASR 0.227",
    ),
)

"""Unit 05: permissions checked above retrieval, so the prompt already escaped the check.

Access control sitting in the application layer instead of the retriever, and
why diffing retrieved chunk ids across users catches the leak that reading
answers never will. Numbers and citations verified against primary sources;
see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


UNIT = Unit(
    slug="permissions",
    number=5,
    title="Permissions checked above retrieval, so the prompt already escaped the check",
    failure=(
        "The retriever runs against the whole index regardless of who is asking, "
        "so chunks the current user is not entitled to see enter the prompt before "
        "any access check runs."
    ),
    detection="Diff the retrieved chunk ids across two users with different entitlements, never the answers.",
    minutes=25,
    brief=(
        "Most teams wire access control exactly once, at the edge of the request: "
        "the user is authenticated, their role is loaded, and the endpoint decides "
        "whether they are allowed to ask the assistant anything at all. That check "
        "answers one question, can this person use the system, and it has nothing "
        "to say about which specific documents the retriever is about to pull back "
        "for them. The retriever sits below that gate, it queries a shared vector "
        "index built from everything the organization has ingested, and it ranks "
        "chunks by semantic similarity to the question, not by who is holding the "
        "question. Unless someone deliberately filters the retriever's candidate "
        "set by the caller's entitlements before it runs, the retriever will return "
        "the best-matching chunks whether or not the caller is allowed to see them.",
        "The phrase the prompt has already escaped the check describes what happens "
        "next with precision. By the time an authorization check could run on the "
        "generated answer, the unauthorized chunk is no longer a document sitting "
        "in an index, it is tokens inside the context window the model is "
        "conditioning on. The model can summarize it, paraphrase it, cite it, or "
        "fold one of its facts into a sentence about something else entirely, and "
        "none of those paths require the model to reproduce the chunk verbatim for "
        "the information to have leaked. A filter applied to the final answer can "
        "catch a direct quote. It cannot catch a number that shaped a forecast, or "
        "a conclusion that would not exist without the chunk that fed it.",
        "ConfusedPilot, published against a production deployment of Microsoft 365 "
        "Copilot running over SharePoint, is a working demonstration of a version of "
        "this timing gap. In their account, a low-privilege account seeds a fake "
        "sales report into a shared store, and a compliance or deletion check only "
        "runs late in the pipeline, after retrieval has already cached the chunk and "
        "folded it into a draft answer. The deleted or unauthorized content kept "
        "shaping Copilot's responses to a different, higher-privilege user for "
        "roughly 164 seconds after the source document was gone, and a related "
        "phantom-document effect persisted for about 42 seconds past deletion, both "
        "measured in their experiments. The researchers ran this against real "
        "enterprise-scale document sets, not a toy corpus, which is why the paper "
        "reads as an incident report rather than a thought experiment.",
        "Microsoft's own published guidance about Copilot oversharing makes the same "
        "point from the defender's side instead of the attacker's. Copilot answers "
        "with whatever the asking user's identity can already technically read "
        "across SharePoint, OneDrive, and Teams, which means years of permission "
        "sprawl that nobody noticed while it sat quietly in a search index becomes "
        "visible the moment an assistant can summarize it on request. Microsoft's "
        "fix is not a smarter filter on Copilot's output, it is tooling aimed at the "
        "retrieval boundary itself: access reviews, sensitivity labels, and a "
        "restricted content discovery control that removes a site from the "
        "assistant's candidate set before a query ever reaches it. That is the same "
        "boundary this unit asks you to test.",
        "Testing this by reading the model's answers is the trap, and it is a "
        "comfortable one, because the model usually declines or hedges and the test "
        "passes. A refusal on the surface tells you nothing about what already sat "
        "in the context window when the refusal was generated, and a hundred other "
        "phrasings of the same question were never tried. The only test that "
        "measures the boundary where it actually lives is a diff: run the same "
        "queries as two accounts with different entitlements, log the chunk ids "
        "each retrieval returned before generation ever starts, and compare the "
        "sets directly against what each account is actually entitled to see. If a "
        "restricted account's retrieved set contains chunk ids from categories "
        "outside its entitlement, you have measured a leak, independent of whatever "
        "the model chose to say about it.",
    ),
    probes=(
        Probe(
            id="where-the-check-sits",
            asks=(
                "In the usual RAG architecture, where does the access control check "
                "actually run relative to the retrieval call?"
            ),
            choices=(
                Choice("a", "Before the embedding query is built, so unauthorized chunks are never embedded"),
                Choice("b", "Inside the vector index itself, which filters by caller identity automatically"),
                Choice("c", "At the edge of the request or after generation, with the retriever itself entitlement-blind"),
                Choice("d", "There is no single place, every layer re-checks independently"),
            ),
            answer="c",
            because=(
                "Authentication at the edge answers whether someone may use the system "
                "at all, not which documents they may retrieve. Unless someone adds "
                "entitlement filtering as an explicit pre-filter on the retriever's "
                "candidate set, the retriever ranks the whole index by similarity alone, "
                "and any check on the output comes after the chunk is already inside "
                "the prompt."
            ),
        ),
        Probe(
            id="escaped-the-check",
            asks=(
                "A chunk the user is not entitled to see enters the prompt, and the "
                "final answer never quotes it directly. In what sense has it leaked?"
            ),
            choices=(
                Choice("a", "It has not leaked, since nothing unauthorized appears in the visible output"),
                Choice("b", "It leaked only if the model names the source document explicitly"),
                Choice("c", "It can leak through a summary, an inferred fact, or a number that shaped the answer, with no verbatim quote required"),
                Choice("d", "It leaked only if the same chunk later appears in a citation list"),
            ),
            answer="c",
            because=(
                "Once a chunk's tokens are part of the context the model is "
                "conditioning on, its content can influence word choice, inferred "
                "conclusions, and numbers in the answer without ever being quoted. A "
                "filter looking for a verbatim match on the final text will pass a "
                "paraphrase that still carries the unauthorized fact."
            ),
        ),
        Probe(
            id="why-answers-are-the-wrong-test",
            asks=(
                "You ask a restricted account's assistant the same sensitive question "
                "a dozen different ways and it declines or hedges every time. What has "
                "this actually told you about the access-control boundary?"
            ),
            choices=(
                Choice("a", "The boundary is sound, since no unauthorized content reached the user"),
                Choice("b", "Close to nothing, because the model's willingness to answer is a different variable from whether the unauthorized chunk was retrieved into the prompt at all"),
                Choice("c", "The boundary is sound for this question, though other phrasings should still be checked"),
                Choice("d", "The retriever is correctly filtering by entitlement, since a hedge implies no unauthorized match was found"),
            ),
            answer="b",
            because=(
                "The model's refusal is a property of the model, not a property of the "
                "retrieval pipeline, and it tells you nothing about whether the "
                "unauthorized chunk was already sitting in the context window when the "
                "refusal happened. Twelve declined phrasings leave the thirteenth "
                "untested, and none of them substitute for looking at what the "
                "retriever actually returned. That is why the only test that measures "
                "this boundary is a diff of retrieved chunk ids against the "
                "entitlement map, done before generation, not a read of what the model "
                "said afterward."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "A fixture ships with this unit: 65 queries, each run through the same "
            "retriever as two accounts with different entitlements, plus the "
            "entitlement map and a category label for every chunk in the index. "
            "Measure the leak for the restricted account, contractor_jdoe: of all "
            "the chunks retrieved for that account across all 65 queries, what "
            "fraction belong to a category contractor_jdoe is not entitled to see? "
            "Post that fraction."
        ),
        fixture_path="fixtures/permissions/retrieval_by_user.json",
        fixture_note=(
            "A JSON object with four keys. entitlements maps each of two user ids to "
            "the list of chunk categories they are allowed to see. chunk_categories "
            "maps every chunk id in the index to exactly one category. queries lists "
            "the 65 query ids and their text. retrievals maps each user id to a list "
            "of 65 entries, each an executed query id and the list of chunk ids the "
            "retriever actually returned for it, top 8 per query. Note before you "
            "write anything: the retriever is entitlement-blind, so diffing the two "
            "users' retrieved chunk ids against each other will show zero "
            "difference. That is the point, and it is also why the diff alone is not "
            "the measurement. You need the entitlement map to tell you which of "
            "contractor_jdoe's identical retrievals it was never supposed to see."
        ),
        starter=(
            'import json\n'
            '\n'
            'fixture = json.load(open("fixtures/permissions/retrieval_by_user.json"))\n'
            '\n'
            'user = "contractor_jdoe"\n'
            'allowed_categories = set(fixture["entitlements"][user])\n'
            'chunk_categories = fixture["chunk_categories"]\n'
            'retrievals = fixture["retrievals"][user]\n'
            '\n'
            '# retrievals is a list of {"query_id": ..., "chunk_ids": [...]}.\n'
            '# For every chunk id this user retrieved, look up its category and\n'
            "# check it against allowed_categories. Work out total retrieved and\n"
            "# how many of those fall outside the entitlement, then the ratio.\n"
            'leaked = 0\n'
            'total = 0\n'
            '# ... your measurement here ...\n'
            'print(leaked / total)\n'
        ),
        metric="leaked_chunk_rate",
        expected=0.6404,
        tolerance=0.0005,
        because=(
            "contractor_jdoe is entitled to the public and onboarding categories "
            "only, but the retriever ranks every query against the full six-category "
            "index without knowing that. Across the 65 queries, contractor_jdoe's "
            "retrievals pulled 520 chunks total, and 333 of them, about 64.0 percent, "
            "came from finance, legal, eng, or hr, categories outside that account's "
            "entitlement. A diff against fulltime_asmith's retrievals for the same "
            "queries would show identical chunk id sets query for query: the "
            "retriever cannot tell the two accounts apart. The leak is only visible "
            "once you cross those identical retrieved sets against the entitlement "
            "map, which is exactly the step that reading either account's final "
            "answer would skip."
        ),
    ),
    sources=(
        "arXiv:2408.04870 (2024-08-09), ConfusedPilot, tested against production Microsoft 365 "
        "Copilot over SharePoint: compliance check runs after generation, cached unauthorized "
        "content shaped answers for a measured 164.2 +/- 3.25 seconds after deletion, phantom "
        "documents persisted 42.4 +/- 2.06 seconds",
        "learn.microsoft.com, Protect your Microsoft 365 Copilot data with Microsoft 365 "
        "security tools (updated 2026-10-26), Microsoft's own guidance that Copilot surfaces "
        "whatever the asking identity can already read, and that the fix is access review and "
        "restricted content discovery at the retrieval boundary, not output filtering",
    ),
)

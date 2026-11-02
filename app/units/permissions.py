"""Unit 19: permissions checked above retrieval, so Ledger's prompt already escaped the check.

Ledger's access control sits in the application layer instead of in the
retriever, and diffing retrieved chunk ids across two underwriters with
different deal entitlements catches the leak that reading answers never will.
Numbers and citations verified against primary sources; see UNIT.sources.
"""

from app.units.types import Choice, Exercise, Probe, Unit


def solve(data: dict) -> float:
    """Reference answer to this unit's exercise, run by tests/test_units.py.

    It exists so `Exercise.expected` is a measured number rather than one
    somebody typed beside a fixture. Reading it before attempting the exercise
    is reading the answer key.
    """
    user = "contractor_jdoe"
    allowed = set(data["entitlements"][user])
    categories = data["chunk_categories"]
    retrieved = [
        chunk_id
        for entry in data["retrievals"][user]
        for chunk_id in entry["chunk_ids"]
    ]
    leaked = sum(1 for chunk_id in retrieved if categories[chunk_id] not in allowed)
    return leaked / len(retrieved)


UNIT = Unit(
    slug="permissions",
    number=19,
    part="governance",
    title="Permissions checked above retrieval, so Ledger's prompt already escaped the check",
    failure=(
        "Ledger's retriever runs against the whole document index "
        "regardless of which underwriter is asking. So clauses from deals "
        "that underwriter may not read enter the prompt before any access "
        "check runs."
    ),
    detection="Diff the retrieved chunk ids across two underwriters with different deal entitlements, never Ledger's answers.",
    brief=(
        "The team wired Ledger's access control exactly once, at the edge of "
        "the request. The app authenticates the underwriter, loads their "
        "role, and the endpoint decides whether they may ask Ledger "
        "anything at all. That check answers one question: can this person "
        "use the system. It has nothing to say about which credit "
        "agreements, amendments or side letters the retriever is about to "
        "pull back for them.",
        "The retriever sits below that gate. It queries a shared vector "
        "index built from every document the lender has ingested, across "
        "every borrower and every deal. It ranks chunks by semantic "
        "similarity to the question, not by who is holding the question. "
        "Unless someone deliberately filters the candidates the retriever "
        "considers by caller entitlement before it runs, the retriever "
        "will return the best-matching clauses. It does this whether or "
        "not the lender staffed that underwriter on the deal.",
        "The phrase the prompt has already escaped the check describes "
        "what happens next with precision. By the time an authorization "
        "check could run on Ledger's answer, the restricted clause is no "
        "longer a document sitting in an index. It is tokens inside the "
        "context window the model is conditioning on.",
        "The model can summarize it, paraphrase it, cite it, or fold one "
        "of its terms into a sentence about a different borrower "
        "entirely. None of those paths require the model to reproduce the "
        "clause verbatim for the information to have leaked. A filter "
        "applied to the final answer can catch a direct quote. It cannot "
        "catch a leverage ratio from another deal that shaped a "
        "conclusion. It cannot catch an answer that would not exist without "
        "the side letter that fed it.",
        "ConfusedPilot, published against a production deployment of "
        "Microsoft 365 Copilot running over SharePoint, is a working "
        "demonstration of a version of this timing gap. The paper walks "
        "the mechanism through a fictional company it invents for the "
        "purpose. A low-privilege account seeds a fake sales report into a "
        "shared store. A compliance or deletion check only runs late in "
        "the pipeline, after retrieval has already cached the chunk and "
        "folded it into a draft answer. That narrative is an illustration "
        "rather than a reported incident, and it is worth reading it as "
        "one.",
        "The measurements behind it are separate, and they are real. The "
        "authors connected to an actual Microsoft 365 Copilot instance "
        "over actual SharePoint. They filled it with a corpus they "
        "generated from HotpotQA, deployed at enterprise scale, 500 "
        "folders of 1,000 files, but synthetic rather than real "
        "organizational records.",
        "Two timings matter and they are easy to transpose. Deleting a "
        "seeded malicious document still left it shaping answers for 42.4 "
        "seconds, plus or minus 2.06. The case closer to the subject of "
        "this unit is a document that had been over-shared, after which "
        "someone revoked its access. That document still kept surfacing "
        "for 164.2 seconds, plus or minus 3.25. The access-control failure "
        "is the longer-lived of the two. Ledger has both cases: a side "
        "letter pulled back out of a deal room, and an amendment "
        "superseded and withdrawn.",
        "Microsoft publishes its own guidance about Copilot oversharing, "
        "and it makes the same point from the side of the defender instead "
        "of the attacker. Copilot answers with whatever the identity of "
        "the asking user can already technically read across SharePoint, "
        "OneDrive, and Teams. That means years of permission sprawl, "
        "sitting in a search index with nobody noticing, becomes visible "
        "the moment an assistant can summarize it on request. A lender's "
        "document store collects the same sprawl, deal folders left open "
        "to a team that staffed up and rotated off. Ledger is what "
        "makes it answerable.",
        "The fix from Microsoft is not a smarter filter on the output of "
        "Copilot. It is tooling aimed at the retrieval boundary itself: "
        "access reviews, sensitivity labels, and a restricted content "
        "discovery control. That control removes a site from the "
        "candidate set of the assistant before a query ever reaches it. "
        "That is the same boundary this unit asks you to test.",
        "Testing this by reading Ledger's answers is the trap, and it is a "
        "comfortable one. The model usually declines or hedges "
        "when asked about a borrower it has no business discussing, and "
        "the test passes. A refusal on the surface tells you nothing about "
        "what already sat in the context window when the model generated "
        "that refusal. Nobody tried a hundred other phrasings of the same "
        "question.",
        "The only test that measures the boundary where it actually lives "
        "is a diff. Run the same covenant questions as two accounts with "
        "different deal entitlements, and log the chunk ids each retrieval "
        "returned before generation ever starts. Then compare the sets "
        "directly against what each account is actually entitled to read. "
        "If the retrieved set of a restricted account contains chunk ids "
        "from categories outside its entitlement, you have measured a "
        "leak. This holds independent of whatever Ledger chose to say "
        "about it.",
    ),
    builds_on=(
        "All four parts before it. Every retrieval unit so far assumed the "
        "index was fair game, and Ledger's index holds documents the person "
        "asking is not entitled to read."
    ),
    probes=(
        Probe(
            id="where-the-check-sits",
            asks=(
                "Ledger is built the usual RAG (Retrieval-Augmented Generation) way. "
                "Where does its access control check "
                "actually run relative to the retrieval call?"
            ),
            choices=(
                Choice("a", "Before the embedding query is built, so clauses the underwriter may not read are never embedded"),
                Choice("b", "Inside the vector index itself, which filters by caller identity automatically"),
                Choice("c", "At the edge of the request or after generation, with the retriever itself entitlement-blind"),
                Choice("d", "There is no single place, every layer re-checks independently"),
            ),
            answer="c",
            because=(
                "Authentication at the edge answers whether an underwriter may use "
                "Ledger at all, not which deals they may retrieve from. Unless "
                "someone adds entitlement filtering as an explicit pre-filter on the "
                "candidates the retriever considers, the retriever ranks the whole "
                "index by similarity alone. Any check on the output then comes after "
                "the clause already sits inside the prompt."
            ),
        ),
        Probe(
            id="escaped-the-check",
            asks=(
                "A clause from another borrower's side letter enters Ledger's prompt, "
                "and the answer never quotes it directly. In what sense has it leaked?"
            ),
            choices=(
                Choice("a", "It has not leaked, since no restricted text appears in the visible answer"),
                Choice("b", "It leaked only if Ledger cites the restricted document by name"),
                Choice("c", "It can leak through a summary, an inferred term, or a ratio that shaped the answer, with no verbatim quote required"),
                Choice("d", "It leaked only if the same chunk later appears in a citation list"),
            ),
            answer="c",
            because=(
                "Once the tokens of a clause are part of the context the model is "
                "conditioning on, its content can shape the answer. It can influence "
                "word choice, an inferred conclusion, or a threshold, all without a "
                "direct quote. A filter looking for a verbatim match on the final "
                "text will pass a paraphrase that still carries the restricted "
                "term."
            ),
        ),
        Probe(
            id="why-answers-are-the-wrong-test",
            asks=(
                "From a restricted account you ask Ledger about another borrower's "
                "covenant package a dozen different ways, and it declines or hedges "
                "every time. What has this actually told you about the "
                "access-control boundary?"
            ),
            choices=(
                Choice("a", "The boundary is sound, since no restricted clause reached the underwriter"),
                Choice("b", "Close to nothing, because whether Ledger is willing to answer is a different variable from whether retrieval pulled the restricted clause into the prompt"),
                Choice("c", "The boundary is sound for this question, though you should still check other phrasings"),
                Choice("d", "The retriever is correctly filtering by entitlement, since a hedge implies no restricted clause matched"),
            ),
            answer="b",
            because=(
                "A refusal is a property of the model, not of Ledger's retrieval "
                "pipeline. It tells you nothing about whether the restricted clause "
                "was already sitting in the context window when the refusal "
                "happened. Twelve declined phrasings leave the thirteenth untested, "
                "and none of them substitute for looking at what the retriever "
                "actually returned. That is why the only test that measures this "
                "boundary is a diff of retrieved chunk ids against the entitlement "
                "map, done before generation. It is not a read of what Ledger "
                "said afterward."
            ),
        ),
    ),
    exercise=Exercise(
        asks=(
            "A fixture ships with this unit: 65 queries, each run through one "
            "entitlement-blind retriever as two accounts with different "
            "entitlements. It also ships the entitlement map and a category label "
            "for every chunk in the index. The queries are ordinary internal "
            "lookups rather than covenant questions, and the shape is the one "
            "Ledger has. Measure the leak for the restricted account, "
            "contractor_jdoe. Of all the chunks retrieved for that account across "
            "all 65 queries, what fraction belong to a category contractor_jdoe "
            "may not read? Post that fraction."
        ),
        fixture_path="fixtures/permissions/retrieval_by_user.json",
        fixture_note=(
            "entitlements maps each of two account ids to the list of chunk "
            "categories it may read. chunk_categories maps every chunk id in the "
            "index to exactly one category, while queries lists the 65 query ids "
            "and their text. retrievals maps each account id to a list of 65 "
            "entries. Each entry has an executed query id and the list of chunk "
            "ids the retriever actually returned for it, top 8 per query. The "
            "retriever is entitlement-blind, the way Ledger's is, so diffing the "
            "two accounts' retrieved chunk ids against each other will show zero "
            "difference. That is why the diff alone is not the measurement, and "
            "you still need the entitlement map to find the leak."
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
            '# retrievals is a list of {"query_id": ..., "chunk_ids": [...]},\n'
            '# so flattening it gives every chunk id this account was handed.\n'
            'retrieved = [\n'
            '    chunk_id\n'
            '    for entry in retrievals\n'
            '    for chunk_id in entry["chunk_ids"]\n'
            ']\n'
            '\n'
            'print("queries run as this account:", len(retrievals))\n'
            'print("categories the account may read:", sorted(allowed_categories))\n'
            "# A quick look at the other account proves the retriever cannot\n"
            "# tell them apart, which is why a diff is not the measurement.\n"
            'other = [\n'
            '    chunk_id\n'
            '    for entry in fixture["retrievals"]["fulltime_asmith"]\n'
            '    for chunk_id in entry["chunk_ids"]\n'
            ']\n'
            'print("chunk ids identical to the entitled account:", retrieved == other)\n'
            'print("categories it was actually handed:",\n'
            '      sorted({chunk_categories[chunk_id] for chunk_id in retrieved}))\n'
            'print("chunk ids it was handed in total:", len(retrieved))\n'
            '\n'
            "# TODO: those two category lists are not the same list. Decide what\n"
            "# makes a retrieved chunk a leak for this account, and what the\n"
            "# right denominator is for a rate you would hand an examiner: the\n"
            "# queries, the chunks, or the index. Print that rate.\n"
        ),
        metric="leaked_chunk_rate",
        expected=0.6404,
        tolerance=0.0005,
        because=(
            "contractor_jdoe may read only the public and onboarding categories, "
            "but the retriever ranks every query against the full six-category "
            "index without knowing that. Across the 65 queries, the retrievals "
            "of contractor_jdoe pulled 520 chunks total. Of those, 333, about "
            "64.0 percent, came from finance, legal, eng, or hr, categories "
            "outside the entitlement of that account. In Ledger the category is "
            "a deal room or a restricted side letter instead, and the mechanism "
            "is the same one. A diff against the retrievals of fulltime_asmith "
            "would show identical chunk id sets, since the retriever cannot tell "
            "the two accounts apart. The leak is only visible once you cross "
            "those identical sets against the entitlement map, the exact step "
            "that reading either account's answer would skip."
        ),
    ),
    sources=(
        "arXiv:2408.04870 (2024-08-09), ConfusedPilot, run against a live Microsoft 365 Copilot "
        "instance over SharePoint with a HotpotQA-generated corpus at enterprise scale: the "
        "compliance check runs after generation, and Table IV measures a revoked-access "
        "document still surfacing for 164.2 +/- 3.25 seconds, a deleted malicious document "
        "for 42.4 +/- 2.06 seconds",
        "learn.microsoft.com/en-us/microsoft-365/copilot/microsoft-365-copilot-privacy, Data, "
        "Privacy, and Security for Microsoft Copilot (updated 2026-10-26), Microsoft's own "
        "statement that Copilot surfaces only what the asking identity can already read, and "
        "that Restricted Content Discovery keeps a site out of the candidate set at the "
        "retrieval boundary rather than filtering the output",
    ),
)

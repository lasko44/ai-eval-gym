"""The glossary for ai-eval-gym.

Every acronym in this app's copy gets its full name here, and every
expansion comes from a source this project actually fetched. Where a
source could not confirm an expansion, the entry says so instead of
guessing. See the project's own writing standard in
docs/ste100/rules.md for the five rules this file's prose follows: a
25 word sentence limit, a six sentence paragraph limit, active voice,
no contractions, and no semicolons.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Term:
    term: str                 # as it appears in the copy, for example "HNSW"
    expansion: str | None     # the full name, or None when the term is not an acronym
    definition: str           # two to four plain sentences
    sources: tuple[str, ...] = field(default_factory=tuple)
    verified: bool = True     # False when you could not confirm the expansion


TERMS: tuple[Term, ...] = (
    Term(
        term="A100",
        expansion=None,
        definition=(
            "A100 is a product name rather than an acronym, so the letter "
            "and the number stand for nothing on their own. The NVIDIA A100 "
            "is a graphics processing unit built for data "
            "centers and for AI work. NVIDIA released it in 2020 as part of "
            "its Ampere product line. This app's inference economics unit "
            "cites measurements that researchers took on a single A100, "
            "including throughput and latency across different batch sizes."
        ),
        sources=(
            "nvidia.com/en-us/data-center/a100",
            "en.wikipedia.org/wiki/Ampere_(microarchitecture)",
        ),
    ),
    Term(
        term="ablation",
        expansion=None,
        definition=(
            "An ablation removes one component of a system and then measures "
            "how much performance drops. The drop is that component's "
            "contribution, measured rather than argued. Allen Newell "
            "introduced the word in a 1974 speech recognition tutorial, "
            "borrowing it from surgery. This app's multi-hop unit cites an "
            "ablation that removed the reranker from a retrieval pipeline."
        ),
        sources=("en.wikipedia.org/wiki/Ablation_(artificial_intelligence)",),
    ),
    Term(
        term="ACM",
        expansion="Association for Computing Machinery",
        definition=(
            "The Association for Computing Machinery is a nonprofit society "
            "for people who work in computing, founded in 1947. It publishes "
            "Communications of the ACM, a monthly magazine for the field. "
            "This app cites that magazine as the source of Dean and "
            "Barroso's 2013 paper on tail latency."
        ),
        sources=("en.wikipedia.org/wiki/Communications_of_the_ACM",),
    ),
    Term(
        term="amendment",
        expansion=None,
        definition=(
            "An amendment is a change to the provisions of an agreement that "
            "already exists. A lender and a borrower amend a credit agreement "
            "when they want different terms, and they do this repeatedly over "
            "a loan's life. The amendment does not replace the original "
            "document, so the language in force is the original clause as "
            "every later amendment left it. That is why Ledger has to read "
            "several documents together, and why retrieving only the original "
            "produces a confident wrong answer."
        ),
        sources=(
            "www.lw.com/admin/Upload/Documents/BoJ_US_Corporate_and_Bank_Finance-second-edition.pdf",
        ),
    ),
    Term(
        term="ANN",
        expansion="Approximate Nearest Neighbor",
        definition=(
            "Approximate nearest neighbor search finds vectors close to a "
            "query vector, without a guarantee of the exact closest match. "
            "It trades a small amount of accuracy for a large gain in "
            "speed. HNSW and IVF are two common ways to build an "
            "approximate nearest neighbor index. ANN-Benchmarks is a "
            "public project that compares methods like these on the same "
            "datasets."
        ),
        sources=("arxiv.org/abs/1807.05614",),
    ),
    Term(
        term="API",
        expansion="Application Programming Interface",
        definition=(
            "An application programming interface is the set of rules that "
            "lets one piece of software call another. A model provider "
            "publishes an API so a client program can send a prompt and "
            "receive a response. This app treats the API as the boundary "
            "where cost, latency, and token counts get measured."
        ),
    ),
    Term(
        term="ASR",
        expansion="Attack Success Rate",
        definition=(
            "Attack success rate is the share of adversarial prompts that "
            "get past a safety filter and reach the model. A guardrail "
            "with a high attack success rate blocks few real attacks. This "
            "app's guardrails unit cites attack success rate numbers for "
            "six commercial filters against six evasion techniques, where "
            "100 percent means every attempt got through."
        ),
        sources=("arxiv.org/html/2504.11168",),
    ),
    Term(
        term="base rate",
        expansion=None,
        definition=(
            "The base rate is the true frequency of an outcome in a "
            "population, before any model makes a prediction. Two groups "
            "can have different base rates of the same outcome, for "
            "reasons outside a model's control. This app's fairness unit "
            "uses the base rate to show why three fairness tests cannot "
            "all pass at once when base rates differ between groups."
        ),
    ),
    Term(
        term="BEIR",
        expansion="Benchmarking Information Retrieval",
        definition=(
            "BEIR is a benchmark that tests a retrieval method across many "
            "different domains and tasks at once, instead of just one. "
            "Researchers built it so a method that looks strong on one "
            "dataset gets checked against many others. This app's "
            "reranking unit cites BEIR results where a plain keyword "
            "method, BM25, still beat some neural rerankers on several "
            "datasets. The paper that introduced BEIR does not spell out "
            "the letters itself, so this project confirmed the expansion "
            "from a secondary glossary source instead."
        ),
        sources=(
            "arxiv.org/abs/2104.08663",
            "zilliz.com/glossary/beir",
        ),
    ),
    Term(
        term="BM25",
        expansion="Best Match 25",
        definition=(
            "BM in BM25 stands for best matching. The number 25 marks it "
            "as the 25th scoring formula the Okapi retrieval project tried "
            "before the team settled on this one. Stephen Robertson and "
            "colleagues at City University London developed it for the "
            "Okapi system in the 1980s and 1990s. BM25 ranks documents by "
            "term overlap with a query, weighted by how rare and how often "
            "each term appears. This app's reranking unit uses BM25 as the "
            "plain keyword baseline that a neural reranker must beat."
        ),
        sources=("en.wikipedia.org/wiki/Okapi_BM25",),
    ),
    Term(
        term="borrower",
        expansion=None,
        definition=(
            "A borrower is the company that borrows money under a credit "
            "agreement. In Ledger's world the borrower is a business rather "
            "than a person, and it carries the covenants the agreement "
            "imposes. Every question an underwriter asks Ledger concerns one "
            "borrower's own documents. The permissions unit turns that into a "
            "test: a retriever that returns one borrower's clauses to a user "
            "entitled to another has leaked."
        ),
        sources=(
            "www.lw.com/admin/Upload/Documents/BoJ_US_Corporate_and_Bank_Finance-second-edition.pdf",
        ),
    ),
    Term(
        term="Brier score",
        expansion=None,
        definition=(
            "The Brier score measures how well a predicted probability "
            "matches the actual outcome, from 0 for a perfect forecast to "
            "1 for the worst case. It squares the difference between the "
            "predicted probability and the outcome, which is 1 or 0. A "
            "model that says 90 percent and is right scores better than "
            "one that says 90 percent and is wrong. This app uses it to "
            "score calibration, not only whether the final answer was "
            "correct."
        ),
    ),
    Term(
        term="calibration",
        expansion=None,
        definition=(
            "Calibration means that when a model says it is 70 percent "
            "confident, it is right about 70 percent of the time across "
            "many such predictions. A model can be accurate overall and "
            "still be poorly calibrated, when its confidence numbers do "
            "not match reality. This app's fairness unit treats "
            "calibration as one of three properties a fair model might "
            "need."
        ),
    ),
    Term(
        term="calibration within groups",
        expansion=None,
        definition=(
            "Calibration within groups asks whether a model's confidence "
            "numbers match reality separately inside each demographic "
            "group, not only overall. Jon Kleinberg and coauthors proved "
            "that calibration within groups, demographic parity, and "
            "equalized odds cannot all hold together when groups have "
            "different base rates. This app's fairness unit walks through "
            "that proof with a worked example."
        ),
    ),
    Term(
        term="chunk",
        expansion=None,
        definition=(
            "A chunk is one piece of a document that a retrieval system "
            "stores and searches as a single unit. Splitting a document "
            "into chunks lets a retrieval step find and return only the "
            "relevant part, instead of the whole file. This app's "
            "permissions unit tracks chunk ids to catch a document leaking "
            "to a user who should not see it."
        ),
    ),
    Term(
        term="COMPAS",
        expansion="Correctional Offender Management Profiling for Alternative Sanctions",
        definition=(
            "COMPAS is a commercial risk scoring tool that United States "
            "courts use to predict whether a defendant will reoffend. "
            "Northpointe built it in 1998, and the company is now called "
            "Equivant. A 2016 ProPublica investigation found the tool was "
            "equally accurate for Black and white defendants, yet made "
            "opposite kinds of errors between the two groups. This app's "
            "fairness unit uses that COMPAS data to show how one accuracy "
            "number can hide that disagreement."
        ),
        sources=("en.wikipedia.org/wiki/COMPAS_(software)",),
    ),
    Term(
        term="context window",
        expansion=None,
        definition=(
            "The context window is the maximum number of tokens a model "
            "can hold in a single prompt. It covers everything the model "
            "reads before it writes a reply. A longer context window lets a "
            "model see more text at once, but it does not guarantee the "
            "model uses all of that text well. This app's context rot unit "
            "shows accuracy can fall as useful information gets buried in "
            "a longer context window."
        ),
    ),
    Term(
        term="continuous batching",
        expansion=None,
        definition=(
            "Continuous batching is a serving technique. It adds a new "
            "request to a running batch as soon as a slot opens, instead "
            "of waiting for the whole batch to finish together. It keeps a "
            "GPU busier than static batching does. This app's inference "
            "economics unit cites a measured throughput gain from "
            "switching to continuous batching alone."
        ),
    ),
    Term(
        term="covenant",
        expansion=None,
        definition=(
            "A covenant is a promise inside a credit agreement. The borrower "
            "agrees to do something, to avoid something, or to keep a number "
            "inside a limit. A covenant limiting distributions is the kind an "
            "underwriter asks Ledger about. Lenders then amend covenants "
            "repeatedly, so the promise in force today is rarely the one the "
            "original agreement printed. That gap is what makes Ledger hard "
            "to evaluate, because an answer built on the original clause "
            "reads correct and is wrong."
        ),
        sources=(
            "www.lw.com/admin/Upload/Documents/BoJ_US_Corporate_and_Bank_Finance-second-edition.pdf",
            "www.occ.gov/publications-and-resources/publications/comptrollers-handbook/files/leveraged-lending/pub-ch-leveraged-lending.pdf",
        ),
    ),
    Term(
        term="credit agreement",
        expansion=None,
        definition=(
            "A credit agreement is the legal document in which one or more "
            "lenders agree to lend money to a borrower. It sets out the "
            "mechanics of the loan and it carries the covenants, the "
            "representations and the remedies the lenders get after a "
            "default. It runs to hundreds of pages, and later amendments "
            "change parts of it without reprinting it. Ledger exists to "
            "answer questions about this document and the amendments stacked "
            "on top of it."
        ),
        sources=(
            "www.lw.com/admin/Upload/Documents/BoJ_US_Corporate_and_Bank_Finance-second-edition.pdf",
        ),
    ),
    Term(
        term="deal room",
        expansion=None,
        definition=(
            "A deal room is the folder, or the website behind a login, that "
            "holds every document for one loan. Lenders use it to share "
            "drafts and diligence material with the people entitled to see "
            "them. A law firm glossary prints the same idea as a data room, "
            "the actual or virtual room that holds diligence material. The "
            "entitlement to a deal room is what decides which clauses a given "
            "underwriter may read. This app's permissions unit measures a "
            "retriever that ignores that entitlement."
        ),
        sources=(
            "www.lw.com/admin/Upload/Documents/BoJ_US_Corporate_and_Bank_Finance-second-edition.pdf",
            "app/units/permissions.py",
        ),
    ),
    Term(
        term="decode",
        expansion=None,
        definition=(
            "Decode is the phase of generation where a model produces each "
            "new output token, one at a time, after it has read the "
            "prompt. Each decode step reads only the previous token and "
            "the cached state, so it moves far less data than reading the "
            "full prompt does. That makes decode memory bound, while "
            "reading the prompt is compute bound instead. This app's "
            "inference economics unit uses the split between prefill and "
            "decode to explain why batch size changes cost so much."
        ),
    ),
    Term(
        term="demographic parity",
        expansion=None,
        definition=(
            "Demographic parity asks whether a model predicts a positive "
            "outcome for the same share of people in each demographic "
            "group. It compares outcome rates across groups and ignores "
            "whether those outcomes were correct. This app's fairness unit "
            "shows demographic parity is one of three fairness tests that "
            "can conflict with each other."
        ),
    ),
    Term(
        term="distribution",
        expansion=None,
        definition=(
            "Distribution means two different things in this course. In "
            "Ledger's loan documents it is cash or property that a borrower "
            "pays out to its own owners, and a dividend is one kind. In "
            "statistics it is the shape of a set of values, which is what a "
            "latency distribution or a label distribution means. Lenders "
            "restrict the first kind, because money leaving the borrower is "
            "money that cannot repay the loan."
        ),
        sources=(
            "www.lw.com/admin/Upload/Documents/BoJ_US_Corporate_and_Bank_Finance-second-edition.pdf",
        ),
    ),
    Term(
        term="DOI",
        expansion="Digital Object Identifier",
        definition=(
            "A digital object identifier is a permanent name for a "
            "document, so a reader can still find it after the publisher "
            "moves the page. The International Organization for "
            "Standardization defines the system in ISO 26324, Information "
            "and documentation, Digital object identifier system. The "
            "registry explains that the name means a digital identifier "
            "of an object, and not an identifier of a digital object. The "
            "object itself can be physical. This app's latency tails unit "
            "gives a DOI for the 2013 paper it cites, because that paper "
            "sits behind a publisher page that moves."
        ),
        sources=(
            "www.doi.org/the-identifier/what-is-a-doi/",
            "www.iso.org/standard/88862.html",
        ),
    ),
    Term(
        term="EBITDA",
        expansion="Earnings Before Interest, Taxes, Depreciation, and Amortization",
        definition=(
            "Earnings before interest, taxes, depreciation, and amortization "
            "is a rough measure of the cash a business generates from "
            "operating. Lenders use it as the denominator of a leverage "
            "ratio, so a covenant limit depends on it. The Office of the "
            "Comptroller of the Currency publishes a leveraged lending "
            "handbook that spells the letters out. That handbook measures "
            "leverage as total debt over EBITDA. Nothing in this app computes "
            "EBITDA, and a reader needs it only to read a leverage covenant."
        ),
        sources=(
            "www.occ.gov/publications-and-resources/publications/comptrollers-handbook/files/leveraged-lending/pub-ch-leveraged-lending.pdf",
        ),
    ),
    Term(
        term="EM",
        expansion="Exact Match",
        definition=(
            "Exact match is a scoring rule that gives full credit only "
            "when a model's answer is character for character identical "
            "to the correct answer. It gives zero credit for an answer "
            "that is right in substance but phrased differently. This "
            "app's multi-hop unit reports a drop in exact match points "
            "when a retrieval loop gets cut short."
        ),
    ),
    Term(
        term="EY",
        expansion=None,
        definition=(
            "EY is the name of an accounting and consulting firm, and the "
            "letters do not stand for separate words today. The firm "
            "states that EY refers to the global organization. It can also "
            "refer to one or more of the member firms of Ernst & Young "
            "Global Limited, each a separate legal entity. This project "
            "treats EY as a name rather than an acronym. This app's agent "
            "traceability unit cites a survey that the Institute of "
            "International Finance and EY ran together."
        ),
        sources=(
            "www.ey.com/en_gl/legal-and-privacy",
        ),
    ),
    Term(
        term="equalized odds",
        expansion=None,
        definition=(
            "Equalized odds asks whether a model's error rates match "
            "across demographic groups, for both the false positive rate "
            "and the false negative rate. It does not require the groups "
            "to get the same overall share of positive outcomes. A model "
            "can satisfy equalized odds while failing demographic parity, "
            "when the groups have different base rates. This app's "
            "fairness unit measures the equalized odds gap as the larger "
            "of the two group error rate gaps."
        ),
    ),
    Term(
        term="eval",
        expansion=None,
        definition=(
            "An eval, short for evaluation, is one measurement of whether a "
            "system does its job. The word names both the measurement and the "
            "suite of cases it runs over. An eval is not a unit test: it "
            "reports a score on real inputs, not a pass or a fail on an "
            "assertion. Every unit in this app builds one eval of Ledger and "
            "then attacks the number it produced."
        ),
    ),
    Term(
        term="eval set",
        expansion=None,
        definition=(
            "An eval set is the fixed collection of cases an eval runs over, "
            "each one with a known correct answer. It plays the role a test "
            "suite plays in application code. The difference is that its "
            "cases come from real traffic and a human supplied its answers. A "
            "frozen eval set rots, because production keeps producing "
            "failures the set never held. Several units in this app attack "
            "the eval set itself, over contamination, over sampling, and over "
            "size."
        ),
    ),
    Term(
        term="FAISS",
        expansion="Facebook AI Similarity Search",
        definition=(
            "FAISS is an open source library from Meta AI Research for "
            "searching large collections of vectors quickly. It implements "
            "both HNSW and IVF, two different ways to trade search speed "
            "against recall. FAISS also publishes memory formulas for its "
            "own indexes, which this app's index tradeoff unit uses "
            "directly."
        ),
        sources=(
            "github.com/facebookresearch/faiss",
            "engineering.fb.com/2017/03/29/data-infrastructure/faiss-a-library-for-efficient-similarity-search",
        ),
    ),
    Term(
        term="fan-out",
        expansion=None,
        definition=(
            "Fan-out is the pattern where one incoming request triggers "
            "many parallel calls to other services before it can finish. "
            "The slowest of those parallel calls sets the floor for the "
            "whole request's latency. This app's latency tails unit "
            "explains why fan-out raises p99 latency more than the average "
            "backend call would suggest."
        ),
    ),
    Term(
        term="fixture",
        expansion=None,
        definition=(
            "A fixture, in this app, is the data file a unit ships so a "
            "reader can run the unit's measurement without a running system. "
            "Each fixture holds a known answer, so the exercise checks a "
            "number rather than an opinion. The fixtures live in the fixtures "
            "directory, one folder per unit, and the runner copies only the "
            "one fixture an exercise names. The word is common in testing "
            "generally, where it means any prepared input a test runs against."
        ),
        sources=("app/runner.py", "app/units/types.py"),
    ),
    Term(
        term="flip rate",
        expansion=None,
        definition=(
            "Flip rate is the share of judgments that change when an LLM "
            "judge sees the same pair of answers in the opposite order. A "
            "low flip rate shows the judge is consistent, but it does not "
            "show the judge is correct. This app's judges unit uses flip "
            "rate as an upper bound on how much a judge's bias could cost "
            "an evaluation."
        ),
    ),
    Term(
        term="golden dataset",
        expansion=None,
        definition=(
            "A golden dataset is a set of inputs with answers a human checked "
            "and signed off, used as the reference an eval scores against. "
            "The name claims more than it delivers, because the humans who "
            "labeled it disagree with each other and with themselves. Measure "
            "that disagreement before you treat the labels as truth. This "
            "app's judges unit shows what happens to an agreement number once "
            "you correct for chance."
        ),
    ),
    Term(
        term="GPT",
        expansion="Generative Pre-trained Transformer",
        definition=(
            "A Generative Pre-trained Transformer is a language model that "
            "OpenAI first trains on a broad mass of text, then adapts for "
            "a specific task. The three words describe this process: "
            "generative text, pre-training on general data, and the "
            "transformer architecture it runs on. OpenAI released the "
            "first GPT model in 2018 and later released larger versions. "
            "This app cites named GPT versions, such as GPT-4, in "
            "benchmark results from other researchers' papers."
        ),
        sources=("en.wikipedia.org/wiki/Generative_pre-trained_transformer",),
    ),
    Term(
        term="GPU",
        expansion="Graphics Processing Unit",
        definition=(
            "A graphics processing unit is a chip built to run many small "
            "calculations at the same time, originally for rendering "
            "images. That same design also suits the matrix math behind "
            "training and running language models. This app's inference "
            "economics unit measures throughput and cost per request on a "
            "single GPU, the NVIDIA A100."
        ),
    ),
    Term(
        term="ground truth",
        expansion=None,
        definition=(
            "Ground truth is the answer you treat as correct when you score a "
            "system. It is a decision, not a fact: somebody chose it, and "
            "that choice can be wrong. An eval inherits every error in its "
            "ground truth and reports those errors as the system's errors. "
            "This app's contamination unit starts by checking the instrument "
            "against ground truth, which is the step most teams skip."
        ),
    ),
    Term(
        term="harness",
        expansion=None,
        definition=(
            "A harness, in this app, is the code a reader writes to run a "
            "measurement and post the number back. It is the reader's own "
            "code rather than something this app supplies, and it imports the "
            "pure functions in app/metrics to do the arithmetic. A harness "
            "run records what that code measured, in the reader's own words, "
            "against one sealed cycle. A harness that cannot produce a finite "
            "number has measured nothing, so this app refuses the run rather "
            "than scoring it."
        ),
        sources=("app/models.py", "app/scoring.py"),
    ),
    Term(
        term="HNSW",
        expansion="Hierarchical Navigable Small World",
        definition=(
            "Hierarchical Navigable Small World is a graph-based method "
            "for approximate nearest neighbor search. Malkov and Yashunin "
            "published it in 2016. It links vectors into layers, so a "
            "search starts at a sparse top layer and narrows down through "
            "denser layers below. This app's index tradeoff unit compares "
            "HNSW against IVF on the same fixture to show how the two "
            "trade speed for memory in different ways."
        ),
        sources=("arxiv.org/abs/1603.09320",),
    ),
    Term(
        term="hop",
        expansion=None,
        definition=(
            "A hop is one step in a chain of retrieval and reasoning, "
            "where the answer to one step supplies a fact the next step "
            "needs. A single retrieved passage alone cannot answer a "
            "question that needs two hops. This app's multi-hop unit "
            "measures how much accuracy a system loses when a retrieval "
            "loop stops before it covers every hop a question needs."
        ),
    ),
    Term(
        term="IIF",
        expansion="Institute of International Finance",
        definition=(
            "The Institute of International Finance is a global "
            "association of banks and financial firms, based in "
            "Washington, D.C. It publishes an annual survey on AI use in "
            "financial services together with the professional services "
            "firm EY. This app's agent traceability unit cites the October "
            "2025 edition of that survey."
        ),
        sources=("iif.com/Publications/ID/6322",),
    ),
    Term(
        term="IVF",
        expansion="Inverted File",
        definition=(
            "An inverted file index clusters vectors ahead of time, then "
            "stores each cluster as a list of its own members. A search "
            "checks only the nprobe closest clusters, instead of every "
            "vector in the whole collection. Raising nprobe checks more "
            "clusters and raises both recall and latency together. This "
            "app's index tradeoff unit compares IVF against HNSW at a "
            "matched recall to show which method serves more queries per "
            "second."
        ),
        sources=("github.com/facebookresearch/faiss/wiki/Faiss-indexes",),
    ),
    Term(
        term="JSON",
        expansion="JavaScript Object Notation",
        definition=(
            "JavaScript Object Notation is a lightweight text format for "
            "structuring data as nested keys and values. Despite the name, "
            "any programming language can read and write it, not only "
            "JavaScript. Many exercises in this app ask for an answer "
            "formatted as a JSON object with specific keys, so a checker "
            "can parse it without guessing."
        ),
    ),
    Term(
        term="judge",
        expansion=None,
        definition=(
            "A judge is a model this app uses to score another model's "
            "output. Hand grading stops scaling once Ledger answers questions "
            "all week, so a judge takes over, and its verdict becomes your "
            "measurement. A judge is not an instrument until you have "
            "measured it, because it carries preferences that have nothing to "
            "do with the answers. This app's first unit measures position "
            "bias and chance-corrected agreement before any other number gets "
            "trusted."
        ),
        sources=("app/units/judges.py",),
    ),
    Term(
        term="key-value cache",
        expansion=None,
        definition=(
            "The key-value cache stores the intermediate values a model "
            "computed for every earlier token in a request. It saves the "
            "model from recomputing those values for each new token. "
            "Without this cache, generating each new token would require "
            "reprocessing the entire prompt again. The cache grows with "
            "context length, batch size, and model size. It can become "
            "the limit on how many requests a GPU serves at once. This "
            "app's inference economics unit works through a cache size "
            "calculation for a real model and a real request size."
        ),
    ),
    Term(
        term="Ledger",
        expansion=None,
        definition=(
            "Ledger is the one system this whole course takes apart, and it "
            "is not a product anybody shipped. It answers an underwriter's "
            "questions about private credit loan documents by reading the "
            "credit agreement and the amendments that changed it. Every unit "
            "measures a different part of the same Ledger, so the course "
            "teaches one method instead of twenty separate tricks. Ledger is "
            "a name this project chose, and the system module describes it "
            "once so no unit has to."
        ),
        sources=("app/units/system.py",),
    ),
    Term(
        term="lender",
        expansion=None,
        definition=(
            "A lender is the party that puts up the money in a credit "
            "agreement and collects the repayments. In private credit the "
            "lender is usually a fund rather than a bank. The lender writes "
            "the covenants, grants the waivers, and signs every amendment. "
            "Its view of the documents is the one Ledger has to reproduce. An "
            "underwriter works for the lender."
        ),
        sources=(
            "www.lw.com/admin/Upload/Documents/BoJ_US_Corporate_and_Bank_Finance-second-edition.pdf",
        ),
    ),
    Term(
        term="leverage ratio",
        expansion=None,
        definition=(
            "A leverage ratio compares a company's debt to the cash it "
            "generates, usually total debt divided by EBITDA over the last "
            "four quarters. A credit agreement often carries a covenant "
            "requiring the borrower to keep that ratio under a stated number. "
            "So a question about whether the covenants permit a distribution "
            "can turn on one computed ratio and the limit a later amendment "
            "moved. Watch the word outside lending, where a bank's own "
            "leverage ratio means capital over assets, a different thing."
        ),
        sources=(
            "www.lw.com/admin/Upload/Documents/Books%20of%20Jargon/Book-of-Jargon-European-Capital-Markets-and-Bank-Finance-2nd-Edition.pdf",
            "www.occ.gov/publications-and-resources/publications/comptrollers-handbook/files/leveraged-lending/pub-ch-leveraged-lending.pdf",
        ),
    ),
    Term(
        term="LLM",
        expansion="Large Language Model",
        definition=(
            "A large language model is a neural network trained on a huge "
            "amount of text to predict and generate language. It learns "
            "patterns of grammar, fact, and style from that training data, "
            "without being told explicit rules. This app treats an LLM as "
            "a component that needs measurement, not trust by default, "
            "whether it generates answers or judges other answers."
        ),
    ),
    Term(
        term="ML",
        expansion="Machine Learning",
        definition=(
            "Machine learning is the practice of training a program to "
            "improve at a task from data, instead of writing out every "
            "rule by hand. A large language model is one kind of machine "
            "learning system. This app's routing unit evaluates an ML "
            "router, a smaller trained model that decides which queries "
            "need an expensive retrieval step."
        ),
    ),
    Term(
        term="MPT",
        expansion="MosaicML Pretrained Transformer",
        definition=(
            "MosaicML Pretrained Transformer is a family of open source "
            "language models that the company MosaicML released in 2023. "
            "MPT-7B, the 7 billion parameter version, is one of the models "
            "this app cites in its inference economics benchmarks. "
            "Databricks measured MPT-7B's throughput and latency on a "
            "single A100 across different batch sizes, and this app's "
            "inference economics unit walks through those measurements."
        ),
        sources=(
            "www.kdnuggets.com/2023/05/introducing-mpt7b-new-opensource-llm.html",
            "huggingface.co/mosaicml/mpt-7b-chat",
        ),
    ),
    Term(
        term="MT-Bench",
        expansion="Multi-Turn Benchmark",
        definition=(
            "Multi-Turn Benchmark, MT-Bench, is a set of 80 questions. "
            "Each question needs two connected turns of conversation, so "
            "it tests how well a model holds a dialogue together. "
            "Researchers at LMSYS built it in 2023 to score chat models "
            "with an LLM acting as the judge. This app's judges unit cites "
            "the spread of scores that 21 different judge models gave on "
            "an MT-Bench style question set. The paper that introduced it "
            "calls it a multi-turn question set, without spelling the "
            "acronym out directly. This project also checked a secondary "
            "glossary source to confirm it."
        ),
        sources=(
            "arxiv.org/abs/2306.05685",
            "ai-solutions.daviesmeyer.com/en/glossary/mt-bench",
        ),
    ),
    Term(
        term="NANDA",
        expansion="Networked Agents and Decentralized AI",
        definition=(
            "Networked Agents and Decentralized AI, Project NANDA, is an "
            "MIT Media Lab project. It builds infrastructure so AI agents "
            "from different vendors can find and trust each other. The "
            "2025 report often cited as proof that 95 percent of AI pilots "
            "fail came from this project. MIT's own project page states "
            "this expansion, though other outlets have described it with "
            "slightly different wording."
        ),
        sources=("www.media.mit.edu/projects/mit-nanda/overview",),
    ),
    Term(
        term="nearest rank",
        expansion=None,
        definition=(
            "The nearest rank method computes a percentile by sorting all "
            "the values and picking the one at a specific position in that "
            "sorted list. It is one of several valid ways to define a "
            "percentile, and different tools can disagree slightly "
            "because they use different methods. This app's latency tails "
            "unit uses the nearest rank method to compute p99 from a set "
            "of latencies."
        ),
    ),
    Term(
        term="NIST",
        expansion="National Institute of Standards and Technology",
        definition=(
            "The National Institute of Standards and Technology is a "
            "United States government agency that sets technical "
            "standards, including for cryptography and for AI risk. It "
            "published the AI Risk Management Framework, AI RMF 1.0, in "
            "January 2023 as voluntary guidance for organizations that "
            "build or use AI. This app's agent traceability unit cites "
            "that framework among the sources financial regulators point "
            "to. NIST also defines the SHA family of hash algorithms this "
            "app's sealing step relies on."
        ),
        sources=("www.nist.gov/publications/artificial-intelligence-risk-management-framework",),
    ),
    Term(
        term="NVIDIA",
        expansion=None,
        definition=(
            "NVIDIA is a company that designs graphics processing units "
            "and the software that runs on them. It is the source of "
            "several figures this app cites, including GPU memory "
            "formulas and an inference optimization guide. The A100 is one "
            "of NVIDIA's data center GPU models, used in benchmarks this "
            "app's inference economics unit walks through. NVIDIA is a "
            "company name, not an abbreviation of other words."
        ),
        sources=("nvidia.com/en-us/data-center/a100",),
    ),
    Term(
        term="operative clause",
        expansion=None,
        definition=(
            "The operative clause is the language actually in force right "
            "now, after every amendment and waiver that touched it. The "
            "original credit agreement prints one version, and three later "
            "amendments can leave something different standing. Ledger has to "
            "find the operative clause, not the first one it retrieves, and "
            "that is the whole difficulty. Several units use the phrase, and "
            "the context rot unit holds one operative clause fixed while it "
            "grows the prompt around it."
        ),
        sources=("app/units/system.py", "app/units/context_rot.py"),
    ),
    Term(
        term="OPT",
        expansion="Open Pre-trained Transformer",
        definition=(
            "Open Pre-trained Transformer is a family of language models "
            "that Meta AI released in 2022 to match GPT-3's scale with an "
            "openly shared model. The family ranges from 125 million to "
            "175 billion parameters, and OPT-13B is the 13 billion "
            "parameter version. This app's inference economics unit cites "
            "a measured throughput gain from continuous batching on "
            "OPT-13B running on a single A100."
        ),
        sources=("arxiv.org/abs/2205.01068",),
    ),
    Term(
        term="oracle ceiling",
        expansion=None,
        definition=(
            "The oracle ceiling is the best result a system could reach if "
            "an all-knowing router made every routing decision correctly. "
            "It is a reference point, not a target a real system can "
            "exceed, since a real router cannot know the future. This "
            "app's routing unit insists on reporting the oracle ceiling "
            "next to every routing accuracy number."
        ),
    ),
    Term(
        term="p50",
        expansion=None,
        definition=(
            "p50 is the median, the latency value that half of all "
            "requests finish at or faster than. It describes the typical "
            "request, not the slow ones that cause complaints. This app's "
            "latency tails unit reports p50 alongside p95 and p99 so a "
            "reader can see the whole shape of a latency distribution."
        ),
    ),
    Term(
        term="p95",
        expansion=None,
        definition=(
            "p95 is the latency value that 95 percent of requests finish "
            "at or faster than, leaving the slowest 5 percent above it. It "
            "captures a meaningfully bad request without reaching the "
            "extreme tail. This app's latency tails unit reports p95 "
            "together with p50 and p99 and the load that produced them."
        ),
    ),
    Term(
        term="p99",
        expansion=None,
        definition=(
            "p99 is the latency value that 99 percent of requests finish "
            "at or faster than, so it describes the slowest 1 percent of "
            "traffic. A system can have a fast average and still make 1 "
            "in 100 users wait far longer. This app's latency tails unit "
            "shows that fan-out across several backend calls raises p99 "
            "more than it raises the mean."
        ),
    ),
    Term(
        term="position bias",
        expansion=None,
        definition=(
            "Position bias is a judge's tendency to prefer whichever answer "
            "it reads first, or whichever it reads last, regardless of "
            "content. It is a property of the judge and not of the answers, "
            "so it adds noise to every comparison the judge makes. Measure it "
            "by running each pair in both orders and counting how often the "
            "verdict changes. The number that comes out is the flip rate, and "
            "this app's first unit computes it on 200 pairs."
        ),
    ),
    Term(
        term="prefill",
        expansion=None,
        definition=(
            "Prefill is the phase where a model reads the entire prompt at "
            "once and builds the key-value cache before it writes the "
            "first output token. It is compute bound, since it processes "
            "many tokens together as one large matrix operation. A longer "
            "prompt makes prefill take longer, which is part of why time "
            "to first token rises with prompt length. This app's "
            "inference economics unit contrasts prefill against decode to "
            "explain where GPU time actually goes."
        ),
    ),
    Term(
        term="private credit",
        expansion=None,
        definition=(
            "Private credit means loans that nonbank funds negotiate directly "
            "with a business, instead of loans a bank makes or bonds a market "
            "trades. The Federal Reserve describes it as direct loans to "
            "mid-market companies from private debt funds and business "
            "development companies. Nothing about these loans is public, so "
            "the documents live in a deal room and never reach a filing. That "
            "is why Ledger reads documents rather than a database, and why "
            "only a few people can check its answers."
        ),
        sources=(
            "www.federalreserve.gov/econres/notes/feds-notes/bank-lending-to-private-credit-size-characteristics-and-financial-stability-implications-20250523.html",
        ),
    ),
    Term(
        term="probe",
        expansion=None,
        definition=(
            "A probe, in this app, is one question inside a unit that the "
            "user answers to check understanding of that unit's idea. Each "
            "probe carries its own choices and its own explanation of why "
            "one answer is right. The sealing step records probe answers, "
            "so a later check can compare a teardown cycle's claims "
            "against what the user actually answered. Probe is this app's "
            "own name for that "
            "question type, not a term borrowed from a published "
            "benchmark."
        ),
    ),
    Term(
        term="RAG",
        expansion="Retrieval-Augmented Generation",
        definition=(
            "Retrieval-Augmented Generation is an approach where a model "
            "retrieves relevant passages from an outside source before it "
            "generates an answer. It relies on that outside source "
            "instead of only on training data. Lewis and coauthors "
            "introduced the term in a 2020 paper "
            "on knowledge-intensive language tasks. A RAG system can still "
            "answer incorrectly if its retrieval step returns the wrong "
            "passages, even when the model itself works well. Several "
            "units in this app, including permissions and multi-hop, "
            "evaluate specific failure modes of RAG systems."
        ),
        sources=("arxiv.org/abs/2005.11401",),
    ),
    Term(
        term="recall at k",
        expansion=None,
        definition=(
            "Recall at k measures whether the correct document appears "
            "anywhere in the top k results a retrieval system returns, not "
            "only whether it ranks first. A system can have strong recall "
            "at k and still rank the correct document poorly among those k "
            "results. This app's reranking unit treats recall at k as a "
            "separate question from ranking quality."
        ),
    ),
    Term(
        term="regression gate",
        expansion=None,
        definition=(
            "A regression gate is a rule that blocks a release when a "
            "measured number falls below the one the last release scored. It "
            "turns an eval into a deploy decision, the way a failing test "
            "blocks a merge. A gate inherits every weakness of the eval "
            "behind it, so a gate on a noisy number blocks good releases and "
            "passes bad ones. The release gates unit shows a gate whose "
            "threshold sits inside the spread of an unchanged suite, so one "
            "run in four flips."
        ),
        sources=("app/units/release_gates.py",),
    ),
    Term(
        term="reranker",
        expansion=None,
        definition=(
            "A reranker is a second model that reorders a list of "
            "retrieved documents. It uses a closer and more expensive "
            "comparison than the first retrieval step could afford. The "
            "first retrieval step, often BM25 or an embedding search, must "
            "run fast over the whole collection, so it trades some "
            "accuracy for speed. A reranker only scores the smaller "
            "shortlist that step already found. This app's reranking unit "
            "cites BEIR results where adding a reranker improved results "
            "most of the time, but not always."
        ),
    ),
    Term(
        term="restricted payment",
        expansion=None,
        definition=(
            "A restricted payment is money the borrower sends to its owners "
            "or to junior lenders, which the credit agreement limits. "
            "Dividends, share buybacks and early repayment of subordinated "
            "debt all count. Nearly every credit agreement carries a covenant "
            "capping these payments, because each one moves value away from "
            "the lender. An underwriter who asks Ledger whether a "
            "distribution clears the covenants is asking about this one."
        ),
        sources=(
            "www.lw.com/admin/Upload/Documents/BoJ_US_Corporate_and_Bank_Finance-second-edition.pdf",
        ),
    ),
    Term(
        term="RULER",
        expansion=None,
        definition=(
            "RULER is the name of a benchmark. It measures how much of a "
            "model's advertised context window it can actually use, not "
            "just how large that window is. NVIDIA built it and published "
            "it on GitHub and arXiv in 2024. Despite the capital letters, "
            "neither the paper nor NVIDIA's own repository spells RULER "
            "out as separate words. This project treats it as a name "
            "rather than an acronym. This app's context rot unit cites "
            "RULER's result that GPT-4 accuracy drops at longer context "
            "lengths."
        ),
        sources=(
            "arxiv.org/abs/2404.06654",
            "github.com/NVIDIA/RULER",
        ),
    ),
    Term(
        term="seal",
        expansion=None,
        definition=(
            "A seal, in this app, is a recorded commitment that locks in a "
            "prediction before the real outcome gets measured. Nobody can "
            "adjust that prediction later, after the fact. Each claim's hash "
            "chains to the previous claim's hash, and the seal commit's "
            "own commit hash gets read back afterward. This stops a user "
            "from quietly changing a prediction once they already know the "
            "answer. The sealing module computes this chain with the "
            "SHA-256 hash function."
        ),
    ),
    Term(
        term="SHA",
        expansion="Secure Hash Algorithm",
        definition=(
            "The Secure Hash Algorithm family is a set of one-way "
            "functions, standardized by NIST, that turn any input into a "
            "fixed-length digest. Changing even one character of the input "
            "produces a completely different digest, so a digest proves "
            "the input has not changed. This app's sealing module uses "
            "SHA-256 to chain each claim's hash to the one before it. A "
            "git commit SHA, a different use of the same word, identifies "
            "one specific commit in that seal chain."
        ),
        sources=("nvlpubs.nist.gov/nistpubs/fips/nist.fips.180-4.pdf",),
    ),
    Term(
        term="side letter",
        expansion=None,
        definition=(
            "A side letter is a separate agreement that sits beside the main "
            "contract and changes or clarifies it without rewriting it. In "
            "lending, a lender and a borrower use one to record a waiver, a "
            "reporting change or a fee. In principle it binds them the same "
            "way the credit agreement does, though courts have refused to "
            "enforce some side letters. A side letter is usually restricted, so "
            "only some people on a deal may read it. Both the permissions "
            "unit and the guardrails unit use a side letter as the document "
            "that must not leak."
        ),
        sources=(
            "en.wikipedia.org/wiki/Side_letter_(contract_law)",
            "www.lw.com/admin/Upload/Documents/Books%20of%20Jargon/Book-of-Jargon-European-Capital-Markets-and-Bank-Finance-2nd-Edition.pdf",
        ),
    ),
    Term(
        term="SR",
        expansion="Supervision and Regulation",
        definition=(
            "Supervision and Regulation letters, SR letters, are guidance "
            "documents the Federal Reserve issues to the banks it "
            "supervises. SR 11-7, issued in 2011 together with a matching "
            "OCC bulletin, is the foundational guidance on how a bank "
            "should manage the risk of using a model. This app's agent "
            "traceability unit cites SR 11-7 as the standard banks now use "
            "to judge their agentic AI systems. The numbers after SR mark "
            "the year and the sequence of that letter."
        ),
        sources=("www.federalreserve.gov/supervisionreg/srletters/srletters.htm",),
    ),
    Term(
        term="syndicate",
        expansion=None,
        definition=(
            "A syndicate is the group of lenders who together fund one loan, "
            "because a single lender does not want the whole exposure. As a "
            "verb, to syndicate means to sell parts of a loan to other banks "
            "and funds. Each member holds the same credit agreement, and an "
            "amendment needs a vote, which is one reason the documents "
            "multiply. This app's guardrails unit uses a question about what "
            "another lender in the syndicate agreed as an attempt to pull "
            "restricted material."
        ),
        sources=(
            "www.lw.com/admin/Upload/Documents/BoJ_US_Corporate_and_Bank_Finance-second-edition.pdf",
        ),
    ),
    Term(
        term="teardown",
        expansion=None,
        definition=(
            "A teardown, in this app, is the act of taking a working system "
            "apart to find out what it actually does. It is the opposite of a "
            "demo: nothing counts until a number comes out of a measurement "
            "you ran. This app never asks a reader to build Ledger, only to "
            "tear it down, unit by unit. The teardown cycle entry describes "
            "the loop that makes one teardown scoreable."
        ),
        sources=("app/units/types.py", "app/scoring.py"),
    ),
    Term(
        term="teardown cycle",
        expansion=None,
        definition=(
            "A teardown cycle, in this app, is the full loop of predicting "
            "an answer, sealing that prediction, and measuring the real "
            "result. The cycle then scores the prediction against that "
            "result. The cycle exists so a user commits to a guess before "
            "seeing the data that would make the guess easy. Scoring only "
            "makes sense when the prediction's seal came before the "
            "measurement ran."
        ),
    ),
    Term(
        term="token",
        expansion=None,
        definition=(
            "A token is the unit a language model reads and writes in, "
            "usually a word piece rather than a whole word or a single "
            "character. Providers charge by the token and report speed in "
            "tokens per second. The same text can produce different token "
            "counts across different models. This app's inference "
            "economics unit tracks token counts for both the prompt and "
            "the generated answer."
        ),
    ),
    Term(
        term="TPS",
        expansion="Tokens Per Second",
        definition=(
            "Tokens per second measures how fast a model generates text "
            "once it has already produced the first token. It describes "
            "the decode phase, after the slower, one-time prefill step has "
            "finished. A model can have a fast tokens per second rate and "
            "still feel slow to a user, if its time to first token is "
            "high. This app's latency tails unit cites tokens per second "
            "alongside time to first token as a pair of numbers that must "
            "be read together."
        ),
        sources=("docs.together.ai/learn/ttft-and-tps",),
    ),
    Term(
        term="TTFT",
        expansion="Time To First Token",
        definition=(
            "Time to first token is the delay between sending a request "
            "and receiving the first piece of a model's reply. It "
            "measures how responsive a system feels, since a user staring "
            "at a blank screen experiences this delay directly. A long "
            "prompt raises time to first token because the prefill step "
            "must finish before any output token can appear. This app's "
            "latency tails unit treats time to first token as a separate "
            "number from tokens per second, the speed after that first "
            "token arrives."
        ),
        sources=(
            "docs.together.ai/learn/ttft-and-tps",
            "clickhouse.com/resources/engineering/llm-inference-latency",
        ),
    ),
    Term(
        term="underwriter",
        expansion=None,
        definition=(
            "An underwriter is the person at a lender who decides whether a "
            "loan works and on what terms. The Office of the Comptroller of "
            "the Currency describes underwriting as the terms and conditions "
            "under which a bank extends credit, including covenants. The "
            "underwriter is Ledger's user: every question in this course "
            "comes from one, and every wrong answer costs one. Watch the word "
            "in securities markets, where an underwriter is an investment "
            "bank that buys an offering, a different job."
        ),
        sources=(
            "www.occ.gov/topics/supervision-and-examination/credit/commercial-credit/underwriting.html",
            "www.lw.com/admin/Upload/Documents/BoJ_US_Corporate_and_Bank_Finance-second-edition.pdf",
        ),
    ),
    Term(
        term="waiver",
        expansion=None,
        definition=(
            "A waiver is a lender's agreement not to enforce a breach that "
            "already happened. It differs from an amendment: an amendment "
            "changes the text going forward, while a waiver forgives one "
            "breach and can expire. So the documents can show a breach that a "
            "separate letter already forgave, and Ledger has to find both. "
            "This app's sampling unit ships a draw where one waiver hides a "
            "breach."
        ),
        sources=(
            "www.lw.com/admin/Upload/Documents/Books%20of%20Jargon/Book-of-Jargon-European-Capital-Markets-and-Bank-Finance-2nd-Edition.pdf",
        ),
    ),
)

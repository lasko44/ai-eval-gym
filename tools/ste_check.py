"""Measure this project's copy against ASD-STE100, as a goal and not a gate.

Run it:

    .venv/bin/python -m tools.ste_check

The rules are in docs/ste100/rules.md and the dictionary is in
docs/ste100/dictionary.json. Both come from Issue 9 of the specification.

The standard is a target here, not a pass or fail test. Full STE suits
maintenance instructions. This app explains technical content, and some of that
explanation needs a comparison or a longer clause to land. So the tool splits
its findings in two.

CLARITY findings are the rules that make an explanation easier to follow. A
long sentence, the passive voice, a contraction, or a semicolon costs the
reader something and buys nothing. Drive these to zero.

ADVISORY findings are the rules that would flatten the teaching. The dictionary
rejects ordinary words that carry meaning here, and rule 3.5 rejects an "-ing"
form that often reads better than the alternative. Read these, then decide. Do
not obey them without thought.

The tool has limits, and a reader should know them before trusting a number
it produces.

It cannot judge whether a word is a technical noun, which rule 1.6 permits.
It cannot count multi-word nouns for rule 2.1. Its passive voice test is a
regular expression, so it reads "coverage is resolved claims" as the passive
voice when the phrase is a copula and a noun. An earlier version also read a
flattened table of labels as one 62 word sentence, which measured the
extraction and not the copy.

A clean report is therefore not proof. A report with findings is proof of the
opposite, which is the useful direction.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DICTIONARY = json.loads((ROOT / "docs" / "ste100" / "dictionary.json").read_text())
APPROVED = {w.upper() for w in DICTIONARY["approved"]}
REPLACE = {w.lower() for w in DICTIONARY["unapproved"]}

# Rule 6.3 sets 25 words for descriptive text. Rule 5.1 sets 20 for procedures.
# Every string this tool reads is descriptive, so it uses 25.
MAX_WORDS = 25
MAX_SENTENCES = 6

# Rule 1.6 permits a word that is a technical noun. These are the technical
# nouns of this project, and a person added each one deliberately.
TECHNICAL_NOUNS = {
    "ai", "api", "arxiv", "benchmark", "bm25", "brier", "calibration", "chunk",
    "chunks", "claim", "claims", "context", "corpus", "cycle", "cycles",
    "dataset", "embedding", "embeddings", "entitlement", "entitlements",
    "eval", "evals", "fixture", "fixtures", "git", "guardrail", "guardrails",
    "harness", "hash", "hop", "json", "judge", "judges", "kappa", "llm",
    "metric", "metrics", "ndcg", "postgres", "precision", "probe", "probes",
    "prompt", "query", "queries", "rag", "recall", "reranker", "reranking",
    "retrieval", "router", "routing", "seal", "sha", "teardown", "threshold",
    "token", "tokens", "url",
}

CONTRACTION = re.compile(r"\b\w+'(t|re|ve|ll|d|m)\b", re.I)
POSSESSIVE = re.compile(r"\b\w+'s\b", re.I)
ING = re.compile(r"\b\w{3,}ing\b", re.I)
PASSIVE = re.compile(r"\b(is|are|was|were|be|been|being)\s+\w+(ed|en)\b", re.I)
WORD = re.compile(r"[A-Za-z][A-Za-z\-']*")


@dataclass
class Finding:
    rule: str
    where: str
    detail: str


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def check(text: str, where: str) -> list[Finding]:
    """Apply the rules a machine can apply to one block of copy."""
    found: list[Finding] = []

    if ";" in text:
        found.append(Finding("8.1", where, "semicolon"))

    for hit in CONTRACTION.finditer(text):
        found.append(Finding("4.2", where, f"contraction {hit.group(0)!r}"))

    for hit in POSSESSIVE.finditer(text):
        found.append(Finding("GR-8", where, f"possessive {hit.group(0)!r}"))

    for sentence in sentences(text):
        count = len(WORD.findall(sentence))
        if count > MAX_WORDS:
            found.append(Finding("6.3", where, f"{count} words: {sentence[:60]}..."))
        for hit in ING.finditer(sentence):
            word = hit.group(0).lower()
            if word not in TECHNICAL_NOUNS:
                found.append(Finding("3.5", where, f"-ing form {word!r}"))
        hit = PASSIVE.search(sentence)
        if hit:
            found.append(Finding("3.6", where, f"passive {hit.group(0)!r}"))

    if len(sentences(text)) > MAX_SENTENCES:
        found.append(Finding("6.6", where, f"{len(sentences(text))} sentences in one block"))

    for hit in WORD.finditer(text):
        word = hit.group(0).lower()
        if len(word) < 3 or word in TECHNICAL_NOUNS:
            continue
        if word in REPLACE and word.upper() not in APPROVED:
            found.append(Finding("1.1", where, f"not approved: {word!r}"))

    return found


def copy_blocks() -> list[tuple[str, str]]:
    """Every string a reader of this app sees."""
    import app.units as curriculum

    blocks: list[tuple[str, str]] = []
    for unit in curriculum.UNITS:
        blocks.append((f"{unit.slug}:title", unit.title))
        blocks.append((f"{unit.slug}:failure", unit.failure))
        blocks.append((f"{unit.slug}:detection", unit.detection))
        for i, paragraph in enumerate(unit.brief, 1):
            blocks.append((f"{unit.slug}:brief[{i}]", paragraph))
        for probe in unit.probes:
            blocks.append((f"{unit.slug}:{probe.id}:asks", probe.asks))
            blocks.append((f"{unit.slug}:{probe.id}:because", probe.because))
            for choice in probe.choices:
                blocks.append((f"{unit.slug}:{probe.id}:{choice.key}", choice.label))
        blocks.append((f"{unit.slug}:exercise:asks", unit.exercise.asks))
        blocks.append((f"{unit.slug}:exercise:note", unit.exercise.fixture_note))
        blocks.append((f"{unit.slug}:exercise:because", unit.exercise.because))

    # Read a template one prose element at a time. An earlier version of this
    # tool flattened the whole file into one string, which reported a table of
    # labels as a 62 word sentence and a code sample as a 51 word one. Those
    # findings measured the extraction, not the copy. This project is about
    # distrusting a number whose method is wrong, so the method is now narrow:
    # only the elements that hold sentences a reader reads.
    PROSE = re.compile(r"<(p|li|h2|h3|h4)\b[^>]*>(.*?)</\1>", re.S | re.I)
    for template in sorted((ROOT / "app" / "templates").glob("*.html")):
        raw = template.read_text()
        raw = re.sub(r"<style>.*?</style>", " ", raw, flags=re.S)
        raw = re.sub(r"<pre>.*?</pre>", " ", raw, flags=re.S)
        for n, match in enumerate(PROSE.finditer(raw), 1):
            text = match.group(2)
            if "<pre" in text or "<input" in text or "<textarea" in text:
                continue
            # Jinja output is a value, not prose. Count it as one word.
            text = re.sub(r"\{\{.*?\}\}", "value", text, flags=re.S)
            text = re.sub(r"\{%.*?%\}|\{#.*?#\}", " ", text, flags=re.S)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"&[a-z]+;", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            if len(WORD.findall(text)) >= 6:
                blocks.append((f"{template.name}:{n}", text))
    return blocks


def main() -> None:
    all_findings: list[Finding] = []
    for where, text in copy_blocks():
        all_findings += check(text, where)

    by_rule: dict[str, list[Finding]] = {}
    for finding in all_findings:
        by_rule.setdefault(finding.rule, []).append(finding)

    clarity = {"6.3", "6.6", "3.6", "4.2", "8.1"}
    titles = {
        "1.1": "Use approved words, technical nouns, or technical verbs",
        "3.5": "Use an -ing form only in a technical noun",
        "3.6": "Use the active voice",
        "4.2": "Do not use contractions",
        "6.3": "Use a maximum of 25 words in a sentence",
        "6.6": "Use a maximum of six sentences in a paragraph",
        "8.1": "Do not use the semicolon",
        "GR-8": "Prefer a phrase with \"of\" over the possessive form",
    }
    blocks = len(copy_blocks())
    n_clarity = sum(len(v) for k, v in by_rule.items() if k in clarity)
    n_advisory = len(all_findings) - n_clarity

    print(f"{blocks} blocks of copy\n")
    print(f"CLARITY   {n_clarity:>5}   drive to zero")
    for rule in sorted(by_rule, key=lambda r: -len(by_rule[r])):
        if rule in clarity:
            print(f"  rule {rule:<4} {len(by_rule[rule]):>5}  {titles.get(rule, '')}")
    print(f"\nADVISORY  {n_advisory:>5}   read, then decide")
    for rule in sorted(by_rule, key=lambda r: -len(by_rule[r])):
        if rule not in clarity:
            print(f"  rule {rule:<4} {len(by_rule[rule]):>5}  {titles.get(rule, '')}")

    worst = sorted(
        (f for f in all_findings if f.rule == "6.3"),
        key=lambda f: -int(f.detail.split()[0]),
    )[:8]
    if worst:
        print("\nLongest sentences:")
        for hit in worst:
            print(f"  {hit.detail.split()[0]:>3} words  {hit.where}")


if __name__ == "__main__":
    main()

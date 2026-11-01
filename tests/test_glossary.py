"""The glossary page, and the rule it exists to enforce.

The house rule is that a reader never meets an acronym without its full name.
A glossary alone does not deliver that: a reader who hits "BEIR" in unit 02
will not stop and open another page. So these tests check both halves. The
page has to render every term, and the unit copy has to give the full name at
the first use, inside the unit itself.

The acronym check is the same function the clarity tool runs, applied to the
same strings the unit template renders, in the order the template renders
them. That is the real path: if this passes and the page still shows a bare
acronym, the check is reading the wrong text and should be fixed here first.
"""

import re

import pytest

import app.units as curriculum
from app.glossary import TERMS
from tools.ste_check import ACRONYM, ACRONYM_SKIP, unexpanded_acronyms

ALL_UNITS = list(curriculum.UNITS)
UNIT_IDS = [unit.slug for unit in ALL_UNITS]


def reader_order(unit):
    """Every string of a unit page, in the order the template prints it.

    app/templates/unit.html prints the title, the failure line, the briefing,
    the probes, the exercise, and the sources last. "First use" means first in
    this order, so this helper is what makes the rule match the page.
    """
    # app/templates/unit.html prints builds_on between the failure line
    # and the briefing, so it is part of reading order.
    parts = [unit.title, unit.failure, unit.detection,
             unit.builds_on, *unit.brief]
    for probe in unit.probes:
        parts += [probe.asks, probe.because, *(c.label for c in probe.choices)]
    parts += [unit.exercise.asks, unit.exercise.fixture_note, unit.exercise.because]
    parts += list(unit.sources)
    return "\n".join(parts)


@pytest.mark.parametrize("unit", ALL_UNITS, ids=UNIT_IDS)
def test_every_acronym_in_a_unit_carries_its_full_name(unit):
    findings = unexpanded_acronyms(reader_order(unit), unit.slug)
    assert not findings, (
        f"{unit.slug} uses an acronym before anybody said what it stands for: "
        + ", ".join(f.detail for f in findings)
        + ". Write it as 'Full Name (ACR)' or 'ACR (Full Name)' at the first "
        "use, taking the wording from app/glossary.py."
    )


def test_the_glossary_has_terms():
    assert TERMS, "app/glossary.py defines no terms."


def test_no_two_terms_share_a_name():
    names = [term.term for term in TERMS]
    assert len(names) == len(set(names)), f"Duplicate term in {names}"


@pytest.mark.parametrize("term", TERMS, ids=[t.term for t in TERMS])
def test_a_term_either_expands_or_says_why_not(term):
    """An entry never leaves a reader guessing, and never guesses for them.

    RULER and EY are real cases: the sources do not spell either one out. The
    honest entry carries expansion=None and explains that in its definition,
    which is why this asserts on the definition rather than letting an empty
    expansion pass silently.

    A plain term such as "chunk" or "p99" has nothing to expand, so the
    assertion applies only to a term shaped like an acronym.
    """
    assert term.definition.strip(), f"{term.term} has no definition."
    if term.expansion is not None:
        assert term.expansion.strip(), f"{term.term} has a blank expansion."
    elif ACRONYM.fullmatch(term.term):
        assert "name" in term.definition.lower(), (
            f"{term.term} has no expansion, so its definition has to tell the "
            "reader it is a name rather than leave the gap unexplained."
        )


@pytest.mark.parametrize("term", TERMS, ids=[t.term for t in TERMS])
def test_an_expansion_does_not_hide_another_acronym(term):
    """A full name written with an acronym inside it fails its own rule.

    BEIR shipped as "Benchmarking IR (Information Retrieval)" first, which
    hands a reader a second acronym while answering the first.
    """
    if term.expansion is None:
        return
    known = {t.term for t in TERMS if t.expansion is None}
    bare = [
        m.group(0)
        for m in ACRONYM.finditer(term.expansion)
        if m.group(0) not in ACRONYM_SKIP and m.group(0) not in known
    ]
    assert not bare, (
        f"The full name of {term.term} still contains {bare}. Spell it out, or "
        "give the inner acronym its own entry with expansion=None."
    )


def test_the_glossary_page_renders_every_term(client):
    response = client.get("/glossary")
    assert response.status_code == 200, response.text
    body = response.text
    for term in TERMS:
        assert term.term in body, f"{term.term} is missing from /glossary."
        if term.expansion:
            assert term.expansion in body, (
                f"The full name of {term.term} is missing from /glossary."
            )


def test_the_glossary_page_is_reachable_from_every_page(client):
    """A glossary nobody can find does not answer anybody's question."""
    for path in ("/", "/units", "/glossary"):
        body = client.get(path).text
        assert re.search(r'href="/glossary"', body), (
            f"{path} has no link to the glossary."
        )

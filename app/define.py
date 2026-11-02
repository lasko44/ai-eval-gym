"""Define a term the first time a reader meets it, without anybody marking it.

The glossary rule in this project used to be about acronyms: never let a
reader meet "BEIR" without its full name. That rule was enforced and it was
the wrong rule, because it only caught the words that look difficult.

The first line of unit 01 reads "The judge grading Ledger covenant answers
flips when you swap the order". Not one of those words is an acronym. A
reader who does not know what a covenant is, or what a judge means here, is
lost at the title, and the acronym check was green the whole time.

So this marks the first use of any glossary term in a unit, in reading order,
wherever it appears. Hovering or tabbing to it gives the definition, and the
word links into the glossary for the longer version. No unit has to mark its
own terms, which means adding a term to the glossary defines it everywhere at
once and a unit written next year gets the same treatment.

Only the first use is marked. A page where every instance of "judge" is
underlined is a page nobody can read, and the second time is not when
somebody needs telling.
"""

import html
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Marked:
    """One block of copy with its first-use definitions already in it."""

    html: str


def _pattern(term: str) -> re.Pattern:
    """Match a term on a word boundary, case insensitively, plus a plural.

    Case insensitive because a term is capitalised at the start of a sentence
    and lowercase inside one, and both are the same word to a reader.
    """
    body = re.escape(term)
    return re.compile(rf"\b({body}(?:s|es)?)\b", re.IGNORECASE)


def mark(blocks: list[str], terms, already: set[str] | None = None) -> list[str]:
    """Return the blocks as HTML, with each term defined at its first use.

    `blocks` is the copy in reading order. `terms` is the glossary. `already`
    lets a caller carry state between calls, so a term defined on step 1 of a
    lesson is not defined again on step 4.

    Each block is held as alternating plain and already-marked pieces, and a
    search only ever looks at the plain ones. An earlier version replaced
    straight into the string and then kept scanning it, so a short term
    matched inside the anchor a longer one had just written and corrupted the
    attribute: "calibration" landed inside the href of "calibration within
    groups". Splitting instead of rescanning makes that unrepresentable.

    Everything is escaped on the way in. The only markup here is its own, so
    a stray angle bracket in a briefing cannot become a tag.
    """
    seen = already if already is not None else set()
    # Longest first, so "credit agreement" wins over "agreement" and the
    # shorter term cannot eat the longer one's first use.
    ordered = sorted(terms, key=lambda t: len(t.term), reverse=True)

    out = []
    for block in blocks:
        # (text, is_markup). Only text pieces are ever searched.
        pieces: list[tuple[str, bool]] = [(html.escape(block), False)]

        for term in ordered:
            key = term.term.lower()
            if key in seen:
                continue
            pattern = _pattern(term.term)
            for index, (piece, is_markup) in enumerate(pieces):
                if is_markup:
                    continue
                match = pattern.search(piece)
                if not match:
                    continue
                tip = html.escape(_short(term), quote=True)
                anchor = (
                    f'<a class="tip defined" href="/glossary#{_anchor(term.term)}" '
                    f'tabindex="0" data-tip="{tip}">{match.group(1)}</a>'
                )
                pieces[index:index + 1] = [
                    (piece[:match.start()], False),
                    (anchor, True),
                    (piece[match.end():], False),
                ]
                seen.add(key)
                break

        out.append("".join(piece for piece, _ in pieces))
    return out


def _short(term) -> str:
    """One sentence for a tooltip, from a definition written as several.

    The glossary entry is two to four sentences, which is right on the
    glossary page and too long hovering over a word. The expansion comes
    first when there is one, because for an acronym that is the whole answer.
    """
    first = term.definition.strip().split(". ")[0].rstrip(".") + "."
    if term.expansion:
        return f"{term.expansion}. {first}"
    return first


def _anchor(term: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", term.lower()).strip("-")


def short_for(term_name: str) -> str:
    """The one-sentence form of a glossary term, by name.

    For the few places a template names a term directly rather than having it
    found in prose.
    """
    from app.glossary import TERMS

    for term in TERMS:
        if term.term.lower() == term_name.lower():
            return _short(term)
    return ""

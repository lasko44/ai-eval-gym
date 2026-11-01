"""Colour contrast, computed rather than asserted.

A test that checks the palette still holds the hex values somebody chose
proves only that nobody edited the file. It passes happily while muted grey
sits on a card at 2.9 to 1 and a reader cannot read it.

So this parses the stylesheet's custom properties, computes the real WCAG
relative-luminance ratio for every pair the pages actually paint, and holds
each one to the threshold for the role it plays. If a colour changes, the
number here changes with it, which is the whole point.

Thresholds, from WCAG 2.1:
  4.5:1  normal body text
  3.0:1  large text (at or above 18.66px bold, or 24px) and UI boundaries
"""

import re
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent / "app" / "templates" / "base.html"

BODY_TEXT = 4.5
LARGE_TEXT = 3.0


def _variables() -> dict[str, str]:
    """Custom properties declared on :root in the one stylesheet."""
    css = BASE.read_text()
    root = re.search(r":root\s*\{(.*?)\}", css, re.S)
    assert root, "No :root block in base.html, so there is no palette to check."
    return {
        name: value.strip()
        for name, value in re.findall(r"--([a-z-]+)\s*:\s*([^;]+);", root.group(1))
        if value.strip().startswith("#")
    }


def _rgb(value: str) -> tuple[float, float, float]:
    text = value.lstrip("#")
    if len(text) == 3:
        text = "".join(c * 2 for c in text)
    return tuple(int(text[i : i + 2], 16) / 255 for i in (0, 2, 4))


def _luminance(value: str) -> float:
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in _rgb(value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(foreground: str, background: str) -> float:
    a, b = _luminance(foreground), _luminance(background)
    light, dark = max(a, b), min(a, b)
    return (light + 0.05) / (dark + 0.05)


# Every pair the templates actually paint, named by where it appears. The
# background is the EFFECTIVE painted surface, not the page default: muted
# text inside a card sits on --surface, and checking it against --bg would
# measure a combination that never reaches a screen.
PAIRS = [
    ("ink", "bg", BODY_TEXT, "body text on the page"),
    ("ink", "surface", BODY_TEXT, "body text inside a card"),
    ("muted", "bg", BODY_TEXT, "notes on the page"),
    ("muted", "surface", BODY_TEXT, "notes inside a card"),
    ("accent", "surface", BODY_TEXT, "links inside a card"),
    ("accent", "bg", BODY_TEXT, "links on the page"),
    ("good", "surface", BODY_TEXT, "an earned badge marker"),
    ("warn", "surface", BODY_TEXT, "the overconfidence cell in the calibration table"),
    ("ink", "accent-soft", BODY_TEXT, "text on a highlighted row"),
    # State markers, so WCAG 1.4.11 applies at 3:1. --line-strong is not in
    # this list on purpose: it draws table rules and card edges, which are
    # decorative boundaries and exempt. The moment it is used to report a
    # state it belongs here, and it measures 1.48:1, so it will fail.
    ("muted", "surface", LARGE_TEXT, "the marker on an unearned badge"),
    ("good", "surface", LARGE_TEXT, "the marker on an earned badge"),
]


@pytest.mark.parametrize(
    "fg,bg,floor,where", PAIRS, ids=[p[3].replace(" ", "-") for p in PAIRS]
)
def test_every_painted_pair_clears_its_threshold(fg, bg, floor, where):
    palette = _variables()
    assert fg in palette, f"--{fg} is gone from the palette but still used for {where}."
    assert bg in palette, f"--{bg} is gone from the palette but still used for {where}."

    measured = ratio(palette[fg], palette[bg])
    assert measured >= floor, (
        f"{where}: --{fg} ({palette[fg]}) on --{bg} ({palette[bg]}) measures "
        f"{measured:.2f} to 1, under the {floor} to 1 floor. Darken the "
        "foreground rather than widening the threshold."
    )


def test_the_contrast_maths_is_right():
    """Pin the formula against the two ratios everybody knows.

    Without this, a bug in the luminance curve would quietly pass every pair
    above and the suite would be reassuring rather than useful.
    """
    assert ratio("#000000", "#ffffff") == pytest.approx(21.0, rel=1e-6)
    assert ratio("#ffffff", "#ffffff") == pytest.approx(1.0, rel=1e-9)
    # A mid grey that is a known near-miss for body text on white.
    assert ratio("#767676", "#ffffff") == pytest.approx(4.54, abs=0.02)


def test_meaning_is_never_carried_by_colour_alone():
    """An earned badge has to be distinguishable without seeing hue.

    The badge list uses a check character for earned and a dot for not, so
    the state survives greyscale and a screen reader. This pins that the
    characters are still there, because the colour rule beside them would
    otherwise be the only signal.
    """
    css = BASE.read_text()
    on = re.search(r"\.badge-on::before\s*\{([^}]*)\}", css)
    off = re.search(r"\.badge-off::before\s*\{([^}]*)\}", css)
    assert on and off, "The badge markers are gone, so state is colour alone."
    assert "content:" in on.group(1) and "content:" in off.group(1)
    assert on.group(1) != off.group(1), (
        "Earned and unearned badges render the same character, so the only "
        "difference left is colour."
    )


# The pill variants set colour with literal hex rather than custom properties,
# because each is a foreground and background chosen as a pair. They are not
# in PAIRS above, which only reads :root, so they are checked here by name.
PILL_PAIRS = [
    ("#16452f", "#dfe9e0", "a finished pill"),
    ("#8a2a10", "#f6e3dc", "a confident-miss pill in review"),
]


@pytest.mark.parametrize(
    "fg,bg,where", PILL_PAIRS, ids=[p[2].replace(" ", "-") for p in PILL_PAIRS]
)
def test_every_pill_clears_body_text_contrast(fg, bg, where):
    css = BASE.read_text()
    assert fg in css and bg in css, (
        f"{where} no longer uses {fg} on {bg}; update this test to the new pair "
        "rather than deleting it."
    )
    measured = ratio(fg, bg)
    assert measured >= BODY_TEXT, (
        f"{where}: {fg} on {bg} measures {measured:.2f} to 1, under "
        f"{BODY_TEXT} to 1."
    )

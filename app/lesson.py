"""A unit, broken into the steps you actually take through it.

A unit page used to print everything at once: four hundred words of briefing,
then three questions, then an exercise. That is an article with a quiz after
it. A reader meets the whole thing before doing any of it, decides where to
start, and usually starts by scrolling.

A lesson is different. One thing is in front of you, there is exactly one next
action, and the work sits beside the instruction rather than three screens
below it. So this module cuts a unit into steps and the page shows one at a
time, with `?step=`. There is no JavaScript: a step is a number the server
reads, the same way the tour works, which also means a step is a link somebody
can bookmark or send.

`?all=1` still prints the whole unit on one page. That view is worth keeping
and is worth not being the default: it is a reference for a unit you have
already worked, and a wall for one you have not.
"""

from dataclasses import dataclass, field
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class LessonStep:
    """One screen. Exactly one thing to do on it."""

    index: int
    kind: str            # read, probe, detect, close
    label: str           # three or four words, for the step rail
    heading: str
    paragraphs: tuple[str, ...] = field(default_factory=tuple)
    probe_id: str | None = None


def steps(unit) -> tuple[LessonStep, ...]:
    """The steps for one unit, in the order a reader takes them.

    The briefing splits in two rather than running as one screen of prose.
    The cut falls after the paragraphs that set up the failure, so the first
    screen asks "what breaks" and the second answers "how do we know". Units
    carry between three and nine paragraphs, so the split is proportional
    rather than a fixed index.
    """
    made: list[LessonStep] = []
    cut = max(1, round(len(unit.brief) * 0.45))

    made.append(LessonStep(
        index=1, kind="read", label="What breaks",
        heading="What goes wrong",
        paragraphs=tuple(unit.brief[:cut]),
    ))
    made.append(LessonStep(
        index=2, kind="read", label="The evidence",
        heading="How we know",
        paragraphs=tuple(unit.brief[cut:]),
    ))

    for offset, probe in enumerate(unit.probes, start=1):
        made.append(LessonStep(
            index=len(made) + 1, kind="probe",
            label=f"Predict {offset}",
            heading=f"Prediction {offset} of {len(unit.probes)}",
            probe_id=probe.id,
        ))

    made.append(LessonStep(
        index=len(made) + 1, kind="detect", label="Measure it",
        heading="Measure it yourself",
    ))
    made.append(LessonStep(
        index=len(made) + 1, kind="close", label="Take away",
        heading="What you took away",
    ))
    return tuple(made)


def step_at(unit, number: int | str | None) -> LessonStep:
    """The step a ?step= value names, defaulting to the first.

    An out of range or unparseable value lands on step one rather than
    raising. A step is a number in a link, and a stale bookmark should open
    the lesson rather than break it.
    """
    all_steps = steps(unit)
    try:
        wanted = int(number)
    except (TypeError, ValueError):
        return all_steps[0]
    if 1 <= wanted <= len(all_steps):
        return all_steps[wanted - 1]
    return all_steps[0]


def fixture_peek(fixture_path: str, lines: int = 14) -> str | None:
    """The opening of a fixture, pretty printed, for a reader who is stuck.

    The exercise describes the fixture in words, and a shape is faster to
    read than a description of a shape. This shows the real file rather than
    an example of one, so it cannot drift, and it is generated rather than
    authored so adding a unit does not mean writing one of these too.

    Returns None when the file will not parse, because a hint that throws is
    worse than no hint.
    """
    path = REPO_ROOT / fixture_path
    try:
        with path.open() as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None

    # Show the shape, not the volume. A fixture is often thousands of rows,
    # and the reader needs the first one.
    if isinstance(data, list):
        sample = data[:2]
    elif isinstance(data, dict):
        sample = {}
        for key, value in data.items():
            if isinstance(value, list):
                sample[key] = value[:2] + (["..."] if len(value) > 2 else [])
            elif isinstance(value, dict):
                first = list(value.items())[:1]
                sample[key] = dict(first) | ({"...": "..."} if len(value) > 1 else {})
            else:
                sample[key] = value
    else:
        return None

    text = json.dumps(sample, indent=1)
    rows = text.splitlines()
    if len(rows) > lines:
        rows = rows[:lines] + ["..."]
    return "\n".join(rows)

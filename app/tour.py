"""The way in: an introduction, a guided tour, and the tooltips.

Three different jobs, kept apart because they answer different questions.

`TIPS` answers "what is this control". One sentence, shown on hover and on
keyboard focus, attached to a label in the interface. It never explains a
concept from the course, because the glossary already does that and a term
with two homes drifts.

`STEPS` answers "where do I start". The tour runs over the real pages rather
than a simulation of them: each step names a route and a panel of prose, and
walking it means walking the app. Nothing here is a screenshot, so the tour
cannot go stale while the interface moves underneath it.

The introduction at /start answers "what is this for", and lives in
app/templates/start.html because it is a page rather than data.

There is no JavaScript in any of it. The tour is a query parameter the server
reads, and the tooltips are a CSS rule, so both survive with scripting off and
neither needs a build step.
"""

from dataclasses import dataclass


# One sentence each, in the interface's own vocabulary. If a tip needs two
# sentences, the control is doing two things and the control is the problem.
TIPS: dict[str, str] = {
    "rank": (
        "How far through the course you can actually work. It rises only when "
        "you finish a whole part, and it says nothing about whether you were "
        "right."
    ),
    # Named for the score rather than the concept. The glossary owns
    # calibration itself; this owns the number on the scoreboard.
    "calibration_score": (
        "The 0 to 100 reading of whether your stated confidence carried "
        "information. Only your first answer to each prediction counts."
    ),
    "streak": (
        "Predictions you got right in a row, counting back from the most "
        "recent one."
    ),
    "predictions": (
        "Questions you answer with a confidence before any answer is shown. "
        "Being wrong is fine; being confidently wrong is what costs you."
    ),
    "detection": (
        "The measurement you write yourself against a fixture in this "
        "repository. The app checks your number and never runs your code."
    ),
    "mastered": (
        "Every prediction committed and a detection that matched. Mastery does "
        "not require being right."
    ),
    "locked": (
        "A part opens once you finish the one before it, which is what makes "
        "the course order mean something. You can always read it anyway."
    ),
    "builds_on": (
        "What this needs from what came before it. A unit that cannot name "
        "that is in the wrong place."
    ),
    "tolerance": (
        "How far your posted number may sit from the known answer. It allows "
        "for floating point, not for sloppiness."
    ),
    "shortfall": (
        "The stretch between the confidence you claimed and the accuracy you "
        "delivered. Hatching means you were surer than you turned out to be."
    ),
    "cycle": (
        "The real thing: four steps against a system nobody graded for you. "
        "Predict, seal the prediction in git, measure, then score."
    ),
}



# What each thing in the navigation is. Seven words across the top with no
# explanation is seven guesses.
NAV_TIPS: dict[str, str] = {
    "Start": (
        "What this is for and how a lesson works. Read this first if you have "
        "not before."
    ),
    "Path": (
        "The job this course is built from, the skills those postings name, "
        "and how far you are from each one."
    ),
    "Lessons": (
        "Every lesson in the order you take them, grouped into the six parts."
    ),
    "Progress": (
        "Your rank and your calibration, and the readout showing where your "
        "confidence was off."
    ),
    "Review": (
        "Every prediction you got wrong the first time, free to try again "
        "without moving your score."
    ),
    "Cycles": (
        "The real thing: a teardown of a system nobody prepared for you, with "
        "no answer key waiting."
    ),
    "Glossary": (
        "Every term this course uses, with its full name and what it means."
    ),
}


@dataclass(frozen=True)
class Step:
    """One stop on the tour, pinned to a real route."""

    slug: str
    route: str
    title: str
    body: tuple[str, ...]


STEPS: tuple[Step, ...] = (
    Step(
        slug="subject",
        route="/",
        title="This page is the job, and your distance from it",
        body=(
            "Three real postings, and the skills they ask for. A skill goes "
            "green when every lesson that teaches it is finished. Some have "
            "no lesson yet and say so, because a map that hides its gaps is "
            "not a map.",
            "A course that used a different example per lesson would teach you "
            "a bag of tricks. One system means each unit measures a different "
            "part of the same thing, in the order you would really have to "
            "measure them.",
        ),
    ),
    Step(
        slug="scoreboard",
        route="/progress",
        title="Two scores, and they never add together",
        body=(
            "Rank counts whole parts finished. Calibration says whether your "
            "confidence meant anything. They are reported apart on purpose, "
            "because doing the work and knowing the thing are different.",
            "That means your calibration can be poor while your rank is high. "
            "Seeing that is the point. One blended number would let you buy "
            "either with the other.",
        ),
    ),
    Step(
        slug="confidence",
        route="/progress",
        title="The one number to act on",
        body=(
            "Once you have answered a few questions, the readout under the "
            "scores plots what you claimed against what you delivered.",
            "A bar that stops short of its rule, with hatching in the gap, "
            "means you were surer than you turned out to be. That gap is the "
            "single most useful thing this app can tell you, and it is also "
            "the hardest to notice on your own.",
        ),
    ),
    Step(
        slug="order",
        route="/units",
        title="The order is the course",
        body=(
            "Six parts, and every part and every unit says what it needs from "
            "the one before it. Look for the line that starts Builds on.",
            "A part stays locked until you finish the one before it, so the "
            "claim is enforced rather than decorative. If you want to read "
            "ahead anyway, every locked unit offers you the way through.",
        ),
    ),
    Step(
        slug="unit",
        route="/units/judges?anyway=1",
        title="A unit is four steps, always in this order",
        body=(
            "Read what goes wrong, with the measured numbers and where they "
            "came from. Then commit predictions, before any answer appears. "
            "Then write the detection yourself. Then review.",
            "The order is the whole point. A prediction made after you have "
            "seen the answer teaches you nothing, which is why this app will "
            "not let you reach one first.",
        ),
    ),
    Step(
        slug="predict",
        route="/units/judges?anyway=1",
        title="Commit a prediction, then live with it",
        body=(
            "Pick an option and say how sure you are. Your first answer is the "
            "only one that counts, so answer before you scroll.",
            "You cannot claim less confidence than guessing would give you. "
            "Having picked one of four options, you already assert 25 percent, "
            "and understating everything would quietly buy you a better score.",
        ),
    ),
    Step(
        slug="detect",
        route="/units/judges?anyway=1",
        title="Then you write the measurement",
        body=(
            "Each unit ships a fixture: real-shaped data with a known answer "
            "nobody has shown you. You write the code that measures it, in "
            "your own editor, and post the number.",
            "The app never runs your code. It checks your number against the "
            "fixture's known result, the same way a harness posts a result "
            "during a real teardown.",
        ),
    ),
    Step(
        slug="review",
        route="/review",
        title="What you got wrong comes back",
        body=(
            "Every prediction you missed the first time, ordered by how sure "
            "you were rather than by when it happened.",
            "Answering again here cannot move your calibration, which reads "
            "first attempts only. If revisiting a miss cost you something, you "
            "would stop revisiting misses.",
        ),
    ),
    Step(
        slug="cycle",
        route="/cycles",
        title="The course is practice. This is the real thing",
        body=(
            "A cycle runs against a system nobody prepared for you, with no "
            "known answer waiting. You write falsifiable claims, seal them "
            "into git before you measure, then score yourself against what you "
            "actually found.",
            "That is why the course exists: so that when you reach a real "
            "system, your prediction is worth sealing.",
        ),
    ),
)

BY_INDEX = {index: step for index, step in enumerate(STEPS, start=1)}


def number(value: int | str | None) -> int | None:
    """The step number a ?tour= value names, or None when it names none.

    A bad value returns None rather than raising. The tour is a query
    parameter anybody can type, and a mistyped one should drop the panel
    rather than break the page it was meant to explain.
    """
    try:
        found = int(value)
    except (TypeError, ValueError):
        return None
    return found if found in BY_INDEX else None


def step(number: int | str | None) -> Step | None:
    """The step for a ?tour= value, or None when there is no such step.

    A bad value returns None rather than raising. The tour is a query
    parameter anybody can type, and a mistyped one should drop the panel
    rather than break the page it was meant to explain.
    """
    try:
        return BY_INDEX.get(int(number))
    except (TypeError, ValueError):
        return None


def next_link(number: int) -> str | None:
    """The route and parameter for the step after this one."""
    following = BY_INDEX.get(number + 1)
    if following is None:
        return None
    joiner = "&" if "?" in following.route else "?"
    return f"{following.route}{joiner}tour={number + 1}"


def previous_link(number: int) -> str | None:
    earlier = BY_INDEX.get(number - 1)
    if earlier is None:
        return None
    joiner = "&" if "?" in earlier.route else "?"
    return f"{earlier.route}{joiner}tour={number - 1}"

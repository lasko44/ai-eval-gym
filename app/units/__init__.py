"""The curriculum.

One module per unit, each a failure mode that shows up in real production
systems paired with the measurement that catches it. Shapes live in `types.py`
and a worked example lives in `judges.py`.

Units are discovered rather than listed: any module in this package that defines
a module-level `UNIT` is picked up, and they are ordered by `UNIT.number`. That
means adding a unit is adding one file, with nothing else to edit and nothing to
keep in sync.

The course order lives in `parts.py`. A unit names its part by slug, and
`COURSE` groups the units under their parts in the order a reader takes them.
Nothing here checks that grouping: tests/test_course_order.py does, because a
course whose order drifts is worse than a flat list that never claimed one.

Every number in a briefing traces to a source listed on that unit, verified
against the primary source rather than recalled. Units are authored content, so
they ship as code. What the user produces (probe answers, exercise results) is
stored in the database, because that is his record and not ours.
"""

import importlib
import pkgutil

from app.units.parts import PARTS
from app.units.system import SYSTEM, SystemUnderEvaluation
from app.units.types import Choice, Exercise, Part, Probe, Unit

__all__ = [
    "Choice",
    "Exercise",
    "Part",
    "Probe",
    "Unit",
    "SYSTEM",
    "SystemUnderEvaluation",
    "UNITS",
    "PARTS",
    "COURSE",
    "BY_SLUG",
    "get",
    "part_of",
]

# Modules in this package that hold shapes or the course order rather than a
# unit. Listing them here is cheaper than a unit module accidentally shipping
# because it happened to define a name called UNIT.
NOT_UNITS = {"types", "parts", "system"}


def _discover() -> tuple[Unit, ...]:
    found = []
    for module in pkgutil.iter_modules(__path__):
        if module.name in NOT_UNITS:
            continue
        loaded = importlib.import_module(f"{__name__}.{module.name}")
        unit = getattr(loaded, "UNIT", None)
        if isinstance(unit, Unit):
            found.append(unit)
    return tuple(sorted(found, key=lambda u: u.number))


UNITS: tuple[Unit, ...] = _discover()

BY_SLUG = {unit.slug: unit for unit in UNITS}

# The course: every part in order, each with its units in order. A part with no
# units is still listed, so an empty part is visible rather than silent.
COURSE: tuple[tuple[Part, tuple[Unit, ...]], ...] = tuple(
    (part, tuple(unit for unit in UNITS if unit.part == part.slug)) for part in PARTS
)


def get(slug: str) -> Unit | None:
    return BY_SLUG.get(slug)


def part_of(unit: Unit) -> Part | None:
    """The part a unit belongs to, or None if it names one that does not exist."""
    for part, units in COURSE:
        if unit in units:
            return part
    return None

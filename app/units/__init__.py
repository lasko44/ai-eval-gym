"""The curriculum.

One module per unit, each a failure mode that shows up in real production
systems paired with the measurement that catches it. Shapes live in `types.py`
and a worked example lives in `judges.py`.

Units are discovered rather than listed: any module in this package that defines
a module-level `UNIT` is picked up, and they are ordered by `UNIT.number`. That
means adding a unit is adding one file, with nothing else to edit and nothing to
keep in sync.

Every number in a briefing traces to a source listed on that unit, verified
against the primary source rather than recalled. Units are authored content, so
they ship as code. What the user produces (probe answers, exercise results) is
stored in the database, because that is his record and not ours.
"""

import importlib
import pkgutil

from app.units.types import Choice, Exercise, Probe, Unit

__all__ = ["Choice", "Exercise", "Probe", "Unit", "UNITS", "BY_SLUG", "get"]


def _discover() -> tuple[Unit, ...]:
    found = []
    for module in pkgutil.iter_modules(__path__):
        if module.name == "types":
            continue
        loaded = importlib.import_module(f"{__name__}.{module.name}")
        unit = getattr(loaded, "UNIT", None)
        if isinstance(unit, Unit):
            found.append(unit)
    return tuple(sorted(found, key=lambda u: u.number))


UNITS: tuple[Unit, ...] = _discover()

BY_SLUG = {unit.slug: unit for unit in UNITS}


def get(slug: str) -> Unit | None:
    return BY_SLUG.get(slug)

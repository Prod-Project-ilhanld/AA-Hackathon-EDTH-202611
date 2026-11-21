"""Which hostiles are worth trying, and in what order. Starter file: planner.py calls it, OFF by default.

Ideas to build here (see docs/ROADMAP.md, "Where the points are"):
- skip hostiles no plan can ever engage (R7: within `collateral_radius_m` of a friendly/civilian) — done below;
- light effectors are the scarce resource at L4 (need 49-86, have 50), heavies are not (need 10-25, have 35):
  give contacts that need many lights a lower priority, e.g. a 2-D knapsack over the light/heavy counts.

Turn on with ENABLED = True (or PLANNER_TARGETS=1) and compare with tools/bench.py on many seeds.
Python 3.9, standard library only; kit code from `fk`, never `fleetkit`.
"""
import math

import params
from fk.model import CIVILIAN, FRIENDLY

ENABLED = params.TARGETS


def skip(scenario, contact) -> bool:
    """True if `contact` (a hostile) can never be engaged (R7). Called first in FastPlanner.serve_hostile."""
    if not ENABLED:
        return False
    r = scenario.rules.collateral_radius_m
    return any(f.cls in (FRIENDLY, CIVILIAN) and math.hypot(f.pos[0] - contact.pos[0], f.pos[1] - contact.pos[1]) < r
               for f in scenario.contacts)


def weight(scenario, contact) -> float:
    """Multiplies the contact's priority in the order search (`_key`). 1.0 = unchanged.

    TODO: light/heavy pricing (lights scarce at L4).
    """
    return 1.0

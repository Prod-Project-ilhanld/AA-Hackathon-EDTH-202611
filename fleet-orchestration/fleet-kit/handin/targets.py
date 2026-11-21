"""Which hostiles are worth trying, and in what order. planner.py calls it.

Ideas to build here (see docs/ROADMAP.md, "Where the points are"):
- skip hostiles no plan can ever engage (R7: within `collateral_radius_m` of a friendly/civilian) — done below;
- light effectors are the scarce resource at L4 (need 49-86, have 50), heavies are not (need 10-25, have 35):
  give contacts that need many lights a lower priority, e.g. a 2-D knapsack over the light/heavy counts.

The R7 skip is ON by default (PLANNER_TARGETS=0 turns it off). Measured on L4, 50 seeds, same conditions: +1.27 %
(25 seeds better, 25 equal, 0 worse, 0 invalid); L3, 20 seeds: +0.51 % (10 better, 0 worse); L1 and L2 unchanged.
It cannot cost a point: a skipped hostile is one that every plan fails on R7, and the saved tries buy more restarts.
Python 3.9, standard library only; kit code from `fk`, never `fleetkit`.
"""
import os

from fk.geometry import EPS, hdist
from fk.model import CIVILIAN, FRIENDLY

ENABLED = os.environ.get("PLANNER_TARGETS", "1") != "0"


def skip(scenario, contact) -> bool:
    """True if `contact` (a hostile) can never be engaged (R7). Called first in FastPlanner.serve_hostile."""
    if not ENABLED:
        return False
    r = scenario.rules.collateral_radius_m
    return any(f.cls in (FRIENDLY, CIVILIAN) and hdist(contact.pos, f.pos) < r - EPS for f in scenario.contacts)  # same test as _r7


def weight(scenario, contact) -> float:
    """Multiplies the contact's priority in the order search (`_key`). 1.0 = unchanged.

    TODO: light/heavy pricing (lights scarce at L4).
    """
    return 1.0

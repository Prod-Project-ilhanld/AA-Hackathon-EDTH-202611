"""Which hostiles are worth trying, and in what order. planner.py calls it.

Ideas to build here (see docs/ROADMAP.md, "Where the points are"):
- skip hostiles no plan can ever engage (R7: within `collateral_radius_m` of a friendly/civilian) — done below;
- light effectors are the scarce resource at L4 (need 49-86, have 50), heavies are not (need 10-25, have 35):
  `weight` gives each effector subtype a shadow price from its scarcity and orders the contacts by points per
  priced effector (switch: params.PRICES, OFF: measured, no gain).
  Measured on L4, 25 train seeds (0-24), FLEET_ITERS=3 (reproducible), paired against the same code with the
  prices off: gamma 1 (plain ratio) +0.4 % (mean +4.4 +/- 5.5, 13 better, 11 worse); gamma 2 -0.73 %
  (-7.9 +/- 10.0, 13 better, 11 worse); gamma 4 -0.48 % (-5.2 +/- 10.8, 10 better, 13 worse); 0 invalid. All inside
  the noise, so the order search already finds what the prices encode and they stay off. On L1-L3 the lights are
  also short of supply (L3: 17 needed for 16), so the prices are not 1 there either.

The R7 skip is ON by default (PLANNER_TARGETS=0 turns it off). Measured on L4, 50 seeds, same conditions: +1.27 %
(25 seeds better, 25 equal, 0 worse, 0 invalid); L3, 20 seeds: +0.51 % (10 better, 0 worse); L1 and L2 unchanged.
It cannot cost a point: a skipped hostile is one that every plan fails on R7, and the saved tries buy more restarts.
Python 3.9, standard library only; kit code from `fk`, never `fleetkit`.
"""
import params
from fk.geometry import EPS, hdist
from fk.model import CIVILIAN, EFFECTOR, FRIENDLY, HOSTILE

ENABLED = params.TARGETS


def skip(scenario, contact) -> bool:
    """True if `contact` (a hostile) can never be engaged (R7). Called first in FastPlanner.serve_hostile."""
    if not ENABLED:
        return False
    r = scenario.rules.collateral_radius_m
    return any(f.cls in (FRIENDLY, CIVILIAN) and hdist(contact.pos, f.pos) < r - EPS for f in scenario.contacts)  # same test as _r7


_PRICES = {}  # id(scenario) -> (scenario, {subtype: price}); one scenario per process, so this stays tiny


def prices(scenario) -> dict:
    """Shadow price per effector subtype: max(1, demand / supply), from the fleet and the servable hostiles only.

    Demand sums `contact.needs` over the hostiles `skip` keeps; supply counts the effectors of each subtype. A
    subtype the fleet covers has price 1.0; a scarce one costs more. Nothing here reads the scenario level.
    Computed once per scenario.
    """
    cached = _PRICES.get(id(scenario))
    if cached is not None and cached[0] is scenario:
        return cached[1]
    supply, demand = {}, {}
    for a in scenario.aircraft:
        if a.type == EFFECTOR and a.subtype:
            supply[a.subtype] = supply.get(a.subtype, 0) + 1
    for c in scenario.contacts:
        if c.cls == HOSTILE and not skip(scenario, c):
            for sub, n in c.needs.items():
                demand[sub] = demand.get(sub, 0) + n
    out = {sub: max(1.0, demand[sub] / supply[sub]) for sub in demand if supply.get(sub)}
    _PRICES[id(scenario)] = (scenario, out)
    return out


def weight(scenario, contact) -> float:
    """Multiplies the contact's priority in the order search (`_key`). 1.0 = unchanged.

    Effectors needed divided by their priced cost: a contact that eats scarce light effectors falls back in the
    order, one that only takes plentiful heavy ones moves forward. Exactly 1.0 when every subtype is covered.
    """
    if not params.PRICES:
        return 1.0
    try:
        total = sum(contact.needs.values())
        if total <= 0:
            return 1.0
        price = prices(scenario)
        cost = sum(price.get(sub, 1.0) * n for sub, n in contact.needs.items())
        return (total / cost) ** params.PRICE_GAMMA if cost > 0 else 1.0
    except Exception:  # a pricing bug must never cost a plan
        return 1.0

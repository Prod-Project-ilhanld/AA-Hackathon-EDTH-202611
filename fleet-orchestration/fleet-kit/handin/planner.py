"""Hand-in: python3 planner.py scenario.json plan.json

Greedy planner of the kit, made faster and wider:
- a cheap pre-filter (validate only the touched routes, check R8 only against the others) runs
  before the authoritative full validation, so many more scouts and options can be tried;
- randomised restarts under an internal time budget keep the best valid plan;
- every accepted step passed `evaluate`, the final plan is re-validated, and the fallback is
  the best valid plan found so far (an empty plan if nothing else).
"""
import os
import random
import sys
import time
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fleetkit.baseline import (EFFECTOR_LAYERS, SCOUT_LAYERS, _effector_route, _Planner)  # noqa: E402
from fleetkit.geometry import hdist  # noqa: E402
from fleetkit.model import HOSTILE, SCOUT, UNKNOWN, Aircraft, Contact, Scenario, load_json, save_json  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
from fleetkit.validator import separation_item, separation_violation, validate  # noqa: E402
from fleetkit.model import parse_plan  # noqa: E402

BUDGET_S = float(os.environ.get("PLANNER_BUDGET_S", "38"))
N_SCOUTS = 6


class OutOfTime(Exception):
    pass


class FastPlanner(_Planner):
    def __init__(self, scenario: Scenario, deadline: float, n_scouts: int = N_SCOUTS):
        super().__init__(scenario)
        self.deadline = deadline
        self.n_scouts = n_scouts
        self.aircraft = scenario.aircraft_by_id()
        self.contacts = scenario.contact_by_id()
        self.items: Dict[str, tuple] = {}

    def _check_time(self) -> None:
        if time.time() > self.deadline:
            raise OutOfTime()

    def _scout_candidates(self, contact: Contact, limit: int = 0) -> List[Aircraft]:
        scouts = [a for a in self.sc.aircraft if a.type == SCOUT]
        scouts.sort(key=lambda s: hdist(s.home, contact.pos))
        return scouts[:limit or self.n_scouts]

    def _prefilter(self, extra: Dict[str, List[dict]]) -> bool:
        """Necessary conditions, cheap: the touched routes alone, then R8 against the rest."""
        self._check_time()
        sub = {"seed": self.sc.seed, "routes": [{"aircraft": a, "waypoints": w} for a, w in extra.items()]}
        if validate(self.sc, sub):
            return False
        routes, _ = parse_plan(sub)
        new_items = {}
        for aid, route in routes.items():
            it = separation_item(aid, route, self.aircraft[aid])
            if it is not None:
                new_items[aid] = it
        for oid, route in self.routes.items():
            if oid in new_items or oid in extra:
                continue
            cached = self.items.get(oid)
            if cached is None or cached[0] is not route:
                r, _ = parse_plan({"seed": self.sc.seed, "routes": [{"aircraft": oid, "waypoints": route}]})
                cached = (route, separation_item(oid, r[oid], self.aircraft[oid]))
                self.items[oid] = cached
            other = cached[1]
            if other is None:
                continue
            for it in new_items.values():
                if separation_violation(self.sc.rules, self.contacts, it, other) is not None:
                    return False
        return True

    def _try(self, extra: Dict[str, List[dict]]) -> Optional[float]:
        if not self._prefilter(extra):
            return None
        return super()._try(extra)

    def serve_hostile(self, contact: Contact) -> bool:
        sc = self.sc
        pool = {}
        for sub, n in contact.needs.items():
            free = [a for a in sc.aircraft if a.type != SCOUT and a.subtype == sub and a.id not in self.used]
            free.sort(key=lambda a: hdist(a.home, contact.pos))
            if len(free) < n:
                return False
            pool[sub] = free[:n]
        effectors = [a for sub in sorted(pool) for a in pool[sub]]
        for scout in self._scout_candidates(contact):
            for z in SCOUT_LAYERS:
                for angle in (0.0, 60.0, -60.0):
                    for dep_shift in (0.0, 7.0):
                        built = self._add_observation(scout, contact, z, angle, dep_shift)
                        if built is None:
                            continue
                        tasks, route = built
                        if not self._prefilter({scout.id: route}):
                            continue
                        obs_end = max(w["t"] + w.get("dwell_s", 0.0) for w in route
                                      if w.get("target") == contact.id and w.get("action") == "observe")
                        if self._place_effectors(contact, effectors, obs_end, scout, tasks, route):
                            return True
        return False


def build(scenario: Scenario, order_key, deadline: float, n_scouts: int) -> Optional[dict]:
    """One greedy construction; returns the plan built so far (valid by construction) at the deadline."""
    planner = FastPlanner(scenario, deadline, n_scouts)
    hostiles = sorted((c for c in scenario.contacts if c.cls == HOSTILE), key=order_key)
    unknowns = sorted((c for c in scenario.contacts if c.cls == UNKNOWN), key=lambda c: -c.points)
    try:
        for c in hostiles:
            planner.serve_hostile(c)
        for c in unknowns:
            planner.serve_unknown(c)
    except OutOfTime:
        pass
    return planner._plan({}), planner.score


def solve(scenario: Scenario, budget_s: float = BUDGET_S) -> dict:
    t0 = time.time()
    deadline = t0 + budget_s
    best_plan, best_score = {"seed": scenario.seed, "routes": []}, 0.0
    rng = random.Random(0)
    attempt = 0
    while time.time() < deadline:
        if attempt == 0:
            key = lambda c: -c.points
        else:
            noise = {c.id: rng.uniform(0.6, 1.4) for c in scenario.contacts}
            key = lambda c, noise=noise: -c.points * noise[c.id]
        plan, score = build(scenario, key, deadline, N_SCOUTS)
        res = evaluate(scenario, plan)
        if res.valid and res.score > best_score:
            best_plan, best_score = plan, res.score
        attempt += 1
        if attempt == 1 and time.time() - t0 > 0.5 * budget_s:
            break
    return best_plan


def main() -> None:
    scenario = Scenario.from_dict(load_json(sys.argv[1]))
    plan = solve(scenario)
    save_json(plan, sys.argv[2])


if __name__ == "__main__":
    main()

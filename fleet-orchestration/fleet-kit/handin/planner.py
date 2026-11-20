"""Hand-in: python3 planner.py scenario.json plan.json

Greedy planner of the kit, made faster and wider:
- a cheap pre-filter (validate only the touched routes, check R8 only against the others) runs
  before the authoritative full validation, so many more scouts and options can be tried;
- restarts under an internal time budget keep the best valid plan: a few deterministic orders of
  the contacts (points per effector needed), then hill-climbing around the best order, spread over
  the available cores (serial fallback);
- every accepted step passed the kit scorer, the final plan is re-validated, and the fallback is
  the best valid plan found so far (an empty plan if nothing else).
"""
import multiprocessing
import os
import random
import sys
import time
from typing import Dict, List, Optional

try:
    import fleetkit  # noqa: F401
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fleetkit.baseline import SCOUT_LAYERS, _Planner  # noqa: E402
from fleetkit.geometry import hdist  # noqa: E402
from fleetkit.model import HOSTILE, SCOUT, UNKNOWN, Aircraft, Contact, Scenario, load_json, parse_plan, save_json  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
from fleetkit.validator import separation_item, separation_violation, validate  # noqa: E402

BUDGET_S = float(os.environ.get("PLANNER_BUDGET_S", "38"))
N_SCOUTS = 6
MAX_WORKERS = int(os.environ.get("PLANNER_WORKERS", "8"))


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
        if time.monotonic() > self.deadline:
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


def build(scenario: Scenario, order_key, deadline: float, n_scouts: int):
    """One greedy construction; returns the plan built so far (valid by construction) at the deadline."""
    planner = FastPlanner(scenario, deadline, n_scouts)
    hostiles = sorted((c for c in scenario.contacts if c.cls == HOSTILE), key=order_key)
    unknowns = sorted((c for c in scenario.contacts if c.cls == UNKNOWN), key=lambda c: -c.points)
    try:
        for c in hostiles + unknowns:
            try:
                if c.cls == HOSTILE:
                    planner.serve_hostile(c)
                else:
                    planner.serve_unknown(c)
            except OutOfTime:
                raise
            except Exception:  # a contact that breaks the routing is skipped, never fatal
                continue
    except OutOfTime:
        pass
    return planner._plan({}), planner.score


def _key(scenario: Scenario, alpha: float, noise: Dict[str, float]):
    return lambda c: -noise.get(c.id, 1.0) * c.points / max(1, sum(c.needs.values())) ** alpha


def _search(scenario: Scenario, deadline: float, worker: int, n_workers: int):
    """Builds plans until the deadline; returns the best valid (score, plan) of this worker."""
    alphas = [0.0, 1.0, 0.5, 1.5]
    rng = random.Random(1000 + worker)
    best = (-1.0, {"seed": scenario.seed, "routes": []})
    best_alpha, best_noise = alphas[worker % len(alphas)], {}
    attempt = 0
    while time.monotonic() < deadline:
        if attempt == 0:
            alpha, noise = best_alpha, {}
        else:
            sigma = 0.12 if worker % 2 == 0 else 0.3
            alpha = min(2.0, max(0.0, best_alpha + rng.uniform(-0.2, 0.2)))
            noise = {c.id: max(0.2, best_noise.get(c.id, 1.0) * rng.gauss(1.0, sigma)) for c in scenario.contacts}
        plan, _ = build(scenario, _key(scenario, alpha, noise), deadline, N_SCOUTS)
        try:
            res = evaluate(scenario, plan)
        except Exception:
            res = None
        if res is not None and res.valid and res.score > best[0]:
            best, best_alpha, best_noise = (res.score, plan), alpha, noise
        attempt += 1
    return best


def _worker(args):
    scenario_dict, deadline, worker, n_workers = args
    try:
        return _search(Scenario.from_dict(scenario_dict), deadline, worker, n_workers)
    except Exception:
        return (-1.0, None)


def solve(scenario: Scenario, scenario_dict: dict, budget_s: float = BUDGET_S) -> dict:
    deadline = time.monotonic() + budget_s
    empty = {"seed": scenario.seed, "routes": []}
    best = (0.0, empty)
    n_workers = max(1, min(MAX_WORKERS, os.cpu_count() or 1))
    results = []
    if n_workers > 1:
        pool = None
        try:
            ctx = multiprocessing.get_context("fork")
            pool = ctx.Pool(n_workers)
            jobs = [pool.apply_async(_worker, ((scenario_dict, deadline, w, n_workers),)) for w in range(n_workers)]
            for job in jobs:
                try:
                    results.append(job.get(timeout=max(0.5, deadline + 8.0 - time.monotonic())))
                except Exception:
                    pass
        except Exception:
            results = []
        finally:
            if pool is not None:
                pool.terminate()
    if not results:
        results = [_search(scenario, deadline, 0, 1)] if time.monotonic() < deadline else []
    for score, plan in results:
        if plan is not None and score > best[0]:
            best = (score, plan)
    # last guard: the plan we write was validated by the kit's own scorer
    try:
        if not evaluate(scenario, best[1]).valid:
            return empty
    except Exception:
        return empty
    return best[1]


def main() -> None:
    data = load_json(sys.argv[1])
    scenario = Scenario.from_dict(data)
    try:
        plan = solve(scenario, data)
    except Exception:
        plan = {"seed": scenario.seed, "routes": []}
    save_json(plan, sys.argv[2])


if __name__ == "__main__":
    main()

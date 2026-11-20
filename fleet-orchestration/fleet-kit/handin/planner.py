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

try:  # routing module of the team (3D minimum-energy routes); the planner works without it
    from fleetkit.baseline import EFFECTOR_LAYERS
    try:
        from . import routing as _routing  # type: ignore
    except ImportError:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import routing as _routing  # type: ignore
except Exception:  # noqa: BLE001
    _routing = None
    EFFECTOR_LAYERS = ()

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


class RoutedPlanner(FastPlanner):
    """Same search, routes built by the team's routing module (minimum energy, visibility-graph detours)."""

    def __init__(self, scenario: Scenario, deadline: float, n_scouts: int = N_SCOUTS):
        super().__init__(scenario, deadline, n_scouts)
        self.eng = _routing.get_engine(scenario)
        self.layers = (None,) + tuple(EFFECTOR_LAYERS)

    def _add_observation(self, scout, contact, z, angle, dep_shift):
        tasks = self.tasks[scout.id] + [contact]
        try:
            route = _routing.build_scout_route(scout, tasks, self.sc, z_layer=z, depart_shift=dep_shift,
                                               engine=self.eng, angle_offset_deg=angle)
        except Exception:  # noqa: BLE001  a route that cannot be built is simply not tried
            route = None
        return (tasks, route) if route is not None else None

    def _place_effectors(self, contact, effectors, obs_end, scout, tasks, scout_route) -> bool:
        lo, hi = contact.window
        base = max(obs_end + self.sc.rules.confirm_margin_s + 2.0, lo)
        for delay in (0.0, 8.0, 20.0, 45.0, 90.0):
            arrive = base + delay
            if arrive + 5.0 * len(effectors) > hi:
                break
            for angle in (0.0, 35.0, -35.0):
                for rotation in range(3):
                    extra = {scout.id: scout_route}
                    ok = True
                    for i, eff in enumerate(effectors):
                        z = self.layers[(i + rotation) % len(self.layers)]
                        try:
                            route, _ = _routing.build_effector_route(
                                eff, contact, arrive + 5.0 * i, self.sc, z_layer=z,
                                approach_angle=angle, engine=self.eng)
                        except Exception:  # noqa: BLE001
                            route = None
                        if route is None:
                            ok = False
                            break
                        extra[eff.id] = route
                    if not ok:
                        continue
                    new = self._try(extra)
                    if new is not None and new > self.score:
                        self.routes.update(extra)
                        self.tasks[scout.id] = tasks
                        self.used.update(e.id for e in effectors)
                        self.score = new
                        return True
        return False



def build(scenario: Scenario, order_key, deadline: float, n_scouts: int, planner_cls=None):
    """One greedy construction; returns the plan built so far (valid by construction) at the deadline."""
    planner = (planner_cls or FastPlanner)(scenario, deadline, n_scouts)
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
    """Builds plans until the deadline; returns the best valid (score, plan) of this worker.

    The first two builds use the same contact order with each router (the team's routing module,
    the kit's own); then the worker hill-climbs around the best (router, order) it has found.
    """
    alphas = [0.0, 1.0, 0.5, 1.5]
    classes = [RoutedPlanner, FastPlanner] if _routing is not None else [FastPlanner]
    first = worker % len(classes)
    rng = random.Random(1000 + worker)
    best = (-1.0, {"seed": scenario.seed, "routes": []})
    base_alpha = alphas[(worker // len(classes)) % len(alphas)]
    best_alpha, best_noise, best_cls = base_alpha, {}, classes[first]
    attempt = 0
    while time.monotonic() < deadline:
        if attempt < len(classes):
            cls, alpha, noise = classes[(first + attempt) % len(classes)], base_alpha, {}
        else:
            cls = best_cls
            sigma = 0.12 if worker % 2 == 0 else 0.3
            alpha = min(2.0, max(0.0, best_alpha + rng.uniform(-0.2, 0.2)))
            noise = {c.id: max(0.2, best_noise.get(c.id, 1.0) * rng.gauss(1.0, sigma)) for c in scenario.contacts}
        try:
            plan, _ = build(scenario, _key(scenario, alpha, noise), deadline, N_SCOUTS, cls)
            res = evaluate(scenario, plan)
        except Exception:  # a failing router never costs the whole run
            res = None
        if res is not None and res.valid and res.score > best[0]:
            best, best_alpha, best_noise, best_cls = (res.score, plan), alpha, noise, cls
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

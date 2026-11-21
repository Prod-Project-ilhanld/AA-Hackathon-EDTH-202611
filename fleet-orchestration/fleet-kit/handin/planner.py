"""Hand-in: python3 planner.py scenario.json plan.json

Greedy planner of the kit, made faster and wider:
- a cheap pre-filter (validate only the touched routes, check R8 only against the others) runs
  before the authoritative full validation, so many more scouts and options can be tried: the 6
  nearest scouts with all options, then every other scout with plain options (on L4 the near scouts
  saturate while others stay on the ground);
- restarts under an internal time budget keep the best valid plan: a few deterministic orders of
  the contacts (points per effector needed), then hill-climbing around the best order, spread over
  the available cores (serial fallback);
- every accepted step passed the kit scorer, the final plan is re-validated, and the fallback is
  the best valid plan found so far (an empty plan if nothing else).
"""
import json
import multiprocessing
import os
import random
import signal
import sys
import time

T0 = time.monotonic()  # every budget counts from process start (ROADMAP rule 10)
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # vendored kit helpers live in handin/fk

from fk.baseline import SCOUT_LAYERS, _Planner  # noqa: E402
from fk.geometry import hdist  # noqa: E402
from fk.model import HOSTILE, SCOUT, UNKNOWN, Aircraft, Contact, Scenario, load_json, parse_plan, save_json  # noqa: E402
from fk.scorer import evaluate  # noqa: E402
from fk.validator import separation_item, separation_violation, validate  # noqa: E402

try:  # routing module of the team (3D minimum-energy routes); the planner works without it
    from fk.baseline import EFFECTOR_LAYERS
    try:
        from . import routing as _routing  # type: ignore
    except ImportError:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import routing as _routing  # type: ignore
except Exception:  # noqa: BLE001
    _routing = None
    EFFECTOR_LAYERS = ()

BUDGET_S = float(os.environ.get("PLANNER_BUDGET_S", "38"))  # search deadline, seconds from process start
ALARM_S = float(os.environ.get("PLANNER_ALARM_S", "52"))    # backstop: write the last validated plan and exit
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
        self.far = True     # also try the scouts beyond the nearest n_scouts (plain options only)

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
        scouts = [a for a in sc.aircraft if a.type == SCOUT]
        scouts.sort(key=lambda s: hdist(s.home, contact.pos))
        # tier 1: the nearest scouts with the full set of options; tier 2: the others, plain options only
        tiers = ((scouts[:self.n_scouts], (0.0, 60.0, -60.0), (0.0, 7.0)),
                 (scouts[self.n_scouts:] if self.far else [], (0.0,), (0.0, 7.0)))
        for cands, angles, shifts in tiers:
            for scout in cands:
                for z in SCOUT_LAYERS:
                    for angle in angles:
                        for dep_shift in shifts:
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



def build(scenario: Scenario, order_key, deadline: float, n_scouts: int, planner_cls=None, far: bool = True):
    """One greedy construction; returns the plan built so far (valid by construction) at the deadline."""
    planner = (planner_cls or FastPlanner)(scenario, deadline, n_scouts)
    planner.far = far
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

    The first two builds of a worker use two variants of the construction (router of the team or of the
    kit, with or without the far scouts); even workers start with the far scouts, odd workers without, so that
    two workers already cover the four variants. Then the worker hill-climbs around the best variant and order.
    """
    alphas = [0.0, 1.0, 0.5, 1.5]
    classes = [RoutedPlanner, FastPlanner] if _routing is not None else [FastPlanner]
    n_far = max(0, sum(1 for a in scenario.aircraft if a.type == SCOUT) - N_SCOUTS)
    first = worker % len(classes)
    far0 = (worker % 2 == 0) or n_far == 0
    rng = random.Random(1000 + worker)
    best = (-1.0, {"seed": scenario.seed, "routes": []})
    base_alpha = alphas[(worker // len(classes)) % len(alphas)]
    best_alpha, best_noise, best_cls, best_far = base_alpha, {}, classes[first], far0
    best_val = -1.0
    attempt = 0
    while time.monotonic() < deadline:
        if attempt < len(classes):
            cls, far, alpha, noise = classes[(first + attempt) % len(classes)], far0, base_alpha, {}
            if worker % 2 == 1 and n_far > 0:
                far = False
        else:
            cls, far = best_cls, best_far
            sigma = 0.12 if worker % 2 == 0 else 0.3
            alpha = min(2.0, max(0.0, best_alpha + rng.uniform(-0.2, 0.2)))
            noise = {c.id: max(0.2, best_noise.get(c.id, 1.0) * rng.gauss(1.0, sigma)) for c in scenario.contacts}
        try:
            plan, _ = build(scenario, _key(scenario, alpha, noise), deadline, N_SCOUTS, cls, far)
            res = evaluate(scenario, plan)
        except Exception:  # a failing router never costs the whole run
            res = None
        if res is not None and res.valid and res.score > best[0]:
            best, best_alpha, best_noise, best_cls, best_far = (res.score, plan), alpha, noise, cls, far
        attempt += 1
    return best


def _worker(args):
    scenario_dict, deadline, worker, n_workers = args
    try:
        return _search(Scenario.from_dict(scenario_dict), deadline, worker, n_workers)
    except Exception:
        return (-1.0, None)


def solve(scenario: Scenario, scenario_dict: dict, budget_s: float = BUDGET_S) -> dict:
    # beyond the official L4 (100 aircraft) route building and validation overshoot the deadline more and more
    # (measured: +1 s at 100, +9 s at 300, +11 s at 400 aircraft): shrink the budget so the 60 s limit holds
    budget_s = max(10.0, budget_s - 0.04 * max(0, len(scenario.aircraft) - 100))
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


_OUT = sys.argv[2] if len(sys.argv) > 2 else "plan.json"
_best_text = None  # pre-serialised last validated plan, written by the alarm handler


def _write(text: str, suffix: str = ".tmp") -> None:
    tmp = _OUT + suffix
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(tmp, _OUT)  # atomic: the jury never reads a half-written plan


def _keep(plan: dict) -> None:
    global _best_text
    _best_text = json.dumps(plan, indent=1) + "\n"
    _write(_best_text)


def _alarm(signum, frame) -> None:
    for child in multiprocessing.active_children():
        child.kill()
    if _best_text is not None:
        _write(_best_text, ".alarm.tmp")
    os._exit(0)


def _official_guard(data: dict, plan: dict) -> dict:
    """Final check with the jury's own validator when importable (else the vendored copy); never negative."""
    empty = {"seed": data.get("seed"), "routes": []}
    try:
        from fleetkit.model import Scenario as OfficialScenario
        from fleetkit.scorer import evaluate as official_evaluate
    except Exception:  # official kit missing or renamed: the vendored validator is identical today
        OfficialScenario, official_evaluate = Scenario, evaluate
    result = official_evaluate(OfficialScenario.from_dict(data), plan)
    return plan if result.valid and result.score >= 0 else empty


def main() -> None:
    data = load_json(sys.argv[1])
    _keep({"seed": data.get("seed"), "routes": []})  # valid, scores 0: written before any search
    if hasattr(signal, "setitimer"):
        signal.signal(signal.SIGALRM, _alarm)
        signal.setitimer(signal.ITIMER_REAL, max(0.1, ALARM_S - (time.monotonic() - T0)))
    scenario = Scenario.from_dict(data)
    plan = solve(scenario, data, max(0.5, BUDGET_S - (time.monotonic() - T0)))
    _keep(_official_guard(data, plan))


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:  # the last validated plan is already on disk; never exit non-zero
        print("planner: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
    sys.exit(0)

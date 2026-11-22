"""Hand-in: python3 planner.py scenario.json plan.json

Greedy planner of the kit, made faster and wider:
- an incremental check (validate only the touched routes, check R8 only against the others, keep
  the score by differences) replaces the full validation of the whole plan at every try, which made
  a construction about 3 times faster; the full kit scorer still validates every plan we keep. So
  many more scouts and options can be tried: the 15
  nearest scouts with all options, then every other scout with plain options (on L4 the near scouts
  saturate while others stay on the ground, so every scout of a 15-scout fleet is tried);
- restarts under an internal time budget keep the best valid plan: a few deterministic orders of
  the contacts (points per effector needed), then hill-climbing around the best order, spread over
  the available cores (serial fallback);
- every accepted step passed the kit scorer, the final plan is re-validated, and the fallback is
  the best valid plan found so far (an empty plan if nothing else).
- on the smallest fleets (L1, 5 aircraft) the search stops once nothing better was found for 12 s
  (same scores on 50 seeds, 12 s instead of 38 s: only the time tie-break changes).
"""
import json
import multiprocessing
import os
import random
import signal
import sys
import threading
import time

T0 = time.monotonic()  # every budget counts from process start (ROADMAP rule 10)
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # vendored kit helpers live in handin/fk

from fk.baseline import SCOUT_LAYERS, _Planner  # noqa: E402
from fk.geometry import hdist  # noqa: E402
from fk.model import HOSTILE, SCOUT, UNKNOWN, Aircraft, Contact, Scenario, load_json, parse_plan, save_json  # noqa: E402
from fk.energy import route_energy_wh  # noqa: E402
from fk.scorer import evaluate  # noqa: E402
from fk.validator import separation_item, separation_violation, validate  # noqa: E402
import params  # noqa: E402       every tunable number and flag
import deconflict  # noqa: E402  starter: R8 departure scheduler (off by default)
import targets  # noqa: E402     starter: which hostiles to try, priorities (off by default)
import scouts  # noqa: E402      scout tours for the unknowns (off by default)
import tours  # noqa: E402       tours-first model: which scout observes what, in which order

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

from params import BOTH_ROUTERS, BUDGET_S, ALARM_S, MAX_WORKERS, MIN_BUILDS, N_SCOUTS, SMALL_FLEET, STAGNATION_S  # noqa: E402


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
        self._cur: Optional[Contact] = None     # the contact being served: its points are the gain of a step
        self.energy_cache: Dict[str, tuple] = {}

    def _check_time(self) -> None:
        if time.monotonic() > self.deadline:
            raise OutOfTime()

    def _scouts_for(self, contact: Contact) -> List[Aircraft]:
        """Every scout, in the order they are tried for `contact`: nearest home first."""
        scouts = [a for a in self.sc.aircraft if a.type == SCOUT]
        scouts.sort(key=lambda s: hdist(s.home, contact.pos))
        return scouts

    def _scout_candidates(self, contact: Contact, limit: int = 0) -> List[Aircraft]:
        scouts = [a for a in self.sc.aircraft if a.type == SCOUT]
        scouts.sort(key=lambda s: hdist(s.home, contact.pos))
        return scouts[:limit or self.n_scouts]

    def _prefilter(self, extra: Dict[str, List[dict]]) -> bool:
        return self._prefilter_routes(extra) is not None

    def _prefilter_routes(self, extra: Dict[str, List[dict]]):
        """The touched routes alone (every per-route and per-contact rule), then R8 against the rest.

        Returns the parsed touched routes when the plan with these routes added or replaced is valid for
        every rule except the confirmation of the earlier contacts of a rebuilt scout route (see _try).
        """
        self._check_time()
        sub = {"seed": self.sc.seed, "routes": [{"aircraft": a, "waypoints": w} for a, w in extra.items()]}
        if validate(self.sc, sub):
            return None
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
                    return None
        return routes

    def _energy_of(self, aid: str) -> float:
        route = self.routes[aid]
        cached = self.energy_cache.get(aid)
        if cached is None or cached[0] is not route:
            r, _ = parse_plan({"seed": self.sc.seed, "routes": [{"aircraft": aid, "waypoints": route}]})
            cached = (route, route_energy_wh(r[aid].waypoints, self.aircraft[aid]))
            self.energy_cache[aid] = cached
        return cached[1]

    def _confirmations_ok(self, extra: Dict[str, List[dict]]) -> bool:
        """R4 for the earlier hostile contacts of a rebuilt scout route: their engagements stay confirmed."""
        margin = self.sc.rules.confirm_margin_s
        for sid, wps in extra.items():
            for t in self.tasks.get(sid, ()):
                cid = t.id if hasattr(t, "id") else t["cid"]
                if self.contacts[cid].cls != HOSTILE:
                    continue
                engages = [r[-1]["t"] for r in self.routes.values()
                           if r and r[-1].get("action") == "engage" and r[-1].get("target") == cid]
                if not engages:
                    continue
                ends = [w["t"] + w.get("dwell_s", 0.0) for w in wps
                        if w.get("action") == "observe" and w.get("target") == cid]
                if any(not any(o <= e - margin + 1e-6 for o in ends) for e in engages):
                    return False
        return True

    def _try(self, extra: Dict[str, List[dict]]) -> Optional[float]:
        """Score of the plan with the routes of `extra` added or replaced, or None when it would be invalid.

        Incremental: the touched routes are validated alone and R8 is checked against the others (the only
        rule that couples routes), so the full validation of the whole plan is not repeated for every try.
        """
        if not deconflict.adjust(self, extra):
            return None
        routes = self._prefilter_routes(extra)
        if routes is None or not self._confirmations_ok(extra):
            return None
        rules = self.sc.rules
        energy_new = sum(route_energy_wh(routes[a].waypoints, self.aircraft[a]) for a in routes)
        energy_old = sum(self._energy_of(a) for a in extra if a in self.routes)
        new_eff = sum(1 for a in extra if a not in self.routes and self.aircraft[a].type != SCOUT)
        gain = self._cur.points if self._cur is not None else 0.0
        return self.score + gain - rules.lambda_e * (energy_new - energy_old) - rules.c_eff * new_eff

    def serve_unknown(self, contact: Contact) -> bool:
        self._cur = contact
        try:
            return super().serve_unknown(contact)
        finally:
            self._cur = None

    def serve_hostile(self, contact: Contact) -> bool:
        if targets.skip(self.sc, contact):
            return False
        self._cur = contact
        try:
            return self._serve_hostile(contact)
        finally:
            self._cur = None

    def _serve_hostile(self, contact: Contact) -> bool:
        sc = self.sc
        pool = {}
        for sub, n in contact.needs.items():
            free = [a for a in sc.aircraft if a.type != SCOUT and a.subtype == sub and a.id not in self.used]
            free.sort(key=lambda a: hdist(a.home, contact.pos))
            if len(free) < n:
                return False
            pool[sub] = free[:n]
        effectors = [a for sub in sorted(pool) for a in pool[sub]]
        scouts = self._scouts_for(contact)
        # tier 1: the nearest scouts with the full set of options; tier 2: the others, plain options only
        tiers = ((scouts[:self.n_scouts], (0.0, 60.0, -60.0), (0.0, 7.0)),
                 (scouts[self.n_scouts:] if self.far else [], (0.0,), (0.0, 7.0)))
        for cands, angles, shifts in tiers:
            for scout in cands:
                for z in params.SCOUT_LEVELS:
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

    def _latest_ends(self, tasks):
        """Latest observation end of each task already struck: its first engagement minus the R4 margin."""
        out = {}
        margin = self.sc.rules.confirm_margin_s
        for t in tasks:
            engages = [r[-1]["t"] for r in self.routes.values()
                       if r and r[-1].get("action") == "engage" and r[-1].get("target") == t.id]
            if engages:
                out[t.id] = min(engages) - margin
        return out or None

    def _add_observation(self, scout, contact, z, angle, dep_shift):
        tasks = self.tasks[scout.id] + [contact]
        latest = self._latest_ends(tasks[:-1]) if params.LATEST_ENDS else None
        try:
            route = _routing.build_scout_route(scout, tasks, self.sc, z_layer=z, depart_shift=dep_shift,
                                               engine=self.eng, angle_offset_deg=angle, latest_ends=latest)
        except Exception:  # noqa: BLE001  a route that cannot be built is simply not tried
            route = None
        return (tasks, route) if route is not None else None

    def _place_effectors(self, contact, effectors, obs_end, scout, tasks, scout_route) -> bool:
        lo, hi = contact.window
        base = max(obs_end + self.sc.rules.confirm_margin_s + 2.0, lo)
        for delay in (0.0, 20.0, 90.0):   # fewer arrival delays: faster builds won more than the extra options
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



class TourPlanner(RoutedPlanner):
    """RoutedPlanner that tries first the scout a tours-first model planned for each contact (tours.py)."""

    def __init__(self, scenario: Scenario, deadline: float, n_scouts: int, hint: Dict[str, str]):
        super().__init__(scenario, deadline, n_scouts)
        self.hint = hint

    def _scouts_for(self, contact: Contact) -> List[Aircraft]:
        planned = self.hint.get(contact.id)
        scouts = [a for a in self.sc.aircraft if a.type == SCOUT]
        scouts.sort(key=lambda s: (s.id != planned, hdist(s.home, contact.pos)))
        return scouts

    def _scout_candidates(self, contact: Contact, limit: int = 0) -> List[Aircraft]:
        return self._scouts_for(contact)[:limit or self.n_scouts]


def build_guided(scenario: Scenario, model, rng: random.Random, deadline: float):
    """One construction that follows the tours of `model` (contacts in tour order, planned scout first), then
    serves the contacts left out in points order; returns the plan built so far (valid by construction)."""
    tour = model.solve(rng, iters=params.TOURS_ITERS)
    planner = TourPlanner(scenario, deadline, N_SCOUTS, {c: s for s, seq in tour.items() for c in seq})
    order = []
    for k in range(max((len(seq) for seq in tour.values()), default=0)):
        order.extend(seq[k] for seq in tour.values() if k < len(seq))
    by_id = scenario.contact_by_id()
    rest = sorted((c for c in scenario.contacts if c.cls in (HOSTILE, UNKNOWN) and c.id not in order),
                  key=lambda c: -c.points)
    try:
        for c in [by_id[cid] for cid in order] + rest:
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
        try:  # starter: scout tours for the unknowns left unserved (off by default)
            scouts.sweep_unknowns(planner, unknowns, SCOUT, hdist)
        except OutOfTime:
            raise
        except Exception:  # never fatal: the plan so far is valid
            pass
    except OutOfTime:
        pass
    return planner._plan({}), planner.score


def _key(scenario: Scenario, alpha: float, noise: Dict[str, float]):
    return lambda c: -noise.get(c.id, 1.0) * targets.weight(scenario, c) * c.points / max(1, sum(c.needs.values())) ** alpha


def _search(scenario: Scenario, deadline: float, worker: int, n_workers: int):
    """Builds plans until the deadline; returns the best valid (score, plan) of this worker.

    Small fleets (L1, L2) build once with each router, then hill-climb around the better one. Larger fleets
    (L3, L4) build only with the team's router (measured better there: the same time buys more restarts);
    the kit's router is the fallback when the team's gives nothing valid. With more scouts than N_SCOUTS,
    even workers also try the far scouts and odd workers do not.
    """
    alphas = params.ALPHAS
    if _routing is None:
        classes = [FastPlanner]
    elif len(scenario.aircraft) <= BOTH_ROUTERS:
        classes = [RoutedPlanner, FastPlanner]      # small fleets: both routers, the kit's one adds variety
    else:
        classes = [RoutedPlanner]                   # larger fleets: the team's router only, it wins on L3 and L4
    n_far = max(0, sum(1 for a in scenario.aircraft if a.type == SCOUT) - N_SCOUTS)
    first = worker % len(classes)
    far0 = (worker % 2 == 0) or n_far == 0
    rng = random.Random(1000 + worker)
    best = (-1.0, {"seed": scenario.seed, "routes": []})
    base_alpha = alphas[(worker // len(classes)) % len(alphas)]
    best_alpha, best_noise, best_cls, best_far = base_alpha, {}, classes[first], far0
    best_val = -1.0
    attempt = 0
    builds = 0  # attempt restarts when the router falls back; FLEET_ITERS counts every build
    last_gain = time.monotonic()
    small = len(scenario.aircraft) <= SMALL_FLEET
    guided = (params.TOURS and _routing is not None
              and params.TOURS_MIN_AC <= len(scenario.aircraft) <= params.TOURS_MAX_AC
              and n_workers > 1 and worker % params.TOURS_EVERY == params.TOURS_EVERY - 1)
    if guided:
        model = tours.Model(scenario, skip=lambda c: targets.skip(scenario, c))
        while time.monotonic() < deadline and (params.FLEET_ITERS <= 0 or builds < params.FLEET_ITERS):
            try:
                plan, _ = build_guided(scenario, model, rng, deadline)
                res = evaluate(scenario, plan)
            except Exception:
                res = None
            if res is not None and res.valid and res.score > best[0]:
                best = (res.score, plan)
            builds += 1
        return best
    while time.monotonic() < deadline and (params.FLEET_ITERS <= 0 or builds < params.FLEET_ITERS):
        if (params.FLEET_ITERS <= 0 and small and attempt >= MIN_BUILDS
                and time.monotonic() - last_gain > STAGNATION_S):
            break
        if attempt < len(classes):
            cls, far, alpha, noise = classes[(first + attempt) % len(classes)], far0, base_alpha, {}
            if worker % 2 == 1 and n_far > 0:
                far = False
        else:
            cls, far = best_cls, best_far
            sigma = params.SIGMA_EVEN if worker % 2 == 0 else params.SIGMA_ODD
            alpha = min(2.0, max(0.0, best_alpha + rng.uniform(-0.2, 0.2)))
            noise = {c.id: max(0.2, best_noise.get(c.id, 1.0) * rng.gauss(1.0, sigma)) for c in scenario.contacts}
        try:
            plan, _ = build(scenario, _key(scenario, alpha, noise), deadline, N_SCOUTS, cls, far)
            res = evaluate(scenario, plan)
        except Exception:  # a failing router never costs the whole run
            res = None
        if (res is None or not res.valid) and cls is RoutedPlanner and best[0] < 0:
            # the team's router gave nothing valid on this scenario: continue with the kit's router
            classes, best_cls, attempt = [FastPlanner], FastPlanner, -1
        if res is not None and res.valid and res.score > best[0]:
            best, best_alpha, best_noise, best_cls, best_far = (res.score, plan), alpha, noise, cls, far
            last_gain = time.monotonic()
        attempt += 1
        builds += 1
    return best


def _worker(args):
    scenario_dict, deadline, worker, n_workers = args
    try:
        return _search(Scenario.from_dict(scenario_dict), deadline, worker, n_workers)
    except Exception:
        return (-1.0, None)


def _greedy(scenario: Scenario) -> Tuple[float, Optional[dict]]:
    """(score, plan) of the kit's greedy plan, validated, or (0.0, None) when it is invalid, scores nothing,
    or the alarm is too close. Measured at 2.7 s on L4 idle, up to 13 s under load."""
    if ALARM_S - (time.monotonic() - T0) < params.FALLBACK_MIN_LEFT_S:
        return (0.0, None)
    try:
        from fk.baseline import greedy_plan
        plan = greedy_plan(scenario)
        result = evaluate(scenario, plan)
        return (result.score, plan) if result.valid and result.score > 0 else (0.0, None)
    except Exception:
        return (0.0, None)


def _greedy_fallback(scenario: Scenario) -> Optional[dict]:
    """The kit's greedy plan, validated, or None. Only on a failure path, and only with time left before the alarm."""
    return _greedy(scenario)[1]


def _load_plan(scenario: Scenario, plan: dict, drop, deadline: float):
    """A RoutedPlanner holding `plan` without the scouts in `drop` and the strikes they confirmed, or None."""
    cs = scenario.contact_by_id()
    ac = scenario.aircraft_by_id()
    routes = {r["aircraft"]: r["waypoints"] for r in plan["routes"]}
    tasks = {s.id: [] for s in scenario.aircraft if s.type == SCOUT}
    for aid, wps in routes.items():
        if ac[aid].type == SCOUT:
            tasks[aid] = [cs[w["target"]] for w in wps if w.get("action") == "observe"]
    gone = set()
    for sid in drop:
        gone |= {c.id for c in tasks.get(sid, [])}
        routes.pop(sid, None)
        tasks[sid] = []
    for aid in list(routes):
        if ac[aid].type != SCOUT and any(w.get("action") == "engage" and w.get("target") in gone for w in routes[aid]):
            routes.pop(aid)
    planner = RoutedPlanner(scenario, deadline, N_SCOUTS)
    planner.routes, planner.tasks = routes, tasks
    planner.used = {a for a in routes if ac[a].type != SCOUT}
    result = evaluate(scenario, planner._plan({}))
    if not result.valid:
        return None, set()
    planner.score = result.score
    return planner, set(result.served)


def _repair(scenario: Scenario, start: Tuple[float, dict], deadline: float, worker: int) -> Tuple[float, dict]:
    """Ruin and recreate around `start` until the deadline; returns the best valid (score, plan) found."""
    rng = random.Random(7000 + worker)
    best = start
    scouts = [a.id for a in scenario.aircraft if a.type == SCOUT]
    contacts = [c for c in scenario.contacts if c.cls in (HOSTILE, UNKNOWN)]
    done = 0
    fixed = params.FLEET_ITERS > 0  # reproducible: a fixed number of repairs, the clock plays no part
    while ((done < params.LNS_ITERS and time.monotonic() - T0 < ALARM_S - 10.0) if fixed
           else time.monotonic() < deadline):
        done += 1
        drop = rng.sample(scouts, min(len(scouts), rng.choice((1, 1, 2))))
        try:
            planner, served = _load_plan(scenario, best[1], drop, time.monotonic() + 600.0 if fixed else deadline)
            if planner is None:
                continue
            todo = [c for c in contacts if c.id not in served]
            todo.sort(key=lambda c: -c.points * rng.uniform(0.6, 1.4))
            for c in todo:
                try:
                    if c.cls == HOSTILE:
                        planner.serve_hostile(c)
                    else:
                        planner.serve_unknown(c)
                except OutOfTime:
                    raise
                except Exception:  # a contact that breaks the routing is skipped
                    continue
        except OutOfTime:
            if params.FLEET_ITERS > 0:
                continue
            break
        except Exception:
            continue
        plan = planner._plan({})
        try:
            result = evaluate(scenario, plan)
        except Exception:
            continue
        if result.valid and result.score > best[0] + 1e-6:
            best = (result.score, plan)
    return best


def _repair_worker(args):
    scenario_dict, start, deadline, worker = args
    try:
        return _repair(Scenario.from_dict(scenario_dict), start, deadline, worker)
    except Exception:
        return start


def _repair_phase(scenario: Scenario, scenario_dict: dict, best: Tuple[float, dict], deadline: float,
                  n_workers: int) -> Tuple[float, dict]:
    """Runs _repair in every worker from the best plan; returns the best valid result (the input when nothing beats it)."""
    pool = None
    try:
        ctx = multiprocessing.get_context("fork")
        pool = ctx.Pool(n_workers)
        jobs = [pool.apply_async(_repair_worker, ((scenario_dict, best, deadline, w),)) for w in range(n_workers)]
        for job in jobs:
            try:
                wait = None if params.FLEET_ITERS > 0 else max(0.5, deadline + params.POOL_GRACE_S - time.monotonic())
                score, plan = job.get(timeout=wait)
                if plan is not None and score > best[0]:
                    best = (score, plan)
            except Exception:
                pass
    except Exception:
        pass
    finally:
        if pool is not None:
            pool.terminate()
    return best


def solve(scenario: Scenario, scenario_dict: dict, budget_s: float = BUDGET_S) -> dict:
    # beyond the official L4 (100 aircraft) route building and validation overshoot the deadline more and more
    # (measured: +1 s at 100, +9 s at 300, +11 s at 400 aircraft): shrink the budget so the 60 s limit holds
    if params.INJECT_FAIL:
        raise RuntimeError("FLEET_INJECT_FAIL")
    budget_s = max(min(budget_s, params.BUDGET_FLOOR_S),
                   budget_s - params.BUDGET_SHRINK_PER_AC * max(0, len(scenario.aircraft) - params.BUDGET_SHRINK_FROM))
    deadline = time.monotonic() + budget_s
    lns = params.LNS and _routing is not None and len(scenario.aircraft) >= params.LNS_MIN_AC
    final_deadline = deadline
    if lns and params.FLEET_ITERS <= 0:
        deadline = time.monotonic() + budget_s * (1.0 - params.LNS_SHARE)  # the search ends early, repair takes the rest
    empty = {"seed": scenario.seed, "routes": []}
    best = (0.0, empty)
    n_workers = max(1, min(MAX_WORKERS, os.cpu_count() or 1))
    results = []
    # task 11: the kit's greedy plan is built in a thread while the search runs, so it costs no time on the clock
    greedy = []
    helper = threading.Thread(target=lambda: greedy.append(_greedy(scenario)), daemon=True)
    if n_workers > 1:
        pool = None
        try:
            ctx = multiprocessing.get_context("fork")
            pool = ctx.Pool(n_workers)
            if params.KEEP_BETTER_GREEDY:
                helper.start()  # after the fork: no thread may be running while the pool forks its workers
            jobs = [pool.apply_async(_worker, ((scenario_dict, deadline, w, n_workers),)) for w in range(n_workers)]
            for job in jobs:
                try:
                    # FLEET_ITERS: wait for every worker (the alarm is the only stop), else drop the late ones
                    wait = None if params.FLEET_ITERS > 0 else max(0.5, deadline + params.POOL_GRACE_S - time.monotonic())
                    results.append(job.get(timeout=wait))
                except Exception:
                    pass
        except Exception:
            results = []
        finally:
            if pool is not None:
                pool.terminate()
    if params.KEEP_BETTER_GREEDY and helper.ident is None:
        helper.start()  # serial path: the pool is gone, nothing forks any more
    if not results:
        results = [_search(scenario, deadline, 0, 1)] if time.monotonic() < deadline else []
    for score, plan in results:  # worker-index order, strict >: ties go to the lowest worker
        if plan is not None and score > best[0]:
            best = (score, plan)
    if lns and best[0] > 0.0 and n_workers > 1:
        if helper.is_alive():  # no thread may run while the repair pool forks: wait for the greedy plan, or skip
            helper.join(None if params.FLEET_ITERS > 0 else max(0.0, final_deadline - time.monotonic() - 4.0))
        if not helper.is_alive():
            if _checkpoint is not None:
                _checkpoint(best[1])  # the alarm writes the search's best plan, never the empty one, during the repair
            best = _repair_phase(scenario, scenario_dict, best, final_deadline, n_workers)
    if best[0] <= 0.0:  # every build failed or found nothing positive: the kit's greedy plan beats an empty one
        return _greedy_fallback(scenario) or empty
    # last guard: the plan we write was validated by the kit's own scorer
    try:
        res = evaluate(scenario, best[1])
        if not res.valid or res.score < 0:
            return _greedy_fallback(scenario) or empty
    except Exception:
        return _greedy_fallback(scenario) or empty
    if helper.ident is not None:  # never below the kit baseline: the greedy plan wins when it scores strictly higher
        helper.join(None if params.FLEET_ITERS > 0 else max(0.0, deadline - time.monotonic()))
        if greedy and greedy[0][1] is not None and greedy[0][0] > res.score:
            return greedy[0][1]
    return best[1]


_OUT = sys.argv[2] if len(sys.argv) > 2 else "plan.json"
_checkpoint = None  # set by main(): writes a validated plan to disk before the repair phase
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
        result = official_evaluate(OfficialScenario.from_dict(data), plan)
    except Exception:  # official kit missing, renamed or changed: the vendored validator is identical today
        result = evaluate(Scenario.from_dict(data), plan)
    return plan if result.valid and result.score >= 0 else empty


def main() -> None:
    try:
        data = load_json(sys.argv[1])
    except Exception:  # missing or malformed scenario: a plan file with no seed beats no file
        data = None
    _keep({"seed": data.get("seed") if isinstance(data, dict) else None, "routes": []})  # valid, scores 0
    if data is None:
        return
    if hasattr(signal, "setitimer"):
        signal.signal(signal.SIGALRM, _alarm)
        signal.setitimer(signal.ITIMER_REAL, max(0.1, ALARM_S - (time.monotonic() - T0)))
    scenario = Scenario.from_dict(data)
    global _checkpoint
    _checkpoint = _keep
    try:
        plan = solve(scenario, data, max(0.5, BUDGET_S - (time.monotonic() - T0)))
    except Exception:  # solve crashed: the kit's greedy plan beats the empty one that is already on disk
        plan = _greedy_fallback(scenario) or {"seed": scenario.seed, "routes": []}
    _keep(plan)  # validated, never negative: the alarm backstop now writes this plan, not the empty one
    while params.INJECT_HANG:  # test hook: the alarm must write the kept plan
        time.sleep(1)
    _keep(_official_guard(data, plan))


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:  # the last validated plan is already on disk; never exit non-zero
        print("planner: %s: %s" % (type(exc).__name__, exc), file=sys.stderr)
    sys.exit(0)

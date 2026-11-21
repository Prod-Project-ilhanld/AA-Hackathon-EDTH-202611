"""Link-loss mini-simulator: what a valid plan is still worth when the radio dies and the world drifts.

Model (all assumptions are ours: the kit does not simulate link loss and its scorer does not grade it):
- The plan is valid and deterministic. At `t_cut` the radio link to the operator is lost for good.
- After the cut each aircraft may fly slower than planned (wind, battery sag): its arrival at waypoint k is
  late by `slow * (t_k - t_cut)` seconds, dwells keep their length. Nothing else changes, so the geometry of
  the routes (zones, contact positions) is unchanged and only timing rules can break.
- Policies decide what the aircraft do without the operator:
    continue : follow the plan blindly (zero messages).
    return   : every aircraft aborts and returns home at the cut: no post-cut point, no violation (safety floor).
    adjust   : late aircraft broadcast their delay to the aircraft within `range_m`; an aircraft that hears a
               later partner of one of its contacts hovers at the last waypoint before its action, so the
               crew keeps its relative timing.
- Score of a run = points of the contacts still served after the cut (rules R4, R9, R10 re-checked on the
  perturbed times, no separation R8 violation involving the contact's aircraft, energy and horizon respected)
  minus `cost` per message sent. `ceiling` is the same sum on the unperturbed plan.
"""
import math
import random
from collections import Counter
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Tuple

from fleetkit.energy import route_energy_wh
from fleetkit.geometry import dist3
from fleetkit.model import EFFECTOR, HOSTILE, SCOUT, UNKNOWN, Route, Scenario, Waypoint, parse_plan
from fleetkit.validator import separation_item, separation_violation, valid_observation

EPS = 1e-6


@dataclass(frozen=True)
class Comms:
    """Communication budget of the `adjust` policy."""

    range_m: float = 1000.0     # a broadcast is heard by aircraft closer than this at send time
    max_msgs: int = 3           # broadcasts per aircraft over the mission (rate budget)
    period_s: float = 30.0      # time between two broadcasts of the same aircraft
    loss_prob: float = 0.0      # probability that a receiver misses a broadcast
    latency_s: float = 1.0      # delay before a receiver can act on a broadcast
    cost: float = 1.0           # score cost of one message, in points
    threshold_s: float = 2.0    # an aircraft broadcasts when its delay at an action exceeds this


@dataclass(frozen=True)
class Disturbance:
    """The drift applied after the cut."""

    t_cut: float
    p_affected: float = 0.3     # share of aircraft that fly slower after the cut
    max_slow: float = 0.3       # their slowdown is uniform in (0, max_slow): 0.3 means 30 % longer legs


@dataclass
class RunResult:
    """Outcome of one run."""

    ceiling: float
    served: float = 0.0         # points of contacts still served (before message cost)
    msgs: int = 0
    violations: int = 0         # R8 pairs closer than d_sep after the perturbation
    cost: float = 0.0
    fails: Counter = field(default_factory=Counter)

    @property
    def score(self) -> float:
        """Points still served minus the message cost."""
        return self.served - self.cost * self.msgs

    @property
    def share(self) -> float:
        """Score as a share of the ceiling (1.0 means nothing lost)."""
        return self.score / self.ceiling if self.ceiling > 0 else 1.0


class World:
    """A plan plus the per-waypoint delays of every aircraft."""

    def __init__(self, scenario: Scenario, plan: dict, dist: Disturbance):
        routes, errors = parse_plan(plan)
        if routes is None or errors:
            raise ValueError("unusable plan: %s" % errors)
        self.scn = scenario
        self.dist = dist
        self.routes: Dict[str, Route] = routes
        self.aircraft = scenario.aircraft_by_id()
        self.contacts = scenario.contact_by_id()
        self.delay: Dict[str, List[float]] = {a: [0.0] * len(r.waypoints) for a, r in routes.items()}
        self.hold: Dict[str, List[float]] = {a: [0.0] * len(r.waypoints) for a, r in routes.items()}
        self.slow: Dict[str, float] = {a: 0.0 for a in routes}

    def disturb(self, rng: random.Random) -> None:
        """Draws which aircraft fly slower and applies it to their waypoint delays."""
        for aid in sorted(self.routes):
            if rng.random() < self.dist.p_affected:
                e = rng.uniform(0.0, self.dist.max_slow)
                self.slow[aid] = e
                self.delay[aid] = [e * max(0.0, w.t - self.dist.t_cut) for w in self.routes[aid].waypoints]

    def arrival(self, aid: str, k: int) -> float:
        """Actual arrival time at waypoint k."""
        return self.routes[aid].waypoints[k].t + self.delay[aid][k]

    def actual_route(self, aid: str) -> Route:
        """The route with the actual (delayed) arrival times."""
        wps = self.routes[aid].waypoints
        return Route(aid, [replace(w, t=w.t + self.delay[aid][k], dwell_s=w.dwell_s + self.hold[aid][k])
                           for k, w in enumerate(wps)])

    def position(self, aid: str, t: float) -> Tuple[float, float, float]:
        """Actual position of an aircraft at time t (home before its first waypoint, last waypoint after)."""
        wps = self.routes[aid].waypoints
        if not wps:
            return self.aircraft[aid].home
        first_t = self.arrival(aid, 0)
        if t <= first_t:
            return wps[0].pos
        for k in range(len(wps)):
            a_t = self.arrival(aid, k)
            d_t = a_t + wps[k].dwell_s + self.hold[aid][k]
            if a_t <= t <= d_t:
                return wps[k].pos
            if k + 1 < len(wps) and d_t < t < self.arrival(aid, k + 1):
                f = (t - d_t) / (self.arrival(aid, k + 1) - d_t)
                p, q = wps[k].pos, wps[k + 1].pos
                return (p[0] + f * (q[0] - p[0]), p[1] + f * (q[1] - p[1]), p[2] + f * (q[2] - p[2]))
        return wps[-1].pos

    def actions(self) -> Dict[str, List[Tuple[str, int, Waypoint]]]:
        """Planned actions by contact id: (aircraft, waypoint index, nominal waypoint)."""
        out: Dict[str, List[Tuple[str, int, Waypoint]]] = {}
        for aid, route in self.routes.items():
            for k, w in enumerate(route.waypoints):
                if w.action is None or w.target not in self.contacts:
                    continue
                if w.action == "observe" and not (self.aircraft[aid].type == SCOUT
                                                  and valid_observation(w, self.contacts[w.target], self.scn)):
                    continue
                out.setdefault(w.target, []).append((aid, k, w))
        return out


def _end(w: Waypoint, shift: float = 0.0) -> float:
    """End time of an action: observation spans its dwell, engagement is instantaneous."""
    return w.t + shift + (w.dwell_s if w.action == "observe" else 0.0)


def post_cut_contacts(world: World) -> List[str]:
    """Contacts with at least one planned action after the cut (their points are 'still to be served')."""
    out = []
    for cid, acts in world.actions().items():
        if max(_end(w) for _, _, w in acts) > world.dist.t_cut + EPS:
            out.append(cid)
    return out


def ceiling(world: World) -> float:
    """Points of the post-cut contacts on the unperturbed plan (the plan is valid, so all are served)."""
    return sum(world.contacts[c].points for c in post_cut_contacts(world)
               if world.contacts[c].cls in (HOSTILE, UNKNOWN))


def _lost_aircraft(world: World) -> set:
    """Aircraft that cannot reach their last action on their battery (the return leg is not charged)."""
    lost = set()
    for aid, route in world.routes.items():
        if not any(world.delay[aid]) and not any(world.hold[aid]):
            continue
        idx = [k for k, w in enumerate(route.waypoints) if w.action is not None]
        if not idx:
            continue
        prefix = world.actual_route(aid).waypoints[:idx[-1] + 1]
        if route_energy_wh(prefix, world.aircraft[aid]) > world.aircraft[aid].usable_wh + EPS:
            lost.add(aid)
    return lost


def _violating_aircraft(world: World) -> Tuple[set, int]:
    """Aircraft involved in an R8 violation after the perturbation, and the number of violating pairs.

    Only pairs with at least one changed route are checked: the unperturbed pairs come from a valid plan.
    """
    changed = [a for a in world.routes if any(world.delay[a]) or any(world.hold[a])]
    items = {}
    for aid in world.routes:
        item = separation_item(aid, world.actual_route(aid) if aid in changed else world.routes[aid],
                               world.aircraft[aid])
        if item is not None:
            items[aid] = item
    bad, pairs = set(), 0
    ids = sorted(items)
    cset = set(changed)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if a not in cset and b not in cset:
                continue
            if separation_violation(world.scn.rules, world.contacts, items[a], items[b]) is not None:
                bad.update((a, b))
                pairs += 1
    return bad, pairs


def contact_failure(world: World, c, times) -> Optional[str]:
    """Why a contact is no longer served with these actual action times, or None when it still is.

    `times` lists (aircraft, waypoint index, nominal waypoint, actual arrival time) for the contact's actions.
    Checks the horizon, the time window (R9), the synchronisation (R10) and the confirmation (R4).
    """
    scn, rules = world.scn, world.scn.rules
    if any(_end(w, t - w.t) > scn.horizon_s + EPS for _, _, w, t in times):
        return "horizon"
    lo, hi = c.window if c.window is not None else (-math.inf, math.inf)
    if any(t < lo - EPS or _end(w, t - w.t) > hi + EPS for _, _, w, t in times):
        return "window"
    if c.cls == UNKNOWN:
        return None
    eng = [t for _, _, w, t in times if w.action == "engage"]
    obs_end = [_end(w, t - w.t) for _, _, w, t in times if w.action == "observe"]
    if not eng or max(eng) - min(eng) > rules.sync_window_s + EPS:
        return "sync"
    if not obs_end or any(not any(o <= e - rules.confirm_margin_s + EPS for o in obs_end) for e in eng):
        return "confirm"
    return None


def score_run(world: World, msgs: int, cost: float) -> RunResult:
    """Scores the perturbed world: which post-cut contacts are still served, and at what message cost."""
    res = RunResult(ceiling=ceiling(world), msgs=msgs, cost=cost)
    lost = _lost_aircraft(world)
    unsafe, res.violations = _violating_aircraft(world)
    acts = world.actions()
    for cid in post_cut_contacts(world):
        c = world.contacts[cid]
        if c.cls not in (HOSTILE, UNKNOWN):
            continue
        members = acts[cid]
        who = {a for a, _, _ in members}
        if who & lost:
            res.fails["energy"] += 1
            continue
        if who & unsafe:
            res.fails["separation"] += 1
            continue
        fail = contact_failure(world, c, [(aid, k, w, w.t + world.delay[aid][k]) for aid, k, w in members])
        if fail:
            res.fails[fail] += 1
            continue
        res.served += c.points
    return res


def run_continue(world: World, comms: Optional[Comms] = None) -> RunResult:
    """Blind execution of the plan: no message."""
    return score_run(world, 0, comms.cost if comms else Comms().cost)


def run_return(world: World, comms: Optional[Comms] = None) -> RunResult:
    """Everyone aborts at the cut and returns home: safe by assumption, nothing more is served."""
    res = RunResult(ceiling=ceiling(world), cost=comms.cost if comms else Comms().cost)
    res.fails["aborted"] = len(post_cut_contacts(world))
    return res


def _late_alone(world: World, aid: str, acts) -> bool:
    """Tells whether this aircraft's own delay would break one of its contacts if everyone else were on time."""
    for cid, members in acts.items():
        if not any(x == aid for x, _, _ in members):
            continue
        times = [(x, k, w, w.t + (world.delay[x][k] if x == aid else 0.0)) for x, k, w in members]
        if contact_failure(world, world.contacts[cid], times):
            return True
    return False


def run_adjust(world: World, comms: Comms, rng: random.Random) -> RunResult:
    """Late aircraft broadcast their delay; crew mates that hear it hover to keep the crew in step.

    An aircraft only speaks when its own lateness would break one of its contacts (it knows the plan, so
    it can tell). A listener only waits when the contact would otherwise fail, at the last waypoint before
    its action, then flies the rest of its route as planned.
    """
    t_cut = world.dist.t_cut
    acts = world.actions()
    heard: Dict[str, List[Tuple[str, float]]] = {}      # receiver -> [(sender, time it can act on it)]
    msgs = 0
    for b in sorted(world.routes):
        if world.slow[b] <= 0.0 or not _late_alone(world, b, acts):
            continue
        wps = world.routes[b].waypoints
        last = max((_end(w, world.delay[b][k]) for k, w in enumerate(wps) if w.action), default=None)
        if last is None or last <= t_cut:
            continue
        got = set()
        for i in range(comms.max_msgs):
            t_send = t_cut + i * comms.period_s
            if t_send >= last:
                break
            msgs += 1
            pb = world.position(b, t_send)
            for m in sorted(world.routes):
                if m == b or m in got:
                    continue
                if dist3(pb, world.position(m, t_send)) <= comms.range_m and rng.random() >= comms.loss_prob:
                    got.add(m)
                    heard.setdefault(m, []).append((b, t_send + comms.latency_s))
    order = sorted(post_cut_contacts(world), key=lambda c: min(w.t for _, _, w in acts[c]))
    for cid in order:
        members = acts[cid]
        c = world.contacts[cid]
        if contact_failure(world, c, [(x, k, w, w.t + world.delay[x][k]) for x, k, w in members]) is None:
            continue                          # still fine as flown: nobody needs to wait
        for aid, k, _ in members:
            hears = [(b, t_rx) for b, t_rx in heard.get(aid, []) if any(b == x for x, _, _ in members)]
            if not hears:
                continue
            ref = max(world.delay[b][kb] for b, t_rx in hears for x, kb, _ in members if x == b)
            s = ref - world.delay[aid][k]
            if s <= EPS:
                continue
            t_rx = min(t for _, t in hears)
            j = next((i for i in range(len(world.delay[aid])) if world.arrival(aid, i) > t_rx), None)
            if j is None or j > k - 1:
                continue                      # the message came too late: no waypoint left to wait at
            world.hold[aid][j] += s           # wait in the air at that waypoint, then fly the rest as planned
            for i in range(j + 1, len(world.delay[aid])):
                world.delay[aid][i] += s
    return score_run(world, msgs, comms.cost)


def simulate(scenario: Scenario, plan: dict, dist: Disturbance, comms: Comms, policy: str, seed: int) -> RunResult:
    """Runs one policy on one disturbance draw (same draw for every policy given the same seed)."""
    world = World(scenario, plan, dist)
    rng = random.Random(seed)
    world.disturb(rng)
    if policy == "continue":
        return run_continue(world, comms)
    if policy == "return":
        return run_return(world, comms)
    if policy == "adjust":
        return run_adjust(world, comms, random.Random(seed * 7919 + 1))
    raise ValueError("unknown policy %r" % policy)

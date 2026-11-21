"""R8 separation (40 m in 3D between airborne aircraft). planner.py calls it; the scheduler is ON by default.

R8 is the main wall at L4: all aircraft start from one pad grid (pads 11.1 m apart at L4) and most rejected
candidates fail on separation near the pads (docs/ROADMAP.md §3, WS4 phase 1).

What `adjust` does (earliest R8-free departure on the WHOLE route, aircraft by aircraft):
- it parses the candidate routes of `extra` and checks them (full route, 3D, the official
  `separation_violation`) against every route already accepted and against each other;
- on a conflict it delays a take-off: waiting on the ground is free and not checked by R8. The delay jumps
  over the conflict interval (`fk.geometry.close_intervals`), doubling the step, then a bisection shortens it;
- effectors (a strike group) are scheduled in two steps: a shared delay clears the group from the routes
  already accepted and from the scout (so their strikes stay together, R10), then members that still conflict
  with each other (neighbouring pads, a few seconds apart) are delayed one by one, but never so that the
  strikes spread over more than the 20 s synchronisation window (R10, with a margin), nor past the strike
  window of the contact (R9) or the horizon;
- a scout route alone (an unknown contact, or a rebuilt tour) is delayed only when no hostile it already
  observes has been engaged (that engagement needs the observation 10 s earlier, R4) and never past a window;
- a spatial filter keeps only the accepted routes that come within d_sep of the candidate, so the checks stay
  cheap; a candidate that cannot be made free is left untouched (the caller's cheap checks reject it as before);
- the scheduler never rejects. The caller still runs the official validator on every accepted plan, so a bug
  here costs points, not validity; any exception here is swallowed for the same reason.

R10 guard (ON by default, PLANNER_R10_GUARD=0 turns it off), independent of the scheduler: the incremental
`_try` validates the touched routes alone, and R10 couples routes (a contact needs EXACTLY its effectors,
within 20 s). A candidate that engages a hostile already engaged by an accepted route is checked here against
those engagements together (counts by subtype, sync window) and rejected when the union would break R10. Such
a candidate is invalid for the official validator anyway, so rejecting it never loses a valid plan. Today the
planner serves each contact once per build, so this only fires for a second pass on a contact (a repair loop):
without it, that second pass is accepted and the whole build is invalid.

Scheduler ON by default (paired bench, deterministic mode, L4 seeds 0-19: +5.9% ± 0.9%, 1/20 worse, 0 invalid);
PLANNER_DECONFLICT=0 turns it off.
Python 3.9, standard library only; kit code from `fk`, never `fleetkit`.
"""
import params
from typing import Dict, List, Optional, Tuple

from fk.geometry import close_intervals, hdist, overlapping_pieces
from fk.model import CIVILIAN, EFFECTOR, FRIENDLY, HOSTILE, parse_plan
from fk.validator import separation_item, separation_violation, validate

ENABLED = params.DECONFLICT
R10_GUARD = params.R10_GUARD

MAX_STEPS = 12          # re-checks per search: each jumps over one conflict interval, doubling the step
REFINE_STEPS = 6        # bisection checks to shorten the delay found
MIN_STEP_S = 1.0        # smallest delay added per step
GRID_S = 0.1            # delays are rounded up to this grid
EPS_S = 0.5             # margin added after a conflict interval
MARGIN_S = 0.2          # kept free before a window closes / the horizon
SYNC_MARGIN_S = 0.5     # strikes of one group stay this far inside the synchronisation window

Item = tuple  # (aircraft id, pieces, start, end, engage target) from fk.validator.separation_item
Box = Tuple[float, float, float, float]


def _shifted(item: Item, delta: float) -> Item:
    aid, pieces, start, end, target = item
    if delta == 0.0:
        return item
    return (aid, [(a + delta, b + delta, p, q) for a, b, p, q in pieces], start + delta, end + delta, target)


def _box(item: Item, pad: float) -> Box:
    xs, ys = [], []
    for _a, _b, p, q in item[1]:
        xs += (p[0], q[0])
        ys += (p[1], q[1])
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def _overlap(a: Box, b: Box) -> bool:
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def _conflict_span(rules, a: Item, b: Item) -> Optional[Tuple[float, float]]:
    """First interval where the two routes are closer than d_sep (the exemption is ignored: only a step size)."""
    if min(a[3], b[3]) - max(a[2], b[2]) <= 1e-12:
        return None
    for pa, pb, lo, hi in overlapping_pieces(a[1], b[1]):
        bad = close_intervals(pa, pb, lo, hi, rules.d_sep_m)
        if bad is not None and bad[1] - bad[0] > 1e-6:
            return bad
    return None


def _other_item(planner, oid: str) -> Tuple[Optional[Item], Optional[Box]]:
    """Separation item and bounding box of an accepted route (cached on the planner)."""
    route = planner.routes[oid]
    cache = getattr(planner, "_dc_cache", None)
    if cache is None:
        cache = planner._dc_cache = {}
    cached = cache.get(oid)
    if cached is None or cached[0] is not route:
        parsed, _ = parse_plan({"seed": planner.sc.seed, "routes": [{"aircraft": oid, "waypoints": route}]})
        item = separation_item(oid, parsed[oid], planner.sc.aircraft_by_id()[oid])
        cached = (route, item, _box(item, planner.sc.rules.d_sep_m + 1.0) if item is not None else None)
        cache[oid] = cached
    return cached[1], cached[2]


def _hit(rules, contacts, item: Item, against: List[Item]):
    """Span of the first R8 violation of `item` against any of `against`, None when free."""
    for other in against:
        if separation_violation(rules, contacts, item, other) is not None:
            return _conflict_span(rules, item, other) or (item[2], item[2] + MIN_STEP_S)
    return None


def _find_delay(check, start: float, cap: float) -> Optional[float]:
    """Smallest delay >= start (<= cap) for which check(delay) is None (free). check returns a conflict span,
    or False when no delay can help."""
    delta, last_bad, free = start, start, None
    for k in range(MAX_STEPS + 1):
        found = check(delta)
        if found is None:
            free = delta
            break
        if found is False or delta >= cap:
            return None
        last_bad = delta
        delta = min(cap, delta + max(MIN_STEP_S * (2 ** k), found[1] - found[0] + EPS_S))
        if delta < cap:
            delta = float(int(delta / GRID_S + 0.999999)) * GRID_S
    if free is None:
        return None
    lo, hi = last_bad, free
    for _ in range(REFINE_STEPS):
        if hi - lo <= GRID_S * 5:
            break
        mid = float(int((lo + hi) / 2 / GRID_S)) * GRID_S
        if mid <= lo:
            break
        if check(mid) is None:
            hi = mid
        else:
            lo = mid
    return hi


def _cap(planner, route: List[dict]) -> float:
    """Largest delay that keeps one route inside its contact windows and the horizon."""
    cap = planner.sc.horizon_s - route[-1]["t"] - MARGIN_S
    for w in route:
        c = planner.contacts.get(w.get("target"))
        if c is None or c.window is None:
            continue
        if w.get("action") == "engage":
            cap = min(cap, c.window[1] - w["t"] - MARGIN_S)
        elif w.get("action") == "observe":
            cap = min(cap, c.window[1] - w["t"] - w.get("dwell_s", 0.0) - MARGIN_S)
    return cap


def _scout_may_shift(planner, aid: str) -> bool:
    """A scout that already observes an engaged hostile cannot be delayed (R4 needs the observation first)."""
    engaged = {r[-1].get("target") for r in planner.routes.values() if r and r[-1].get("action") == "engage"}
    for t in planner.tasks.get(aid, ()):
        cid = t["cid"] if isinstance(t, dict) else t.id
        c = planner.contacts.get(cid)
        if c is not None and c.cls == HOSTILE and cid in engaged:
            return False
    return True


def schedule(planner, extra: Dict[str, List[dict]]) -> Dict[str, float]:
    """Delay (s) per aircraft of `extra` that makes the candidate R8-free; {} if already free or no slot."""
    sc = planner.sc
    rules, contacts = sc.rules, planner.contacts
    aircraft = sc.aircraft_by_id()
    parsed, _ = parse_plan({"seed": sc.seed, "routes": [{"aircraft": a, "waypoints": w} for a, w in extra.items()]})
    if parsed is None:
        return {}
    items = {}
    for aid, route in parsed.items():
        it = separation_item(aid, route, aircraft[aid])
        if it is not None:
            items[aid] = it
    if not items:
        return {}
    # sorted lists, not sets: the first conflict found sets the delay, so the order must not depend on PYTHONHASHSEED
    effectors = sorted(a for a in items if aircraft[a].type == EFFECTOR)
    moving = effectors or sorted(a for a in items if _scout_may_shift(planner, a))
    if not moving:
        return {}
    fixed = {a: it for a, it in items.items() if a not in moving}
    # accepted routes that can come near the candidate (space only: a shift changes times, not places)
    boxes = {a: _box(it, rules.d_sep_m + 1.0) for a, it in items.items()}
    near, near_of = [], {a: [] for a in moving}
    for oid in planner.routes:
        if oid in extra:
            continue
        item, box = _other_item(planner, oid)
        if item is not None and any(_overlap(box, b) for b in boxes.values()):
            near.append(item)
            for a in moving:  # per aircraft, so it does not depend on the rest of the candidate
                if _overlap(box, boxes[a]):
                    near_of[a].append(item)
    memo = _memo(planner)
    replaced = tuple(sorted(a for a in extra if a in planner.routes))  # accepted routes left out of near_of
    keys = {a: (a, tuple(items[a][1]), replaced) for a in moving}

    def near_hit(aid, d):
        # the same effector route is re-scheduled for every scout option against the same accepted routes
        k = (keys[aid], d)
        if k not in memo:
            memo[k] = _hit(rules, contacts, _shifted(items[aid], d), near_of[aid])
        return memo[k]
    fixed_items = list(fixed.values())
    for f in fixed_items:                       # a fixed route in conflict with an accepted one: no delay helps
        if _hit(rules, contacts, f, near) is not None:
            return {}

    # step A: one shared delay clears the whole moving set from the accepted routes and the fixed ones
    def check_shared(d):
        for aid in moving:
            span = near_hit(aid, d) or _hit(rules, contacts, _shifted(items[aid], d), fixed_items)
            if span is not None:
                return span
        return None

    if check_shared(0.0) is None and not _intra_conflict(rules, contacts, items, moving, {}):
        return {}
    cap_shared = min(_cap(planner, extra[a]) for a in moving)
    shared = _find_delay(check_shared, 0.0, cap_shared)
    if shared is None:
        return {}
    delays = {a: shared for a in moving}

    # step B: members of the group that still conflict with each other are delayed one by one inside R10's window
    if len(moving) > 1 and _intra_conflict(rules, contacts, items, moving, delays):
        if not aircraft[moving[0]].type == EFFECTOR:
            return {}
        strikes = {a: extra[a][-1]["t"] for a in moving}
        window_end = min(strikes.values()) + shared + rules.sync_window_s - SYNC_MARGIN_S
        placed: List[Item] = []
        for aid in sorted(moving, key=lambda a: (items[a][2], a)):
            cap_i = min(_cap(planner, extra[aid]), window_end - strikes[aid])
            if cap_i < shared:
                return {}

            def check_one(d, aid=aid):
                return near_hit(aid, d) or _hit(rules, contacts, _shifted(items[aid], d), fixed_items + placed)

            d_i = _find_delay(check_one, shared, cap_i)
            if d_i is None:
                return {}
            delays[aid] = d_i
            placed.append(_shifted(items[aid], d_i))
        lo = min(strikes[a] + delays[a] for a in moving)
        hi = max(strikes[a] + delays[a] for a in moving)
        if hi - lo > rules.sync_window_s - SYNC_MARGIN_S + 1e-9:
            return {}
    return {a: d for a, d in delays.items() if d > 0.0}


def _memo(planner) -> dict:
    """Cache of near-route checks, valid while the accepted routes stay the same."""
    routes = tuple(planner.routes.items())
    cached = getattr(planner, "_dc_memo", None)
    if cached is None or len(cached[0]) != len(routes) or any(
            a[0] != b[0] or a[1] is not b[1] for a, b in zip(cached[0], routes)):
        cached = planner._dc_memo = (routes, {})  # holds the route objects, so identity checks stay sound
    return cached[1]


def _intra_conflict(rules, contacts, items, moving, delays) -> bool:
    shifted = [_shifted(items[a], delays.get(a, 0.0)) for a in sorted(moving)]
    for i in range(len(shifted)):
        for j in range(i + 1, len(shifted)):
            if separation_violation(rules, contacts, shifted[i], shifted[j]) is not None:
                return True
    return False


def adjust(planner, extra: Dict[str, List[dict]]) -> bool:
    """Called in FastPlanner._try before checking a candidate. Return False to reject it.

    `planner.routes` holds the routes already accepted (aircraft id -> waypoint dicts), `extra` the new or
    changed routes. The waypoints in `extra` are edited IN PLACE (the take-off and every later time of a route
    are shifted by that aircraft's delay): the caller keeps using that same dict when it accepts the candidate.
    Rejects only what the R10 guard proves invalid; otherwise the caller's own checks decide.
    """
    if R10_GUARD and planner is not None and extra:
        try:
            if not r10_ok(planner, extra):
                return False
        except Exception:  # noqa: BLE001  the guard must never cost the plan either
            pass
    if not ENABLED:
        return True
    try:
        if _hopeless(planner, extra):
            return True
        delays = schedule(planner, extra)
        if not delays:
            return True
        shifted = {a: [dict(w, t=w["t"] + delays.get(a, 0.0)) for w in route] for a, route in extra.items()}
        # a delay only fixes R8: if the shifted candidate still fails a cheap check, leave it to the caller
        sub = {"seed": planner.sc.seed, "routes": [{"aircraft": a, "waypoints": w} for a, w in shifted.items()]}
        if validate(planner.sc, sub) or not _confirmations_ok(planner, shifted):
            return True
        for aid, delta in delays.items():
            for w in extra[aid]:
                w["t"] += delta
    except Exception:  # noqa: BLE001  a bug here must never cost the plan
        pass
    return True


def _hopeless(planner, extra: Dict[str, List[dict]]) -> bool:
    """Cheap checks that no delay can fix: engaging a hostile too close to a friendly or a civilian (R7), or a
    rebuilt scout route that loses the confirmation of a hostile already engaged (R4)."""
    sc = planner.sc
    radius = sc.rules.collateral_radius_m
    for route in extra.values():
        w = route[-1]
        if w.get("action") != "engage":
            continue
        c = planner.contacts.get(w.get("target"))
        if c is None or c.cls != HOSTILE:
            continue
        for f in sc.contacts:
            if f.cls in (FRIENDLY, CIVILIAN) and hdist(c.pos, f.pos) < radius - 1e-6:
                return True
    return not _confirmations_ok(planner, extra)


def _confirmations_ok(planner, extra: Dict[str, List[dict]]) -> bool:
    """R4 for the hostiles a rebuilt scout route already observes: their engagements stay confirmed."""
    margin = planner.sc.rules.confirm_margin_s
    for sid, wps in extra.items():
        for t in planner.tasks.get(sid, ()):
            cid = t["cid"] if isinstance(t, dict) else t.id
            c = planner.contacts.get(cid)
            if c is None or c.cls != HOSTILE:
                continue
            engages = [r[-1]["t"] for oid, r in planner.routes.items()
                       if oid not in extra and r and r[-1].get("action") == "engage" and r[-1].get("target") == cid]
            ends = [w["t"] + w.get("dwell_s", 0.0) for w in wps if w.get("action") == "observe" and w.get("target") == cid]
            if any(not any(o <= e - margin + 1e-6 for o in ends) for e in engages):
                return False
    return True


def r10_ok(planner, extra: Dict[str, List[dict]]) -> bool:
    """R10 across tries: the candidate's engagements, together with the accepted engagements of the same hostile
    (routes not replaced by the candidate), must be exactly the effectors it needs, within the sync window."""
    mine: Dict[str, List[Tuple[str, float]]] = {}
    for aid, route in extra.items():
        if route and route[-1].get("action") == "engage":
            mine.setdefault(route[-1].get("target"), []).append((aid, route[-1]["t"]))
    if not mine:
        return True
    sc = planner.sc
    aircraft = getattr(planner, "aircraft", None) or sc.aircraft_by_id()
    contacts = getattr(planner, "contacts", None) or sc.contact_by_id()
    for cid, engs in mine.items():
        c = contacts.get(cid)
        if c is None or c.cls != HOSTILE:
            continue
        accepted = [(oid, r[-1]["t"]) for oid, r in planner.routes.items()
                    if oid not in extra and r and r[-1].get("action") == "engage" and r[-1].get("target") == cid]
        if not accepted:
            continue  # the candidate alone is checked by the caller (touched routes validated together)
        group = [(a, t) for a, t in engs + accepted if a in aircraft and aircraft[a].type == EFFECTOR]
        counts: Dict[str, int] = {}
        for aid, _t in group:
            sub = aircraft[aid].subtype or "?"
            counts[sub] = counts.get(sub, 0) + 1
        if counts != {k: v for k, v in c.needs.items() if v > 0}:
            return False
        times = [t for _a, t in group]
        if max(times) - min(times) > sc.rules.sync_window_s + 1e-9:
            return False
    return True

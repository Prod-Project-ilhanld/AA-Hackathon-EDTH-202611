"""R8 separation (40 m in 3D between airborne aircraft). planner.py calls it; the scheduler is ON by default.

R8 is the main wall at L4: all aircraft start from one pad grid (pads 11.1 m apart at L4) and most rejected
candidates fail on separation near the pads (docs/ROADMAP.md §3, WS4 phase 1).

What `adjust` does (earliest R8-free departure on the WHOLE route, aircraft by aircraft):
- it parses the candidate routes of `extra` and checks them (full route, 3D, the official
  `separation_violation`) against every route already accepted and against each other;
- on a conflict it delays a take-off: waiting on the ground is free and not checked by R8. The delay is the
  smallest one outside the forbidden delay intervals (`_pair_delays`, closed form per pair of pieces, a superset
  of the official conflicts), confirmed by one official check; the old step search (jumps over the conflict
  interval, then bisection) only takes over if that confirmation fails. Intervals against the accepted routes
  do not depend on the delay, so they are memoised until planner.routes changes (`_near_forbidden`);
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
import math
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
IV_MARGIN_S = 0.05      # added after a forbidden delay interval

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
        if item is not None:  # piece boxes for _forbidden; the entry keeps `item` alive, so its id is never reused
            boxes = getattr(planner, "_dc_boxes", None)
            if boxes is None:
                boxes = planner._dc_boxes = {}
            boxes[id(item)] = (item, _piece_boxes(item[1], 0.0))
    return cached[1], cached[2]


def _hit(rules, contacts, item: Item, against: List[Item]):
    """Span of the first R8 violation of `item` against any of `against`, None when free."""
    for other in against:
        if separation_violation(rules, contacts, item, other) is not None:
            return _conflict_span(rules, item, other) or (item[2], item[2] + MIN_STEP_S)
    return None


def _roots(a: float, b: float, c: float) -> List[float]:
    """Real roots of a x^2 + b x + c = 0."""
    if abs(a) < 1e-12:
        return [] if abs(b) < 1e-12 else [-c / b]
    disc = b * b - 4.0 * a * c
    if disc < 0.0:
        return []
    r = math.sqrt(disc)
    return [(-b - r) / (2.0 * a), (-b + r) / (2.0 * a)]


def _vel(t0: float, t1: float, p, q):
    if t1 - t0 <= 1e-12:
        return (0.0, 0.0, 0.0)
    k = 1.0 / (t1 - t0)
    return ((q[0] - p[0]) * k, (q[1] - p[1]) * k, (q[2] - p[2]) * k)


def _pair_delays(A, B, d: float) -> Optional[Tuple[float, float]]:
    """Delays x for which piece A, taking off x later, comes within d of piece B: an interval, or None.

    A is at A(u) for its own time u in [a0, a1], B at B(t) for t in [b0, b1]; delayed by x, A is at A(t - x) at
    time t. The set {(u, t): |A(u) - B(t)| <= d} is convex (an ellipse cut by a box), so x = t - u spans an
    interval whose ends lie at box corners, box edges cut by the ellipse, or ellipse points tangent to the
    lines t - u = const. Closed set and d >= the official limit: a superset of the official R8 conflicts."""
    a0, a1, P, P1 = A
    b0, b1, Q, Q1 = B
    va, vb = _vel(a0, a1, P, P1), _vel(b0, b1, Q, Q1)
    c = (P[0] - va[0] * a0 - Q[0] + vb[0] * b0, P[1] - va[1] * a0 - Q[1] + vb[1] * b0,
         P[2] - va[2] * a0 - Q[2] + vb[2] * b0)
    q11 = va[0] * va[0] + va[1] * va[1] + va[2] * va[2]
    q12 = -(va[0] * vb[0] + va[1] * vb[1] + va[2] * vb[2])
    q22 = vb[0] * vb[0] + vb[1] * vb[1] + vb[2] * vb[2]
    l1 = c[0] * va[0] + c[1] * va[1] + c[2] * va[2]
    l2 = -(c[0] * vb[0] + c[1] * vb[1] + c[2] * vb[2])
    k0 = c[0] * c[0] + c[1] * c[1] + c[2] * c[2] - d * d
    xs = []
    for u in (a0, a1):                                   # edges u = a0, a1 (and their corners)
        cu = q11 * u * u + 2.0 * l1 * u + k0
        for t in (b0, b1):
            if cu + 2.0 * q12 * u * t + q22 * t * t + 2.0 * l2 * t <= 0.0:
                xs.append(t - u)
        for t in _roots(q22, 2.0 * (q12 * u + l2), cu):
            if b0 - 1e-9 <= t <= b1 + 1e-9:
                xs.append(t - u)
    for t in (b0, b1):                                   # edges t = b0, b1
        for u in _roots(q11, 2.0 * (q12 * t + l1), q22 * t * t + 2.0 * l2 * t + k0):
            if a0 - 1e-9 <= u <= a1 + 1e-9:
                xs.append(t - u)
    al, be, ga = q11 + q12, q12 + q22, l1 + l2           # g_u + g_t = 0: tangent to the lines t - u = const
    if abs(be) >= abs(al) and abs(be) > 1e-12:           # on that line t = m u + n
        m, n = -al / be, -ga / be
        for u in _roots(q11 + 2.0 * q12 * m + q22 * m * m, 2.0 * (q12 * n + q22 * m * n + l1 + l2 * m),
                        q22 * n * n + 2.0 * l2 * n + k0):
            t = m * u + n
            if a0 - 1e-9 <= u <= a1 + 1e-9 and b0 - 1e-9 <= t <= b1 + 1e-9:
                xs.append(t - u)
    elif abs(al) > 1e-12:                                # u = m t + n
        m, n = -be / al, -ga / al
        for t in _roots(q11 * m * m + 2.0 * q12 * m + q22, 2.0 * (q11 * m * n + q12 * n + l1 * m + l2),
                        q11 * n * n + 2.0 * l1 * n + k0):
            u = m * t + n
            if a0 - 1e-9 <= u <= a1 + 1e-9 and b0 - 1e-9 <= t <= b1 + 1e-9:
                xs.append(t - u)
    return (min(xs), max(xs)) if xs else None


def _piece_boxes(pieces, pad: float) -> List[Box]:
    return [(min(p[0], q[0]) - pad, min(p[1], q[1]) - pad, min(p[2], q[2]) - pad,
             max(p[0], q[0]) + pad, max(p[1], q[1]) + pad, max(p[2], q[2]) + pad) for _a, _b, p, q in pieces]


def _forbidden(planner, item: Item, others: List[Item], d: float, lo: float, hi: float) -> List[Tuple[float, float]]:
    """Delay intervals of `item` (touching [lo, hi]) that may break R8 against one of `others`."""
    cache = getattr(planner, "_dc_boxes", {})
    pa = item[1]
    ba = _piece_boxes(pa, d)
    out = []
    for o in others:
        if o[2] > item[3] + hi or o[3] < item[2] + lo:   # never airborne together for a delay in [lo, hi]
            continue
        got = cache.get(id(o))
        bb = got[1] if got is not None and got[0] is o else _piece_boxes(o[1], 0.0)
        for i, A in enumerate(pa):
            x = ba[i]
            for j, B in enumerate(o[1]):
                if B[1] - A[0] < lo or B[0] - A[1] > hi:
                    continue
                y = bb[j]
                if x[0] > y[3] or y[0] > x[3] or x[1] > y[4] or y[1] > x[4] or x[2] > y[5] or y[2] > x[5]:
                    continue
                iv = _pair_delays(A, B, d)
                if iv is not None and iv[1] >= lo and iv[0] <= hi:
                    out.append(iv)
    return out


def _near_forbidden(planner, aid: str, item: Item, near: List[Item], extra) -> List[Tuple[float, float]]:
    """_forbidden against the accepted routes, over every delay up to the horizon, memoised: the planner tries the
    same effector route for many scout options against the same accepted plan. The memo is dropped whenever
    planner.routes changes (it holds the route objects, so the identity check is safe)."""
    memo = getattr(planner, "_dc_memo", None)
    routes = planner.routes
    if (memo is None or len(memo[0]) != len(routes)
            or any(memo[0].get(k) is not v for k, v in routes.items())):
        memo = planner._dc_memo = (dict(routes), {})
    key = (aid, tuple(item[1]), tuple(sorted(k for k in extra if k in routes)))
    got = memo[1].get(key)
    if got is None:
        got = memo[1][key] = _forbidden(planner, item, near, planner.sc.rules.d_sep_m, 0.0, planner.sc.horizon_s)
    return got


def _covers(intervals, x: float) -> bool:
    return any(a <= x <= b for a, b in intervals)


def _first_free(intervals, start: float, cap: float, check) -> Optional[float]:
    """Smallest delay >= start (<= cap) outside every interval, confirmed by the official check (`check` returns
    None when free); the step search takes over in the rare case the confirmation fails."""
    cur = start
    for a, b in sorted(intervals):
        if a > cur:
            break
        cur = max(cur, b + IV_MARGIN_S)
    if cur > cap:
        return None
    if check(cur) is None:
        return cur
    return _find_delay(check, cur, cap)


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
    boxes = [_box(it, rules.d_sep_m + 1.0) for it in items.values()]
    near = []
    for oid in planner.routes:
        if oid in extra:
            continue
        item, box = _other_item(planner, oid)
        if item is not None and any(_overlap(box, b) for b in boxes):
            near.append(item)
    fixed_items = list(fixed.values())
    d_iv = rules.d_sep_m
    for f in fixed_items:                       # a fixed route in conflict with an accepted one: no delay helps
        if _covers(_forbidden(planner, f, near, d_iv, 0.0, 0.0), 0.0) and _hit(rules, contacts, f, near) is not None:
            return {}

    # step A: one shared delay clears the whole moving set from the accepted routes and the fixed ones
    def check_shared(d):
        for aid in moving:
            span = _hit(rules, contacts, _shifted(items[aid], d), near + fixed_items)
            if span is not None:
                return span
        return None

    cap_shared = min(_cap(planner, extra[a]) for a in moving)
    ivs: List[Tuple[float, float]] = []
    for aid in moving:
        ivs += _near_forbidden(planner, aid, items[aid], near, extra)
        ivs += _forbidden(planner, items[aid], fixed_items, d_iv, 0.0, max(0.0, cap_shared))
    free0 = not _covers(ivs, 0.0) or check_shared(0.0) is None
    if free0 and not _intra_conflict(rules, contacts, items, moving, {}):
        return {}
    shared = 0.0 if free0 else _first_free(ivs, 0.0, cap_shared, check_shared)
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
                return _hit(rules, contacts, _shifted(items[aid], d), near + fixed_items + placed)

            d_i = _first_free(_near_forbidden(planner, aid, items[aid], near, extra)
                              + _forbidden(planner, items[aid], fixed_items + placed, d_iv, shared, cap_i),
                              shared, cap_i, check_one)
            if d_i is None:
                return {}
            delays[aid] = d_i
            placed.append(_shifted(items[aid], d_i))
        lo = min(strikes[a] + delays[a] for a in moving)
        hi = max(strikes[a] + delays[a] for a in moving)
        if hi - lo > rules.sync_window_s - SYNC_MARGIN_S + 1e-9:
            return {}
    return {a: d for a, d in delays.items() if d > 0.0}


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

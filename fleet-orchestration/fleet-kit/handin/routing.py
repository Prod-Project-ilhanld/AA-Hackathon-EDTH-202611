"""3D minimum-energy routing, visibility-graph 2D avoidance, 3D overflight arbitrage,
and memoized fast cost API for fleet allocation.

Standard library + fleetkit only.
"""
from __future__ import annotations

import heapq
import math
from typing import Dict, List, Optional, Sequence, Tuple

from fleetkit.energy import J_PER_WH, best_range_speed, leg_energy_wh, route_energy_wh
from fleetkit.geometry import EPS, INF, dist3, hdist, segment_enters_cylinder
from fleetkit.model import (
    CIVILIAN,
    FRIENDLY,
    Aircraft,
    Contact,
    Scenario,
    Waypoint,
)

Point = Tuple[float, float, float]
Point2D = Tuple[float, float]
# (cx, cy, radius_m, top_m, id)
Cylinder = Tuple[float, float, float, float, str]

# Safety margins to survive 3-decimal JSON rounding and EPS=1e-6 checks.
SAFE_MARGIN_R = 1.5
SAFE_MARGIN_Z = 0.5
SAFE_MARGIN_T = 0.05
SAFE_OBS_MARGIN = 2.0
SAFE_ENG_MARGIN = 1.0
MAX_SPEED_FRAC = 0.995
NGON_SIDES = 12
_NGON_SCALE = 1.0 / math.cos(math.pi / NGON_SIDES)

ALTITUDE_LAYERS = (30.0, 72.0, 114.0, 148.0)


def extract_cylinders(scenario: Scenario) -> List[Cylinder]:
    """Extracts all exclusion cylinders: no-fly zones and friendly/civilian protected areas."""
    cyls: List[Cylinder] = [
        (z.center[0], z.center[1], z.radius_m, z.top_m, z.id)
        for z in scenario.zones
    ]
    pr = scenario.rules.protect_radius_m
    for c in scenario.contacts:
        if c.cls in (FRIENDLY, CIVILIAN):
            cyls.append((c.pos[0], c.pos[1], pr, INF, c.id))
    return cyls


def _segment_hits_circle_2d(
    ax: float, ay: float, bx: float, by: float, cx: float, cy: float, r: float
) -> bool:
    """Fast closed-form 2D segment-circle interior intersection check."""
    dx = bx - ax
    dy = by - ay
    fx = ax - cx
    fy = ay - cy
    a = dx * dx + dy * dy
    r2 = r * r
    c = fx * fx + fy * fy - r2
    if a < 1e-12:
        return c < -EPS
    b = 2.0 * (fx * dx + fy * dy)
    disc = b * b - 4.0 * a * c
    if disc <= 0.0:
        return False
    root = math.sqrt(disc)
    inv2a = 0.5 / a
    lo = (-b - root) * inv2a
    hi = (-b + root) * inv2a
    if lo < 0.0:
        lo = 0.0
    if hi > 1.0:
        hi = 1.0
    return hi - lo > 1e-9


def _segment_clear_2d(
    ax: float, ay: float, bx: float, by: float, active_cyls: Sequence[Cylinder]
) -> bool:
    """Returns True iff the 2D segment avoids all active cylinders with SAFE_MARGIN_R."""
    for cx, cy, r, _, _ in active_cyls:
        if _segment_hits_circle_2d(ax, ay, bx, by, cx, cy, r + SAFE_MARGIN_R):
            return False
    return True


def _segment_clear_3d(p0: Point, p1: Point, cylinders: Sequence[Cylinder]) -> bool:
    """Returns True iff the 3D segment avoids all cylinders with safety margins."""
    for cx, cy, r, top, _ in cylinders:
        top_safe = top if math.isinf(top) else top + SAFE_MARGIN_Z * 0.5
        if segment_enters_cylinder(p0, p1, (cx, cy), r + SAFE_MARGIN_R, top_safe):
            return False
    return True


def _point_outside_all(x: float, y: float, active_cyls: Sequence[Cylinder]) -> bool:
    """Returns True iff (x, y) is outside all active cylinders (with margin)."""
    for cx, cy, r, _, _ in active_cyls:
        rm = r + SAFE_MARGIN_R * 0.95
        dx = x - cx
        dy = y - cy
        if dx * dx + dy * dy < rm * rm:
            return False
    return True


def _tangent_points(
    px: float, py: float, cx: float, cy: float, r: float
) -> List[Point2D]:
    """Exact tangent points from (px, py) to circle (cx, cy, r), pushed slightly outside."""
    dx = px - cx
    dy = py - cy
    d2 = dx * dx + dy * dy
    if d2 <= r * r * 1.0001:
        return []
    d = math.sqrt(d2)
    base_ang = math.atan2(dy, dx)
    alpha = math.acos(min(1.0, max(-1.0, r / d)))
    # Push slightly outside r so chords near the tangent stay outside r.
    r_out = r * 1.005 + 0.15
    return [
        (cx + r_out * math.cos(base_ang + alpha), cy + r_out * math.sin(base_ang + alpha)),
        (cx + r_out * math.cos(base_ang - alpha), cy + r_out * math.sin(base_ang - alpha)),
    ]


def _smooth_2d_path(
    path: List[Point2D], active_cyls: Sequence[Cylinder]
) -> List[Point2D]:
    """String-pulling shortcut pass on a 2D polyline."""
    if len(path) <= 2:
        return path
    out = [path[0]]
    i = 0
    n = len(path)
    while i < n - 1:
        best = i + 1
        for j in range(n - 1, i + 1, -1):
            if _segment_clear_2d(path[i][0], path[i][1], path[j][0], path[j][1], active_cyls):
                best = j
                break
        out.append(path[best])
        i = best
    return out


def _astar_2d(
    start_xy: Point2D,
    goal_xy: Point2D,
    active_cyls: Sequence[Cylinder],
    subset_cyls: Sequence[Cylinder],
) -> Optional[List[Point2D]]:
    """Lazy A* over exact tangent points + circumscribed 12-gon vertices."""
    nodes: List[Point2D] = [start_xy, goal_xy]
    for cx, cy, r, _, _ in subset_cyls:
        r_tan = r + SAFE_MARGIN_R + 0.2
        for tp in _tangent_points(start_xy[0], start_xy[1], cx, cy, r_tan):
            if _point_outside_all(tp[0], tp[1], active_cyls):
                nodes.append(tp)
        for tp in _tangent_points(goal_xy[0], goal_xy[1], cx, cy, r_tan):
            if _point_outside_all(tp[0], tp[1], active_cyls):
                nodes.append(tp)
        r_poly = (r + SAFE_MARGIN_R) * _NGON_SCALE + 0.25
        for k in range(NGON_SIDES):
            ang = 2.0 * math.pi * k / NGON_SIDES
            vx = cx + r_poly * math.cos(ang)
            vy = cy + r_poly * math.sin(ang)
            if _point_outside_all(vx, vy, active_cyls):
                nodes.append((vx, vy))

    n = len(nodes)
    gx, gy = goal_xy
    h_vals = [math.hypot(nx - gx, ny - gy) for nx, ny in nodes]
    g_score = [INF] * n
    g_score[0] = 0.0
    parent = [-1] * n
    closed = [False] * n
    pq: List[Tuple[float, float, int]] = [(h_vals[0], 0.0, 0)]

    while pq:
        _, gu, u = heapq.heappop(pq)
        if closed[u]:
            continue
        if u == 1:
            path = []
            cur = 1
            while cur != -1:
                path.append(nodes[cur])
                cur = parent[cur]
            path.reverse()
            return _smooth_2d_path(path, active_cyls)
        closed[u] = True
        ux, uy = nodes[u]

        # Always check direct visibility to goal first.
        d_goal = h_vals[u]
        if gu + d_goal < g_score[1]:
            if _segment_clear_2d(ux, uy, gx, gy, active_cyls):
                g_score[1] = gu + d_goal
                parent[1] = u
                heapq.heappush(pq, (g_score[1], g_score[1], 1))

        best_goal = g_score[1]
        for v in range(2, n):
            if closed[v]:
                continue
            vx, vy = nodes[v]
            dv = math.hypot(vx - ux, vy - uy)
            ng = gu + dv
            if ng >= g_score[v] or ng + h_vals[v] >= best_goal:
                continue
            if _segment_clear_2d(ux, uy, vx, vy, active_cyls):
                g_score[v] = ng
                parent[v] = u
                heapq.heappush(pq, (ng + h_vals[v], ng, v))

    return None


def shortest_2d_path(
    start_xy: Point2D,
    goal_xy: Point2D,
    z_flight: float,
    cylinders: Sequence[Cylinder],
) -> Optional[List[Point2D]]:
    """Computes the shortest 2D obstacle-free path at altitude `z_flight`.

    Uses a fast direct-line check, then lazy A* starting from only the blocking
    cylinders (typically 1-3) before expanding to the corridor or full active set.
    """
    active = [c for c in cylinders if z_flight < c[3] + SAFE_MARGIN_Z * 0.5]
    if not active:
        return [start_xy, goal_xy]

    blocking = [
        c for c in active
        if _segment_hits_circle_2d(
            start_xy[0], start_xy[1], goal_xy[0], goal_xy[1],
            c[0], c[1], c[2] + SAFE_MARGIN_R,
        )
    ]
    if not blocking:
        return [start_xy, goal_xy]

    # Fast tier 1: only blocking cylinders (typically 1-3 -> ~20-40 nodes, < 0.2 ms).
    if len(blocking) < len(active):
        res = _astar_2d(start_xy, goal_xy, active, blocking)
        if res is not None:
            return res

    # Tier 2: blocking cylinders + nearby neighbors in corridor.
    mx = 0.5 * (start_xy[0] + goal_xy[0])
    my = 0.5 * (start_xy[1] + goal_xy[1])
    span = math.hypot(goal_xy[0] - start_xy[0], goal_xy[1] - start_xy[1])
    corridor = max(0.65 * span + 350.0, 800.0)
    subset = [
        c for c in active
        if math.hypot(c[0] - mx, c[1] - my) <= corridor + c[2]
    ]
    if subset and len(subset) < len(active):
        res = _astar_2d(start_xy, goal_xy, active, subset)
        if res is not None:
            return res
    return _astar_2d(start_xy, goal_xy, active, active)


def _optimal_leg_time_energy(
    p0: Point, p1: Point, aircraft: Aircraft, max_duration: Optional[float] = None
) -> Optional[Tuple[float, float]]:
    """Returns (duration_s, energy_wh) for a single straight 3D leg."""
    dh = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    dz = p1[2] - p0[2]
    v_h_max = MAX_SPEED_FRAC * aircraft.v_h_mps
    t_h_min = dh / v_h_max if dh > 0.0 else 0.0
    t_z_min = (dz / (MAX_SPEED_FRAC * aircraft.v_up_mps)) if dz > 0.0 else (-dz / (MAX_SPEED_FRAC * aircraft.v_down_mps))
    d_min = max(t_h_min, t_z_min) + SAFE_MARGIN_T

    v_opt = min(best_range_speed(aircraft.power), v_h_max)
    d_opt = max(d_min, (dh / v_opt + SAFE_MARGIN_T) if dh > 0.0 else d_min)

    if max_duration is not None:
        if max_duration < d_min:
            return None
        d = min(d_opt, max_duration)
    else:
        d = d_opt

    power = aircraft.power
    v = dh / d if d > 0.0 else 0.0
    cruise_wh = (power.p0_w + power.k_v * v * v) * d / J_PER_WH
    climb_wh = power.e_climb_wh_per_m * max(0.0, dz)
    return d, cruise_wh + climb_wh


def _polyline_time_energy(
    pts: Sequence[Point],
    aircraft: Aircraft,
    max_duration: Optional[float] = None,
) -> Optional[Tuple[List[float], float, float]]:
    """Computes per-leg durations, total duration, and total energy for a 3D polyline.

    If `max_duration` is tighter than the v*-optimal total time, proportionally
    accelerates horizontal legs up to `MAX_SPEED_FRAC * v_h_mps`.
    """
    n_legs = len(pts) - 1
    if n_legs <= 0:
        return [], 0.0, 0.0

    v_h_max = MAX_SPEED_FRAC * aircraft.v_h_mps
    v_opt = min(best_range_speed(aircraft.power), v_h_max)
    power = aircraft.power

    d_mins: List[float] = []
    d_opts: List[float] = []
    dhs: List[float] = []
    dzs: List[float] = []

    for k in range(n_legs):
        p0, p1 = pts[k], pts[k + 1]
        dh = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        dz = p1[2] - p0[2]
        t_h = dh / v_h_max if dh > 0.0 else 0.0
        t_z = (dz / (MAX_SPEED_FRAC * aircraft.v_up_mps)) if dz > 0.0 else (-dz / (MAX_SPEED_FRAC * aircraft.v_down_mps))
        dm = max(t_h, t_z) + SAFE_MARGIN_T
        do = max(dm, (dh / v_opt + SAFE_MARGIN_T) if dh > 0.0 else dm)
        d_mins.append(dm)
        d_opts.append(do)
        dhs.append(dh)
        dzs.append(dz)

    tot_min = sum(d_mins)
    tot_opt = sum(d_opts)
    if max_duration is not None and max_duration < tot_min:
        return None

    if max_duration is None or max_duration >= tot_opt:
        durs = d_opts
    else:
        # Allocate available slack above d_mins proportionally to (d_opts - d_mins).
        slack_avail = max_duration - tot_min
        slack_opt = tot_opt - tot_min
        ratio = slack_avail / slack_opt if slack_opt > 1e-9 else 0.0
        durs = [d_mins[k] + ratio * (d_opts[k] - d_mins[k]) for k in range(n_legs)]

    total_e = 0.0
    for k in range(n_legs):
        d = durs[k]
        v = dhs[k] / d if d > 0.0 else 0.0
        total_e += (power.p0_w + power.k_v * v * v) * d / J_PER_WH
        if dzs[k] > 0.0:
            total_e += power.e_climb_wh_per_m * dzs[k]
    return durs, sum(durs), total_e


def _entry_exit_params(
    ax: float, ay: float, bx: float, by: float, cx: float, cy: float, r: float
) -> Optional[Tuple[float, float]]:
    """Returns (s_enter, s_exit) in [0, 1] where 2D segment intersects circle (cx, cy, r)."""
    dx = bx - ax
    dy = by - ay
    fx = ax - cx
    fy = ay - cy
    a = dx * dx + dy * dy
    c = fx * fx + fy * fy - r * r
    if a < 1e-12:
        return (0.0, 1.0) if c < 0.0 else None
    b = 2.0 * (fx * dx + fy * dy)
    disc = b * b - 4.0 * a * c
    if disc <= 0.0:
        return None
    root = math.sqrt(disc)
    lo = max((-b - root) / (2.0 * a), 0.0)
    hi = min((-b + root) / (2.0 * a), 1.0)
    if hi - lo <= 1e-9:
        return None
    return (lo, hi)


def _build_3d_from_2d(
    p_start: Point, p_end: Point, path_2d: Sequence[Point2D], z_cruise: float
) -> List[Point]:
    """Lifts a 2D path to 3D using `z_cruise` for all intermediate waypoints."""
    if len(path_2d) <= 2:
        return [p_start, p_end]
    pts: List[Point] = [p_start]
    for x, y in path_2d[1:-1]:
        pts.append((x, y, z_cruise))
    pts.append(p_end)
    return pts


def _verify_3d_polyline(pts: Sequence[Point], cylinders: Sequence[Cylinder]) -> bool:
    for k in range(len(pts) - 1):
        if not _segment_clear_3d(pts[k], pts[k + 1], cylinders):
            return False
    return True


def optimal_leg_3d(
    p_start: Point,
    p_end: Point,
    aircraft: Aircraft,
    scenario: Scenario,
    max_duration: Optional[float] = None,
    engine: Optional["RoutingEngine"] = None,
    z_cruise: Optional[float] = None,
) -> Optional[Tuple[List[Point], float, float]]:
    """Computes the minimum-energy 3D leg between `p_start` and `p_end`.

    Arbitrates between:
      1. Direct 3D segment (if clear of all cylinders).
      2. 2D visibility-graph detour at `z_base`.
      3. 3D overflight at `top_m + SAFE_MARGIN_Z` over climbable cylinders.

    Returns:
        `(waypoints_3d, duration_s, energy_wh)` or `None` if infeasible.
    """
    cyls = engine.cylinders if engine is not None else extract_cylinders(scenario)
    rules = scenario.rules

    # Fast path: direct 3D segment is clear!
    if _segment_clear_3d(p_start, p_end, cyls):
        res = _polyline_time_energy([p_start, p_end], aircraft, max_duration)
        if res is not None:
            return [p_start, p_end], res[1], res[2]
        return None

    z_base = z_cruise if z_cruise is not None else max(p_start[2], p_end[2], rules.z_min_m)
    z_base = max(rules.z_min_m, min(rules.z_max_m, z_base))

    best: Optional[Tuple[List[Point], float, float]] = None

    def _consider(pts: List[Point]) -> None:
        nonlocal best
        # Ensure intermediate waypoints obey R2 altitude band.
        for k in range(1, len(pts) - 1):
            if pts[k][2] < rules.z_min_m - 1e-6 or pts[k][2] > rules.z_max_m + 1e-6:
                return
        if not _verify_3d_polyline(pts, cyls):
            return
        res = _polyline_time_energy(pts, aircraft, max_duration)
        if res is None:
            return
        _, dur, ene = res
        if best is None or ene < best[2] - 1e-9:
            best = (pts, dur, ene)

    # Candidate 1: 2D detour at z_base (check also if p_start.z or p_end.z < z_base).
    path_2d = (
        engine.shortest_2d_cached(p_start[:2], p_end[:2], z_base)
        if engine is not None
        else shortest_2d_path(p_start[:2], p_end[:2], z_base, cyls)
    )
    if path_2d is not None:
        pts_2d = _build_3d_from_2d(p_start, p_end, path_2d, z_base)
        _consider(pts_2d)
        # If first or last segment clips a cylinder due to low start/end z, add climb/descent shoulder.
        if best is None and (p_start[2] < z_base - 0.1 or p_end[2] < z_base - 0.1):
            pts_sh: List[Point] = [p_start]
            if p_start[2] < z_base - 0.1:
                pts_sh.append((p_start[0], p_start[1], z_base))
            for x, y in path_2d[1:-1]:
                pts_sh.append((x, y, z_base))
            if p_end[2] < z_base - 0.1:
                pts_sh.append((p_end[0], p_end[1], z_base))
            pts_sh.append(p_end)
            _consider(pts_sh)

    # Candidate 2: 3D overflight over finite-ceiling blocking cylinders.
    blocking_tops: List[float] = []
    has_inf_block = False
    t_enter_min = 1.0
    t_exit_max = 0.0
    for cx, cy, r, top, _ in cyls:
        iv = _entry_exit_params(
            p_start[0], p_start[1], p_end[0], p_end[1], cx, cy, r + SAFE_MARGIN_R
        )
        if iv is None:
            continue
        if math.isinf(top):
            has_inf_block = True
        else:
            blocking_tops.append(top)
            if iv[0] < t_enter_min:
                t_enter_min = iv[0]
            if iv[1] > t_exit_max:
                t_exit_max = iv[1]

    if blocking_tops:
        z_over = max(z_base, max(blocking_tops) + SAFE_MARGIN_Z + 0.5)
        if z_over <= rules.z_max_m:
            if not has_inf_block:
                # Straight horizontal overflight with climb before entry & descent after exit.
                dx = p_end[0] - p_start[0]
                dy = p_end[1] - p_start[1]
                s1 = max(0.0, t_enter_min - 0.02)
                s2 = min(1.0, t_exit_max + 0.02)
                pts_over: List[Point] = [p_start]
                if s1 > 1e-4:
                    pts_over.append((p_start[0] + s1 * dx, p_start[1] + s1 * dy, z_over))
                else:
                    pts_over.append((p_start[0], p_start[1], z_over))
                if s2 < 1.0 - 1e-4 and s2 > s1 + 1e-4:
                    pts_over.append((p_start[0] + s2 * dx, p_start[1] + s2 * dy, z_over))
                elif p_end[2] < z_over - 0.1:
                    pts_over.append((p_end[0], p_end[1], z_over))
                pts_over.append(p_end)
                _consider(pts_over)
            else:
                # Overfly finite zones while routing around INF cylinders at z_over.
                path_over = (
                    engine.shortest_2d_cached(p_start[:2], p_end[:2], z_over)
                    if engine is not None
                    else shortest_2d_path(p_start[:2], p_end[:2], z_over, cyls)
                )
                if path_over is not None:
                    pts_over = _build_3d_from_2d(p_start, p_end, path_over, z_over)
                    _consider(pts_over)
                    if best is None or best[2] > 0:
                        pts_sh2: List[Point] = [p_start]
                        if p_start[2] < z_over - 0.1:
                            pts_sh2.append((p_start[0], p_start[1], z_over))
                        for x, y in path_over[1:-1]:
                            pts_sh2.append((x, y, z_over))
                        if p_end[2] < z_over - 0.1:
                            pts_sh2.append((p_end[0], p_end[1], z_over))
                        pts_sh2.append(p_end)
                        _consider(pts_sh2)

    return best


class RoutingEngine:
    """Per-scenario routing engine with aggressive memoization for O(1) cost queries."""

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.rules = scenario.rules
        self.aircraft_by_id: Dict[str, Aircraft] = scenario.aircraft_by_id()
        self.cylinders: List[Cylinder] = extract_cylinders(scenario)
        self._cache_2d: Dict[Tuple[int, int, int, int, int], Optional[List[Point2D]]] = {}
        self._cache_leg: Dict[Tuple[str, int, int, int, int, int, int, int], Optional[Tuple[List[Point], float, float]]] = {}
        self._cache_cost: Dict[Tuple[str, int, int, int, int, int, int, int], Tuple[float, float]] = {}

    @staticmethod
    def _q(v: float) -> int:
        return int(round(v * 2.0))  # 0.5 m quantization

    def shortest_2d_cached(
        self, start_xy: Point2D, goal_xy: Point2D, z_flight: float
    ) -> Optional[List[Point2D]]:
        key = (
            self._q(start_xy[0]),
            self._q(start_xy[1]),
            self._q(goal_xy[0]),
            self._q(goal_xy[1]),
            int(round(z_flight)),
        )
        if key in self._cache_2d:
            cached = self._cache_2d[key]
            if cached is None:
                return None
            if len(cached) == 2:
                return [start_xy, goal_xy]
            return [start_xy] + cached[1:-1] + [goal_xy]
        path = shortest_2d_path(start_xy, goal_xy, z_flight, self.cylinders)
        self._cache_2d[key] = path
        return path

    def optimal_leg(
        self,
        p_start: Point,
        p_end: Point,
        aircraft: Aircraft,
        max_duration: Optional[float] = None,
        z_cruise: Optional[float] = None,
    ) -> Optional[Tuple[List[Point], float, float]]:
        if max_duration is None:
            zc_key = -1 if z_cruise is None else int(round(z_cruise))
            key = (
                aircraft.id,
                self._q(p_start[0]),
                self._q(p_start[1]),
                self._q(p_start[2]),
                self._q(p_end[0]),
                self._q(p_end[1]),
                self._q(p_end[2]),
                zc_key,
            )
            if key in self._cache_leg:
                cached = self._cache_leg[key]
                if cached is None:
                    return None
                pts, dur, ene = cached
                if len(pts) == 2:
                    return [p_start, p_end], dur, ene
                return [p_start] + pts[1:-1] + [p_end], dur, ene
            res = optimal_leg_3d(
                p_start, p_end, aircraft, self.scenario,
                max_duration=None, engine=self, z_cruise=z_cruise,
            )
            self._cache_leg[key] = res
            return res
        return optimal_leg_3d(
            p_start, p_end, aircraft, self.scenario,
            max_duration=max_duration, engine=self, z_cruise=z_cruise,
        )

    def leg_cost(
        self,
        p_start: Point,
        p_end: Point,
        aircraft_id: str,
        max_duration: Optional[float] = None,
        z_cruise: Optional[float] = None,
    ) -> Tuple[float, float]:
        """Returns `(duration_s, energy_wh)` or `(INF, INF)` if infeasible."""
        if max_duration is None:
            zc_key = -1 if z_cruise is None else int(round(z_cruise))
            key = (
                aircraft_id,
                self._q(p_start[0]),
                self._q(p_start[1]),
                self._q(p_start[2]),
                self._q(p_end[0]),
                self._q(p_end[1]),
                self._q(p_end[2]),
                zc_key,
            )
            cached = self._cache_cost.get(key)
            if cached is not None:
                return cached
            ac = self.aircraft_by_id[aircraft_id]
            res = self.optimal_leg(p_start, p_end, ac, max_duration=None, z_cruise=z_cruise)
            val = (res[1], res[2]) if res is not None else (INF, INF)
            self._cache_cost[key] = val
            return val
        ac = self.aircraft_by_id[aircraft_id]
        res = self.optimal_leg(p_start, p_end, ac, max_duration=max_duration, z_cruise=z_cruise)
        return (res[1], res[2]) if res is not None else (INF, INF)


_ENGINE_CACHE: Dict[int, RoutingEngine] = {}


def get_engine(scenario: Scenario) -> RoutingEngine:
    """Returns a cached RoutingEngine for a Scenario instance."""
    sid = id(scenario)
    eng = _ENGINE_CACHE.get(sid)
    if eng is None or eng.scenario is not scenario:
        if len(_ENGINE_CACHE) > 8:
            _ENGINE_CACHE.clear()
        eng = RoutingEngine(scenario)
        _ENGINE_CACHE[sid] = eng
    return eng


def leg_cost_fast(
    p_start: Point,
    p_end: Point,
    aircraft_id: str,
    scenario: Scenario,
    max_duration: Optional[float] = None,
    engine: Optional[RoutingEngine] = None,
) -> Tuple[float, float]:
    """Fast memoized API for allocation: returns `(duration_s, energy_wh)`."""
    eng = engine if engine is not None else get_engine(scenario)
    return eng.leg_cost(p_start, p_end, aircraft_id, max_duration=max_duration)


def route_cost_fast(
    waypoints_3d: Sequence[Point],
    aircraft_id: str,
    scenario: Scenario,
    engine: Optional[RoutingEngine] = None,
) -> Tuple[float, float]:
    """Fast memoized API for a sequence of 3D waypoints: returns `(total_duration_s, total_energy_wh)`."""
    eng = engine if engine is not None else get_engine(scenario)
    tot_d = 0.0
    tot_e = 0.0
    for k in range(len(waypoints_3d) - 1):
        d, e = eng.leg_cost(waypoints_3d[k], waypoints_3d[k + 1], aircraft_id)
        if math.isinf(d):
            return INF, INF
        tot_d += d
        tot_e += e
    return tot_d, tot_e


def best_observation_point(
    contact: Contact,
    prev_xy: Point2D,
    next_xy: Point2D,
    z_cruise: float,
    r_obs: float,
    cylinders: Optional[Sequence[Cylinder]] = None,
    angle_offset_deg: float = 0.0,
) -> Point2D:
    """Places the observation point on the maximum horizontal circle inside `r_obs`,
    oriented along the bisector between `prev_xy` and `next_xy` to minimize tour length.
    """
    cx, cy, cz = contact.pos
    dz = z_cruise - cz
    r_sq = r_obs * r_obs - dz * dz
    if r_sq <= 0.0:
        return (cx, cy)
    r_h = max(0.0, math.sqrt(r_sq) - SAFE_OBS_MARGIN)

    # Unit vectors from contact toward prev and next.
    v1x, v1y = prev_xy[0] - cx, prev_xy[1] - cy
    n1 = math.hypot(v1x, v1y)
    v2x, v2y = next_xy[0] - cx, next_xy[1] - cy
    n2 = math.hypot(v2x, v2y)

    bx, by = 0.0, 0.0
    if n1 > 1e-6:
        bx += v1x / n1
        by += v1y / n1
    if n2 > 1e-6:
        bx += v2x / n2
        by += v2y / n2
    nb = math.hypot(bx, by)
    if nb < 1e-6:
        if n1 > 1e-6:
            bx, by = v1x / n1, v1y / n1
        else:
            bx, by = 1.0, 0.0
    else:
        bx, by = bx / nb, by / nb

    if abs(angle_offset_deg) > 1e-6:
        rad = math.radians(angle_offset_deg)
        ca, sa = math.cos(rad), math.sin(rad)
        bx, by = bx * ca - by * sa, bx * sa + by * ca

    cand = (cx + bx * r_h, cy + by * r_h)
    if cylinders is None:
        return cand

    active = [c for c in cylinders if z_cruise < c[3] + SAFE_MARGIN_Z * 0.5]
    if _point_outside_all(cand[0], cand[1], active):
        return cand

    # Fallback: rotate around circle to find closest valid observation point.
    base_ang = math.atan2(by, bx)
    for deg in (20, -20, 40, -40, 60, -60, 90, -90, 120, -120, 150, -150, 180):
        ang = base_ang + math.radians(deg)
        pt = (cx + r_h * math.cos(ang), cy + r_h * math.sin(ang))
        if _point_outside_all(pt[0], pt[1], active):
            return pt
    # Last resort: shrink radius toward contact center.
    for frac in (0.6, 0.3, 0.0):
        pt = (cx + bx * r_h * frac, cy + by * r_h * frac)
        if _point_outside_all(pt[0], pt[1], active):
            return pt
    return (cx, cy)


def _round_wp(
    t: float,
    p: Point,
    action: Optional[str] = None,
    target: Optional[str] = None,
    dwell_s: float = 0.0,
) -> dict:
    d: dict = {
        "t": round(t, 3),
        "x": round(p[0], 3),
        "y": round(p[1], 3),
        "z": round(p[2], 3),
    }
    if action is not None:
        d["action"] = action
    if target is not None:
        d["target"] = target
    if dwell_s > 0.0:
        d["dwell_s"] = round(dwell_s, 3)
    return d


def _append_leg_wps(
    wps: List[dict],
    pts: Sequence[Point],
    t_start: float,
    t_end: float,
    aircraft: Aircraft,
    action: Optional[str] = None,
    target: Optional[str] = None,
    dwell_s: float = 0.0,
) -> Optional[float]:
    """Appends timed waypoints for `pts[1:]` over `[t_start, t_end]`.

    Returns the rounded arrival time at `pts[-1]`, or None if kinematically infeasible.
    """
    n_legs = len(pts) - 1
    if n_legs <= 0:
        return t_start
    total_dur = t_end - t_start
    if total_dur <= 0.0:
        return None

    v_h_max = MAX_SPEED_FRAC * aircraft.v_h_mps
    d_mins: List[float] = []
    dhs: List[float] = []
    for k in range(n_legs):
        p0, p1 = pts[k], pts[k + 1]
        dh = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        dz = p1[2] - p0[2]
        t_h = dh / v_h_max if dh > 0.0 else 0.0
        t_z = (dz / (MAX_SPEED_FRAC * aircraft.v_up_mps)) if dz > 0.0 else (-dz / (MAX_SPEED_FRAC * aircraft.v_down_mps))
        d_mins.append(max(t_h, t_z) + 0.015)
        dhs.append(dh)

    sum_min = sum(d_mins)
    if total_dur < sum_min:
        return None

    # Distribute extra duration proportionally to horizontal distance (constant speed minimizes k_v * v^2 * d).
    extra = total_dur - sum_min
    sum_dh = sum(dhs)
    t_cur = t_start
    for k in range(n_legs):
        if k == n_legs - 1:
            t_next = t_end
        else:
            share = (dhs[k] / sum_dh) if sum_dh > 1e-6 else (1.0 / n_legs)
            t_next = t_cur + d_mins[k] + extra * share
        is_last = k == n_legs - 1
        wps.append(
            _round_wp(
                t_next,
                pts[k + 1],
                action=action if is_last else None,
                target=target if is_last else None,
                dwell_s=dwell_s if is_last else 0.0,
            )
        )
        t_cur = t_next
    return round(t_end, 3)


def build_scout_route(
    scout: Aircraft,
    tasks: Sequence[Contact],
    scenario: Scenario,
    z_layer: Optional[float] = None,
    depart_shift: float = 0.0,
    engine: Optional[RoutingEngine] = None,
    latest_ends: Optional[Dict[str, float]] = None,
    angle_offset_deg: float = 0.0,
) -> Optional[List[dict]]:
    """Builds a minimum-energy scout route visiting `tasks` in order and returning home.

    Key optimizations:
      - Optimal observation points on the 150 m observation sphere oriented along tour bisectors.
      - Delayed ground departure (`waypoints[0].t > 0`, 0 Wh) to eliminate airborne waiting.
      - Diagonal climb/descent on first/last legs (no vertical hover waste).
      - Speed adaptation up to `0.995 * v_h_mps` when tight time windows require it.
    """
    if not tasks:
        return None
    eng = engine if engine is not None else get_engine(scenario)
    rules = scenario.rules
    z_cruise = rules.z_min_m if z_layer is None else max(rules.z_min_m, min(rules.z_max_m, z_layer))
    dwell = rules.obs_dwell_s + SAFE_MARGIN_T

    home = scout.home
    m = len(tasks)

    # 1. Compute optimal observation points iteratively (2 passes for tight bisectors).
    obs_xy: List[Point2D] = [(c.pos[0], c.pos[1]) for c in tasks]
    for _ in range(2):
        new_xy: List[Point2D] = []
        for i, c in enumerate(tasks):
            prev_p = home[:2] if i == 0 else obs_xy[i - 1]
            next_p = home[:2] if i == m - 1 else obs_xy[i + 1]
            new_xy.append(
                best_observation_point(
                    c, prev_p, next_p, z_cruise, rules.R_obs_m,
                    cylinders=eng.cylinders, angle_offset_deg=angle_offset_deg,
                )
            )
        obs_xy = new_xy

    obs_pts: List[Point] = [(xy[0], xy[1], z_cruise) for xy in obs_xy]

    # 2. Compute optimal 3D legs: home -> obs[0] -> ... -> obs[m-1] -> home.
    waypoints_seq: List[Point] = [home] + obs_pts + [home]
    legs_pts: List[List[Point]] = []
    legs_opt_dur: List[float] = []
    legs_min_dur: List[float] = []

    for k in range(m + 1):
        p0, p1 = waypoints_seq[k], waypoints_seq[k + 1]
        leg_res = eng.optimal_leg(p0, p1, scout, max_duration=None, z_cruise=z_cruise)
        if leg_res is None:
            return None
        pts, opt_d, _ = leg_res
        # Compute kinematic minimum duration for this polyline.
        v_h_max = MAX_SPEED_FRAC * scout.v_h_mps
        min_d = 0.0
        for j in range(len(pts) - 1):
            a, b = pts[j], pts[j + 1]
            dh = math.hypot(b[0] - a[0], b[1] - a[1])
            dz = b[2] - a[2]
            t_h = dh / v_h_max if dh > 0.0 else 0.0
            t_z = (dz / (MAX_SPEED_FRAC * scout.v_up_mps)) if dz > 0.0 else (-dz / (MAX_SPEED_FRAC * scout.v_down_mps))
            min_d += max(t_h, t_z) + SAFE_MARGIN_T
        legs_pts.append(pts)
        legs_opt_dur.append(opt_d)
        legs_min_dur.append(min_d)

    # 3. Forward pass: compute earliest feasible arrival at each observation.
    # Start with ideal ground departure for task 0.
    w0 = tasks[0].window
    if w0 is None:
        return None
    lo0, hi0 = w0[0] + SAFE_MARGIN_T, w0[1] - SAFE_MARGIN_T
    if latest_ends and tasks[0].id in latest_ends:
        hi0 = min(hi0, latest_ends[tasks[0].id] - SAFE_MARGIN_T)

    # Ground departure to arrive at task 0 at max(legs_opt_dur[0], lo0) + depart_shift.
    t_dep = max(0.0, lo0 - legs_opt_dur[0]) + depart_shift
    arrivals: List[float] = [0.0] * m

    t_cur = t_dep
    for i, c in enumerate(tasks):
        if c.window is None:
            return None
        lo = c.window[0] + SAFE_MARGIN_T
        hi = c.window[1] - SAFE_MARGIN_T
        if latest_ends and c.id in latest_ends:
            hi = min(hi, latest_ends[c.id] - SAFE_MARGIN_T)
        if hi - lo < dwell:
            return None

        earliest_opt = t_cur + legs_opt_dur[i]
        earliest_min = t_cur + legs_min_dur[i]

        if earliest_min + dwell > hi:
            return None
        if earliest_opt + dwell <= hi:
            arr = max(earliest_opt, lo)
        else:
            # Accelerate leg i to meet hi.
            arr = max(earliest_min, min(lo, hi - dwell))
            if arr + dwell > hi:
                arr = hi - dwell
            if arr < lo or arr < earliest_min:
                return None
        arrivals[i] = arr
        t_cur = arr + dwell

    # 4. Backward pass: push earlier tasks later (within their hi & latest_ends)
    # so any inter-task waiting is shifted to free ground wait at t_dep!
    if depart_shift == 0.0:
        for i in range(m - 2, -1, -1):
            c = tasks[i]
            hi = c.window[1] - SAFE_MARGIN_T  # type: ignore[index]
            if latest_ends and c.id in latest_ends:
                hi = min(hi, latest_ends[c.id] - SAFE_MARGIN_T)
            ideal_arr = arrivals[i + 1] - legs_opt_dur[i + 1] - dwell
            if ideal_arr > arrivals[i]:
                arrivals[i] = min(ideal_arr, hi - dwell)
        t_dep = max(0.0, arrivals[0] - legs_opt_dur[0])

    # Check return leg against horizon.
    t_last_dep = arrivals[-1] + dwell
    t_home = t_last_dep + legs_opt_dur[m]
    if t_home > scenario.horizon_s - SAFE_MARGIN_T:
        # Try accelerating return leg.
        t_home_min = t_last_dep + legs_min_dur[m]
        if t_home_min > scenario.horizon_s - SAFE_MARGIN_T:
            return None
        t_home = scenario.horizon_s - SAFE_MARGIN_T

    # 5. Materialize rounded waypoints.
    wps: List[dict] = [_round_wp(t_dep, home)]
    t_prev = round(t_dep, 3)
    for i, c in enumerate(tasks):
        arr = _append_leg_wps(
            wps, legs_pts[i], t_prev, arrivals[i], scout,
            action="observe", target=c.id, dwell_s=dwell,
        )
        if arr is None:
            return None
        t_prev = round(arr + round(dwell, 3), 3)

    ret_arr = _append_leg_wps(wps, legs_pts[m], t_prev, t_home, scout)
    if ret_arr is None or ret_arr > scenario.horizon_s + 1e-6:
        return None

    # 6. Quick energy check against usable_wh.
    wp_objs = [
        Waypoint(w["t"], w["x"], w["y"], w["z"], w.get("action"), w.get("target"), w.get("dwell_s", 0.0))
        for w in wps
    ]
    if route_energy_wh(wp_objs, scout) > scout.usable_wh - 1e-3:
        return None

    return wps


def build_effector_route(
    effector: Aircraft,
    contact: Contact,
    arrive_t: float,
    scenario: Scenario,
    z_layer: Optional[float] = None,
    approach_angle: float = 0.0,
    engine: Optional[RoutingEngine] = None,
) -> Tuple[Optional[List[dict]], float]:
    """Builds a minimum-energy effector route engaging `contact` at `arrive_t`.

    Optimizations:
      - Eliminates the 300 m approach hold and vertical takeoff hover of `baseline.py`.
      - Engages at the edge of the R_eng_m sphere (24 m closer along approach) at optimal z.
      - Direct low-altitude flight when `z_layer is None` and airspace is clear, or
        minimum-energy layered cruise with optimal 2D tangent detour / 3D overflight.
      - Accelerates up to `0.995 * v_h_mps` if `arrive_t` is tighter than v*-optimal.

    Returns:
        `(waypoints_dicts_or_None, earliest_feasible_arrival_s)`.
    """
    eng = engine if engine is not None else get_engine(scenario)
    rules = scenario.rules
    home = effector.home
    cx, cy, cz = contact.pos

    # Direction from contact toward home, rotated by approach_angle.
    vx, vy = home[0] - cx, home[1] - cy
    vn = math.hypot(vx, vy)
    if vn < 1e-6:
        ux, uy = 1.0, 0.0
    else:
        ux, uy = vx / vn, vy / vn
    if abs(approach_angle) > 1e-6:
        rad = math.radians(approach_angle)
        ca, sa = math.cos(rad), math.sin(rad)
        ux, uy = ux * ca - uy * sa, ux * sa + uy * ca

    r_eng = max(0.0, rules.R_eng_m - SAFE_ENG_MARGIN)

    if z_layer is None:
        # Try direct 2-waypoint low-altitude engagement (zero climb energy if cz == 0!).
        z_eng = cz
        e_pt: Point = (cx + ux * r_eng, cy + uy * r_eng, z_eng)
        if abs(approach_angle) < 1e-6:
            pts_direct = [home, e_pt]
            if _verify_3d_polyline(pts_direct, eng.cylinders):
                res = _polyline_time_energy(pts_direct, effector, max_duration=None)
                if res is not None:
                    _, opt_d, _ = res
                    # Check kinematic min duration.
                    v_h_max = MAX_SPEED_FRAC * effector.v_h_mps
                    dh = math.hypot(e_pt[0] - home[0], e_pt[1] - home[1])
                    dz = e_pt[2] - home[2]
                    min_d = max(
                        dh / v_h_max if dh > 0 else 0.0,
                        (dz / (MAX_SPEED_FRAC * effector.v_up_mps)) if dz > 0 else (-dz / (MAX_SPEED_FRAC * effector.v_down_mps)),
                    ) + SAFE_MARGIN_T
                    if arrive_t < min_d:
                        return None, min_d
                    dur = min(opt_d, arrive_t)
                    t_dep = arrive_t - dur
                    wps = [_round_wp(t_dep, home)]
                    arr = _append_leg_wps(
                        wps, pts_direct, round(t_dep, 3), arrive_t, effector,
                        action="engage", target=contact.id,
                    )
                    if arr is not None:
                        wp_objs = [Waypoint(w["t"], w["x"], w["y"], w["z"], w.get("action"), w.get("target"), 0.0) for w in wps]
                        if route_energy_wh(wp_objs, effector) <= effector.usable_wh - 1e-3:
                            return wps, min_d
        # Fall back to z_min_m cruise layer if direct path was blocked or angled.
        z_cruise = rules.z_min_m
    else:
        z_cruise = max(rules.z_min_m, min(rules.z_max_m, z_layer))

    # Engagement point at optimal height inside R_eng_m sphere (minimizes descent time).
    z_eng = min(z_cruise, cz + r_eng * 0.85)
    dz_eng = z_eng - cz
    r_h_eng = math.sqrt(max(0.0, r_eng * r_eng - dz_eng * dz_eng))
    e_pt = (cx + ux * r_h_eng, cy + uy * r_h_eng, z_eng)

    if abs(approach_angle) > 1e-6:
        # Insert an approach waypoint offset by angle_deg at distance min(250m, 0.4*dist) to separate paths.
        reach = min(250.0, 0.4 * max(vn, 100.0))
        a_pt: Point = (cx + ux * reach, cy + uy * reach, z_cruise)
        leg1 = eng.optimal_leg(home, a_pt, effector, max_duration=None, z_cruise=z_cruise)
        if leg1 is None:
            return None, arrive_t
        leg2 = eng.optimal_leg(a_pt, e_pt, effector, max_duration=None, z_cruise=z_cruise)
        if leg2 is None:
            return None, arrive_t
        pts = leg1[0] + leg2[0][1:]
    else:
        leg = eng.optimal_leg(home, e_pt, effector, max_duration=None, z_cruise=z_cruise)
        if leg is None:
            return None, arrive_t
        pts = leg[0]
        # If z_layer was explicitly requested and path is direct 2-wp, lift mid-point to z_cruise for R8 separation.
        if z_layer is not None and len(pts) == 2:
            mid_x = home[0] + 0.15 * (e_pt[0] - home[0])
            mid_y = home[1] + 0.15 * (e_pt[1] - home[1])
            mid2_x = home[0] + 0.85 * (e_pt[0] - home[0])
            mid2_y = home[1] + 0.85 * (e_pt[1] - home[1])
            cand_pts = [home, (mid_x, mid_y, z_cruise), (mid2_x, mid2_y, z_cruise), e_pt]
            if _verify_3d_polyline(cand_pts, eng.cylinders):
                pts = cand_pts

    # Compute kinematic min and optimal duration for `pts`.
    v_h_max = MAX_SPEED_FRAC * effector.v_h_mps
    min_d = 0.0
    for j in range(len(pts) - 1):
        a, b = pts[j], pts[j + 1]
        dh = math.hypot(b[0] - a[0], b[1] - a[1])
        dz = b[2] - a[2]
        t_h = dh / v_h_max if dh > 0.0 else 0.0
        t_z = (dz / (MAX_SPEED_FRAC * effector.v_up_mps)) if dz > 0.0 else (-dz / (MAX_SPEED_FRAC * effector.v_down_mps))
        min_d += max(t_h, t_z) + SAFE_MARGIN_T

    if arrive_t < min_d:
        return None, min_d

    res_opt = _polyline_time_energy(pts, effector, max_duration=None)
    if res_opt is None:
        return None, min_d
    opt_d = res_opt[1]
    dur = min(opt_d, arrive_t)
    t_dep = arrive_t - dur
    if t_dep < 0.0:
        t_dep = 0.0

    wps = [_round_wp(t_dep, home)]
    arr = _append_leg_wps(
        wps, pts, round(t_dep, 3), arrive_t, effector,
        action="engage", target=contact.id,
    )
    if arr is None:
        return None, min_d

    wp_objs = [Waypoint(w["t"], w["x"], w["y"], w["z"], w.get("action"), w.get("target"), 0.0) for w in wps]
    if route_energy_wh(wp_objs, effector) > effector.usable_wh - 1e-3:
        return None, min_d

    return wps, min_d

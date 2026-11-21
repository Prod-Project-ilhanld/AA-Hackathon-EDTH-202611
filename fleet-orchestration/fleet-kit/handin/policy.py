"""Link-loss decentralized policy: event-driven gossip, R4 confirmation guard, and R8 separation hold.

An aircraft that aborts hovers where it is (hold, flagged "ab") instead of retracing its route against later
traffic, and backs off along its route only when it stands in an on-plan peer's way.

Standard library + fleetkit only. Messages <= 64 bytes, < 50 ms per step.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set, Tuple

from fleetkit.geometry import dist3, hdist, segment_enters_cylinder
from fleetkit.linkloss.sim import RouteClock
from fleetkit.model import EFFECTOR, HOSTILE, SCOUT, parse_plan

MAX_MSG_BYTES = 64
SEP_PAD_M = 4.5


def _seg_min_dist3(
    p0: Tuple[float, float, float],
    p1: Tuple[float, float, float],
    q0: Tuple[float, float, float],
    q1: Tuple[float, float, float],
) -> float:
    """Exact minimum 3D distance between synchronized linear segments p(s) and q(s), s in [0, 1]."""
    rx, ry, rz = p0[0] - q0[0], p0[1] - q0[1], p0[2] - q0[2]
    vx = (p1[0] - p0[0]) - (q1[0] - q0[0])
    vy = (p1[1] - p0[1]) - (q1[1] - q0[1])
    vz = (p1[2] - p0[2]) - (q1[2] - q0[2])
    vv = vx * vx + vy * vy + vz * vz
    if vv <= 1e-12:
        s = 0.0
    else:
        s = -(rx * vx + ry * vy + rz * vz) / vv
        if s < 0.0:
            s = 0.0
        elif s > 1.0:
            s = 1.0
    dx = rx + s * vx
    dy = ry + s * vy
    dz = rz + s * vz
    return (dx * dx + dy * dy + dz * dz) ** 0.5


def _pack_msg(d: dict) -> Optional[dict]:
    """Ensures compact JSON fits within 64 bytes."""
    if not d:
        return None
    if len(json.dumps(d, separators=(",", ":")).encode()) <= MAX_MSG_BYTES:
        return d
    # Trim optional fields if over budget.
    trimmed = dict(d)
    for k in ("zn", "rc", "ob", "u"):
        if k in trimmed:
            val = trimmed[k]
            if isinstance(val, list) and len(val) > 1:
                trimmed[k] = val[:1]
            else:
                del trimmed[k]
            if len(json.dumps(trimmed, separators=(",", ":")).encode()) <= MAX_MSG_BYTES:
                return trimmed
    return None


class Policy:
    """Decentralized link-loss policy with minimal messaging and R4/R8 safety."""

    def __init__(self, scenario: Any, plan: dict, aircraft_id: str) -> None:
        self.scenario = scenario
        self.aircraft_id = aircraft_id
        self.rules = scenario.rules
        routes, _ = parse_plan(plan)
        self.routes = routes
        self.clocks: Dict[str, RouteClock] = {aid: RouteClock(rt) for aid, rt in routes.items()}
        self.clock = self.clocks[aircraft_id]

        ac_by_id = scenario.aircraft_by_id()
        self.ac = ac_by_id[aircraft_id]
        self.is_effector = self.ac.type == EFFECTOR
        self.is_scout = self.ac.type == SCOUT

        last_wp = routes[aircraft_id].waypoints[-1]
        self.target: Optional[str] = last_wp.target if (self.is_effector and last_wp.action == "engage") else None

        # Planned observation completion times per contact: {contact_id: [(scout_id, t_end), ...]}.
        self.obs_plan: Dict[str, List[Tuple[str, float]]] = {}
        self.my_obs_targets: Set[str] = set()
        for aid, rt in routes.items():
            if ac_by_id[aid].type != SCOUT:
                continue
            for wp in rt.waypoints:
                if wp.action == "observe" and wp.target:
                    self.obs_plan.setdefault(wp.target, []).append((aid, wp.depart))
                    if aid == aircraft_id:
                        self.my_obs_targets.add(wp.target)

        # Effector peer groups per target (for R8 exemption & group abort).
        self.peers_by_target: Dict[str, Set[str]] = {}
        self.peer_target: Dict[str, Optional[str]] = {}
        for aid, rt in routes.items():
            lw = rt.waypoints[-1]
            tgt = lw.target if (ac_by_id[aid].type == EFFECTOR and lw.action == "engage") else None
            self.peer_target[aid] = tgt
            if tgt:
                self.peers_by_target.setdefault(tgt, set()).add(aid)

        self.reclassified: Set[str] = set()
        self.zones: List[Tuple[int, int, int, int]] = []
        self.observed: Set[str] = set()
        self.pre_cut_init = False

        # Peer state tracking: {aid: (t_ref, tau_ref, mode)} where mode in ("route", "hold", "return")
        self.peer_state: Dict[str, Tuple[float, float, str]] = {}
        self.aborted_peers: Set[str] = set()

        # Outbound queues with repeat counts so critical news survives packet loss.
        self._rc_ttl: Dict[str, int] = {}
        self._zn_ttl: Dict[Tuple[int, int, int, int], int] = {}
        self._ob_ttl: Dict[str, int] = {}
        self._rt_ttl: int = 0
        self._last_rt_sent: float = -100.0
        self._last_hd_sent: float = -100.0
        self._last_mode: str = "route"
        self._last_hb_t: float = -100.0
        self._sent_obs: Set[str] = set()
        self._hold_streak: int = 0
        self._rs_ttl: int = 0

    def _init_pre_cut(self, t_loss: float) -> None:
        self.pre_cut_init = True
        for cid, lst in self.obs_plan.items():
            if any(t_end <= t_loss + 1e-6 for _, t_end in lst):
                self.observed.add(cid)

    def _learn_sensed(self, ev: dict) -> None:
        kind = ev["kind"]
        if kind == "reclassify":
            c = ev["contact"]
            if c not in self.reclassified:
                self.reclassified.add(c)
                self._rc_ttl[c] = 4
        elif kind == "popup_zone":
            z = (round(ev["center"][0]), round(ev["center"][1]), round(ev["radius_m"]), round(ev["top_m"]))
            if z not in self.zones:
                self.zones.append(z)
                self._zn_ttl[z] = 4

    def _learn_inbox(self, inbox: List[dict]) -> None:
        for msg in inbox:
            src = msg["from"]
            sent_t = float(msg["sent_t"])
            p = msg["payload"]
            if not isinstance(p, dict):
                continue
            for c in p.get("rc", ()):
                if c not in self.reclassified:
                    self.reclassified.add(c)
                    self._rc_ttl[c] = 2
            for z_raw in p.get("zn", ()):
                z = (int(z_raw[0]), int(z_raw[1]), int(z_raw[2]), int(z_raw[3]))
                if z not in self.zones:
                    self.zones.append(z)
                    self._zn_ttl[z] = 2
            for c in p.get("ob", ()):
                if c not in self.observed:
                    self.observed.add(c)
                    self._ob_ttl[c] = 2
            if "rt" in p:
                self.aborted_peers.add(src)
                u = float(p.get("u", sent_t))
                self.peer_state[src] = (sent_t, u, "return")
            elif "hd" in p:
                u = float(p.get("u", sent_t))
                self.peer_state[src] = (sent_t, u, "hold")
                if p.get("ab"):  # aborted: it hovers for good, and co-effectors must abort too
                    self.aborted_peers.add(src)
            elif "rs" in p:
                u = float(p.get("u", sent_t))
                self.peer_state[src] = (sent_t, u, "route")

    def _route_hits_known_zone(self, tau: float) -> bool:
        if not self.zones:
            return False
        k = self.clock.next_waypoint(tau)
        pts = [self.clock.position(tau)] + self.clock.pos[k:]
        for cx, cy, r, top in self.zones:
            for a, b in zip(pts, pts[1:]):
                if segment_enters_cylinder(a, b, (cx, cy), r + 1.0, top):
                    return True
        return False

    def _peer_pos_at(self, aid: str, t: float, now_t: float) -> Optional[Tuple[float, float, float]]:
        clk = self.clocks[aid]
        if aid in self.peer_state:
            t_ref, tau_ref, mode = self.peer_state[aid]
            # Expire stale hold states only after 5 missed 3s heartbeats.
            if mode == "hold" and now_t - t_ref > 15.0 and aid not in self.aborted_peers:
                del self.peer_state[aid]
            else:
                dt = max(0.0, t - t_ref)
                if mode == "return":
                    tau_est = tau_ref - dt
                    if tau_est <= clk.start + 1e-6:
                        return None
                    return clk.position(tau_est)
                if mode == "hold":
                    return clk.position(tau_ref)
                if mode == "route":
                    tau_est = tau_ref + dt
                    if tau_est >= clk.end - 1e-6:
                        return None
                    return clk.position(tau_est)
        # Default: dead-reckon along planned route.
        if t < clk.start - 1e-6 or t > clk.end + 1e-6:
            return None
        return clk.position(t)

    def _r8_conflict(self, t: float, tau: float, rate: float) -> bool:
        """Checks if moving at `rate` over the next 3s risks violating R8 against any peer."""
        if rate == 0.0:
            return False
        d_lim = self.rules.d_sep_m + SEP_PAD_M
        i_am_returning = rate < 0.0
        i_am_off_plan = i_am_returning or abs(tau - t) >= 0.25

        # Precompute our 1s segments over [t, t+4].
        my_segs: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = []
        for k in range(4):
            t0_k = max(self.clock.start, min(self.clock.end, tau + k * rate))
            t1_k = max(self.clock.start, min(self.clock.end, tau + (k + 1) * rate))
            if t1_k <= self.clock.start + 1e-6 and t0_k <= self.clock.start + 1e-6:
                break
            my_segs.append((self.clock.position(t0_k), self.clock.position(t1_k)))
        if not my_segs:
            return False

        for aid, clk in self.clocks.items():
            if aid == self.aircraft_id:
                continue
            peer_mode = self.peer_state.get(aid, (0.0, 0.0, "route"))[2]
            # Two on-plan aircraft follow the already-validated plan; skip false-positive holds.
            if not i_am_off_plan and peer_mode == "route":
                continue
            # R8 exemption: effectors engaging the same target near it.
            if (
                self.target is not None
                and self.peer_target.get(aid) == self.target
                and self.target in self.scenario.contact_by_id()
            ):
                cpos = self.scenario.contact_by_id()[self.target].pos
                if hdist(my_segs[0][1], cpos) <= self.rules.R_eng_m + 50.0:
                    continue

            for k, (p0, p1) in enumerate(my_segs):
                q0 = self._peer_pos_at(aid, t + k, t)
                q1 = self._peer_pos_at(aid, t + k + 1.0, t)
                if q0 is None and q1 is None:
                    continue
                if q0 is None:
                    q0 = q1
                if q1 is None:
                    q1 = q0
                if _seg_min_dist3(p0, p1, q0, q1) < d_lim:
                    cur_pm = self.peer_state.get(aid, (0.0, 0.0, "route"))[2]
                    if cur_pm == "hold":
                        return True
                    # A returning aircraft yields to any on-plan peer (which may not have heard the abort).
                    if i_am_returning and cur_pm == "route":
                        return True
                    if not i_am_returning and cur_pm == "return":
                        # Only yield in immediate 1-2s if returning peer is already on our path.
                        if k <= 1 and self.aircraft_id > aid:
                            return True
                        break
                    if self.aircraft_id > aid:
                        return True
                    break
        return False

    def _blocking(self, t: float, tau: float, horizon: int = 6) -> bool:
        """True if an on-plan peer is predicted to pass within separation of our position in the next seconds."""
        me = self.clock.position(tau)
        d_lim = self.rules.d_sep_m + SEP_PAD_M
        for aid in self.clocks:
            if aid == self.aircraft_id or self.peer_state.get(aid, (0.0, 0.0, "route"))[2] != "route":
                continue
            for k in range(horizon + 1):
                q = self._peer_pos_at(aid, t + k, t)
                if q is not None and dist3(me, q) < d_lim:
                    return True
        return False

    def _peer_near(self, t: float, tau: float, radius: float = 500.0) -> bool:
        """True if any live peer is predicted within `radius` of our held position (it must hear we hover)."""
        me = self.clock.position(tau)
        for aid in self.clocks:
            if aid != self.aircraft_id:
                q = self._peer_pos_at(aid, t, t)
                if q is not None and dist3(me, q) < radius:
                    return True
        return False

    def _build_message(self, t: float, tau: float, mode: str, action_kind: str) -> Optional[dict]:
        msg: Dict[str, Any] = {}

        if self._rc_ttl:
            rc_list = sorted(self._rc_ttl)[:2]
            msg["rc"] = rc_list
            for c in rc_list:
                self._rc_ttl[c] -= 1
                if self._rc_ttl[c] <= 0:
                    del self._rc_ttl[c]

        if self._zn_ttl:
            z = next(iter(self._zn_ttl))
            msg["zn"] = [list(z)]
            self._zn_ttl[z] -= 1
            if self._zn_ttl[z] <= 0:
                del self._zn_ttl[z]

        if self._ob_ttl:
            ob_list = sorted(self._ob_ttl)[:2]
            msg["ob"] = ob_list
            for c in ob_list:
                self._ob_ttl[c] -= 1
                if self._ob_ttl[c] <= 0:
                    del self._ob_ttl[c]

        if action_kind == "hold":
            gap = 3.0 if self._last_mode != "return" or self._peer_near(t, tau) else 15.0
            if self._hold_streak <= 3 or t - self._last_hd_sent >= gap:
                msg["hd"] = 1
                msg["u"] = round(tau, 1)
                if self._last_mode == "return":
                    msg["ab"] = 1
                self._last_hd_sent = t
        elif mode == "return" or action_kind == "return":
            if self._rt_ttl > 0 or (t - self._last_rt_sent >= 5.0):
                msg["rt"] = 1
                msg["u"] = round(tau, 1)
                self._last_rt_sent = t
                if self._rt_ttl > 0:
                    self._rt_ttl -= 1

        elif self._rs_ttl > 0:
            msg["rs"] = 1
            msg["u"] = round(tau, 1)
            self._rs_ttl -= 1

        if not msg:
            return None
        return _pack_msg(msg)

    def step(self, obs: dict) -> Tuple[dict, Optional[dict]]:
        t = float(obs["t"])
        t_loss = float(obs["t_loss"])
        tau = float(obs["tau"])
        mode = str(obs["mode"])

        if not self.pre_cut_init:
            self._init_pre_cut(t_loss)

        for c in obs.get("own_observed", ()):
            if c not in self.observed:
                self.observed.add(c)
            if c not in self._sent_obs:
                self._sent_obs.add(c)
                self._ob_ttl[c] = 4

        for ev in obs.get("sensed", ()):
            self._learn_sensed(ev)

        self._learn_inbox(obs.get("inbox", ()))

        # Decide continue vs return.
        abort = mode == "return"
        if not abort and self._route_hits_known_zone(tau):
            abort = True

        if not abort and self.is_effector and self.target is not None:
            if self.target in self.reclassified:
                abort = True
            else:
                # Group abort if a co-effector on the same target aborted.
                peers = self.peers_by_target.get(self.target, set())
                if any(p in self.aborted_peers for p in peers if p != self.aircraft_id):
                    abort = True
                # R4 guard: never engage without confirmed observation when close to engagement.
                if not abort and self.target not in self.observed:
                    time_to_eng = self.clock.end - tau
                    if time_to_eng <= 4.0:
                        abort = True

        if abort and self._last_mode != "return":
            self._rt_ttl = 4
            self._last_mode = "return"

        if abort:
            # Hover instead of retracing the route against later traffic; back off only when in an on-plan peer's way.
            if self._blocking(t, tau) and not self._r8_conflict(t, tau, -1.0):
                if self._hold_streak > 0:
                    self._rt_ttl = 3
                self._hold_streak = 0
                return {"kind": "return"}, self._build_message(t, tau, mode, "return")
            self._hold_streak += 1
            return {"kind": "hold"}, self._build_message(t, tau, mode, "hold")
        rate = 1.0
        action: dict = {"kind": "continue"}

        # R8 separation check.
        if self._r8_conflict(t, tau, rate):
            action = {"kind": "hold"}
            self._hold_streak += 1
        else:
            if self._hold_streak > 0:
                self._rs_ttl = 2
            self._hold_streak = 0

        msg = self._build_message(t, tau, mode, action["kind"])
        return action, msg

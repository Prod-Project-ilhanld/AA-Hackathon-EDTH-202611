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
SEP_PAD_M = 6.0
OB_WAIT_MAX_S = 40.0   # longest an effector waits short of its target for a late observation
STOP_S = 10.0          # a reclassify or group abort keeps flying the plan until this long before the target


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


def _pack_msg(msg: Any) -> Optional[Any]:
    """Ensures compact JSON (list or dict) fits within 64 bytes."""
    if not msg:
        return None
    if len(json.dumps(msg, separators=(",", ":")).encode()) <= MAX_MSG_BYTES:
        return msg
    if isinstance(msg, list):
        trimmed = list(msg)
        while len(trimmed) > 2:
            trimmed.pop()
            if len(json.dumps(trimmed, separators=(",", ":")).encode()) <= MAX_MSG_BYTES:
                return trimmed
        return None
    trimmed_d = dict(msg)
    for k in ("zn", "rc", "ob", "u"):
        if k in trimmed_d:
            val = trimmed_d[k]
            if isinstance(val, list) and len(val) > 1:
                trimmed_d[k] = val[:1]
            else:
                del trimmed_d[k]
            if len(json.dumps(trimmed_d, separators=(",", ":")).encode()) <= MAX_MSG_BYTES:
                return trimmed_d
    return None


class Policy:
    """Decentralized link-loss policy with minimal messaging and R4/R8 safety."""

    def __init__(self, scenario: Any, plan: dict, aircraft_id: str) -> None:
        self.scenario = scenario
        self.aircraft_id = aircraft_id
        self.rules = scenario.rules
        self._i2c: List[str] = [c.id for c in scenario.contacts]
        self._c2i: Dict[str, int] = {cid: i for i, cid in enumerate(self._i2c)}
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
        self._last_ob_near: Dict[str, float] = {}
        self._last_ae_t: float = -100.0
        self._ae_idx: int = 0
        self._tgt_ob_t: Optional[float] = None   # when we first knew our target's observation was complete
        self._ob_wait_t: Optional[float] = None   # when we started waiting short of the target for it
        self._yield_to: Optional[str] = None      # lower-id peer we backed off for, and since when
        self._yield_t: float = -100.0

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
            if isinstance(p, list) and len(p) >= 2:
                st = int(p[0])
                u = float(p[1]) * 0.1
                rc_raw = p[2] if len(p) > 2 and isinstance(p[2], list) else ()
                zn_raw = p[3] if len(p) > 3 and isinstance(p[3], list) else ()
                ob_raw = p[4] if len(p) > 4 and isinstance(p[4], list) else ()
                for idx in rc_raw:
                    if isinstance(idx, int) and 0 <= idx < len(self._i2c):
                        c = self._i2c[idx]
                        if c not in self.reclassified:
                            self.reclassified.add(c)
                            self._rc_ttl[c] = 2
                for z_item in zn_raw:
                    z = (int(z_item[0]), int(z_item[1]), int(z_item[2]), int(z_item[3]))
                    if z not in self.zones:
                        self.zones.append(z)
                        self._zn_ttl[z] = 2
                for idx in ob_raw:
                    if isinstance(idx, int) and 0 <= idx < len(self._i2c):
                        c = self._i2c[idx]
                        if c not in self.observed:
                            self.observed.add(c)
                            self._ob_ttl[c] = 2
                if st == 2:
                    self.aborted_peers.add(src)
                    self.peer_state[src] = (sent_t, u, "return")
                elif st in (1, 4):
                    self.peer_state[src] = (sent_t, u, "hold")
                    if st == 4:
                        self.aborted_peers.add(src)
                elif st == 3:
                    self.peer_state[src] = (sent_t, u, "route")
                continue
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

    def _back_hits_known_zone(self, tau: float, secs: int = 6) -> bool:
        """True if retracing the route for the next `secs` seconds enters a known zone."""
        pts = [self.clock.position(max(self.clock.start, tau - k)) for k in range(secs + 1)]
        return any(segment_enters_cylinder(a, b, (cx, cy), r + 1.0, top)
                   for cx, cy, r, top in self.zones for a, b in zip(pts, pts[1:]))

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

        # Precompute our 1s segments: 6s lookahead when returning, 4s otherwise.
        horizon_k = 6 if i_am_returning else 4
        my_segs: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = []
        for k in range(horizon_k):
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
            ps = self.peer_state.get(aid)
            peer_mode = ps[2] if ps else "route"
            # Two on-plan aircraft follow the already-validated plan; skip false-positive holds. A peer that
            # resumed late is not on plan: neither of us would yield if we skipped it.
            if not i_am_off_plan and peer_mode == "route" and (ps is None or ps[0] - ps[1] < 0.25):
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
                        if self.aircraft_id > aid:
                            return True
                        d_now = dist3(p0, q0)
                        d_next = dist3(p1, q0)
                        if d_next < d_now - 1e-3 and d_next < d_lim:
                            return True
                        break
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
                    if i_am_returning and cur_pm == "return" and k == 0 and dist3(p1, q0) < self.rules.d_sep_m + 1.5:
                        return True
                    break
            # A peer that just resumed after a hold may stop again any second, and that hold may reach us late:
            # also check it as held where we predict it now.
            st = self.peer_state.get(aid)
            if st is not None and st[2] == "route" and st[0] - st[1] >= 0.5 and t - st[0] <= 5.0:
                q = self._peer_pos_at(aid, t, t)
                if q is not None:
                    for p0, p1 in my_segs:
                        if _seg_min_dist3(p0, p1, q, q) < d_lim:
                            d_next = dist3(p1, q)
                            if self.aircraft_id > aid or (d_next < dist3(p0, q) - 1e-3 and d_next < d_lim):
                                return True
                            break
        return False

    def _blocking(self, t: float, tau: float, horizon: int = 6, below: Optional[str] = None) -> Optional[str]:
        """The id of an on-plan peer, or of a non-aborted peer waiting in a hold, predicted to pass within separation
        of our position in the next seconds, else None. `below`: only peers with a lower id."""
        me = self.clock.position(tau)
        d_lim = self.rules.d_sep_m + SEP_PAD_M
        for aid, clk in self.clocks.items():
            if aid == self.aircraft_id or (below is not None and aid >= below):
                continue
            t_ref, tau_ref, mode = self.peer_state.get(aid, (0.0, 0.0, "route"))
            if mode == "hold" and aid not in self.aborted_peers and t - t_ref <= 15.0:
                # It waits, maybe for us: where it would fly if it resumed now.
                for k in range(horizon + 1):
                    if tau_ref + k <= clk.end and dist3(me, clk.position(tau_ref + k)) < d_lim:
                        return aid
                continue
            if mode != "route":
                continue
            for k in range(horizon + 1):
                q = self._peer_pos_at(aid, t + k, t)
                if q is not None and dist3(me, q) < d_lim:
                    return aid
        return None

    def _peer_near(self, t: float, tau: float, radius: float = 500.0) -> bool:
        """True if any live peer is predicted within `radius` of our held position (it must hear we hover)."""
        me = self.clock.position(tau)
        for aid in self.clocks:
            if aid != self.aircraft_id:
                q = self._peer_pos_at(aid, t, t)
                if q is not None and dist3(me, q) < radius:
                    return True
        return False

    def _build_message(self, t: float, tau: float, mode: str, action_kind: str) -> Optional[Any]:
        """Builds a compact positional list `[st, u_tenths, rc_idx, zn, ob_idx]` (<= 64 B)."""
        rc_idx: List[int] = []
        if self._rc_ttl:
            rc_list = sorted(self._rc_ttl)[:2]
            rc_idx = [self._c2i[c] for c in rc_list if c in self._c2i]
            for c in rc_list:
                self._rc_ttl[c] -= 1
                if self._rc_ttl[c] <= 0:
                    del self._rc_ttl[c]

        zn_list: List[List[int]] = []
        if self._zn_ttl:
            z = next(iter(self._zn_ttl))
            zn_list = [list(z)]
            self._zn_ttl[z] -= 1
            if self._zn_ttl[z] <= 0:
                del self._zn_ttl[z]

        ob_idx: List[int] = []
        if self._ob_ttl:
            ob_list = sorted(self._ob_ttl)[:2]
            ob_idx = [self._c2i[c] for c in ob_list if c in self._c2i]
            for c in ob_list:
                self._ob_ttl[c] -= 1
                if self._ob_ttl[c] <= 0:
                    del self._ob_ttl[c]

        st = 0
        u_tenths = 0
        if action_kind == "hold":
            gap = 1.0 if (self._last_mode != "return" or self._peer_near(t, tau, 350.0)) else 15.0
            if self._hold_streak <= 3 or t - self._last_hd_sent >= gap:
                st = 4 if self._last_mode == "return" else 1
                u_tenths = int(round(tau * 10.0))
                self._last_hd_sent = t
        elif mode == "return" or action_kind == "return":
            if self._rt_ttl > 0 or (t - self._last_rt_sent >= 5.0):
                st = 2
                u_tenths = int(round(tau * 10.0))
                self._last_rt_sent = t
                if self._rt_ttl > 0:
                    self._rt_ttl -= 1
        elif self._rs_ttl > 0:
            st = 3
            u_tenths = int(round(tau * 10.0))
            self._rs_ttl -= 1

        if st == 0 and not rc_idx and not zn_list and not ob_idx:
            return None

        payload: List[Any] = [st, u_tenths]
        if ob_idx:
            payload.extend([rc_idx or 0, zn_list or 0, ob_idx])
        elif zn_list:
            payload.extend([rc_idx or 0, zn_list])
        elif rc_idx:
            payload.append(rc_idx)
        return _pack_msg(payload)

    def step(self, obs: dict) -> Tuple[dict, Optional[dict]]:
        t = float(obs["t"])
        t_loss = float(obs["t_loss"])
        tau = float(obs["tau"])
        # Our own abort state: the sim's mode also reads "return" after an on-plan back-off.
        mode = self._last_mode

        if not self.pre_cut_init:
            self._init_pre_cut(t_loss)

        for c in obs.get("own_observed", ()):
            if c not in self.observed:
                self.observed.add(c)
            if c not in self._sent_obs:
                self._sent_obs.add(c)
                self._ob_ttl[c] = 4

        # Range-aware ob re-send: when an effector of `c` is within ~260 m on the plan, re-send `ob`.
        if self.is_scout and self._sent_obs:
            my_pos = obs["pos"]
            for c in self._sent_obs:
                if t - self._last_ob_near.get(c, -100.0) < 2.0:
                    continue
                for eff_id in self.peers_by_target.get(c, ()):
                    eff_clk = self.clocks[eff_id]
                    if t <= eff_clk.end and dist3(my_pos, eff_clk.position(t)) <= 260.0:
                        self._ob_ttl[c] = max(self._ob_ttl.get(c, 0), 2)
                        self._last_ob_near[c] = t
                        break

        # Anti-entropy backup: periodically relay one active `ob` every 8s for hop-by-hop delivery.
        if not self._ob_ttl and t - self._last_ae_t >= 8.0 and self.observed:
            active_obs = sorted(
                c for c in self.observed
                if any(t <= self.clocks[eid].end for eid in self.peers_by_target.get(c, ()))
            )
            if active_obs:
                pick = active_obs[self._ae_idx % len(active_obs)]
                self._ae_idx += 1
                self._ob_ttl[pick] = 1
                self._last_ae_t = t

        for ev in obs.get("sensed", ()):
            self._learn_sensed(ev)

        self._learn_inbox(obs.get("inbox", ()))
        if self._tgt_ob_t is None and self.target in self.observed:
            self._tgt_ob_t = t   # the observation ended at or before the first time we heard of it

        # Decide continue vs return.
        abort = mode == "return"
        wait = False
        if not abort and self._route_hits_known_zone(tau):
            abort = True

        if not abort and self.is_effector and self.target is not None:
            peers = self.peers_by_target.get(self.target, set())
            if self.target in self.reclassified or any(p in self.aborted_peers for p in peers if p != self.aircraft_id):
                # Reclassified target, or a co-effector aborted (group abort). On the plan we stay deconflicted, and a
                # pop-up zone never covers a planned position when it appears: stop only short of the target.
                abort = self.clock.end - tau <= STOP_S
            else:
                # R4 guard: never engage without a confirmed observation. Without one close to the target, wait
                # for a late scout while the delay and the target window allow, else abort.
                time_to_eng = self.clock.end - tau
                if not abort and time_to_eng <= 4.0:
                    if self.target not in self.observed:
                        win = self.scenario.contact_by_id()[self.target].window
                        if self._ob_wait_t is None:
                            self._ob_wait_t = t
                        if t - tau < OB_WAIT_MAX_S and (not win or t + time_to_eng <= win[1]):
                            wait = True
                        else:
                            abort = True
                    elif self._ob_wait_t is not None and self._tgt_ob_t is not None \
                            and t + time_to_eng < self._tgt_ob_t + self.rules.confirm_margin_s:
                        wait = True   # heard while waiting: that observation ended at most confirm_margin ago

        if abort and self._last_mode != "return":
            self._rt_ttl = 4
            self._last_mode = "return"

        if abort:
            # Hover instead of retracing the route against later traffic; back off only when in an on-plan peer's way.
            if self._blocking(t, tau) and not self._r8_conflict(t, tau, -1.0) and not self._back_hits_known_zone(tau):
                if self._hold_streak > 0:
                    self._rt_ttl = 3
                self._hold_streak = 0
                return {"kind": "return"}, self._build_message(t, tau, mode, "return")
            self._hold_streak += 1
            return {"kind": "hold"}, self._build_message(t, tau, mode, "hold")
        rate = 1.0
        action: dict = {"kind": "continue"}

        # After backing off for a lower-id peer, hold until it moves (or 20 s): resuming at once flip-flops, and a
        # lost hold after our resume makes it believe we fly on.
        if self._yield_to is not None:
            ys = self.peer_state.get(self._yield_to)
            if t - self._yield_t > 20.0 or ys is None or ys[2] != "hold" or t - ys[0] > 15.0:
                self._yield_to = None
        # R8 separation check.
        if wait or self._yield_to is not None or self._r8_conflict(t, tau, rate):
            # Deadlock breaker: held > 10 s and in the way of a lower-id peer -> back off along the route if clear.
            # Peers hear a plain hold at the tau we back off to (we only move away from it).
            blocked = self._blocking(t, tau, below=self.aircraft_id) if self._hold_streak >= 10 else None
            if blocked and not self._r8_conflict(t, tau, -1.0) and not self._back_hits_known_zone(tau):
                self._yield_to, self._yield_t = blocked, t
                return {"kind": "return"}, self._build_message(t, max(self.clock.start, tau - 1.0), mode, "hold")
            action = {"kind": "hold"}
            self._hold_streak += 1
        else:
            if self._hold_streak > 0:
                self._rs_ttl = 2
            self._hold_streak = 0

        msg = self._build_message(t, tau, mode, action["kind"])
        return action, msg

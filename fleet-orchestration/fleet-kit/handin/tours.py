"""Scout tours first: a fast team-orienteering model decides which scout observes which contacts and in which order.

The model is straight-line and approximate (observation reach, ground wait free, hover waits paid, dwell, windows,
battery with a margin); the exact routes, effectors and every rule are left to the planner's own builder, which
follows the tours as hints. Value of a contact: hostile = points minus its cheapest strike (c_eff + lambda x energy
of the nearest effectors that can arrive in its window), unknown = points. Objective: total value minus lambda x
scout energy.
"""
import math
import random
from typing import Dict, List, Optional

from fk.geometry import hdist
from fk.baseline import _detour, _length
from fk.model import EFFECTOR, HOSTILE, SCOUT, UNKNOWN

J_PER_WH = 3600.0
REACH = 0.8        # fraction of the observation radius the model credits (the exact point is chosen later)
BATTERY = 0.85     # fraction of the usable energy the model may plan (detours, climbs and speed-ups are not modelled)
SLACK_S = 6.0      # per-visit slack on time (climb, observation point placement)
LEVEL = 70.0       # cruise level of the distances (zones and protected areas below it are flown around)


class Model:
    def __init__(self, sc, skip=lambda c: False):
        self.sc = sc
        r = sc.rules
        self.r = r
        self.scouts = [a for a in sc.aircraft if a.type == SCOUT]
        effs = [a for a in sc.aircraft if a.type == EFFECTOR]
        self.sp = {}
        for s in self.scouts:
            p = s.power
            v = min(math.sqrt(p.p0_w / p.k_v), 0.95 * s.v_h_mps)
            self.sp[s.id] = (v, (p.p0_w + p.k_v * v * v) / v / J_PER_WH, p.p0_w / J_PER_WH,
                             p.e_climb_wh_per_m * 70.0)
        self._dc = {}
        self.value: Dict[str, float] = {}
        self.eng_by: Dict[str, float] = {}   # latest observation end that still lets the strike fit in the window
        self.contacts = {}
        for c in sc.contacts:
            if c.cls == UNKNOWN:
                self.value[c.id] = float(c.points)
                self.eng_by[c.id] = c.window[1] if c.window else sc.horizon_s
                self.contacts[c.id] = c
            elif c.cls == HOSTILE and c.needs and not skip(c):
                total, latest, ok = 0.0, c.window[1] if c.window else sc.horizon_s, True
                for sub, n in c.needs.items():
                    costs = []
                    for a in effs:
                        if a.subtype != sub:
                            continue
                        d = max(0.0, hdist(a.home, c.pos) - r.R_eng_m)
                        p = a.power
                        v = min(math.sqrt(p.p0_w / p.k_v), a.v_h_mps)
                        wh = d * (p.p0_w + p.k_v * v * v) / v / J_PER_WH
                        if wh <= 0.9 * a.usable_wh and d / a.v_h_mps <= latest:
                            costs.append(r.c_eff + r.lambda_e * wh)
                    if len(costs) < n:
                        ok = False
                        break
                    costs.sort()
                    total += sum(costs[:n])
                if ok and c.points - total > 0:
                    self.value[c.id] = c.points - total
                    self.eng_by[c.id] = latest - r.confirm_margin_s - 2.0 - 5.0 * sum(c.needs.values())
                    self.contacts[c.id] = c

    def d(self, a, b) -> float:
        """Horizontal flight distance from a to b at LEVEL around zones and protected areas (cached)."""
        key = (a, b) if a <= b else (b, a)
        got = self._dc.get(key)
        if got is None:
            path = _detour([(a[0], a[1], LEVEL), (b[0], b[1], LEVEL)], self.sc)
            got = _length(path) if path is not None else 1e9
            self._dc[key] = got
        return got

    def tour_cost(self, sid: str, seq: List[str]) -> Optional[float]:
        """Scout energy in Wh of visiting `seq` in order and coming home, or None if a window or the battery fails."""
        if not seq:
            return 0.0
        s = next(a for a in self.scouts if a.id == sid)
        v, e_m, hover, climb = self.sp[sid]
        reach = REACH * self.r.R_obs_m
        dwell = self.r.obs_dwell_s
        home = (s.home[0], s.home[1])
        pos = home
        legs = []
        for k, cid in enumerate(seq):
            c = self.contacts[cid]
            cp = (c.pos[0], c.pos[1])
            legs.append(max(0.0, self.d(pos, cp) - (reach if k == 0 else 2.0 * reach)))
            pos = cp
        back = max(0.0, self.d(pos, home) - reach)
        # schedule: depart as late as the first window allows (ground wait free), then wait in the air if early
        c0 = self.contacts[seq[0]]
        lo0 = c0.window[0] if c0.window else 0.0
        t = max(0.0, lo0 - legs[0] / v - SLACK_S)
        start = t
        wait = 0.0
        for cid, leg in zip(seq, legs):
            c = self.contacts[cid]
            lo = c.window[0] if c.window else 0.0
            arrive = t + leg / v + SLACK_S
            if arrive < lo:
                wait += lo - arrive
                arrive = lo
            end = arrive + dwell
            if end > self.eng_by[cid]:
                return None
            t = end
        t += back / v
        if t > self.sc.horizon_s:
            return None
        dist = sum(legs) + back
        wh = dist * e_m + (wait + dwell * len(seq)) * hover + climb
        if wh > BATTERY * s.usable_wh:
            return None
        return wh

    def solve(self, rng: random.Random, iters: int = 300, noise: float = 0.15) -> Dict[str, List[str]]:
        lam = self.r.lambda_e
        val = {cid: v * rng.uniform(1.0 - noise, 1.0 + noise) for cid, v in self.value.items()}
        tours: Dict[str, List[str]] = {s.id: [] for s in self.scouts}
        cost = {s.id: 0.0 for s in self.scouts}

        def insert_all(pool):
            pool = list(pool)
            while pool:
                best = None
                for cid in pool:
                    for sid, seq in tours.items():
                        for k in range(len(seq) + 1):
                            cand = seq[:k] + [cid] + seq[k:]
                            wh = self.tour_cost(sid, cand)
                            if wh is None:
                                continue
                            gain = val[cid] - lam * (wh - cost[sid])
                            if gain > 0 and (best is None or gain > best[0]):
                                best = (gain, cid, sid, cand, wh)
                if best is None:
                    return
                _, cid, sid, cand, wh = best
                tours[sid], cost[sid] = cand, wh
                pool.remove(cid)

        def objective():
            return sum(val[c] for seq in tours.values() for c in seq) - lam * sum(cost.values())

        insert_all(self.value)
        best_obj, best_tours = objective(), {k: list(v) for k, v in tours.items()}
        for _ in range(iters):
            # ruin: a random tour, or contacts near a random one; recreate by best insertion
            served = [c for seq in tours.values() for c in seq]
            if not served:
                break
            if rng.random() < 0.3:
                sid = rng.choice([s for s, q in tours.items() if q])
                removed = tours[sid]
                tours[sid], cost[sid] = [], 0.0
            else:
                pivot = self.contacts[rng.choice(served)]
                k = rng.randint(2, 6)
                removed = sorted(served, key=lambda c: hdist(self.contacts[c].pos, pivot.pos))[:k]
                for sid, seq in tours.items():
                    if any(c in removed for c in seq):
                        tours[sid] = [c for c in seq if c not in removed]
                        wh = self.tour_cost(sid, tours[sid])
                        if wh is None:  # a shorter tour can be infeasible in the model (reach credited per leg)
                            tours[sid], wh = [], 0.0
                        cost[sid] = wh
            unserved = [c for c in self.value if c not in {x for q in tours.values() for x in q}]
            insert_all(unserved)
            obj = objective()
            if obj > best_obj + 1e-9:
                best_obj, best_tours = obj, {k: list(v) for k, v in tours.items()}
            else:
                tours = {k: list(v) for k, v in best_tours.items()}
                cost = {k: (self.tour_cost(k, v) or 0.0) for k, v in tours.items()}
        return best_tours

"""Link-loss diagnosis: why does the policy lose points against the oracle?

Cases are generator scenarios + fleetkit.baseline.greedy_plan + fleetkit.linkloss.events.make_events
(the jury runs the policy on its own reference plans). The only verifier is the official code:
`sim.simulate` per run for the cause table, `score.sizing` for the grid (--sizing).

Each point lost against the oracle is put in one cause bucket:
  r4_delivered  effector returned for lack of an "ob" although a scout had completed the observation
  r4_not_done   effector returned for lack of an "ob" and no scout had completed it yet (scout late/dead)
  failure       an aircraft of the task was removed by a `failure` event
  energy        an aircraft of the task ran out of energy
  event_abort   reclassify or pop-up zone abort (sensed or heard)
  late_hold     everyone flew to the end but the task was missed after R8 holds
  other         none of the above
A run that fails loses its whole retention, bucketed as fail:<rule>.

    nice -n 19 python3 tools/linkloss_diag.py --policy handin/policy.py -o runs/b2-diag-before.json
    nice -n 19 python3 tools/linkloss_diag.py --policy handin/policy.py --sizing -o runs/b2-sizing.json
    nice -n 19 python3 tools/linkloss_diag.py --r8 -o runs/b2-r8-diag.json   # classify every R8 failure + mutual holds
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))

from fleetkit.baseline import greedy_plan  # noqa: E402
from fleetkit.generator import generate  # noqa: E402
from fleetkit.linkloss import score  # noqa: E402
from fleetkit.linkloss.events import make_events  # noqa: E402
from fleetkit.linkloss.policies import load_policy  # noqa: E402
from fleetkit.linkloss.sim import simulate  # noqa: E402
from fleetkit.geometry import dist3, hdist  # noqa: E402
from fleetkit.linkloss.sim import RouteClock  # noqa: E402
from fleetkit.model import EFFECTOR, HOSTILE, SCOUT, Scenario, parse_plan  # noqa: E402

DIAG_SETTINGS = [(250.0, c) for c in score.CAPACITIES] + [score.LEADERBOARD]
_CASES = {}
_POLICY = {}


def _seeds(text):
    if "-" in text:
        lo, hi = text.split("-", 1)
        return list(range(int(lo), int(hi) + 1))
    return [int(x) for x in text.split(",")]


def build_case(key):
    level, seed, ev_seed = key
    data = generate(level, seed)
    sc = Scenario.from_dict(data)
    plan = greedy_plan(sc)
    ev = make_events(sc, plan, ev_seed)
    orc = simulate(sc, plan, ev, oracle=True)
    return key, data, plan, ev, orc.points, sorted(orc.served)


def _case(key):
    data, plan, ev, v, served = _CASES[key]
    return Scenario.from_dict(data), plan, ev, v, served


def _init(cases, policy_path):
    _CASES.update(cases)
    _POLICY["base"] = load_policy(policy_path)


def _instrumented(base, log):
    """Subclass of the team Policy that records why and when each aircraft first turns back, and its holds."""

    r8 = log.get("_r8", False)

    class Probe(base):
        def step(self, obs):
            pre = self._reason(obs)
            t = float(obs["t"])
            if r8:
                heard = self.__dict__.setdefault("_heard", {})
                new = {m["from"] for m in obs.get("inbox", ()) if m["from"] not in heard}
                if new:   # copy on change only: the step list keeps a reference per step
                    heard = self._heard = dict(heard, **{a: t for a in new})
                self._culprits = ()
            action, msg = super().step(obs)
            rec = log.setdefault(self.aircraft_id, {"abort": None, "hold_s": 0})
            if action.get("kind") == "hold":
                rec["hold_s"] += 1
            wants_back = action.get("kind") == "return" or (r8 and getattr(self, "_prop", 1.0) < 0)
            if wants_back and rec["abort"] is None:   # r8: an aircraft that wants back but holds has aborted too
                rec["abort"] = (t, self._reason(obs) or pre or "unknown")
            if r8:
                ps = rec.get("_ps")
                if ps != self.peer_state:
                    ps = rec["_ps"] = dict(self.peer_state)
                rec.setdefault("steps", {})[int(round(t))] = (
                    float(obs["tau"]), getattr(self, "_prop", 1.0), action.get("kind"), ps, self._heard,
                    self._culprits)
            return action, msg

        def _r8_conflict(self, t, tau, rate):
            self._prop = rate
            hit = super()._r8_conflict(t, tau, rate)
            if hit and r8:   # which peers alone would trigger the hold (for the mutual-hold count)
                allc, me, cul = self.clocks, self.aircraft_id, []
                try:
                    for aid in allc:
                        if aid != me:
                            self.clocks = {me: allc[me], aid: allc[aid]}
                            if super()._r8_conflict(t, tau, rate):
                                cul.append(aid)
                finally:
                    self.clocks = allc
                self._culprits = tuple(cul)
            return hit

        def _reason(self, obs):
            tgt = getattr(self, "target", None)
            if obs["mode"] == "return":
                return "mode"
            try:
                if self._route_hits_known_zone(float(obs["tau"])):
                    return "zone"
            except Exception:
                pass
            if tgt is None:
                return None
            if tgt in getattr(self, "reclassified", ()):
                return "reclassify"
            peers = getattr(self, "peers_by_target", {}).get(tgt, set())
            if any(p in getattr(self, "aborted_peers", ()) for p in peers if p != self.aircraft_id):
                return "group"
            if tgt not in getattr(self, "observed", ()):
                return "r4"
            return None

    return Probe


def run_one(job):
    key, setting, comm_seed = job
    sc, plan, ev, v_oracle, oracle_served = _case(key)
    log = {}
    factory = _instrumented(_POLICY["base"], log)
    run = simulate(sc, plan, ev, factory, setting=setting, run_seed=comm_seed)
    ret = score.retention(run.points, bool(run.failed), v_oracle)
    causes = defaultdict(float)
    if run.failed:
        causes["fail:" + _fail_kind(run.failed[0])] = 1.0
    else:
        for cid in set(oracle_served) - set(run.served):
            causes[_classify(sc, run, ev, log, cid)] += sc.contact_by_id()[cid].points / v_oracle
    r4_aborts = [(a, r["abort"][0]) for a, r in log.items() if r["abort"] and r["abort"][1] == "r4"]
    return {"case": "%s-%d-e%d" % key, "setting": "%gx%g" % setting, "seed": comm_seed, "retention": ret,
            "failed": run.failed[:2], "msgs_per_min": run.messages_per_aircraft_per_min,
            "ms_per_call": 1000.0 * run.policy_seconds / max(1, run.policy_calls),
            "causes": dict(causes), "r4_aborts": r4_aborts,
            "aborts": {a: r["abort"] for a, r in log.items() if r["abort"]}}


R8_RE = re.compile(r"R8 \(separation\): (\S+) and (\S+) come within ([\d.]+) m .*around t = ([\d.]+) s")
WINDOW_S = 10
CLASSIFY_S = 3      # a side is stale if its belief was wrong at any decision step in the last CLASSIFY_S s
STALE_ERR_M = 20.0  # predicted-position error that counts as a wrong belief (half of d_sep)
MUTUAL_HOLD_S = 20


def _mode(rate):
    if rate is None:
        return "ended"
    return "return" if rate < 0 else ("hold" if rate == 0 else "route")


def run_one_r8(job):
    """One run with R8 logging: every R8 failure classified, plus mutual holds (B4 deadlock check)."""
    key, setting, comm_seed = job
    sc, plan, ev, v_oracle, _ = _case(key)
    log = {"_r8": True}
    trace = {}
    run = simulate(sc, plan, ev, _instrumented(_POLICY["base"], log), setting=setting, run_seed=comm_seed,
                   trace=trace)
    log.pop("_r8")
    rates = {int(round(t)): r for t, r in trace["rates"]}
    fails = [_r8_failure(sc, plan, log, rates, trace, m) for m in run.failed if R8_RE.search(m)]
    return {"case": "%s-%d-e%d" % key, "setting": "%gx%g" % setting, "seed": comm_seed,
            "retention": score.retention(run.points, bool(run.failed), v_oracle), "failed": run.failed[:3],
            "r8": fails, "mutual_holds": _mutual_holds(log),
            "aborts": {a: r["abort"] for a, r in log.items() if r["abort"]}}


def _belief(step, peer, t):
    """What `step`'s aircraft believed about `peer` at t: (mode, predicted tau or None), as Policy._peer_pos_at."""
    st = step[3].get(peer)
    if st is None or (st[2] == "hold" and t - st[0] > 15.0):
        return "route(default)", float(t)
    t_ref, tau_ref, mode = st
    dt = max(0.0, t - t_ref)
    return mode, {"return": tau_ref - dt, "hold": tau_ref, "route": tau_ref + dt}[mode]


def _side(sc, plan, log, rates, trace, me, other, ts):
    """One aircraft's view of the other at decision step ts."""
    mine, theirs = log.get(me, {}).get("steps", {}).get(ts), log.get(other, {}).get("steps", {}).get(ts)
    real = _mode(rates.get(ts - 1, {}).get(other))   # the latest the other's mode could be known
    if mine is None:
        return {"mode": _mode(rates.get(ts, {}).get(me)), "real_other": real, "missing": True}
    tau, prop, kind, _, heard, _ = mine
    bmode, pred = _belief(mine, other, ts)
    clocks = _clocks(sc, plan)
    err = None
    if theirs is not None:
        err = dist3(clocks[other].position(pred), clocks[other].position(theirs[0]))
    off_plan = prop < 0 or abs(tau - ts) >= 0.25
    tgt = log[me].get("target")
    exempt = False
    if tgt is not None and tgt == log.get(other, {}).get("target"):
        nxt = max(clocks[me].start, min(clocks[me].end, tau + prop))
        exempt = hdist(clocks[me].position(nxt), sc.contact_by_id()[tgt].pos) <= sc.rules.R_eng_m + 50.0
    believed = bmode.split("(")[0]
    return {"mode": _mode(rates.get(ts, {}).get(me)), "proposed": _mode(prop), "tau_lag": round(ts - tau, 1),
            "abort": log[me]["abort"], "heard_since_cut": heard.get(other), "belief": bmode, "real_other": real,
            "pos_err_m": None if err is None else round(err, 1),
            "stale": believed != real or (err is not None and err > STALE_ERR_M),
            "checked": not ((not off_plan and believed == "route") or exempt), "exempt": exempt}


def _r8_failure(sc, plan, log, rates, trace, text):
    a, b, dmin, tf = R8_RE.search(text).groups()
    s = int(float(tf))
    for c in (a, b):   # store targets once, for the R8 exemption
        r = log.setdefault(c, {"abort": None, "hold_s": 0})
        last = _clocks(sc, plan)[c].route.waypoints[-1]
        r["target"] = last.target if last.action == "engage" else None
    window = []
    for ts in range(s - WINDOW_S, s + 1):
        pa, pb = (log.get(c, {}).get("steps", {}).get(ts) for c in (a, b))
        d = None
        if pa is not None and pb is not None:
            ck = _clocks(sc, plan)
            d = round(dist3(ck[a].position(pa[0]), ck[b].position(pb[0])), 1)
        window.append({"t": ts, "dist_m": d, a: _side(sc, plan, log, rates, trace, a, b, ts),
                       b: _side(sc, plan, log, rates, trace, b, a, ts)})
    at = window[-1]
    sa, sb = at[a], at[b]
    recent = window[-1 - CLASSIFY_S:]
    stale = {c: any(w[c].get("stale") for w in recent) for c in (a, b)}
    if sa.get("missing") or sb.get("missing"):
        cls = "other"
    elif stale[a] or stale[b]:
        cls = "stale_belief"
    elif not sa["checked"] and not sb["checked"]:
        cls = "onplan_skip"
    else:
        cls = "both_known"
    why = {}
    for me, other in ((a, b), (b, a)):   # for a stale side: was the other's state news never sent, out of range or lost?
        if stale[me]:
            w = next(w for w in reversed(recent) if w[me].get("stale"))
            t0 = w["t"] - 1
            while t0 - 1 in rates and _mode(rates[t0 - 1].get(other)) == w[me]["real_other"]:
                t0 -= 1
            sent = {t for t, src, p, _ in trace["sent"]
                    if src == other and t0 <= t < w["t"] and isinstance(p, dict) and ({"rt", "hd", "rs"} & set(p))}
            links = [dl for t, src, dst, dl, _ in trace["links"] if src == other and dst == me and t in sent]
            why[me] = {"at": w["t"], "belief": w[me]["belief"], "other_was": w[me]["real_other"],
                       "pos_err_m": w[me]["pos_err_m"], "other_mode_since": t0, "state_msgs_sent": len(sent), "in_range": len(links),
                       "delivered": sum(links)}
    return {"pair": [a, b], "t": float(tf), "min_dist_m": float(dmin), "class": cls, "at": at, "stale": stale,
            "stale_why": why, "window": window}


def _mutual_holds(log):
    """Spans of >= MUTUAL_HOLD_S s where two aircraft both hold, each because of the other."""
    holds = defaultdict(set)   # (a, b) -> steps where a held because of b
    for a, r in log.items():
        for ts, st in r.get("steps", {}).items():
            if st[2] == "hold":
                for b in st[5]:
                    holds[(a, b)].add(ts)
    out = []
    for (a, b), ta in holds.items():
        if a < b:
            both = sorted(ta & holds.get((b, a), set()))
            start = prev = None
            for ts in both + [None]:
                if ts is None or prev is None or ts != prev + 1:
                    if start is not None and prev - start + 1 >= MUTUAL_HOLD_S:
                        last = max(max(log[a]["steps"]), max(log[b]["steps"]))
                        out.append([a, b, start, prev - start + 1, prev >= last])   # True: never released
                    start = ts
                prev = ts
    return out


_CLOCKS = {}


def _clocks(sc, plan):
    k = id(plan)
    if k not in _CLOCKS:
        routes, _ = parse_plan(plan)
        _CLOCKS.clear()
        _CLOCKS[k] = {a: RouteClock(r) for a, r in routes.items()}
    return _CLOCKS[k]


def r8_table(rows):
    out = {}
    for s in sorted({r["setting"] for r in rows}, key=lambda x: tuple(float(v) for v in x.split("x"))):
        rs = [r for r in rows if r["setting"] == s]
        fails = [f for r in rs for f in r["r8"]]
        first = [r["r8"][0]["class"] for r in rs if r["r8"]]
        out[s] = {"runs": len(rs), "failed_runs": sum(bool(r["failed"]) for r in rs),
                  "r8_runs": len(first), "r8_failures": len(fails),
                  "by_class": {c: sum(f["class"] == c for f in fails) for c in CLASSES},
                  "by_class_first_per_run": {c: first.count(c) for c in CLASSES},
                  "mutual_holds": sum(len(r["mutual_holds"]) for r in rs),
                  "runs_with_mutual_hold": sum(bool(r["mutual_holds"]) for r in rs),
                  "mutual_holds_never_released": sum(m[4] for r in rs for m in r["mutual_holds"])}
    return out


CLASSES = ("stale_belief", "both_known", "onplan_skip", "other")


def print_r8_table(tab):
    print("%-9s %4s %4s %5s  " % ("setting", "runs", "fail", "R8") + " ".join("%12s" % c for c in CLASSES)
          + "  mutual>=%ds (runs, never released)" % MUTUAL_HOLD_S)
    for s, c in tab.items():
        print("%-9s %4d %4d %5d  " % (s, c["runs"], c["failed_runs"], c["r8_failures"])
              + " ".join("%12d" % c["by_class"][k] for k in CLASSES)
              + "  %d (%d, %d)" % (c["mutual_holds"], c["runs_with_mutual_hold"], c["mutual_holds_never_released"]))


def _fail_kind(text):
    for k in ("R4", "R8", "R6", "reclassified", "policy error"):
        if k in text:
            return k
    return "other"


def _first_obs_end(run, target):
    ends = [end for c in run.crafts.values() if c.ac.type == SCOUT
            for k, _, end in c.obs_done if c.route.waypoints[k].target == target]
    return min(ends) if ends else None


def _classify(sc, run, ev, log, cid):
    crafts = run.crafts
    contact = sc.contact_by_id()[cid]
    if contact.cls == HOSTILE:
        team = [c for c in crafts.values() if c.ac.type == EFFECTOR
                and c.route.waypoints[-1].action == "engage" and c.route.waypoints[-1].target == cid]
    else:
        team = [c for c in crafts.values() if c.ac.type == SCOUT
                and any(w.action == "observe" and w.target == cid for w in c.route.waypoints)]
    if any(c.end_kind == "failed" for c in team):
        return "failure"
    if any(c.end_kind == "lost" for c in team):
        return "energy"
    roots = sorted((log[c.id]["abort"] for c in team if c.id in log and log[c.id]["abort"]
                    and log[c.id]["abort"][1] not in ("group", "mode")), key=lambda x: x[0])
    if roots:
        t_ab, why = roots[0]
        if why == "r4":
            end = _first_obs_end(run, cid)
            return "r4_delivered" if end is not None and end <= t_ab - sc.rules.confirm_margin_s else "r4_not_done"
        if why in ("zone", "reclassify"):
            return "event_abort"
        return "other"
    if any(c.id in log and log[c.id]["abort"] for c in team):
        return "other"   # group abort with no recorded root: the peer turned back pre-cut
    if any(log.get(c.id, {}).get("hold_s", 0) > 0 for c in team):
        return "late_hold"
    return "other"


def table(rows):
    cells = defaultdict(list)
    for r in rows:
        cells[r["setting"]].append(r)
    out = {}
    for s, rs in cells.items():
        n = len(rs)
        agg = defaultdict(float)
        for r in rs:
            for k, v in r["causes"].items():
                agg[k] += v / n
        out[s] = {"runs": n, "retention": sum(r["retention"] for r in rs) / n,
                  "failed_runs": sum(bool(r["failed"]) for r in rs),
                  "msgs_per_min": sum(r["msgs_per_min"] for r in rs) / n,
                  "loss_by_cause": dict(sorted(agg.items(), key=lambda kv: -kv[1]))}
    return out


def print_table(tab):
    keys = sorted({k for c in tab.values() for k in c["loss_by_cause"]})
    print("%-9s %5s %6s %4s  " % ("setting", "runs", "ret", "fail") + " ".join("%12s" % k for k in keys))
    for s in sorted(tab, key=lambda x: tuple(float(v) for v in x.split("x"))):
        c = tab[s]
        print("%-9s %5d %6.3f %4d  " % (s, c["runs"], c["retention"], c["failed_runs"])
              + " ".join("%12.3f" % c["loss_by_cause"].get(k, 0.0) for k in keys))


def _sizing_cell(args):
    r, cap, seeds = args
    keys = sorted(_CASES)
    cases = [_case(k)[:3] for k in keys]
    res = score.sizing(cases, _POLICY["base"], seeds=seeds, ranges=[r], capacities=[cap])
    return res["cells"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default=str(KIT / "handin" / "policy.py"))
    ap.add_argument("--levels", default="L1,L2,L3,L4")
    ap.add_argument("--seeds", default="0-4")
    ap.add_argument("--events-seed", type=int, default=1)
    ap.add_argument("--comm-seeds", type=int, default=score.SEEDS)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--sizing", action="store_true", help="the full official sizing grid instead of the cause table")
    ap.add_argument("--r8", action="store_true", help="classify every R8 failure and count mutual holds")
    ap.add_argument("--settings", help="e.g. 250x50,1000x200 (default: the cause-table settings)")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    os.nice(max(0, 19 - os.nice(0)))   # low priority: another session times its runs
    keys = [(lv, s, a.events_seed) for lv in a.levels.split(",") for s in _seeds(a.seeds)]
    t0 = time.time()
    with Pool(a.workers) as pool:
        cases = {}
        for key, data, plan, ev, v, served in pool.imap_unordered(_build_safe, keys):
            if data is not None:
                cases[key] = (data, plan, ev, v, served)
            else:
                print("skip case", key, "-", v, file=sys.stderr)
    print("%d cases built in %.0fs" % (len(cases), time.time() - t0), file=sys.stderr)
    with Pool(a.workers, initializer=_init, initargs=(cases, a.policy)) as pool:
        if a.sizing:
            cells = {}
            for c in pool.imap_unordered(_sizing_cell, [(r, cap, a.comm_seeds) for r in score.RANGES
                                                         for cap in score.CAPACITIES]):
                cells.update(c)
            # same aggregation as score.sizing
            meets = sum(1 for c in cells.values() if c["meets"])
            frontier = {}
            for r in score.RANGES:
                ok = [cap for cap in score.CAPACITIES if cells["%gx%g" % (r, cap)]["meets"]]
                frontier["%g" % r] = min(ok) if ok else None
            result = {"cells": cells, "sizing_score": meets / len(cells), "frontier": frontier}
            for k in sorted(cells, key=lambda x: tuple(float(v) for v in x.split("x"))):
                c = cells[k]
                print("%-9s ret %.3f fail %d/%d msgs %.2f s_loss %.3f %s" % (
                    k, c["retention"], c["failures"], c["runs"], c["messages_per_aircraft_per_min"], c["s_loss"],
                    "MEETS" if c["meets"] else ""))
            print("sizing score %.2f frontier %s" % (result["sizing_score"], frontier))
        else:
            settings = DIAG_SETTINGS if not a.settings else [
                tuple(float(v) for v in x.split("x")) for x in a.settings.split(",")]
            jobs = [(k, s, seed) for k in sorted(cases) for s in settings for seed in range(a.comm_seeds)]
        if a.r8:
            rows = list(pool.imap_unordered(run_one_r8, jobs, chunksize=4))
            result = {"table": r8_table(rows), "runs": rows}
            print_r8_table(result["table"])
        elif not a.sizing:
            rows = list(pool.imap_unordered(run_one, jobs, chunksize=4))
            result = {"table": table(rows), "runs": rows}
            print_table(result["table"])
    result["meta"] = {"policy": a.policy, "cases": ["%s-%d-e%d" % k for k in sorted(cases)],
                      "comm_seeds": a.comm_seeds, "wall_s": round(time.time() - t0, 1)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(result, indent=1, default=str))
    print("wrote", a.out, "in %.0fs" % (time.time() - t0), file=sys.stderr)


def _build_safe(key):
    try:
        return build_case(key)
    except Exception as exc:   # make_events may find no feasible event set for a case
        return key, None, None, None, "%s: %s" % (type(exc).__name__, exc), None


if __name__ == "__main__":
    main()

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
"""
from __future__ import annotations

import argparse
import json
import os
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
from fleetkit.model import EFFECTOR, HOSTILE, SCOUT, Scenario  # noqa: E402

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

    class Probe(base):
        def step(self, obs):
            pre = self._reason(obs)
            action, msg = super().step(obs)
            rec = log.setdefault(self.aircraft_id, {"abort": None, "hold_s": 0})
            if action.get("kind") == "hold":
                rec["hold_s"] += 1
            if action.get("kind") == "return" and rec["abort"] is None:
                rec["abort"] = (float(obs["t"]), self._reason(obs) or pre or "unknown")
            return action, msg

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
            jobs = [(k, s, seed) for k in sorted(cases) for s in DIAG_SETTINGS for seed in range(a.comm_seeds)]
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

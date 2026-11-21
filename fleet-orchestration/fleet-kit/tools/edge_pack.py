"""Edge pack: degenerate scenarios the planner must survive (a crash, a timeout or an invalid plan scores 0).

Each case edits a normal scenario (L2 seed 0) into an odd one: no scout, one aircraft, closed time windows,
unreachable contacts, impossible needs, dead batteries... The planner is run the way the jury runs it
(subprocess, minimal environment); the plan must be written, VALID for the kit scorer, and on time.
A valid empty plan (score 0) is a pass: the pack checks safety, not score.

From fleet-kit/:
    python3 tools/edge_pack.py                    # every case, 2 s internal budget each
    python3 tools/edge_pack.py --only no_scouts one_scout --budget 5
    python3 tools/edge_pack.py --list
Exit code 1 if any case crashes, times out, writes no plan or writes an invalid plan.
Python 3.9, standard library only.
"""
import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
import time
from typing import Callable, Dict, List

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import Scenario  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402

PLANNER = os.path.join(KIT, "handin", "planner.py")
LIMIT_S = 60.0


def base() -> dict:
    return generate("L2", 0)


def _hostiles(d):
    return [c for c in d["contacts"] if c["class"] == "hostile"]


def _unknowns(d):
    return [c for c in d["contacts"] if c["class"] == "unknown"]


def _keep(d, pred):
    d["aircraft"] = [a for a in d["aircraft"] if pred(a)]
    return d


def _is_scout(a):
    return a["type"] == "scout"


# ---- fleet ---------------------------------------------------------------------------------------------------
def no_scouts(d):
    return _keep(d, lambda a: not _is_scout(a))


def no_effectors(d):
    return _keep(d, _is_scout)


def no_lights(d):
    return _keep(d, lambda a: a.get("subtype") != "light")


def no_heavies(d):
    return _keep(d, lambda a: a.get("subtype") != "heavy")


def one_scout(d):
    d["aircraft"] = [a for a in d["aircraft"] if _is_scout(a)][:1]
    return d


def one_light(d):
    d["aircraft"] = [a for a in d["aircraft"] if a.get("subtype") == "light"][:1]
    return d


def one_heavy(d):
    d["aircraft"] = [a for a in d["aircraft"] if a.get("subtype") == "heavy"][:1]
    return d


def one_scout_one_light(d):
    d["aircraft"] = ([a for a in d["aircraft"] if _is_scout(a)][:1]
                     + [a for a in d["aircraft"] if a.get("subtype") == "light"][:1])
    return d


def batteries_empty(d):
    for a in d["aircraft"]:
        a["battery_pct"] = 0.0
    return d


def batteries_tiny(d):
    for a in d["aircraft"]:
        a["battery_pct"] = 1.0
    return d


def no_aircraft(d):
    d["aircraft"] = []
    return d


# ---- time windows --------------------------------------------------------------------------------------------
def _windows(d, fn):
    for c in d["contacts"]:
        if c["class"] in ("hostile", "unknown") and c.get("window_s"):
            c["window_s"] = fn(c["window_s"])
    return d


def window_zero_width(d):
    return _windows(d, lambda w: [w[0], w[0]])


def window_inverted(d):
    return _windows(d, lambda w: [w[1], w[0]])


def window_shorter_than_dwell(d):
    return _windows(d, lambda w: [w[0], w[0] + 5.0])


def window_unreachable_early(d):
    return _windows(d, lambda w: [0.0, 1.0])


def window_after_horizon(d):
    return _windows(d, lambda w: [d["horizon_s"] + 10.0, d["horizon_s"] + 100.0])


def window_negative(d):
    return _windows(d, lambda w: [-50.0, w[1]])


def window_unknown_none(d):
    for c in _unknowns(d):
        c["window_s"] = None
    return d


def window_hostile_none(d):
    for c in _hostiles(d):
        c["window_s"] = None
    return d


# ---- contacts ------------------------------------------------------------------------------------------------
def needs_more_than_fleet(d):
    for c in _hostiles(d):
        c["engage_needs"] = {"light": 999, "heavy": 999}
    return d


def needs_empty(d):
    for c in _hostiles(d):
        c["engage_needs"] = {}
    return d


def needs_unknown_subtype(d):
    for c in _hostiles(d):
        c["engage_needs"] = {"medium": 1}
    return d


def needs_zero(d):
    for c in _hostiles(d):
        c["engage_needs"] = {"light": 0}
    return d


def contacts_on_a_base(d):
    home = d["aircraft"][0]["home"]
    for c in d["contacts"]:
        if c["class"] in ("hostile", "unknown"):
            c["pos"] = list(home)
    return d


def contacts_stacked(d):
    target = list(_hostiles(d)[0]["pos"])
    for c in d["contacts"]:
        if c["class"] in ("hostile", "unknown"):
            c["pos"] = list(target)
    return d


def contacts_inside_a_zone(d):
    z = d["zones"][0]
    for c in d["contacts"]:
        if c["class"] in ("hostile", "unknown"):
            c["pos"] = [z["center"][0], z["center"][1], 0.0]
    return d


def contacts_very_far(d):
    for c in d["contacts"]:
        if c["class"] in ("hostile", "unknown"):
            c["pos"] = [1.0e6, 1.0e6, 0.0]
    return d


def hostiles_next_to_civilians(d):
    """Every hostile 20 m from a civilian: R7 forbids engaging all of them."""
    civ = [c for c in d["contacts"] if c["class"] == "civilian"]
    if not civ:
        civ = [{"id": "CX", "class": "civilian", "pos": [500.0, 500.0, 0.0], "points": 0, "window_s": None}]
        d["contacts"].append(civ[0])
    for c in _hostiles(d):
        c["pos"] = [civ[0]["pos"][0] + 20.0, civ[0]["pos"][1], 0.0]
    return d


def zero_points(d):
    for c in d["contacts"]:
        if c["class"] in ("hostile", "unknown"):
            c["points"] = 0.0
    return d


def negative_points(d):
    for c in d["contacts"]:
        if c["class"] in ("hostile", "unknown"):
            c["points"] = -10.0
    return d


def only_unknowns(d):
    d["contacts"] = [c for c in d["contacts"] if c["class"] != "hostile"]
    return d


def only_hostiles(d):
    d["contacts"] = [c for c in d["contacts"] if c["class"] != "unknown"]
    return d


def no_contacts(d):
    d["contacts"] = []
    return d


def only_friendlies(d):
    d["contacts"] = [c for c in d["contacts"] if c["class"] in ("friendly", "civilian")]
    return d


# ---- world ---------------------------------------------------------------------------------------------------
def horizon_tiny(d):
    d["horizon_s"] = 5.0
    return d


def horizon_long(d):
    d["horizon_s"] = 100000.0
    return d


def zone_over_every_base(d):
    d["zones"] = [{"id": "ZB%d" % i, "center": list(a["home"][:2]), "radius_m": 300.0, "top_m": 150.0}
                  for i, a in enumerate(d["aircraft"][:1])] or d["zones"]
    return d


def no_zones(d):
    d["zones"] = []
    return d


CASES = {f.__name__: f for f in (
    no_scouts, no_effectors, no_lights, no_heavies, no_aircraft, one_scout, one_light, one_heavy,
    one_scout_one_light, batteries_empty, batteries_tiny,
    window_zero_width, window_inverted, window_shorter_than_dwell, window_unreachable_early,
    window_after_horizon, window_negative, window_unknown_none, window_hostile_none,
    needs_more_than_fleet, needs_empty, needs_unknown_subtype, needs_zero,
    contacts_on_a_base, contacts_stacked, contacts_inside_a_zone, contacts_very_far,
    hostiles_next_to_civilians, zero_points, negative_points,
    only_unknowns, only_hostiles, no_contacts, only_friendlies,
    horizon_tiny, horizon_long, zone_over_every_base, no_zones,
)}  # type: Dict[str, Callable[[dict], dict]]


def build(name: str) -> dict:
    return CASES[name](copy.deepcopy(base()))


def run_case(name: str, planner: str = PLANNER, budget: str = "2", workers: str = "1", timeout: float = LIMIT_S):
    """Runs the planner on one case; returns a dict(ok, why, score, time)."""
    data = build(name)
    with tempfile.TemporaryDirectory() as tmp:
        scen, out = os.path.join(tmp, "scenario.json"), os.path.join(tmp, "plan.json")
        with open(scen, "w") as f:
            json.dump(data, f)
        env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": KIT, "PYTHONDONTWRITEBYTECODE": "1",
               "HOME": tmp, "PLANNER_BUDGET_S": budget, "PLANNER_WORKERS": workers}
        t0 = time.time()
        try:
            proc = subprocess.run([sys.executable, planner, scen, out], env=env, capture_output=True,
                                  text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"ok": False, "why": "timeout > %.0f s" % timeout, "score": 0.0, "time": time.time() - t0}
        dt = time.time() - t0
        if proc.returncode != 0:
            return {"ok": False, "why": "exit %d: %s" % (proc.returncode, proc.stderr.strip()[-120:]),
                    "score": 0.0, "time": dt}
        if not os.path.exists(out):
            return {"ok": False, "why": "no plan written", "score": 0.0, "time": dt}
        try:
            with open(out) as f:
                plan = json.load(f)
            res = evaluate(Scenario.from_dict(data), plan)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "why": "unreadable plan or scenario: %s" % exc, "score": 0.0, "time": dt}
        if not res.valid:
            return {"ok": False, "why": "invalid: " + "; ".join(str(v) for v in res.violations[:2]),
                    "score": 0.0, "time": dt}
        return {"ok": True, "why": "", "score": res.score, "time": dt}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", default=None, help="case names (see --list)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--budget", default="2", help="planner internal budget in seconds (PLANNER_BUDGET_S)")
    ap.add_argument("--workers", default="1")
    ap.add_argument("--planner", default=PLANNER)
    args = ap.parse_args()
    if args.list:
        print("\n".join(CASES))
        return
    names = args.only or list(CASES)
    bad = 0
    for name in names:
        r = run_case(name, args.planner, args.budget, args.workers)
        bad += 0 if r["ok"] else 1
        print("%s %-28s score %8.1f  %5.1fs  %s" % ("OK " if r["ok"] else "BAD", name, r["score"], r["time"], r["why"]),
              flush=True)
    print("--- %d cases, %d failing" % (len(names), bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

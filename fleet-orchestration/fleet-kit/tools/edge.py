"""Edge-case pack: absurd or degenerate scenarios the planner must survive.

Pass = exit 0, a plan file, valid under the OFFICIAL scorer (an empty plan is fine), score never negative.
The planner is run like the jury: fresh copy of handin/, subprocess, clean environment.
Used by tests/test_edge.py (fast, CI) and runnable by hand from fleet-kit/:
    python3 tools/edge.py [--budget 3] [--workers 2] [--python /usr/bin/python3] [name ...]
"""
import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import Scenario  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402

HANDIN = os.path.join(KIT, "handin")


def run_handin(scenario, budget=3, workers=2, python=None, timeout=60):
    """Runs `planner.py scenario plan` from a copy of handin/. Returns (code, seconds, plan text or None, stderr tail)."""
    tmp = tempfile.mkdtemp(prefix="edge_")
    try:
        team = os.path.join(tmp, "team")
        shutil.copytree(HANDIN, team, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        scen, plan = os.path.join(tmp, "scenario.json"), os.path.join(tmp, "plan.json")
        with open(scen, "w") as f:
            json.dump(scenario, f)
        env = {"PATH": os.environ.get("PATH", ""), "HOME": tmp, "PYTHONDONTWRITEBYTECODE": "1",
               "PYTHONPATH": KIT, "PLANNER_BUDGET_S": str(budget), "PLANNER_WORKERS": str(workers)}
        if os.name == "nt":  # Windows needs these to start a process at all
            env.update({k: os.environ[k] for k in ("SYSTEMROOT", "TEMP", "TMP") if k in os.environ})
        t0 = time.time()
        proc = subprocess.run([python or sys.executable, "planner.py", scen, plan], env=env, cwd=team,
                              capture_output=True, text=True, timeout=timeout)
        dt = time.time() - t0
        text = None
        if os.path.exists(plan):
            with open(plan) as f:
                text = f.read()
        return proc.returncode, dt, text, proc.stderr[-400:]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def judge(scenario, code, text, err):
    """Returns '' if the run passes, else a one-line reason."""
    if code != 0:
        return "exit %s: %s" % (code, err.strip())
    if text is None:
        return "no plan.json written"
    if "planner: " in err:  # main() swallows exceptions and exits 0 with the last kept plan: a hidden crash
        return "swallowed exception: %s" % err.strip().splitlines()[-1]
    try:
        plan = json.loads(text)
        res = evaluate(Scenario.from_dict(scenario), plan)
    except Exception as exc:  # the scorer itself choking on the plan or the scenario is a finding too
        return "scorer failed: %s: %s" % (type(exc).__name__, exc)
    if not res.valid:
        return "invalid plan: %s" % "; ".join(str(v) for v in res.violations[:2])
    if res.score < 0:
        return "negative score %.1f" % res.score
    return ""


# ---- the cases: name -> builder() returning a scenario dict --------------------------------------

def base():
    return copy.deepcopy(generate("L2", 0))


def _no_type(pred):
    d = base()
    d["aircraft"] = [a for a in d["aircraft"] if not pred(a)]
    return d


def r7_all_blocked():
    d = base()
    extra = []
    for c in d["contacts"]:
        if c["class"] == "hostile":  # a civilian 50 m away: inside collateral_radius_m for every hostile
            extra.append({"id": "X%s" % c["id"], "class": "civilian", "pos": [c["pos"][0] + 50, c["pos"][1], 0.0],
                          "window_s": None})
    d["contacts"] += extra
    return d


def windows_closed():
    d = base()
    for c in d["contacts"]:
        if c.get("window_s"):
            c["window_s"] = [0.0, 1.0]  # closes before anything can fly 1.5 km
    return d


def horizon_120():
    d = base()
    d["horizon_s"] = 120.0
    return d


def one_aircraft():
    d = base()
    d["aircraft"] = [a for a in d["aircraft"] if a["id"] == "L01"]
    return d


def battery_5():
    d = base()
    for a in d["aircraft"]:
        a["battery_pct"] = 5.0
    return d


def unknown_level():
    d = base()
    d["level"] = "L9"
    return d


def extra_keys():
    d = base()
    d["surprise"] = {"a": 1}
    d["rules"]["new_rule_m"] = 12.0
    d["aircraft"][0]["colour"] = "red"
    d["contacts"][0]["note"] = "x"
    d["zones"] and d["zones"][0].update({"label": "z"})
    return d


def events_nonempty():
    d = base()
    d["events"] = [{"t": 100.0, "type": "link_loss", "aircraft": d["aircraft"][0]["id"]},
                   {"t": 200.0, "type": "something_new"}]
    return d


def need_zero():
    d = base()
    hs = [c for c in d["contacts"] if c["class"] == "hostile"]
    hs[0]["engage_needs"] = {"light": 0}
    hs[1]["engage_needs"] = {"light": 0, "heavy": 1}
    return d


def need_unknown_subtype_null_window():
    d = base()
    hs = [c for c in d["contacts"] if c["class"] == "hostile"]
    hs[0]["engage_needs"] = {"medium": 1}
    hs[1]["window_s"] = None
    return d


def no_check_L2():
    return generate("L2", 1, ensure_feasible=False)


def no_check_L4():
    return generate("L4", 7, ensure_feasible=False)


CASES = {
    "no_scout": lambda: _no_type(lambda a: a["type"] == "scout"),
    "no_light": lambda: _no_type(lambda a: a.get("subtype") == "light"),
    "no_heavy": lambda: _no_type(lambda a: a.get("subtype") == "heavy"),
    "no_effector": lambda: _no_type(lambda a: a["type"] == "effector"),
    "r7_all_blocked": r7_all_blocked,
    "windows_closed": windows_closed,
    "horizon_120": horizon_120,
    "one_aircraft": one_aircraft,
    "battery_5": battery_5,
    "unknown_level": unknown_level,
    "extra_keys": extra_keys,
    "events_nonempty": events_nonempty,
    "need_zero": need_zero,
    "need_unknown_subtype_null_window": need_unknown_subtype_null_window,
    "no_check_L2": no_check_L2,
    "no_check_L4": no_check_L4,
}


def run_case(name, budget=3, workers=2, python=None):
    """Returns (reason or '', seconds)."""
    scenario = CASES[name]()
    code, dt, text, err = run_handin(scenario, budget, workers, python)
    return judge(scenario, code, text, err), dt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*", help="cases to run (default: all)")
    ap.add_argument("--budget", type=float, default=3)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--python", default=None, help="interpreter for the planner (default: this one)")
    args = ap.parse_args()
    bad = 0
    for name in args.names or CASES:
        reason, dt = run_case(name, args.budget, args.workers, args.python)
        bad += bool(reason)
        print("%s %-36s %5.1fs  %s" % ("BAD" if reason else "OK ", name, dt, reason))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

"""Edge pack: degenerate scenarios the planner must survive (a crash, a timeout or an invalid plan scores 0).

Each case edits a normal scenario (L2 seed 0) into an odd one: no scout, one aircraft, closed time windows,
unreachable contacts, impossible needs, dead batteries... The planner is run the way the jury runs it
(subprocess, minimal environment); the plan must be written, VALID for the kit scorer, and on time.
Three checks per case:
  1. safety: plan written, VALID for the kit scorer, on time (an empty plan is valid);
  2. no swallowed crash: the planner catches its own errors and falls back to a valid empty plan, so a hidden
     crash looks like a pass; any `planner: ...` line or traceback on stderr is a failure;
  3. expectation (EXPECT): "positive" = the planner must score > 0 (something is servable, giving up is a bug);
     "zero" = it must score 0 (provably nothing servable: a score > 0 would mean a hole in the validator).
Cases without an EXPECT entry are only checked for safety.

From fleet-kit/:
    python3 tools/edge_pack.py                    # every case, 2 s internal budget each
    python3 tools/edge_pack.py --only no_scouts one_scout --budget 5
    python3 tools/edge_pack.py --list
Exit code 1 if any case crashes, times out, writes no plan or writes an invalid plan.
Python 3.9, standard library only.
"""
import argparse
import copy
import functools
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


# ---- exact boundaries (where `<` versus `<=` bugs live; tolerance of the kit: EPS = 1e-6) -----------------------
DWELL_S = 20.0  # rules.obs_dwell_s of every scenario


def window_exactly_dwell(d):
    """Every window is exactly one observation long: servable only by being on station at its first second."""
    return _windows(d, lambda w: [w[0], w[0] + DWELL_S])


def window_just_below_dwell(d):
    """1 ms shorter than the dwell: no observation can fit (R9), so nothing is servable."""
    return _windows(d, lambda w: [w[0], w[0] + DWELL_S - 0.001])


def window_ends_at_horizon(d):
    return _windows(d, lambda w: [w[0], d["horizon_s"]])


def _civilian(d):
    civ = [c for c in d["contacts"] if c["class"] == "civilian"]
    if not civ:
        civ = [{"id": "CX", "class": "civilian", "pos": [500.0, 500.0, 0.0], "points": 0, "window_s": None}]
        d["contacts"].append(civ[0])
    return civ[0]


def r7_exactly_200(d):
    """Every hostile exactly on the collateral radius of a civilian (R7 is strict: 200.0 m is allowed)."""
    civ = _civilian(d)
    for c in _hostiles(d):
        c["pos"] = [civ["pos"][0] + 200.0, civ["pos"][1], 0.0]
    return d


def r7_just_inside(d):
    """Every hostile 1 mm inside the collateral radius: engaging any of them breaks R7."""
    civ = _civilian(d)
    for c in _hostiles(d):
        c["pos"] = [civ["pos"][0] + 199.999, civ["pos"][1], 0.0]
    return d


def homes_identical(d):
    """Every aircraft starts on the same point: the planner must stagger the departures (R8)."""
    home = list(d["aircraft"][0]["home"])
    for a in d["aircraft"]:
        a["home"] = list(home)
    return d


def needs_exactly_the_fleet(d):
    """One hostile needs every light and every heavy of the fleet (R10 all-or-nothing, no spare)."""
    lights = sum(1 for a in d["aircraft"] if a.get("subtype") == "light")
    heavies = sum(1 for a in d["aircraft"] if a.get("subtype") == "heavy")
    _hostiles(d)[0]["engage_needs"] = {"light": lights, "heavy": heavies}
    return d


@functools.lru_cache(maxsize=1)
def _baseline_energy_wh():
    """Energy of every aircraft in the kit baseline plan for the base scenario."""
    from fleetkit.baseline import greedy_plan
    from fleetkit.energy import route_energy_wh
    from fleetkit.model import parse_plan
    sc = Scenario.from_dict(base())
    routes, _ = parse_plan(greedy_plan(sc))
    by_id = sc.aircraft_by_id()
    return {aid: route_energy_wh(r.waypoints, by_id[aid]) for aid, r in routes.items()}


def battery_exact_baseline(d):
    """Every aircraft the baseline uses has exactly the energy the baseline spends: no margin at all (R3)."""
    for a in d["aircraft"]:
        need = _baseline_energy_wh().get(a["id"])
        if need:
            a["capacity_wh"] = need * (1.0 + 1e-12)
            a["battery_pct"] = 100.0
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
    window_exactly_dwell, window_just_below_dwell, window_ends_at_horizon, r7_exactly_200, r7_just_inside,
    homes_identical, needs_exactly_the_fleet, battery_exact_baseline,
)}  # type: Dict[str, Callable[[dict], dict]]

# What each case must score (see the module docstring). Only cases where the answer is evident are listed.
# "zero": provably nothing servable (no scout, no aircraft, no energy, no window that fits a dwell, nothing
# reachable, no point to win), so any score above 0 would reveal a hole in the validator.
ZERO = ("no_scouts", "no_aircraft", "batteries_empty", "no_contacts", "only_friendlies", "zero_points",
        "negative_points", "window_zero_width", "window_inverted", "window_shorter_than_dwell",
        "window_unreachable_early", "window_just_below_dwell", "window_after_horizon", "horizon_tiny",
        "contacts_very_far")
# "positive": the normal scenario still contains something a reduced fleet can serve (measured on L2 seed 0,
# stable over repeated runs), so an empty answer means the planner gave up.
POSITIVE = ("no_effectors", "no_lights", "no_heavies", "one_scout", "one_scout_one_light", "window_negative",
            "window_unknown_none", "window_hostile_none", "needs_more_than_fleet", "needs_unknown_subtype",
            "contacts_on_a_base", "contacts_stacked", "hostiles_next_to_civilians", "only_unknowns",
            "only_hostiles", "horizon_long", "no_zones")
EXPECT = dict([(n, "zero") for n in ZERO] + [(n, "positive") for n in POSITIVE])  # type: Dict[str, str]
assert set(EXPECT) <= set(CASES), sorted(set(EXPECT) - set(CASES))


def judge_expectation(name: str, score: float) -> str:
    """Returns "" when the score meets the case's expectation, else the reason it does not."""
    want = EXPECT.get(name)
    if want == "positive" and not score > 1e-6:
        return "expected a positive score, the planner gave up (score %.1f)" % score
    if want == "zero" and score > 1e-6:
        return "expected 0 (nothing is servable) but the plan scores %.1f: hole in the validator?" % score
    return ""


def swallowed_error(stderr: str) -> str:
    """Returns the internal error the planner printed before falling back to a safe plan, or ""."""
    for line in stderr.splitlines():
        if line.startswith("planner:") or line.startswith("Traceback"):
            return line.strip()[:160]
    return ""


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
        hidden = swallowed_error(proc.stderr)
        if hidden:
            return {"ok": False, "why": "internal error swallowed by the safety net: " + hidden,
                    "score": res.score, "time": dt}
        miss = judge_expectation(name, res.score)
        if miss:
            return {"ok": False, "why": miss, "score": res.score, "time": dt}
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

"""Scaling study: how the hand-in planner behaves when the fleet grows beyond the official L4 (100 aircraft).

Usage, from fleet-kit/:
    python3 tools/scaling.py --factors 1 2 3 --seeds 0-1 [--base]
The generator only knows L1 to L4; we add synthetic levels by scaling L4 (every count times the factor, the
area times the square root of the factor so that the density stays the same). Each scenario runs through
planner.py in a subprocess with the evaluation's 60 s limit; the plan is validated with the kit's scorer.
Prints one line per run: aircraft, contacts, validity, score, wall time (and the baseline planner's, if asked).
"""
import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit import generator  # noqa: E402
from fleetkit.model import Scenario  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402

COUNTS = ("scouts", "light", "heavy", "hostile", "unknown", "friendly", "civilian", "zones")


def scaled_level(factor: int) -> dict:
    """L4 with every count multiplied by `factor` and the area scaled to keep the density."""
    level = dict(generator.LEVELS["L4"])
    for key in COUNTS:
        level[key] = int(level[key] * factor)
    level["area"] = level["area"] * math.sqrt(factor)
    return level


def run(planner: str, scenario_path: str, timeout: float):
    """Runs a planner the way the evaluation does; returns (plan or None, wall seconds, error text)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "plan.json")
        env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": KIT, "PYTHONDONTWRITEBYTECODE": "1", "HOME": tmp}
        t0 = time.monotonic()
        try:
            proc = subprocess.run([sys.executable, planner, scenario_path, out], env=env, capture_output=True,
                                  text=True, timeout=timeout)
            wall = time.monotonic() - t0
            err = proc.stderr[-200:] if proc.returncode else ""
        except subprocess.TimeoutExpired:
            return None, time.monotonic() - t0, "timeout"
        if not os.path.exists(out):
            return None, wall, err or "no plan written"
        with open(out) as f:
            return json.load(f), wall, err


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--factors", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--seeds", default="0-1")
    ap.add_argument("--planner", default=os.path.join(KIT, "handin", "planner.py"))
    ap.add_argument("--base", action="store_true", help="also run the kit baseline planner")
    ap.add_argument("--timeout", type=float, default=60.0)
    args = ap.parse_args()
    lo, _, hi = args.seeds.partition("-")
    seeds = range(int(lo), int(hi or lo) + 1)
    baseline = os.path.join(KIT, "tools", "baseline_planner.py")
    for factor in args.factors:
        generator.LEVELS["X%d" % factor] = scaled_level(factor)
        for seed in seeds:
            data = generator.generate("X%d" % factor, seed, ensure_feasible=False)
            scn = Scenario.from_dict(data)
            with tempfile.TemporaryDirectory() as tmp:
                path = os.path.join(tmp, "scenario.json")
                with open(path, "w") as f:
                    json.dump(data, f)
                plan, wall, err = run(args.planner, path, args.timeout)
                res = evaluate(scn, plan) if plan is not None else None
                line = "x%d seed %d  aircraft %3d contacts %3d  %s  score %8.1f  %5.1fs" % (
                    factor, seed, len(scn.aircraft), len(scn.contacts),
                    "valid  " if res is not None and res.valid else "INVALID", res.score if res else 0.0, wall)
                if err:
                    line += "  " + err.replace("\n", " ")
                if args.base:
                    bplan, bwall, _ = run(baseline, path, args.timeout)
                    bres = evaluate(scn, bplan) if bplan is not None else None
                    line += "   baseline %s %8.1f %5.1fs" % (
                        "valid" if bres is not None and bres.valid else "INVALID/none", bres.score if bres else 0.0, bwall)
                print(line, flush=True)


if __name__ == "__main__":
    main()

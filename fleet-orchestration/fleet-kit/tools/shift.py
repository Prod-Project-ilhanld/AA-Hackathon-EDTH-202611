"""Shift suite: generator variants no public level uses, to catch a planner tuned too tightly to L1-L4.

Variants are built at run time by copying LEVELS entries in fleetkit/generator.py (the kit is never edited).
Per variant, seeds N-M: planner run like the jury (fresh copy of the hand-in, subprocess, 60 s) next to
tools/baseline_planner.py. Pass = 0 failures and ratio >= 1.0 for every variant. Long: run by hand from fleet-kit/.
    python3 tools/shift.py --seeds 0-49 --python /usr/bin/python3
    python3 tools/shift.py --variants S-battery S-nofeas --seeds 0-4 --json shift.json
Variant names must keep _needs() compatible: it only tests `level_name in ("L1", "L2")` (3 weights), so every
S-* name takes the 4-weight branch, like L3/L4. S-l3-on-l4 is thus L3 staffing with L4 needs, not L3's own.
Exit code 1 on any failure or any variant under the baseline.
"""
import argparse
import json
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)
sys.path.insert(0, os.path.join(KIT, "tools"))

import bench  # noqa: E402
from fleetkit import generator  # noqa: E402
from fleetkit.model import save_json  # noqa: E402

L3, L4 = generator.LEVELS["L3"], generator.LEVELS["L4"]
_L4_SCOUTS = {"scouts": L4["scouts"] // 2}
_L3_ON_L4 = {k: L3[k] for k in ("scouts", "light", "heavy", "hostile", "unknown", "friendly", "civilian", "zones")}

# name -> (LEVELS entry, ensure_feasible)
VARIANTS = {
    "S-battery": (dict(L4, battery=(40, 70)), True),
    "S-points": (dict(L4, points_per_need=15), True),
    "S-nofeas": (dict(L4), False),
    "S-l3-on-l4": (dict(L4, **_L3_ON_L4), True),
    "S-half-scouts": (dict(L4, **_L4_SCOUTS), True),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS), choices=list(VARIANTS))
    ap.add_argument("--seeds", default="0-49")
    ap.add_argument("--planner", default=os.path.join(KIT, "handin", "planner.py"))
    ap.add_argument("--base", default=os.path.join(KIT, "tools", "baseline_planner.py"))
    ap.add_argument("--jobs", type=int, default=1, help="1 = honest timings (the planner already uses all cores)")
    ap.add_argument("--python", default="/usr/bin/python3" if os.path.exists("/usr/bin/python3") else sys.executable,
                    help="planner interpreter; the jury uses /usr/bin/python3")
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args()
    bench.PYTHON = args.python

    work = tempfile.mkdtemp(prefix="fleetshift_")
    cases = []
    for name in args.variants:
        entry, feasible = VARIANTS[name]
        generator.LEVELS[name] = entry
        for sd in bench.parse_seeds(args.seeds):
            path = os.path.join(work, "%s-%d.json" % (name, sd))
            save_json(generator.generate(name, sd, ensure_feasible=feasible), path)
            cases.append((name, sd, path))

    def job(case):
        name, sd, path = case
        tag = "%s-%d" % (name, sd)
        return (name, sd, bench.run_one(args.planner, path, work, tag + ".mine"),
                bench.run_one(args.base, path, work, tag + ".base"))

    rows = []
    with ThreadPoolExecutor(args.jobs) as pool:
        for name, sd, mine, base in pool.map(job, cases):
            print("%s %-14s seed %-3d mine %8.1f  base %8.1f  %5.1fs %s" % (
                "OK " if mine["valid"] else "BAD", name, sd, mine["score"], base["score"], mine["time"], mine["err"]),
                flush=True)
            rows.append({"level": name, "seed": sd, "mine": mine["score"], "base": base["score"],
                         "valid": mine["valid"], "time": round(mine["time"], 2), "err": mine["err"]})

    print("--- per variant")
    summary, fail = {}, False
    for name in args.variants:
        s = bench.summarize([r for r in rows if r["level"] == name])
        summary[name] = s
        under = s["ratio"] < 1.0
        fail |= bool(s["failures"]) or under
        print("%-14s n=%d total=%.1f base=%.1f ratio=%.3f failures=%d tmax=%.1fs%s" % (
            name, s["n"], s["mine"], s["base"], s["ratio"], s["failures"], s["tmax"], "  UNDER BASELINE" if under else ""))
    if args.json:
        with open(args.json, "w") as f:
            json.dump({"rows": rows, "summary": summary}, f, indent=1)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()

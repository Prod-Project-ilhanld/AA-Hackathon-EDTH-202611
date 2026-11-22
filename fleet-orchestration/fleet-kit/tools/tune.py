"""Paired, deterministic tuning of the planner's numbers. Train seeds only (0-199), never holdout or final.

From fleet-kit/:
    python3 tools/tune.py --levels L4 --seeds 0-39 --iters 6 --var "N_SCOUTS=10" --var "ANNEAL=1 ANNEAL_T0=0.02"
    python3 tools/tune.py --levels L4 --seeds 0-39 --iters 5 --var "N_SCOUTS=20" --base-iters 6   # slower builds

Every run is the hand-in planner (a snapshot of handin/ taken at start) in a subprocess with FLEET_ITERS=--iters
builds per worker, PLANNER_WORKERS=--workers, and a budget and alarm far beyond the run, so the deadline never
cuts a build: the plan depends only on the code, the scenario and the setting, never on machine load.
A setting (--var) is space-separated KEY=VALUE pairs, KEY as in handin/params.py, passed as PLANNER_<KEY>; the
baseline is every default (at --base-iters, default --iters). Results are cached in --cache, keyed by setting,
level, seed, iters and workers, so the baseline runs once: delete the cache when the planner code changes.

Per setting and level: paired delta (setting - baseline) as % of the baseline total, the per-seed s.e. in the same
unit, seeds worse, invalid plans, and user CPU per build relative to the baseline (children's user time from
wait4, fixed builds per run). A setting with slower builds gets fewer builds in the real 38 s: re-run it with
--iters scaled down by that ratio against --base-iters before trusting a gain. --json writes rows and summary.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)
sys.path.insert(0, os.path.join(KIT, "tools"))

from bench import parse_seeds  # noqa: E402
from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import Scenario, load_json, save_json  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402

FAR = "100000"  # budget and alarm (s) the run never reaches: FLEET_ITERS alone ends the search


def planner_env(setting, iters, workers):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PLANNER_", "FLEET_"))}
    env.update(PYTHONPATH=KIT, PYTHONDONTWRITEBYTECODE="1", FLEET_ITERS=str(iters), PLANNER_WORKERS=str(workers),
               PLANNER_BUDGET_S=FAR, PLANNER_ALARM_S=FAR)
    for pair in setting.split():
        key, _, value = pair.partition("=")
        env["PLANNER_" + key] = value
    return env


def run(planner, scen_path, setting, iters, workers, python):
    """One planner run: score, validity and the user CPU of the planner and its worker processes."""
    fd, plan_path = tempfile.mkstemp(suffix=".plan.json")
    os.close(fd)
    try:
        proc = subprocess.Popen([python, planner, scen_path, plan_path], env=planner_env(setting, iters, workers),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _, status, usage = os.wait4(proc.pid, 0)
        proc.returncode = status
        res = evaluate(Scenario.from_dict(load_json(scen_path)), load_json(plan_path))
        return {"score": res.score, "valid": bool(res.valid), "cpu": round(usage.ru_utime, 3)}
    except Exception as exc:  # noqa: BLE001  an unreadable or missing plan counts as invalid
        return {"score": 0.0, "valid": False, "cpu": 0.0, "err": str(exc)[:200]}
    finally:
        os.remove(plan_path)


def compare(base_rows, var_rows):
    """Paired stats of var against base over the (level, seed) keys both have. Rows: key -> run result."""
    keys = sorted(set(base_rows) & set(var_rows))
    if not keys:
        return None
    base = sum(base_rows[k]["score"] for k in keys)
    d = [var_rows[k]["score"] - base_rows[k]["score"] for k in keys]
    n = len(d)
    mean = sum(d) / n
    se = math.sqrt(sum((x - mean) ** 2 for x in d) / (n - 1) / n) if n > 1 else float("nan")
    unit = 100.0 * n / base if base else float("nan")  # per-seed delta -> % of the baseline total
    cpu_b = sum(base_rows[k]["cpu"] for k in keys)
    return {"n": n, "delta_pct": mean * unit, "se_pct": se * unit, "worse": sum(1 for x in d if x < 0),
            "better": sum(1 for x in d if x > 0), "invalid": sum(1 for k in keys if not var_rows[k]["valid"]),
            "cpu_ratio": sum(var_rows[k]["cpu"] for k in keys) / cpu_b if cpu_b else float("nan")}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--levels", nargs="+", default=["L4"])
    ap.add_argument("--seeds", default="0-39")
    ap.add_argument("--iters", type=int, default=6, help="FLEET_ITERS of the settings")
    ap.add_argument("--base-iters", type=int, help="FLEET_ITERS of the baseline (default: --iters)")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--var", action="append", default=[], help="one setting, e.g. 'SIGMA_ODD=0.4 ALPHA_STEP=0.3'")
    ap.add_argument("--jobs", type=int, default=3, help="runs in parallel (each uses --workers processes)")
    ap.add_argument("--python", default="/usr/bin/python3" if os.path.exists("/usr/bin/python3") else sys.executable)
    ap.add_argument("--planner", default=os.path.join(KIT, "handin", "planner.py"))
    ap.add_argument("--cache", default=os.path.join(KIT, "runs", "tune-cache.json"))
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args()
    base_iters = args.base_iters or args.iters

    work = tempfile.mkdtemp(prefix="fleettune_")
    snap = os.path.join(work, "handin")  # edits to handin/ during a long run never mix two versions
    shutil.copytree(os.path.dirname(os.path.abspath(args.planner)), snap,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    planner = os.path.join(snap, os.path.basename(args.planner))
    cache = load_json(args.cache) if os.path.exists(args.cache) else {}
    lock = threading.Lock()

    cases = [(lv, sd) for lv in args.levels for sd in parse_seeds(args.seeds)]
    for lv, sd in cases:
        save_json(generate(lv, sd), os.path.join(work, "%s-%d.json" % (lv, sd)))
    settings = [("", base_iters)] + [(" ".join(v.split()), args.iters) for v in args.var]
    jobs = []
    for setting, iters in settings:
        for lv, sd in cases:
            key = "%s|%s|%d|%d|%d" % (setting, lv, sd, iters, args.workers)
            if key not in cache:
                jobs.append((key, setting, iters, lv, sd))

    def job(j):
        key, setting, iters, lv, sd = j
        out = run(planner, os.path.join(work, "%s-%d.json" % (lv, sd)), setting, iters, args.workers, args.python)
        with lock:
            cache[key] = out
            os.makedirs(os.path.dirname(os.path.abspath(args.cache)), exist_ok=True)
            save_json(cache, args.cache)
        print("%-40s %s-%-4d %9.1f %s cpu %6.1fs" % (setting or "(base)", lv, sd, out["score"],
                                                     "OK " if out["valid"] else "BAD", out["cpu"]), flush=True)

    with ThreadPoolExecutor(args.jobs) as pool:
        list(pool.map(job, jobs))

    def rows(setting, iters):
        return {(lv, sd): cache["%s|%s|%d|%d|%d" % (setting, lv, sd, iters, args.workers)] for lv, sd in cases}

    base = rows("", base_iters)
    summary = {}
    print("--- vs baseline (FLEET_ITERS %d, %d workers); cpu = user CPU per build, base = 1" % (base_iters, args.workers))
    for setting, iters in settings[1:]:
        var = rows(setting, iters)
        for lv in args.levels:
            s = compare({k: v for k, v in base.items() if k[0] == lv}, {k: v for k, v in var.items() if k[0] == lv})
            s["cpu_ratio"] *= base_iters / iters  # per build: the two sides may run different FLEET_ITERS
            summary["%s @%d %s" % (setting, iters, lv)] = s
            print("%-40s @%-3d %s n=%d  delta %+6.2f%% +- %.2f  worse %d/%d  invalid %d  cpu x%.3f" % (
                setting, iters, lv, s["n"], s["delta_pct"], s["se_pct"], s["worse"], s["n"], s["invalid"],
                s["cpu_ratio"]))
    if args.json:
        save_json({"levels": args.levels, "seeds": args.seeds, "iters": args.iters, "base_iters": base_iters,
                   "workers": args.workers, "python": args.python, "summary": summary,
                   "rows": {"%s @%d|%s-%d" % (s or "(base)", it, lv, sd): cache["%s|%s|%d|%d|%d" % (
                       s, lv, sd, it, args.workers)] for s, it in settings for lv, sd in cases}}, args.json)


if __name__ == "__main__":
    main()

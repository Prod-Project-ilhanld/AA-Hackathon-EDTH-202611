"""Bench multi-graines : lance un planner comme l'évaluation (sous-processus, 60 s) et compare.

Exemples (depuis fleet-kit/). --jobs > 1 fausse les temps (le planner utilise déjà tous les cœurs) :
    python3 tools/bench.py --levels L1 L2 --seeds 0-9
    python3 tools/bench.py --levels L4 --seeds 0-4 --planner handin/planner.py --base tools/baseline_planner.py
    python3 tools/bench.py --levels L1 L2 L3 L4 --seeds 0-1 --jobs 1 --python /usr/bin/python3   # comme le jury
Chaque ligne : niveau-graine, validité, score, temps ; puis un résumé par niveau. Le code de sortie est 1
si un plan est invalide, en retard ou absent (un zéro coûte plus cher que tout gain).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import Scenario, load_json, save_json  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402

LIMIT_S = 60.0


def parse_seeds(text):
    out = []
    for part in text.split(","):
        a, _, b = part.partition("-")
        out.extend(range(int(a), int(b or a) + 1))
    return out


PYTHON = sys.executable


def run_one(planner, scen_path, work, tag):
    """Like the jury: a fresh copy of the planner's folder, `python planner.py scenario plan`, 60 s."""
    plan_path = os.path.join(work, f"{tag}.plan.json")
    team = os.path.join(work, f"{tag}.team")
    shutil.copytree(os.path.dirname(os.path.abspath(planner)), team,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if os.path.isdir(os.path.join(team, "fleetkit")):
        return {"valid": False, "score": 0.0, "time": 0.0, "err": "hand-in contains a fleetkit folder"}
    env = dict(os.environ, PYTHONPATH=KIT, PYTHONDONTWRITEBYTECODE="1")
    t0 = time.time()
    try:
        proc = subprocess.run([PYTHON, os.path.basename(planner), scen_path, plan_path], env=env, cwd=team,
                              capture_output=True, text=True, timeout=LIMIT_S)
        err = "" if proc.returncode == 0 else f"exit {proc.returncode}: {proc.stderr.strip()[-200:]}"
    except subprocess.TimeoutExpired:
        err = f"timeout > {LIMIT_S:.0f}s"
    dt = time.time() - t0
    if err or not os.path.exists(plan_path):
        return {"valid": False, "score": 0.0, "time": dt, "err": err or "no plan"}
    res = evaluate(Scenario.from_dict(load_json(scen_path)), load_json(plan_path))
    err = "" if res.valid else "; ".join(str(v) for v in res.violations[:2])
    return {"valid": res.valid, "score": res.score, "time": dt, "err": err, "points": res.points}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", nargs="+", default=["L1", "L2", "L3", "L4"])
    ap.add_argument("--seeds", default="0-4")
    ap.add_argument("--planner", default=os.path.join(KIT, "handin", "planner.py"))
    ap.add_argument("--base", default=os.path.join(KIT, "tools", "baseline_planner.py"),
                    help="planner de référence ('' pour désactiver)")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--python", default=sys.executable,
                    help="interpréteur du planner, ex. /usr/bin/python3 (le jury promet seulement Python 3.9+)")
    args = ap.parse_args()
    global PYTHON
    PYTHON = args.python

    work = tempfile.mkdtemp(prefix="fleetbench_")
    cases = []
    for lv in args.levels:
        for sd in parse_seeds(args.seeds):
            path = os.path.join(work, f"{lv}-{sd}.json")
            save_json(generate(lv, sd), path)
            cases.append((lv, sd, path))

    def job(case):
        lv, sd, path = case
        tag = f"{lv}-{sd}"
        mine = run_one(args.planner, path, work, tag + ".mine")
        base = run_one(args.base, path, work, tag + ".base") if args.base else None
        return lv, sd, mine, base

    bad = 0
    stats = {}
    with ThreadPoolExecutor(args.jobs) as pool:
        for lv, sd, mine, base in pool.map(job, cases):
            flag = "OK " if mine["valid"] else "BAD"
            bad += 0 if mine["valid"] else 1
            line = f"{flag} {lv}-{sd:<4} score {mine['score']:8.1f}  {mine['time']:5.1f}s"
            if base:
                line += f"   base {base['score']:8.1f}  ({mine['score'] - base['score']:+.1f})"
            if mine["err"]:
                line += f"   {mine['err']}"
            print(line, flush=True)
            s = stats.setdefault(lv, {"n": 0, "mine": 0.0, "base": 0.0, "tmax": 0.0})
            s["n"] += 1
            s["mine"] += mine["score"]
            s["base"] += base["score"] if base else 0.0
            s["tmax"] = max(s["tmax"], mine["time"])
    print("--- résumé (somme des scores)")
    tm = tb = 0.0
    for lv, s in stats.items():
        print(f"{lv}: n={s['n']} mine={s['mine']:.1f} base={s['base']:.1f} "
              f"ratio={(s['mine'] / s['base']) if s['base'] else float('nan'):.3f} tmax={s['tmax']:.1f}s")
        tm += s["mine"]
        tb += s["base"]
    print(f"TOTAL mine={tm:.1f} base={tb:.1f} invalides/échecs={bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

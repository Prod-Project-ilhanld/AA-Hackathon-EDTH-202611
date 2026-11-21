"""Bench multi-graines : lance un planner comme l'évaluation (sous-processus, 60 s) et compare.

Exemples (depuis fleet-kit/). --jobs > 1 fausse les temps (le planner utilise déjà tous les cœurs) :
    python3 tools/bench.py --levels L1 L2 --seeds 0-9
    python3 tools/bench.py --levels L4 --seeds 0-4 --planner handin/planner.py --base tools/baseline_planner.py
    python3 tools/bench.py --levels L1 L2 L3 L4 --seeds 0-1 --jobs 1 --python /usr/bin/python3   # comme le jury
    FLEET_ITERS=3 PLANNER_WORKERS=2 python3 tools/bench.py --levels L3 --seeds 0-4 --json out.json  # déterministe
Chaque ligne : niveau-graine, validité, score, temps ; puis un résumé par niveau, avec les stats appariées
(delta moyen par graine mine - base ± erreur standard, graines pires k/n). --json PATH écrit les lignes et le
résumé en JSON. L'environnement (PLANNER_*, FLEET_ITERS...) passe tel quel aux planners. Le code de sortie est 1
si un plan est invalide, en retard ou absent (un zéro coûte plus cher que tout gain).
"""
import argparse
import json
import math
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


def summarize(rows):
    """Totals and paired stats (mine - base, per seed) for a list of rows."""
    d = [r["mine"] - r["base"] for r in rows if r["base"] is not None]
    n = len(rows)
    mine = sum(r["mine"] for r in rows)
    base = sum(r["base"] or 0.0 for r in rows)
    mean = sum(d) / len(d) if d else float("nan")
    se = math.sqrt(sum((x - mean) ** 2 for x in d) / (len(d) - 1) / len(d)) if len(d) > 1 else float("nan")
    worse = sum(1 for x in d if x < 0)
    return {"n": n, "mine": mine, "base": base, "ratio": mine / base if base else float("nan"),
            "failures": sum(1 for r in rows if not r["valid"]), "tmax": max((r["time"] for r in rows), default=0.0),
            "delta_mean": mean, "delta_se": se, "worse": worse, "worse_share": worse / len(d) if d else float("nan"),
            "paired_n": len(d)}


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
    ap.add_argument("--json", metavar="PATH", help="écrit les lignes par run et le résumé en JSON")
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
    rows = []
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
            rows.append({"level": lv, "seed": sd, "mine": mine["score"], "base": base["score"] if base else None,
                         "valid": mine["valid"], "time": round(mine["time"], 2), "err": mine["err"]})
    print("--- résumé (somme des scores)")
    tm = tb = 0.0
    for lv, s in stats.items():
        print(f"{lv}: n={s['n']} mine={s['mine']:.1f} base={s['base']:.1f} "
              f"ratio={(s['mine'] / s['base']) if s['base'] else float('nan'):.3f} tmax={s['tmax']:.1f}s")
        p = summarize([r for r in rows if r["level"] == lv])
        if p["paired_n"]:
            print(f"    delta/graine {p['delta_mean']:+.1f} ± {p['delta_se']:.1f} (s.e.)  "
                  f"graines pires {p['worse']}/{p['paired_n']}")
        tm += s["mine"]
        tb += s["base"]
    print(f"TOTAL mine={tm:.1f} base={tb:.1f} invalides/échecs={bad}")
    if args.json:
        summary = {lv: summarize([r for r in rows if r["level"] == lv]) for lv in stats}
        summary["TOTAL"] = summarize(rows)
        with open(args.json, "w") as f:  # NaN (no baseline, or n=1) is written as NaN, which json.load accepts
            json.dump({"rows": rows, "summary": summary}, f, indent=1)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

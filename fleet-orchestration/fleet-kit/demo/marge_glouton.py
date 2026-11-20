"""Marge laissée par le glouton, sur plusieurs seeds par niveau (slide « le problème » du pitch).

À placer dans  fleet-kit/demo/marge_glouton.py  et lancer depuis fleet-kit :

    python demo/marge_glouton.py                       # L1 à L4, seeds 0 à 4
    python demo/marge_glouton.py --levels L3 L4 --seeds 0-9 --csv marge.csv

Pour chaque scénario : score du glouton, contacts servis, éclaireurs et drones d'action utilisés,
et points non servis sans blocage évident (même diagnostic que swann_demo.py : hors R7 et hors
drones épuisés). Ce n'est pas un plafond atteignable : fenêtres, énergie et séparation peuvent
encore bloquer. Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
for candidate in (os.path.dirname(HERE), HERE, os.getcwd()):
    if os.path.isdir(os.path.join(candidate, "fleetkit")) and candidate not in sys.path:
        sys.path.insert(0, candidate)
sys.path.insert(0, HERE)

from fleetkit.baseline import greedy_plan  # noqa: E402
from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import EFFECTOR, HOSTILE, SCOUT, UNKNOWN, Scenario, parse_plan  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
from swann_demo import diagnose  # noqa: E402


def seeds_from(text: str):
    if "-" in text:
        lo, hi = text.split("-")
        return list(range(int(lo), int(hi) + 1))
    return [int(x) for x in text.split(",")]


def analyse(level: str, seed: int) -> dict:
    scenario = Scenario.from_dict(generate(level, seed))
    t0 = time.time()
    plan = greedy_plan(scenario)
    dt = time.time() - t0
    res = evaluate(scenario, plan)
    routes, _ = parse_plan(plan)
    served = set(res.served)
    missed = [c for c in scenario.contacts if c.cls in (HOSTILE, UNKNOWN) and c.id not in served]
    open_pts = sum(c.points for c in missed if diagnose(scenario, routes, c)[1])
    n = lambda t: sum(1 for a in scenario.aircraft if a.type == t)  # noqa: E731
    used = lambda t: sum(1 for a in scenario.aircraft if a.type == t and a.id in routes)  # noqa: E731
    servable = sum(1 for c in scenario.contacts if c.cls in (HOSTILE, UNKNOWN))
    return {
        "niveau": level, "seed": seed, "score_glouton": round(res.score, 1),
        "servis": len(served), "servables": servable,
        "eclaireurs": f"{used(SCOUT)}/{n(SCOUT)}", "effecteurs": f"{used(EFFECTOR)}/{n(EFFECTOR)}",
        "points_a_gagner": round(open_pts), "temps_glouton_s": round(dt, 1),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Marge laissée par le glouton sur plusieurs seeds.")
    p.add_argument("--levels", nargs="+", default=["L1", "L2", "L3", "L4"])
    p.add_argument("--seeds", default="0-4", help="ex. 0-9 ou 1,5,7")
    p.add_argument("--csv", help="écrit aussi les lignes dans ce fichier CSV")
    args = p.parse_args()

    rows = []
    head = f"{'niv':4} {'seed':>4} {'score':>8} {'servis':>9} {'éclair.':>8} {'effect.':>8} {'à gagner':>9} {'temps':>6}"
    print(head)
    for level in args.levels:
        for seed in seeds_from(args.seeds):
            r = analyse(level, seed)
            rows.append(r)
            print(f"{r['niveau']:4} {r['seed']:>4} {r['score_glouton']:>8} {str(r['servis']) + '/' + str(r['servables']):>9} "
                  f"{r['eclaireurs']:>8} {r['effecteurs']:>8} {r['points_a_gagner']:>9} {r['temps_glouton_s']:>5}s")
    print("\nMoyenne par niveau (score glouton · points à gagner sans blocage évident)")
    for level in args.levels:
        rs = [r for r in rows if r["niveau"] == level]
        if rs:
            s = sum(r["score_glouton"] for r in rs) / len(rs)
            g = sum(r["points_a_gagner"] for r in rs) / len(rs)
            print(f"  {level} : {s:7.1f} · {g:7.0f}")
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"-> {args.csv}")


if __name__ == "__main__":
    main()

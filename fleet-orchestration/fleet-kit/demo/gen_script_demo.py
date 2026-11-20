"""Remplit SCRIPT_DEMO.template.md avec les vrais chiffres d'un scénario/plan (binôme 3, Swann).

Évite de recopier les chiffres à la main dans SCRIPT_DEMO.md : à relancer à chaque nouveau plan.

    python demo/gen_script_demo.py s_l4.json plan.json

Écrit demo/SCRIPT_DEMO.md (ou --out) à partir de demo/SCRIPT_DEMO.template.md.
Bibliothèque standard uniquement.
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for candidate in (os.path.dirname(HERE), HERE, os.getcwd()):
    if os.path.isdir(os.path.join(candidate, "fleetkit")) and candidate not in sys.path:
        sys.path.insert(0, candidate)
sys.path.insert(0, HERE)

from fleetkit.baseline import greedy_plan  # noqa: E402
from fleetkit.model import HOSTILE, UNKNOWN, Scenario, load_json, parse_plan  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
from swann_demo import diagnose  # noqa: E402


def fr(x: float, decimals: int = 0) -> str:
    """Formate un nombre à la française (virgule décimale) pour le texte du script de démo."""
    return f"{x:.{decimals}f}".replace(".", ",")


def main() -> None:
    p = argparse.ArgumentParser(description="Génère SCRIPT_DEMO.md avec les vrais chiffres mesurés.")
    p.add_argument("scenario")
    p.add_argument("plan")
    p.add_argument("--template", default=os.path.join(HERE, "SCRIPT_DEMO.template.md"))
    p.add_argument("-o", "--out", default=os.path.join(HERE, "SCRIPT_DEMO.md"))
    args = p.parse_args()

    scenario = Scenario.from_dict(load_json(args.scenario))
    greedy = greedy_plan(scenario)
    ours = load_json(args.plan)
    res_greedy, res_ours = evaluate(scenario, greedy), evaluate(scenario, ours)
    servable_total = sum(1 for c in scenario.contacts if c.cls in (HOSTILE, UNKNOWN))

    def open_and_contested(plan, res):
        routes, _ = parse_plan(plan)
        routes = routes or {}
        served = set(res.served)
        missed = [c for c in scenario.contacts if c.cls in (HOSTILE, UNKNOWN) and c.id not in served]
        open_pts = contested_pts = 0.0
        for c in missed:
            _, _, cat = diagnose(scenario, routes, c)
            if cat == "a_gagner":
                open_pts += c.points
            elif cat == "concurrence":
                contested_pts += c.points
        return open_pts, contested_pts

    open_pts_glouton, _ = open_and_contested(greedy, res_greedy)
    open_pts_ours, contested_pts_ours = open_and_contested(ours, res_ours)

    gain_pct = 100.0 * (res_ours.score - res_greedy.score) / res_greedy.score if res_greedy.score else 0.0
    values = dict(
        level=scenario.level, seed=scenario.seed,
        score_glouton=fr(res_greedy.score, 1), score_ours=fr(res_ours.score, 1), gain_pct=fr(gain_pct, 0),
        served_glouton=len(res_greedy.served), served_ours=len(res_ours.served),
        servable_total=servable_total,
        open_pts_glouton=fr(open_pts_glouton, 0), open_pts_ours=fr(open_pts_ours, 0),
        contested_pts_ours=fr(contested_pts_ours, 0),
    )

    with open(args.template, encoding="utf-8") as f:
        template = f.read()
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(template.format(**values))
    print(f"glouton {res_greedy.score:.1f} ({len(res_greedy.served)} servis) -> "
          f"notre plan {res_ours.score:.1f} ({len(res_ours.served)} servis), +{gain_pct:.0f} %")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()

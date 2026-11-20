"""Démo et explication d'un plan (binôme 3, Swann).

À placer dans  fleet-kit/demo/swann_demo.py  et lancer depuis le dossier fleet-kit :

    python demo/swann_demo.py scenario.json                  # compare le glouton à lui-même (test)
    python demo/swann_demo.py scenario.json notre_plan.json  # compare notre plan au glouton

Produit, dans le dossier de sortie (par défaut demo_out/) :
    view.html        le visualiseur du kit avec nos calques (gagnés, perdus, non servis, routes du glouton)
    explication.md   le rapport qui justifie chaque affectation (pour le jury)

Bibliothèque standard uniquement, comme le reste du kit.
"""
from __future__ import annotations

import argparse
import math
import os
import sys

# Rend `fleetkit` importable quand le script est lancé depuis fleet-kit/ ou fleet-kit/demo/.
HERE = os.path.dirname(os.path.abspath(__file__))
for candidate in (os.path.dirname(HERE), HERE, os.getcwd()):
    if os.path.isdir(os.path.join(candidate, "fleetkit")) and candidate not in sys.path:
        sys.path.insert(0, candidate)

from fleetkit.baseline import greedy_plan  # noqa: E402
from fleetkit.energy import route_energy_wh  # noqa: E402
from fleetkit.geometry import hdist  # noqa: E402
from fleetkit.model import CIVILIAN, EFFECTOR, FRIENDLY, HOSTILE, UNKNOWN, Scenario, load_json, parse_plan  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
from fleetkit.viewer import Viewer  # noqa: E402

GREEN, RED, AMBER, GREY = "#3fb950", "#f85149", "#d29922", "#8b949e"


def route_length_m(waypoints) -> float:
    """Distance 3D parcourue par une route, en mètres."""
    return sum(math.dist(a.pos, b.pos) for a, b in zip(waypoints, waypoints[1:]))


def servable(scenario: Scenario):
    """Contacts qui peuvent rapporter des points : hostiles (engagement) et inconnus (observation)."""
    return [c for c in scenario.contacts if c.cls in (HOSTILE, UNKNOWN)]


def diagnose(scenario, routes, c):
    """Raison simple et vérifiable pour laquelle un contact n'est pas servi : (texte, gagnable ?)."""
    rules = scenario.rules
    if c.cls == HOSTILE:
        protected = [f for f in scenario.contacts if f.cls in (FRIENDLY, CIVILIAN)]
        near = [f for f in protected if hdist(c.pos, f.pos) < rules.collateral_radius_m]
        if near:
            return f"interdit par R7 (à {hdist(c.pos, near[0].pos):.0f} m de {near[0].id}, {near[0].cls})", False
        left = {}
        for a in scenario.aircraft:
            if a.id not in routes and a.type == EFFECTOR:
                left[a.subtype] = left.get(a.subtype, 0) + 1
        short = [k for k, n in c.needs.items() if left.get(k, 0) < n]
        if short:
            return f"plus assez de drones {', '.join(short)} au sol", False
        return "drones disponibles au sol : à gagner", True
    return "observation possible par un éclaireur", True


def build_view(scenario, ours, res_ours, greedy, res_greedy, path):
    contacts = scenario.contact_by_id()
    served_ours, served_greedy = set(res_ours.served), set(res_greedy.served)
    gained = sorted(served_ours - served_greedy)
    lost = sorted(served_greedy - served_ours)
    missed = [c for c in servable(scenario) if c.id not in served_ours]

    def ring(cid, r=160):
        c = contacts[cid]
        return (c.pos[0], c.pos[1], r)

    def tag(cid, text):
        c = contacts[cid]
        return (c.pos[0], c.pos[1] + 180, text)

    v = Viewer(scenario, ours, title="Notre plan face au glouton")
    v.layer("Gagnés vs glouton", circles=[ring(c) for c in gained],
            labels=[tag(c, f"+{contacts[c].points:g} pts") for c in gained], color=GREEN)
    v.layer("Perdus vs glouton", circles=[ring(c) for c in lost],
            labels=[tag(c, f"-{contacts[c].points:g} pts") for c in lost], color=RED)
    routes_ours, _ = parse_plan(ours)
    routes_ours = routes_ours or {}
    open_c = [c for c in missed if diagnose(scenario, routes_ours, c)[1]]
    blocked = [c for c in missed if not diagnose(scenario, routes_ours, c)[1]]
    v.layer("À gagner", circles=[ring(c.id, 120) for c in open_c],
            labels=[tag(c.id, f"{c.id} · {c.points:g} pts") for c in open_c], color=AMBER)
    v.layer("Bloqués (R7 ou drones épuisés)", circles=[ring(c.id, 120) for c in blocked],
            labels=[tag(c.id, f"{c.id} bloqué") for c in blocked], color=GREY, visible=False)
    routes, _ = parse_plan(greedy)
    v.layer("Routes du glouton", lines=[[(w.x, w.y) for w in r.waypoints] for r in routes.values()],
            color=GREY, visible=False)
    v.save(path)
    return gained, lost, missed


def build_report(scenario, ours, res_ours, res_greedy, gained, lost, missed, path):
    aircraft, contacts = scenario.aircraft_by_id(), scenario.contact_by_id()
    rules = scenario.rules
    routes, _ = parse_plan(ours)
    out = []
    w = out.append
    w(f"# Explication du plan · scénario {scenario.level} seed {scenario.seed}\n")
    w("| | Glouton | Notre plan |\n| --- | ---: | ---: |")
    w(f"| Valide | {'oui' if res_greedy.valid else 'non'} | {'oui' if res_ours.valid else 'non'} |")
    w(f"| Score | {res_greedy.score:.1f} | {res_ours.score:.1f} |")
    w(f"| Points servis | {res_greedy.points:.1f} | {res_ours.points:.1f} |")
    w(f"| Énergie (Wh) | {res_greedy.energy_wh:.1f} | {res_ours.energy_wh:.1f} |")
    w(f"| Drones d'action consommés | {res_greedy.effectors_used} | {res_ours.effectors_used} |")
    w(f"| Contacts servis | {len(res_greedy.served)} | {len(res_ours.served)} |\n")
    w(f"Coût d'1 Wh = {rules.lambda_e:g} pt · coût d'un drone d'action = {rules.c_eff:g} pts.\n")

    if not res_ours.valid:
        w("## Plan invalide\n")
        for v in res_ours.violations[:20]:
            w(f"- {v}")
        w("")

    w(f"Gagnés par rapport au glouton : {', '.join(gained) or 'aucun'} · "
      f"perdus : {', '.join(lost) or 'aucun'}.\n")

    # Ressources : quels types de drones sont épuisés (le vrai goulot) et lesquels restent au sol.
    w("## Ressources\n")
    w("| Type | Disponibles | Utilisés | Restants |\n| --- | ---: | ---: | ---: |")
    groups = {}
    for a in scenario.aircraft:
        key = a.type + (f" ({a.subtype})" if a.subtype else "")
        groups.setdefault(key, []).append(a.id)
    for key in sorted(groups):
        ids = groups[key]
        used = sum(1 for i in ids if i in routes)
        w(f"| {key} | {len(ids)} | {used} | {len(ids) - used} |")
    idle = sorted(a.id for a in scenario.aircraft if a.id not in routes)
    w(f"\nDrones au sol : {', '.join(idle) or 'aucun'}.\n")

    w("## Affectations, drone par drone\n")
    for aid in sorted(routes):
        r, a = routes[aid], aircraft[aid]
        kind = f"{a.type}" + (f" ({a.subtype})" if a.subtype else "")
        energy = route_energy_wh(r.waypoints, a)
        w(f"### {aid} · {kind}\n")
        w(f"Distance {route_length_m(r.waypoints) / 1000:.2f} km · énergie {energy:.1f} Wh "
          f"sur {a.usable_wh:.1f} Wh utilisables · coût {rules.lambda_e * energy:.1f} pts.\n")
        for wp in r.waypoints:
            if not wp.action:
                continue
            c = contacts.get(wp.target)
            window = f"{c.window[0]:.0f}–{c.window[1]:.0f} s" if c and c.window else "sans fenêtre"
            pts = f"{c.points:g} pts" if c else "?"
            verb = "observe" if wp.action == "observe" else "engage"
            w(f"- t = {wp.t:.0f} s · {verb} **{wp.target}** ({c.cls if c else '?'}, {pts}, fenêtre {window})")
        w("")

    w("## Contacts non servis\n")
    if not missed:
        w("Tous les contacts qui rapportent des points sont servis.")
    open_pts = 0.0
    for c in sorted(missed, key=lambda c: -c.points):
        need = ", ".join(f"{n} {k}" for k, n in c.needs.items()) if c.needs else "observation"
        window = f"{c.window[0]:.0f}–{c.window[1]:.0f} s" if c.window else "sans fenêtre"
        why, possible = diagnose(scenario, routes, c)
        open_pts += c.points if possible else 0.0
        w(f"- **{c.id}** · {c.cls}, {c.points:g} pts, besoin : {need}, fenêtre {window} · {why}")
    if missed:
        w(f"\nPoints non servis sans blocage évident (R7 ou drones épuisés) : **{open_pts:g} pts**. "
          "À vérifier : fenêtre atteignable, énergie, séparation.")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description="Calques de démo et rapport d'explication d'un plan.")
    p.add_argument("scenario")
    p.add_argument("plan", nargs="?", help="notre plan ; absent = le glouton (pour tester)")
    p.add_argument("-o", "--out", default="demo_out")
    args = p.parse_args()

    scenario = Scenario.from_dict(load_json(args.scenario))
    greedy = greedy_plan(scenario)
    ours = load_json(args.plan) if args.plan else greedy
    res_greedy, res_ours = evaluate(scenario, greedy), evaluate(scenario, ours)

    os.makedirs(args.out, exist_ok=True)
    view_path, report_path = os.path.join(args.out, "view.html"), os.path.join(args.out, "explication.md")
    gained, lost, missed = build_view(scenario, ours, res_ours, greedy, res_greedy, view_path)
    build_report(scenario, ours, res_ours, res_greedy, gained, lost, missed, report_path)
    print(f"Glouton {res_greedy.score:.1f} · notre plan {res_ours.score:.1f} "
          f"({'valide' if res_ours.valid else 'INVALIDE'})")
    print(f"-> {view_path}\n-> {report_path}")


if __name__ == "__main__":
    main()

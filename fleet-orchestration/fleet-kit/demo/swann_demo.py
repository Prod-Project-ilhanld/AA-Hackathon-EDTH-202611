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
from fleetkit.model import CIVILIAN, EFFECTOR, FRIENDLY, HOSTILE, SCOUT, UNKNOWN, Scenario, load_json, parse_plan  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
from fleetkit.viewer import Viewer  # noqa: E402

GREEN, RED, AMBER, GREY = "#3fb950", "#f85149", "#d29922", "#8b949e"

DEFAULT_STRATEGY = (
    "Glouton large et relances randomisées sous budget de temps (planner v1, Louis) : réutilise le "
    "routage du glouton de base (détours de zones, couches d'altitude) ; teste beaucoup plus "
    "d'éclaireurs candidats par contact plutôt que les 3 plus proches ; valide à bas coût (routes "
    "touchées seulement) avant la validation complète des 10 règles ; relance plusieurs fois avec un "
    "ordre de contacts randomisé et garde le meilleur plan valide ; replie sur le glouton si rien de "
    "mieux n'est trouvé dans le budget."
)


def route_length_m(waypoints) -> float:
    """Distance 3D parcourue par une route, en mètres."""
    return sum(math.dist(a.pos, b.pos) for a, b in zip(waypoints, waypoints[1:]))


def servable(scenario: Scenario):
    """Contacts qui peuvent rapporter des points : hostiles (engagement) et inconnus (observation)."""
    return [c for c in scenario.contacts if c.cls in (HOSTILE, UNKNOWN)]


def _direct_transit(ac, origin, dest):
    """Temps (s) et énergie (Wh) d'un trajet direct origine -> destination à la vitesse max de l'appareil.

    Hypothèse optimiste (ligne droite) : ignore les détours imposés par R6 (zones) et par R8 (séparation).
    """
    dh = hdist(origin, dest)
    dz = dest[2] - origin[2]
    t = max(dh / ac.v_h_mps, (dz / ac.v_up_mps if dz > 0 else -dz / ac.v_down_mps), 0.0)
    if t <= 0:
        return 0.0, 0.0
    speed = dh / t
    cruise_wh = (ac.power.p0_w + ac.power.k_v * speed * speed) * t / 3600.0
    return t, cruise_wh + ac.power.e_climb_wh_per_m * max(0.0, dz)


def _effector_reach(ac, contact, window_end):
    """Un effecteur au sol peut-il rejoindre le contact à temps et avec assez de batterie ?"""
    t, e = _direct_transit(ac, ac.home, contact.pos)
    return t <= window_end + 1e-6 and e <= ac.usable_wh + 1e-6


def _scout_observe_ok(ac, contact, window_end, rules):
    """Un éclaireur au sol peut-il observer puis rentrer, à temps et avec assez de batterie ?"""
    t_out, e_out = _direct_transit(ac, ac.home, contact.pos)
    _, e_back = _direct_transit(ac, contact.pos, ac.home)
    hover_wh = ac.power.p0_w * rules.obs_dwell_s / 3600.0
    return (t_out + rules.obs_dwell_s <= window_end + 1e-6
            and e_out + hover_wh + e_back <= ac.usable_wh + 1e-6)


def _scout_confirm_ok(ac, contact, window_end, rules):
    """Un éclaireur au sol peut-il en plus finir son observation `confirm_margin_s` avant la fin de fenêtre ?"""
    if not _scout_observe_ok(ac, contact, window_end, rules):
        return False
    t_out, _ = _direct_transit(ac, ac.home, contact.pos)
    return t_out + rules.obs_dwell_s + rules.confirm_margin_s <= window_end + 1e-6


def diagnose(scenario, routes, c):
    """Raison simple et vérifiable pour laquelle un contact n'est pas servi : (texte, gagnable ?).

    Vérifie R7 (collatéral) et la disponibilité des drones, puis teste si un trajet direct vers le
    contact tient dans la fenêtre et dans la batterie utilisable d'un drone encore au sol. Condition
    nécessaire mais pas suffisante : R6 (détour autour des zones), R8 (séparation) et la synchronisation
    R10 entre plusieurs effecteurs ne sont pas vérifiés ici.
    """
    rules = scenario.rules
    window_end = c.window[1] if c.window else scenario.horizon_s

    def idle(actype, subtype=None):
        return [a for a in scenario.aircraft
                if a.id not in routes and a.type == actype and (subtype is None or a.subtype == subtype)]

    if c.cls == HOSTILE:
        protected = [f for f in scenario.contacts if f.cls in (FRIENDLY, CIVILIAN)]
        near = [f for f in protected if hdist(c.pos, f.pos) < rules.collateral_radius_m]
        if near:
            return f"interdit par R7 (à {hdist(c.pos, near[0].pos):.0f} m de {near[0].id}, {near[0].cls})", False
        short = [sub for sub, need in c.needs.items()
                 if sum(1 for a in idle(EFFECTOR, sub) if _effector_reach(a, c, window_end)) < need]
        if short:
            return f"pas assez d'effecteurs {', '.join(short)} au sol capables d'arriver à temps et en énergie", False
        scouts = idle(SCOUT)
        if not scouts:
            return "aucun éclaireur au sol pour confirmer avant l'engagement", False
        if not any(_scout_confirm_ok(a, c, window_end, rules) for a in scouts):
            return "aucun éclaireur au sol ne peut confirmer à temps (fenêtre ou énergie)", False
        return "drones au sol, fenêtre et énergie compatibles en ligne directe : à gagner", True

    scouts = idle(SCOUT)
    if not scouts:
        return "aucun éclaireur au sol", False
    if not any(_scout_observe_ok(a, c, window_end, rules) for a in scouts):
        return "hors de portée d'un éclaireur au sol (fenêtre ou énergie), même en ligne directe", False
    return "éclaireur disponible, fenêtre et énergie compatibles en ligne directe : à gagner", True


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


def build_report(scenario, ours, res_ours, res_greedy, gained, lost, missed, path, strategy=None):
    aircraft, contacts = scenario.aircraft_by_id(), scenario.contact_by_id()
    rules = scenario.rules
    routes, _ = parse_plan(ours)
    routes = routes or {}
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

    if res_ours.valid and res_ours.score > res_greedy.score and strategy:
        gain_pct = 100.0 * (res_ours.score - res_greedy.score) / res_greedy.score if res_greedy.score else 0.0
        w("## Stratégie du planificateur\n")
        w(f"{strategy}\n")
        w(f"Résultat sur ce scénario : **+{gain_pct:.0f} %** par rapport au glouton "
          f"({res_greedy.score:.1f} → {res_ours.score:.1f} pts).\n")

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
        if aid not in aircraft:
            w(f"### {aid}\n")
            w("Identifiant d'avion inconnu du scénario (voir violations R1 ci-dessus).\n")
            continue
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
        w(f"\nPoints non servis sans blocage évident (R7, drones épuisés, fenêtre ou énergie en ligne "
          f"directe) : **{open_pts:g} pts**. À vérifier : détour autour des zones (R6), séparation (R8) "
          "et synchronisation entre effecteurs (R10).")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description="Calques de démo et rapport d'explication d'un plan.")
    p.add_argument("scenario")
    p.add_argument("plan", nargs="?", help="notre plan ; absent = le glouton (pour tester)")
    p.add_argument("-o", "--out", default="demo_out")
    p.add_argument("--strategy", default=DEFAULT_STRATEGY,
                    help="texte décrivant la stratégie du planificateur, affiché si notre plan gagne")
    p.add_argument("--no-strategy", action="store_true", help="n'affiche pas la section stratégie")
    args = p.parse_args()

    scenario = Scenario.from_dict(load_json(args.scenario))
    greedy = greedy_plan(scenario)
    ours = load_json(args.plan) if args.plan else greedy
    res_greedy, res_ours = evaluate(scenario, greedy), evaluate(scenario, ours)

    os.makedirs(args.out, exist_ok=True)
    view_path, report_path = os.path.join(args.out, "view.html"), os.path.join(args.out, "explication.md")
    gained, lost, missed = build_view(scenario, ours, res_ours, greedy, res_greedy, view_path)
    strategy = None if args.no_strategy or not args.plan else args.strategy
    build_report(scenario, ours, res_ours, res_greedy, gained, lost, missed, report_path, strategy)
    print(f"Glouton {res_greedy.score:.1f} · notre plan {res_ours.score:.1f} "
          f"({'valide' if res_ours.valid else 'INVALIDE'})")
    print(f"-> {view_path}\n-> {report_path}")


if __name__ == "__main__":
    main()

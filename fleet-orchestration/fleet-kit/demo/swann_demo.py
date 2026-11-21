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
import time

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

# Le vrai planificateur (Louis, v7) est fusionné dans main, mais pas sur cette branche de démo :
# on ne duplique pas son code ici, chaque équipier reste sur son chantier. S'il est présent sur le
# disque (dépôt mis à jour depuis main, ou handin/ copié pour un test local), le diagnostic rejoue
# le vrai routage ; sinon il retombe sur l'heuristique en ligne directe ci-dessous.
try:
    from handin.planner import FastPlanner, OutOfTime  # noqa: E402
    HAS_REAL_PLANNER = True
except Exception:
    FastPlanner, OutOfTime, HAS_REAL_PLANNER = None, Exception, False

DIAG_BUDGET_S = float(os.environ.get("DIAG_BUDGET_S", "8.0"))

GREEN, RED, AMBER, TEAL, GREY = "#3fb950", "#f85149", "#d29922", "#39c5cf", "#8b949e"

DEFAULT_STRATEGY = (
    "Construction gloutonne élargie (planner v7, Louis, fusionné dans main) : 15 éclaireurs testés "
    "par hostile avec toutes leurs options (les proches saturent, les autres aussi testés sur une "
    "flotte de 15 éclaireurs) ; contrôle incrémental à chaque essai (ne revalide que les routes "
    "touchées, environ 3 fois plus d'essais par seconde) ; hostiles bloqués par R7 (collatéral) "
    "ignorés d'emblée ; relances par petites variations autour du meilleur ordre de contacts "
    "trouvé (points par effecteur requis), réparties sur plusieurs processus, sous un budget de "
    "38 s ; deux routages selon la taille de la flotte ; garde de séparation (R10) systématique à "
    "chaque tentative. Chaque plan construit est revalidé par le scorer du kit ; au final, on "
    "écrit le meilleur plan valide trouvé (plan vide si aucun ne l'est)."
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


def _diagnose_heuristic(scenario, routes, c):
    """Repli utilisé quand `handin.planner` (Louis) n'est pas sur le disque : borne optimiste par
    trajet direct, sans rejouer le vrai routage. Mêmes limites que l'ancienne version : ignore R6
    (détour de zones), R8 (séparation) et R10 (synchronisation entre effecteurs)."""
    rules = scenario.rules
    window_end = c.window[1] if c.window else scenario.horizon_s

    def idle(actype, subtype=None):
        return [a for a in scenario.aircraft
                if a.id not in routes and a.type == actype and (subtype is None or a.subtype == subtype)]

    if c.cls == HOSTILE:
        short = [sub for sub, need in c.needs.items()
                 if sum(1 for a in idle(EFFECTOR, sub) if _effector_reach(a, c, window_end)) < need]
        if short:
            return (f"pas assez d'effecteurs {', '.join(short)} au sol capables d'arriver à temps et en "
                     "énergie (estimation en ligne directe, routage réel non disponible)"), False, "hors_de_portee"
        scouts = idle(SCOUT)
        if not scouts or not any(_scout_confirm_ok(a, c, window_end, rules) for a in scouts):
            return ("aucun éclaireur au sol ne peut confirmer à temps (estimation en ligne directe, "
                     "routage réel non disponible)"), False, "hors_de_portee"
        return ("drones au sol, fenêtre et énergie compatibles en ligne directe (routage réel non "
                 "disponible) : à gagner, à confirmer"), True, "a_gagner"

    scouts = idle(SCOUT)
    if not scouts or not any(_scout_observe_ok(a, c, window_end, rules) for a in scouts):
        return ("hors de portée d'un éclaireur au sol, même en ligne directe (routage réel non "
                 "disponible)"), False, "hors_de_portee"
    return ("éclaireur disponible, fenêtre et énergie compatibles en ligne directe (routage réel non "
             "disponible) : à gagner, à confirmer"), True, "a_gagner"


def _real_routing_ok(scenario, c, used):
    """Rejoue le vrai routage de Louis (planner v2) sur ce contact seul, `used` déjà pris par ailleurs.

    True/False = verdict ; None = budget dépassé (indéterminé, pas une preuve d'échec).
    """
    deadline = time.monotonic() + DIAG_BUDGET_S
    p = FastPlanner(scenario, deadline)
    p.used = set(used)
    try:
        return p.serve_hostile(c) if c.cls == HOSTILE else p.serve_unknown(c)
    except OutOfTime:
        return None


def diagnose(scenario, routes, c):
    """Raison vérifiable pour laquelle un contact n'est pas servi : (texte, gagnable ?, catégorie).

    Catégories : "r7" (collatéral, HOSTILE seulement), "a_gagner" (routage réel réussi avec des
    drones encore au sol, zéro conflit), "concurrence" (routable seul, mais les drones nécessaires
    sont déjà pris par un autre contact dans notre plan), "hors_de_portee" (aucun routage trouvé
    même avec tous les drones disponibles).

    Si `handin.planner` (Louis) n'est pas sur le disque de cette branche, ou si le budget de test
    par contact est dépassé, retombe sur une borne optimiste par trajet direct (voir
    `_diagnose_heuristic`) : nécessaire mais pas suffisante, ne vérifie pas R6/R8/R10.
    """
    rules = scenario.rules
    if c.cls == HOSTILE:
        protected = [f for f in scenario.contacts if f.cls in (FRIENDLY, CIVILIAN)]
        near = [f for f in protected if hdist(c.pos, f.pos) < rules.collateral_radius_m]
        if near:
            return (f"interdit par R7 (à {hdist(c.pos, near[0].pos):.0f} m de {near[0].id}, "
                     f"{near[0].cls})"), False, "r7"

    if not HAS_REAL_PLANNER:
        return _diagnose_heuristic(scenario, routes, c)

    ok_idle = _real_routing_ok(scenario, c, routes.keys())
    if ok_idle is None:
        text, win, cat = _diagnose_heuristic(scenario, routes, c)
        return text + " [routage réel : budget de test dépassé]", win, cat
    if ok_idle:
        return "routage réel réussi avec des drones encore au sol, sans conflit : à gagner", True, "a_gagner"

    ok_full = _real_routing_ok(scenario, c, [])
    if ok_full is None:
        text, win, cat = _diagnose_heuristic(scenario, routes, c)
        return text + " [routage réel : budget de test dépassé]", win, cat
    if ok_full:
        return ("routable seul, mais les drones nécessaires sont déjà pris par un autre contact dans "
                 "notre plan (concurrence de ressources)"), False, "concurrence"
    return "aucun routage trouvé, même avec tous les drones disponibles (routage réel testé)", False, "hors_de_portee"


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
    diag = {c.id: diagnose(scenario, routes_ours, c) for c in missed}
    open_c = [c for c in missed if diag[c.id][2] == "a_gagner"]
    contested = [c for c in missed if diag[c.id][2] == "concurrence"]
    blocked = [c for c in missed if diag[c.id][2] in ("r7", "hors_de_portee")]
    v.layer("À gagner", circles=[ring(c.id, 120) for c in open_c],
            labels=[tag(c.id, f"{c.id} · {c.points:g} pts") for c in open_c], color=AMBER)
    v.layer("Concurrence ressources", circles=[ring(c.id, 120) for c in contested],
            labels=[tag(c.id, f"{c.id} en concurrence") for c in contested], color=TEAL, visible=False)
    v.layer("Bloqués (R7 ou hors de portée)", circles=[ring(c.id, 120) for c in blocked],
            labels=[tag(c.id, f"{c.id} bloqué") for c in blocked], color=GREY, visible=False)
    routes, _ = parse_plan(greedy)
    v.layer("Routes du glouton", lines=[[(w.x, w.y) for w in r.waypoints] for r in routes.values()],
            color=GREY, visible=False)
    v.save(path)
    return gained, lost, missed, diag


def build_report(scenario, ours, res_ours, res_greedy, gained, lost, missed, diag, path, strategy=None):
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
    open_pts, contested_pts = 0.0, 0.0
    for c in sorted(missed, key=lambda c: -c.points):
        need = ", ".join(f"{n} {k}" for k, n in c.needs.items()) if c.needs else "observation"
        window = f"{c.window[0]:.0f}–{c.window[1]:.0f} s" if c.window else "sans fenêtre"
        why, possible, cat = diag[c.id]
        if cat == "a_gagner":
            open_pts += c.points
        elif cat == "concurrence":
            contested_pts += c.points
        w(f"- **{c.id}** · {c.cls}, {c.points:g} pts, besoin : {need}, fenêtre {window} · {why}")
    if missed:
        source = "routage réel rejoué sur chaque contact" if HAS_REAL_PLANNER else \
            "estimation en ligne directe, routage réel non disponible sur cette branche"
        w(f"\nPoints réellement gagnables sans toucher au plan actuel ({source}) : "
          f"**{open_pts:g} pts**. En concurrence avec un contact déjà servi pour les mêmes drones : "
          f"**{contested_pts:g} pts** (gagnable seulement en sacrifiant un autre contact).")
        if not HAS_REAL_PLANNER:
            w("À vérifier avec le vrai routage (R6 détour de zones, R8 séparation, R10 "
              "synchronisation entre effecteurs non couverts par l'estimation).")
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
    gained, lost, missed, diag = build_view(scenario, ours, res_ours, greedy, res_greedy, view_path)
    strategy = None if args.no_strategy or not args.plan else args.strategy
    build_report(scenario, ours, res_ours, res_greedy, gained, lost, missed, diag, report_path, strategy)
    print(f"Glouton {res_greedy.score:.1f} · notre plan {res_ours.score:.1f} "
          f"({'valide' if res_ours.valid else 'INVALIDE'})")
    print(f"-> {view_path}\n-> {report_path}")


if __name__ == "__main__":
    main()

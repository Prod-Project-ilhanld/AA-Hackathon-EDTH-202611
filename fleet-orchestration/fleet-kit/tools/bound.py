"""Borne supérieure du score par scénario et par niveau : « quel pourcentage du possible a-t-on atteint ? ».

La borne relâche ce qui est dur à calculer (séparation R8, synchronisation R10, conflits de temps entre
contacts, montée, vol stationnaire) et garde ce qui est exact et statique :
  - R7 (collatéral) : un hostile trop près d'un ami ou d'un civil n'est jamais engagé ;
  - R9 + R4 : un hostile doit être observé (20 s) puis engagé (10 s plus tard) dans sa fenêtre, au plus tôt
    quand le premier éclaireur et le premier effecteur peuvent arriver en ligne droite ;
  - R3 : l'énergie minimale (ligne droite à la vitesse de meilleur rendement) doit tenir dans la batterie ;
  - la flotte : nombre d'effecteurs légers et lourds disponibles (sac à dos exact sur les deux types) ;
  - le coût : 10 par effecteur + 0,5 par Wh, au minimum possible.
Une borne supérieure n'est jamais inférieure au meilleur plan valide : un test le vérifie sur des plans réels.
La borne est lâche (elle ignore R8 et le temps des éclaireurs partagés) : un pourcentage de borne de 60 % ne
veut pas dire 40 % de perdu à coup sûr, seulement que 40 % ne sont pas prouvés hors d'atteinte.

Usage (depuis fleet-kit/) :
    python3 tools/bound.py --levels L1 L2 L3 L4 --seeds 0-49
    python3 tools/bound.py --bench bench.json          # % de borne d'un banc : python3 tools/bench.py --json bench.json
"""
import argparse
import json
import math
import os
import sys
from typing import Dict, List, Optional, Tuple

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit.generator import generate  # noqa: E402
from fleetkit.geometry import hdist  # noqa: E402
from fleetkit.model import (CIVILIAN, EFFECTOR, FRIENDLY, HOSTILE, SCOUT, UNKNOWN, Aircraft,  # noqa: E402
                            Scenario)

J_PER_WH = 3600.0


def _wh_per_m(a: Aircraft) -> float:
    """Énergie minimale par mètre en ligne droite : vitesse de meilleur rendement, bornée par la vitesse max."""
    p = a.power
    v = min(math.sqrt(p.p0_w / p.k_v), a.v_h_mps)
    return (p.p0_w + p.k_v * v * v) / v / J_PER_WH


def _fly(a: Aircraft, d_h: float, within: float) -> Tuple[float, float]:
    """(temps minimal en s, énergie minimale en Wh) pour s'approcher à `within` m horizontaux d'un point."""
    reach = max(0.0, d_h - within)
    return reach / a.v_h_mps, reach * _wh_per_m(a)


def _scout_obs(sc: Scenario, c, scouts: List[Aircraft]) -> Optional[Tuple[float, float]]:
    """Meilleure observation possible de `c` : (fin d'observation au plus tôt, énergie minimale du vol aller-retour).

    None si aucun éclaireur ne peut observer dans la fenêtre avec sa batterie.
    """
    r = sc.rules
    end_min = e_min = None
    for s in scouts:
        t_go, e_go = _fly(s, hdist(s.home, c.pos), r.R_obs_m)
        e = 2.0 * e_go + s.power.p0_w * r.obs_dwell_s / J_PER_WH
        if e > s.usable_wh:
            continue
        start = t_go if c.window is None else max(t_go, c.window[0])
        end = start + r.obs_dwell_s
        if (c.window is not None and end > c.window[1]) or end > sc.horizon_s:
            continue
        # deux minima séparés (fin au plus tôt, énergie la plus basse) : relâchement valide
        end_min = end if end_min is None else min(end_min, end)
        e_min = e if e_min is None else min(e_min, e)
    return None if end_min is None else (end_min, e_min)


def _effector_costs(sc: Scenario, c, obs_end: float, effectors: List[Aircraft]) -> Dict[str, List[float]]:
    """Coûts minimaux (c_eff + lambda * Wh) des effecteurs capables d'engager `c`, triés, par sous-type."""
    r = sc.rules
    t_engage_min = obs_end + r.confirm_margin_s
    if c.window is not None:
        t_engage_min = max(t_engage_min, c.window[0])
    out: Dict[str, List[float]] = {}
    for a in effectors:
        t_go, e_go = _fly(a, hdist(a.home, c.pos), r.R_eng_m)
        if e_go > a.usable_wh:
            continue
        t = max(t_go, t_engage_min)
        if t > sc.horizon_s or (c.window is not None and t > c.window[1]):
            continue
        out.setdefault(a.subtype or "", []).append(r.c_eff + r.lambda_e * e_go)
    for v in out.values():
        v.sort()
    return out


def bound(sc: Scenario) -> Dict[str, float]:
    """Retourne la borne supérieure du score de `sc`, avec son détail (hostiles, inconnus)."""
    r = sc.rules
    scouts = [a for a in sc.aircraft if a.type == SCOUT]
    effectors = [a for a in sc.aircraft if a.type == EFFECTOR]
    supply = {}
    for a in effectors:
        supply[a.subtype or ""] = supply.get(a.subtype or "", 0) + 1
    protected = [f for f in sc.contacts if f.cls in (FRIENDLY, CIVILIAN)]

    items = []  # (besoin léger, besoin lourd, valeur nette)
    for c in sc.contacts:
        if c.cls != HOSTILE or not c.needs:
            continue
        if any(hdist(c.pos, f.pos) < r.collateral_radius_m for f in protected):
            continue
        obs = _scout_obs(sc, c, scouts)
        if obs is None:
            continue
        costs = _effector_costs(sc, c, obs[0], effectors)
        total, ok = 0.0, True
        for sub, n in c.needs.items():
            have = costs.get(sub, [])
            if len(have) < n:
                ok = False
                break
            total += sum(have[:n])
        if not ok:
            continue
        net = c.points - total
        if net > 0:
            items.append((c.needs.get("light", 0), c.needs.get("heavy", 0), net))

    cap_l, cap_h = supply.get("light", 0), supply.get("heavy", 0)
    dp = [[0.0] * (cap_h + 1) for _ in range(cap_l + 1)]
    for nl, nh, v in items:
        for l in range(cap_l, nl - 1, -1):
            for h in range(cap_h, nh - 1, -1):
                cand = dp[l - nl][h - nh] + v
                if cand > dp[l][h]:
                    dp[l][h] = cand
    hostile_part = dp[cap_l][cap_h]

    unknown_part = 0.0
    n_unknown = 0
    for c in sc.contacts:
        if c.cls != UNKNOWN:
            continue
        obs = _scout_obs(sc, c, scouts)
        if obs is not None and c.points - r.lambda_e * obs[1] > 0:
            unknown_part += c.points - r.lambda_e * obs[1]
            n_unknown += 1
    return {"bound": hostile_part + unknown_part, "hostiles": hostile_part, "unknown": unknown_part,
            "n_hostile_items": len(items), "n_unknown": n_unknown}


def parse_seeds(text: str) -> List[int]:
    out: List[int] = []
    for part in text.split(","):
        a, _, b = part.partition("-")
        out.extend(range(int(a), int(b or a) + 1))
    return out


def level_bounds(levels: List[str], seeds: List[int]) -> Dict[Tuple[str, int], float]:
    return {(lv, sd): bound(Scenario.from_dict(generate(lv, sd)))["bound"] for lv in levels for sd in seeds}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--levels", nargs="+", default=["L1", "L2", "L3", "L4"])
    ap.add_argument("--seeds", default="0-49")
    ap.add_argument("--bench", metavar="JSON", help="sortie de `tools/bench.py --json` : affiche le % de la borne")
    args = ap.parse_args()

    rows = None
    if args.bench:
        with open(args.bench) as f:
            rows = json.load(f)["rows"]
        levels = sorted({r["level"] for r in rows})
        seeds_by_level = {lv: sorted({r["seed"] for r in rows if r["level"] == lv}) for lv in levels}
    else:
        levels = args.levels
        seeds_by_level = {lv: parse_seeds(args.seeds) for lv in levels}

    tot_b = tot_m = tot_base = 0.0
    print(f"{'niveau':<7}{'n':>4}{'borne moy.':>12}" + ("" if rows is None else f"{'planner':>10}{'% borne':>9}{'glouton':>10}{'% borne':>9}"))
    for lv in levels:
        sds = seeds_by_level[lv]
        b = {sd: bound(Scenario.from_dict(generate(lv, sd)))["bound"] for sd in sds}
        line = f"{lv:<7}{len(sds):>4}{sum(b.values()) / len(sds):>12.1f}"
        if rows is not None:
            mine = sum(r["mine"] for r in rows if r["level"] == lv)
            base = sum((r["base"] or 0.0) for r in rows if r["level"] == lv)
            sb = sum(b.values())
            line += f"{mine / len(sds):>10.1f}{100 * mine / sb:>8.1f}%{base / len(sds):>10.1f}{100 * base / sb:>8.1f}%"
            tot_m += mine
            tot_base += base
        tot_b += sum(b.values())
        print(line)
    if rows is not None:
        print(f"TOTAL  : planner {100 * tot_m / tot_b:.1f} % de la borne, glouton {100 * tot_base / tot_b:.1f} % "
              f"(somme des scores / somme des bornes, mêmes graines)")


if __name__ == "__main__":
    main()

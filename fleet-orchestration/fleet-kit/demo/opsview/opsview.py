"""Vue opérateur : le visualiseur du kit avec des ajouts d'équipe, sans toucher à `fleetkit/`.

`OpsViewer` hérite de `fleetkit.viewer.Viewer` : mêmes calques, même modèle, même verdict du kit. Il rend la page
avec les fichiers de ce dossier (`template.html`, `style.css`, `app.js`), copiés de la vue de base puis étendus.
La page produite s'écrit à côté de la vue de base (`view_ops.html`), jamais à sa place.

Usage depuis fleet-kit/ :
    python3 demo/opsview/opsview.py scenario.json plan.json -o out/view_ops.html

Bibliothèque standard uniquement, comme le reste du kit.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

HERE = Path(__file__).resolve().parent
KIT = HERE.parent.parent
if str(KIT) not in sys.path:
    sys.path.insert(0, str(KIT))

from fleetkit.energy import route_energy_wh  # noqa: E402
from fleetkit.geometry import hdist  # noqa: E402
from fleetkit.model import CIVILIAN, FRIENDLY, HOSTILE, SCOUT, UNKNOWN, Scenario, load_json, parse_plan  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
from fleetkit.validator import route_pieces, separation_item  # noqa: E402
from fleetkit.viewer import Viewer  # noqa: E402
from fleetkit.viewer.brand import font_face_css, logo_data_uri  # noqa: E402


def render_ops(model: Dict[str, Any]) -> str:
    """Retourne la page autonome (pas de réseau, aucun fichier externe) pour un modèle de vue."""
    template = (HERE / "template.html").read_text(encoding="utf-8")
    css = (HERE / "style.css").read_text(encoding="utf-8")
    js = (HERE / "app.js").read_text(encoding="utf-8")
    data = json.dumps(model, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "\\u003c!--")
    title = html.escape(str(model["meta"]["title"]))
    return (template.replace("__TITLE__", title).replace("/*__FONTS__*/", font_face_css()).replace("/*__CSS__*/", css)
            .replace("/*__JS__*/", js).replace("__DATA__", data).replace("__LOGO__", logo_data_uri()))


REASON_TEXT = {
    "a_gagner": "Routable with drones still idle and no conflict found: points left on the table.",
    "concurrence": "Routable alone, but the drones it needs are already used by another contact of the plan (resource competition).",
    "hors_de_portee": "No routing found even with every drone free: out of range or energy.",
}


def reasons_from_diagnosis(diag: Dict[str, tuple]) -> Dict[str, Dict[str, str]]:
    """Convertit le résultat de `swann_demo.diagnose` ({contact: (texte, gagnable, catégorie)}) en raisons de fiche."""
    out: Dict[str, Dict[str, str]] = {}
    for cid, (text, _win, cat) in diag.items():
        msg = REASON_TEXT.get(cat)
        if msg is None:
            continue
        if "budget" in text:
            msg += " (approximate: routing test budget exceeded)"
        out[cid] = {"cat": cat, "text": msg}
    return out


def build_ops(scenario: Any, plan: Optional[dict], model: Dict[str, Any], reasons: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    """Données de la vue opérateur : flotte, fiche par contact, fil d'événements. Exact, tiré du plan et du scénario."""
    rules = scenario.rules
    ops: Dict[str, Any] = {"fleet": {}, "contacts": {}, "feed": [],
                           "rules": {"confirm": rules.confirm_margin_s, "dwell": rules.obs_dwell_s,
                                     "collateral": rules.collateral_radius_m, "c_eff": rules.c_eff, "lambda": rules.lambda_e, "d_sep": rules.d_sep_m}}
    routes: Dict[str, Any] = {}
    if plan is not None:
        routes = parse_plan(plan)[0] or {}
    used = {aid for aid, r in routes.items() if any(w.action in ("observe", "engage") for w in r.waypoints)}
    for a in scenario.aircraft:
        key = "scout" if a.type == SCOUT else (a.subtype or "light")
        slot = ops["fleet"].setdefault(key, {"total": 0, "used": 0})
        slot["total"] += 1
        slot["used"] += 1 if a.id in used else 0

    ac_by = scenario.aircraft_by_id()
    protected = [f for f in scenario.contacts if f.cls in (FRIENDLY, CIVILIAN)]
    marks_by: Dict[str, list] = {}
    for m in model.get("marks", []):
        marks_by.setdefault(m["contact"], []).append(m)
    served = model.get("served", {})
    for c in scenario.contacts:
        if c.cls not in (HOSTILE, UNKNOWN):
            continue
        near = min(((hdist(c.pos, f.pos), f.id, f.cls) for f in protected), default=None)
        r7 = None
        if near is not None and c.cls == HOSTILE:
            r7 = {"dist": round(near[0]), "id": near[1], "cls": near[2], "blocked": near[0] < rules.collateral_radius_m}
        obs = [{"aid": m["aid"], "t0": m["t0"], "t1": m["t1"], "ok": bool(m.get("ok"))}
               for m in marks_by.get(c.id, []) if m["kind"] == "observe"]
        eng = [{"aid": m["aid"], "t": m["t"], "sub": ac_by[m["aid"]].subtype if m["aid"] in ac_by else None,
                "km": round(hdist(ac_by[m["aid"]].home, c.pos) / 1000.0, 1) if m["aid"] in ac_by else None}
               for m in marks_by.get(c.id, []) if m["kind"] == "engage"]
        margin = None
        valid_obs = [o["t1"] for o in obs if o["ok"]]
        if eng and valid_obs:
            margin = round(min(e["t"] for e in eng) - min(valid_obs), 1)
        n_eff = sum(c.needs.values()) if c.needs else 0
        info: Dict[str, Any] = {"cls": c.cls, "points": c.points, "needs": {k: v for k, v in c.needs.items() if v},
                                "window": list(c.window) if c.window else None, "served_t": served.get(c.id), "r7": r7,
                                "obs": obs, "eng": eng, "r4_margin": margin,
                                "pts_per_eff": round(c.points / n_eff, 1) if n_eff else None}
        if c.id not in served:
            if r7 and r7["blocked"]:
                info["reason"] = {"cat": "r7", "text": "Forbidden by R7: %d m from %s (%s), limit %g m. No valid plan can serve it."
                                  % (r7["dist"], r7["id"], r7["cls"], rules.collateral_radius_m)}
            elif c.id in reasons:
                info["reason"] = reasons[c.id]
            else:
                info["reason"] = {"cat": "unknown", "text": "Not served in this plan. The cause is not computed here: see the explanation report."}
        ops["contacts"][c.id] = info

    for cid, info in ops["contacts"].items():
        for o in info["obs"]:
            ops["feed"].append({"t": o["t1"], "kind": "observe", "aid": o["aid"], "cid": cid,
                                "text": "%s observed %s (%g s)%s" % (o["aid"], cid, o["t1"] - o["t0"], "" if o["ok"] else " · not valid")})
        for e in info["eng"]:
            last = info["served_t"] is not None and abs(e["t"] - info["served_t"]) < 1e-6
            ops["feed"].append({"t": e["t"], "kind": "engage", "aid": e["aid"], "cid": cid,
                                "text": "%s engages %s%s" % (e["aid"], cid, (" · %s served +%g pts" % (cid, info["points"])) if last else "")})
    ops["feed"].sort(key=lambda x: (x["t"], x["kind"], x["aid"]))
    ops["drones"], ops["outcome"] = drone_outcomes(scenario, model)
    ops["alerts"] = build_alerts(scenario, routes, model, ops)
    return ops


def drone_outcomes(scenario: Any, model: Dict[str, Any]):
    """Rôle de chaque drone dans le plan, tiré des marques et des contacts servis (exact, aucune supposition).

    strike : a engagé un contact servi. spot : a seulement observé (observation valide) un contact servi.
    wasted : a observé ou engagé sans contribuer à un contact servi. idle : aucune tâche.
    `pts` répartit les points d'un contact servi à parts égales entre les drones qui y ont contribué.
    """
    served = model.get("served", {})
    pts = {c.id: c.points for c in scenario.contacts}
    marks_by: Dict[str, list] = {}
    for m in model.get("marks", []):
        marks_by.setdefault(m["aid"], []).append(m)
    contrib: Dict[str, set] = {}
    for aid, ms in marks_by.items():
        for m in ms:
            if m["contact"] in served and (m["kind"] == "engage" or m.get("ok")):
                contrib.setdefault(m["contact"], set()).add(aid)
    drones: Dict[str, Any] = {}
    summary = {"strike": 0, "spot": 0, "wasted": 0, "idle": 0, "wasted_eff": 0}
    for a in scenario.aircraft:
        ms = marks_by.get(a.id, [])
        good = [m for m in ms if m["contact"] in served and (m["kind"] == "engage" or m.get("ok"))]
        if not ms:
            cat = "idle"
        elif any(m["kind"] == "engage" for m in good):
            cat = "strike"
        elif good:
            cat = "spot"
        else:
            cat = "wasted"
        summary[cat] += 1
        summary["wasted_eff"] += sum(1 for m in ms if m["kind"] == "engage" and m["contact"] not in served)
        share = sum(pts.get(m["contact"], 0) / len(contrib[m["contact"]]) for m in {(x["contact"]): x for x in good}.values())
        drones[a.id] = {"cat": cat, "pts": round(share, 1), "targets": sorted({m["contact"] for m in ms})}
    return drones, summary


DEPART_S = 3.0  # les départs depuis un même emplacement sont cadencés par le planificateur : exclus du classement en vol


def _min_sep(pa, pb, t_from=0.0):
    """Distance minimale (m) et instant entre deux trajectoires affines par morceaux, à partir de `t_from` ; None si jamais en vol ensemble."""
    best = None
    i = j = 0
    while i < len(pa) and j < len(pb):
        a, b = pa[i], pb[j]
        lo, hi = max(a[0], b[0], t_from), min(a[1], b[1])
        if hi - lo > 1e-9:
            def at(pc, t):
                u = 0.0 if pc[1] - pc[0] < 1e-12 else (t - pc[0]) / (pc[1] - pc[0])
                return [pc[2][k] + (pc[3][k] - pc[2][k]) * u for k in range(3)]
            r0 = [x - y for x, y in zip(at(a, lo), at(b, lo))]
            r1 = [x - y for x, y in zip(at(a, hi), at(b, hi))]
            w = [(r1[k] - r0[k]) / (hi - lo) for k in range(3)]
            qa = sum(x * x for x in w)
            u = 0.0 if qa < 1e-12 else min(max(-sum(r0[k] * w[k] for k in range(3)) / qa, 0.0), hi - lo)
            d = sum((r0[k] + u * w[k]) ** 2 for k in range(3)) ** 0.5
            if best is None or d < best[0]:
                best = (d, lo + u)
        if a[1] < b[1]:
            i += 1
        else:
            j += 1
    return best


def build_alerts(scenario: Any, routes: Dict[str, Any], model: Dict[str, Any], ops: Dict[str, Any], top: int = 5) -> list:
    """Points faibles d'un plan valide : marges les plus serrées, classées. Exact, tiré du plan ; ce ne sont pas des violations.

    sep : plus petite distance entre deux drones (R8, limite d_sep_m ; les paires qui frappent le même contact
    sont exemptées près de lui par la règle, donc exclues ici). r4 : confirmation après l'observation. batt : énergie
    restante (modèle du kit) à la fin du vol. r7 : distance d'un hostile servi au civil ou à l'ami le plus proche.
    """
    rules = scenario.rules
    out: list = []
    by = scenario.aircraft_by_id()
    items = {}
    for aid, r in routes.items():
        if aid in by:
            it = separation_item(aid, r, by[aid])
            if it:
                items[aid] = it
    pairs = []
    ids = sorted(items)
    for x in range(len(ids)):
        a = items[ids[x]]
        for y in range(x + 1, len(ids)):
            b = items[ids[y]]
            if min(a[3], b[3]) - max(a[2], b[2]) <= 1e-9 or (a[4] is not None and a[4] == b[4]):
                continue
            m = _min_sep(a[1], b[1], max(a[2], b[2]) + DEPART_S)
            if m:
                pairs.append((m[0], m[1], ids[x], ids[y]))
    for d, t, a, b in sorted(pairs)[:top]:
        out.append({"kind": "sep", "level": "watch" if d < 1.5 * rules.d_sep_m else "ok", "t": round(t, 1), "aids": [a, b], "cid": None,
                    "value": round(d, 1), "text": "%s and %s come within %.0f m (limit %g m)" % (a, b, d, rules.d_sep_m)})
    r4 = sorted((i["r4_margin"] - rules.confirm_margin_s, cid) for cid, i in ops["contacts"].items() if i["r4_margin"] is not None)
    for slack, cid in r4[:top]:
        i = ops["contacts"][cid]
        first = min(i["eng"], key=lambda e: e["t"])
        out.append({"kind": "r4", "level": "watch" if slack < 5 else "ok", "t": first["t"], "aids": [first["aid"]], "cid": cid, "value": round(slack, 1),
                    "text": "%s engaged %.1f s after the observation ended, minimum %g s (spare %.1f s)" % (cid, i["r4_margin"], rules.confirm_margin_s, slack)})
    batt = []
    for aid, r in routes.items():
        a = by.get(aid)
        if a is None or not a.usable_wh or not r.waypoints:
            continue
        batt.append(((a.usable_wh - route_energy_wh(r.waypoints, a)) / a.usable_wh, r.waypoints[-1].t, aid))
    for frac, t, aid in sorted(batt)[:top]:
        out.append({"kind": "batt", "level": "watch" if frac < 0.10 else "ok", "t": round(t, 1), "aids": [aid], "cid": None, "value": round(100 * frac, 1),
                    "text": "%s has %.0f%% battery left at the end of its flight" % (aid, 100 * frac)})
    r7 = sorted((i["r7"]["dist"], cid) for cid, i in ops["contacts"].items() if i["served_t"] is not None and i["r7"])
    for dist, cid in r7[:top]:
        i = ops["contacts"][cid]
        out.append({"kind": "r7", "level": "watch" if dist < 1.25 * rules.collateral_radius_m else "ok", "t": i["served_t"], "aids": [], "cid": cid, "value": dist,
                    "text": "%s served %d m from %s (%s), limit %g m" % (cid, dist, i["r7"]["id"], i["r7"]["cls"], rules.collateral_radius_m)})
    return out


class OpsViewer(Viewer):
    """Le visualiseur du kit, rendu avec la vue opérateur de l'équipe."""

    def model(self) -> Dict[str, Any]:
        model = super().model()
        self.extend_model(model)
        return model

    def __init__(self, *args: Any, reasons: Optional[Dict[str, Dict[str, str]]] = None, **kwargs: Any):
        """`reasons` : {contact: {"cat": ..., "text": ...}} pour les contacts non servis (voir `reasons_from_diagnosis`)."""
        super().__init__(*args, **kwargs)
        self.reasons = reasons or {}

    def extend_model(self, model: Dict[str, Any]) -> None:
        """Ajoute au modèle les données calculées en Python : flotte, fiches de contacts, fil d'événements.

        Tout vient du plan et du scénario (exact) ; la raison d'un contact non servi n'est affirmée que si elle est
        prouvée (R7 : calcul exact ici) ou fournie par un diagnostic (`reasons`). Sinon la fiche le dit.
        """
        model["ops"] = build_ops(self.scenario, self.plan, model, self.reasons)

    def html(self) -> str:
        return render_ops(self.model())


def run_diagnosis(scenario: Scenario, plan: dict) -> Dict[str, Dict[str, str]]:
    """Diagnostic réel de Swann (`demo/swann_demo.py`) pour chaque contact utile non servi. Compter ~30 s sur L4."""
    sys.path.insert(0, str(KIT / "demo"))
    import swann_demo  # noqa: WPS433

    routes = parse_plan(plan)[0] or {}
    served = set(evaluate(scenario, plan).served)
    diag = {c.id: swann_demo.diagnose(scenario, routes, c) for c in swann_demo.servable(scenario) if c.id not in served}
    return reasons_from_diagnosis(diag)


def main() -> None:
    ap = argparse.ArgumentParser(description="Vue opérateur d'un scénario et d'un plan.")
    ap.add_argument("scenario")
    ap.add_argument("plan", nargs="?")
    ap.add_argument("-o", "--output", default="view_ops.html")
    ap.add_argument("--title", default=None)
    ap.add_argument("--diagnose", action="store_true",
                    help="rejoue le routage réel pour expliquer chaque contact non servi (lent : ~30 s sur L4)")
    args = ap.parse_args()
    scenario = Scenario.from_dict(load_json(args.scenario))
    plan = load_json(args.plan) if args.plan else None
    reasons = run_diagnosis(scenario, plan) if args.diagnose and plan else None
    out = OpsViewer(scenario, plan, title=args.title, reasons=reasons).save(args.output)
    print("écrit", os.path.abspath(out))


if __name__ == "__main__":
    main()

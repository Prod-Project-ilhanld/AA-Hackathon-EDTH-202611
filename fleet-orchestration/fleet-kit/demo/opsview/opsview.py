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

from fleetkit.geometry import hdist  # noqa: E402
from fleetkit.model import CIVILIAN, FRIENDLY, HOSTILE, SCOUT, UNKNOWN, Scenario, load_json, parse_plan  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
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
                                     "collateral": rules.collateral_radius_m, "c_eff": rules.c_eff, "lambda": rules.lambda_e}}
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
    return ops


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

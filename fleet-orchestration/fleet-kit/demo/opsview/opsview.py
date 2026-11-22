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
from typing import Any, Dict

HERE = Path(__file__).resolve().parent
KIT = HERE.parent.parent
if str(KIT) not in sys.path:
    sys.path.insert(0, str(KIT))

from fleetkit.model import load_json  # noqa: E402
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


class OpsViewer(Viewer):
    """Le visualiseur du kit, rendu avec la vue opérateur de l'équipe."""

    def model(self) -> Dict[str, Any]:
        model = super().model()
        self.extend_model(model)
        return model

    def extend_model(self, model: Dict[str, Any]) -> None:
        """Ajoute au modèle les données calculées en Python (jauges, raisons). Vide pour l'instant."""

    def html(self) -> str:
        return render_ops(self.model())


def main() -> None:
    ap = argparse.ArgumentParser(description="Vue opérateur d'un scénario et d'un plan.")
    ap.add_argument("scenario")
    ap.add_argument("plan", nargs="?")
    ap.add_argument("-o", "--output", default="view_ops.html")
    ap.add_argument("--title", default=None)
    args = ap.parse_args()
    plan = load_json(args.plan) if args.plan else None
    out = OpsViewer(load_json(args.scenario), plan, title=args.title).save(args.output)
    print("écrit", os.path.abspath(out))


if __name__ == "__main__":
    main()

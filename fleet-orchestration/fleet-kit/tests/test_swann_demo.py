"""Un cas positif et un cas négatif par détecteur de demo/swann_demo.py (binôme 3, Swann).

Couvre `diagnose()` (R7, et la borne optimiste de repli quand `handin.planner` n'est pas sur le
disque) et la robustesse de `build_report()` face à un plan invalide ou malformé (ne doit jamais
planter le rapport du jury).
"""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo"))

from fleetkit.model import Scenario  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
import swann_demo  # noqa: E402
from swann_demo import build_report, build_view, diagnose  # noqa: E402


# ----- diagnose() : R7 (collatéral), vérifié avant tout repli ou routage réel -----------------

def test_r7_blocks_a_hostile_too_close_to_a_civilian(scenario_dict):
    d = copy.deepcopy(scenario_dict)
    d["contacts"].append({"id": "C99", "class": "hostile", "pos": [1500, 450, 0], "points": 40,
                           "engage_needs": {"light": 1}, "window_s": [100, 800]})
    s = Scenario.from_dict(d)
    c99 = s.contact_by_id()["C99"]  # à 150 m de C03 (civil, [1500, 300, 0]) : sous le rayon par défaut (200 m)
    text, winnable, category = diagnose(s, {}, c99)
    assert category == "r7"
    assert winnable is False
    assert "R7" in text


def test_r7_does_not_block_a_hostile_far_from_protected_contacts(scenario_dict):
    s = Scenario.from_dict(scenario_dict)
    c01 = s.contact_by_id()["C01"]  # à 300 m de C03 (civil) : au-delà du rayon par défaut (200 m)
    _, _, category = diagnose(s, {}, c01)
    assert category != "r7"


# ----- diagnose() : borne optimiste de repli (handin.planner absent de cette branche) ----------

def test_heuristic_fallback_marks_a_reachable_idle_contact_as_winnable(scenario_dict, monkeypatch):
    monkeypatch.setattr(swann_demo, "HAS_REAL_PLANNER", False)  # force the fallback, planner now merged
    s = Scenario.from_dict(scenario_dict)
    c01 = s.contact_by_id()["C01"]  # L01 (light, idle) est à portée en ligne directe dans la fenêtre
    text, winnable, category = diagnose(s, {}, c01)
    assert category == "a_gagner"
    assert winnable is True
    assert "non disponible" in text  # le rapport doit dire que c'est une estimation, pas un fait vérifié


def test_heuristic_fallback_marks_an_out_of_reach_contact_as_blocked(scenario_dict, monkeypatch):
    monkeypatch.setattr(swann_demo, "HAS_REAL_PLANNER", False)
    d = copy.deepcopy(scenario_dict)
    d["contacts"].append({"id": "C98", "class": "hostile", "pos": [500_000, 0, 0], "points": 40,
                           "engage_needs": {"light": 1}, "window_s": [100, 150]})
    s = Scenario.from_dict(d)
    c98 = s.contact_by_id()["C98"]  # bien trop loin pour tenir dans la fenêtre à vitesse max
    text, winnable, category = diagnose(s, {}, c98)
    assert category == "hors_de_portee"
    assert winnable is False


# ----- build_report() ne doit jamais planter, même sur un plan invalide ou malformé ------------

def test_build_report_does_not_crash_on_an_unknown_aircraft_id(tmp_path, scenario, plan):
    bad = copy.deepcopy(plan)
    bad["routes"].append({"aircraft": "XX99", "waypoints": [{"t": 0, "x": 0, "y": 0, "z": 0}]})
    res_ok, res_bad = evaluate(scenario, plan), evaluate(scenario, bad)
    gained, lost, missed, diag = build_view(scenario, bad, res_bad, plan, res_ok, tmp_path / "view.html")
    build_report(scenario, bad, res_bad, res_ok, gained, lost, missed, diag, tmp_path / "explication.md")
    assert "Identifiant d'avion inconnu" in (tmp_path / "explication.md").read_text(encoding="utf-8")


def test_build_report_does_not_crash_on_a_plan_without_routes(tmp_path, scenario, plan):
    malformed = {"seed": scenario.seed}  # pas de clé "routes" du tout
    res_ok, res_bad = evaluate(scenario, plan), evaluate(scenario, malformed)
    gained, lost, missed, diag = build_view(scenario, malformed, res_bad, plan, res_ok, tmp_path / "view.html")
    build_report(scenario, malformed, res_bad, res_ok, gained, lost, missed, diag, tmp_path / "explication.md")
    assert (tmp_path / "explication.md").exists()

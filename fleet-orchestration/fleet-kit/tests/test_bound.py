"""tools/bound.py : la borne n'est jamais sous un plan valide (cas positifs), et elle bouge quand elle le doit (cas négatifs).

Un détecteur se teste sur un cas où il doit réagir et un cas où il ne doit pas : sans le contrôle négatif,
une borne constante énorme passerait tous les tests « borne >= score ».
"""
import copy
import json
import sys
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "tools"))

from fleetkit.baseline import greedy_plan  # noqa: E402
from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import Scenario  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
import bound as B  # noqa: E402


@pytest.mark.parametrize("level,seed", [("L1", 0), ("L1", 1), ("L2", 0), ("L3", 0), ("L3", 3), ("L4", 0), ("L4", 3)])
def test_bound_is_above_the_greedy_plan(level, seed):
    sc = Scenario.from_dict(generate(level, seed))
    res = evaluate(sc, greedy_plan(sc))
    assert res.valid
    assert B.bound(sc)["bound"] >= res.score


@pytest.mark.parametrize("name,level", [("L3-seed3", "L3"), ("L4-seed3", "L4")])
def test_bound_is_above_the_team_plans(name, level):
    sc = Scenario.from_dict(generate(level, 3))
    plan = json.loads((KIT / "examples" / "plans" / f"{name}.plan.json").read_text())
    res = evaluate(sc, plan)
    assert res.valid
    assert B.bound(sc)["bound"] >= res.score


def test_bound_is_tight_enough_to_mean_something():
    """Sans cela, une borne énorme passerait tout. L4 seed 3 : le plan d'équipe fait plus de 40 % de la borne."""
    sc = Scenario.from_dict(generate("L4", 3))
    plan = json.loads((KIT / "examples" / "plans" / "L4-seed3.plan.json").read_text())
    assert evaluate(sc, plan).score / B.bound(sc)["bound"] > 0.4


def test_no_effector_means_no_hostile_points():
    """Cas négatif : sans effecteur, aucun hostile n'est engageable, la borne ne garde que les inconnus."""
    d = generate("L3", 0)
    d["aircraft"] = [a for a in d["aircraft"] if a["type"] != "effector"]
    out = B.bound(Scenario.from_dict(d))
    assert out["hostiles"] == 0.0
    assert out["bound"] == out["unknown"]


def test_r7_removes_a_hostile_from_the_bound():
    """Cas négatif : un civil posé à 10 m d'un hostile rend ce hostile inengageable (R7), la borne baisse."""
    d = generate("L2", 0)
    sc = Scenario.from_dict(d)
    before = B.bound(sc)["hostiles"]
    target = max((c for c in d["contacts"] if c["class"] == "hostile"), key=lambda c: c["points"])
    d2 = copy.deepcopy(d)
    d2["contacts"].append({"id": "C99", "class": "civilian", "pos": [target["pos"][0] + 10, target["pos"][1], 0]})
    assert B.bound(Scenario.from_dict(d2))["hostiles"] < before


def test_energy_limits_the_bound():
    """Cas négatif : des batteries à 1 % empêchent tout vol utile, la borne tombe à zéro."""
    d = generate("L2", 0)
    for a in d["aircraft"]:
        a["battery_pct"] = 1.0
    assert B.bound(Scenario.from_dict(d))["bound"] == 0.0


def test_a_window_that_closes_before_arrival_removes_the_contact():
    """Cas négatif : une fenêtre qui se ferme à 1 s est inatteignable (observation + confirmation)."""
    d = generate("L2", 0)
    before = B.bound(Scenario.from_dict(d))["bound"]
    for c in d["contacts"]:
        if c["class"] in ("hostile", "unknown"):
            c["window_s"] = [0.0, 1.0]
    assert B.bound(Scenario.from_dict(d))["bound"] < before
    assert B.bound(Scenario.from_dict(d))["bound"] == 0.0


def test_the_bound_is_deterministic():
    sc = Scenario.from_dict(generate("L3", 7))
    assert B.bound(sc) == B.bound(sc)

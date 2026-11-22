"""demo/opsview : la vue opérateur reste autonome, exacte et honnête sur ce qu'elle ne sait pas.

Cas positifs : la page n'appelle aucun réseau, son modèle se relit, les chiffres de flotte et de contacts viennent du plan.
Cas négatifs : un hostile à moins de 200 m d'un civil reçoit la raison R7 ; un contact non servi sans diagnostic n'a pas de
raison inventée ; une raison fournie est reprise telle quelle.
"""
import copy
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]
OPS = KIT / "demo" / "opsview"
sys.path.insert(0, str(KIT))
sys.path.insert(0, str(OPS))

from fleetkit.baseline import greedy_plan  # noqa: E402
from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import Scenario, parse_plan  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
import opsview  # noqa: E402


@pytest.fixture(scope="module")
def case():
    sc = Scenario.from_dict(generate("L3", 1))
    return sc, greedy_plan(sc)


def _model(html: str) -> dict:
    return json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S).group(1))


def test_the_page_is_self_contained(case):
    page = opsview.OpsViewer(*case, title="a <b> title").html()
    assert "<title>a &lt;b&gt; title</title>" in page
    assert not re.search(r"(?:src|href)\s*=\s*[\"']?https?:", page)
    assert "@import" not in page and "fetch(" not in page and "XMLHttpRequest" not in page


def test_the_model_carries_the_kit_verdict_and_the_ops_data(case):
    sc, plan = case
    m = _model(opsview.OpsViewer(sc, plan).html())
    res = evaluate(sc, plan)
    assert m["plan"]["score"] == round(res.score, 1)
    served = {cid for cid, c in m["ops"]["contacts"].items() if c["served_t"] is not None}
    assert served == set(res.served) & set(m["ops"]["contacts"])
    fleet = m["ops"]["fleet"]
    assert sum(f["total"] for f in fleet.values()) == len(sc.aircraft)
    routes = parse_plan(plan)[0]
    used = sum(1 for r in routes.values() if any(w.action in ("observe", "engage") for w in r.waypoints))
    assert sum(f["used"] for f in fleet.values()) == used
    assert m["ops"]["feed"] == sorted(m["ops"]["feed"], key=lambda x: (x["t"], x["kind"], x["aid"]))


def test_an_r7_blocked_hostile_gets_the_exact_r7_reason():
    d = generate("L2", 0)
    target = max((c for c in d["contacts"] if c["class"] == "hostile"), key=lambda c: c["points"])
    d2 = copy.deepcopy(d)
    d2["contacts"].append({"id": "C99", "class": "civilian", "pos": [target["pos"][0] + 10, target["pos"][1], 0]})
    sc = Scenario.from_dict(d2)
    ops = opsview.OpsViewer(sc, greedy_plan(sc)).model()["ops"]
    reason = ops["contacts"][target["id"]]["reason"]
    assert reason["cat"] == "r7" and "C99" in reason["text"] and "10 m" in reason["text"]


def test_an_unserved_contact_without_diagnosis_is_not_given_an_invented_reason(case):
    sc, plan = case
    ops = opsview.OpsViewer(sc, plan).model()["ops"]
    unserved = [c for c in ops["contacts"].values() if c["served_t"] is None and not (c["r7"] and c["r7"]["blocked"])]
    assert unserved, "the case must leave a non-R7 contact unserved for this check"
    assert all(c["reason"]["cat"] == "unknown" for c in unserved)


def test_a_provided_reason_is_used():
    d = generate("L3", 1)
    sc = Scenario.from_dict(d)
    plan = greedy_plan(sc)
    base = opsview.OpsViewer(sc, plan).model()["ops"]["contacts"]
    cid = next(c for c, i in base.items() if i["served_t"] is None and not (i["r7"] and i["r7"]["blocked"]))
    diag = {cid: ("x", True, "concurrence")}
    got = opsview.OpsViewer(sc, plan, reasons=opsview.reasons_from_diagnosis(diag)).model()["ops"]["contacts"][cid]
    assert got["reason"]["cat"] == "concurrence" and "resource competition" in got["reason"]["text"]


def test_drone_outcomes_cover_the_fleet_and_match_the_effector_count(case):
    sc, plan = case
    m = opsview.OpsViewer(sc, plan).model()
    ops = m["ops"]
    assert set(ops["drones"]) == {a.id for a in sc.aircraft}
    o = ops["outcome"]
    assert o["strike"] + o["spot"] + o["wasted"] + o["idle"] == len(sc.aircraft)
    engages = [k for k in m["marks"] if k["kind"] == "engage"]
    assert len(engages) == m["plan"]["effectors"]
    assert o["wasted_eff"] == sum(1 for k in engages if k["contact"] not in m["served"])
    total = sum(d["pts"] for d in ops["drones"].values())
    assert abs(total - sum(c["points"] for c in ops["contacts"].values() if c["served_t"] is not None)) < 0.1 * len(ops["drones"])


def test_a_tasked_drone_that_serves_nothing_is_wasted_and_its_effector_counted():
    class A:
        def __init__(self, i): self.id = i
    class C:
        def __init__(self, i, p): self.id, self.points = i, p
    sc = type("S", (), {"aircraft": [A("S1"), A("L1"), A("L2"), A("L3")], "contacts": [C("C1", 50), C("C2", 30)]})()
    model = {"served": {"C1": 100.0}, "marks": [
        {"aid": "S1", "contact": "C1", "kind": "observe", "t0": 10, "t1": 30, "ok": True},
        {"aid": "L1", "contact": "C1", "kind": "engage", "t": 100.0},
        {"aid": "L2", "contact": "C2", "kind": "engage", "t": 120.0}]}
    drones, o = opsview.drone_outcomes(sc, model)
    assert [drones[k]["cat"] for k in ("S1", "L1", "L2", "L3")] == ["spot", "strike", "wasted", "idle"]
    assert o["wasted_eff"] == 1 and drones["S1"]["pts"] == 25.0 and drones["L2"]["pts"] == 0


@pytest.mark.skipif(shutil.which("node") is None, reason="node n'est pas installé")
def test_the_page_script_is_valid_javascript():
    proc = subprocess.run(["node", "--check", str(OPS / "app.js")], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr

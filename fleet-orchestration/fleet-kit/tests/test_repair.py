"""Repair phase of handin/planner.py (ruin and recreate around the best plan).

Positive cases: a loaded plan keeps its score, dropping a scout also drops the strikes it confirmed, a repair never
returns a plan worse than its start nor an invalid one. Negative cases: the flag off or a small fleet skips the
phase; a start plan that does not validate gives no planner instead of a broken one.
"""
import copy
import sys
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(KIT), str(KIT / "handin")]

import params  # noqa: E402
import planner  # noqa: E402
from fk.model import SCOUT, Scenario  # noqa: E402
from fk.scorer import evaluate  # noqa: E402
from fleetkit.generator import generate  # noqa: E402

pytestmark = pytest.mark.skipif(planner._routing is None, reason="the repair phase needs the team router")


@pytest.fixture(scope="module")
def case():
    data = generate("L3", 1)
    sc = Scenario.from_dict(data)
    plan, _ = planner.build(sc, planner._key(sc, 1.0, {}), planner.time.monotonic() + 60, planner.N_SCOUTS,
                            planner.RoutedPlanner, True)
    res = evaluate(sc, plan)
    assert res.valid and res.score > 0
    return data, sc, plan, res.score


def _engaged(plan, cid):
    return [r["aircraft"] for r in plan["routes"]
            if any(w.get("action") == "engage" and w.get("target") == cid for w in r["waypoints"])]


def test_a_loaded_plan_keeps_its_score_and_its_tasks(case):
    _, sc, plan, score = case
    p, served = planner._load_plan(sc, plan, [], planner.time.monotonic() + 60)
    assert p is not None and abs(p.score - score) < 1e-6
    assert served == set(evaluate(sc, plan).served)
    flying = {r["aircraft"] for r in plan["routes"]}
    assert {s for s, t in p.tasks.items() if t} <= flying


def test_dropping_a_scout_drops_the_strikes_it_confirmed(case):
    _, sc, plan, _ = case
    p0, _ = planner._load_plan(sc, plan, [], planner.time.monotonic() + 60)
    sid = max((s for s in p0.tasks if p0.tasks[s]), key=lambda s: len(p0.tasks[s]))
    observed = {c.id for c in p0.tasks[sid]}
    p, served = planner._load_plan(sc, plan, [sid], planner.time.monotonic() + 60)
    assert p is not None and sid not in p.routes and p.tasks[sid] == []
    left = p._plan({})
    for cid in observed:
        assert not _engaged(left, cid)
    assert evaluate(sc, left).valid


def test_a_start_plan_that_does_not_validate_gives_no_planner(case):
    _, sc, plan, _ = case
    broken = copy.deepcopy(plan)
    broken["routes"][0]["waypoints"][0]["x"] = 1e6  # not the home position: R1
    assert not evaluate(sc, broken).valid
    p, served = planner._load_plan(sc, broken, [], planner.time.monotonic() + 60)
    assert p is None and served == set()


def test_a_repair_is_never_worse_nor_invalid(case, monkeypatch):
    _, sc, plan, score = case
    monkeypatch.setattr(params, "FLEET_ITERS", 1)
    monkeypatch.setattr(params, "LNS_ITERS", 3)
    got, out = planner._repair(sc, (score, plan), planner.time.monotonic() + 60, 0)
    res = evaluate(sc, out)
    assert res.valid and got >= score - 1e-6 and abs(res.score - got) < 1e-6


def test_the_flag_off_skips_the_repair_phase(case, monkeypatch):
    data, sc, _, _ = case
    called = []
    monkeypatch.setattr(planner, "_repair_phase", lambda *a, **k: called.append(1) or a[2])
    monkeypatch.setattr(params, "LNS", False)
    monkeypatch.setattr(params, "FLEET_ITERS", 1)
    monkeypatch.setattr(planner, "MAX_WORKERS", 2)
    planner.solve(sc, data, 20.0)
    assert called == []


def test_a_small_fleet_skips_the_repair_phase(monkeypatch):
    data = generate("L2", 0)
    sc = Scenario.from_dict(data)
    assert len(sc.aircraft) < params.LNS_MIN_AC
    called = []
    monkeypatch.setattr(planner, "_repair_phase", lambda *a, **k: called.append(1) or a[2])
    monkeypatch.setattr(params, "FLEET_ITERS", 1)
    monkeypatch.setattr(planner, "MAX_WORKERS", 2)
    planner.solve(sc, data, 20.0)
    assert called == []


def test_the_repair_phase_runs_on_a_large_fleet_and_its_plan_is_valid(case, monkeypatch):
    data, sc, _, _ = case
    called = []
    real = planner._repair_phase
    monkeypatch.setattr(planner, "_repair_phase", lambda *a, **k: called.append(1) or real(*a, **k))
    monkeypatch.setattr(params, "FLEET_ITERS", 1)
    monkeypatch.setattr(params, "LNS_ITERS", 2)
    monkeypatch.setattr(planner, "MAX_WORKERS", 2)
    plan = planner.solve(sc, data, 30.0)
    assert called == [1] and evaluate(sc, plan).valid
    assert all(sc.aircraft_by_id()[r["aircraft"]].type == SCOUT or r["waypoints"] for r in plan["routes"])


def test_the_search_plan_is_on_disk_before_the_repair_starts(case, monkeypatch):
    data, sc, _, _ = case
    events = []
    monkeypatch.setattr(planner, "_checkpoint", lambda plan: events.append(("kept", evaluate(sc, plan).score)))
    monkeypatch.setattr(planner, "_repair_phase", lambda *a, **k: events.append(("repair", a[2][0])) or a[2])
    monkeypatch.setattr(params, "FLEET_ITERS", 1)
    monkeypatch.setattr(planner, "MAX_WORKERS", 2)
    planner.solve(sc, data, 30.0)
    assert [e[0] for e in events] == ["kept", "repair"]
    assert events[0][1] > 0 and abs(events[0][1] - events[1][1]) < 1e-6

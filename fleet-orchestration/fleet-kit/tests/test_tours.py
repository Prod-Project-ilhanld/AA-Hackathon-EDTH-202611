"""Tours-first model (handin/tours.py) and the guided build of handin/planner.py.

Positive cases: every planned tour is feasible in the model and no contact is planned twice; the planned scout is
tried first; a guided build is valid. Negative cases: a tour that cannot meet a window or the battery is refused;
R7-blocked hostiles and hostiles worth less than their strike are never planned.
"""
import random
import sys
import time
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(KIT), str(KIT / "handin")]

import planner  # noqa: E402
import targets  # noqa: E402
import tours  # noqa: E402
from fk.model import HOSTILE, SCOUT, Scenario  # noqa: E402
from fk.scorer import evaluate  # noqa: E402
from fleetkit.generator import generate  # noqa: E402


@pytest.fixture(scope="module")
def case():
    sc = Scenario.from_dict(generate("L3", 1))
    return sc, tours.Model(sc, skip=lambda c: targets.skip(sc, c))


def test_planned_tours_are_feasible_and_disjoint(case):
    sc, m = case
    tour = m.solve(random.Random(0), iters=20)
    planned = [c for seq in tour.values() for c in seq]
    assert planned and len(planned) == len(set(planned))
    assert all(m.tour_cost(sid, seq) is not None for sid, seq in tour.items())
    assert set(planned) <= set(m.value)


def test_a_tour_that_misses_a_window_is_refused(case, monkeypatch):
    sc, m = case
    sid = m.scouts[0].id
    cid = next(iter(m.value))
    monkeypatch.setitem(m.eng_by, cid, m.r.obs_dwell_s - 1.0)  # the observation cannot end in time
    assert m.tour_cost(sid, [cid]) is None


def test_a_tour_beyond_the_battery_is_refused(case, monkeypatch):
    sc, m = case
    monkeypatch.setattr(tours, "BATTERY", 1e-6)
    sid = m.scouts[0].id
    assert m.tour_cost(sid, [next(iter(m.value))]) is None


def test_blocked_or_unprofitable_hostiles_are_never_planned():
    d = generate("L2", 0)
    sc = Scenario.from_dict(d)
    m = tours.Model(sc, skip=lambda c: targets.skip(sc, c))
    for c in sc.contacts:
        if c.cls == HOSTILE and targets.skip(sc, c):
            assert c.id not in m.value
    assert all(v > 0 for v in m.value.values())


@pytest.mark.skipif(planner._routing is None, reason="the guided build needs the team router")
def test_the_planned_scout_is_tried_first_and_a_guided_build_is_valid(case):
    sc, m = case
    some = next(iter(m.value))
    far = max((a for a in sc.aircraft if a.type == SCOUT), key=lambda s: planner.hdist(s.home, m.contacts[some].pos))
    p = planner.TourPlanner(sc, time.monotonic() + 60, planner.N_SCOUTS, {some: far.id})
    assert p._scouts_for(m.contacts[some])[0].id == far.id
    plan, _ = planner.build_guided(sc, m, random.Random(1), time.monotonic() + 120)
    res = evaluate(sc, plan)
    assert res.valid and res.score > 0

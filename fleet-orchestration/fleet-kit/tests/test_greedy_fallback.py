"""Greedy fallback of handin/planner.py: a failure path writes the kit's greedy plan instead of an empty one,
and the normal path never calls it."""
import copy
import sys
import time
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(KIT), str(KIT / "handin")]

import planner  # noqa: E402
from fk.model import Scenario  # noqa: E402
from fk.scorer import evaluate  # noqa: E402
from fleetkit.generator import generate  # noqa: E402


@pytest.fixture
def setup(monkeypatch):
    data = generate("L2", 0)
    monkeypatch.setattr(planner, "T0", time.monotonic())  # the alarm budget counts from process start
    monkeypatch.setattr(planner, "MAX_WORKERS", 1)        # serial search: _search is called in this process
    return data, Scenario.from_dict(data)


def failing_search(*_args, **_kwargs):
    return (-1.0, None)


def test_every_build_failing_returns_the_greedy_plan(setup, monkeypatch):
    data, sc = setup
    monkeypatch.setattr(planner, "_search", failing_search)
    plan = planner.solve(sc, data, 3.0)
    res = evaluate(sc, plan)
    assert plan["routes"] and res.valid and res.score > 0


def test_invalid_best_plan_returns_the_greedy_plan(setup, monkeypatch):
    data, sc = setup
    wrong_seed = {"seed": sc.seed + 1, "routes": []}
    assert not evaluate(sc, wrong_seed).valid  # the stub plan is invalid on purpose
    monkeypatch.setattr(planner, "_search", lambda *a, **k: (5.0, wrong_seed))
    plan = planner.solve(sc, data, 3.0)
    res = evaluate(sc, plan)
    assert plan["routes"] and res.valid and res.score > 0


def test_no_time_before_the_alarm_returns_the_empty_plan(setup, monkeypatch):
    data, sc = setup
    monkeypatch.setattr(planner, "_search", failing_search)
    monkeypatch.setattr(planner, "T0", time.monotonic() - 100.0)  # the alarm is long gone
    assert planner.solve(sc, data, 3.0)["routes"] == []


def test_normal_run_never_calls_the_fallback(setup, monkeypatch):
    data, sc = setup

    def boom(_scenario):
        raise AssertionError("the greedy fallback ran on the normal path")

    monkeypatch.setattr(planner, "_greedy_fallback", boom)
    plan = planner.solve(sc, data, 3.0)
    assert plan["routes"] and evaluate(sc, plan).valid


def test_nothing_to_gain_stays_empty(setup, monkeypatch):
    data, _ = setup
    d = copy.deepcopy(data)
    d["contacts"] = []
    sc = Scenario.from_dict(d)
    monkeypatch.setattr(planner, "_search", failing_search)
    plan = planner.solve(sc, d, 3.0)
    assert plan["routes"] == [] and evaluate(sc, plan).valid

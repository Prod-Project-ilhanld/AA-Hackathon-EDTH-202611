"""Task 11 in handin/planner.py: the plan never scores below the kit greedy plan (KEEP_BETTER_GREEDY),
and with the flag off the planner is the same as before."""
import json
import sys
import time
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(KIT), str(KIT / "handin")]

import planner  # noqa: E402
from fk.baseline import greedy_plan  # noqa: E402
from fk.model import Scenario  # noqa: E402
from fk.scorer import evaluate  # noqa: E402
from fleetkit.generator import generate  # noqa: E402


@pytest.fixture
def setup(monkeypatch):
    data = generate("L2", 0)
    monkeypatch.setattr(planner, "T0", time.monotonic())  # the alarm budget counts from process start
    monkeypatch.setattr(planner, "MAX_WORKERS", 1)        # serial search, in this process
    monkeypatch.setattr(planner.params, "FLEET_ITERS", 2)  # reproducible plan
    return data, Scenario.from_dict(data)


def test_flag_off_never_builds_greedy_and_ours_is_unchanged(setup, monkeypatch):
    data, sc = setup

    def boom(_scenario):
        raise AssertionError("the greedy plan was built with KEEP_BETTER_GREEDY off")

    monkeypatch.setattr(planner.params, "KEEP_BETTER_GREEDY", False)
    with monkeypatch.context() as m:
        m.setattr(planner, "_greedy", boom)
        off = json.dumps(planner.solve(sc, data, 10.0))
    monkeypatch.setattr(planner.params, "KEEP_BETTER_GREEDY", True)
    on = json.dumps(planner.solve(sc, data, 10.0))
    assert evaluate(sc, json.loads(on)).score > evaluate(sc, greedy_plan(sc)).score  # ours wins on this seed
    assert on == off  # ... so the flag changes nothing


def test_weak_plan_loses_to_the_greedy_plan(setup, monkeypatch):
    data, sc = setup
    full = greedy_plan(sc)
    base = evaluate(sc, full).score
    weak = None
    for route in full["routes"]:  # a valid plan that scores something, but less than the greedy plan
        cand = {"seed": sc.seed, "routes": [route]}
        res = evaluate(sc, cand)
        if res.valid and 0 < res.score < base:
            weak = (res.score, cand)
            break
    assert weak is not None
    monkeypatch.setattr(planner.params, "KEEP_BETTER_GREEDY", True)
    monkeypatch.setattr(planner, "_search", lambda *a, **k: weak)
    plan = planner.solve(sc, data, 10.0)
    assert evaluate(sc, plan).score == pytest.approx(base)
    monkeypatch.setattr(planner.params, "KEEP_BETTER_GREEDY", False)
    assert planner.solve(sc, data, 10.0) == weak[1]  # flag off: the weak plan stays

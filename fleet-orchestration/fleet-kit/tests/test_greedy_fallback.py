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


def test_normal_run_never_calls_the_fallback_when_the_flag_is_off(setup, monkeypatch):
    data, sc = setup
    monkeypatch.setattr(planner.params, "KEEP_BETTER_GREEDY", False)

    def boom(_scenario):
        raise AssertionError("the greedy fallback ran on the normal path")

    monkeypatch.setattr(planner, "_greedy_fallback", boom)
    plan = planner.solve(sc, data, 3.0)
    assert plan["routes"] and evaluate(sc, plan).valid


def test_a_greedy_plan_that_scores_strictly_more_replaces_ours(setup, monkeypatch):
    data, sc = setup
    ours = {"seed": sc.seed, "routes": []}  # valid, scores 0
    assert evaluate(sc, ours).valid
    monkeypatch.setattr(planner, "_search", lambda *a, **k: (1.0, ours))
    plan = planner.solve(sc, data, 3.0)
    assert plan["routes"] and evaluate(sc, plan).score > evaluate(sc, ours).score


def test_a_tie_or_a_better_plan_of_ours_is_kept_untouched(setup, monkeypatch):
    data, sc = setup
    from fk.baseline import greedy_plan
    ours = greedy_plan(sc)
    same = copy.deepcopy(ours)
    monkeypatch.setattr(planner, "_search", lambda *a, **k: (evaluate(sc, ours).score, ours))
    monkeypatch.setattr(planner, "_greedy_fallback", lambda _s: same)
    assert planner.solve(sc, data, 3.0) is ours          # tie: strictly more is required
    monkeypatch.setattr(planner, "_greedy_fallback", lambda _s: {"seed": sc.seed, "routes": []})
    assert planner.solve(sc, data, 3.0) is ours          # greedy worse: ours stays


def test_flag_off_keeps_our_plan_even_when_greedy_is_better(setup, monkeypatch):
    data, sc = setup
    ours = {"seed": sc.seed, "routes": []}
    monkeypatch.setattr(planner.params, "KEEP_BETTER_GREEDY", False)
    monkeypatch.setattr(planner, "_search", lambda *a, **k: (1.0, ours))
    assert planner.solve(sc, data, 3.0) is ours


def test_a_large_fleet_skips_the_greedy_comparison(setup, monkeypatch):
    data, sc = setup
    ours = {"seed": sc.seed, "routes": []}
    monkeypatch.setattr(planner.params, "KEEP_GREEDY_MAX_AC", len(sc.aircraft) - 1)

    def boom(_scenario):
        raise AssertionError("the greedy ran on a fleet above the limit")

    monkeypatch.setattr(planner, "_search", lambda *a, **k: (1.0, ours))
    monkeypatch.setattr(planner, "_greedy_fallback", boom)
    assert planner.solve(sc, data, 3.0) is ours


def test_a_crash_while_scoring_the_greedy_plan_keeps_ours(setup, monkeypatch):
    data, sc = setup
    ours = {"seed": sc.seed, "routes": []}
    monkeypatch.setattr(planner, "_search", lambda *a, **k: (1.0, ours))
    calls = {"n": 0}
    real = planner.evaluate

    def flaky(scenario, plan):
        calls["n"] += 1
        if calls["n"] >= 2:
            raise RuntimeError("boom")
        return real(scenario, plan)

    monkeypatch.setattr(planner, "evaluate", flaky)
    monkeypatch.setattr(planner, "_greedy_fallback", lambda _s: {"seed": sc.seed, "routes": [{"aircraft": "X", "waypoints": []}]})
    assert planner.solve(sc, data, 3.0) is ours


def test_our_plan_is_checkpointed_before_the_greedy_runs(setup, monkeypatch):
    data, sc = setup
    ours = {"seed": sc.seed, "routes": []}
    seen = []
    monkeypatch.setattr(planner, "_checkpoint", lambda plan: seen.append(("kept", plan)))
    monkeypatch.setattr(planner, "_search", lambda *a, **k: (1.0, ours))

    def greedy(_scenario):
        seen.append(("greedy", None))
        return None

    monkeypatch.setattr(planner, "_greedy_fallback", greedy)
    assert planner.solve(sc, data, 3.0) is ours
    assert [k for k, _ in seen] == ["kept", "greedy"] and seen[0][1] is ours


def test_nothing_to_gain_stays_empty(setup, monkeypatch):
    data, _ = setup
    d = copy.deepcopy(data)
    d["contacts"] = []
    sc = Scenario.from_dict(d)
    monkeypatch.setattr(planner, "_search", failing_search)
    plan = planner.solve(sc, d, 3.0)
    assert plan["routes"] == [] and evaluate(sc, plan).valid

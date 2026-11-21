"""CP1 safety checks: the hand-in run like the jury (fresh copy of handin/, subprocess, explicit env).

Every plan is scored with the OFFICIAL fleetkit.scorer.evaluate. Hooks used (see handin/planner.py):
PLANNER_BUDGET_S, PLANNER_ALARM_S, PLANNER_WORKERS, FLEET_ITERS, FLEET_INJECT_FAIL, FLEET_INJECT_HANG.
Run from fleet-kit/: `python3 -m pytest -q tests/test_cp1_safety.py`.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import Scenario  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402

HANDIN = os.path.join(KIT, "handin")


def run_handin(scenario, extra_env, kit_on_path=True, timeout=30):
    """Copies handin/ to a temp dir and runs `planner.py scen plan` there.

    scenario: a dict (written as JSON), a str (written verbatim) or None (no file).
    Returns (returncode, wall seconds, plan text or None, stderr tail).
    """
    tmp = tempfile.mkdtemp(prefix="cp1_")
    try:
        team = os.path.join(tmp, "team")
        shutil.copytree(HANDIN, team, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        scen, plan = os.path.join(tmp, "scenario.json"), os.path.join(tmp, "plan.json")
        if isinstance(scenario, dict):
            with open(scen, "w") as f:
                json.dump(scenario, f)
        elif isinstance(scenario, str):
            with open(scen, "w") as f:
                f.write(scenario)
        env = {"PATH": os.environ.get("PATH", ""), "HOME": tmp, "PYTHONDONTWRITEBYTECODE": "1",
               "PLANNER_WORKERS": "2"}
        if kit_on_path:
            env["PYTHONPATH"] = KIT
        env.update(extra_env)
        t0 = time.time()
        proc = subprocess.run([sys.executable, "planner.py", scen, plan], env=env, cwd=team,
                              capture_output=True, text=True, timeout=timeout)
        dt = time.time() - t0
        text = None
        if os.path.exists(plan):
            with open(plan) as f:
                text = f.read()
        return proc.returncode, dt, text, proc.stderr[-400:]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def assert_valid(data, text):
    assert text is not None, "no plan.json written"
    plan = json.loads(text)
    res = evaluate(Scenario.from_dict(data), plan)
    assert res.valid, [str(v) for v in res.violations[:3]]
    return plan


def test_injected_failure_writes_the_greedy_plan():
    """solve() crashed: the kit's greedy plan (valid, scores something) beats the empty plan."""
    data = generate("L2", 0)
    code, _, text, err = run_handin(data, {"FLEET_INJECT_FAIL": "1", "PLANNER_BUDGET_S": "3"})
    assert code == 0, err
    plan = assert_valid(data, text)
    assert plan["routes"], "expected the greedy fallback plan, got the empty one"
    assert evaluate(Scenario.from_dict(data), plan).score > 0


def test_injected_failure_with_the_alarm_too_close_writes_the_empty_plan():
    """Fewer than FALLBACK_MIN_LEFT_S before the alarm: no time for the greedy plan, the empty one stays."""
    data = generate("L2", 0)
    code, _, text, err = run_handin(
        data, {"FLEET_INJECT_FAIL": "1", "PLANNER_BUDGET_S": "3", "PLANNER_ALARM_S": "6"})
    assert code == 0, err
    assert assert_valid(data, text)["routes"] == []


def test_short_deadline_is_respected():
    data = generate("L4", 3)
    code, dt, text, err = run_handin(data, {"PLANNER_BUDGET_S": "3"})
    assert code == 0, err
    assert_valid(data, text)
    assert dt < 4.5, "took %.1fs with a 3 s budget" % dt


def test_hang_is_caught_by_alarm_with_best_plan():
    data = generate("L4", 3)
    code, dt, text, err = run_handin(
        data, {"FLEET_INJECT_HANG": "1", "PLANNER_BUDGET_S": "3", "PLANNER_ALARM_S": "6"}, timeout=20)
    assert code == 0, err
    assert assert_valid(data, text)["routes"], "alarm wrote an empty plan, expected the kept best plan"
    assert dt < 7.5, "took %.1fs with a 6 s alarm" % dt


def test_official_kit_missing_still_valid():
    data = generate("L2", 0)
    code, _, text, err = run_handin(data, {"PLANNER_BUDGET_S": "3"}, kit_on_path=False)
    assert code == 0, err
    assert_valid(data, text)


def test_missing_scenario_file():
    code, _, text, err = run_handin(None, {"PLANNER_BUDGET_S": "3"})
    assert code == 0, err
    assert text is not None, "no plan.json written"
    assert json.loads(text)["routes"] == []


def test_malformed_scenario_file():
    code, _, text, err = run_handin("{", {"PLANNER_BUDGET_S": "3"})
    assert code == 0, err
    assert text is not None, "no plan.json written"


def test_fleet_iters_is_deterministic_across_hash_seeds():
    data = generate("L3", 3)
    # the budget is only a safety net: FLEET_ITERS=3 must finish well before it
    common = {"FLEET_ITERS": "3", "PLANNER_BUDGET_S": "20"}
    runs = [run_handin(data, dict(common, PYTHONHASHSEED=h), timeout=40) for h in ("1", "2")]
    for code, _, text, err in runs:
        assert code == 0, err
        assert_valid(data, text)
    assert runs[0][2] == runs[1][2], "plan.json differs between PYTHONHASHSEED=1 and =2"


def _handin_sources(skip):
    for name in sorted(os.listdir(HANDIN)):
        if name.endswith(".py") and name not in skip:
            with open(os.path.join(HANDIN, name), encoding="utf-8") as f:
                yield name, f.read().splitlines()


def test_no_branching_on_level():
    # handin/fk/ is a subfolder, so listing handin/*.py already leaves it out
    hits = ["%s:%d: %s" % (n, i, l.strip()) for n, lines in _handin_sources({"check_handin.py", "check_policy.py", "policy.py"})
            for i, l in enumerate(lines, 1) if re.search(r"\.level\b", l)]
    assert not hits, hits


def test_no_direct_kit_import():
    hits = ["%s:%d: %s" % (n, i, l.strip()) for n, lines in _handin_sources({"check_handin.py", "check_policy.py", "policy.py"})
            for i, l in enumerate(lines, 1) if re.match(r"(from|import) fleetkit", l)]
    assert not hits, hits

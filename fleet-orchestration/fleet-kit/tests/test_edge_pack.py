"""Edge pack (tools/edge_pack.py): the planner writes a valid plan on every degenerate scenario, in time.

Also two negative controls: the harness must flag a planner that crashes and one that writes an invalid plan.
Run: `python3 -m pytest tests/test_edge_pack.py` from fleet-kit/.
"""
import sys
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "tools"))

import edge_pack  # noqa: E402


@pytest.mark.parametrize("name", list(edge_pack.CASES))
def test_planner_survives_case(name):
    r = edge_pack.run_case(name, budget="1")
    assert r["ok"], "%s: %s" % (name, r["why"])
    assert r["time"] < 20.0


def test_every_case_builds_a_scenario_the_kit_can_read():
    from fleetkit.model import Scenario
    for name in edge_pack.CASES:
        Scenario.from_dict(edge_pack.build(name))


def test_harness_flags_a_crashing_planner(tmp_path):
    bad = tmp_path / "planner.py"
    bad.write_text("import sys\nsys.exit(3)\n")
    r = edge_pack.run_case("no_scouts", planner=str(bad), timeout=30)
    assert not r["ok"] and "exit 3" in r["why"]


def test_harness_flags_a_swallowed_crash(tmp_path):
    """A planner that hits an internal error, prints it and falls back to a valid empty plan must not pass."""
    bad = tmp_path / "planner.py"
    seed = edge_pack.build("no_scouts")["seed"]  # the plan must echo the scenario seed to be valid
    bad.write_text("import json, sys\n"
                   "json.dump({'seed': %d, 'routes': []}, open(sys.argv[2], 'w'))\n"
                   "print('planner: KeyError: x', file=sys.stderr)\n" % seed)
    r = edge_pack.run_case("no_scouts", planner=str(bad), timeout=30)
    assert not r["ok"] and "swallowed" in r["why"], r


def test_harness_flags_giving_up_on_a_servable_case(tmp_path):
    """A planner that always answers with the empty plan fails the cases where something is servable."""
    lazy = tmp_path / "planner.py"
    seed = edge_pack.build("only_hostiles")["seed"]
    lazy.write_text("import json, sys\n"
                    "json.dump({'seed': %d, 'routes': []}, open(sys.argv[2], 'w'))\n" % seed)
    r = edge_pack.run_case("only_hostiles", planner=str(lazy), timeout=30)
    assert not r["ok"] and "gave up" in r["why"], r
    assert edge_pack.run_case("no_scouts", planner=str(lazy), timeout=30)["ok"]  # nothing servable: empty is right


def test_expectation_judge():
    assert edge_pack.judge_expectation("no_scouts", 0.0) == ""
    assert "validator" in edge_pack.judge_expectation("no_scouts", 5.0)
    assert edge_pack.judge_expectation("only_hostiles", 10.0) == ""
    assert "gave up" in edge_pack.judge_expectation("only_hostiles", 0.0)
    assert edge_pack.judge_expectation("window_exactly_dwell", 0.0) == ""  # no expectation: safety only


def test_every_expectation_names_a_real_case():
    assert set(edge_pack.EXPECT) <= set(edge_pack.CASES)
    assert set(edge_pack.ZERO).isdisjoint(edge_pack.POSITIVE)


def test_harness_flags_an_invalid_plan(tmp_path):
    bad = tmp_path / "planner.py"
    bad.write_text("import json, sys\n"
                   "json.dump({'seed': -1, 'routes': []}, open(sys.argv[2], 'w'))\n")
    r = edge_pack.run_case("no_scouts", planner=str(bad), timeout=30)
    assert not r["ok"] and "invalid" in r["why"]

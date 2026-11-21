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


def test_harness_flags_an_invalid_plan(tmp_path):
    bad = tmp_path / "planner.py"
    bad.write_text("import json, sys\n"
                   "json.dump({'seed': -1, 'routes': []}, open(sys.argv[2], 'w'))\n")
    r = edge_pack.run_case("no_scouts", planner=str(bad), timeout=30)
    assert not r["ok"] and "invalid" in r["why"]

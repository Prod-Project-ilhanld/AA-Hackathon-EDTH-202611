"""Edge-case pack through pytest (fast: PLANNER_BUDGET_S=3, PLANNER_WORKERS=2). Cases live in tools/edge.py."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

import edge  # noqa: E402


@pytest.mark.parametrize("name", list(edge.CASES))
def test_edge_case(name):
    reason, dt = edge.run_case(name, budget=3, workers=2)
    assert not reason, reason
    assert dt < 12, "took %.1fs with a 3 s budget" % dt

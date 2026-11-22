"""latest_ends of handin/planner.py: extending a scout tour keeps the observations of struck contacts early enough.

Positive cases: a struck task gets its first engagement minus the R4 margin; a tour extended after a strike still
confirms it (the full plan validates). Negative cases: a task never struck gets no bound; no struck task gives None.
"""
import sys
import time
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(KIT), str(KIT / "handin")]

import params  # noqa: E402
import planner  # noqa: E402
from fk.model import HOSTILE, Scenario  # noqa: E402
from fk.scorer import evaluate  # noqa: E402
from fleetkit.generator import generate  # noqa: E402

pytestmark = pytest.mark.skipif(planner._routing is None, reason="latest_ends belongs to the team router")


@pytest.fixture(scope="module")
def built():
    sc = Scenario.from_dict(generate("L3", 1))
    p = planner.RoutedPlanner(sc, time.monotonic() + 120, planner.N_SCOUTS)
    for c in sorted((c for c in sc.contacts if c.cls == HOSTILE), key=lambda c: -c.points):
        p.serve_hostile(c)
    return sc, p


def test_a_struck_task_is_bounded_by_its_first_strike_minus_the_margin(built):
    sc, p = built
    sid = next(s for s, t in p.tasks.items() if t)
    got = p._latest_ends(p.tasks[sid])
    assert got
    for cid, latest in got.items():
        first = min(r[-1]["t"] for r in p.routes.values() if r[-1].get("action") == "engage" and r[-1].get("target") == cid)
        assert abs(latest - (first - sc.rules.confirm_margin_s)) < 1e-9


def test_tasks_never_struck_get_no_bound(built):
    sc, p = built
    unstruck = [c for c in sc.contacts if c.cls == HOSTILE
                and not any(r[-1].get("target") == c.id for r in p.routes.values() if r[-1].get("action") == "engage")]
    assert unstruck
    assert p._latest_ends(unstruck[:3]) is None


def test_extending_tours_after_strikes_keeps_the_plan_valid(built):
    sc, p = built
    assert params.LATEST_ENDS
    res = evaluate(sc, p._plan({}))
    assert res.valid and res.score > 0
    multi = [s for s, t in p.tasks.items() if len(t) >= 2]
    assert multi, "the case must extend at least one tour after a strike"

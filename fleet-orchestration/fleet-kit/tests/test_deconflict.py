"""handin/deconflict.py: the R8 departure scheduler delays a take-off until the whole route is 40 m free.

Run from fleet-kit/: python3 tests/test_deconflict.py  (or pytest). Plain unittest, the official validator is the oracle.
"""
import copy
import os
import sys
import time
import types
import unittest

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [KIT, os.path.join(KIT, "handin"), os.path.join(KIT, "tests")]
try:
    import pytest  # noqa: F401
except ImportError:  # conftest only needs pytest.fixture
    stub = types.ModuleType("pytest")
    stub.fixture = lambda f=None, **k: (f if f else (lambda g: g))
    sys.modules["pytest"] = stub

from conftest import make_scenario_dict  # noqa: E402
from helpers import hop  # noqa: E402
from fk.model import Scenario, parse_plan  # noqa: E402
from fk.scorer import evaluate  # noqa: E402
from fk.validator import separation_item, separation_violation, validate  # noqa: E402
import deconflict  # noqa: E402
import planner as P  # noqa: E402


def make(d=None, cls=None):
    sc = Scenario.from_dict(d or make_scenario_dict())
    return sc, (cls or P.FastPlanner)(sc, time.monotonic() + 3600)


def r8(sc, plan):
    """R8 violations of a plan, checked directly (validate() stops at the first failing rules)."""
    from fk.validator import _r8
    routes, _ = parse_plan(plan)
    return _r8(sc, routes)


class Deconflict(unittest.TestCase):
    def setUp(self):
        self.old = deconflict.ENABLED
        deconflict.ENABLED = True

    def tearDown(self):
        deconflict.ENABLED = self.old

    def test_off_by_default_changes_nothing(self):
        deconflict.ENABLED = False
        sc, pl = make()
        pl.routes["S01"] = hop((0, 0))
        extra = {"S02": hop((0, 20))}
        before = copy.deepcopy(extra)
        self.assertTrue(deconflict.adjust(pl, extra))
        self.assertEqual(extra, before)

    def test_pad_conflict_is_resolved_by_a_ground_delay_of_the_whole_route(self):
        sc, pl = make()
        pl.routes["S01"] = hop((0, 0))
        extra = {"S02": hop((0, 20))}
        before = copy.deepcopy(extra["S02"])
        self.assertTrue(r8(sc, pl._plan(extra)), "the scenario must conflict without the scheduler")
        self.assertTrue(deconflict.adjust(pl, extra))
        deltas = {round(a["t"] - b["t"], 6) for a, b in zip(extra["S02"], before)}
        self.assertEqual(len(deltas), 1, "every waypoint must be shifted by the same delay (internal timing kept)")
        self.assertGreater(deltas.pop(), 0.0)
        self.assertEqual(r8(sc, pl._plan(extra)), [], "still an R8 violation after the delay")

    def test_it_is_a_minimal_delay_not_a_huge_one(self):
        sc, pl = make()
        pl.routes["S01"] = hop((0, 0))           # airborne from 0 to 120 s
        extra = {"S02": hop((0, 20))}
        deconflict.adjust(pl, extra)
        self.assertLess(extra["S02"][0]["t"], 125.0, "the delay is far beyond the end of the conflict")

    def test_no_conflict_means_no_change(self):
        d = make_scenario_dict()
        d["aircraft"][1]["home"] = [0, 400, 0]
        sc, pl = make(d)
        pl.routes["S01"] = hop((0, 0))
        extra = {"S02": hop((0, 400))}
        before = copy.deepcopy(extra)
        deconflict.adjust(pl, extra)
        self.assertEqual(extra, before)

    def test_no_slot_before_the_horizon_leaves_the_route_untouched(self):
        d = make_scenario_dict()
        d["horizon_s"] = 130
        sc, pl = make(d)
        pl.routes["S01"] = hop((0, 0))
        extra = {"S02": hop((0, 20))}
        before = copy.deepcopy(extra)
        deconflict.adjust(pl, extra)
        self.assertEqual(extra, before, "a delay past the horizon must not be applied")

    def test_a_conflict_with_a_fixed_route_is_not_hidden(self):
        """Group of effectors shifted together, scout fixed: the scout conflicting with an accepted route stays."""
        sc, pl = make()
        pl.routes["S02"] = hop((0, 20))
        extra = {"S01": hop((0, 0))}             # scout alone may move, so this one is solved...
        deconflict.adjust(pl, extra)
        self.assertEqual(r8(sc, pl._plan(extra)), [])

    def test_never_raises_on_garbage(self):
        sc, pl = make()
        self.assertTrue(deconflict.adjust(pl, {"NOPE": []}))
        self.assertTrue(deconflict.adjust(pl, {}))
        self.assertTrue(deconflict.adjust(pl, {"S01": [{"t": "x"}]}))


class EffectorGroup(unittest.TestCase):
    """C04 needs one light and one heavy effector: they must keep their strike times relative to each other."""

    def setUp(self):
        self.old = deconflict.ENABLED
        deconflict.ENABLED = True
        self.sc, self.pl = make(cls=P.RoutedPlanner)
        self.c = self.sc.contact_by_id()
        self.ac = self.sc.aircraft_by_id()

    def tearDown(self):
        deconflict.ENABLED = self.old

    def bundle(self):
        tasks, sroute = self.pl._add_observation(self.ac["S01"], self.c["C04"], 70.0, 0.0, 0.0)
        obs_end = max(w["t"] + w.get("dwell_s", 0) for w in sroute if w.get("action") == "observe")
        base = max(obs_end + 12.0, 250.0)
        extra = {"S01": sroute}
        for i, e in enumerate(("L01", "H01")):
            route, _ = P._routing.build_effector_route(self.ac[e], self.c["C04"], base + 3.0 * i, self.sc,
                                                       z_layer=(None, 85.0)[i], approach_angle=0.0, engine=self.pl.eng)
            self.assertIsNotNone(route)
            extra[e] = route
        return extra

    def test_group_is_shifted_together_and_the_scout_stays(self):
        extra = self.bundle()
        # an accepted (valid) scout route airborne around the take-off of the light effector, its pad 36 m away
        t0 = extra["L01"][0]["t"]
        self.pl.routes["S02"] = hop((0, 20), depart=t0)
        before = copy.deepcopy(extra)
        pre = r8(self.sc, self.pl._plan(extra))
        deconflict.adjust(self.pl, extra)
        self.assertEqual(extra["S01"], before["S01"], "the scout route must stay fixed")
        d_l = extra["L01"][-1]["t"] - before["L01"][-1]["t"]
        d_h = extra["H01"][-1]["t"] - before["H01"][-1]["t"]
        self.assertAlmostEqual(d_l, d_h, places=6, msg="the group must keep its sync (R10)")
        print(f"    pad conflict before: {len(pre)} R8 ; group delay {d_l:.1f} s ; "
              f"R8 after: {len(r8(self.sc, self.pl._plan(extra)))}")
        if pre:
            self.assertGreater(d_l, 0.0)
            self.assertEqual(r8(self.sc, self.pl._plan(extra)), [])

    def test_a_tight_window_blocks_the_delay(self):
        extra = self.bundle()
        t_strike = extra["L01"][-1]["t"]
        self.sc.contact_by_id()["C04"].window = (100.0, t_strike + 3.0)
        self.pl.routes["S02"] = hop((0, 20), depart=extra["L01"][0]["t"])
        before = copy.deepcopy(extra)
        deconflict.adjust(self.pl, extra)
        self.assertEqual(extra, before, "a delay beyond the strike window (R9) must not be applied")

    def test_the_planner_stays_sound_with_the_scheduler_on(self):
        """_try after adjust: either rejected or the whole plan is valid for the official validator."""
        extra = self.bundle()
        self.pl.routes["S02"] = hop((0, 20), depart=extra["L01"][0]["t"])
        got = self.pl._try(extra)
        if got is not None:
            self.assertTrue(evaluate(self.sc, self.pl._plan(extra)).valid)


if __name__ == "__main__":
    unittest.main(verbosity=2)

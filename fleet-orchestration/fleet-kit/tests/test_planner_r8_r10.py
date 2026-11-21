"""R8 (separation) and R10 (synchronised all-or-nothing engagement) against the incremental check of
handin/planner.py (branch feature/planner-v1). Oracle = the kit's full validator.

Run from fleet-kit/: python3 tests/test_planner_r8_r10.py
"""
import copy
import os
import sys
import time
import types
import unittest

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [KIT, os.path.join(KIT, "handin"), os.path.join(KIT, "tests")]
stub = types.ModuleType("pytest")
stub.fixture = lambda f=None, **k: (f if f else (lambda g: g))
sys.modules.setdefault("pytest", stub)

from conftest import make_scenario_dict  # noqa: E402
from helpers import hop  # noqa: E402
from fleetkit.model import Scenario  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
from fleetkit.validator import validate  # noqa: E402
import planner as P  # noqa: E402

R = P._routing


def planner_for(d, cls=P.RoutedPlanner):
    sc = Scenario.from_dict(d)
    return sc, cls(sc, time.monotonic() + 3600)


def rules_of(sc, pl, extra):
    return {v.rule for v in validate(sc, pl._plan(extra))}


def check_sound(tc, sc, pl, extra, label=""):
    """Incremental accepts => the full validator accepts (soundness). Returns the incremental verdict."""
    got = pl._try(extra)
    if got is not None:
        tc.assertEqual(rules_of(sc, pl, extra), set(), f"UNSOUND {label}: _try accepted an invalid plan")
    return got


class R8(unittest.TestCase):
    def two_scouts(self, gap):
        d = make_scenario_dict()
        d["aircraft"][1]["home"] = [0, gap, 0]
        return planner_for(d)

    def test_new_route_vs_existing_route_too_close(self):
        for gap in (0.5, 20, 39.9):
            sc, pl = self.two_scouts(gap)
            pl.routes["S01"] = hop((0, 0))
            self.assertIsNone(check_sound(self, sc, pl, {"S02": hop((0, gap))}, f"gap={gap}"), f"gap {gap} m accepted")

    def test_two_new_routes_in_the_same_try_too_close(self):
        sc, pl = self.two_scouts(20)
        self.assertIsNone(check_sound(self, sc, pl, {"S01": hop((0, 0)), "S02": hop((0, 20))}))

    def test_boundary_40_m_is_accepted_and_39_9_rejected(self):
        sc, pl = self.two_scouts(40)
        pl.routes["S01"] = hop((0, 0))
        self.assertIsNotNone(check_sound(self, sc, pl, {"S02": hop((0, 40))}), "exactly 40 m must be valid")
        sc, pl = self.two_scouts(39.9)
        pl.routes["S01"] = hop((0, 0))
        self.assertIsNone(pl._try({"S02": hop((0, 39.9))}))

    def test_staggered_launch_is_accepted(self):
        sc, pl = self.two_scouts(20)
        pl.routes["S01"] = hop((0, 0))
        self.assertIsNotNone(check_sound(self, sc, pl, {"S02": hop((0, 20), depart=125.0)}),
                             "a legitimate staggered launch is refused (planner too strict)")

    def test_crossing_flights(self):
        d = make_scenario_dict()
        d["aircraft"][1]["home"] = [0, 200, 0]
        d["aircraft"][1]["v_h_mps"] = 40
        sc, pl = planner_for(d)
        a = [{"t": 0, "x": 0, "y": 0, "z": 0}, {"t": 10, "x": 0, "y": 0, "z": 60}, {"t": 60, "x": 500, "y": 0, "z": 60},
             {"t": 110, "x": 0, "y": 0, "z": 60}, {"t": 120, "x": 0, "y": 0, "z": 0}]
        b = [{"t": 0, "x": 0, "y": 200, "z": 0}, {"t": 10, "x": 0, "y": 200, "z": 60}, {"t": 60, "x": 500, "y": -200, "z": 60},
             {"t": 110, "x": 0, "y": 200, "z": 60}, {"t": 120, "x": 0, "y": 200, "z": 0}]
        pl.routes["S01"] = a
        self.assertIsNone(check_sound(self, sc, pl, {"S02": b}))

    def test_rebuilt_route_is_not_compared_with_its_own_old_version(self):
        sc, pl = self.two_scouts(20)
        pl.routes["S01"] = hop((0, 0))
        # replacing S01 by a different harmless route must not clash with the S01 it replaces
        self.assertIsNotNone(pl._try({"S01": hop((0, 0), depart=5.0)}))


class R10(unittest.TestCase):
    """C04 needs one light + one heavy effector; C01 needs one light. S01 observes, effectors from L01/L02/H01."""

    def setUp(self):
        self.d = make_scenario_dict()
        self.sc, self.pl = planner_for(self.d)
        self.c = self.sc.contact_by_id()
        self.ac = self.sc.aircraft_by_id()

    def scout_route(self, cid):
        built = self.pl._add_observation(self.ac["S01"], self.c[cid], 70.0, 0.0, 0.0)
        self.assertIsNotNone(built, "could not build the observation route")
        tasks, route = built
        obs_end = max(w["t"] + w.get("dwell_s", 0) for w in route if w.get("action") == "observe" and w.get("target") == cid)
        return tasks, route, obs_end

    def eff(self, eid, cid, arrive, z=None):
        route, _ = R.build_effector_route(self.ac[eid], self.c[cid], arrive, self.sc, z_layer=z, approach_angle=0.0,
                                          engine=self.pl.eng)
        self.assertIsNotNone(route, f"could not build {eid} -> {cid} at {arrive}")
        return route

    def c04(self, gap, effs=("L01", "H01")):
        _, sroute, obs_end = self.scout_route("C04")
        base = max(obs_end + 12.0, 250.0)
        extra = {"S01": sroute}
        for i, e in enumerate(effs):
            extra[e] = self.eff(e, "C04", base + (gap if i else 0.0), z=(None, 85.0, 130.0)[i % 3])
        return extra

    def test_desync_over_20s_is_rejected_and_within_is_judged_like_the_oracle(self):
        for gap in (0, 5, 19.9, 20.0, 20.1, 25, 60):
            extra = self.c04(gap)
            got = check_sound(self, self.sc, self.pl, extra, f"gap={gap}")
            oracle = rules_of(self.sc, self.pl, extra)
            if gap > 20.0:
                self.assertIn("R10", oracle, f"scenario does not trigger R10 for gap={gap}: {oracle}")
                self.assertIsNone(got, f"R10 desync of {gap}s accepted")
            print(f"    R10 sync gap={gap:5}: _try={'reject' if got is None else 'accept'} oracle={sorted(oracle) or 'valid'}")

    def test_missing_effector_is_rejected(self):
        extra = self.c04(0, effs=("L01",))
        self.assertIn("R10", rules_of(self.sc, self.pl, extra))
        self.assertIsNone(self.pl._try(extra))

    def test_too_many_effectors_is_rejected(self):
        _, sroute, obs_end = self.scout_route("C01")
        base = max(obs_end + 12.0, 250.0)
        extra = {"S01": sroute, "L01": self.eff("L01", "C01", base), "L02": self.eff("L02", "C01", base + 3, z=85.0)}
        self.assertIn("R10", rules_of(self.sc, self.pl, extra))
        self.assertIsNone(self.pl._try(extra))

    def test_engagement_too_far_from_the_contact_is_rejected(self):
        _, sroute, obs_end = self.scout_route("C01")
        r = self.eff("L01", "C01", max(obs_end + 12.0, 250.0))
        r[-1]["x"] += 30.0           # 30 m off the contact (limit 25 m)
        extra = {"S01": sroute, "L01": r}
        self.assertIsNone(check_sound(self, self.sc, self.pl, extra))

    @unittest.expectedFailure  # known latent hole, to report to Louis; becomes 'unexpected success' once fixed
    def test_second_engagement_added_in_a_later_try_for_an_already_engaged_contact(self):
        """The planner commits a contact once, but _try's docstring says R8 is the only rule coupling routes."""
        _, sroute, obs_end = self.scout_route("C01")
        base = max(obs_end + 12.0, 250.0)
        first = {"S01": sroute, "L01": self.eff("L01", "C01", base)}
        self.assertIsNotNone(self.pl._try(first))
        self.pl.routes.update(first)                       # contact C01 is now engaged by L01 (needs exactly 1 light)
        # the scout route is part of `extra`, exactly as in _place_effectors (without it R4 would reject for another reason)
        second = {"S01": sroute, "L02": self.eff("L02", "C01", base + 2, z=40.0)}
        got = self.pl._try(second)
        full = rules_of(self.sc, self.pl, second)
        self.assertEqual(full, {"R10"}, "the scenario must trigger R10 alone, otherwise the test proves nothing")
        print(f"    R10 cross-try (L02 added to C01 already engaged by L01): _try={'reject' if got is None else 'ACCEPT'}, "
              f"full validator={sorted(full) or 'valid'}")
        self.assertIsNone(got, "LATENT HOLE: _try accepted a 2nd engagement of an already engaged contact "
                               f"(full validator says {sorted(full)})")


class StaggerLimit(unittest.TestCase):
    """_place_effectors staggers effectors by a hard-coded 5 s: contacts needing > 5 effectors can never sync."""

    def test_stagger_vs_sync_window(self):
        self.assertEqual(P.RoutedPlanner._place_effectors.__code__.co_consts.count(5.0) >= 1, True)
        from fleetkit.generator import generate
        worst = 0
        for lvl in ("L1", "L2", "L3", "L4"):
            for seed in range(50):
                data = generate(lvl, seed)
                for c in data["contacts"]:
                    worst = max(worst, sum(c.get("engage_needs", {}).values()))
        window = Scenario.from_dict(generate("L1", 0)).rules.sync_window_s
        span = 5.0 * (worst - 1)
        print(f"    max effectors needed by one contact (L1-L4 x 50 seeds): {worst}; stagger span {span:g}s; window {window:g}s")
        self.assertLessEqual(span, window, "a contact exists that the 5 s stagger cannot synchronise")


if __name__ == "__main__":
    unittest.main(verbosity=2)

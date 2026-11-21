"""The two latent flaws of handin/planner.py, forced to fire.

1. R10 across tries. The incremental `_try` validates the touched routes alone, so a SECOND pass on a contact
   already served (what a repair loop would do) is accepted and the plan becomes invalid (R10). Fixed by the R10
   guard in handin/deconflict.py (called by `_try` through `deconflict.adjust`, ON by default).
2. No greedy_plan fallback. When every build is invalid, solve() returns the empty plan: score 0, below the kit's
   own greedy plan. Not fixed: the fix belongs in solve() of planner.py (Louis's code); the test that needs it is
   marked expectedFailure and turns into an 'unexpected success' once a fallback exists.

Run from fleet-kit/: python3 tests/test_latent_guards.py  (or pytest). The oracle is the official kit (fleetkit).
"""
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
from fleetkit.baseline import greedy_plan  # noqa: E402
from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import Scenario as OfficialScenario  # noqa: E402
from fleetkit.scorer import evaluate as official  # noqa: E402
from fk.model import HOSTILE, Scenario  # noqa: E402
import deconflict  # noqa: E402
import planner as P  # noqa: E402

CASES = [("hand", make_scenario_dict), ("L2-0", lambda: generate("L2", 0)), ("L3-0", lambda: generate("L3", 0))]


def second_pass(data, cls):
    """Serves the hostiles richest first; on the first one served, serves it AGAIN. Returns (contact, accepted, plan)."""
    sc = Scenario.from_dict(data)
    pl = cls(sc, time.monotonic() + 600)
    for c in sorted((c for c in sc.contacts if c.cls == HOSTILE), key=lambda c: -c.points):
        if pl.serve_hostile(c):
            first = pl._plan({})
            again = pl.serve_hostile(c)
            return c.id, again, first, pl._plan({})
    return None, False, None, None


class R10AcrossTries(unittest.TestCase):
    def setUp(self):
        self.old = deconflict.R10_GUARD

    def tearDown(self):
        deconflict.R10_GUARD = self.old

    def test_without_the_guard_a_second_pass_breaks_the_plan(self):
        deconflict.R10_GUARD = False
        broken = 0
        for name, make in CASES:
            data = make()
            for cls in (P.RoutedPlanner, P.FastPlanner):
                cid, again, _first, plan = second_pass(data, cls)
                if not again:
                    continue
                res = official(OfficialScenario.from_dict(data), plan)
                self.assertFalse(res.valid)
                self.assertIn("R10", {v.rule for v in res.violations})
                broken += 1
        print(f"    without the guard: the second pass is accepted and the plan breaks (R10) in {broken} of "
              f"{2 * len(CASES)} runs")
        self.assertGreater(broken, 0, "no scenario reproduces the flaw: the test proves nothing")

    def test_with_the_guard_the_second_pass_is_rejected_and_the_plan_stays_valid(self):
        deconflict.R10_GUARD = True
        for name, make in CASES:
            data = make()
            for cls in (P.RoutedPlanner, P.FastPlanner):
                cid, again, first, plan = second_pass(data, cls)
                if cid is None:
                    continue
                self.assertFalse(again, f"{name} {cls.__name__}: second pass on {cid} accepted")
                self.assertEqual(plan, first, "a rejected pass must leave the plan unchanged")
                self.assertTrue(official(OfficialScenario.from_dict(data), plan).valid)

    def test_the_guard_does_not_change_a_normal_build(self):
        data = generate("L2", 0)
        sc = Scenario.from_dict(data)
        out = []
        for guard in (False, True):
            deconflict.R10_GUARD = guard
            plan, score = P.build(sc, P._key(sc, 0.0, {}), time.monotonic() + 600, P.N_SCOUTS, P.FastPlanner)
            out.append((plan, score))
        self.assertEqual(out[0], out[1], "the guard changed a build that serves each contact once")


class GreedyFallback(unittest.TestCase):
    """Every build broken (a regression that makes each construction crash): what does solve() write?

    (A `_try` that accepts anything is not enough: on L2 some builds stay valid and solve() still scores 293.)
    """

    def run_broken(self, data):
        sc = Scenario.from_dict(data)
        orig, workers = P.build, P.MAX_WORKERS

        def broken_build(*args, **kwargs):
            raise RuntimeError("simulated regression in the builder")

        P.build = broken_build
        P.MAX_WORKERS = 1
        try:
            plan = P.solve(sc, data, budget_s=3.0)
        finally:
            P.build, P.MAX_WORKERS = orig, workers
        got = official(OfficialScenario.from_dict(data), plan)
        base = official(OfficialScenario.from_dict(data), greedy_plan(OfficialScenario.from_dict(data)))
        return got, base

    def test_without_a_fallback_every_broken_build_scores_zero(self):
        data = generate("L2", 0)
        got, base = self.run_broken(data)
        print(f"    all builds broken: solve() writes a valid plan scoring {got.score:.1f}; kit greedy plan "
              f"{base.score:.1f}")
        self.assertTrue(got.valid)
        self.assertEqual(got.score, 0.0)
        self.assertGreater(base.score, 0.0)

    @unittest.expectedFailure  # needs a greedy_plan fallback in solve() (planner.py, Louis's code): not applied
    def test_with_a_fallback_the_score_never_drops_below_the_kit_greedy(self):
        data = generate("L2", 0)
        got, base = self.run_broken(data)
        self.assertGreaterEqual(got.score, base.score)


if __name__ == "__main__":
    unittest.main(verbosity=2)

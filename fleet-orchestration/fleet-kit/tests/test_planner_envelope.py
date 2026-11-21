"""Anti-zero envelope of handin/planner.py (Louis): what is written when the incremental checker is wrong?"""
import os, re, sys, types, unittest
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [KIT, KIT + "/handin"]
from fleetkit.baseline import greedy_plan
from fleetkit.generator import generate
from fleetkit.model import Scenario, parse_plan
from fleetkit.scorer import evaluate
import planner as P

class Envelope(unittest.TestCase):
    @unittest.expectedFailure  # known gap: no greedy_plan last resort; becomes 'unexpected success' once added
    def test_greedy_plan_of_the_kit_is_never_called(self):
        with open(KIT + "/handin/planner.py") as f:
            src = f.read()
        calls = re.findall(r"greedy_plan\(", src)
        print("    calls to the kit's greedy_plan() in handin/planner.py:", len(calls))
        self.assertTrue(calls, "no fallback on the kit's greedy plan anywhere")

    def test_buggy_incremental_check_degrades_to_greedy_not_to_zero(self):
        data = generate("L2", 0)
        sc = Scenario.from_dict(data)
        base = evaluate(sc, greedy_plan(Scenario.from_dict(data))).score
        def accept_all(self, extra):      # simulates a bug that lets any route through
            sub = {"seed": self.sc.seed, "routes": [{"aircraft": a, "waypoints": w} for a, w in extra.items()]}
            return parse_plan(sub)[0]
        orig, P.MAX_WORKERS = P.FastPlanner._prefilter_routes, 1
        P.FastPlanner._prefilter_routes = accept_all
        try:
            plan = P.solve(Scenario.from_dict(data), data, budget_s=10.0)
        finally:
            P.FastPlanner._prefilter_routes = orig
        res = evaluate(Scenario.from_dict(data), plan)
        print(f"    buggy checker: plan valid={res.valid} score={res.score:.1f} routes={len(plan['routes'])} | kit greedy baseline={base:.1f}")
        self.assertTrue(res.valid)
        self.assertGreaterEqual(res.score, base, "fell to an empty plan although the kit greedy gives %.1f" % base)

if __name__ == "__main__":
    unittest.main(verbosity=2)

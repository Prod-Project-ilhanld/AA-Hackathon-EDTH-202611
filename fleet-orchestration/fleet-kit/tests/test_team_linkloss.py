"""Tests of the link-loss mini-simulator (linkloss/). Run from fleet-kit/: python3 -m unittest tests.test_linkloss."""
import copy
import os
import sys
import unittest

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import Scenario  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
from linkloss.harden import LEVELS, harden  # noqa: E402
from linkloss.sim import Comms, Disturbance, World, ceiling, post_cut_contacts, simulate  # noqa: E402
from linkloss.sweep import make_plan  # noqa: E402


class LinkLossSim(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = generate("L2", 1)
        cls.scn = Scenario.from_dict(cls.data)
        cls.plan = make_plan(cls.data, "3", "1")
        assert evaluate(cls.scn, cls.plan).valid
        cls.cut = 0.25 * cls.scn.horizon_s

    def test_no_drift_nothing_is_lost(self):
        dist = Disturbance(t_cut=self.cut, p_affected=0.0)
        r = simulate(self.scn, self.plan, dist, Comms(), "continue", 0)
        self.assertGreater(r.ceiling, 0.0)
        self.assertAlmostEqual(r.served, r.ceiling)
        self.assertEqual(r.violations, 0)
        self.assertEqual(sum(r.fails.values()), 0)

    def test_return_serves_nothing_after_the_cut_and_never_violates(self):
        dist = Disturbance(t_cut=self.cut, p_affected=1.0, max_slow=0.5)
        r = simulate(self.scn, self.plan, dist, Comms(), "return", 3)
        self.assertEqual(r.served, 0.0)
        self.assertEqual(r.violations, 0)

    def test_detector_sees_heavy_drift(self):
        """Negative control: when every aircraft flies 90 % slower, blind execution must lose points."""
        dist = Disturbance(t_cut=0.0, p_affected=1.0, max_slow=0.9)
        shares = [simulate(self.scn, self.plan, dist, Comms(), "continue", s).share for s in range(10)]
        self.assertLess(sum(shares) / len(shares), 0.95)

    def test_same_seed_same_result(self):
        dist = Disturbance(t_cut=self.cut)
        a = simulate(self.scn, self.plan, dist, Comms(), "adjust", 5)
        b = simulate(self.scn, self.plan, dist, Comms(), "adjust", 5)
        self.assertEqual((a.served, a.msgs, a.violations), (b.served, b.msgs, b.violations))

    def test_adjust_with_no_range_sends_messages_nobody_hears(self):
        """Range 0: messages cost points and change nothing, so adjust cannot beat continue."""
        dist = Disturbance(t_cut=self.cut, p_affected=1.0, max_slow=0.3)
        for s in range(5):
            c = simulate(self.scn, self.plan, dist, Comms(), "continue", s)
            a = simulate(self.scn, self.plan, dist, Comms(range_m=0.0), "adjust", s)
            self.assertAlmostEqual(a.served, c.served)
            self.assertLessEqual(a.score, c.score + 1e-9)

    def test_ceiling_counts_only_post_cut_contacts(self):
        world = World(self.scn, self.plan, Disturbance(t_cut=self.scn.horizon_s * 10))
        self.assertEqual(post_cut_contacts(world), [])
        self.assertEqual(ceiling(world), 0.0)


class Hardening(unittest.TestCase):
    def test_level_zero_is_a_copy_and_input_is_never_mutated(self):
        data = generate("L1", 0)
        frozen = copy.deepcopy(data)
        self.assertEqual(harden(data, 0), data)
        for level in LEVELS:
            harden(data, level)
        self.assertEqual(data, frozen)

    def test_hardened_plan_is_valid_on_the_real_scenario(self):
        data = generate("L2", 2)
        plan = make_plan(harden(data, 2), "3", "1")
        self.assertTrue(evaluate(Scenario.from_dict(data), plan).valid)

    def test_hardened_rules_are_stricter(self):
        data = generate("L1", 0)
        h = harden(data, 3)
        self.assertGreater(h["rules"]["d_sep_m"], data["rules"]["d_sep_m"])
        self.assertLess(h["rules"]["sync_window_s"], data["rules"]["sync_window_s"])


class Isolation(unittest.TestCase):
    def test_hand_in_never_imports_linkloss(self):
        for name in os.listdir(os.path.join(KIT, "handin")):
            if name.endswith(".py") and name not in ("check_policy.py", "policy.py"):  # the link-loss hand-in itself
                with open(os.path.join(KIT, "handin", name)) as f:
                    self.assertNotIn("linkloss", f.read(), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Robustness of handin/planner.py: it must always write a VALID plan, whatever the scenario.

A crash, a timeout or an invalid plan scores 0, so each case runs the planner the way the evaluation
does (subprocess, minimal environment) with a short internal budget, then checks the plan with the
kit's own scorer. Run: `python3 -m pytest tests/test_planner_robustness.py` or
`python3 tests/test_planner_robustness.py` from fleet-kit/.
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import Scenario  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402

PLANNER = os.path.join(KIT, "handin", "planner.py")


def run_planner(data, planner=PLANNER, workers="1", budget="2", timeout=60):
    """Runs the planner in a temp dir; returns (returncode, plan dict or None, stderr)."""
    with tempfile.TemporaryDirectory() as tmp:
        scen, out = os.path.join(tmp, "scenario.json"), os.path.join(tmp, "plan.json")
        with open(scen, "w") as f:
            json.dump(data, f)
        env = {"PATH": os.environ.get("PATH", ""), "PYTHONPATH": KIT, "PYTHONDONTWRITEBYTECODE": "1",
               "HOME": tmp, "PLANNER_BUDGET_S": budget, "PLANNER_WORKERS": workers}
        proc = subprocess.run([sys.executable, planner, scen, out], env=env, capture_output=True,
                              text=True, timeout=timeout)
        plan = None
        if os.path.exists(out):
            with open(out) as f:
                plan = json.load(f)
        return proc.returncode, plan, proc.stderr[-300:]


def check_valid(testcase, data, **kw):
    code, plan, err = run_planner(data, **kw)
    testcase.assertEqual(code, 0, err)
    testcase.assertIsNotNone(plan, "no plan written")
    res = evaluate(Scenario.from_dict(data), plan)
    testcase.assertTrue(res.valid, [str(v) for v in res.violations[:3]])
    return res


class PlannerRobustness(unittest.TestCase):
    def setUp(self):
        self.data = generate("L1", 0)

    def test_normal_scenario_is_valid_and_scores(self):
        res = check_valid(self, self.data)
        self.assertGreater(res.score, 0.0)

    def test_two_workers_same_validity(self):
        check_valid(self, self.data, workers="2")

    def test_no_contacts(self):
        d = copy.deepcopy(self.data)
        d["contacts"] = []
        check_valid(self, d)

    def test_no_scouts(self):
        d = copy.deepcopy(self.data)
        d["aircraft"] = [a for a in d["aircraft"] if a["type"] != "scout"]
        res = check_valid(self, d)
        self.assertEqual(res.points, 0.0)

    def test_no_effectors(self):
        d = copy.deepcopy(self.data)
        d["aircraft"] = [a for a in d["aircraft"] if a["type"] == "scout"]
        check_valid(self, d)

    def test_no_aircraft(self):
        d = copy.deepcopy(self.data)
        d["aircraft"] = []
        check_valid(self, d)

    def test_hostile_without_window_does_not_crash(self):
        d = copy.deepcopy(self.data)
        for c in d["contacts"]:
            if c["class"] == "hostile":
                c["window_s"] = None
        check_valid(self, d)

    def test_works_without_the_routing_module(self):
        """The team's routing module is optional: without it the planner falls back to the kit's routes."""
        with tempfile.TemporaryDirectory() as tmp:
            dst = os.path.join(tmp, "handin")
            shutil.copytree(os.path.dirname(PLANNER), dst,
                            ignore=shutil.ignore_patterns("routing.py", "__pycache__", "*.pyc"))
            self.assertFalse(os.path.exists(os.path.join(dst, "routing.py")))
            code, plan, err = run_planner(self.data, planner=os.path.join(dst, "planner.py"))
            self.assertEqual(code, 0, err)
            self.assertTrue(evaluate(Scenario.from_dict(self.data), plan).valid)

    def test_broken_routing_module_falls_back_to_kit_router(self):
        """The team's routing module is the default router: if it fails, the kit's router must still score."""
        with tempfile.TemporaryDirectory() as tmp:
            dst = os.path.join(tmp, "handin")
            shutil.copytree(os.path.dirname(PLANNER), dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            with open(os.path.join(dst, "routing.py"), "w") as f:
                f.write("def get_engine(scenario):\n    raise RuntimeError('routing is broken')\n")
            code, plan, err = run_planner(self.data, planner=os.path.join(dst, "planner.py"), budget="4")
            self.assertEqual(code, 0, err)
            res = evaluate(Scenario.from_dict(self.data), plan)
            self.assertTrue(res.valid, [str(v) for v in res.violations[:3]])
            self.assertGreater(res.score, 0.0, "no fallback to the kit router")

    def _planner_with_shim(self, tmp, shim_source):
        """Copies handin/ to tmp with a multiprocessing.py shim that shadows the stdlib module."""
        dst = os.path.join(tmp, "handin")
        shutil.copytree(os.path.dirname(PLANNER), dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        with open(os.path.join(dst, "multiprocessing.py"), "w") as f:
            f.write(shim_source)
        return os.path.join(dst, "planner.py")

    def test_pool_creation_failure_falls_back_to_serial(self):
        """If the process pool cannot be created, the planner searches serially and still scores."""
        shim = "def get_context(method):\n    raise RuntimeError('no pool here')\n"
        with tempfile.TemporaryDirectory() as tmp:
            planner = self._planner_with_shim(tmp, shim)
            code, plan, err = run_planner(self.data, planner=planner, workers="2", budget="3")
            self.assertEqual(code, 0, err)
            res = evaluate(Scenario.from_dict(self.data), plan)
            self.assertTrue(res.valid, [str(v) for v in res.violations[:3]])
            self.assertGreater(res.score, 0.0, "serial fallback produced nothing")

    def test_hung_workers_still_write_a_valid_plan_in_time(self):
        """Workers that never answer: the planner stops waiting after deadline+8 s and writes a valid plan."""
        shim = (
            "import time\n"
            "class _Job:\n"
            "    def get(self, timeout=None):\n"
            "        time.sleep(timeout or 0)\n"
            "        raise TimeoutError()\n"
            "class _Pool:\n"
            "    def apply_async(self, *a, **k):\n"
            "        return _Job()\n"
            "    def terminate(self):\n"
            "        pass\n"
            "class _Ctx:\n"
            "    def Pool(self, n):\n"
            "        return _Pool()\n"
            "def get_context(method):\n"
            "    return _Ctx()\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            planner = self._planner_with_shim(tmp, shim)
            start = time.monotonic()
            code, plan, err = run_planner(self.data, planner=planner, workers="2", budget="2")
            elapsed = time.monotonic() - start
            self.assertEqual(code, 0, err)
            self.assertTrue(evaluate(Scenario.from_dict(self.data), plan).valid)
            self.assertLess(elapsed, 20.0, "waited too long on hung workers")

    def test_detector_flags_an_invalid_plan(self):
        """Negative control: a plan with the wrong seed must be reported invalid by the checker we use."""
        _, plan, _ = run_planner(self.data)
        bad = dict(plan, seed=self.data["seed"] + 1)
        self.assertFalse(evaluate(Scenario.from_dict(self.data), bad).valid)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""tools/tune.py self-check, the env-var knobs of handin/params.py (defaults unchanged) and the ANNEAL flag."""
import json
import os
import random
import subprocess
import sys
import tempfile

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KIT, "tools"))
sys.path.insert(0, os.path.join(KIT, "handin"))

import tune  # noqa: E402
from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import save_json  # noqa: E402


def test_compare_paired_stats():
    base = {("L4", 0): {"score": 100.0, "valid": True, "cpu": 10.0}, ("L4", 1): {"score": 300.0, "valid": True, "cpu": 10.0}}
    var = {("L4", 0): {"score": 104.0, "valid": True, "cpu": 11.0}, ("L4", 1): {"score": 296.0, "valid": False, "cpu": 11.0},
           ("L4", 2): {"score": 999.0, "valid": True, "cpu": 1.0}}  # unpaired key: ignored
    s = tune.compare(base, var)
    assert s["n"] == 2 and s["worse"] == 1 and s["better"] == 1 and s["invalid"] == 1
    assert abs(s["delta_pct"]) < 1e-9          # +4 and -4 on a total of 400
    assert abs(s["se_pct"] - 2.0) < 1e-9       # s.e. of (+4, -4) is 4, per seed 200 on average
    assert abs(s["cpu_ratio"] - 1.1) < 1e-9


def test_planner_env_setting_and_clean_inheritance(monkeypatch):
    monkeypatch.setenv("PLANNER_SIGMA_ODD", "9")
    env = tune.planner_env("ALPHAS=0,1 ANNEAL=1", 6, 2)
    assert env["PLANNER_ALPHAS"] == "0,1" and env["PLANNER_ANNEAL"] == "1"
    assert "PLANNER_SIGMA_ODD" not in env
    assert env["FLEET_ITERS"] == "6" and env["PLANNER_WORKERS"] == "2" and float(env["PLANNER_BUDGET_S"]) > 1000


def _params(env):
    code = ("import json, params; print(json.dumps([params.N_SCOUTS, params.BOTH_ROUTERS, params.ALPHAS, "
            "params.SIGMA_EVEN, params.SIGMA_ODD, params.ALPHA_STEP, params.ANNEAL]))")
    clean = {k: v for k, v in os.environ.items() if not k.startswith(("PLANNER_", "FLEET_"))}
    out = subprocess.run([sys.executable, "-c", code], env=dict(clean, **env), cwd=os.path.join(KIT, "handin"),
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_params_defaults_are_the_old_literals():
    assert _params({}) == [15, 20, [0.0, 1.0, 0.5, 1.5], 0.12, 0.3, 0.2, False]
    assert _params({"PLANNER_ALPHAS": "0.5", "PLANNER_N_SCOUTS": "10", "PLANNER_ANNEAL": "1"})[:3] == [10, 20, [0.5]]


def test_anneal_accept():
    import params
    import planner
    rng = random.Random(0)
    assert planner._anneal_accept(100.0, 100.0, 5, 0.0, 1.0, rng)            # not worse: always
    old = (params.FLEET_ITERS, params.ANNEAL_T0)
    try:
        params.FLEET_ITERS, params.ANNEAL_T0 = 10, 0.01
        assert not planner._anneal_accept(100.0, 99.0, 10, 0.0, 1.0, rng)    # cooled to 0: never worse
        hits = sum(planner._anneal_accept(100.0, 99.0, 0, 0.0, 1.0, rng) for _ in range(2000))
        assert 600 < hits < 870                                               # exp(-1/1) = 0.37 at the start
    finally:
        params.FLEET_ITERS, params.ANNEAL_T0 = old


def test_flag_off_plan_equals_explicit_old_values():
    """Defaults and the old literal values give the same bytes; ANNEAL=1 stays valid and deterministic."""
    work = tempfile.mkdtemp()
    scen = os.path.join(work, "L2-0.json")
    save_json(generate("L2", 0), scen)

    def plan(setting):
        out = os.path.join(work, "plan.json")
        subprocess.run([sys.executable, os.path.join(KIT, "handin", "planner.py"), scen, out],
                       env=tune.planner_env(setting, 2, 2), check=True, timeout=300)
        with open(out, "rb") as f:
            return f.read()

    explicit = "N_SCOUTS=15 BOTH_ROUTERS=20 ALPHAS=0.0,1.0,0.5,1.5 SIGMA_EVEN=0.12 SIGMA_ODD=0.3 ALPHA_STEP=0.2 ANNEAL=0"
    assert plan("") == plan(explicit)
    on = plan("ANNEAL=1 ANNEAL_T0=0.05")
    assert on == plan("ANNEAL=1 ANNEAL_T0=0.05")
    assert tune.run(os.path.join(KIT, "handin", "planner.py"), scen, "ANNEAL=1", 2, 2, sys.executable)["valid"]

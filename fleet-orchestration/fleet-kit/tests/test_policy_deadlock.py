"""Link-loss policy (handin/policy.py): holds that never end (task 9).

- an aborted aircraft gets out of the way of an on-plan peer that already waits for it;
- an effector without its observation waits for a late scout instead of aborting, and then engages only
  confirm_margin after it heard of the observation (R4);
- L2-21 of check_policy (events seed = seed + 1, 1000x200), which ended in a permanent hold;
- R8 cases of the sizing grid (events seed 1) found on the way: L4-24 and L4-6.
"""
from pathlib import Path

from test_policy_r8 import CROSSING, TAU_AT_800, ZONE_AHEAD, obs, scenario_and_plan
from fleetkit.baseline import greedy_plan
from fleetkit.generator import generate
from fleetkit.linkloss import simulate
from fleetkit.linkloss.events import make_events
from fleetkit.linkloss.policies import load_policy
from fleetkit.linkloss.score import oracle_points
from fleetkit.model import Scenario

POLICY_PATH = str(Path(__file__).resolve().parents[1] / "handin" / "policy.py")
Policy = load_policy(POLICY_PATH)


def test_an_aborted_aircraft_backs_off_for_a_peer_that_waits_for_it():
    sc, plan = scenario_and_plan(CROSSING)
    p = Policy(sc, plan, "L01")
    waiting = {"from": "L02", "sent_t": 29.0, "payload": [1, 170]}   # L02 holds at tau 17, 90 m short of our hover
    action, _ = p.step(obs(30.0, TAU_AT_800, sensed=[ZONE_AHEAD], inbox=[waiting]))
    assert action == {"kind": "return"}


def _r4_case():
    from test_policy import _make_simple_scenario   # L01 engages C01 at t = 100; S01 observes it until t = 55
    sc, plan = _make_simple_scenario()
    return Policy(sc, plan, "L01")


def _obs(p, t, tau, inbox=()):
    return {"t": t, "t_loss": 25.0, "pos": p.clock.position(tau), "vel": (0.0, 0.0, 0.0), "tau": tau, "next_wp": 1,
            "mode": "route", "energy_left_wh": 80.0, "own_observed": [], "sensed": [], "inbox": list(inbox),
            "last_heard": {}}


def test_an_effector_waits_for_a_late_observation_then_keeps_the_confirm_margin():
    p = _r4_case()
    assert p.step(_obs(p, 97.0, 97.0))[0] == {"kind": "hold"} and p._last_mode == "route"   # waits, not aborted
    ob = {"from": "S01", "sent_t": 104.0, "payload": [0, 0, 0, 0, [0]]}                     # C01 observed
    assert p.step(_obs(p, 105.0, 97.0, [ob]))[0] == {"kind": "hold"}                        # 105 + 3 < 105 + 10
    assert p.step(_obs(p, 111.0, 97.0))[0] == {"kind": "hold"}
    assert p.step(_obs(p, 112.0, 97.0))[0] == {"kind": "continue"}                          # engages at 115


def test_an_effector_gives_up_waiting_after_the_longest_wait():
    p = _r4_case()
    p.step(_obs(p, 97.0, 97.0))
    p.step(_obs(p, 140.0, 97.0))
    assert p._last_mode == "return"


def _check_policy_case(level, seed):
    sc = Scenario.from_dict(generate(level, seed))
    plan = greedy_plan(sc)
    ev = make_events(sc, plan, seed + 1)
    res = simulate(sc, plan, ev, Policy, setting=(1000.0, 200.0), run_seed=0)
    return res, res.points / oracle_points(sc, plan, ev)


def test_l2_21_no_longer_ends_in_a_mutual_hold():
    res, ret = _check_policy_case("L2", 21)   # was 0.148: S01 waits for L03, which waits for H02, which waits for S01
    assert res.ok and ret >= 0.9


import pytest  # noqa: E402


@pytest.mark.parametrize("level,seed,setting,run_seed", [
    ("L4", 24, (2000.0, 50.0), 1),   # L20 backed off for L18, resumed at once, then held; the hold was lost (33 m)
    ("L4", 24, (250.0, 50.0), 2),    # L18 kept flying on a "resumed" belief while L20 had stopped again (33 m)
    ("L4", 6, (250.0, 50.0), 2),     # on-plan S04 skipped L32, which had resumed 16 s late and did not yield (32 m)
])
def test_sizing_r8_cases_found_while_breaking_holds(level, seed, setting, run_seed):
    sc = Scenario.from_dict(generate(level, seed))
    plan = greedy_plan(sc)
    assert simulate(sc, plan, make_events(sc, plan, 1), Policy, setting=setting, run_seed=run_seed).ok

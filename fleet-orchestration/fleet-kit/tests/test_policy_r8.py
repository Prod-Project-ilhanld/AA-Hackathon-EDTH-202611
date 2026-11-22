"""Link-loss policy (handin/policy.py): R8 behaviour of aborted aircraft, message size and step time."""
import json
import time
from pathlib import Path

import pytest

from conftest import make_scenario_dict
from fleetkit.baseline import greedy_plan
from fleetkit.generator import generate
from fleetkit.linkloss import RouteClock, simulate
from fleetkit.linkloss.events import make_events
from fleetkit.linkloss.policies import load_policy
from fleetkit.model import Scenario

Policy = load_policy(str(Path(__file__).resolve().parents[1] / "handin" / "policy.py"))


def wp(t, x, y, z, **kw):
    return dict(t=t, x=x, y=y, z=z, **kw)


def scenario_and_plan(l02_route):
    """L01 flies along +x at 130 m to engage C01 at t = 60; L02 flies `l02_route`."""
    plan = {"seed": 1, "routes": [
        {"aircraft": "L01", "waypoints": [wp(0, 30, 0, 0), wp(10, 30, 0, 130), wp(50, 1230, 0, 130),
                                          wp(60, 1500, 0, 10, action="engage", target="C01")]},
        {"aircraft": "L02", "waypoints": l02_route},
    ]}
    return Scenario.from_dict(make_scenario_dict()), plan


CROSSING = [wp(0, 800, -600, 130), wp(40, 800, 600, 130, action="engage", target="C04")]   # crosses x = 800 at t = 20
PARALLEL = [wp(0, 30, 200, 0), wp(10, 30, 200, 130), wp(50, 1230, 200, 130),
            wp(60, 1500, 200, 10, action="engage", target="C01")]                            # same target, 200 m aside
TAU_AT_800 = 10 + 770 / 30.0                                                                 # L01's planned time at x = 800


def obs(t, tau, inbox=(), sensed=(), mode="route"):
    return {"t": t, "t_loss": 5.0, "tau": tau, "mode": mode, "pos": (0, 0, 0), "vel": (0, 0, 0),
            "energy_left_wh": 50.0, "own_observed": [], "sensed": list(sensed), "inbox": list(inbox), "last_heard": {}}


RECLASSIFY_C01 = {"kind": "reclassify", "contact": "C01"}


def test_an_aborted_aircraft_hovers_and_flags_its_abort():
    sc, plan = scenario_and_plan(CROSSING)
    p = Policy(sc, plan, "L01")
    action, msg = p.step(obs(30.0, TAU_AT_800, sensed=[RECLASSIFY_C01]))   # L02 crossed at t = 20: nobody in the way
    assert action == {"kind": "hold"}
    assert msg[0] == 4   # status 4: hold while aborted (list message since #23)


def test_an_aborted_hover_beats_three_times_then_every_12_s_when_nobody_closes_in():
    sc, plan = scenario_and_plan(CROSSING)
    p = Policy(sc, plan, "L01")
    beats = []
    for t in range(30, 46):   # L02 crossed at t = 20 and flies away: nobody closes in
        action, msg = p.step(obs(float(t), TAU_AT_800, sensed=[RECLASSIFY_C01] if t == 30 else []))
        assert action == {"kind": "hold"}
        if msg is not None and msg[0] == 4:
            beats.append(t)
    assert beats == [30, 31, 32, 44]


def test_an_aborted_aircraft_in_an_on_plan_peers_way_backs_off_within_one_step():
    sc, plan = scenario_and_plan(CROSSING)
    p = Policy(sc, plan, "L01")
    action, msg = p.step(obs(17.0, TAU_AT_800, sensed=[RECLASSIFY_C01]))   # L02 reaches x = 800 at t = 20
    assert action == {"kind": "return"}
    assert msg[0] == 2   # status 2: return


def test_a_co_effector_aborts_when_it_hears_a_flagged_hold():
    sc, plan = scenario_and_plan(PARALLEL)
    p = Policy(sc, plan, "L02")
    heard = {"from": "L01", "sent_t": 29.0, "payload": {"hd": 1, "u": 29.0, "ab": 1}}
    action, _ = p.step(obs(30.0, 30.0, inbox=[heard]))
    assert action["kind"] != "continue"   # before: it kept flying and waited behind the hovering partner


def test_an_aborted_hover_never_expires_into_an_on_plan_belief():
    sc, plan = scenario_and_plan(PARALLEL)
    p = Policy(sc, plan, "L02")
    heard = {"from": "L01", "sent_t": 29.0, "payload": {"hd": 1, "u": 29.0, "ab": 1}}
    p.step(obs(30.0, 30.0, inbox=[heard]))
    assert p._peer_pos_at("L01", 90.0, 90.0) == RouteClock(p.routes["L01"]).position(29.0)   # still hovering at 29


@pytest.mark.parametrize("offset, kind", [(45.8, "continue"), (42.0, "hold")])
def test_an_on_plan_aircraft_passes_an_aborted_hover_clear_of_d_sep(offset, kind):
    # L02 hovers (aborted) at (800, offset, 130), beside L01's path; before: a 46 m limit froze L01 at 45.8 m (L4-21)
    hover_route = [wp(0, 800, offset, 0), wp(20, 800, offset, 130), wp(60, 800, offset + 600, 130, action="engage",
                                                                       target="C04")]
    sc, plan = scenario_and_plan(hover_route)
    p = Policy(sc, plan, "L01")
    t = TAU_AT_800 - 2.0
    heard = {"from": "L02", "sent_t": t - 1.0, "payload": [4, 200]}
    action, _ = p.step(obs(t, t, inbox=[heard]))
    assert action["kind"] == kind


@pytest.fixture(scope="module")
def l4_run():
    sc = Scenario.from_dict(generate("L4", 0))
    plan = greedy_plan(sc)
    sent, times = [], []

    class Timed(Policy):
        def step(self, o):
            t0 = time.perf_counter()
            action, msg = super().step(o)
            times.append(time.perf_counter() - t0)
            if msg is not None:
                sent.append(msg)
            return action, msg

    run = simulate(sc, plan, make_events(sc, plan, 1), Timed, setting=(250.0, 50.0), run_seed=0)
    return run, sent, times


def test_every_message_fits_in_64_bytes(l4_run):
    _, sent, _ = l4_run
    assert sent
    assert max(len(json.dumps(m, separators=(",", ":")).encode()) for m in sent) <= 64


def test_step_time_stays_under_50_ms(l4_run):
    run, _, times = l4_run
    assert not any("policy" in f for f in run.failed)
    assert max(times) < 0.050

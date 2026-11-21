"""Unit tests for handin/policy.py (R8 deadlock order, R4 ob delivery, <= 64B messages, < 50ms)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))

from fleetkit.baseline import greedy_plan  # noqa: E402
from fleetkit.generator import generate  # noqa: E402
from fleetkit.linkloss.sim import simulate  # noqa: E402
from fleetkit.model import EFFECTOR, HOSTILE, LIGHT, SCOUT, Aircraft, Contact, Power, Rules, Scenario  # noqa: E402
from handin.policy import Policy  # noqa: E402


def _make_simple_scenario():
    pw = Power(80.0, 0.25, 0.02)
    s1 = Aircraft("S01", SCOUT, None, (0.0, 0.0, 0.0), 20.0, 5.0, 5.0, 100.0, 100.0, pw)
    l1 = Aircraft("L01", EFFECTOR, LIGHT, (0.0, 0.0, 0.0), 20.0, 5.0, 5.0, 100.0, 100.0, pw)
    l2 = Aircraft("L02", EFFECTOR, LIGHT, (0.0, 60.0, 0.0), 20.0, 5.0, 5.0, 100.0, 100.0, pw)
    c1 = Contact("C01", HOSTILE, (1000.0, 0.0, 0.0), {"light": 1}, 100.0, (0.0, 500.0))
    sc = Scenario("T", 1, "L1", 600.0, [s1, l1, l2], [c1], [], Rules())
    plan = {
        "seed": 1,
        "routes": [
            {
                "aircraft": "S01",
                "waypoints": [
                    {"t": 0.0, "x": 0.0, "y": 0.0, "z": 30.0},
                    {"t": 50.0, "x": 900.0, "y": 0.0, "z": 30.0, "action": "observe", "target": "C01", "dwell_s": 5.0},
                    {"t": 110.0, "x": 0.0, "y": 0.0, "z": 30.0},
                ],
            },
            {
                "aircraft": "L01",
                "waypoints": [
                    {"t": 20.0, "x": 0.0, "y": 0.0, "z": 30.0},
                    {"t": 100.0, "x": 980.0, "y": 0.0, "z": 30.0, "action": "engage", "target": "C01"},
                ],
            },
            {
                "aircraft": "L02",
                "waypoints": [
                    {"t": 20.0, "x": 0.0, "y": 60.0, "z": 30.0},
                    {"t": 100.0, "x": 980.0, "y": 60.0, "z": 30.0, "action": "engage", "target": "C01"},
                ],
            },
        ],
    }
    return sc, plan


def test_lower_id_breaks_mutual_hold_when_not_closing() -> None:
    sc, plan = _make_simple_scenario()
    # Put L02 at y=30m so L01 (y=0, tau=40) and L02 (y=30, tau=37) are inside d_lim (44.5m),
    # with L02 behind L01 so L01 moves away while L02 must yield.
    plan["routes"][2]["waypoints"][0]["y"] = 30.0
    plan["routes"][2]["waypoints"][1]["y"] = 30.0
    p_low = Policy(sc, plan, "L01")
    p_high = Policy(sc, plan, "L02")

    # L01 (y=0, tau=40) moving forward moves AWAY from L02 (y=60, tau=30) or test same-y with L02 behind.
    # Use a shared-corridor pair: L01 at tau=40 (x=245, y=0) and L02 at tau=30 (x=122.5, y=0 -> within 40m? Use tau=37 -> x=208.25, 36.75m behind L01).
    obs_low = {
        "t": 45.0, "t_loss": 25.0, "pos": p_low.clock.position(40.0), "vel": (0.0, 0.0, 0.0),
        "tau": 40.0, "next_wp": 1, "mode": "route", "energy_left_wh": 90.0,
        "own_observed": [], "sensed": [],
        "inbox": [{"from": "L02", "sent_t": 44.0, "payload": {"hd": 1, "u": 37.0}}],
        "last_heard": {},
    }
    obs_high = {
        "t": 45.0, "t_loss": 25.0, "pos": p_high.clock.position(37.0), "vel": (0.0, 0.0, 0.0),
        "tau": 37.0, "next_wp": 1, "mode": "route", "energy_left_wh": 90.0,
        "own_observed": [], "sensed": [],
        "inbox": [{"from": "L01", "sent_t": 44.0, "payload": {"hd": 1, "u": 40.0}}],
        "last_heard": {},
    }
    act_low, _ = p_low.step(obs_low)
    act_high, _ = p_high.step(obs_high)
    assert act_low["kind"] == "continue", f"Expected L01 to move, got {act_low}"
    assert act_high["kind"] == "hold", f"Expected L02 to hold, got {act_high}"


def test_effector_aborts_without_ob_and_accepts_relayed_ob() -> None:
    sc, plan = _make_simple_scenario()
    # 1. No ob received before clock.end - 4 -> abort
    p1 = Policy(sc, plan, "L01")
    obs_near_end = {
        "t": 97.0, "t_loss": 25.0, "pos": p1.clock.position(97.0), "vel": (12.0, 0.0, 0.0),
        "tau": 97.0, "next_wp": 1, "mode": "route", "energy_left_wh": 80.0,
        "own_observed": [], "sensed": [], "inbox": [], "last_heard": {},
    }
    act1, _ = p1.step(obs_near_end)
    assert act1["kind"] == "return"

    # 2. Relayed ob received -> continue to engage
    p2 = Policy(sc, plan, "L01")
    obs_relayed = dict(obs_near_end, inbox=[{"from": "L02", "sent_t": 96.0, "payload": {"ob": ["C01"]}}])
    act2, _ = p2.step(obs_relayed)
    assert act2["kind"] == "continue"


def test_scout_failure_causes_zero_r4_failures() -> None:
    sc, plan = _make_simple_scenario()
    events = {"version": 1, "t_loss": 25.0, "events": [{"kind": "failure", "t": 30.0, "aircraft": "S01"}]}
    res = simulate(sc, plan, events, Policy, setting=(1000.0, 200.0), run_seed=0)
    assert res.ok, f"Expected 0 failures, got {res.failed}"
    assert res.dropped_messages == 0


def test_l4_message_size_and_step_latency() -> None:
    sc = Scenario.from_dict(generate("L4", 0))
    plan = greedy_plan(sc)
    p = Policy(sc, plan, plan["routes"][0]["aircraft"])
    obs = {
        "t": 100.0, "t_loss": 80.0, "pos": (0.0, 0.0, 30.0), "vel": (0.0, 0.0, 0.0),
        "tau": 100.0, "next_wp": 1, "mode": "route", "energy_left_wh": 50.0,
        "own_observed": ["C01"], "sensed": [{"kind": "reclassify", "contact": "C02"}],
        "inbox": [], "last_heard": {},
    }
    t0 = time.perf_counter()
    for k in range(200):
        _, msg = p.step(dict(obs, t=100.0 + k, tau=100.0 + k))
        if msg is not None:
            assert len(json.dumps(msg, separators=(",", ":")).encode()) <= 64
    avg_ms = (time.perf_counter() - t0) * 1000.0 / 200.0
    assert avg_ms < 50.0, f"Step took {avg_ms:.2f} ms >= 50 ms"


if __name__ == "__main__":
    test_lower_id_breaks_mutual_hold_when_not_closing()
    test_effector_aborts_without_ob_and_accepts_relayed_ob()
    test_scout_failure_causes_zero_r4_failures()
    test_l4_message_size_and_step_latency()
    print("OK - all policy unit tests passed!")

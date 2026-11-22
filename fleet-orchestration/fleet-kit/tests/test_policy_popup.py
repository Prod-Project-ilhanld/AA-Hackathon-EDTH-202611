"""Pop-up zones against the team's link-loss policy (handin/policy.py).

A `popup_zone` is a no-fly disc (ceiling 200 m) that appears after the cut, on or near a route; entering it
fails the whole run (retention 0). The simulator itself is tested in test_linkloss.py; this file tests OUR
POLICY against it, which no other test does.

What it pins down (measured on main, L1 to L3, popup-only events and combined events):
- a zone that appears on the way forward is avoided: green regression guard;
- a zone that appears BEHIND an aircraft that has already turned back: the policy used to retrace its route into
  it. Since #19 an aborted aircraft hovers, and every back-off checks known zones on the way back, so the
  hand-built case passes (its xfail marker is removed). check_policy's L1-6 still fails (also with `broadcast`).

`POLICY_UNDER_TEST=path/to/policy.py python3 -m pytest tests/test_policy_popup.py` runs the same tests on
another copy of the policy (e.g. a patch under review). Standard library only, Python 3.9.
"""
import os
import random
from pathlib import Path

import pytest

from fleetkit.baseline import greedy_plan
from fleetkit.generator import generate
from fleetkit.geometry import dist3
from fleetkit.linkloss import RouteClock, simulate
from fleetkit.linkloss.events import make_events
from fleetkit.linkloss.policies import BroadcastSensePolicy, ContinuePolicy, load_policy
from fleetkit.model import Scenario, parse_plan

KIT = Path(__file__).resolve().parents[1]
POLICY_PATH = os.environ.get("POLICY_UNDER_TEST") or str(KIT / "handin" / "policy.py")


@pytest.fixture(scope="module")
def team():
    return load_policy(POLICY_PATH)


def ev(*events, t_loss=50.0):
    return {"t_loss": t_loss, "events": list(events)}


def popup(t, x, y, radius, top=200.0):
    return {"kind": "popup_zone", "t": t, "center": [x, y], "radius_m": radius, "top_m": top}


# The small hand-written scenario of conftest: L01 engages C01 at (1500, 0) along y = 0 (cruise 130 m, t = 69 to 135 s),
# S01 observes it from (1450, 100). A zone of radius 30 centred on y = -20 sits on L01's line and 68 m from S01's.
RECLASSIFY_C01 = {"kind": "reclassify", "t": 70.0, "contact": "C01"}


def test_a_zone_ahead_on_the_route_is_avoided(scenario, plan, team):
    events = ev(popup(60.0, 1000.0, 70.0, 100.0))
    assert simulate(scenario, plan, events, oracle=True).ok               # the case is fair
    assert any("pop-up zone" in f for f in simulate(scenario, plan, events, ContinuePolicy).failed)   # and it bites
    assert simulate(scenario, plan, events, team).ok


def test_a_zone_above_every_ceiling_changes_nothing(scenario, plan, team):
    events = ev(popup(60.0, 1000.0, 70.0, 100.0, top=20.0))
    result = simulate(scenario, plan, events, team)
    assert result.ok and result.points == simulate(scenario, plan, events, oracle=True).points


def test_the_hand_built_case_is_fair(scenario, plan):
    """Abort (the contact turns friendly), then a zone behind the returning aircraft: the oracle copes, so a
    policy that fails here is the one at fault. The shipped broadcast baseline copes too."""
    events = ev(RECLASSIFY_C01, popup(118.0, 700.0, -20.0, 30.0))
    assert simulate(scenario, plan, events, oracle=True).ok
    assert simulate(scenario, plan, events, BroadcastSensePolicy).ok
    assert any("engaged C01" in f for f in simulate(scenario, plan, events, ContinuePolicy).failed)


def test_a_zone_behind_an_aircraft_that_turned_back_is_avoided(scenario, plan, team):
    events = ev(RECLASSIFY_C01, popup(118.0, 700.0, -20.0, 30.0))
    assert simulate(scenario, plan, events, team).ok


def popup_only_events(sc, plan, seed, tries=200):
    """One pop-up zone placed on a route as in the official event draw, kept only if the oracle copes and the
    blind plan fails; None if no such draw is found."""
    routes, _ = parse_plan(plan)
    clocks = {a: RouteClock(r) for a, r in routes.items()}
    span = max(c.end for c in clocks.values())
    rng = random.Random("popup:%d:%d" % (sc.seed, seed))
    for _ in range(tries):
        t_loss = float(round(rng.uniform(0.25 * span, 0.5 * span)))
        aid = rng.choice(sorted(clocks))
        clock = clocks[aid]
        lo, hi = max(t_loss + 35, clock.start + 10), clock.end - 10
        if hi <= lo:
            continue
        tp = rng.uniform(lo, hi)
        c = clock.position(tp)
        if c[2] < 20.0 or tp - 25 <= t_loss + 5:
            continue
        te = float(round(rng.uniform(t_loss + 5, tp - 25)))
        radius = float(round(rng.uniform(60, 120)))
        if any(dist3((c[0], c[1], 0), (k.position(te)[0], k.position(te)[1], 0)) < radius + 15
               for k in clocks.values()):
            continue                                            # nobody is inside when it appears
        events = ev(popup(te, round(c[0], 1), round(c[1], 1), radius), t_loss=t_loss)
        if simulate(sc, plan, events, oracle=True).failed or simulate(sc, plan, events, oracle=True).points <= 0:
            continue
        if not simulate(sc, plan, events, ContinuePolicy).failed:
            continue
        return events
    return None


@pytest.mark.parametrize("level,seed", [(lv, s) for lv in ("L1", "L2") for s in range(4)])
def test_a_popup_alone_on_a_generated_case_never_fails_the_policy(level, seed, team):
    sc = Scenario.from_dict(generate(level, seed))
    plan = greedy_plan(sc)
    events = popup_only_events(sc, plan, 1)
    if events is None:
        pytest.skip("no fair pop-up draw for this case")
    assert simulate(sc, plan, events, team).ok


def test_the_popup_draw_finds_cases(team):
    """Guard against the sweep above going silently empty (a generator change would skip every case)."""
    found = 0
    for seed in range(4):
        sc = Scenario.from_dict(generate("L2", seed))
        found += popup_only_events(sc, greedy_plan(sc), 1) is not None
    assert found >= 2


@pytest.mark.xfail(strict=False, reason="check_policy.py L1-6 (events: failure, reclassify, popup_zone): same cause as "
                                        "the hand-built case. Not strict: this case depends on the generator and on "
                                        "greedy_plan, so it may legitimately stop failing for other reasons.")
def test_l1_seed_6_of_check_policy_does_not_fail(team):
    sc = Scenario.from_dict(generate("L1", 6))
    plan = greedy_plan(sc)
    events = make_events(sc, plan, 7)                           # check_policy.py uses seed + 1
    assert simulate(sc, plan, events, team).ok


def test_l3_21_of_the_sizing_grid_does_not_hover_into_a_popup_at_2000_m(team):
    """Sizing case L3-21 (events seed 1): at 2000 m, H03 hears C06's reclassification early and used to hover where
    a zone appeared 8 s later (4 failed runs out of 5 in every 2000 m cell). A planned position is never inside a
    zone when it appears, so a reclassified effector now keeps to its plan until just short of its target."""
    sc = Scenario.from_dict(generate("L3", 21))
    plan = greedy_plan(sc)
    events = make_events(sc, plan, 1)
    assert simulate(sc, plan, events, team, setting=(2000.0, 50.0), run_seed=1).ok

"""Tests unitaires autonomes pour handin/routing.py (Phases 1, 2 et 3-4)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
HANDIN = KIT / "handin"
sys.path.insert(0, str(KIT))
sys.path.insert(0, str(HANDIN))

from fleetkit.baseline import _detour as baseline_detour, greedy_plan  # noqa: E402
from fleetkit.energy import route_energy_wh  # noqa: E402
from fleetkit.generator import generate  # noqa: E402
from fleetkit.geometry import hdist  # noqa: E402
from fleetkit.model import (  # noqa: E402
    SCOUT,
    Aircraft,
    Power,
    Rules,
    Scenario,
    Waypoint,
    Zone,
    parse_plan,
)
from routing import (  # noqa: E402
    RoutingEngine,
    build_effector_route,
    build_scout_route,
    extract_cylinders,
    leg_cost_fast,
    optimal_leg_3d,
    route_cost_fast,
    shortest_2d_path,
)


def _wps_energy(wps: list, ac: Aircraft) -> float:
    objs = [
        Waypoint(w["t"], w["x"], w["y"], w["z"], w.get("action"), w.get("target"), w.get("dwell_s", 0.0))
        for w in wps
    ]
    return route_energy_wh(objs, ac)


def test_phase1_lower_energy_than_baseline() -> None:
    """Phase 1 : énergie strictement inférieure au glouton à affectations égales."""
    base_e_tot = 0.0
    our_e_tot = 0.0
    n_routes = 0

    for level in ("L1", "L2", "L3"):
        for seed in (0, 1, 2):
            sc = Scenario.from_dict(generate(level, seed))
            routes, _ = parse_plan(greedy_plan(sc))
            assert routes is not None
            ac_by_id = sc.aircraft_by_id()
            c_by_id = sc.contact_by_id()
            eng = RoutingEngine(sc)

            for aid, rt in routes.items():
                ac = ac_by_id[aid]
                base_e = route_energy_wh(rt.waypoints, ac)
                if ac.type == SCOUT:
                    tasks = [c_by_id[w.target] for w in rt.waypoints if w.action == "observe" and w.target]
                    if not tasks:
                        continue
                    wps = build_scout_route(ac, tasks, sc, z_layer=sc.rules.z_min_m, engine=eng)
                    assert wps is not None
                else:
                    last = rt.waypoints[-1]
                    assert last.target is not None
                    wps, _ = build_effector_route(ac, c_by_id[last.target], last.t, sc, z_layer=None, engine=eng)
                    assert wps is not None
                base_e_tot += base_e
                our_e_tot += _wps_energy(wps, ac)
                n_routes += 1

    saving = 100.0 * (base_e_tot - our_e_tot) / base_e_tot
    print(f"[Phase 1] {n_routes} routes : baseline={base_e_tot:.1f} Wh | ours={our_e_tot:.1f} Wh (-{saving:.1f}%)")
    assert our_e_tot < base_e_tot


def test_phase2_overflight_and_shorter_detours() -> None:
    """Phase 2 : survol 3D si moins cher que contourner + détours 2D plus courts que le glouton."""
    ac = Aircraft(
        id="S01", type=SCOUT, subtype=None, home=(0.0, 0.0, 0.0),
        v_h_mps=20.0, v_up_mps=6.0, v_down_mps=6.0,
        capacity_wh=50.0, battery_pct=100.0,
        power=Power(p0_w=80.0, k_v=0.25, e_climb_wh_per_m=0.02),
    )

    # Zone large et basse -> survol au-dessus du plafond (40 m) moins cher
    sc_low = Scenario("1", 1, "L1", 600.0, [ac], [], [Zone("Z1", (1000.0, 0.0), 400.0, 40.0)], Rules())
    res_low = optimal_leg_3d((0.0, 0.0, 30.0), (2000.0, 0.0, 30.0), ac, sc_low)
    assert res_low is not None and max(p[2] for p in res_low[0]) > 40.0

    # Zone haute -> contournement 2D plus court que baseline._detour
    sc_high = Scenario("1", 2, "L1", 600.0, [ac], [], [Zone("Z1", (1000.0, 0.0), 250.0, 145.0)], Rules())
    our_2d = shortest_2d_path((0.0, 0.0), (2000.0, 0.0), 30.0, extract_cylinders(sc_high))
    base_3d = baseline_detour([(0.0, 0.0, 30.0), (2000.0, 0.0, 30.0)], sc_high)
    assert our_2d is not None and base_3d is not None
    our_len = sum(hdist(our_2d[i], our_2d[i + 1]) for i in range(len(our_2d) - 1))
    base_len = sum(hdist(base_3d[i], base_3d[i + 1]) for i in range(len(base_3d) - 1))
    print(f"[Phase 2] détour 2D : ours={our_len:.1f} m vs baseline={base_len:.1f} m | survol max_z={max(p[2] for p in res_low[0]):.1f} m")
    assert our_len < base_len


def test_phase3_fast_cost_api_for_louis() -> None:
    """Phases 3-4 : API rapide mémoïsée `leg_cost_fast` / `route_cost_fast`."""
    sc = Scenario.from_dict(generate("L2", 7))
    eng = RoutingEngine(sc)
    ac = sc.aircraft[0]
    p0 = ac.home
    p1 = (sc.contacts[0].pos[0], sc.contacts[0].pos[1], 30.0)
    p2 = (sc.contacts[1].pos[0], sc.contacts[1].pos[1], 30.0)

    d1, e1 = leg_cost_fast(p0, p1, ac.id, sc, engine=eng)
    d2, e2 = leg_cost_fast(p1, p2, ac.id, sc, engine=eng)
    dt, et = route_cost_fast([p0, p1, p2], ac.id, sc, engine=eng)
    assert abs(dt - (d1 + d2)) < 1e-9
    assert abs(et - (e1 + e2)) < 1e-9

    t0 = time.monotonic()
    for _ in range(1000):
        leg_cost_fast(p0, p1, ac.id, sc, engine=eng)
    ms = (time.monotonic() - t0) * 1000.0
    print(f"[Phase 3-4] 1000 appels leg_cost_fast (cache) en {ms:.2f} ms")
    assert ms < 100.0


if __name__ == "__main__":
    test_phase1_lower_energy_than_baseline()
    test_phase2_overflight_and_shorter_detours()
    test_phase3_fast_cost_api_for_louis()
    print("OK - Phases 1, 2 et 3-4 validées !")

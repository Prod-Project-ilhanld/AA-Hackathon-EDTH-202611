"""Scout tours: serve the unknown contacts the greedy pass left unserved. Off by default.

The greedy planner appends each observation at the END of one scout's tour and serves the unknowns
last, with the 6 nearest scouts only. Here, for every unserved unknown (richest first), every scout
(already-flying ones first, far ones too) and every insertion position in its tour is tried; the best
VALID net-score gain is kept. The kit scorer decides (planner._try), so a plan stays valid by
construction: an insertion that delays an observation an engagement relies on (R4) is simply refused.

Turn on with ENABLED = True (or PLANNER_SCOUTS=1); compare with tools/bench.py.
Python 3.9, standard library only; kit code from `fk`, never `fleetkit`.
"""
import os

ENABLED = os.environ.get("PLANNER_SCOUTS", "0") == "1"
LAYERS = (70.0, 110.0)
ANGLES = (0.0, 60.0, -60.0)
SHIFTS = (0.0, 7.0)


def _served_unknowns(planner):
    done = set()
    for tasks in planner.tasks.values():
        for t in tasks:
            done.add(t["cid"] if isinstance(t, dict) else t.id)
    return done


def _tour_ids(tasks):
    return [t["cid"] if isinstance(t, dict) else t.id for t in tasks]


def sweep_unknowns(planner, unknowns, scout_type, hdist) -> int:
    """Tries to add every unknown in `unknowns` to some scout tour; returns how many were added."""
    added = 0
    if not ENABLED or not hasattr(planner, "eng"):  # needs the routed planner (tasks are Contact objects)
        return 0
    from fk.baseline import SCOUT_LAYERS  # noqa: F401  (kept for symmetry with the greedy options)
    import routing
    scouts = [a for a in planner.sc.aircraft if a.type == scout_type]
    for contact in unknowns:
        if contact.id in _served_unknowns(planner):
            continue
        best = None  # (score, scout, tasks, route)
        flying = [s for s in scouts if planner.tasks[s.id]]
        idle = sorted((s for s in scouts if not planner.tasks[s.id]), key=lambda s: hdist(s.home, contact.pos))
        for scout in flying + idle:
            base = planner.tasks[scout.id]
            for pos in range(len(base) + 1):
                tasks = base[:pos] + [contact] + base[pos:]
                for z in LAYERS:
                    for angle in ANGLES:
                        for shift in SHIFTS:
                            planner._check_time()
                            try:
                                route = routing.build_scout_route(
                                    scout, tasks, planner.sc, z_layer=z, depart_shift=shift,
                                    engine=planner.eng, angle_offset_deg=angle)
                            except Exception:  # noqa: BLE001
                                route = None
                            if route is None or not planner._prefilter({scout.id: route}):
                                continue
                            new = planner._try({scout.id: route})
                            if new is not None and new > planner.score and (best is None or new > best[0]):
                                best = (new, scout, tasks, route)
        if best is not None:
            planner.score, scout, tasks, route = best
            planner.routes[scout.id] = route
            planner.tasks[scout.id] = tasks
            added += 1
    return added

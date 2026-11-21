"""R8 separation (40 m in 3D between airborne aircraft). Starter file: planner.py calls it, OFF by default.

R8 is the main wall at L4: all aircraft start from one pad grid (pads 11.1 m apart at L4) and most rejected
candidates fail on separation near the pads. Idea to build here (docs/ROADMAP.md §3, WS4):
- departure scheduler: shift each new route's take-off to the first time where its WHOLE route stays 40 m
  from every route already in the plan (`fk.validator.separation_item` / `separation_violation` on the
  pair; jump to the end of each conflict interval from `fk.geometry.close_intervals`), climb out diagonally;
- an effector's take-off can only move if its strike still falls inside the window and the 20 s sync of its
  group (R9/R10) — shifting the whole group together is the simple safe version;
- waiting on the ground is free and not checked by R8; hovering costs energy.

Turn on with ENABLED = True (or PLANNER_DECONFLICT=1) and compare with tools/bench.py on many seeds.
Python 3.9, standard library only; kit code from `fk`, never `fleetkit`.
"""
from typing import Dict, List

import params

ENABLED = params.DECONFLICT


def adjust(planner, extra: Dict[str, List[dict]]) -> bool:
    """Called in FastPlanner._try before checking a candidate. Return False to reject it.

    `planner.routes` holds the routes already accepted (aircraft id -> waypoint dicts), `extra` the new or
    changed routes. Edit the waypoints in `extra` IN PLACE (e.g. shift the times): the caller keeps using
    that same dict when it accepts the candidate. Every accepted plan is still checked by the official
    validator, so a bug here costs points, not validity.
    """
    if not ENABLED:
        return True
    return True  # TODO: departure scheduler

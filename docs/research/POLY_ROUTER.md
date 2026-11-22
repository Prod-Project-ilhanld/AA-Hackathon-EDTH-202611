# Circles to polygons: what a visibility-graph router is worth (Sun 22 Nov)

A contestant's tip was "turn the circles into polygons". Our `handin/routing.py` already does this
(12-gon visibility graph, A*, overflight arbitrage). This note records two things:

1. **How much the idea is worth on its own**, measured on the kit baseline planner (not our planner).
2. **A self-check of our router**, `tools/check_routing.py`, with one finding.

## 1. Polygon router vs. the kit's push-out detour (kit baseline planner)

Setup: the kit baseline greedy (`fleetkit/baseline.py`), whose `_detour` pushes one waypoint to
radius + 60 m off the nearest circle, up to 12 times. Replacement: a circumscribed 16-gon per circle,
5 m outside it, visibility graph built once per (scenario, altitude), Dijkstra per leg, edges checked
against the true circles + 0.5 m. Scores from a jury-style run (fresh copy, 60 s limit, official validator).

Leg level (random blocked legs, L3/L4 seeds 0-3, z 40/85): the kit detour finds no path on about 9 % of
blocked L4 legs (2 % at L3); the polygon graph routed all 1432 and none entered a circle. Paths are only
about 1 % shorter (20-27 m per blocked leg). **The gain is reachability, not distance.**

Plan level, L3 + L4:

| Variant | Seeds 0-9 | Change | Holdout 5000-5009 | Change | Slowest run |
|---|---|---|---|---|---|
| Kit detour (baseline) | 8515.5 | | 9390.0 | | 13.6 s |
| Polygon router for every leg | 8498.8 | **-16.7** | not run | | 17.9 s |
| Polygon router only when the kit detour fails | 8587.5 | **+72.0** | 9393.7 | **+3.7** | 18.9 s |

All 60 runs valid. With the fallback, no seed lost more than 0.2 points. The wins are extra contacts
served: L4-1 14 -> 15 contacts (+41), L3-7 10 -> 12 (+19), L3-8 8 -> 9 (+12), L4-5006 +3.5.

**Lesson: better routes can lower a greedy planner's score.** Replacing every leg won big on some seeds
(L4-1 +41, L4-0 +20) and lost big on others (L4-8 -53, L3-4 -48): a different route for an early contact
changes which aircraft are free for later ones. A 5 to 15 m margin change did not remove it. A greedy
decoder's score moves by about +/-50 per seed when its legs change slightly, so judge routing changes
on paired seeds (our merge rule), never on one or two scenarios.

Cost: building the graph is 0.3-0.7 s per altitude at L4 in pure Python, so +3 to 5 s per L4 run.

## 2. Self-check of our router: `tools/check_routing.py`

Random legs at fixed altitude. Asserts that every path returned by `routing.shortest_2d_path` keeps its
endpoints and never enters a true cylinder (exact radius, the validator's `segment_enters_cylinder`),
and counts legs with no path that the kit detour does route.

    cd fleet-orchestration/fleet-kit
    python3 tools/check_routing.py                                                   # ~6 s
    python3 tools/check_routing.py --levels L1,L2,L3,L4 --seeds 0-9 --alts 30,40,72,85,114,130 --legs 200

Result on `main` (8e4a799):

- L3/L4 seeds 0-3, z 40/85: 1442 blocked legs, **0 enter a cylinder, 0 without a path**, 6 s.
  About 3x faster than the 16-gon Dijkstra above.
- L1-L4 seeds 0-9, six altitudes: 8772 blocked legs, 0 enter a cylinder; **38 legs get no path while
  the kit detour routes them.**

**Finding: those 38 legs all fly exactly at a zone's top** (L1-9 at 72 m, zone top 72 m: 30 legs; L4-4 and
L4-7 at 40 m; L4-8 at 85 m). The validator allows that (`z < top - EPS` counts as inside). Our router
treats a zone as active while `z < top + SAFE_MARGIN_Z / 2`, so at z == top the zone blocks, and a leg
with an endpoint inside its footprint has no path. It is a deliberate safety margin, not a safety bug.
It matters because the planner's cruise layers are whole metres (effectors 40/85/130 m and scouts 70/110 m,
from `fk.baseline`; `ALTITUDE_LAYERS` in `routing.py` is unused) and so are generated zone tops (40-120 m).
**31 of 100 L4 scenarios** (15/100 L3, 7/100 L2, 4/100 L1) have a zone topped at exactly one of those layers,
which then blocks that layer for legs that start or end over the zone.
Follow-up: cruise 0.5 m above each layer instead of shrinking the margin (paired gate in progress).

## Recommendation

- No change to our router: it is safe on every leg tested and already a polygon visibility graph.
- Keep `tools/check_routing.py` as a regression test when `routing.py` changes.
- Any routing change must pass the paired-seed merge rule. The kit experiment shows plan scores swinging
  +/-50 per seed from route changes alone.

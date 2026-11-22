"""Self-check for handin/routing.shortest_2d_path: random legs at fixed altitude on L3/L4. Every returned path
must keep its endpoints and stay out of every true zone/protected cylinder (exact radius, the validator's own
segment test). Also counts legs where it returns None while the kit baseline detour does find a path.

    python3 tools/check_routing.py                  # L3,L4 seeds 0-3, z 40 and 85
    python3 tools/check_routing.py --seeds 0-9 --legs 500
"""
import argparse
import os
import random
import sys
import time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)
sys.path.insert(0, os.path.join(KIT, "handin"))

from fleetkit.baseline import _detour  # noqa: E402
from fleetkit.generator import generate  # noqa: E402
from fleetkit.geometry import segment_enters_cylinder  # noqa: E402
from fk.model import Scenario  # noqa: E402
import routing  # noqa: E402


def seeds(text):
    lo, _, hi = text.partition("-")
    return range(int(lo), int(hi or lo) + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", default="L3,L4")
    ap.add_argument("--seeds", default="0-3")
    ap.add_argument("--alts", default="40,85")
    ap.add_argument("--legs", type=int, default=300, help="random legs per (scenario, altitude)")
    a = ap.parse_args()
    rng = random.Random(0)
    blocked = none = kit_found = 0
    t0 = time.monotonic()
    for level in a.levels.split(","):
        for seed in seeds(a.seeds):
            sc = Scenario.from_dict(generate(level, seed))
            cyl = routing.extract_cylinders(sc)
            xs = [c.pos[0] for c in sc.contacts] + [p.home[0] for p in sc.aircraft]
            ys = [c.pos[1] for c in sc.contacts] + [p.home[1] for p in sc.aircraft]
            for z in (float(v) for v in a.alts.split(",")):
                live = [c for c in cyl if c[3] > z]
                for _ in range(a.legs):
                    p0 = (rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys)))
                    p1 = (rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys)))
                    # skip endpoints inside a cylinder or within the router's safety margin of one
                    if any((p[0] - cx) ** 2 + (p[1] - cy) ** 2 < (r + 2.0) ** 2
                           for cx, cy, r, _, _ in live for p in (p0, p1)):
                        continue
                    pts = routing.shortest_2d_path(p0, p1, z, cyl)
                    if pts is None or len(pts) > 2:
                        blocked += 1
                    if pts is None:
                        none += 1
                        kit_found += _detour([(p0[0], p0[1], z), (p1[0], p1[1], z)], sc) is not None
                        continue
                    assert tuple(pts[0]) == p0 and tuple(pts[-1]) == p1, (level, seed, z, pts)
                    for u, v in zip(pts, pts[1:]):
                        for cx, cy, r, top, cid in cyl:
                            assert not segment_enters_cylinder((u[0], u[1], z), (v[0], v[1], z), (cx, cy), r, top), \
                                (level, seed, z, u, v, cid)
    print("ok: %d blocked legs, 0 enter a cylinder; no path on %d, of which the kit detour routes %d; %.1fs"
          % (blocked, none, kit_found, time.monotonic() - t0))


if __name__ == "__main__":
    main()

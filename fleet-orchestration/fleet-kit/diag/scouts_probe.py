"""Calls planner.build once (RoutedPlanner) on a scenario and reports what scouts.sweep_unknowns did, exceptions included."""
import os, sys, time, traceback
os.environ["PLANNER_SCOUTS"] = "1"
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(KIT, "handin"), KIT, os.path.join(KIT, "tools")]
import scouts, planner
from fleetkit import generator
from shift import VARIANTS
from fk.model import Scenario, UNKNOWN
for n, (e, f) in VARIANTS.items():
    generator.LEVELS[n] = e
orig = scouts.sweep_unknowns
def probe(p, unknowns, *a):
    before = len(scouts._served_unknowns(p))
    try:
        n = orig(p, unknowns, *a)
        print("  sweep added", n, "| unknowns served before", before, "of", len(unknowns))
        return n
    except Exception:
        print("  sweep RAISED:"); traceback.print_exc(); raise
scouts.sweep_unknowns = probe
planner.scouts.sweep_unknowns = probe
for lv, sd in [(a, int(b)) for a, b in (x.split(":") for x in sys.argv[1:])]:
    sc = Scenario.from_dict(generator.generate(lv, sd))
    print(lv, sd)
    t = time.monotonic()
    planner.build(sc, lambda c: -c.points, time.monotonic() + 120, 15, planner.RoutedPlanner)
    print("  build %.1fs" % (time.monotonic() - t))

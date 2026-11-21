"""tools/bench.py on shift variants: registers the variants in generator.LEVELS (as shift.py does), then runs bench.

    python3 diag/bench_variant.py --levels S-half-scouts --seeds 0-19 --base '' --json out.json
Only variants with ensure_feasible=True (bench always generates with the default).
"""
import os
import sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)
sys.path.insert(0, os.path.join(KIT, "tools"))

import bench  # noqa: E402
from fleetkit import generator  # noqa: E402
from shift import VARIANTS  # noqa: E402

for name, (entry, feasible) in VARIANTS.items():
    if feasible:
        generator.LEVELS[name] = entry

if __name__ == "__main__":
    bench.main()

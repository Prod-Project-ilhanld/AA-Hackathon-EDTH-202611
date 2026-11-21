"""Paired comparison of two bench JSON files (same levels and seeds): B minus A, per seed.

    python3 diag/paired.py off.json on.json
Prints mean delta ± standard error, the % change of the totals, seeds worse, and invalid runs in each file.
"""
import json
import math
import sys

a = {(r["level"], r["seed"]): r for r in json.load(open(sys.argv[1]))["rows"]}
b = {(r["level"], r["seed"]): r for r in json.load(open(sys.argv[2]))["rows"]}
keys = sorted(set(a) & set(b))
d = [b[k]["mine"] - a[k]["mine"] for k in keys]
n = len(d)
mean = sum(d) / n
se = math.sqrt(sum((x - mean) ** 2 for x in d) / (n - 1) / n) if n > 1 else float("nan")
ta, tb = sum(a[k]["mine"] for k in keys), sum(b[k]["mine"] for k in keys)
worse = [k[1] for k, x in zip(keys, d) if x < -1e-9]
better = sum(1 for x in d if x > 1e-9)
print("seeds %d | total A %.1f B %.1f (%+.2f %%) | delta/seed %+.2f ± %.2f (s.e.) | better %d, equal %d, worse %d (%.0f %%) %s"
      % (n, ta, tb, 100 * (tb - ta) / ta, mean, se, better, n - better - len(worse), len(worse),
         100 * len(worse) / n, worse))
print("invalid A %d, B %d" % (sum(not a[k]["valid"] for k in keys), sum(not b[k]["valid"] for k in keys)))

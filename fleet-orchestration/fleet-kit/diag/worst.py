"""Worst seeds of a shift variant by share of the upper bound, with Swann's report and a static reason per miss.

    python3 diag/worst.py S-battery diag/shift2_battery.json /tmp/fleetshift_xxxx [--keep 3]

Share = planner score / bound.bound(scenario). For the --keep worst seeds: writes scenario.json and plan.json
into diag/diag_<variant>_<seed>/, runs `demo/swann_demo.py` there (explication.md, view.html), then classifies
every unserved hostile/unknown with a static check (straight-line flight, like tools/bound.py):
  R7            hostile within collateral_radius_m of a friendly/civilian
  scout_window  no scout can finish its observation inside the window (too far / too slow), battery ignored
  scout_energy  some scout is in time, but none has the battery for the round trip
  eff_window    for a needed subtype, fewer effectors than needed can arrive in time (battery ignored)
  eff_energy    enough in time, but fewer than needed also have the battery
  contention    statically feasible: lost to resource sharing in the plan (scout time, effectors taken,
                R8 separation / R10 sync); the static check cannot tell these apart
Output: diag/worst_<variant>.md and diag/shares_<variant>.csv.
"""
import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)
sys.path.insert(0, os.path.join(KIT, "tools"))

import bound as B  # noqa: E402
from fleetkit import generator  # noqa: E402
from fleetkit.geometry import hdist  # noqa: E402
from fleetkit.model import CIVILIAN, EFFECTOR, FRIENDLY, HOSTILE, SCOUT, UNKNOWN, Scenario, save_json  # noqa: E402
from shift import VARIANTS  # noqa: E402

OUT = os.path.join(KIT, "diag")
MISS = re.compile(r"^- \*\*(C\d+)\*\* · (\w+), ([\d.]+) pts, .*· (.*)$")


def scout_reason(sc, c):
    r, ok_time = sc.rules, False
    for s in (a for a in sc.aircraft if a.type == SCOUT):
        t_go, e_go = B._fly(s, hdist(s.home, c.pos), r.R_obs_m)
        start = t_go if c.window is None else max(t_go, c.window[0])
        end = start + r.obs_dwell_s
        if (c.window is not None and end > c.window[1]) or end > sc.horizon_s:
            continue
        ok_time = True
        if 2.0 * e_go + s.power.p0_w * r.obs_dwell_s / B.J_PER_WH <= s.usable_wh:
            return None, end
    return ("scout_energy" if ok_time else "scout_window"), None


def classify(sc, c):
    r = sc.rules
    if c.cls == HOSTILE and any(f.cls in (FRIENDLY, CIVILIAN) and hdist(c.pos, f.pos) < r.collateral_radius_m
                                for f in sc.contacts):
        return "R7"
    why, obs_end = scout_reason(sc, c)
    if why:
        return why
    if c.cls != HOSTILE:
        return "contention"
    t_min = obs_end + r.confirm_margin_s
    if c.window is not None:
        t_min = max(t_min, c.window[0])
    for sub, need in c.needs.items():
        in_time = in_both = 0
        for a in (a for a in sc.aircraft if a.type == EFFECTOR and a.subtype == sub):
            t_go, e_go = B._fly(a, hdist(a.home, c.pos), r.R_eng_m)
            t = max(t_go, t_min)
            if t > sc.horizon_s or (c.window is not None and t > c.window[1]):
                continue
            in_time += 1
            in_both += e_go <= a.usable_wh
        if in_time < need:
            return "eff_window"
        if in_both < need:
            return "eff_energy"
    return "contention"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant")
    ap.add_argument("shift_json")
    ap.add_argument("plan_dir", help="the fleetshift_* work dir of that run (holds <variant>-<seed>.mine.plan.json)")
    ap.add_argument("--keep", type=int, default=3)
    args = ap.parse_args()
    entry, feasible = VARIANTS[args.variant]
    generator.LEVELS[args.variant] = entry  # same registration as shift.py

    rows = [r for r in json.load(open(args.shift_json))["rows"] if r["level"] == args.variant]
    shares = []
    for r in rows:
        data = generator.generate(args.variant, r["seed"], ensure_feasible=feasible)
        b = B.bound(Scenario.from_dict(data))["bound"]
        shares.append({"seed": r["seed"], "mine": r["mine"], "bound": round(b, 1),
                       "share": round(r["mine"] / b, 4) if b > 0 else None, "valid": r["valid"]})
    with open(os.path.join(OUT, "shares_%s.csv" % args.variant), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(shares[0]))
        w.writeheader()
        w.writerows(shares)
    ranked = sorted((s for s in shares if s["share"] is not None), key=lambda s: s["share"])
    total_share = sum(s["mine"] for s in shares) / sum(s["bound"] for s in shares)

    md = ["# %s: 3 worst seeds by share of the bound\n" % args.variant,
          "Seeds %d, total score / total bound = %.1f %%, median seed share = %.1f %%.\n" % (
              len(shares), 100 * total_share, 100 * ranked[len(ranked) // 2]["share"])]
    for s in ranked[:args.keep]:
        seed = s["seed"]
        d = os.path.join(OUT, "diag_%s_%d" % (args.variant, seed))
        os.makedirs(d, exist_ok=True)
        data = generator.generate(args.variant, seed, ensure_feasible=feasible)
        save_json(data, os.path.join(d, "scenario.json"))
        shutil.copy(os.path.join(args.plan_dir, "%s-%d.mine.plan.json" % (args.variant, seed)), os.path.join(d, "plan.json"))
        env = dict(os.environ, PYTHONPATH=os.pathsep.join([KIT, os.path.join(KIT, "handin")]))  # real routing in the report
        subprocess.run([sys.executable, os.path.join(KIT, "demo", "swann_demo.py"), os.path.join(d, "scenario.json"),
                        os.path.join(d, "plan.json"), "-o", d], cwd=KIT, env=env, check=True,
                       stdout=subprocess.DEVNULL)
        sc = Scenario.from_dict(data)
        by_id = sc.contact_by_id()
        missed = []
        for line in open(os.path.join(d, "explication.md"), encoding="utf-8"):
            m = MISS.match(line.strip())
            if m and m.group(2) in (HOSTILE, UNKNOWN):
                cid = m.group(1)
                missed.append((cid, m.group(2), float(m.group(3)), classify(sc, by_id[cid]), m.group(4)))
        n_h = sum(1 for c in sc.contacts if c.cls == HOSTILE)
        n_u = sum(1 for c in sc.contacts if c.cls == UNKNOWN)
        mh = [x for x in missed if x[1] == HOSTILE]
        mu = [x for x in missed if x[1] == UNKNOWN]
        md.append("## %s seed %d: %.1f %% of the bound (score %.1f, bound %.1f)\n" % (
            args.variant, seed, 100 * s["share"], s["mine"], s["bound"]))
        md.append("Unserved: **%d / %d hostiles** (%g pts), **%d / %d unknowns** (%g pts). Report: `%s/explication.md`.\n" % (
            len(mh), n_h, sum(x[2] for x in mh), len(mu), n_u, sum(x[2] for x in mu), os.path.relpath(d, KIT)))
        for label, group in (("Hostiles", mh), ("Unknowns", mu)):
            counts = {}
            for x in group:
                counts.setdefault(x[3], [0, 0.0])
                counts[x[3]][0] += 1
                counts[x[3]][1] += x[2]
            md.append("- %s by static reason: %s" % (label, ", ".join(
                "%s %d (%g pts)" % (k, v[0], v[1]) for k, v in sorted(counts.items(), key=lambda kv: -kv[1][1])) or "none"))
        md.append("\n| Contact | Class | Points | Static reason | Swann's verdict |\n|---|---|---|---|---|")
        for x in sorted(missed, key=lambda x: -x[2]):
            md.append("| %s | %s | %g | %s | %s |" % (x[0], x[1], x[2], x[3], x[4].replace("|", "/")))
        md.append("")
    with open(os.path.join(OUT, "worst_%s.md" % args.variant), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()

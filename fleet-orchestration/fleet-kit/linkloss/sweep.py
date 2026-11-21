"""Sweeps for the link-loss study: robustness of margin-hardened plans, and the communication sizing curve.

Usage, from fleet-kit/:
    python3 -m linkloss.sweep --levels L2 L3 --seeds 0-3 --draws 30 --out linkloss/results
Plans are produced by handin/planner.py (short budget) on the scenario hardened to each margin level, then
validated against the REAL scenario. Writes robustness.csv, sizing.csv and sizing.svg into --out.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from collections import defaultdict
from typing import Dict, List

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit.generator import generate  # noqa: E402
from fleetkit.model import Scenario  # noqa: E402
from fleetkit.scorer import evaluate  # noqa: E402
from linkloss.harden import LEVELS, harden  # noqa: E402
from linkloss.sim import Comms, Disturbance, simulate  # noqa: E402

PLANNER = os.path.join(KIT, "handin", "planner.py")


def parse_seeds(text: str) -> List[int]:
    """Parses '0-3' or '1,4,7'."""
    out: List[int] = []
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        out.extend(range(int(lo), int(hi or lo) + 1))
    return out


def make_plan(data: dict, budget: str, workers: str) -> dict:
    """Runs the hand-in planner on a scenario dictionary and returns its plan."""
    with tempfile.TemporaryDirectory() as tmp:
        scen, out = os.path.join(tmp, "s.json"), os.path.join(tmp, "p.json")
        with open(scen, "w") as f:
            json.dump(data, f)
        env = dict(os.environ, PLANNER_BUDGET_S=budget, PLANNER_WORKERS=workers)
        subprocess.run([sys.executable, PLANNER, scen, out], env=env, check=True, stdout=subprocess.DEVNULL)
        with open(out) as f:
            return json.load(f)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", nargs="+", default=["L2", "L3"])
    ap.add_argument("--seeds", default="0-3")
    ap.add_argument("--draws", type=int, default=30)
    ap.add_argument("--cut", type=float, default=0.25, help="cut time as a share of the horizon")
    ap.add_argument("--slows", type=float, nargs="+", default=[0.05, 0.1, 0.3])
    ap.add_argument("--budget", default="8", help="planner budget in seconds")
    ap.add_argument("--workers", default="2")
    ap.add_argument("--out", default=os.path.join(KIT, "linkloss", "results"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    plans: Dict[tuple, dict] = {}
    scenarios: Dict[tuple, Scenario] = {}
    rob = defaultdict(list)      # (margin, slow, policy) -> rows
    siz = defaultdict(list)      # (margin, slow, range, msgs, loss) -> rows
    for lv in args.levels:
        for seed in parse_seeds(args.seeds):
            data = generate(lv, seed)
            scn = Scenario.from_dict(data)
            for margin in LEVELS:
                plan = make_plan(harden(data, margin), args.budget, args.workers)
                res = evaluate(scn, plan)
                if not res.valid:
                    sys.exit("hardened plan invalid on the real scenario: %s %d margin %d" % (lv, seed, margin))
                plans[(lv, seed, margin)] = plan
                scenarios[(lv, seed)] = scn
                for slow in args.slows:
                    dist = Disturbance(t_cut=args.cut * scn.horizon_s, max_slow=slow)
                    for policy, comms in (("continue", Comms()), ("adjust", Comms(range_m=1000.0, max_msgs=3)),
                                          ("return", Comms())):
                        tot, uns, msgs = 0.0, 0, 0.0
                        for d in range(args.draws):
                            r = simulate(scn, plan, dist, comms, policy, d)
                            # score of the whole mission: plan score minus what the drift cost after the cut
                            tot += res.score - (r.ceiling - r.served) - r.cost * r.msgs
                            uns += r.violations > 0
                            msgs += r.msgs
                        rob[(margin, slow, policy)].append((res.score, tot / args.draws, uns / args.draws,
                                                            msgs / args.draws))
                    if margin == 0 or margin == 2:
                        for rng_m in (0.0, 100.0, 300.0, 1000.0, 3000.0):
                            for m_cap in (1, 3):
                                for loss in (0.0, 0.3):
                                    comms = Comms(range_m=rng_m, max_msgs=m_cap, loss_prob=loss)
                                    tot = 0.0
                                    for d in range(args.draws):
                                        r = simulate(scn, plan, dist, comms, "adjust", d)
                                        tot += res.score - (r.ceiling - r.served) - r.cost * r.msgs
                                    siz[(margin, slow, rng_m, m_cap, loss)].append((res.score, tot / args.draws))
            print("done", lv, seed, flush=True)

    with open(os.path.join(args.out, "robustness.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["margin", "slow", "policy", "plan_score", "expected_score", "unsafe_rate", "msgs"])
        for (margin, slow, policy), rows in sorted(rob.items()):
            n = len(rows)
            w.writerow([margin, slow, policy] + ["%.2f" % (sum(r[i] for r in rows) / n) for i in range(4)])
    with open(os.path.join(args.out, "sizing.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["margin", "slow", "range_m", "max_msgs", "loss", "plan_score", "expected_score"])
        for (margin, slow, rng_m, m_cap, loss), rows in sorted(siz.items()):
            n = len(rows)
            w.writerow([margin, slow, rng_m, m_cap, loss] + ["%.2f" % (sum(r[i] for r in rows) / n) for i in range(2)])
    print("written", args.out)


if __name__ == "__main__":
    main()

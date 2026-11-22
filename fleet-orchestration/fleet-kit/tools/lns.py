"""Offline large-neighbourhood search over the contact order, for board plans (not the hand-in).

The hand-in builder serves every hostile before any unknown contact, so the scouts are often spent before
the unknowns get a turn. Here one order holds both classes, and a search moves contacts around in it:
unserved contacts are pulled forward, pairs swapped, the order perturbed. Every candidate is rebuilt with
the hand-in's own builder (valid by construction) and scored with the official scorer.

Usage, from fleet-kit/:
    python3 tools/lns.py SCENARIO.json OUT_PLAN.json --minutes 20 --chains 4 [--start PLAN.json]
The best plan is written to OUT_PLAN.json each time it improves (atomically).
"""
import argparse
import json
import math
import multiprocessing as mp
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "handin"))
import planner as P  # noqa: E402  (hand-in builder, routers and vendored scorer)
from fk.model import HOSTILE, UNKNOWN  # noqa: E402

FAR = 1e18  # no deadline inside a build


def build_order(scenario, order, far):
    """One greedy construction serving the contacts in `order` (ids), both classes mixed."""
    planner = P.RoutedPlanner(scenario, FAR, P.N_SCOUTS)
    planner.far = far
    by_id = scenario.contact_by_id()
    for cid in order:
        c = by_id[cid]
        try:
            if c.cls == HOSTILE:
                planner.serve_hostile(c)
            else:
                planner.serve_unknown(c)
        except Exception:  # a contact that breaks the routing is skipped, as in the hand-in
            continue
    plan = planner._plan({})
    res = P.evaluate(scenario, plan)
    return (res.score if res.valid else -1.0), plan, set(res.served or []) if res.valid else set()


def default_order(scenario):
    key = P._key(scenario, 1.0, {})
    hostiles = sorted((c for c in scenario.contacts if c.cls == HOSTILE), key=key)
    unknowns = sorted((c for c in scenario.contacts if c.cls == UNKNOWN), key=lambda c: -c.points)
    return [c.id for c in hostiles + unknowns]


def mutate(order, served, rng):
    o = list(order)
    unserved = [i for i, c in enumerate(o) if c not in served]
    move = rng.random()
    if unserved and move < 0.5:  # pull one or two unserved contacts forward
        for _ in range(1 if rng.random() < 0.7 else 2):
            unserved = [i for i, c in enumerate(o) if c not in served]
            if not unserved:
                break
            i = rng.choice(unserved)
            c = o.pop(i)
            o.insert(rng.randrange(0, max(1, i)), c)
    elif move < 0.8:  # swap two
        i, j = rng.randrange(len(o)), rng.randrange(len(o))
        o[i], o[j] = o[j], o[i]
    else:  # move a block
        i = rng.randrange(len(o))
        k = rng.randint(2, 5)
        blk = o[i:i + k]
        del o[i:i + k]
        o[rng.randrange(0, len(o) + 1):0] = blk
    return o


def chain(args):
    scen_path, out_dir, idx, seconds, start_order, far = args
    data = json.load(open(scen_path))
    scenario = P.Scenario.from_dict(data) if hasattr(P.Scenario, "from_dict") else P.parse_scenario(data)
    rng = random.Random(7919 * idx + 17)
    order = list(start_order)
    best_s, best_plan, served = build_order(scenario, order, far)
    cur_s, cur_order, cur_served = best_s, order, served
    t_end = time.monotonic() + seconds
    temp0, n, n_acc = 6.0, 0, 0
    while time.monotonic() < t_end:
        frac = 1.0 - (t_end - time.monotonic()) / seconds
        temp = temp0 * (1.0 - frac) + 0.05
        cand = mutate(cur_order, cur_served, rng)
        s, plan, sv = build_order(scenario, cand, far)
        n += 1
        if s >= cur_s or (s > 0 and rng.random() < math.exp((s - cur_s) / temp)):
            cur_s, cur_order, cur_served = s, cand, sv
            n_acc += 1
        if s > best_s:
            best_s, best_plan = s, plan
            tmp = os.path.join(out_dir, f"chain{idx}.json.tmp")
            json.dump({"score": s, "order": cand, "plan": plan}, open(tmp, "w"))
            os.replace(tmp, os.path.join(out_dir, f"chain{idx}.json"))
            print(f"chain {idx}: {s:.1f} after {n} builds", flush=True)
    return best_s, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("out")
    ap.add_argument("--minutes", type=float, default=20.0)
    ap.add_argument("--chains", type=int, default=4)
    a = ap.parse_args()
    data = json.load(open(a.scenario))
    scenario = P.Scenario.from_dict(data) if hasattr(P.Scenario, "from_dict") else P.parse_scenario(data)
    out_dir = a.out + ".chains"
    os.makedirs(out_dir, exist_ok=True)
    start = default_order(scenario)
    t0 = time.monotonic()
    s0, plan0, _ = build_order(scenario, start, True)
    print(f"start order: {s0:.1f} in {time.monotonic() - t0:.1f} s per build", flush=True)
    jobs = [(a.scenario, out_dir, i, a.minutes * 60, start, i % 2 == 0) for i in range(a.chains)]
    with mp.get_context("fork").Pool(a.chains) as pool:
        res = pool.map(chain, jobs)
    best = max((json.load(open(os.path.join(out_dir, f))) for f in os.listdir(out_dir) if f.endswith(".json")),
               key=lambda d: d["score"], default=None)
    if best is None or best["score"] < s0:
        best = {"score": s0, "plan": plan0}
    json.dump(best["plan"], open(a.out, "w"))
    print(f"best {best['score']:.1f}; builds per chain {[n for _, n in res]}", flush=True)


if __name__ == "__main__":
    main()

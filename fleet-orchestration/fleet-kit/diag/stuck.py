"""Link-loss: which aircraft end the run frozen in a hold, and who is near them when the hold starts.

Same case as check_policy (kit greedy plan, events seed = seed + 1, 1000x200, run seeds 0-1).
    python3 diag/stuck.py . handin/policy.py L2 21
"""
import sys
K, pol = sys.argv[1], sys.argv[2]
sys.path.insert(0, K)
from fleetkit.generator import generate
from fleetkit.model import Scenario
from fleetkit.baseline import greedy_plan
from fleetkit.linkloss.events import make_events
from fleetkit.linkloss.policies import load_policy
from fleetkit.linkloss.sim import simulate
from fleetkit.linkloss.score import oracle_points
from fleetkit.geometry import dist3
level, seed = sys.argv[3], int(sys.argv[4])
sc = Scenario.from_dict(generate(level, seed)); plan = greedy_plan(sc); ev = make_events(sc, plan, seed + 1)
v = oracle_points(sc, plan, ev)
print("events", [(e["kind"], e.get("aircraft") or e.get("contact"), e["t"]) for e in ev["events"]], "t_loss", ev["t_loss"])
for rs in (0, 1):
    tr = {}
    r = simulate(sc, plan, ev, load_policy(pol), setting=(1000.0, 200.0), run_seed=rs, trace=tr)
    print(f"run {rs}: retention {min(1, r.points / v):.3f} points {r.points}/{v} served {r.served} failed {r.failed[:1]}")
    if rs: continue
    rates = tr["rates"]; last_t = rates[-1][0]
    def pos(aid, t):
        for (t0, t1, p0, p1) in r.crafts[aid].pieces:
            if t0 - 1e-9 <= t <= t1 + 1e-9:
                f = 0 if t1 == t0 else (t - t0) / (t1 - t0); return tuple(p0[i] + f * (p1[i] - p0[i]) for i in range(3))
        return None
    for aid, c in sorted(r.crafts.items()):
        if c.end_kind in ("engaged", "landed"): continue
        # start of the final run of rate 0
        t0 = None
        for t, rr in rates:
            x = rr.get(aid)
            if x == 0.0:
                t0 = t if t0 is None else t0
            elif x is not None:
                t0 = None
        if t0 is None: continue
        wp = c.route.waypoints[-1]
        tgt = wp.target if wp.action == "engage" else "-"
        rate_hist = [rr.get(aid) for t, rr in rates]
        aborted = any(x is not None and x < 0 for x in rate_hist)
        p = pos(aid, t0)
        near = []
        for b, cb in r.crafts.items():
            if b == aid: continue
            q = pos(b, t0)
            if q and p and dist3(p, q) < 120:
                rb = [rr.get(b) for t, rr in rates if abs(t - t0) < 0.6]
                near.append(f"{b}@{dist3(p, q):.0f}m rate={rb[0] if rb else None} end={cb.end_kind}")
        print(f"  {aid} tgt={tgt} end={c.end_kind or 'flying'} final hold from t={t0:.0f} to {last_t:.0f} ever_returned={aborted}  near: {near}")

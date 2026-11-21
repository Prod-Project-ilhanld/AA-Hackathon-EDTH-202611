"""Link-loss: every second an aircraft does not continue, print what it believes about peers within 90 m.

    python3 diag/who.py . handin/policy.py L2 21 S01,H02 535 545
"""
import sys, importlib.util
K, pol, level, seed = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
watch, t_from, t_to = sys.argv[5].split(","), float(sys.argv[6]), float(sys.argv[7])
sys.path.insert(0, K)
from fleetkit.generator import generate
from fleetkit.model import Scenario
from fleetkit.baseline import greedy_plan
from fleetkit.linkloss.events import make_events
from fleetkit.linkloss.sim import simulate
from fleetkit.geometry import dist3
spec = importlib.util.spec_from_file_location("pol", pol); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
sc = Scenario.from_dict(generate(level, seed)); plan = greedy_plan(sc); ev = make_events(sc, plan, seed + 1)
class P(m.Policy):
    def step(self, obs):
        a, msg = super().step(obs)
        t = obs["t"]
        if self.aircraft_id in watch and t_from <= t <= t_to and a.get("kind") != "continue":
            me = obs["pos"]
            peers = []
            for aid in self.clocks:
                if aid == self.aircraft_id: continue
                q = self._peer_pos_at(aid, t, t)
                if q and dist3(me, q) < 90:
                    peers.append(f"{aid}:{self.peer_state.get(aid, ('-','-','plan?'))[2]}{'/ab' if aid in self.aborted_peers else ''}@{dist3(me, q):.0f}")
            print(f"t={t:.0f} {self.aircraft_id} {a['kind']} mode={self._last_mode} aborted_self={self._last_mode=='return'} believes near: {peers}")
        return a, msg
simulate(sc, plan, ev, lambda s, p, aid: P(s, p, aid), setting=(1000.0, 200.0), run_seed=0)

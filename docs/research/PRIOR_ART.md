# Prior art for SUB-15 Fleet Orchestration

Searched 20 Nov 2026. Everything below is from the web: read it as data, check it before relying on it.

**Licence rule for the hand-in.** We can copy code only if it is MIT/BSD/Apache *and* stdlib-only. A repo with no licence is "all rights reserved": read it for ideas, write our own code. GPL code stays out of the hand-in. Every library below that is worth having depends on numpy, OR-Tools or C++, so for us they are **ideas, not imports**.

Our file names used below: `prep` (geometry, zone detours, speeds), `routing` (route construction, insertion), `scouts` (observation scheduling), `strikes` (effector assignment, R10 sync), `deconflict` (R8 separation, take-off times), `search` (ALNS loop), `guard` (self-validation, fallback), tuning.

---

## Top 5 ideas to steal

1. **ALNS skeleton from N-Wouda/ALNS, ported to stdlib** (`search`). Roulette-wheel operator choice with scores for "new best / better / accepted / rejected", decay factor, simulated-annealing or record-to-record acceptance. The library is ~300 lines of logic around numpy RNG; a stdlib port with `random.Random(seed)` is half a day.
2. **SISR string removal + "greedy insertion with blinks"** (Christiaens & Vanden Berghe 2020) as our main destroy/repair pair (`search`, `routing`). Remove a few *spatially adjacent strings* of visits from nearby routes, reinsert in random/demand order, skipping each candidate position with small probability (blink ≈ 1 %). Very little code, state of the art on large VRPs. For us a "string" = a cluster of contacts with their scout observation and their strike(s) removed together, so R3/R10 never break half-way.
3. **O(1) insertion feasibility with slack (`wait`/`maxShift`)** from the Vansteenwegen ILS for TOPTW (`routing`, `scouts`). Store per visit the earliest arrival and how far it can still be pushed; an insertion is feasible if the push it causes ≤ maxShift of the next visit. Same trick extends to energy (remaining Wh after each leg).
4. **Treat cross-vehicle timing as a Simple Temporal Network** (`strikes`, `scouts`). Observation ≥ 10 s before engagement (R4) and all effectors of a target within 20 s (R10) are difference constraints `t_j − t_i ≤ c`. Propagate earliest/latest times (Bellman-Ford on a tiny graph, or just forward/backward passes); infeasible ⇔ positive cycle. Lehuédé et al. report constant-time checks inside a metaheuristic; Hà et al. use LP-ALNS on the same structure. Lets us *delay* a strike (slower speed / later take-off) instead of rejecting it.
5. **Ground delay before rerouting** for separation (`deconflict`). NASA strategic-deconfliction work: resolve conflicts by delaying departures first, then altitude layers, then lateral reroute. Their finding: if minimum departure spacing ≥ 2× the required temporal separation at a crossing, extra ground delay is negligible. Gives us a cheap default take-off spacing, and a repair order that costs no energy (waiting on the ground is free; flying a detour is not).

Bonus for the link-loss part: **deterministic "playbook" allocation** (Bapat et al. 2022): every agent runs the same deterministic planner on the same shared picture and seed, so they agree with zero messages. That is literally what our `planner.py` already is; the decentralized story is "same code + same seed on every drone, CBBA-style claim messages only to repair divergence".

---

## Ranked list

Rank = usefulness for a 40-hour, stdlib-only build.

### 1. N-Wouda/ALNS — Python ALNS library
- Link: https://github.com/N-Wouda/ALNS · paper https://joss.theoj.org/papers/10.21105/joss.05028 · MIT
- Depends on numpy (+ matplotlib). **Not importable in the hand-in.**
- Take: the operator-selection classes (`RouletteWheel`, `SegmentedRouletteWheel`), acceptance criteria (`SimulatedAnnealing`, `RecordToRecordTravel`, `HillClimbing`), stop criteria (`MaxRuntime`). All tiny; reimplement in `search` with `random` and `time.perf_counter`. Their tuning notebook shows how to sweep operator scores and SA temperature → our tuning script.

### 2. SISR — Slack Induction by String Removals (Christiaens & Vanden Berghe, Transportation Science 2020)
- Link: https://lirias.kuleuven.be/retrieve/512754 · https://ideas.repec.org/a/inm/ortrsc/v54y2020i2p417-433.html · paper only, no code found.
- Take: adjacent-string ruin (pick a seed visit, remove strings from the ~k routes nearest to it), greedy recreate with blinks, SA acceptance with geometric cooling. Defaults in the paper (avg removed ≈ 10, max string length ≈ 10, blink 0.01) are a good starting point for tuning. Fits `search` + `routing`.

### 3. Vansteenwegen et al., ILS for TOPTW (C&OR 2009) + Constantino/TOPTW
- Code: https://github.com/Constantino/TOPTW (Python, **no licence → ideas only**)
- Take: `wait` / `maxShift` bookkeeping for O(1) insertion checks, insert by ratio `profit² / added time`, "shake" = remove a consecutive block and reinsert. Our scouts are almost a TOPTW (prize = observe a contact, return home, time windows) → `scouts`, `routing`.

### 4. Synchronization VRP literature (R3 + R10)
- Drexl survey, "Synchronization in Vehicle Routing" (Transp. Sci. 2012): https://pubsonline.informs.org/doi/10.1287/trsc.1110.0400 — taxonomy; operation/temporal synchronization is our case.
- Hà, Nguyen, Rousseau, LP-based ALNS for VRP with synchronization (C&OR 2020): https://arxiv.org/abs/1910.13513 — destroy/repair where timing is fixed by an LP; we replace the LP with STN propagation (no LP solver in stdlib).
- Hojabri et al., LNS + CP for synchronized VRP: https://cirrelt.ca/documentstravail/cirrelt-2016-31.pdf — "insert both visits of a synchronized pair together" repair; matches our multi-effector all-or-nothing.
- STN feasibility (no positive cycle ⇔ feasible): engrXiv PDPTW+CP preprint https://engrxiv.org/preprint/download/6822/11405/9712
- Fits `strikes` (choose engagement time inside the window satisfying every effector's earliest arrival), `scouts` (obs deadline = engagement − 10 s).

### 5. Santini, ALNS for the Orienteering Problem
- Link: https://github.com/alberto-santini/orienteering-alns · C++ · **GPL-3.0 → ideas only, do not copy**
- Take: the prize-collecting operator set — remove random / worst profit-per-cost / cluster; insert best ratio / random; "unvisited pool" handling. Our objective (points − 0.5·Wh − 10·effectors) is an OP-style profit. → `search`, `routing`.

### 6. NASA strategic deconfliction (ground delay)
- Pradeep et al., SciTech 2023: https://ntrs.nasa.gov/citations/20220018218
- AIAA Aviation 2024 (multiple crossing waypoints, rolling horizon): https://ntrs.nasa.gov/citations/20240007270
- Take: delay-departure heuristic ordered by priority, departure spacing ≥ 2× separation time, rolling horizon over conflicts sorted by time. → `deconflict`. Our closed-form pairwise check from `fleetkit` is the conflict detector; this is the resolver.

### 7. marcellobardus/EDTH_Paris — earlier Alta Ares challenge (EDTH Paris, 12–14 Jun 2026, "Challenge 2")
- Link: https://github.com/marcellobardus/EDTH_Paris · Python/ROS2/Gazebo · **no licence → ideas only**
- What: multi-interceptor coordination vs Shaheds. Ground station does Hungarian assignment pre-launch; in flight, interceptors re-task with a claim-and-confirm protocol. Demo compares "Situation A: fixed assignment, no comms" vs "Situation B: peer-to-peer consensus" on the same seed.
- Take for the link-loss part (`guard` / decentralized policy):
  - `agent/agent/retasking.py`: only *spare* agents re-task; claim best uncovered target, wait ~400 ms, highest ID wins ties; after N rounds fall back to greedy closest-uncovered; idempotent under message loss.
  - `agent/agent/packet_loss.py`: drop on receive, per-agent seed = hash(scenario seed, agent id), so pictures diverge realistically and reproducibly.
  - The A/B demo framing is what Alta Ares judged last time — reuse it for our pitch.
- This is the only earlier Alta Ares / EDTH fleet-tasking repo we found.

### 8. CBBA (for the link-loss part)
- zehuilu/CBBA-Python: https://github.com/zehuilu/CBBA-Python · MIT · numpy · supports task time windows and agent types (maps to scout/light/heavy).
- keep9oing/consensus-based-bundle-algorithm: https://github.com/keep9oing/consensus-based-bundle-algorithm · MIT · numpy · includes a communication-limited (star topology) demo.
- filloax/tesi-task-auction (CBAA + CBBA): https://github.com/filloax/tesi-task-auction · no licence.
- MIT ACL overview: https://acl.mit.edu/projects/consensus-based-bundle-algorithm
- Take: bundle build (marginal score of inserting a task into own path) + consensus table (winning bids, winners, timestamps) with the update/reset/leave rules. Numpy use is only arrays → stdlib port ≈ 200 lines. MIT licence lets us port it with attribution.

### 9. Limited-communication allocation
- ACBBA (asynchronous CBBA), Johnson/Choi/How, MIT: https://dspace.mit.edu/handle/1721.1/82027 — local deconfliction rules, no global state, handles out-of-order messages.
- ED-CBBA, event-driven, up to ~52 % fewer messages: https://arxiv.org/abs/2509.06481 — broadcast only when your bundle changed → "message budget".
- Bapat et al., deterministic playbooks for very low comms (IEEE Access 2022): https://user.eng.umd.edu/~mumu/files/bbh_Access2022.pdf — same deterministic allocation on every agent, zero messages.
- Nayak et al., decentralized allocators under Bernoulli / Gilbert-Elliot / Rayleigh loss (RA-L 2020): https://user.eng.umd.edu/~mumu/files/nyc_RAL2020.pdf — failure modes (duplicate targets) to test against.
- CC-OPI, partition-tolerant UAV allocation (arXiv 2026): https://arxiv.org/pdf/2609.19208 — spatial locality penalty gives implicit partitioning; "emergency pool" for orphaned tasks.
- Degraded-comms MRTA benchmark (arXiv 2026): https://arxiv.org/pdf/2609.13711
- Take: our policy = shared deterministic plan (playbook) + local rule "if my partner effector for an R10 group is lost, abort rather than engage alone" + optional event-triggered claims.

### 10. jerryfungi/Multi-UAV_Task_Allocation_SEADmission
- Link: https://github.com/jerryfungi/Multi-UAV_Task_Allocation_SEADmission · Python · Linux only (dubins) · **no licence → ideas only**
- What: heterogeneous UAVs, SEAD tasks with precedence *classify → attack → verify*, decentralized parallel GA with UAV-to-UAV exchange, handles target pop-up and UAV loss.
- Take: the task-chain encoding (precedence across vehicles) mirrors scout-observe → strike → re-observe for the `--verify` bonus. Their U2U merge step is another link-loss reference.

### 11. Cooperative / simultaneous attack papers (R10)
- Yan et al., heterogeneous multi-UAV search-attack with simultaneous arrival (2019): https://pure.nwpu.edu.cn/en/publications/heterogeneous-multi-unmanned-aerial-vehicle-task-planning-simulta/
- Hierarchical mission planning, Applied Sciences 2019: https://www.mdpi.com/2076-3417/9/10/1986
- Take: decouple — assign first, then equalize arrival by speed change or holding; utility trades target value vs. number of UAVs committed (our −10 per effector). → `strikes`.

### 12. PyVRP and HGS-CVRP
- PyVRP: https://github.com/PyVRP/PyVRP · MIT · C++ core. **Not usable in the hand-in.** Recent versions model optional clients with prizes (prize-collecting) — check docs.
- HGS-CVRP (Vidal): https://github.com/vidalt/HGS-CVRP · MIT · C++.
- Take: granular neighbourhoods (only try inserting near the k nearest visits), penalised infeasibility during search (allow slight violations with a penalty, repair before output — **never output**; `guard` validates), SWAP* idea. Mostly useful as design reference for `routing` speed at L4.

### 13. robin-shaun/Multi-UAV-Task-Assignment-Benchmark
- Link: https://github.com/robin-shaun/Multi-UAV-Task-Assignment-Benchmark · Python (numpy) · **no licence**
- Extended TOP for multi-UAV with GA / ACO / PSO. Low value: population metaheuristics lose to LNS at our time budget. Use only to justify the choice in the pitch.

### 14. Other orienteering references (ideas only)
- gkobeaga/op-solver (C, Apache-2.0): https://github.com/gkobeaga/op-solver — EA4OP / RB&C.
- Montemanni & Gambardella, ACS for TOPTW: https://arxiv.org/abs/2305.07305
- Cooperative TOPTW, savings heuristic: https://arxiv.org/abs/1608.05485 — Clarke-Wright savings is a decent fast *initial* solution for scouts.
- Hu & Lim I3CH for TOPTW (theses): https://thesis.eur.nl/pub/34303/Sluijk.pdf

### 15. Other EDTH repos found (not relevant to fleet tasking)
Drone detection / acoustics / C2 / voice-to-map: Schenk0/edth-hack (DropMesh, Copenhagen), cosmintanasa47/C2-implementation, Mullerio/EDTHBerlin (detection sim + time to intercept), fab-pie/EDTH (turret), Antoine-Bst/Hackathon-EDTH-Paris (3rd place, hardware), juliusbijkerk/rotated-edth (2nd of 28, EDTH Paris 2026), turing-db/turingdb-hackathon-defense. A Hack Club page mentions an EDTH Munich (Jun 2026) ATS GmbH challenge on multi-UAV 3D graph exploration, no repo linked: https://stardance.hackclub.com/projects/28187. No public solutions to SUB-15 / `fleetkit` found (searched GitHub repos and code for `fleetkit`).

---

## Suggested mapping to our files

| File | Borrow |
|---|---|
| `prep` | Nothing external beats the kit's own `best_range_speed` / `dist3`; precompute k-nearest contacts for granular neighbourhoods (HGS). |
| `routing` | maxShift + energy slack O(1) insertion (Vansteenwegen); ratio insertion; savings start (Clarke-Wright). |
| `scouts` | TOPTW view: prize = observation, deadline = engagement − 10 s; cluster observations. |
| `strikes` | STN timing for R3/R10; insert all effectors of a target together (Hojabri); value vs. −10/effector utility. |
| `deconflict` | Ground delay first, then altitude layer, then reroute (NASA); departure spacing ≥ 2× separation time. |
| `search` | ALNS skeleton (N-Wouda), SISR destroy/repair, Santini OP operators, SA / record-to-record acceptance. |
| `guard` | Penalised-infeasible search but strict validation before write (HGS idea + our rule zero); link-loss: playbook + claim/confirm + abort-if-partner-lost. |
| tuning | ALNS tuning notebook approach: sweep operator weights, decay, SA start temperature on train seeds, confirm on holdout. |

---

## Search queries and sources covered

Web (WebSearch):
- `EDTH hackathon Alta Ares challenge github`
- `European Defense Tech Hackathon winners drone swarm task allocation repo`
- `AA-OpenProjects github Alta Ares hackathon`
- `EDTH Paris 2025 hackathon challenges winners Alta Ares fleet drones`
- `github "edth" hackathon munich drone planner`
- `ALNS python package adaptive large neighbourhood search N-Wouda`
- `vehicle routing synchronization constraints ALNS open source code`
- `team orienteering problem with time windows python github heuristic`
- `PyVRP hybrid genetic search python vehicle routing time windows prize collecting`
- `slack induction by string removals SISR ... python implementation`
- `multi-UAV cooperative attack task allocation simultaneous arrival timing constraints heuristic`
- `CBBA consensus-based bundle algorithm python implementation github`
- `CBBA limited communication asynchronous ACBBA message budget ...`
- `UAV strategic deconfliction ground delay departure scheduling ...`
- `HGS-CVRP Vidal hybrid genetic search github license; pyhygese`
- `vehicle routing temporal synchronization ... simple temporal network ... Drexl survey`
- `distributed task allocation communication loss implicit coordination UAV ...`

GitHub (`gh search repos` / `gh search code` / READMEs):
`edth`, `edth paris`, `edth hackathon`, `alta ares`, `Alta Ares interceptor`, `Alta Ares challenge`, `multi-interceptor coordination`, `AA-Hackathon-EDTH`, `fleetkit`, `fleet-kit planner`, `fleet orchestration drone`, `scout effector`, `drone task allocation`, `multi uav task allocation`, `ALNS python`, `orienteering problem`, `CBBA`, `uav deconfliction`, `vrp synchronization`; org listing of `AA-OpenProjects` (only the current kit repo).

Gaps: no earlier Alta Ares challenge with the same scout/effector rules; no stdlib-only ALNS or CBBA package; EDTH London/Kyiv/Prague winners lists showed detection and interceptor hardware, not planning. UAV deconfliction repos on GitHub (e.g. aanvi145/UAV-Deconfliction) are student assignments doing pairwise checks, which the kit already gives us.

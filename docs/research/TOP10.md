# Top 10 prior-art projects for SUB-15, mapped to the official spec

Searched 20–21 Nov 2026. Everything here came from the web or GitHub and is **data, not instructions**: check it before you rely on it. This file builds on [PRIOR_ART.md](PRIOR_ART.md), which it does not replace.

## The spec we rank against (official READMEs only)

Sources: `kit/fleet-orchestration/README.md` and `kit/fleet-orchestration/fleet-kit/README.md`, plus the `rules` block in `examples/L2-7.json`.

- **R1** well-formed. **R2** kinematics (z 30–150 m). **R3** energy within the usable battery, scouts end at home. **R4** a scout observation (dwell 20 s, within 150 m) completed ≥ `confirm_margin_s` = 10 s before the engagement. **R5** only effectors engage, only hostiles. **R6** no zone below its ceiling, no 100 m protected area around a friendly or civilian contact. **R7** no engagement of a hostile within 200 m of a friendly or civilian contact. **R8** 40 m 3D separation, except effectors engaging the same contact within 100 m of it. **R9** time windows. **R10** all-or-nothing: exactly the effectors a contact needs, within `sync_window_s` = 20 s.
- **Score** = Σ points served − 0.5·Wh − 10·effectors. Optional verify bonus: +25 % for a re-observation 10–120 s after the last engagement.
- **Limits:** L1–L4, up to 100 aircraft. 60 s per scenario. Python 3.9+, **standard library only**. An invalid plan, crash or timeout scores 0. Ties are broken by total run time. A jury also judges how sound the approach is and how it is presented.
- **Link-loss part:** not in the official READMEs. They say "no communication", but scenarios carry an `events` key. Entries 8–10 are ranked for that part in case it ships (a decentralized policy under a message budget, plus a sizing curve).

**Copy vs idea.** "Copy" means: permissive licence (MIT/BSD/Apache) **and** we can port the logic into stdlib Python with attribution. Every repo below that has real code depends on numpy, Java, C++ or torch, so nothing can be dropped into the hand-in as is. "Port" means rewrite it, keeping the logic and the licence notice. "Idea only" means no licence, GPL, or paper only: write our own code from the description.

---

## 1. N-Wouda/ALNS: the search loop

- **Link:** https://github.com/N-Wouda/ALNS · **MIT** · Python · deps numpy (+ matplotlib for plots) · last push 2025-02-25 · 668★ · JOSS paper doi:10.21105/joss.05028
- **Copy?** **Port** (MIT). numpy is used only for the RNG, weight arrays and `np.exp`; `random.Random` and `math.exp` replace it one for one.
- **Helps with:** the whole score (points − 0.5·Wh − 10·eff) and the **60 s limit**. It is the frame that every other operator plugs into.
- **Mechanism to take:**
  - `alns/ALNS.py` → `ALNS.iterate(state, op_select, accept, stop)`: each iteration picks a destroy and a repair operator, evaluates the candidate (`_eval_cand`) and sorts the outcome into **best / better / accepted / rejected** (`_determine_outcome`).
  - `alns/select/RouletteWheel.py`: operator weight `w ← decay·w + (1−decay)·score[outcome]`. The docs' examples use `scores=[25, 5, 1, 0]` and `decay=0.8` (check in their notebooks). `SegmentedRouletteWheel` updates the weights every `seg_length` iterations.
  - `alns/accept/SimulatedAnnealing.py` → `autofit(init_obj, worse, accept_prob, num_iters)`: sets the start temperature so that a solution `worse`·100 % worse is accepted with probability `accept_prob`. Also `RecordToRecordTravel`, `LateAcceptanceHillClimbing`.
  - `alns/stop/MaxRuntime.py`.
- **How we'd adapt it:** about 120 lines in `search.py`. The state is our plan plus a pool of unserved contacts; the objective is the official score. Stop at about 50 s wall time, so validation and writing still fit in 60 s. Seed the RNG from the scenario seed so runs are reproducible.
- **Effort:** 3 h.
- **Risks:** none in the code itself. The gain depends entirely on the operators (entries 2–6) and on how fast we evaluate a candidate. At L4, the full `fleetkit` validator is too slow to call on every iteration.

## 2. graphhopper/jsprit (+ SISR): the operator set and its defaults

- **Link:** https://github.com/graphhopper/jsprit · **Apache-2.0** · Java 21 · no runtime deps that matter to us · last push 2026-11-19 · 1.8k★. Paper behind `RuinString`: Christiaens & Vanden Berghe, "Slack Induction by String Removals", *Transp. Sci.* 2020 (https://lirias.kuleuven.be/retrieve/512754).
- **Copy?** **Port** (Apache-2.0 allows a translation with a NOTICE). In practice we re-implement 4–5 operators.
- **Helps with:** **points served**. Like our problem, jsprit leaves jobs unassigned, so it is prize-collecting by construction. Also **energy** (relocating visits) and **R9** (its regret scorer is time-window aware).
- **Mechanism to take** (file names under `jsprit-core/src/main/java/com/graphhopper/jsprit/core/algorithm/`):
  - Ruin: `ruin/RuinRadial.java` (remove a seed job and its nearest neighbours), `ruin/RuinRandom.java`, `ruin/RuinWorst.java` (remove the jobs with the highest removal saving), `ruin/RuinString.java` + `StringUtil.java` (SISR: strings from k nearby routes), `ruin/RuinKruskalClusters.java`.
  - Recreate: `recreate/RegretInsertion.java` and `RegretInsertionFast.java` (regret-k), `recreate/BestInsertion.java`.
  - Defaults in `box/Jsprit.java`: strategy weights `radial_regret .5`, `random_best .5`, `random_regret .5`, `worst_regret 1`, `cluster_regret 1` (string strategies 0 by default). `string_kmin 1`, `string_kmax 6`, `string_lmin 10`, `string_lmax 30`. `regret.distance_scorer .05`, `regret.tw_scorer -.1`, `iterations 2000`. Acceptance is a Schrimpf threshold (`threshold.ini`, `threshold.alpha`).
- **How we'd adapt it:** one "job" = one contact bundle (observation + n_light + n_heavy engagements, see entry 4). The ruin operators remove whole bundles. Regret-2 insertion inserts the bundle with the largest gap between its best and second-best placement first, scored as Δpoints − 0.5·ΔWh − 10·Δeff. Add a "drop" outcome so that unprofitable contacts stay in the pool.
- **Effort:** 6 h for radial + random + worst + string ruin and greedy + regret-2 insertion.
- **Risks:** jsprit's insertion assumes one vehicle per job. Our bundles span 2–4 aircraft, so regret has to be computed per bundle, not per visit, which costs more at L4. Keep k-nearest filters (`regret.spatial_filter_k`).

## 3. Vansteenwegen et al., ILS for the team orienteering problem with time windows (TOPTW) + Constantino/TOPTW: fast insertion checks

- **Link:** paper: Vansteenwegen, Souffriau, Vanden Berghe, Van Oudheusden, *C&OR* 36(12), 2009. Code: https://github.com/Constantino/TOPTW · **no licence** · Python · last push 2016-05-30.
- **Copy?** **Idea only** (no licence). The method is simple enough to write from the paper.
- **Helps with:** **R9** (time windows), **R3** (energy) and **points served by scouts**. Scouts are a TOPTW: visit for a prize, respect windows, return home. Speed at L4.
- **Mechanism to take:** keep `arrive`, `start`, `wait` and `maxShift` per visit, where `maxShift_i = min(close_i − start_i, wait_{i+1} + maxShift_{i+1})`. Inserting j between i and k costs `shift_j = travel(i,j) + wait_j + dwell_j + travel(j,k) − travel(i,k)`, which is feasible iff `shift_j ≤ wait_k + maxShift_k`. That is an **O(1)** check. Insert by the ratio `profit² / shift`. "Shake" removes a block of `S` consecutive visits per route; S grows each round and resets when the solution improves.
- **How we'd adapt it:** add the same backward slack for energy: `eSlack_i` = Wh still available after visit i. A scout insertion is then O(1) for R9 + R3 + the return home. Use dwell 20 s at an observation point within `R_obs_m` = 150 m (not at the contact itself), which also lets a scout skip zone detours.
- **Effort:** 3 h.
- **Risks:** the 3D zone detours (R6) make the distance from i to j non-Euclidean. Cache detour lengths per contact pair in `prep`. The cache costs about 90²·2 shortest paths at L4, which is fine.

## 4. Synchronized VRP literature: precedence and sync as a simple temporal network (STN)

- **Links:** Drexl, "Synchronization in Vehicle Routing" survey, *Transp. Sci.* 46(3) 2012 (https://pubsonline.informs.org/doi/10.1287/trsc.1110.0400). Hà, Nguyen, Rousseau, LP-based ALNS for VRP with synchronization, *C&OR* 2020 (https://arxiv.org/abs/1910.13513). Hojabri et al., LNS + CP for synchronized VRP (https://cirrelt.ca/documentstravail/cirrelt-2016-31.pdf). STN feasibility ⇔ no positive cycle (https://engrxiv.org/preprint/download/6822/11405/9712). Constant-time synchronization checks: Lehuédé et al., Odysseus 2015.
- **Copy?** **Idea only** (papers; no public code found).
- **Helps with:** **R4** (observation done ≥ 10 s before the engagement), **R10** (all needed effectors within 20 s), **R9**. These are the two cross-vehicle rules that greedy plans give up on.
- **Mechanism to take:** every timed event is a node. Constraints are differences, `t_b − t_a ≥ c`:
  - R4: `t_engage_e − (t_obs_start + 20) ≥ 10` for each effector e.
  - R10: `|t_engage_e − t_engage_f| ≤ 20` for every effector pair of the contact.
  - Each vehicle's own route gives earliest and latest times (entry 3).
  - Propagate earliest and latest times (forward and backward passes, or Bellman-Ford on the small graph of one bundle); infeasible ⇔ a positive cycle.
  - From Hojabri: **insert all of a contact's visits together, or none**. Hà et al. fix the times with an LP after each repair; we replace the LP with propagation.
- **How we'd adapt it:** in `strikes.py`, a bundle's insertion picks a common engagement time T in [max(earliest arrivals, obs end + 10), min(window close, latest arrivals)] and checks that the effectors' T values span ≤ 20 s. Effectors that arrive early burn **take-off delay**, not hover energy. A delay on one vehicle changes others only through bundles, so re-propagate just the bundles touched.
- **Effort:** 5 h.
- **Risks:** the network gets coupled when one scout confirms several contacts that are struck by different effector groups. A delay ripples along the scout route and can break other bundles. Bound the ripple: reject an insertion if it would push more than about 3 bundles.

## 5. vidalt/HGS-CVRP and PyVRP: speed tricks, penalized infeasibility, prize-collecting

- **Links:** https://github.com/vidalt/HGS-CVRP · **MIT** · C++ · last push 2025-03-26. https://github.com/PyVRP/PyVRP · **MIT** · Python + C++ core · last push 2026-11-19 · ranked 1st in the DIMACS 2021–22 VRPTW track (its earlier versions, per the PyVRP paper https://arxiv.org/abs/2403.13795) · built on the HGS baseline of EURO Meets NeurIPS 2022 (OptiML: https://github.com/N-Wouda/Euro-NeurIPS-2022, 1st on the static track).
- **Copy?** **Idea only** in practice: C++ core, and PyVRP can't be imported in the hand-in.
- **Helps with:** the **60 s limit at L4** (100 aircraft, 90 contacts), **energy**, and **points served** (PyVRP models optional clients with prizes; check the current docs).
- **Mechanism to take:**
  - **Granular neighbourhoods:** only try moves or insertions next to the Γ nearest visits (HGS default Γ = 20, `nbGranular` in `Params.h`).
  - **Penalized infeasibility:** during search, accept time-window and energy violations at a penalty that adapts towards a target feasible share (`targetFeasible` ≈ 0.2, penalty × 1.2 or × 0.85 every 100 iterations). Never output such a plan.
  - **SWAP\*** (`LocalSearch.cpp`): swap two visits between routes, each reinserted at its best position, not in place.
  - **Concatenation data** for O(1) route evaluation (time-window data per subsequence).
- **How we'd adapt it:** precompute the 20 nearest contacts per contact in `prep`. Restrict SISR/radial ruin and insertion to them. Allow a soft penalty on the R9/R3 slack during ALNS, and keep a separate "best feasible" solution that `guard` validates with `fleetkit` before writing.
- **Effort:** 2 h for granular lists. 4 h for the penalty scheme (optional).
- **Risks:** the penalty scheme adds tuning. R8 and R10 can't be soft-penalized cheaply. Keep those hard.

## 6. NASA strategic deconfliction (ground delay) + eartser/sipp-mapf: separation

- **Links:** Pradeep et al., SciTech 2023 (https://ntrs.nasa.gov/citations/20220018218). NASA, AIAA Aviation 2024, multiple crossing waypoints and rolling horizon (https://ntrs.nasa.gov/citations/20240007270). Safe-interval path planning (SIPP) for multi-agent paths: https://github.com/eartser/sipp-mapf · **no licence** · Python · last push 2021-12-23. Also https://github.com/PathPlanning/SIPP-IP (MIT, C++).
- **Copy?** **Idea only.**
- **Helps with:** **R8** (40 m 3D, effectors on the same contact exempt within 100 m) at **zero energy cost**, plus **R2**.
- **Mechanism to take:**
  - NASA: resolve conflicts by **delaying departures first**. Process conflicts in time order (rolling horizon) and delay the lower-priority flight. Rule of thumb from their study: departure spacing ≥ 2× the minimum temporal separation at a crossing makes extra delay negligible.
  - SIPP: each vehicle plans inside "safe intervals" in time, not just in space. Here that means choosing a take-off time from the intervals in which the vehicle's straight legs stay clear of the routes already fixed.
- **How we'd adapt it:** in `deconflict.py`:
  1. Give each aircraft its own cruise altitude layer (about 30 m apart, inside 30–150 m). This alone removes most crossings where the slots allow.
  2. For the remaining pairs, use the kit's closed-form 3D distance check per leg pair.
  3. If they conflict, delay the later take-off by the smallest Δt that clears every pair (scan candidate Δt values from the leg-pair intervals).
  4. If R9/R10 forbid the delay, give the bundle back to ALNS as infeasible.
- **Effort:** 4 h.
- **Risks:** a delay changes the R10 sync and the R9 windows downstream, so it couples with entry 4. Climbing between layers costs energy (`e_climb_wh_per_m` ≈ 0.027 Wh/m for a scout, small). The 40 m rule also applies during climb-out from shared bases, so no two aircraft share a home (each has its own pad, 11.1 m apart at L4); the constraint is neighbouring pads, handled by the roadmap's earliest-free scheduler.

## 7. alberto-santini/orienteering-alns: profit-aware destroy and repair

- **Link:** https://github.com/alberto-santini/orienteering-alns · **GPL-3.0** · C++ (needs CPLEX/Concorde for parts) · last push 2023-02-24. Paper: Santini, *ESWA* 123 (2019).
- **Copy?** **Idea only** (GPL; keep it out of the hand-in).
- **Helps with:** the **score trade-off** itself: serve a contact only if points > 0.5·ΔWh + 10·Δeff. Unknown contacts (observe only) and cheap single-effector hostiles are pure orienteering decisions.
- **Mechanism to take:** OP-specific destroy operators: remove random, remove **lowest profit / cost ratio**, remove a **cluster** of nearby visits. Repair operators: insert by best ratio, insert by highest prize, random. Keep a pool of unvisited targets that every repair reads from. The paper also adds periodic "local branching" on the visited set, which we skip.
- **How we'd adapt it:** add "worst-ratio removal" (ratio = points / (0.5·marginal Wh + 10·effectors)) and "best-ratio insertion" to entry 2's set. Let ALNS learn their weights. This is the piece that makes the planner **drop** low-value hostiles that need 3 heavy effectors (−30 points before energy).
- **Effort:** 2 h on top of entry 2.
- **Risks:** with the GPL licence, write from the paper and don't read the code while writing. The single-vehicle OP has no sync, so ratio scores need the bundle cost from entry 4.

## 8. zehuilu/CBBA-Python + keep9oing/consensus-based-bundle-algorithm: decentralized allocation (link-loss part)

- **Links:** https://github.com/zehuilu/CBBA-Python · **MIT** · Python · deps numpy + matplotlib · last push 2021-04-22 · 132★. https://github.com/keep9oing/consensus-based-bundle-algorithm · **MIT** · Python · numpy · last push 2022-11-25 · 394-line `CBBA.py`. Background: Choi, Brunet, How, *IEEE T-RO* 2009. Low-comm variants: ACBBA (https://dspace.mit.edu/handle/1721.1/82027), ED-CBBA (https://arxiv.org/abs/2509.06481, up to ~52 % fewer messages).
- **Copy?** **Port** (MIT). numpy is only used for 2D arrays; nested lists work.
- **Helps with:** the possible **link-loss part**: a decentralized policy, message budget, sizing curve. Indirectly R5 and R10 (agent types map to scout / light / heavy).
- **Mechanism to take:**
  - zehuilu `lib/CBBA.py`: `bundle_add` (greedy marginal-score insertion into the agent's own path), `bundle_remove`, `compute_bid`, `scoring_compute_score` (time-window aware), `communicate` (the 3×3 update / reset / leave table on winning bids, winners and timestamps).
  - keep9oing `CBBA.py`: `build_bundle`, `update_task`, `__update`, `__reset`, `__leave`, and a **star-topology limited-comms** demo.
  - ED-CBBA: broadcast only when your bundle changed. That gives a natural **message budget**.
- **How we'd adapt it:** about 200 lines, in a separate module from the hand-in planner. Each drone runs CBBA from the shared plan. Effector bids for an R10 contact count only once the full set is claimed; otherwise everyone releases it. Sizing curve: run it with message caps of {0, 1, 2, 5, ∞} per agent per round and plot score vs. budget.
- **Effort:** 6 h.
- **Risks:** classic CBBA has no multi-agent (sync) tasks. Our all-or-nothing R10 needs coalition bidding, which breaks CBBA's convergence guarantees. And the link-loss part may never ship (the official READMEs say "no communication").

## 9. marcellobardus/EDTH_Paris: Alta Ares' previous EDTH challenge

- **Link:** https://github.com/marcellobardus/EDTH_Paris · **no licence** · Python (ROS2/Gazebo/Docker) · last push 2026-06-14 · "EDTH Paris Hackathon — Challenge 2 (Alta Ares)", 12–14 June 2026.
- **Copy?** **Idea only.**
- **Helps with:** the **link-loss part** and the **jury / presentation** criterion. It is the only earlier Alta Ares fleet-tasking entry we found. No planning rules overlap with R1–R10.
- **Mechanism to take:**
  - `agent/agent/retasking.py`: claim-and-confirm. Only **spare** agents re-task. They claim the best uncovered target, wait about 400 ms, and the highest ID wins ties. After N rounds they fall back to greedy closest-uncovered. Idempotent under message loss.
  - `agent/agent/packet_loss.py`: drop on receive, per-agent seed `sha256(f"{seed}:{agent_id}")`, so loss is reproducible and uncorrelated across agents.
  - Pitch framing: "Situation A, fixed plan with no comms" vs "Situation B, peer consensus" on the same seed.
  - `gs/gs/optimizer.py`: Hungarian assignment before launch.
- **How we'd adapt it:** reuse the A/B framing for our demo: our central plan vs. a decentralized policy under loss, on the same `fleetkit` seeds, scored by the official scorer. Reuse the hashed per-agent seed for a reproducible loss model.
- **Effort:** 2 h (framing + loss model). Re-tasking logic is part of entry 8.
- **Risks:** it is a different problem (interceptors vs. Shaheds, real-time). The jury may know it. Use it for framing, not as a claim of novelty.

## 10. jerryfungi/Multi-UAV_Task_Allocation_SEADmission: precedence across heterogeneous UAVs

- **Link:** https://github.com/jerryfungi/Multi-UAV_Task_Allocation_SEADmission · **no licence** · Python (Linux only, `dubins` package) · last push 2024-05-13 · 109★.
- **Copy?** **Idea only.**
- **Helps with:** **R4** (observe before engage) and the **verify bonus** (+25 %, re-observe 10–120 s after the last engagement). SEAD tasks are *classify → attack → verify*, which is our *observe → engage → re-observe*. Also the link-loss part: a decentralized parallel GA with UAV-to-UAV exchange that handles UAV loss and pop-up targets.
- **Mechanism to take:** the chromosome encodes (target, task type, UAV) triples, and a decode step enforces the order of task types per target across UAVs. Infeasible orders are repaired by pushing later tasks back in time. Merging each UAV's best solution periodically is a simple consensus step.
- **How we'd adapt it:** treat verify as an optional fourth visit in a bundle: a scout observation in [T_last_eng + 10, T_last_eng + 120] inside the window. Insert it only when 0.25·points > its marginal energy·0.5. Put it behind a flag, because it has its own board and doesn't change the ranking.
- **Effort:** 2 h (the verify insertion only; skip the GA).
- **Risks:** a GA is too slow at L4 in pure Python and is beaten by LNS anyway. Take only the precedence encoding. The verify bonus doesn't count for the main ranking.

---

## Summary table

| # | Project | Rules / score terms helped | Copy vs idea | Effort | Expected impact |
|---|---|---|---|---|---|
| 1 | N-Wouda/ALNS | whole score, 60 s | Port (MIT) | 3 h | High: the frame everything plugs into |
| 2 | jsprit + SISR | points served, energy, R9 | Port (Apache-2.0) | 6 h | High: the operators that actually find gains |
| 3 | Vansteenwegen ILS TOPTW | R9, R3, scout points, L4 speed | Idea | 3 h | High: O(1) feasibility makes ALNS fast enough |
| 4 | Sync-VRP / STN (Drexl, Hà, Hojabri) | **R4, R10**, R9 | Idea | 5 h | High: unlocks multi-effector hostiles, the biggest unserved points at L4 |
| 5 | HGS-CVRP / PyVRP | 60 s at L4, energy, points | Idea | 2–6 h | Medium: granular lists are a cheap must-have, penalties optional |
| 6 | NASA ground delay + SIPP | **R8**, R2 | Idea | 4 h | Medium–high: valid separation without energy cost |
| 7 | Santini OP-ALNS | points vs 0.5·Wh vs 10·eff trade-off | Idea (GPL) | 2 h | Medium: stops serving unprofitable contacts |
| 8 | CBBA (zehuilu, keep9oing) + ED-CBBA | link-loss part, message budget, sizing curve | Port (MIT) | 6 h | Only if the link-loss part ships |
| 9 | marcellobardus/EDTH_Paris (Alta Ares, Jun 2026) | link-loss part, jury framing | Idea | 2 h | Low for score, medium for pitch |
| 10 | jerryfungi SEAD task allocation | R4, verify bonus, link-loss | Idea | 2 h | Low (verify board only) |

Rough total for 1–7: about 27 h (with entry 5 at its 4 h midpoint). That fits in about 40 h shared by two planner people plus one person on R8/R10.

## If we only take 3 things

1. **ALNS loop (1) with jsprit's ruin/recreate set and SISR strings (2), operating on whole contact bundles.** This is how the planner goes beyond the 24 % of points the greedy baseline serves at L4.
2. **Bundle insertion with STN timing (4).** Observation + all required effectors are inserted together, with a common engagement time inside the window, ≥ 10 s after the observation ends, spread ≤ 20 s, and early arrivals absorbed by take-off delay. This makes R4 and R10 correct by construction.
3. **O(1) slack checks (3) plus granular neighbourhoods (5).** Without these, a pure-Python ALNS gets too few iterations in 50 s at L4 to beat greedy by much.

Separation (6) is required for validity, but the official validator and our `guard` fallback already prevent zero scores, so take-off staggering plus altitude layers is enough at first.

---

## Looked at and excluded (with reason)

- **Learned routing solvers: RL4CO** (https://github.com/ai4co/rl4co, MIT, Python + torch, push 2026-09-14), **RouteFinder** (https://github.com/ai4co/routefinder, MIT; weights at https://huggingface.co/ai4co/routefinder), **PARCO** multi-agent (https://huggingface.co/ai4co/parco), **POMO** (https://github.com/yd-kwon/POMO, no licence), **attention-learn-to-route** (https://github.com/wouterkool/attention-learn-to-route, MIT). All need torch and GPU training. None model cross-vehicle sync, 3D separation, no-fly cylinders or one-way vehicles. Pure-Python transformer inference would eat the 60 s for worse solutions than LNS. At most a pitch slide on "why not learning".
- **Amazon Last Mile winner, Just Passing Through** (https://github.com/heldstephan/jpt-amz, MIT, C, LKH-based). Single-vehicle TSP with zone-order penalties; nothing on sync. Second-place code not found.
- **EURO Meets NeurIPS 2022:** OptiML (https://github.com/N-Wouda/Euro-NeurIPS-2022, archived) and the ORTEC quickstart (https://github.com/ortec/euro-neurips-vrp-2022-quickstart, C++ HGS). Folded into entry 5. Their dynamic dispatch/postpone logic doesn't apply to our static scenarios.
- **DIMACS 12th challenge (VRPTW):** PyVRP's earlier versions ranked 1st on this track (entry 5). The controller and instances are at laser-ufpb on GitHub.
- **VROOM** (https://github.com/VROOM-Project/vroom, BSD-2, C++) and **Timefold** (https://github.com/TimefoldAI/timefold-solver, Apache-2.0, Java). Same operator ideas as jsprit; jsprit's defaults are easier to read.
- **Kaggle Santa / Reaktor CVRP puzzles:** write-ups agree that **simulated annealing with fast delta evaluation** wins under fixed time (deepsense.ai Santa's Stolen Sleigh, Reaktor 2018). That supports SA acceptance in entry 1. There is no code to reuse.
- **ROADEF/EURO:** winners are heuristic every year since 2010 (2020 prize page). The 2018 top-3 code is on GitHub, but the problem was not fleet tasking (from memory, inventory routing; not verified).
- **Papers with Code:** shut down by Meta in July 2025, now redirecting to Hugging Face Trending Papers. Benchmark leaderboards are not carried over.
- **Hugging Face Spaces / datasets:** only the RL4CO-family checkpoints and datasets (see above). No routing Space relevant to us.
- **robin-shaun/Multi-UAV-Task-Assignment-Benchmark** (no licence, GA/ACO/PSO on an extended team orienteering problem). Population methods without sync or separation; weaker than LNS at our budget.
- **NASA / defense ISR-strike papers:** Yan et al. 2019, Applied Sciences 2019, and the arXiv 2411.02062 heterogeneous MRTA (code under ROS, explicitly no precedence). Folded into entries 4 and 10.
- **Other EDTH repos** (detection, acoustics, C2, hardware; listed in PRIOR_ART.md §15). No SUB-15 / `fleetkit` solutions are public (GitHub repo and code search for `fleetkit`, `AA-Hackathon-EDTH`).

## Sources and queries covered

**Official spec read:** `kit/fleet-orchestration/README.md`, `kit/fleet-orchestration/fleet-kit/README.md`, `fleet-kit/examples/L2-7.json` (`rules` block, top-level keys).

**Web searches (this round):**
- `RL4CO RouteFinder POMO attention model vehicle routing github license 2025 2026`
- `huggingface vehicle routing model dataset space RL4CO`
- `huggingface.co ai4co routefinder model card weights license`
- `EURO Meets NeurIPS 2022 vehicle routing competition winning solution code github`
- `Amazon Last Mile Routing Research Challenge winning solution github code`
- `DIMACS implementation challenge VRPTW 2021 winning code github open source`
- `ROADEF EURO challenge winners open source code vehicle routing scheduling inventory routing github`
- `Kaggle Santa competition routing optimization winning write-up simulated annealing traveling santa`
- `Papers with Code shut down 2025 redirect Hugging Face`
- `jsprit ruin and recreate operators radial random worst string removal regret insertion time windows skills`
- `multi-UAV ISR strike mission planning heterogeneous scouts attackers task allocation open source code precedence`
- plus the 17 web queries listed in PRIOR_ART.md (EDTH / Alta Ares, ALNS, sync VRP, TOPTW, PyVRP, SISR, cooperative attack, CBBA, ACBBA, deconfliction, HGS, STN, implicit coordination).

**GitHub (`gh api` repo metadata, trees and file greps; `gh search repos`):**
- Metadata (licence, language, last push, stars) for: heldstephan/jpt-amz, N-Wouda/Euro-NeurIPS-2022, ortec/euro-neurips-vrp-2022-quickstart, ai4co/rl4co, ai4co/routefinder, VROOM-Project/vroom, graphhopper/jsprit, TimefoldAI/timefold-solver, PyVRP/PyVRP, N-Wouda/ALNS, vidalt/HGS-CVRP, zehuilu/CBBA-Python, keep9oing/consensus-based-bundle-algorithm, Constantino/TOPTW, alberto-santini/orienteering-alns, marcellobardus/EDTH_Paris, jerryfungi/Multi-UAV_Task_Allocation_SEADmission, robin-shaun/Multi-UAV-Task-Assignment-Benchmark, wouterkool/attention-learn-to-route, yd-kwon/POMO, eartser/sipp-mapf.
- File level: ALNS `alns/` tree and numpy usage in `ALNS.py`, `RouletteWheel.py`, `SegmentedRouletteWheel.py`, `SimulatedAnnealing.py`, `RecordToRecordTravel.py`. jsprit ruin/recreate file list and `box/Jsprit.java` defaults. CBBA function lists in zehuilu `lib/CBBA.py` and keep9oing `CBBA.py`. marcellobardus `retasking.py`, `packet_loss.py`, `gs/gs/` tree.
- Repo searches: `safe interval path planning`, `conflict based search MAPF`, `SISR vrp`, `slack induction string removal`, `vrptw synchronization`, `decentralized task allocation communication loss`, plus the round-1 searches in PRIOR_ART.md.

**Not verified:**
- the ALNS example defaults (`[25,5,1,0]`, decay 0.8), the HGS `targetFeasible`/penalty factors and Γ = 20 (all from memory of the papers and docs);
- that PyVRP's current API has prize-collecting clients;
- the first-place EURO-NeurIPS 2022 team's code (the CodaLab leaderboard is flagged incorrect by the organisers);
- the official DIMACS VRPTW winner name.

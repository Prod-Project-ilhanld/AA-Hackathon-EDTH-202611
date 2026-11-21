# Research round 2: existing algorithms vs. what `main` does now (Sat 21 Nov, 16:40)

Builds on [TOP10.md](TOP10.md) and [PRIOR_ART.md](PRIOR_ART.md). Those were written before we knew our own design and before the link-loss rules came out. This round starts from current `main` (5dbc69a) and asks: **which known algorithm is our code already, and what can that algorithm's literature add cheaply before the 09:00 merge window?**

Constraints applied to every item: standard library only, Python 3.9, 60 s per scenario (search budget 38 s), `policy.step` < 50 ms, 64-byte messages, policy actions limited to continue/speed/hold/return, and the merge rule (paired, ≥ 20 L4 train seeds, mean > 0, ≤ 40 % worse, 0 invalid).

## 1. What our code already is, in textbook terms

| Our code | Textbook name | Consequence |
|---|---|---|
| `planner._search`: greedy `build` driven by a priority order of contacts, Gaussian noise on per-contact weights, keep the noise vector if the score improves | **Random-key search with a greedy decoder** (the decoder idea of BRKGA), climbed by a **(1+1) hill-climb** | The literature on *priority-driven greedy search* applies directly: SWO, iterated greedy, LAHC |
| `deconflict.schedule`: earliest R8-free take-off | **Ground-delay programme** / prioritized fixed-path coordination | Already covered (TOP10 #6) |
| `policy.py`: send only when off plan (`hd`/`rt`/`rs`), peers dead-reckoned on the plan | **DIS dead reckoning** (IEEE 1278): the shared model is the plan, send only when you deviate | Correct design; the threshold idea can go further (see 3c) |
| `policy.py`: news repeated a fixed number of times (`_rc_ttl`, `_ob_ttl` = 4, relays = 2) | **Rumor mongering with a counter** (Demers et al. 1987) | Known weakness: some nodes never hear the rumor. The standard fix is a slow anti-entropy backup |
| `policy.py`: R8 by holding, lower aircraft id has right of way | **Prioritized velocity tuning on fixed paths** (path-velocity decomposition, Kant & Zucker 1986) | Known weakness: **deadlock** when two agents wait on each other |

**Dropped from TOP10:** #8 CBBA. The link-loss rules give no re-routing action (only continue/speed/hold/return), so task re-allocation is impossible. CBBA is out.

## 2. Planner: what to take

### 2a. Squeaky Wheel Optimization (Joslin & Clements, JAIR 1999): best fit, ~20 lines
Loop: **construct** (our `build`) → **analyze** (blame each element for how badly it was handled) → **prioritize** (move blamed elements forward) → repeat. It is our search with the blind Gaussian noise replaced by feedback.
- **Blame for us:** a hostile that was not served gets blame ∝ its net value (`points − 10·needs`); a served contact gets none. A cheap extra: blame the contacts *that took the effectors* of a richer unserved one (optional).
- **Change:** in `_search`, after each build, read the served set from `plan` (engage targets), and set `noise[c] *= (1 + k·blame_c)` for the next order, with some random noise kept (the paper warns SWO can cycle; noise breaks it).
- **Safe rollout:** run SWO on half the workers (e.g. odd ones), keep Gaussian noise on the others. Worst case it wastes half the restarts.
- **Effort:** 1–2 h incl. a paired bench. **Risk:** low, same build, same validation.

### 2b. Iterated greedy with prefix reuse (Ruiz & Stützle, EJOR 2007): the speed lever
IG = remove d elements from the order, reinsert them, rebuild. For us the gain is not the operator, it is that **only the order after the first changed position needs rebuilding**. Today every build starts from scratch.
- **Change:** perturb only the tail (positions ≥ i), snapshot the planner after contact i−1 of the best order, rebuild from the snapshot. ROADMAP WS0 already lists "prefix snapshots".
- **Effort:** 3–4 h (planner state copy must be correct: routes, score, scout task lists, R8 items). **Risk:** medium (shared mutable state). Only worth it if L4 builds are few per worker (see question 1).

### 2c. Late Acceptance Hill Climbing (Burke & Bykov, EJOR 2017): 5 lines
Accept a candidate order if it beats the score from L iterations ago, not only the best. One parameter. Helps when the climb stalls on a plateau.
- **Caveat:** with only tens of builds per worker at L4, acceptance rules barely matter. Try it at L2–L3 first, where builds are fast.

### 2d. BRKGA crossover (Gonçalves & Resende 2011): skip for the hand-in
Our noise vector is already a random key. Elite crossover (inherit the elite gene with ρ ≈ 0.7) needs a population. Our workers are separate processes that share nothing, and L4 has too few builds. Mention it in the pitch as "our search is a random-key search; BRKGA is the population version".

## 3. Link-loss policy: what to take

### 3a. Check for deadlock (fixed-path coordination literature): check first, ~1 h
The fixed-path coordination literature names deadlock as its main failure (Abrahamsen et al. show the problem is NP-hard). In `_r8_conflict`, `if cur_pm == "hold": return True` makes an aircraft hold whenever a conflicting peer is holding. Possible trace: C returns → A and B both hold for C → both are now off plan → each sees the other as `hold` → both hold until the 15 s expiry, then repeat. That's **not a failure** (holding is safe) but it burns energy and misses windows. **A hypothesis, not verified:** grep the sizing runs for aircraft that hold more than ~20 s in a row. Fix if it shows up: the lower-id aircraft never yields to a *holding* higher-id peer (a strict total order stays deadlock-free).

### 3b. Range-aware confirmation (R4) delivery: probably the 250 m column
ROADMAP says "250 m range fails every capacity". Our guess at why: an effector aborts when it hasn't heard `ob` 4 s before engaging. The scout sends `ob` 4 times right after the dwell, when the effector may still be > 250 m away (light effectors at 35 m/s cover 350 m in the 10 s confirm margin). Ideas from the literature, cheapest first:
1. **Time the repeats with dead reckoning:** the scout knows every effector of that contact from the plan, so it sends `ob` when the plan puts one of them within `R_max/2`, not right after the dwell. The policy doesn't know `R_max`, so use the plan distance ranking: send at the predicted closest approach.
2. **Anti-entropy backup (Demers):** every N s, aircraft re-send their oldest confirmed `ob` ids at a low rate. Message cost is 0.002 per msg/aircraft/min, so ~6 extra messages per minute cost 0.012 of S_loss. Cheap compared with the retention it buys.
3. **Store-and-forward by peers:** already present (relays with TTL 2). Raising the relay TTL only for `ob` of contacts whose engagement is still ahead is a one-line change.
Never "trust the plan": a `failure` event can kill the scout silently, and then an engagement without an observation fails the whole run.

### 3c. Shorter messages (DIS-style compact state): helps the 50 B/s column
`p_cap = min(1, C / bytes offered to j)`, so at C = 50 B/s two 40-byte messages to the same receiver already halve delivery. Send contact **indices** (position in `scenario.contacts`) instead of id strings, and a list instead of a keyed dict, e.g. `[1,[3],[],[]]`. Measure bytes per message before and after.

### 3d. `speed` instead of `hold` for R8 (path-velocity decomposition): later
Velocity tuning is the textbook tool; hold is just speed 0. `speed 0.5` keeps progress and arrives less late. But the conflict check must then model the peer at a scaled rate. More code, more risk: after 3a–3c.

## 4. Ranking for the time left (merge window Sun 09:00)

| # | Item | Part | Effort | Why now |
|---|---|---|---|---|
| 1 | 3b range-aware `ob` + anti-entropy | link-loss | 2 h | Likely fixes a whole sizing column (4 of 20 cells) |
| 2 | 2a SWO on half the workers | planner | 1–2 h | Smallest change to the search; same safety net |
| 3 | 3a deadlock check | link-loss | 1 h | Read logs first; fix only if seen |
| 4 | 3c compact messages | link-loss | 1 h | Helps 50 B/s cells |
| 5 | 2c LAHC | planner | 30 min | Trivial, L2–L3 only |
| 6 | 2b prefix reuse | planner | 3–4 h | Biggest planner speed-up, highest risk; only if builds/worker at L4 is low |
| — | 2d BRKGA, 3d speed tuning, CBBA | — | — | Pitch slides, not code |

## In flight elsewhere: strike-group layers (session `group-layers`, branch `feature/group-layers`, 16:40)
- **What it changes:** `RoutedPlanner._place_effectors` in `planner.py`. Besides the 3 layer rotations, it adds a 4th option that puts group members on layers as far apart as possible (heavies low), behind `params.GROUP_SPREAD` (on). There's a 4-case test, `tests/test_group_layers.py`. Not committed. Its paired bench (L4 0–19) and an intra-group conflict measurement (L4 20–29) are running.
- **Overlap with this note:** SWO / LAHC / prefix reuse edit `_search` in the same `planner.py`, a different function, so the merge is easy. But **both change the planner baseline**: prototype the search items only after group-layers is merged or rejected, then bench against that `main`.
- **Prefix reuse (2b) gets harder:** the 4th layer option makes each build slower, so builds per worker drop and 2b matters more. The planner state to snapshot doesn't change, though.
- **Literature check on the idea:** one altitude per member is standard vertical separation (flight levels). The known catch is the one the ROADMAP already notes: layers don't stop conflicts during climb and descent near the pads or on the final dive to the contact. The R8 exemption only covers the last 100 m around the shared contact. Its measurement script classifies the remaining conflicts as intra-group vs external, which is the right test.

## Handoff briefs for the build session (in order; one at a time, each through a PR)
Gate for every brief: paired run with `FLEET_ITERS` (planner) or fixed comm seeds (policy), on train seeds only, 0 invalid / 0 failed runs, CI green. Don't start a wall-clock bench while another one runs.

**B1 — Finish group-layers (already in progress).** Read its L4 0–19 paired bench and the intra-group conflict count. Merge only if it passes the gate; otherwise set `GROUP_SPREAD` off and close. *Done when:* merged or closed, and `main` is the new baseline for B3.

**B2 — Link-loss: deliver the R4 confirmation (`policy.py`, independent of B1, can start now).**
1. Measure first: run `check_policy.py` / `--sizing` and list the failing cells and the reason per run (failure, R4 abort, energy). Confirm that the 250 m column fails because effectors abort without `ob`.
2. If confirmed: the scout re-sends `ob c` when the plan puts an effector of `c` at its closest approach (dead reckoning via `RouteClock`), and every aircraft re-sends one known `ob` every ~10 s (anti-entropy). Keep the "never trust the plan" rule.
*Done when:* sizing score and frontier compared before/after, 0 failed runs, step time still < 50 ms.

**B3 — Planner: Squeaky Wheel on half the workers (`planner._search`, after B1).** After each build, raise the weight of unserved hostiles by their net value (`points − 10·needs`), keep some Gaussian noise; odd workers only, behind a `params.py` flag. *Done when:* paired L4 ≥ 20 seeds passes the gate, plus `check_handin` 8/8 and max time ≤ ~41 s.

**B4 — Link-loss: deadlock check (`policy.py`, after B2).** Count runs where two aircraft hold ≥ 20 s in a row because of each other. Fix only if seen: the lower id never yields to a holding higher-id peer.

**B5 — Link-loss: compact messages (`policy.py`, after B4).** Contact indices instead of ids, a list instead of a dict. Report bytes per message and the 50 B/s cells before/after.

Not handed off (pitch material only): LAHC, prefix reuse (only if B1 leaves very few builds per worker at L4), BRKGA, speed-scaling for R8, CBBA.

## Evidence required per brief (no merge without it)
Every brief ships with four things, written **before** the code runs, so the result can't be argued afterwards:
1. **Claim:** one sentence, with the number it should move.
2. **Proof or argument:** why it holds (or a safety invariant), checked by a test where possible.
3. **Tests:** unit / property tests in `tests/`, run in CI.
4. **Eval + verifier:** exact command, seeds, metric, pass rule. The verifier is always the **official kit code**, never ours: `fleetkit.validator.validate` / `scorer.evaluate` for plans, `fleetkit.linkloss.score` (`simulate`, `evaluate_cases`, `sizing`) for the policy. Raw JSON is saved to `runs/<brief>-<date>.json` and linked from the PR.

General rules: train seeds 0–199 only; holdout 5000–5049 only at a checkpoint (Mahmoud); a result with any invalid plan or failed run is a fail, whatever the mean; fixed-iteration or fixed-seed runs for comparisons, wall-clock only on an idle machine, one at a time.

| Brief | Claim | Proof / invariant | Tests (CI) | Eval + verifier | Pass rule |
|---|---|---|---|---|---|
| **B1** group layers | Spreading members over layers cuts intra-group R8 rejections and raises L4 score | Members on distinct layers ≥ 40 m apart can't conflict while both cruise; conflicts can only remain in climb/descent (measured, not assumed) | `test_group_layers.py` (4 cases, done): distinct layers, sync kept, flag off = old behaviour | `FLEET_ITERS=N PLANNER_WORKERS=1 python3 tools/bench.py --levels L4 --seeds 0-19 --base <main copy> --json runs/b1.json` + its intra-conflict count before/after (L4 20–29) | Paired mean > 0, ≤ 40 % seeds worse (or mean > 2 s.e.), 0 invalid; `check_handin` 8/8; max time ≤ ~41 s idle |
| **B2** R4 delivery | Effectors that would have engaged stop aborting for lack of `ob`, so the 250 m (and low-capacity) cells reach retention ≥ 0.9 | **Safety invariant:** an effector engages only if it holds an `ob` for its target that came from a scout's `own_observed` (directly or relayed). Re-sending more never makes an engagement happen without a real observation, so R4 can't fail because of this change | (a) unit: an effector with no `ob` aborts before its last waypoint; (b) unit: a relayed `ob` is accepted; (c) property: in sim runs with a `failure` event killing the scout, 0 R4 failures; (d) message ≤ 64 B for every built message; (e) step time < 50 ms | Step 1 (diagnosis, before code): `sizing()` per cell on baseline plans (the jury uses its own reference plans, so test on those first, ours second), scenario seeds 0–19 L1–L4, events seed 1; log each lost point as R4-abort / failure / energy / event. Step 2: same grid after | Sizing score up, frontier no worse at any range, **0 failed runs in every cell**, S_loss at 1000×200 no worse; diagnosis must show R4 aborts are the main loss at 250 m, otherwise stop and re-plan |
| **B3** Squeaky Wheel | Feedback on unserved hostiles finds better orders than blind noise in the same number of builds | Same `build`, same validator on every kept plan, so validity is unchanged; only the order differs. Gain is empirical, not provable | unit: blame is 0 for served contacts and grows with net value; flag off = byte-identical plans to `main` under `FLEET_ITERS` | `FLEET_ITERS=N` paired L4 0–39 (≥ 20 required, 40 for a smaller effect) + L2/L3 0–19 to check no regression | Gate as B1 on L4; L2/L3 mean ≥ 0 |
| **B4** deadlock | Mutual holds exist and cost retention | **Proof of the fix:** with a strict total order (lower id never yields to a holding higher id) a wait-for cycle can't form, so no deadlock (standard prioritized-coordination argument) | unit: two aircraft, each in the other's path while holding: the lower id moves within 1 step; regression: no R8 failure in `test_team_linkloss.py` | Count mutual holds ≥ 20 s over the B2 grid runs (needs a trace hook in the eval script, not in `policy.py`) | Fix only if count > 0; after: count 0, 0 failed runs, retention no worse |
| **B5** compact messages | Fewer bytes raise delivery at 50–100 B/s | `p_cap = min(1, C / bytes offered)`: fewer bytes ⇒ `p_cap` never lower (direct from the rule) | unit: encode → decode round-trip for every message kind; every message ≤ 64 B; mean bytes reported | Same grid as B2, capacity 50/100 columns | Mean bytes down, those cells' retention no worse, 0 failed runs |

What counts as "proof" here: B2's and B4's safety claims are invariants we can argue and pin with tests; B1, B3 and B5 are empirical claims, proven only by the paired evals above. The pitch must say which is which.

## Results so far (Sat 21 Nov, ~17:30)
**B2 step 1 (diagnosis), current `policy.py`, baseline plans, L1–L4 seeds 0–4, events seed 1, 5 comm seeds, official sim.** Raw: `runs/b2-diag-2026-11-21-before.json` (branch `feature/policy-r4-delivery`, 64e8cee). I re-read the table from the JSON.

| Cell | Retention | Failed runs /100 | R8 failure | R4 abort, obs was done | Hold lateness | R4 abort, obs not done |
|---|---|---|---|---|---|---|
| 250 × 50 | 0.742 | 13 | −0.130 | −0.092 | −0.029 | −0.011 |
| 250 × 100–800 | 0.754 | 10 | −0.100 | −0.094 | −0.042 | −0.013 |
| 1000 × 200 (leaderboard) | 0.983 | **1** | −0.010 | −0.003 | −0.004 | — |

- **The B2 claim was half right.** Missing "ob" costs ~0.09 at 250 m, but **R8 separation failures cost more** (−0.10 to −0.13), and each one zeroes its run. Fixing "ob" alone would give ~0.85, still below 0.9 and still with failures.
- **The leaderboard cell also fails the bar:** 1 failed run in 100.
- Capacity barely matters at 250 m: range, not bandwidth, is the limit.

**R8 diagnosis** (session r8-diag, `feature/r8-diag` d77db35, raw `runs/b2-r8-diag-2026-11-21.json` in the `repo-r8-diag` worktree), as reported by that session; I haven't re-derived these counts myself:
- 41 of 61 R8 failures at 250 m come from a **wrong belief about a peer**: about 30 from lost messages, about 15 from a policy gap (no `rt` is sent when switching from hold to return), and a few from the 15 s hold expiry.
- 20 of 61 happen with both sides informed, mostly two returning aircraft.
- **Deadlock confirmed (B4 hypothesis):** 152 mutual holds of ≥ 20 s in 48 of 100 runs per 250 m cell, almost none released. Also seen at 1000 × 200.
- Open: hold lateness is only −0.04 despite the stuck aircraft. Probably most stuck ones have no task left, but nobody has checked.

**Re-ordered plan for link-loss:** failures are zero-tolerance, so R8 comes before "ob".
1. **R8-a:** always send `rt` on hold → return; don't expire a holder's `hd` while it still sends.
2. **R8-b (was B4):** break mutual holds with a strict total order (proof in the evidence table); fix the returning-pair case.
3. **B2 fix:** range-aware `ob` re-send + anti-entropy.
4. The uncertainty band for unheard peers comes only after 1–2, since it adds holds.

Same evidence rule: 0 failed runs in every cell (including 1000 × 200), sizing score up, frontier no worse, S_loss at 1000 × 200 no worse.

## What this research session does next
- Watch B1's numbers and update this note and the checkpoint board with them.
- Before each brief starts, re-check what's in flight (sessions, branches) so two sessions never edit the same file.
- Prepare the jury story: "which textbook algorithm each module is" (section 1) and the "why not" list (learned solvers, CBBA, GA) as slide notes.
- Keep the open questions below chased.

## Open questions (need team input)
1. **How many builds does one worker do at L4 in 38 s?** It decides 2b and 2c. Not measured here: the machine was loaded (load 8.9 on 8 cores) and the rules say one timing job at a time.
2. **Which sizing cells fail today, and why** (R4 abort, failure, energy)? Youcef's last numbers: 40/40 L2/L3 and 8/8 L1–L4, but not per cell. 3b is a guess until the 250 m failures are read.
3. Did the organisers answer on **jury core count**? SWO on half the workers assumes several workers.

## Sources
- Joslin & Clements, "Squeaky Wheel" Optimization, JAIR 10 (1999): https://arxiv.org/pdf/1105.5454 · https://jair.org/index.php/jair/article/view/10231
- Ruiz & Stützle, iterated greedy for flowshop, EJOR 2007; IG vs ILS, TOP 2025: https://ideas.repec.org/a/spr/topjnl/v33y2025i2d10.1007_s11750-025-00699-x.html
- Burke & Bykov, Late Acceptance Hill-Climbing, EJOR 258 (2017): https://ideas.repec.org/a/eee/ejores/v258y2017i1p70-78.html · https://www.cs.stir.ac.uk/~kjt/techreps/pdf/TR192.pdf
- Random-key GA review: https://arxiv.org/pdf/2506.02120 · BRKGA review: https://ar5iv.labs.arxiv.org/html/2312.00961
- Path-velocity decomposition / prioritized velocity planning: https://publica-rest.fraunhofer.de/server/api/core/bitstreams/9f2fa702-fc9a-4890-864a-63e57e147b37/content · Peng & Akella: https://webpages.charlotte.edu/sakella/papers/PengAkellaIJRR05.pdf
- Fixed-path coordination and deadlock: https://w3.onera.fr/copernic/sites/default/files/2022_-_dars_-_a_comparison_of_two_decoupled_methods_for_simultaneous_multiple_robots_path_planning.pdf · https://arxiv.org/pdf/2401.08443 · https://people.kth.se/~dimos/pdfs/ACC20_Pian.pdf
- Demers et al., Epidemic Algorithms for Replicated Database Maintenance (PODC 1987): https://none.cs.umass.edu/~shenoy/courses/fall04/readings/demers.pdf · https://cs.cornell.edu/courses/cs6410/2009fa/lectures/18-epidemics.pdf
- DIS dead reckoning thresholds: https://www.comp.nus.edu.sg/~cs4344/0607s1/deadreckoning.pdf · https://mural.maynoothuniversity.ie/id/eprint/280/1/Paper02_IASTED_2003.pdf
- Event-triggered coordination tutorial (Nowzari, Garcia, Cortés): https://arxiv.org/pdf/1712.00429
- UAS lost-link procedures: https://www3.gmu.edu/schools/vse/seor/studentprojects/graduate/2012Spring/UL2/index.php · https://humanfactors.arc.nasa.gov/publications/AIAA_Fern_etal_ContingencyManagement_Formatted.pdf
- Multi-UAV simultaneous attack allocation: https://mdpi.com/2076-3417/9/10/1986

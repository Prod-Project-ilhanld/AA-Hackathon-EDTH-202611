# Open tasks (Sat 21 Nov, evening)

GitHub Issues are off in this repo, so the open tasks live here. Pick one, put your name next to it in the team chat, work on a `feature/...` branch from current `main`, and open a PR with the evidence each task asks for. Progress is tracked on the checkpoint board: https://claude.ai/artifact/7VzgyqXg2owcpXosdeK2sc

Rules for every task: train seeds 0–199 only (holdout 5000–5049 only at checkpoints, by Mahmoud); a result with any invalid plan or failed run is a fail; compare with `FLEET_ITERS` or fixed seeds; wall-clock runs only on an idle machine, one at a time; plain commit messages.

| # | Task | Owner | Priority |
|---|---|---|---|
| 1 | Link-loss: fix R8 separation failures and mutual-hold deadlocks | Youcef | 1 |
| 2 | Link-loss: deliver the observation (`ob`) at short range | Youcef | 2 |
| 3 | Planner: Squeaky Wheel feedback in the order search | Louis | 3 |
| 4 | Shift suite in jury conditions on the final main | Martin | tonight |
| 5 | Organiser answers: cores, multiprocessing, format, Python | Ilhan | blocking |
| 6 | CP4 holdout on current main + L1-0 check | Mahmoud | tonight |
| 7 | Link-loss: compact messages | Youcef | 4 |


---

## 1. Link-loss: fix R8 separation failures and mutual-hold deadlocks (policy.py)

**Owner suggestion:** Youcef (`handin/policy.py` is his file). **Priority: 1** (link-loss). **Effort:** ~2 h.

### Why
The link-loss policy (PR #9) passes `check_policy` (12/12 retention 1.000 on L1–L4 seeds 0–2), but the organisers' **sizing grid** shows separation (R8) failures, and **a failed run scores 0 retention**:

| Cell (range × capacity) | Retention | Failed runs / 100 |
|---|---|---|
| 250 m × 50 B/s | 0.742 | 13 |
| 250 m × 100–800 B/s | 0.754 | 10 |
| **1000 m × 200 B/s (leaderboard setting)** | 0.983 | **1** |

Source: diagnosis on branch `feature/r8-diag` (`d77db35`, local), notes in `docs/research/ALGORITHMS_R2.md` ("Results so far"). Of 61 R8 failures at 250 m:
- **41 come from a wrong belief about a peer:**
  - ~30 from lost messages.
  - **~15 from a policy gap:** when an aircraft switches from *hold* back to *return*, it sends no new `rt`, so peers still think it is holding.
  - ~5 from the 15 s hold expiry: a peer is reset to "on plan" while it is still holding.
- **20 happen with both sides informed**, mostly two returning aircraft. The higher id holds, but the lower id predicts it still moving and flies into it.
- **Deadlocks:** 152 mutual holds of ≥ 20 s in 48 of 100 runs per 250 m cell, almost never released (also seen at 1000 × 200). Two aircraft each believe the other is holding and wait forever, and all their tasks are lost.

### Task
1. **Always send `rt` on a hold → return switch.** Don't expire a holder's `hd` while that holder keeps re-sending it.
2. **Break mutual holds with a strict total order:** the lower id never yields to a *holding* higher-id peer it is not closing on. A total order means no wait-for cycle can form, so no deadlock.
3. **Fix the returning-pair case** (both returning, lower id flies into the holder).

### Done when (evidence, verifier = official kit code)
- **0 failed runs in every sizing cell**, including 1000 × 200.
- Sizing score (cells meeting retention ≥ 0.9) up; frontier no worse at any range; S_loss at 1000 × 200 no worse.
- Mutual holds ≥ 20 s: count 0 (use the `--r8` mode of the diagnosis script on `feature/r8-diag`).
- Tests in `tests/`:
  - two aircraft each in the other's path while holding: the lower id moves within 1 step;
  - every message ≤ 64 bytes written compactly;
  - step time < 50 ms.
- Commands from `fleet-kit/`: `python3 handin/check_policy.py --levels L1,L2,L3,L4 --seeds 0-9`, and `python3 -m fleetkit linkloss scenario.json plan.json events.json handin/policy.py --sizing` (train scenario seeds only).

### Don't touch
`planner.py`, `deconflict.py`, `params.py` (the planner side; it is scored separately and is being frozen).

---

## 2. Link-loss: deliver the scout's observation (ob) at short range, R4 aborts (policy.py)

**Owner suggestion:** Youcef (after the R8/deadlock issue, same file). **Priority: 2.** **Effort:** ~2 h.

### Why
At 250 m range, effectors abort their strike because they never hear that the target was observed (rule R4: an engagement needs a completed scout observation first). That costs ~0.09 retention per cell (see `docs/research/ALGORITHMS_R2.md`, "Results so far"). At 250 m the scout is often out of range when it observes, so the `ob` message never reaches the strikers. Capacity barely matters there: range is the limit.

### Task
- The scout **re-sends `ob <contact>` when the plan brings an effector of that contact within range**. It dead-reckons the effector's position with `fleetkit.linkloss.RouteClock` on the plan.
- **Anti-entropy:** every aircraft re-sends one known `ob` every ~10 s, so it spreads hop by hop.
- **Keep the safety rule:** an effector engages only if it holds an `ob` for its target that came from a scout's `own_observed`, directly or relayed. Re-sending more can never cause an engagement without a real observation, so this cannot create an R4 failure.

### Done when
- At 250 m: fewer R4 aborts (measure before/after with the diagnosis script), retention up, **0 failed runs in every cell**.
- Sizing score up, frontier no worse, S_loss at 1000 × 200 no worse.
- Tests:
  - an effector with no `ob` aborts before its last waypoint;
  - a relayed `ob` is accepted;
  - with a `failure` event killing the scout, 0 R4 failures;
  - every message ≤ 64 bytes; step time < 50 ms.

### Don't touch
The planner files. Do this after the R8/deadlock issue, since both edit `policy.py`.

---

## 3. Planner: Squeaky Wheel feedback in the order search, on half the workers (planner.py)

**Owner suggestion:** Louis (`_search` in `handin/planner.py` is his code). **Priority: 3** (planner, last planner change before the freeze). **Effort:** 1–2 h.

### Why
After this afternoon's merges (R8 scheduler + cache, R7 skip, greedy fallback), the cheap planner levers have been measured and **none gives more**:
- light/heavy pricing: noise;
- `scouts.py`: +0.12 %, a single seed;
- strike-group altitude spread: +5.7 ± 6.8 per seed over 40 seeds, 16 worse.

The search itself is still blind: after each build, the next contact order is the best one plus **random Gaussian noise**. Squeaky Wheel Optimization (Joslin & Clements, JAIR 1999) replaces the blind noise with feedback: **move the contacts the last build failed to serve forward** in the order. Details: `docs/research/ALGORITHMS_R2.md` §2a.

### Task
- In `_search`, after each build, read which hostiles were served (engage targets in the plan). Then multiply the next order's weight of each **unserved** hostile by `(1 + k · blame)`, where `blame ∝ points − 10·needs`. Keep some Gaussian noise, since pure SWO can cycle.
- **Safe rollout:** odd workers only. Even workers keep today's noise, so the worst case is wasting half the restarts.
- Put a flag in `params.py`. The jury passes no env vars, so the default decides.

### Done when (team rule)
- **Flag off ⇒ byte-identical plans to `main`** under `FLEET_ITERS` (test).
- Paired, deterministic, train seeds only:
  - `FLEET_ITERS=N PLANNER_WORKERS=2 python3 tools/bench.py --levels L4 --seeds 0-39 --base <main copy> --json …`
  - mean gain > 0, ≤ 40 % of seeds worse (or mean > 2 standard errors), 0 invalid;
  - L2/L3 seeds 0–19 mean ≥ 0.
- `/usr/bin/python3 handin/check_handin.py` 8/8, max time ≤ ~41 s **on an idle machine**. Run one timing job at a time: load from other benches spoiled several measurements today.

### Don't touch
`deconflict.py` (just changed, PR #11), `policy.py`.

---

## 4. Shift suite in jury conditions on the final main (overnight, Martin's PC)

**Owner suggestion:** Martin, on his PC. **When:** tonight, once `main` is final for the night (Mahmoud will say). **Effort:** ~3 h of machine time, almost no human time.

### Why
The shift suite is our guard against hidden scenarios that differ from the four public levels. Martin's jury-condition run (PR #15: 250 runs, 0 failures, ×2.07) used `main` at `ec5c41e`. That was **before** the R8 scheduler (PR #6), its cache (PR #11), the greedy fallback (PR #7) and the edge packs were merged. The code we hand in has never been through the shift suite in jury conditions.

### Task
1. From `fleet-orchestration/fleet-kit/` on the final `main`:
   `/usr/bin/python3 tools/shift.py --seeds 0-49 --jobs 1 --json shift_final.json`
   Use one job (strictly sequential) and 8 workers (default), on an otherwise idle machine.
2. **Use a Python 3.9 if possible.** The jury promises 3.9+ and our CI tests 3.9; last run used 3.14 under WSL.
3. Post per variant: total, ratio vs baseline, failures, worst seed, max time. Compare with the `ec5c41e` run.

### Done when
- **0 failures, no variant below baseline**, max time well under 60 s.
- Any crash or invalid plan: write down the scenario that triggers it and tell the file owner. Don't fix it yourself.

Also, separately: PR #16 is ready to merge once the six generated `view.html` files are dropped from it.

---

## 5. Organiser answers: jury core count, multiprocessing, hand-in format, Python version

**Owner suggestion:** Ilhan (mentor link). **Priority: blocking for the hand-in.** **Effort:** one conversation with the organisers.

### Why
Four answers change what we ship, and we don't have them yet:

1. **Jury machine core count, and is `multiprocessing` allowed?**
   - The planner runs up to 8 worker processes (`params.MAX_WORKERS`).
   - At 1 worker it stays valid and above baseline, but scores less.
   - With a slow or small machine, L4 runs already reach 39–41 s of the 60 s limit when our machine is loaded.
   - The answer decides the worker default, and whether we lower the 38 s budget for safety.
2. **Hand-in format:** a folder? Which files? We plan the whole `handin/` folder: `planner.py`, `params.py`, `fk/`, `routing.py`, `targets.py`, `deconflict.py`, `scouts.py`, and `policy.py` for link-loss.
3. **Python version** on the jury machine (we test 3.9).
4. **Link-loss:** is `policy.py` handed in the same folder, and which plans does the jury use for it (theirs or ours)?

### Done when
Answers posted as a comment here. The checkpoint board items "Organiser answers" and "Hand-in format confirmed" are marked done.

---

## 6. CP4 holdout on current main + confirm L1-0 is not below baseline

**Owner:** Mahmoud. **When:** tonight, on an idle machine, after the evening merges.

### Why
- The last holdout (seeds 5000–5049) was on `main` at `55327de`: ×1.51 total, L4 ×1.95. Since then `main` gained:
  - the R8 scheduler + cache;
  - the R7 skip;
  - the greedy fallback;
  - the routing fix.
- Nobody has measured the hand-in code on unseen seeds.
- On `717535a`, `check_handin` was run under heavy load (31–36), giving a total of 4229.7. That run also showed **L1-0 at 123.7 vs baseline 123.8**, the first time anything has dipped below the kit baseline. Probably load, but CP2's rule is "no level below baseline".

### Task
1. With no other bench running (`uptime` load < ~6), on the final `main`:
   `/usr/bin/python3 handin/check_handin.py` and `python3 tools/bench.py --levels L1 --seeds 0-9 --python /usr/bin/python3`.
   Check L1 is never below baseline.
2. **CP4 holdout:** `PLANNER_WORKERS=2 python3 tools/bench.py --levels L1 L2 L3 L4 --seeds 5000-5049 --jobs 4 --python /usr/bin/python3 --json holdout_cp4.json`. Compare with ×1.51 / L4 ×1.95.

### Done when
Totals posted here and on the checkpoint board. 0 failures, no level below baseline. If L1 regresses for real, bisect between `55327de` and `main`.

---

## 7. Link-loss: compact messages for the 50-100 B/s cells (policy.py)

**Owner suggestion:** Youcef (`handin/policy.py`). **Priority: 4** (after the R8/deadlock and R4 delivery issues). **Effort:** ~1 h.

### Why
In the sizing grid, a receiver can take `C` bytes per second. A message is delivered with probability `0.95 · p_range · p_cap`, where `p_cap = min(1, C / bytes offered to it this step)`. So **fewer bytes per message can never lower delivery**, and it raises it at 50–100 B/s, where several peers talk at once.

### Task
- Encode messages compactly: contact **indices** instead of ids, short keys, lists instead of dicts.
- Keep every message ≤ 64 bytes once written compactly (`json.dumps(msg, separators=(",", ":"))`). A longer one is silently not sent.

### Done when
- Mean bytes per message reported before/after, and lower.
- 50 and 100 B/s cells: retention no worse; 0 failed runs in every cell.
- Test: encode → decode round-trip for every message kind; every message ≤ 64 B.

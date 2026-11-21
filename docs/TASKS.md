# Open tasks (Sat 21 Nov, 23:45: night and Sunday morning)

GitHub Issues are off in this repo, so the open tasks live here. Pick one, put your name next to it in the team chat, work on a `feature/...` branch from current `main`, and open a PR with the evidence each task asks for. Progress is tracked on the checkpoint board: https://claude.ai/artifact/7VzgyqXg2owcpXosdeK2sc

Rules for every task:
- Train seeds 0–199 only. The holdout (5000–5049) is run only at checkpoints, by Mahmoud.
- A result with any invalid plan or failed run is a fail.
- Compare with `FLEET_ITERS` or fixed seeds.
- Run wall-clock benches only on an idle machine, one at a time.
- Plain commit messages.

## Where we stand (checked by Mahmoud, Sat 23:45)

### Planner: frozen at `cdc0671`

`main` is now `17739f1`: PR #16 adds diagnostics only, and the hand-in code is identical to `cdc0671`.

- The planner code hasn't changed since PR #11, and that PR gives byte-identical plans.
- CI is green, and the 319 tests pass on Python 3.9.
- There is no Squeaky Wheel branch yet (task 3). So the night runs use `cdc0671`: the shift suite (task 4) and the CP4 holdout (task 6).
- **CP4 holdout passed on `cdc0671`** (seeds 5000–5049, 200 runs, Python 3.9.6):
  - total **101,908.6** against a baseline of 63,989.4, so **×1.59**. The last holdout, on `55327de`, gave ×1.51.
  - by level: L1 ×1.09, L2 ×1.10, L3 ×1.26, **L4 ×2.13** (was ×1.95).
  - 0 invalid or failed runs; slowest run 40.0 s.
  - Two seeds land a hair below the baseline, and both reproduce exactly on re-run: L1-5010 79.2 against 79.8, and L2-5031 208.7 against 208.8. That's task 11.
- If task 3 lands by 08:00 with its gate passed, it gets merged and re-checked.

### Link-loss: PR #19 (Martin) + PR #23 (Youcef, stacked on #19) is what we ship

Setup: both PRs were re-run on the official sizing grid with `tools/linkloss_diag.py --sizing`. That means kit baseline plans, events seed 1, 5 comm seeds, and all 20 cells. Seeds 15–24 are fresh: neither author tuned on them.

|  | main | #19 | #19 + #23 |
|---|---|---|---|
| Sizing score, seeds 5–14 | 0.00 | 0.60 | **1.00** |
| Sizing score, seeds 15–24 | 0.00 | 0.00 | **0.75** |
| Frontier (smallest C that meets the bar) at 250/500/1000/2000 m, seeds 5–14 | none everywhere | none/100/100/100 | **50/50/50/50** |
| Failed runs over the 20 cells, seeds 5–14 | 142 | 31 | **0** |
| Failed runs over the 20 cells, seeds 15–24 | 328 | 118 | **20**: one case, see task 10 |
| 1000×200 retention (5–14 / 15–24) | 0.966 / 0.948 | 0.978 / 0.981 | 0.974 / **0.999** |
| 1000×200 messages per aircraft per minute | 5.4–5.9 | 7.9–8.1 | **17–18** |
| 1000×200 S_loss (5–14 / 15–24) | 0.954 / 0.937 | **0.962** / 0.965 | 0.938 / 0.965 |
| `check_policy` L1–L4, seeds 0–9: scenarios clean (retention ≥ 0.9, 0 failed runs) | – | 38/40 | 38/40 |
| Unit tests (Python 3.9) | 319 pass | 325 pass | 2 fail (test format only, see below) |

- **Why we ship both:**
  - #23 removes almost every failed run, and a failed run scores 0.
  - The frontier is part of the hand-in.
  - The price is messages: S_loss is retention − 0.002 × messages, and #23 sends twice as many. That's task 8.
- **#23's red CI:** two tests in `tests/test_policy_r8.py` read messages as dicts (`msg["hd"]`, `msg["rt"]`), but #23 sends compact lists. The behaviour those tests check still holds (hold, then back off). Fix: assert `msg[0] == 4` (hold + abort) and `msg[0] == 2` (return).
- **Merge path:**
  1. Youcef fixes the two tests and CI goes green.
  2. Mahmoud retargets #23 to `main` and merges it with a merge commit. Martin's commits are kept, and #19 closes as merged.
- **The two bad `check_policy` scenarios (same on #19 and #23):**
  - L1-6 fails with an R6 pop-up zone. The shipped `broadcast` baseline fails it too, so we accept it.
  - L3-6 drops to retention 0.611. It was 0.780 on main, and broadcast gets 1.000. That's task 9.
- **Policy cost per step:** at most 0.045 ms per call. The limit is 50 ms.

### Still open
- Organiser answers (task 5).
- The live board submission (Louis): post the total from the frozen planner.
- The repo is still public: the owner has to switch it to private.

## Night plan

| When | What | Who |
|---|---|---|
| now | Shift suite, all 50 seeds, on `cdc0671` (task 4) | Martin's PC |
| done 23:50 | CP4 holdout on `cdc0671` (task 6): ×1.59, L4 ×2.13, 0 failures | Mahmoud |
| tonight | #23: fix the two tests, CI green, then merge (path above) | Youcef, then Mahmoud |
| by 08:00 | Tasks 8, 9, 10: one PR each on top of the merged policy, each passing the link-loss gate below | Youcef (8), Martin (9), free (10) |
| by 08:00 | Task 3 PR with its gate evidence, or it's dropped for this hand-in | Louis |
| 09:00 | **Last merge window** | Mahmoud |
| 09:00–09:45 | CP5 on the candidate: final set 9000–9049, `check_handin`, `check_policy`, sizing on seeds 5–24 | Mahmoud |
| 10:00 | **Freeze:** tag `handin-final` | Mahmoud |

### Link-loss gate (every `policy.py` PR from now on)
Commands, from `fleet-orchestration/fleet-kit/`:
- `python3 tools/linkloss_diag.py --policy handin/policy.py --sizing --seeds 5-14 -o runs/<name>-5-14.json`
- the same with `--seeds 15-24`
- `python3 handin/check_policy.py --levels L1,L2,L3,L4 --seeds 0-9`

Done when, compared with #19 + #23 (numbers above):
- Failed runs no higher (0 on seeds 5–14, 20 on 15–24).
- Sizing score no lower (1.00 and 0.75).
- 1000×200 S_loss higher, or the same with fewer failed runs.
- `check_policy` gives no new unclean scenario.
- pytest is green on Python 3.9, and a step stays under 50 ms.
- Raw JSON is attached to the PR.

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Link-loss: R8 separation failures and mutual-hold deadlocks | Martin (#19), Youcef (#23) | Reviewed. Merge once #23's tests are fixed |
| 2 | Link-loss: deliver `ob` at short range | Youcef (#23) | Reviewed, same merge |
| 3 | Planner: Squeaky Wheel feedback in the order search | Louis | No branch at 23:45. PR with gate evidence by 08:00, or dropped |
| 4 | Shift suite in jury conditions | Martin | **Go now** on `cdc0671`, all 50 seeds |
| 5 | Organiser answers: cores, multiprocessing, format, Python | Ilhan | Blocking |
| 6 | CP4 holdout on current main + L1-0 check | Mahmoud | **Done**: ×1.59, L4 ×2.13, 0 failures, max 40.0 s |
| 7 | Link-loss: compact messages | Youcef (#23) | Done in #23: 8.3–8.5 bytes per message |
| 8 | Link-loss: cut the hover heartbeat (S_loss) | Youcef | **New, link-loss priority 1** |
| 9 | Link-loss: L3-6 retention drop after hover-on-abort | Martin | New, priority 2 |
| 10 | Link-loss: L3-21 enters a pop-up zone at 2000 m | free | New, priority 3 |
| 11 | Planner: never below the kit baseline on a seed | Louis | New, optional, by 08:00 |

Tasks 1, 2 and 7: the full briefs are in git history (`git show cdc0671:docs/TASKS.md`); the evidence is in PRs #19 and #23.

---

## 8. Link-loss: cut the hover heartbeat (policy.py)

**Owner:** Youcef. **Priority:** link-loss 1. **Effort:** ~1–2 h.

### Why
At 1000×200, #23 sends 17–18 messages per aircraft per minute, against 8 for #19. That costs ~0.02 of S_loss, the leaderboard metric. A probe on L2–L4 seeds 15–17 shows where the traffic goes:
- **78 %** is `hd+ab`, the heartbeat of an aborted aircraft hovering in place;
- **14 %** is `ob` re-sends (the near-range re-send plus anti-entropy every 8 s);
- the rest is under 10 %.

In `_build_message`, an aborted hoverer beacons at 1 Hz while any peer is predicted within 350 m. Since #19, peers **never expire** an aborted hold. So after the first few deliveries, a heartbeat only helps a peer that missed them.

### Task
- Keep the first 3 heartbeats.
- After that, beacon only when an on-plan peer is predicted to close in. Reuse `_blocking` with a longer horizon (~10 s) and a wider radius (~2 × (d_sep + pad)). Otherwise beacon every ~10–15 s.
- Check whether 1 Hz is really needed at 250 m. If it is, keep it only while a peer is closing in.
- Optional: anti-entropy only from aircraft that have an effector of that contact within range.

### Done when
- The link-loss gate holds.
- 1000×200 messages are back to ≤ ~10 per aircraft per minute, and S_loss at 1000×200 is ≥ 0.960 on both seed sets.

---

## 9. Link-loss: L3-6 retention drop after hover-on-abort (policy.py)

**Owner:** Martin. **Priority:** link-loss 2. **Effort:** ~1 h.

### Why
In `check_policy`, L3-6 (events `popup_zone` + `reclassify`):
- main: retention **0.780**;
- #19 and #19 + #23: **0.611** (C19 lost);
- `broadcast`: **1.000**.

Every other scenario in seeds 0–9 is clean or unchanged.

### Task
1. Trace the run (`python3 -m fleetkit linkloss ... --trace`, or the viewer).
2. Find who stops serving C19 and why. Suspect the group abort: an `ab` flag making a co-effector abort a contact that was still servable.
3. Fix it without adding failed runs.

### Done when
- L3-6 is back to ≥ 0.780.
- The link-loss gate holds.

---

## 10. Link-loss: L3-21 enters a pop-up zone at 2000 m (policy.py)

**Owner:** free (Martin or Youcef, after 8 or 9). **Priority:** link-loss 3.

### Why
All 20 failed runs left with #19 + #23 on seeds 15–24 are **one case**: L3-21 (events seed 1). H03 flies into a pop-up zone around t = 356 s:
- it happens only at 2000 m, in 4 of 200 runs at every capacity;
- it never happens at 1000 m;
- #19 alone fails it 9–10 times;
- this one case costs the 2000 m frontier.

### Task
Trace the run and find why H03 doesn't stop. Check:
- that the zone reached it in time;
- the position decode;
- that the compact `zn` encoding doesn't truncate the radius with `int()`.

### Done when
- 0 failed runs on L3-21 in every cell.
- The link-loss gate holds.

---

## 11. Planner: never below the kit baseline on a seed (planner.py)

**Owner:** Louis. **Priority:** optional, last planner change. Merge only by 08:00 with the gate below, or skip it.

### Why
On the CP4 holdout, two seeds score a hair under the kit baseline, deterministically:
- L1-5010: 79.2 against 79.8;
- L2-5031: 208.7 against 208.8.

The money is negligible (0.7 points out of 101,909). But "never below the baseline" is a claim for the pitch, and it held on `55327de`.

### Task
- At the end of `main()`, if at least ~8 s are left before the alarm, build the kit `greedy_plan` (already used by the greedy fallback). Score both plans with the vendored evaluator, and write the better one.
- Put a flag in `params.py`, default on.

### Done when
- Flag off: byte-identical plans.
- Flag on: L1-5010 and L2-5031 score at least the baseline. Train seeds L1–L4 0–19 under `FLEET_ITERS` give byte-identical plans wherever ours already beats greedy.
- `check_handin` on an idle machine: 8/8, max time no higher than today (~40 s).

---

## 3. Planner: Squeaky Wheel feedback in the order search, on half the workers (planner.py)

**Status (Sat 23:45):** no branch or PR yet. The night runs use `cdc0671` without it. A PR that passes the gate below by **08:00** gets merged and re-checked at CP5; otherwise it stays out of this hand-in.

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

**Status (Sat 23:45): go now.** `main` stays `cdc0671` for the planner: the only open merges (#23, tasks 8–10) touch `policy.py`, which the shift suite doesn't run. Run all 50 seeds (`0-49`, ~3 h), not half. Your Docker Python 3.9.25 setup is fine.

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

PR #16 (Martin's diag and scouts bench) was squash-merged on Sun 00:05 (`17739f1`). It holds no hand-in code.

---

## 5. Organiser answers: jury core count, multiprocessing, hand-in format, Python version

**Status (Sat 23:45):** still no answers; still blocking. If nothing comes by 09:00, follow the fallback in `research/ENDGAME.md` (default workers, 1-worker L4 above baseline).

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

**Status (Sat 23:50): done** on `cdc0671` (Python 3.9.6, `PLANNER_WORKERS=2`, `--jobs 4`).
- Total 101,908.6 against 63,989.4, so ×1.59.
- By level: L1 ×1.089, L2 ×1.101, L3 ×1.262, L4 ×2.130.
- 0 invalid or failed runs; slowest run 40.0 s.
- No level is below the baseline. Two seeds are a hair below it, and both reproduce exactly on re-run: L1-5010 −0.6 and L2-5031 −0.1 (task 11).

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

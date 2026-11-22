# Open tasks: final stretch (Sun 22 Nov, from 01:30)

GitHub Issues are off in this repo, so the open tasks live here. **This file is the source of truth.** The checkpoint board can't be opened from outside the owner's organisation, so not everyone can see it. Task numbers stay the same as in the PR comments. The previous version is in git history (`git show 5e7cca1:docs/TASKS.md`).

**Fixed times**
- **08:00:** review
- **08:30:** last PR opened
- **09:00:** last merge
- **10:00:** freeze (tag `handin-final`)
- **11:00:** hand-in (deadline 12:00)

**Rules for every task**
- Train seeds 0–199 only. The holdout 5000–5049 and the final set 9000–9049 are run by Mahmoud.
- Any invalid plan or failed run is a fail.
- Run timing benches on an idle machine, one at a time.
- Ship everything through a PR with CI green.
- Plain commit messages.

## Update Sun 03:00

- **#19 + #23 are merged** (main `f0a5f14`, CI green, 330 tests pass). The link-loss baseline for every gate below is now `main`.
- **#27** (polygon router note + `tools/check_routing.py`) and **#28** (Louis's opsview demo) are merged. Neither touches the hand-in code.
- **Task 11** is being built in a Claude session (branch `feature/never-below-greedy`, planner gate, PR by 08:30). Louis: skip it unless you already started; say so in the chat.
- **Tasks 8 → 12 → 9** are being built in a Claude session, one PR each, link-loss gate, last PR by 08:30. P3: claim any of them in the chat before starting so we don't do it twice.
- Still open: repo visibility (still public), shift suite (task 4: who's running it?), organiser answers (task 5).

## Where we stand (Sun 01:30)

**Planner (`main` = `5e7cca1`, hand-in code identical to `cdc0671`)**
- CP4 holdout (seeds 5000–5049): **×1.59** total, **L4 ×2.13**, 0 failures, slowest 40.0 s.
- Louis's train bench (0–49): ×1.616, 81.7 % of the upper bound.
- Two holdout seeds are a hair below the kit greedy plan: L1-5010 −0.6 and L2-5031 −0.1 (task 11).
- Squeaky Wheel and an adaptive budget were measured and dropped: noise, and 38 s is right.

**The planner isn't frozen, but any change must earn its place.** A planner change is allowed only if it fixes a real problem (failure, crash, timeout, a seed below baseline), and only through the planner gate below. Any planner change invalidates the CP4 holdout and the shift run. CP5's final set (9000–9049) is then the only unseen-seed check before the hand-in.

**Link-loss: we ship PR #19 (Martin) + PR #23 (Youcef)**

Official sizing grid (all 20 cells, 5 comm seeds), seeds 5–14 / fresh 15–24:

|  | main | #19 | #19 + #23 |
|---|---|---|---|
| Sizing score | 0.00 / 0.00 | 0.60 / 0.00 | **1.00 / 0.75** |
| Failed runs | 142 / 328 | 31 / 118 | **0 / 20** |
| Frontier, seeds 5–14 (B/s at 250/500/1000/2000 m) | none | none/100/100/100 | **50/50/50/50** |
| 1000×200 S_loss | 0.954 / 0.937 | **0.962** / 0.965 | 0.938 / 0.965 |
| Messages per aircraft per minute at 1000×200 | ~5.5 | ~8 | ~17.5 |

`check_policy` L1–L4 at 1000×200:

|  | main | #19 | #19 + #23 |
|---|---|---|---|
| Seeds 0–9, scenarios clean | – | 38/40 | 38/40 |
| Seeds 20–29, retention / failed runs / S_loss | 0.871 / 8 / 0.858 | **0.974** / 0 / **0.958** | 0.969 / 0 / 0.932 |

- **Why #23 ships:** it removes almost every failed run across the grid (a failed run scores 0), and its frontier is part of the hand-in.
- **Its cost is messages:** #23 sends twice as many, and S_loss is retention − 0.002 × messages. That's task 8. If task 8 isn't in by 08:30, the 08:00 review picks between #19 + #23 and #19 alone, with these numbers.
- **Known defects:**
  - L2-21 and L3-6 regress with #19 (task 9);
  - L4-21 regresses with #23 (task 12);
  - L3-21 enters a pop-up zone at 2000 m (task 10, dropped);
  - L1-6 also fails with the organisers' `broadcast` baseline, so we accept it.

## Who does what

### Mahmoud: owner, merges, checks, hand-in

| When | Task | Done when |
|---|---|---|
| ~~now~~ done 03:00 | **Unblock #23:** in `tests/test_policy_r8.py`, line 52 asserts `msg[0] == 4` and line 60 `msg[0] == 2` (the policy now sends lists). Then retarget #23 to `main` and merge it with a merge commit. Don't delete `feature/policy-r8` first: #19 closes as merged on its own | main CI green |
| now | Make the repo private (GitHub Settings) | The API says private |
| as PRs come in | Run the gate on every link-loss and planner PR, one bench at a time, and post the numbers on the PR | Merged or rejected with numbers |
| 08:00 | **Review:** shift results, open PRs, #19 + #23 against #19 alone | Decision posted in the chat |
| 08:00–09:00 | **Organiser answers, in person (task 5):** cores, multiprocessing allowed, hand-in format, Python version | Answers posted here |
| 09:00–09:45 | **CP5 on the candidate:** final set 9000–9049, `check_handin`, `check_policy`, both edge packs, pytest, and sizing seeds 5–24 on the final policy | 0 failures, no level below baseline |
| 09:45 | **Task 13:** write the frontier table into the hand-in README and a slide | Table from the CP5 sizing run |
| 10:00 | **Freeze:** `git tag handin-final <sha>`, post the SHA in the chat | Tag pushed |
| 10:00–10:40 | **Package from the tag** (`git archive`). Re-run `check_handin` and `check_policy` from the copy, with `/usr/bin/python3` and `env -i` | Same scores as the repo |
| 11:00 | **Hand in.** Re-download what we handed in and re-check it | Same score |

### Louis: planner, board, jury numbers

| When | Task | Done when |
|---|---|---|
| tonight, optional | **Task 11:** never below the kit baseline on a seed | Planner gate. PR by 08:30, or skip |
| tonight | **Task 4:** shift suite, only if Martin isn't running it | 0 failures, no variant below baseline, totals posted |
| morning, optional | **Task 14:** scaling re-run on the current planner | Numbers for one slide |
| morning | **Task 15:** jury presentation, with Swann | Slides and demo script use the numbers above |
| 10:00–10:40 | Second pair of eyes on the packaging | Your check matches Mahmoud's |
| 10:40 | **Live board:** submit the 8 plans regenerated from the tag | Total posted |

### P3: link-loss owner (Youcef or Martin; confirm in the chat)

`policy.py` only. One PR per task, in this order, each from `main` after #23 is merged, each passing the link-loss gate, each opened by 08:30.

| Order | Task | Done when |
|---|---|---|
| 1 | **Task 8:** cut the hover heartbeat | ≤ ~10 messages per aircraft per minute at 1000×200, S_loss ≥ 0.960 on both seed sets, failed runs no higher |
| 2 | **Task 12:** L4-21 regression in #23 | L4-21 ≥ 0.9 |
| 3 | **Task 9:** mutual hold between on-plan aircraft (L2-21), and L3-6 | L2-21 ≥ 0.9; L3-6 ≥ 0.780 if it's the same cause |

If Mahmoud builds one of these overnight, he claims it in the chat first, so P3 skips it.

## Gates

### Link-loss gate (every `policy.py` PR)
Commands, from `fleet-orchestration/fleet-kit/`:
- `python3 tools/linkloss_diag.py --policy handin/policy.py --sizing --seeds 5-14 -o runs/<name>-5-14.json`
- the same with `--seeds 15-24`
- `python3 handin/check_policy.py --levels L1,L2,L3,L4 --seeds 0-9`

Done when, compared with #19 + #23 (numbers above):
- failed runs no higher;
- sizing score no lower;
- 1000×200 S_loss higher, or the same with fewer failed runs;
- no new unclean `check_policy` scenario;
- pytest green on Python 3.9;
- step under 50 ms;
- raw JSON attached to the PR.

### Planner gate (every `planner.py` / `params.py` / `deconflict.py` / `routing.py` / `targets.py` PR)
- **Behind a flag** in `params.py`. Flag off gives byte-identical plans under `FLEET_ITERS` (test).
- **Paired and deterministic, train seeds only:**
  - `FLEET_ITERS=N PLANNER_WORKERS=2 python3 tools/bench.py --levels L4 --seeds 0-39 --base <main copy> --json …`: mean gain > 0, at most 40 % of seeds worse, 0 invalid;
  - L1–L3 seeds 0–19: mean ≥ 0, 0 invalid.
- **Timing:** `/usr/bin/python3 handin/check_handin.py` gives 8/8, max time ≤ 45 s on an idle machine.
- **Only to fix a real problem**, and Mahmoud agrees before merging.

---

## Task briefs

### 4. Shift suite in jury conditions (Martin's PC, or Louis as backup)
- **Why:** the hand-in code has never been through the shift suite in jury conditions. The last run (×2.07, 0 failures) was on `ec5c41e`, before the R8 scheduler, its cache and the greedy fallback.
- **Run:** from `fleet-kit/`, on an otherwise idle machine, with Python 3.9:
  `/usr/bin/python3 tools/shift.py --seeds 0-49 --jobs 1 --json shift_final.json`
  That's ~3 h. Use `--seeds 0-24` if it can't finish by 08:00. The suite doesn't run `policy.py`, so link-loss merges don't affect it. A planner change does.
- **Done when:** 0 failures, no variant below baseline, max time well under 60 s. Post per variant: total, ratio, failures, worst seed, max time. A crash or invalid plan: post the scenario; don't fix it yourself.

### 5. Organiser answers (Mahmoud, in person, Sunday morning)
- **Questions:**
  1. The jury machine's core count, and whether `multiprocessing` is allowed. The planner runs up to 8 workers; at 1 worker it stays valid and above baseline.
  2. The hand-in format. Plan: the whole `handin/` folder (`planner.py`, `params.py`, `fk/`, `routing.py`, `targets.py`, `deconflict.py`, `scouts.py`, `policy.py`).
  3. The Python version (we test 3.9).
  4. For link-loss, which plans the jury uses.
- **No answer by 09:00:** keep the default workers. The 1-worker L4 numbers already stay above baseline.

### 8. Link-loss: cut the hover heartbeat (P3)
- **Why:** 78 % of #23's messages are `hd+ab` heartbeats from aborted aircraft hovering in place, sent at 1 Hz while a peer is within 350 m. `ob` re-sends are another 14 %. That's ~0.02 of S_loss at 1000×200. Since #19, peers **never expire** an aborted hold, so after the first few deliveries a heartbeat only helps a peer that missed them.
- **Task:**
  - Keep the first 3 heartbeats.
  - After that, beacon only when an on-plan peer is predicted to close in. Reuse `_blocking` with a ~10 s horizon and a radius of ~2 × (d_sep + pad). Otherwise beacon every 10–15 s.
  - Check whether 1 Hz is really needed at 250 m.
  - Optional: anti-entropy only from aircraft that have an effector of that contact within range.
- **Done when:** the link-loss gate holds, messages at 1000×200 are ≤ ~10 per aircraft per minute, and S_loss at 1000×200 is ≥ 0.960 on both seed sets.

### 9. Link-loss: mutual hold between on-plan aircraft, L2-21 and L3-6 (P3)
- **Why:**
  - L2-21 (events seed 22): main 1.000, #19 and #19 + #23 **0.148**.
  - L3-6: 0.780 → 0.611.
- **What the L2-21 trace shows:**
  - Two **on-plan** aircraft, S01 and H02, hold for each other from t = 537 s until the end, 72 m apart.
  - #23's id order can't break it. H02 has the lower id, but moving would close on S01, so it yields. S01 always yields to a holding lower id.
  - Their routes pass within separation of each other's held positions, so one must **back off**. Today only aborted aircraft back off (`_blocking`).
  - Separately, L05 (C01) goes into abort mode from ~572 s. Cause unknown.
- **Task:**
  1. When two non-aborted aircraft hold for each other for more than ~10 s, the higher id backs off along its route (rate −1) if that path is clear, then resumes once the lower id has passed.
  2. Find why L05 aborts.
  3. Check whether L3-6 is the same cause.
- **Repro, from `fleet-kit/`:**
  - `python3 diag/stuck.py . handin/policy.py L2 21`
  - `python3 diag/who.py . handin/policy.py L2 21 S01,H02 535 545`
- **Done when:** L2-21 ≥ 0.9, L3-6 ≥ 0.780 if it's the same cause, and the link-loss gate holds.

### 11. Planner: never below the kit baseline on a seed (Louis, optional)
- **Why:** on the holdout, L1-5010 (79.2 against 79.8) and L2-5031 (208.7 against 208.8) score a hair under the kit greedy plan, deterministically. It's 0.7 points in total, but "never below the baseline" is a claim for the pitch.
- **Task:**
  - In `solve()`, after the last guard, call `_greedy_fallback(scenario)`, which already builds and validates the kit greedy plan (2.7 s at most on L4).
  - If its score is strictly higher, return it.
  - Add `KEEP_BETTER_GREEDY = True` to `params.py`.
  - About 6 lines, 1 h at most.
- **Done when:** the planner gate holds, and L1-5010 and L2-5031 score at least the baseline. On L1–L4 seeds 0–19 under `FLEET_ITERS`, plans are byte-identical wherever ours already beats greedy. Max time ≤ 45 s idle (the greedy adds up to 2.7 s on L4).

### 12. Link-loss: L4-21 regression in #23 (P3)
- **Why:** `check_policy` seeds 20–29, L4-21: main 0.620, #19 **0.901**, #19 + #23 **0.620**.
- **Task:** bisect #23's four additions on L4-21 (events seed 22, 1000×200, run seeds 0–1): the id order in `_r8_conflict`, the 6 s return lookahead, `SEP_PAD_M` 4.5 → 6.0, and `ob` delivery. Fix the culprit. Don't just revert it: it carries the sizing gains.
- **Done when:** L4-21 ≥ 0.9 and the link-loss gate holds.

### 13. Link-loss frontier in the hand-in (Mahmoud, at CP5)
- **Why:** LINKLOSS.md says *"the frontier is part of what you hand in"*. We have the numbers but haven't packaged them.
- **Task:** at CP5, run the sizing on the **final** policy (seeds 5–14 and 15–24). Write a short table into a hand-in README (`handin/LINKLOSS_FRONTIER.md`) and onto one slide:
  - the frontier per range;
  - the sizing score;
  - S_loss at 1000×200;
  - messages per aircraft per minute;
  - the seeds and the command.
- **Done when:** the table matches the CP5 JSON, and the file is in the tagged hand-in folder.

### 14. Scaling re-run on the current planner (Louis, optional)
- **Why:** the brief asks about larger fleets. Our scaling numbers (valid up to 500 aircraft, budget shrinking above 100) come from planner v4–v5, before the R8 scheduler.
- **Task:** `python3 tools/scaling.py` on `main` (L4 ×1 to ×4, 2 seeds) on an idle machine.
- **Done when:** a table of valid / score against baseline / time per size, for one slide. If anything fails or runs past 50 s, tell Mahmoud: that would be a real problem for the planner gate.

### 15. Jury presentation (Louis + Swann, morning; no hand-in code)
"A jury also looks at the soundness and presentation of your approach." In order:
1. **Link-loss replay in the kit viewer (zero code):** `python3 -m fleetkit view scenario.json plan.json --events events.json --policy handin/policy.py`. It shows the cut, every hold and return, and messages delivered or lost. Pick one scenario.
2. **Kit viewer playback (zero code):** play at 1–32×, scrubber, altitude strip.
3. **Greedy against ours, side by side**, on the demo seed: the ×2.13 story on L4.
4. **Numbers:** CP4 holdout ×1.59 / L4 ×2.13 (unseen seeds), and Louis's bench ×1.616 / 81.7 % of the bound. Drop the old 71.4 % / 79.4 %. Add Louis's budget curve: 38 s, with +0.12 % at 45 s.
5. **Robustness page:** the shift results (task 4) plus the green CI run (both edge packs), and the frontier table (task 13).
6. **Optional:**
   - a convergence curve, offline: `FLEET_ITERS` 1/2/4/8/16 on one L4 seed;
   - a scout-use table (assigned against idle scouts on the demo seed).

## Done or dropped (details in git history)
- **Done:**
  - CP4 holdout (task 6);
  - Squeaky Wheel measured (task 3);
  - budget curve;
  - link-loss tasks 1, 2 and 7 (in #19 + #23);
  - PR #16 merged.
- **Dropped:**
  - task 3 (Squeaky Wheel: +0.13 %, noise);
  - task 10 (L3-21: one case, at 2000 m only);
  - the adaptive budget;
  - the auto-generated adversarial scenario;
  - the `--verify` bonus (separate board, not in the ranking).

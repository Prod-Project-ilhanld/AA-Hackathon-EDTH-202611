# Roadmap: SUB-15 Fleet Orchestration

Written Sat 21 Nov 00:30. Revised after review rounds; history in research/reviews/LOG.md (reviewers: don't read it).
**Hand-in deadline Sun 22 Nov 12:00, we hand in at 11:00.** About 33 hours left.
Rules and background: [PLAN.md](PLAN.md), [KIT_NOTES.md](KIT_NOTES.md), [research/](research/) .

## 0. Status and paths in this repo (Sat 21 Nov, 03:00) — read first
- **Track 1 is Louis's planner** (`fleet-orchestration/fleet-kit/handin/planner.py`, with 7thwardlord1's `routing.py`): restarts + hill-climb over the contact order on all cores, pre-filtered validation, 3D minimum-energy routing. Measured the jury's way (fresh copy, Python 3.9.6, 60 s, official validator) on L1–L4 seeds 0–1: **3,795.6 vs baseline 2,748.6 (+38%), L4 +72% / +91%, 0 failures**. Not yet measured on holdout seeds.
- **Hardened (rule 10):** empty plan first, atomic writes, `setitimer` alarm that writes the last validated plan, catch-all, exit 0, budget counted from process start, kit helpers vendored in `handin/fk/`, final check with the jury's own validator.
- **Track 2 as written in §6 is parked.** The team's architecture (Louis's planner + `routing.py`) is working; §6 stays as a reference for improving it. Improvements now go into `planner.py` / `routing.py` as measured levers (WS0 list).
- **Paths:** everything in this roadmap that says `handin/` means `fleet-orchestration/fleet-kit/handin/`. `tools/check.py` + `tools/bench.py` are now one tool: `fleet-orchestration/fleet-kit/tools/bench.py` (fresh copy like the jury, `--python /usr/bin/python3`). The kit itself is part of this repo, so no separate `kit/` clone is needed.
- **CI** (`.github/workflows/ci.yml`) runs on every PR and push to `main`: Python 3.9 compile, hand-in rules, unit tests, a jury-style run on L1–L3.

## 1. Vision
> A planner that **never scores zero**, **serves far more targets on L3/L4**, and **can explain every decision**, proven by numbers on scenarios we never tuned on.

**North-star metric (the only number that decides):**
`holdout total` = sum of official scores over 50 holdout seeds per level (seeds 5000–5049, L1–L4), with **0 failures** and **slowest run < 50 s** with the search budget `params.BUDGET_S` (default 40 s from process start) on the slowest team laptop, measured while that laptop is idle. That mirrors the jury: raw sum, unseen scenarios, 60 s cap.

Secondary: live board total (8 public scenarios, no time limit), and jury impression (method + demo).

### Where the points are (from instrumented review runs; R7 and light/heavy counts re-checked by us, the bound and R8 shares not yet scripted)
- **L4 holds ~84% of the headroom.** Rough upper bound on mean net score: L1 115 vs baseline 101 · L2 286 vs 232 · L3 537 vs 379 · **L4 ~1,620 vs 472**. The bound ignores R8, scout time and timing, so it is loose.
- **At L4, light effectors are the scarce resource:** unblocked hostiles need 49–86 lights (supply 50) but only 10–25 heavies (supply 35).
- **Scouts are idle:** the baseline flies 4–7 of 15 scouts at L4 because "3 nearest scouts" is the same 3 every time (all homes sit in one 100 m pad grid).
- **R8 separation is the main wall:** it causes ~69% of the baseline's rejected candidates at L4, 61% of them within 300 m of the pads.
- **R7 blocks 6–17 of 50 hostiles at L4.** Skip them up front.

### Three seed sets
| Set | Seeds | Used for | Who may look |
|---|---|---|---|
| train | 0–199 | every day-to-day decision, tuning, merges, agent loops | everyone, any time |
| holdout | 5000–5049 | checkpoint verdicts (CP1–CP4) | integrator, at checkpoints only |
| final | 9000–9049 | one confirmation run at CP5 | integrator, once |
| shift | 0–49 per variant | robustness only, never tuning: `battery=(40,70)`, `points_per_need=15`, `ensure_feasible=False`, L3 counts in the L4 area, L4 with half the scouts (built by copying `LEVELS` entries in `tools/`, no kit edit) | everyone |

The official README promises the same **rules, score and validator** on hidden scenarios, not the same four generator levels; the generator already has unused `battery` and `points_per_need` hooks. The shift suite guards against that.

Never tune on the 8 board scenarios. If holdout stops tracking train, we're overfitting: stop and simplify.

## 2. Ground rules (how 6 people + agents work without breaking each other)
1. **Locked evaluator.** `kit/` is never edited. `tools/bench.py` and `tools/check.py` are the only judges, owned by E, and changed only by E. No agent may edit them (an agent that can edit the scorer can fake a perfect score).
2. **One owner per file.** Others ask the owner, or open a PR the owner reviews.
3. **Contract first.** `handin/state.py` and the module signatures in §6 are agreed at CP0. Changing a signature = message the team before doing it.
4. **Every merge is gated by the bench.** A PR shows `bench.py --suite quick` plus its target level, before and after, in deterministic mode. PRs touching L4 behaviour show a **paired** comparison on ≥ 20 L4 train seeds (per-seed delta, mean, seeds worse). Merge only if the paired mean delta > 0 **and** at most 40% of seeds are worse (or mean delta > 2× its standard error), with 0 failures.
5. **Merge windows** every 2 h on the hour (10:00, 12:00, …). A (integrator) merges, runs `git -C kit pull` (the jury uses the official, possibly updated, fleetkit), then the full `bench.py --suite train` on `main`, and posts the number in the team chat.
6. **Python 3.9 + standard library only** in `handin/`. Type hints from `typing` (`Dict`, `List`, `Optional`), never `list[dict]` or `X | None`. `tools/` can use anything. **Never branch on `scenario.level`**: derive every parameter from scenario features (counts, area, horizon). Unknown keys, an unknown level string or a non-empty `events` list must not crash. **Import only public kit names:** `handin/` imports `fleetkit.model`, `fleetkit.validator.validate` and `fleetkit.scorer.evaluate`, only inside `guard.py`, inside `try/except`. Everything else we use from the kit (geometry, energy, separation, the baseline) is **vendored** into `handin/fk/` (never named `fleetkit`); if the official import fails, the guard validates with the vendored copy. The empty plan is written **before** any `fleetkit` import.
7. **Two tracks.** **Track 1** = `handin/v1_greedy.py`, a vendored copy of the kit baseline with targeted fixes, each behind a flag in `params.py`. It is the hand-in path from CP1 on. **Track 2** = the `state.py` pipeline (§6). `planner.py` builds Track 1 first. When `USE_V2` is on and time allows, it also builds Track 2, and `guard.finalize` keeps the best officially valid candidate (at L1–L3 both always run; at L4 the budget split comes from measured times). **Smoke test at 11:00:** `to_plan()` of a state holding one hand-inserted bundle passes official `validate()`. Track 2 modules are unit-tested in isolation, not flag-merged into Track 1. **Track 2 go/no-go at CP2 (13:00):** `bundle.insert` must produce officially valid L4 plans on 5 train seeds **scoring at least the baseline on each**. If not, B and C move to Track 1 levers (scout tours, strike groups, shadow prices on waypoint dicts) and Track 2 stops.
8. **Deterministic comparisons, idle timing.** Compare changes with a fixed iteration count passed by the environment variable `FLEET_ITERS` (never by argv: the jury calls with exactly two arguments), not by wall clock. No iteration over `set`s in `handin/` (use `sorted()` or dicts): string hashing is randomised per process. Every `random.Random` is seeded from the scenario seed. Timing runs use ≤ 4 workers (the laptops have 4 performance cores) on the reserved idle laptop.
9. **Agents work in their own git worktree and branch, on one owned file, only while its owner is not editing it.** The owner hands the file to a loop at a merge window and takes it back at the next one. A human owner reviews before anything reaches `main`.
10. **The planner can't score zero by accident** (CP1 items in §5): empty plan written first, every write atomic (`.tmp` + `os.replace`), everything inside `try/except BaseException`, `SIGALRM` backstop that writes the pre-serialised last validated plan and calls `os._exit(0)`, anytime builders, never a negative score.
11. **One search for both tracks.** `search.improve` runs ALNS over the **contact insertion order** (plus per-contact knobs) around any builder: Track 1's greedy or Track 2's `bundle.insert` loop. Whichever track wins CP3, the search and its operators still apply.

## 3. Workstreams
| WS | Owner | Files (writes) | Mission | Hands off to |
|---|---|---|---|---|
| WS0 Baseline++ (Track 1) | F until CP2, then A | `handin/v1_greedy.py` | Anytime clock first (CP1: check the deadline between contacts, stop with the valid plan so far). **Before CP2, only:** A's delta validation, idle scouts first, R7 skip, **best-index scout insertion** (try every position in the scout's task list, keep the cheapest that passes delta validation, which then re-checks R4/R9 for every contact on that scout; the baseline only appends, so tours run in points order), D's departure scheduler + diagonal climb-out, B's light/heavy prices. **After CP2, one lever per lane-L loop, merged by A:** `SPEED_FACTOR` 0.999 with times rounded up, final dive straight from cruise when no zone is in the way, observe from up to 150 m 3D, back-to-back observes from one point for clustered contacts, lowest cruise layer that clears zones on the path (flying exactly at a ceiling is legal), far clusters to high-reach scouts (`reach = min(v·(H − obs − climb)/2, usable_Wh·3600/(p0/v + k_v·v)/2)`), strikes at the earliest slot-feasible T, prefix snapshots; then `search.improve` over the order | A at CP2 |
| WS1 Core | A | `handin/planner.py`, `state.py` (data structures), `guard.py`, `params.py`, `handin/fk/` (vendored kit helpers) | Safety skeleton (rule 10), contract, snapshot/restore, flags, integration, final hand-in; **delta validation** (`handin/fk/delta.py`: R1–R3/R6 per new route, R8 new-vs-existing via `separation_item`/`separation_violation`, R4/R9/R10 for every contact on a touched route), used by Track 1 and `deconflict`, ready by 11:00 | everyone |
| WS2 Assignment | B | `handin/prep.py`, `bundle.py`, `strikes.py`, `state.retime`; ALNS operators | R7 pruning, 2-D knapsack shadow prices (light vs heavy), bundle insert/remove (unknowns = scout slot only), `state.retime` (STN coupling across a bundle), strike group + shared strike time (R4/R10) with members separated by **one altitude layer per member (30/70/110/150 m; needs are at most 4; layer order by `e_climb`, lights highest, heavies lowest)**, or a column on one path **ordered slowest first** (a faster leader is overtaken outside the 100 m exemption: 35 vs 28 m/s with 3 s spacing meet 420 m out); approach angles ≥ 30° only as a final tie-breaker (23° gives 39.9 m at the 100 m circle); from 19:00 order-level ALNS operators (random, cluster, worst-profit, related-by-window); route-level SISR operators are a stretch goal after CP4 | WS4, WS5 |
| WS3 Routes | C | `handin/routing.py`, `scouts.py` | Paths with a leg cache keyed by `(p0, p1, z)`, visit slack (O(1) pre-filter; R8 still checked by `deconflict`), scout tours: **every scout is a candidate**, cheapest insertion first, unknowns interleaved with hostiles by profit per scout-second, per-scout reach (round trip within horizon and battery), observation points on the side away from the effectors' approach; altitude is a tuning knob, not "always ≥ 125 m" | WS2, WS4 |
| WS4 Airspace | D | `handin/deconflict.py`; runs `tools/tune.py` from CP0 | **Phase 1 (by CP2):** departure scheduler: each aircraft takes the **earliest R8-free take-off time** (next candidate = end of the earliest conflict interval from `close_intervals`, official `separation_violation` on the aircraft's **whole route** vs every route already scheduled, in order of strike time, earliest T first; inside a rebuild only the inserted bundle is scheduled against the fixed rest) with a **diagonal climb-out** (leave the pad along the heading while climbing); effector choice within a subtype prefers pads facing the target; effectors work in strike-time space (a later take-off shifts T for the whole bundle via `state.retime`, or Track 1's arrive-time loop). Measured by reviewers: a fixed 3 s stagger leaves 18–65 conflicts; climb-out-only checks leave 19–31 en-route conflicts (overtaking); full-route checks leave 0, last effector airborne at 162–196 s, ~1 s of CPU. Landing reservations for returning scouts, incremental `conflicts()` on the official `separation_violation`. Usable by Track 1 too. **Phase 2 (by CP3):** repair order ground delay → altitude by heading sector **and speed class** (sectors don't stop overtaking) → detour; strike-time ordering inside a cluster (different contacts get no R8 exemption) | WS0, WS1 |
| WS5 Eval + Search | E | `tools/bench.py`, `tools/check.py`, `tools/tune.py` (writes), `tools/loop/`, `tools/edge/`, `tools/shift/`, `handin/search.py` | The judge, tuning tool, agent-loop template, edge-case pack, shift suite, track-agnostic ALNS frame (operators come from B) | everyone |
| WS6 Story | F (from CP2) | `tools/demo/`, `tools/bound.py`, `research/`, pitch deck | drop-reason log per contact (why served or dropped: R7, light price, window, scout reach, R8 slot; data from B), `bound.py` after CP2 (per-level rough upper bound, for the jury), budget curve at CP4 (holdout total at 20/30/40/45 s), robustness slide, viewer layers, explanations, scaling chart, board submissions; link-loss **watch only**: no code unless the organisers say it scores | jury |

Why F owns Track 1 until CP2: B already carries three critical-path files, and the demo work peaks after CP3.

### Research inputs per workstream ([research/TOP10.md](research/TOP10.md))
| WS | Take | From (TOP10 #) | Effort |
|---|---|---|---|
| WS2 | **Bundle insertion:** observation + all required effectors inserted together or not at all; one common strike time T ≥ obs end + 10 s, spread ≤ 20 s; early arrivals absorbed by take-off delay (R4/R10 correct by construction) | #4 sync-VRP / STN | 5 h |
| WS2 | **Target selection with shadow prices:** 2-D 0/1 knapsack (light ≤ nL, heavy ≤ nH, value = points − 10·n − energy estimate) over reachable, R7-unblocked hostiles; gives the shortlist and a per-subtype price for insertion and acceptance | review change 3 (+ #7 Santini ideas, GPL: write from the paper) | 1–2 h |
| WS3 | **O(1) insertion checks** with `wait`/`maxShift` per scout visit, plus an energy slack; insert by `profit² / shift` | #3 Vansteenwegen TOPTW | 3 h |
| WS3 + WS5 | **Granular neighbourhoods:** precompute the 20 nearest contacts per contact in `prep`; only try moves among them | #5 HGS / PyVRP | 2 h |
| WS4 | **Earliest-free departure on the whole route + diagonal climb-out**, then ground delay of the whole bundle, then altitude by heading sector, then detour | #6 NASA ground delay + SIPP, review rounds | 4 h |
| WS5 | **ALNS frame** ported from N-Wouda/ALNS (MIT): roulette wheel `w ← decay·w + (1−decay)·score`, simulated annealing with autofit temperature, max runtime | #1 | 3 h |
| WS2 | **Order-level operators** first (random, cluster, worst-profit, related-by-window); jsprit-style route-level radial/worst/SISR ruin + regret-2 insertion as a stretch goal after CP4 | #2 jsprit + SISR | 2 h (+4 h stretch) |
| WS6 | **Link-loss:** watch only. If it ships and scores: CBBA port (MIT), event-driven messages, sizing curve, A/B framing | #8, #9 | — |

Excluded on purpose: learned solvers (RL4CO, RouteFinder, POMO): torch + GPU, no sync or separation, worse than LNS in 60 s; the verify bonus (own board, doesn't change the ranking); `LOW_STRIKE`, the 2-waypoint sub-30 m strike (≤ 0.5 pt per effector over a 30 m layer, loophole risk). Both make good "why not" slides.

## 4. Agent lanes (use the compute)
| Lane | What runs | Driven by | Starts | Guardrails |
|---|---|---|---|---|
| **T: tuning** | `tools/tune.py`: random search + successive halving over `params.py`, paired seeds, deterministic mode | E builds; **D runs from CP0** on Track 1; spare laptops | once `tune.py` exists (if not by 05:00, from 09:00): Track 1 flags and constants; CP2: Track 2 | Train seeds only; holdout confirms at checkpoints; 0 failures; timing re-checked on the idle laptop |
| **L: eval loops** (autoresearch style) | One Claude session per file, in its own worktree: edit the owned file → `bench.py --suite quick` with `FLEET_ITERS` → keep the commit if better, `git reset` if not → repeat | the file's owner hands it over at a merge window | **CP1 on `v1_greedy.py`** (Track 1 exists early); Track 2 files after CP2 | One file and **one named lever from the WS0 list per loop** (no open exploration: an L4 try costs minutes), owner not editing it meanwhile; can't touch `tools/`, `kit/`, seeds; a kept commit must also beat `main` on a paired ≥ 20-seed train run before its PR; one PR per window; logs every try to `runs/loop-<file>.tsv` |
| **B: board** | Offline long runs (no 60 s cap) of our best planner on the 8 public scenarios, then `submit-all` | F | when the token arrives (not scheduled overnight) | Board ≠ final ranking; never tune on these 8 |
| **R: review** | `/code-review` or `ponytail-review` on each PR, plus `check.py --python /usr/bin/python3` | integrator A | every merge window | Findings go to the file owner |
| **S: research** | The prior-art and review sessions | F triages | done, on call | Ideas only unless licence is MIT/BSD/Apache and code is stdlib |

Lane V (OpenEvolve) is cut: lowest value per hour; T and L cover it.

Loop prompt template (lane L), kept in `tools/loop/program.md`:
```
You may edit only handin/<file>.py. Goal: raise `FLEET_ITERS=200 python3 tools/bench.py --suite quick --json`
total with failures == 0. After each change: run the bench; if better, git commit with the numbers in the
message; if not, git reset --hard. Never edit tools/, kit/ or other handin files. Never iterate over sets.
Stop after N tries or at <time>. Log each try to runs/loop-<file>.tsv: time, idea, total, failures, kept.
Before handing back: run a paired train comparison (>= 20 L4 seeds) of your best commit vs main; report both.
```

## 5. Phases and checkpoints
Each checkpoint has a **verification command** and **pass criteria**. If a checkpoint fails, we fix it before moving on; nobody starts the next phase's risky work on a red `main`.

| CP | When | Deliverable | Verify with | Pass criteria |
|---|---|---|---|---|
| **CP0 Foundations** | Sat 03:00 (hard limit 05:00, before anyone sleeps) | Private GitHub repo; **Track 1 seams** agreed (`params.py`, guard API, `deconflict` on waypoint dicts); `state.py` v1 with mutators agreed at **09:00** after sleep; `params.py` with flags; `tools/bench.py` **v0** (= `check.py` logic + parallel runs + `--json` + quick suite + paired delta vs cached baseline); `tools/loop/program.md` | `python3 tools/bench.py --suite quick` | Runs end to end, prints total, per level, paired delta, failures by type, slowest |
| **CP1 Safe skeleton** | Sat 03:00 (hard limit 05:00) | `planner.py`: (1) writes `{"seed": s, "routes": []}` at once, every write atomic (`.tmp` + `os.replace`); (2) body in `try/except BaseException`, always writes the best validated plan, exits 0; (3) `signal.setitimer(ITIMER_REAL, 52 − elapsed since process start)` when available, the handler writes the pre-serialised last validated plan under its own temp name (`plan.json.alarm.tmp`) and calls `os._exit(0)`; (4) deadline relative to process start, reserve ≥ 3× slowest iteration + validate + write; (5) empty plan if the best score is < 0; (6) incumbent re-validated with the official `validate()` at most once every 2 s and always before the final write (measured 11–13 ms at ~40 routes; expect ~60 ms at 90 routes); (7) the greedy builder checks the deadline between contacts and returns the valid partial plan. Track 1 = vendored baseline, flags off; official kit imported only in the guard, after the empty plan is written | `check.py --python /usr/bin/python3 --levels L1,L2,L3,L4 --seeds 0-2`; `FLEET_INJECT_FAIL=1` run; `FLEET_DEADLINE=3` on L4 seed 3; `FLEET_INJECT_HANG=1 FLEET_ALARM_S=5` on L4 seed 3; official kit missing from `PYTHONPATH`; two runs with different `PYTHONHASHSEED` and the same `FLEET_ITERS` | 0 failures; scores equal the baseline; injected failure still gives a valid plan; 3 s deadline gives a valid plan in < 4 s; the hang gives a valid non-empty plan via the alarm in < 6 s; missing kit still exits 0 with a valid plan; byte-identical plans; `grep -n "\.level" handin/` empty; slowest L4 time recorded as the reserve reference |
| — | overnight | Lane L on `v1_greedy.py`: **one lever at a time** (or each lever in its own function block) so the 08:00 merge isn't a single-file conflict storm, starting with best-index scout insertion; lane T only if `tune.py` exists by 05:00. **Fallback:** if CP1 isn't green by 05:00, `main` gets the plain kit template (`greedy_plan` + empty plan first + catch-all) so a non-zero hand-in exists from tonight | logs | Kept changes beat `main` on paired train |
| **CP2 v1 beats baseline** | Sat 13:00 | Track 1 with delta validation, idle scouts, R7 skip, shadow prices, departure scheduler (WS4 Phase 1); `bench.py` v1 with the shift suite and the edge pack; Track 2 go/no-go | `bench.py --suite holdout` with `FLEET_ITERS`, then wall-clock on the idle laptop; shift suite | Holdout total ≥ **+25%** vs baseline and **L4 ≥ +35%** (one line, idle scouts, already measured +37% on 4 L4 seeds), no level below baseline, edge pack 0 failures, 0 failures, slowest < 50 s (budget 40 s); shift suite 0 failures and no variant below baseline |
| **CP3 L4 at scale** | Sat 19:00 | WS4 Phase 2; Track 2 end to end behind `USE_V2`; guard with one full `validate()` at the end | `bench.py --suite holdout --levels L4`, timing on the idle laptop | L4 holdout **score ≥ 1.8× baseline** (≈ 850 mean); slowest < 50 s (budget 40 s); shift suite 0 failures and no variant below baseline. Whichever track wins is the hand-in path |
| **CP3.5 Demo dry run** | Sat 22:00 | Viewer before/after, numbers table with "% of bound per level", method slide, explanations | Full run-through with the team | Under the pitch time limit; everyone can answer "why this target?" |
| **CP4 Search + tuned** | Sun 01:00 | `search.improve` (order-level ALNS) on the winning track; tuned `params.py`; budget curve (20/30/40/45 s) | `bench.py --suite holdout` with `FLEET_ITERS`, then wall-clock on the idle laptop; shift suite | Holdout gain over CP3 ≥ **+5%**, 0 failures, slowest < 50 s (budget 40 s); shift suite as CP3. If 40 s is within ~1% of 45 s, use 40 s |
| — | overnight | Lanes T and L on all spare machines | logs | Owners review kept commits at 08:00 |
| **CP5 Freeze** | Sun 10:00 | Final `params.py`, no new features after this | `check.py --python /usr/bin/python3 --levels L1,L2,L3,L4 --seeds 9000-9049` (final set) on the idle slowest laptop, plus the edge pack | 0 failures, slowest < 50 s (budget 40 s), total in line with holdout |
| **CP6 Hand-in** | Sun 11:00 | Hand-in delivered in the organisers' format | Re-download what we handed in, run `check.py` on it | Same score as CP5 |

Targets (+25% / L4 +35%, 1.8×, +5%) are goals, not measurements. Adjust them at each checkpoint from the real numbers.

### Hour by hour
| Time | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| Sat 00:30–03:00 (≤ 05:00) | repo, safety skeleton, contract v1 | agree contract, start `prep` (R7, knapsack) | agree contract, start `routing` | agree contract, prototype the earliest-free departure scheduler | `bench.py` v0, edge pack, loop template, `tune.py` v0 if time | vendor Track 1, anytime clock, first two flags (idle scouts, R7) |
| overnight | — | — | — | lane T if `tune.py` exists | lane L on `v1_greedy.py` (one lever at a time) | — |
| Sat 09:00–13:00 | integrate, merge windows, **delta validation** | `prep`, `bundle`, `strikes`, `state.retime` | `routing`, `scouts` (slack, reach) | departure scheduler + landing reservations (Track 1 first) | `bench.py` v1, paired stats, shift suite | Track 1: delta validation, shadow prices, scheduler, cheap-points flags |
| Sat 13:00–19:00 | take over Track 1 | shared strike time, group separation | clustered observations, granular lists | Phase 2 repairs, cluster strike order | `search.py` frame, lane L on Track 2 | viewer layers, scaling chart, pitch draft |
| Sat 19:00–01:00 | integrate, pick winning track | order-level ALNS operators | routing speed, leg cache | conflict-aware insertion, tuning | ALNS acceptance, integration | `bound.py`, CP3.5 dry run at 22:00 |
| overnight | — | — | — | lanes T on all machines | lane L | — |
| Sun 08:00–10:00 | pick best, freeze | review loop commits | review loop commits | review tuning results | final holdout runs | final demo |
| Sun 10:00–11:00 | CP5 + hand-in | QA | QA | QA | QA | pitch rehearsal |

Sleep in shifts: at least two people fresh for Sunday 08:00–11:00 (A and E).

## 6. The contract (Track 2; agree at CP0, then code against it)
The plan is held as **visit sequences with time slack plus per-aircraft timing parameters**, not as waypoint JSON. Waypoints are generated once, at the end, by `routing.timed()` inside `to_plan()`. Detours are not stored as visits (that would break O(1) insertion); `routing` caches legs by `(p0, p1, z)`.

`handin/state.py`:
```python
class Visit:                          # one stop in an aircraft's sequence
    contact: Optional[str]            # None for home
    action: Optional[str]             # "observe" | "engage" | None
    pos: Tuple[float, float, float]   # observation or engagement point (consecutive visits may share a pos)
    dwell: float                      # hover time here (observe: >= obs_dwell_s)
    earliest: float; latest: float    # feasible arrival interval (windows, R4/R10 links)
    slack: float                      # maxShift: how much later this visit may still happen
    energy_left: float                # Wh still available after this visit

class PlanState:
    sc: Scenario                              # from handin/fk/model.py (vendored); the guard builds the official Scenario itself
    seq: Dict[str, List[Visit]]               # aircraft id -> visit sequence
    depart: Dict[str, float]                  # take-off time, scouts only (ground delay lives here); effectors are anchored at bundles[cid]['t_strike']
    cruise_z: Dict[str, float]                # cruise altitude (altitude repair lives here)
    speed: Dict[str, float]                   # cruise speed (effectors: v_h; scouts: tuned)
    approach: Dict[str, dict]                 # keys fixed at CP0: heading_deg, climb_dir_deg, layer_z, via: List[point]; written only by deconflict, read only by routing
    bundles: Dict[str, dict]                  # contact id -> {"scout": id, "effectors": [ids], "t_obs_end": float, "t_strike": float}
    pool: Dict[str, None]                     # unserved contacts, insertion-ordered (never a set)
    def free(self, kind: str) -> List[str]    # "scout" | "light" | "heavy": aircraft that can still take work
    def pieces(self, aid: str) -> list        # cached timed pieces (fleetkit Piece tuples); invalidated on change
    def retime(self, aid: str) -> Optional[List[str]]   # recompute times/slack of one aircraft AND every bundle it is in (STN); None if infeasible, else the touched aircraft
    def snapshot(self, aids: List[str]) -> dict    # copy seq/depart/cruise_z/speed/approach of the touched aircraft (2–5 per bundle move)
    def restore(self, snap: dict) -> None          # undo a rejected move
    # mutators (the only way modules change the plan)
    def insert_visit(self, aid: str, index: int, visit: Visit) -> None
    def remove_visit(self, aid: str, index: int) -> Visit
    def set_depart(self, aid: str, t: float) -> None
    def set_cruise_z(self, aid: str, z: float) -> None
    def set_speed(self, aid: str, v: float) -> None
    def set_strike_time(self, contact_id: str, t: float) -> None
    def set_approach(self, aid: str, approach: dict) -> None
    def estimate(self) -> float               # fast score from cached pieces(): points − 0.5·energy − 10·effectors; never calls to_plan()
    def to_plan(self) -> dict                 # {"seed", "routes": [...]} via routing.timed(), ready for validate()
```
Owners: A owns the `state.py` data structures; **B owns `retime` and slack propagation** (the bundle/strike coupling). `scouts`/`strikes` read slack and never compute cross-aircraft coupling themselves. **For effectors `depart` is derived** (`depart = T − flight time`): ground delay of an effector = shifting T for its whole bundle via `retime`, or flying slower. `deconflict.fix` changes `depart` (scouts), T (via `retime`), `cruise_z`, `speed` and detours, through `state` setters. **Slack checks are necessary, not sufficient:** every `retime` returns the touched aircraft, and `deconflict.conflicts` runs on them before a move is kept.

Module entry points (each owner may add private helpers freely):
```python
prep.analyse(sc, params) -> Prep                         # R7 blocked set, knapsack shortlist + light/heavy shadow prices, per-scout reach, k-nearest lists
routing.path(p0, p1, z, sc, params) -> List[point]       # zone/protected-area-safe polyline, cached
routing.timed(aircraft, visits, z, speed, params, depart=None, arrive=None, approach=None) -> List[dict]   # exactly one of depart / arrive   # waypoints with feasible times (R2, R3); `pieces()` caches its result per aircraft
scouts.best_slot(state, prep, contact_id, params) -> Optional[dict]   # cheapest observation slot over ALL scouts
strikes.best_group(state, prep, contact_id, t_obs_end, params) -> Optional[dict]  # effectors + shared strike time T (R4, R9, R10)
bundle.insert(state, prep, contact_id, params) -> bool   # hostile: scout slot + strike group; unknown: scout slot only; all or nothing
bundle.remove(state, contact_id) -> None                 # removes the bundle, calls state.retime on touched aircraft
deconflict.slots(state, params) -> None                  # departure slot table + landing reservations
deconflict.conflicts(state, aircraft_ids) -> List[tuple] # pairwise R8 for the touched aircraft vs the rest (uses state.pieces)
deconflict.fix(state, aircraft_ids, params) -> bool      # ground delay → altitude → detour
search.improve(build, order, params, deadline, iters=None) -> (plan, score)   # ALNS over the contact order (+ per-contact knobs); build(order) is Track 1's greedy or Track 2's bundle.insert loop
guard.finalize(sc, candidates) -> dict                   # best plan that passes official validate(), never negative
```

## 7. `tools/bench.py` spec (so E builds what everyone needs)
- **v0 (CP0):** `check.py` logic + `multiprocessing` + `--json` + `quick` suite (5 train seeds × 4 levels) + paired per-seed delta vs cached baseline + `guard_fallbacks` count (incumbent rejected by official `validate()`; **> 0 on train fails the merge gate**). The planner reports it through a one-line JSON on stderr.
- **v1 (CP2):** suites `quick`, `train` (50 × 4 from seeds 0–199), `holdout` (50 × 4, 5000–5049), `final` (50 × 4, 9000–9049, integrator only); `--levels`; `--paired N` (N seeds of one level, per-seed deltas, seeds worse); passes `FLEET_ITERS` and a random `PYTHONHASHSEED` explicitly in the subprocess environment (`check.py` builds the environment from scratch, so nothing else gets through); baseline scores cached in `runs/baseline_cache.json`; prints "% of bound" per level from `bound.py`.
- Runs `handin/planner.py` as a **subprocess** per scenario (like the jury), 60 s timeout, official `evaluate()`, scenarios from `generate(level, seed)` (default `ensure_feasible=True`, like the jury; `fleetkit stats` uses `False`).
- Workers: 8 in `FLEET_ITERS` mode, ≤ 4 for any wall-clock or timing run.
- Runtime: `train` ≈ 17 min if every run uses its ~40 s budget (200 runs ÷ 8 workers); planners stop early once converged on L1/L2. PRs use `quick` + their level (+ paired L4); the integrator runs `train` at merge windows.
- Suite `shift` (§1) and `--edge` (the edge pack in `tools/edge/`): no scouts; no effectors of one subtype; every hostile R7-blocked; every window closed before any aircraft can arrive; horizon 120 s; a single aircraft; `battery_pct` = 5; an unknown `level` string; extra unknown keys; non-empty `events`; `engage_needs` with a 0 count; an unknown with `window_s: null`; `--no-check` generator output. Pass = 0 failures, never a negative score.
- Exit code 1 on any failure.

## 8. Risks and what we do about them
| Risk | Watch | Response |
|---|---|---|
| Invalid plan, crash or negative score on a hidden scenario | bench failures, edge pack | Rule 10: empty plan first, catch-all, exit 0, guard keeps the best validated plan, never negative |
| Timeout or torn write on the jury machine | slowest time on the idle laptop; `FLEET_DEADLINE` test | Deadline from process start, measured reserve, anytime builders, atomic writes, `SIGALRM` writes the pre-serialised plan and exits; the kit baseline alone takes 1.1–15 s at L4, so Track 1 replaces it rather than running after it |
| Jury's `fleetkit` API differs (kit updated) | `git -C kit pull` diff at merge windows | Only 3 public names imported, inside the guard's `try`; vendored copies for everything else; empty plan written before the import |
| Hidden scenarios differ from the public levels | shift suite | No branching on `scenario.level`; feature-derived parameters; shift suite 0 failures at every CP |
| Track 1 tweak worse on some seeds | paired per-seed deltas | Measured −12.5% on one of 4 seeds: when time allows (L1–L3), run both and keep the better; at L4, decide from measured times |
| Python 3.10+ syntax slips in | `check.py --python /usr/bin/python3` | Run it at every merge window |
| Overfitting train or holdout | train vs holdout vs final gap | Three seed sets; holdout only at checkpoints, final once |
| Noisy comparisons | same change, different results | `FLEET_ITERS` mode, no set iteration, paired ≥ 20-seed comparisons for L4 |
| Track 2 late | CP3 | Track 1 stays the hand-in path; Track 2 only replaces it when it wins |
| Agent loop collides with its owner | merge conflicts | Owner hands the file over at a merge window |
| Kit updated by the organisers | `git -C kit pull` at merge windows | Rerun `check.py` and the edge pack after any update |
| Link-loss part ships late | kit pull, organisers | Watch only; code only if it scores and CP3 is green |
| Agent loops game the metric | locked evaluator | Agents can't edit `tools/`; kept commits must beat `main` on paired train; humans review |
| E or B overloaded | hour table | Track 1 to F until CP2; tuning runs to D; operators to B only after 19:00 |
| Burnout before Sunday | — | Shifts; A and E sleep before 08:00 |

## 9. Sources for the loop patterns
- Karpathy's autoresearch: agent edits one file, runs a fixed eval, commits if better, resets if not; the eval stays locked. [DataCamp guide](https://www.datacamp.com/tutorial/guide-to-autoresearch)
- OpenEvolve, open-source AlphaEvolve: LLM evolves code judged by an automated evaluator; used on TSP solvers, not yet on VRP. [Hugging Face write-up](https://huggingface.co/blog/codelion/openevolve)
- PyVRP (1st at EURO meets NeurIPS 2022 VRP): reference design for routing heuristics. Ideas only, C++ core.

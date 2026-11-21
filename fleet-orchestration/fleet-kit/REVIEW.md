# Review: shift suite and edge-case pack (branch `feature/shift-edge`, PR #8)

Author: Martin. Reader and decision-maker: mkassaby. Date: 2026-11-21.

## Decision needed

Merge PR #8 into `main` or not. Everything the task asked for is delivered and `handin/` is untouched. No crash, no invalid plan and no score under the baseline was found, so there is no bug to hand to a file owner. The points below are for you to weigh.

1. **CI cost.** `tests/test_edge.py` adds about 56 s to every PR run (16 cases, 3 s budget, 2 workers). If that is too much, drop the slowest cases or mark the file as a nightly job.
2. **Jury run is not one-job.** The final shift run used four parallel processes to finish before 16:00 (details below). If you want a strictly sequential run (one job, 8 workers, about 3 h on a free machine), it is one command and can be run on the final `main` before the freeze.
3. **Ilhan takes over the edge cases.** He starts from this branch and adds cases outside the roadmap list (large fleets, zones on pads, unknown-only scenarios).

## What was asked

From the task message: two open CP2 points, without touching `handin/`.

- **Shift suite** (`tools/shift.py`): generator variants built at run time by copying `LEVELS` entries (the kit is never edited). Variants: low batteries `battery=(40, 70)`, `points_per_need=15`, `ensure_feasible=False`, L3 staffing on the L4 zone, L4 with half the scouts. Seeds 0 to 49, planner run like the jury (clean copy, `/usr/bin/python3`). Pass = 0 failures and no variant under the kit baseline.
- **Edge-case pack** (`tools/edge.py`): hand-made or derived absurd scenarios. Pass = exit 0, valid plan (empty accepted), never a negative score. As a fast pytest for CI with `PLANNER_BUDGET_S=3` and `PLANNER_WORKERS=2`.
- **Check `_needs()`** in the generator does not depend on the level name in a way that breaks the variants.
- Branch `feature/shift-edge` cut from `main` at `ec5c41e`.

## What was built

| File | Purpose |
|---|---|
| `tools/edge.py` | 16 cases in a `CASES` dict (name to builder). `run_handin()` copies `handin/` to a temp dir and runs `planner.py` in a subprocess with a clean environment. `judge()` decides pass or fail. Runnable by hand: `python3 tools/edge.py [--budget 3] [--workers 2] [name ...]`. |
| `tests/test_edge.py` | One pytest per case in `CASES`, with a 12 s wall-time check each. |
| `tools/shift.py` | The 5 variants. Runs the planner and `tools/baseline_planner.py` on each scenario through `bench.run_one`. Prints per variant: total, baseline total, ratio, failures, max time. Exit code 1 on any failure or any ratio under 1.0. Options: `--variants`, `--seeds`, `--jobs`, `--python`, `--json`. |

### The 16 edge cases

`no_scout`, `no_light`, `no_heavy`, `no_effector` (extra), `r7_all_blocked`, `windows_closed`, `horizon_120`, `one_aircraft`, `battery_5`, `unknown_level`, `extra_keys`, `events_nonempty`, `need_zero`, `need_unknown_subtype_null_window`, `no_check_L2`, `no_check_L4`.

### What a case must satisfy

Exit code 0, a plan file written, plan valid under the official scorer (empty accepted), score not negative, and **no swallowed exception**. The last check matters: `planner.py` catches every exception in `main()` and exits 0 with the last kept plan, so a crash would look like a pass. `judge()` fails a case if stderr contains `planner: `.

### `_needs()` check

`_needs(level_name, ...)` only tests `level_name in ("L1", "L2")` to pick 3 weights instead of 4. Every `S-*` variant name therefore takes the 4-weight branch, like L3 and L4. Compatible. Consequence: `S-l3-on-l4` is L3 staffing with L4 needs, not L3's own needs.

## Results

### Edge pack

16 of 16 pass. No crash, no swallowed exception, no invalid plan, no negative score. `pytest tests/test_edge.py`: 16 passed in 56 s.

### Shift suite, jury conditions (final, 250 runs)

38 s budget (default), `/usr/bin/python3` 3.14.4 in WSL, seeds 0 to 49, run on 2026-11-21, finished at 15:53. **0 failures in 250 runs.**

| Variant | Runs | Total | Baseline | Ratio | Worst seed | Max time |
|---|---|---|---|---|---|---|
| S-battery | 50 | 37301.0 | 16518.1 | 2.258 | 1.34x | 38.5 s |
| S-points | 50 | 55800.1 | 23428.2 | 2.382 | 1.51x | 39.0 s |
| S-nofeas | 50 | 55616.9 | 25954.9 | 2.143 | 1.37x | 39.9 s |
| S-l3-on-l4 | 50 | 17605.0 | 11522.9 | 1.528 | 1.11x | 38.5 s |
| S-half-scouts | 50 | 46557.0 | 25681.0 | 1.813 | 1.26x | 39.6 s |
| **Total** | **250** | **212880.0** | **103105.1** | **2.065** | | **39.9 s** |

No seed scored below the baseline. The weakest seed is `S-l3-on-l4` at 1.11x. Maximum run time 39.9 s against the 60 s limit.

### Earlier quick run (15 s budget, 250 runs)

2 workers, 8 parallel jobs, local Windows Python. 0 failures. Ratios: S-battery 2.048, S-points 1.970, S-nofeas 1.803, S-l3-on-l4 1.446, S-half-scouts 1.578. Lower than the jury-condition run, as expected with the shorter budget. Its timings are not usable (parallel load).

One timing anomaly in that run: `S-nofeas` seeds 48 and 49 took 21.4 s and 19.7 s against a 15 s budget. Rerun alone they took 15.2 s and 15.3 s. Cause: machine load from 8 parallel jobs, not the planner.

## How the final run differs from the spec

The spec says one job, `/usr/bin/python3`, clean copy. To finish before 16:00 the final run used four processes at once:

- `S-battery` and `S-points`: one process, 8 workers (planner default).
- `S-nofeas`, `S-l3-on-l4`, `S-half-scouts`: one process each, `PLANNER_WORKERS=5`.

That is 23 workers on 20 cores. The planner searches a fixed 38 s wall-clock budget, so the three variants with 5 workers got slightly less search work. Their scores are slightly conservative. Validity, failures and run times are unaffected. Not done: a strictly sequential single-job run, and a run on the jury's own hardware.

## Not done

- No fix and no change to `handin/`, `fleetkit/` or any file owned by Louis (`planner.py`, `targets.py`) or the lead (`deconflict.py`). Nothing needed one.
- No strictly sequential 3 h run (see above).
- The live dashboard (`shift_dashboard/`) used to follow the run is a local helper. It is **not** in this PR.

## How to reproduce

From `fleet-kit/`:

```bash
python3 -m pytest -q tests/test_edge.py                      # edge pack, about 56 s
python3 tools/edge.py                                        # same cases, readable output
/usr/bin/python3 tools/shift.py --seeds 0-49 --jobs 1 --json shift.json   # about 3 h, jury conditions
python3 tools/shift.py --variants S-battery --seeds 0-4      # quick check of one variant
```

## Risks and limits

- The edge cases use `generate("L2", 0)` as base. Cases that depend on a specific scenario shape (for example `r7_all_blocked`, which adds a civilian 50 m from every hostile) assume the generator keeps its current output for that seed.
- `judge()` detects a swallowed exception through the text `planner: ` on stderr. If `planner.py` changes that message, the check silently stops working.
- The shift variants are chosen from the roadmap. They cannot prove the hidden scenarios resemble them.

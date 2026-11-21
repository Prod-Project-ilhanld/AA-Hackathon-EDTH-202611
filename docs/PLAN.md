# EDTH Paris — SUB-15 Fleet Orchestration

Kit: https://github.com/AA-OpenProjects/AA-Hackathon-EDTH-202611. In this repo the kit is the tree itself; our hand-in is `fleet-orchestration/fleet-kit/handin/` (never edit `fleetkit/`).
Event: 20–22 Nov 2026. **Hand-in: 22 Nov, midday. We hand in by 11:00.**
Background: [KIT_NOTES.md](KIT_NOTES.md) (rules and code), [research/PRIOR_ART.md](research/PRIOR_ART.md) (ideas to borrow).

## The hand-in (hard constraints)
- A folder with `planner.py`. They run `python3 planner.py scenario.json plan.json` in a fresh copy of the folder, with the official `fleetkit` importable.
- **Python 3.9 compatible.** The jury only promises "Python 3.9 or newer". No `match`, no `X | Y` type hints, no `zip(strict=)`, no 3.10+ stdlib features. Test with the system `python3` (`python3` on PATH is 3.9.18; `/usr/bin/python3` is 3.9.6, used by `check.py --python`).
- **Standard library only.** No OR-Tools, no numpy. Anything else must live inside the folder.
- **60 s per scenario.** A crash, timeout, missing plan or invalid plan scores 0. We stop searching at ~45 s.
- **No folder named `fleetkit`** inside the hand-in: it would hide the official one.
- Ranking: sum of raw scores on scenarios we haven't seen. Ties go to the faster total run time.
- Test the hand-in like the jury from `fleet-orchestration/fleet-kit`: `python3 tools/bench.py --levels L1 L2 L3 L4 --seeds 0-1 --jobs 1 --python /usr/bin/python3` (fresh copy per run, 60 s, official validator).

## Rule zero
An invalid plan scores 0. The planner writes an empty valid plan first, then builds Track 1 (the improved baseline, anytime) and keeps the best officially valid plan (see ROADMAP rule 10). Every candidate passes the official `fleetkit` `validate()` before it can replace the best one, and the planner always writes the best valid plan it has. Fast incremental checks are for searching only, never the final judge.

## Score
`points served − 0.5 × energy (Wh) − 10 × effectors used`
Optional `--verify` bonus: re-observe a hostile 10–120 s after it was engaged for +25% of its points. It has its own board and doesn't change the ranking. Low priority.

## Levels
| Level | Scouts | Light | Heavy | Hostile | Unknown | Friendly + civilian | Zones |
|---|---|---|---|---|---|---|---|
| L1 | 2 | 2 | 1 | 3 | 1 | 1 | 1 |
| L2 | 3 | 6 | 3 | 6 | 3 | 2 | 2 |
| L3 | 5 | 16 | 9 | 14 | 6 | 5 | 4 |
| L4 | 15 | 50 | 35 | 50 | 20 | 20 | 8 |

L4 (100 aircraft) is where a fast heuristic matters and an exact solver won't fit in 60 s.

## Greedy baseline (seeds 0–9, all plans valid)
| Level | Mean score | Min–max | Share of points served | Time per scenario |
|---|---|---|---|---|
| L1 | 101.4 | 48.7–168.8 | 62% | <0.1 s |
| L2 | 231.8 | 111.2–349.5 | 73% | ~0.1 s |
| L3 | 379.3 | 211.0–463.9 | 59% | ~1.8 s |
| L4 | 472.2 | 314.7–702.4 | **24%** | ~6.3 s |

The ranking sums raw scores, so the big levels count most. L4 serves under a quarter of the points: that's where we gain the most.

Run from `fleet-orchestration/fleet-kit`: `python3 -m fleetkit stats L4 --seeds 0-9`

## Timeline
The detailed roadmap (vision, workstreams, agent lanes, checkpoints CP0–CP6 with verification commands, hour-by-hour schedule, the `state.py` contract) is in [ROADMAP.md](ROADMAP.md). Short version: CP1 safe skeleton Sat 03:00 · CP2 v1 beats baseline Sat 13:00 · CP3 L4 at scale Sat 19:00 · CP4 search + tuning Sun 01:00 · CP5 freeze Sun 10:00 · hand-in Sun 11:00.

## Who owns what (one owner per file)
Suggested split, not fixed (see [ROADMAP.md §0](ROADMAP.md) for the current state). The original role table:
| Person | Files |
|---|---|
| A | `handin/planner.py`, `guard.py`, `state.py` (contract owner), `params.py`, `handin/fk/`, delta validation; Track 1 from CP2; final hand-in |
| B | `handin/prep.py`, `bundle.py`, `strikes.py`; all ALNS operators from Sat 19:00 |
| C | `handin/routing.py`, `scouts.py` |
| D | `handin/deconflict.py`; runs `tools/tune.py` from CP0 |
| E | `tools/bench.py`, `tools/tune.py` (starter), `tools/loop/program.md`, edge/shift seed sets (to do), `handin/search.py` frame |
| F | `handin/v1_greedy.py` (Track 1) until CP2, then `tools/bound.py`, `tools/demo/`, pitch, board |

`handin/params.py` holds every number we choose and every feature flag; anyone can propose a key, nobody hard-codes a constant.

## ALNS experiment and speed plan
`tools/alns_baseline.py` searches over the order in which the baseline serves targets (destroy/repair on the order, adaptive operator weights, simulated annealing). On the 8 public scenarios, with a 45 s budget each and every plan officially valid: **2,664.5 → 3,166.5 (+18.8%)**. L3 gained up to +44%, L1 +0%. L4 got only 3–11 tries because each try reruns the whole greedy. Not hand-in ready: it can overrun 60 s, and only one seed was tested. **Measured on the board scenarios themselves: re-measure on holdout seeds before counting on it.**

Profile of one greedy run on L4-401 (1.4 s): full `validate()` 67% (R8 pairwise separation alone 29%), `_detour` zone tests 27%.

Speed-ups, biggest first:
1. **Incremental checks:** new route vs existing routes only (`separation_violation(a, b)`), full `validate()` once at the end. ~3–10×. `deconflict.py` + `guard.py`
2. **Lowest cruise layer that clears zones on the path** (≥ 125 m clears every zone but costs climb energy and shrinks observation reach to ≈ 83 m): a tuning knob, not a default. Small
3. **Reuse a saved plan prefix** instead of rebuilding from zero: ~2×. Stopgap until 6
4. **Skip hopeless targets early** (R7-blocked, unprofitable, unreachable window). `prep.py`
5. **Cheap arithmetic checks** (window, energy) before any validation
6. **Real ALNS moves on routes** (remove/re-insert a target locally, no greedy replay): milliseconds per try. Target design for `search.py`
7. **Clock safety:** stop when time left < ~2 average tries. Must have
8. **Parallel chains** with `multiprocessing`: maybe, ask the organisers (core count unknown, ties broken by run time)

Order: 7 → 2 + 4 → 1 → 6 (3 meanwhile, 8 maybe).

## Parameter tuning (`tools/bench.py` + `tools/tune.py`)
- **What:** every number we choose lives in `handin/params.py`. `tune.py` runs parallel workers (`multiprocessing`, one per core, spare laptops overnight). Only the resulting numbers go into the hand-in.
- **Anti-overfitting:** tune on seeds 0–199, confirm on holdout seeds 5000–5049 at checkpoints (final set 9000–9049 once at CP5, see ROADMAP §1), **never on the 8 board scenarios**. Keep ~10–20 global parameters (one set per level at most). Accept a change only if train improves and the checkpoint holdout agrees, failures stay at 0 and run time stays under ~45 s.
- **Method:** random search plus successive halving: try many settings on a few seeds, keep the best third, re-test those on more seeds, repeat. Compare settings on the **same** seeds (paired), so noise between scenarios doesn't decide.
- **Expected value (estimates, not measured):** structural changes give the big gain (likely 2×+ on L4), ALNS +5–15%, tuning **+3–10%** on top. Structure first: a tuned weak planner is still weak.
- **Cost:** ~2–3 h for one person (E). L4 runs take ~45 s each, so overnight on ~48 cores covers a few hundred settings.
- **When:** `bench.py` on day 1. `tune.py` once v1 beats the baseline (Saturday midday), then overnight.
- **Not doing:** full RL, LLM-as-judge. The official `evaluate()` is already the exact judge.
- Optional, after M2: a small decision tree trained in `tools/` on served vs dropped targets, exported as plain if/else rules in `prep.py`. Keep it only if holdout improves.

### What to tune (candidate knobs for `params.py`)
| Area | Knob | Why it matters | Range to try |
|---|---|---|---|
| Target choice | min profit to accept a target | drops money-losing targets | 0–30 points |
| Target choice | effector cost weight in ranking (≥10) | above 10 = save drones for richer targets later | 10–25 |
| Target choice | hostile vs unknown order (interleave by profit or hostiles first) | scouts are the bottleneck | 2 options |
| Altitude | scout cruise altitude, effector cruise altitude | ≥125 m clears zones; higher costs climb energy and shrinks observation reach | 120–150 m |
| Altitude | layer spacing between aircraft sharing a corridor | ≥40 m avoids separation conflicts | 40–60 m |
| Speed | cruise speed between best-range speed and max speed, per type | faster meets windows, slower saves energy | 0–100% of the gap |
| Scouts | observation offset from the contact | reach is √(150² − z²) ≈ 50–145 m; closer = longer flight | 30–140 m |
| Scouts | cluster radius for observing several contacts from one stop | fewer stops per scout | 0–140 m |
| Scouts | candidate scouts tried per target (k nearest) | more choice vs more time | 2–6 |
| Strikes | approach distance and approach angles | baseline uses 300 m and ±35° | 100–400 m |
| Strikes | final strike altitude | baseline uses 10 m | 0–25 m |
| Strikes | spacing between drones on one target (≤20 s window) | baseline uses 5 s | 0–8 s |
| Timing | slack after observation before the strike (rule needs 10 s) | baseline adds 2 s | 0–5 s |
| Timing | take-off spacing out of the pad grid | separation at the base, the L4 bottleneck | 2–10 s |
| Routing | margin around civilian/friendly circles | baseline uses 15 m test, 60 m detour | 5–60 m |
| Search | removal size, operator start weights, reaction/decay, SA start temperature and cooling, blink rate | standard ALNS knobs (see PRIOR_ART) | from N-Wouda / SISR defaults |
| Clock | search budget, reserve kept for the final `validate()` | 60 s hard limit on an unknown machine | 35–50 s |

Easy win now: the baseline's own constants (`SCOUT_LAYERS`, `EFFECTOR_LAYERS`, `APPROACH_M`, `OBS_OFFSET_M`, `SPEED_FACTOR`, the 2 s and 5 s timing gaps) can be tuned on a **copy** of `baseline.py` before v1 exists. That also lets `tune.py` be built and debugged early.

## Demo and pitch (F, with everyone's numbers)
- Before/after in the official viewer: baseline vs ours on an L4 scenario, same seed.
- One table: holdout totals and run times per level, baseline vs ours, 0 failures.
- One slide on the method: prune → build → improve (ALNS) → guard.
- Explainability: why each target was served or dropped (profit, window, drone availability).
- Optional: scaling chart (L1 → L4, or more aircraft) and the link-loss story if that part ships.

## TODO: live board (blocked on organisers)
Get the server address, team name and token from Alta Ares, then from `fleet-orchestration/fleet-kit`:
```bash
python3 -m fleetkit board-login --server http://<address>:8080 --team "<team>" --token <token>
python3 -m fleetkit validation-set -o validation   # then make a plan per scenario into my-plans/
python3 -m fleetkit submit-all my-plans/
```
Regenerate the baseline plans first if `runs/` is missing (it's gitignored). The board has **no 60 s limit**: plans can be computed offline with any amount of time, so submit our best offline plans (ALNS experiment: 3,166.5) once we have the token. The board isn't the final ranking.

## Ask the organisers
- Board server address, team name and token.
- How exactly do we hand in (zip, repo link, form) and what folder name?
- Which Python version is on the evaluation machine, and how many CPU cores?
- Is `multiprocessing` allowed in the hand-in? Is there network access during evaluation?
- Is the link-loss part still coming? The kit says "no communication".
- Will `fleetkit` change before the final run, and will we be told?
- How many hidden scenarios per level? (decides how much L4 matters)

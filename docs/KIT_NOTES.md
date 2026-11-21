# Starter kit notes (read in full on 2026-11-20)

Repo: https://github.com/AA-OpenProjects/AA-Hackathon-EDTH-202611, local copy in `kit/` (gitignored).
Two Alta Ares subjects: `fleet-orchestration/` (ours) and `search-destroy/` (the FPV guidance one). Everything is synthetic.

## Hand-in and ranking
- Folder with `planner.py`; they run `python3 planner.py scenario.json plan.json` in a fresh copy, with the official `fleetkit` on `PYTHONPATH`. So we **can import fleetkit** (validator, geometry, energy) in our planner.
- **Standard library only.** 60 s per scenario. A crash, timeout, missing plan or invalid plan scores 0.
- Ranking = sum of raw scores over hidden scenarios (same rules, score and validator; the README doesn't promise the same generator levels). Ties go to the faster total run time. A jury also judges how sound the approach is and how it's presented.
- Deadline **22 Nov, midday**. The kit's `handin/check_handin.py` only tests the kit's own template folder; use our `tools/check.py`, which runs our `handin/` the same way.
- Live board: 8 public scenarios (L1-101, L2-201, L2-202, L3-301, L3-302, L3-303, L4-401, L4-402). We upload plans, not code, and it keeps our best score per scenario. We need the server address and token from the organisers. `submit` validates locally first.

## Score
`score = Σ points served − 0.5 × energy (Wh) − 10 × effectors that have a route`
- A hostile is served when it is engaged (all rules valid). An unknown is served when a scout observes it.
- **Every effector that gets a route costs 10**, so we only give routes to effectors we use.
- `--verify` bonus (+25%: re-observe 10–120 s after the last engagement) has its own board and doesn't count in the ranking.

## Rule parameters (identical in every scenario)
z 30–150 m · observe within 150 m (3D) with 20 s dwell · confirm ≥10 s before engaging · protected radius 100 m around friendly/civilian · collateral 200 m · separation 40 m (3D) · separation exemption within 100 m of a shared target · engage within 25 m (3D) of the contact · multi-effector sync window 20 s · horizon 600 s (L1) or 900 s (L2–L4).

## The ten rules: the details that matter
- **R1** The first waypoint is the home (z=0) with no action and no dwell. Times are in order, inside [0, horizon]. Engage is the last waypoint and has no dwell. An effector route must end with an engage. **Omit unused aircraft.** The plan carries the scenario `seed`.
- **R2** Each leg's duration ≥ the time its horizontal distance and climb/descent need at max speed. Waypoints k≥1 must be within z 30–150, **except the last one** (landing, or the final dive down to z=0).
- **R3** Route energy ≤ capacity × battery%. Scouts must end exactly at home, z=0.
- **R4** A valid scout observation must finish ≥10 s before the engagement.
- **R5** Effectors only engage hostiles. Scouts only observe hostiles or unknowns.
- **R6** No leg may enter a zone below its `top_m`, and no leg may enter the 100 m cylinder (**infinite height**) around a friendly or civilian.
- **R7** A hostile within 200 m (horizontal) of a friendly or civilian can **never** be engaged. Prune those up front.
- **R8** 40 m 3D separation, checked exactly (closed form) between every pair of airborne routes. A route is "airborne" from its first departure to its last arrival. Waiting on the ground before take-off is free and not checked.
- **R9** The whole observation (t to t+dwell) and the engagement time must fall inside the contact's window.
- **R10** A hostile gets exactly the required number of light and heavy effectors, all engaging within 20 s of each other and each within 25 m of it.

## Energy model
- Cruise power = `p0 + k_v·v²` (W), so the energy-optimal speed is `sqrt(p0/k_v)`, capped at `v_h`. Climbing costs `e_climb` Wh per metre. Descending is free.
- Hovering (dwell) costs p0. Waiting on the ground before take-off costs nothing, so **take off late rather than hover**.

## Generator facts (what the public levels look like; hidden scenarios are only promised the same rules, score and validator)
| | Scouts | Light | Heavy | Hostile | Unknown | Friendly | Civilian | Zones | Area (m) |
|---|---|---|---|---|---|---|---|---|---|
| L1 | 2 | 2 | 1 | 3 | 1 | 0 | 1 | 1 | 3000 |
| L2 | 3 | 6 | 3 | 6 | 3 | 1 | 1 | 2 | 3500 |
| L3 | 5 | 16 | 9 | 14 | 6 | 3 | 2 | 4 | 4500 |
| L4 | 15 | 50 | 35 | 50 | 20 | 12 | 8 | 8 | 7000 |

- **All homes sit on a pad grid near (150, 150)**, 11–20 m apart (L4 is 10×10 in about 100 m). Take-offs and landings must be staggered in time or in altitude because of the 40 m separation. That's the bottleneck at L4.
- **Zone ceilings are 40–120 m and z_max is 150 m, so flying at 125–150 m clears every zone.** Climbing costs 0.01–0.05 Wh/m: cheap in points, but 130 m is 5–15% of a scout's battery, and at 125 m the observation reach shrinks to ≈ 83 m, so treat altitude as a tuning knob. Only the friendly/civilian cylinders need horizontal detours.
- Hostiles: 40–100 points, grouped in clusters, at least 0.3 × area from home. Needs 1–4 effectors (L3/L4 weights 30/30/25/15%), about 40% with heavy ones. **A 4-effector hostile worth 40 points loses money** (4 × 10 + energy).
- Unknowns: 10–30 points, observe only.
- About 40% of friendlies/civilians are placed 110–190 m from a hostile, which makes that hostile unengageable (R7). At L4 that blocks 6–17 of 50 hostiles (verified seeds 0–9).
- Windows open between 0 and 0.55 × horizon and last 0.2–0.4 × horizon (0.25–0.5 at L1).
- Aircraft: scouts fly 15–22 m/s with 35–50 Wh. Light effectors fly 28–35 m/s with 40–55 Wh. Heavy effectors fly 18–25 m/s with 55–75 Wh. Battery is at 70–100%.

## The greedy baseline (`fleetkit/baseline.py`)
- It serves hostiles from the richest down, then unknowns. Each one uses the nearest scout, the nearest free effectors, fixed altitude layers (scouts 70/110 m, effectors 40/85/130 m) and small detours. An assignment is kept only if the **full** plan still validates and the score improves.
- Weaknesses:
  - no look-ahead and no reassignment
  - it ignores profitability per effector
  - one observation per waypoint, at a fixed 100 m offset
  - it re-validates the whole plan on every try, which is O(n²) separation work, so L4 is slow (~6 s) and coverage is low (24%)
  - effectors get spaced 5 s apart at the engagement
- Baseline means over seeds 0–9: L1 101, L2 232, L3 379, L4 472.

## Where the points are
1. **L4 has the most to gain.** Assigning many more hostiles needs fast incremental checks (only test new routes against existing ones) and a take-off schedule out of the pad grid.
2. **Filter by profitability**: points − 10 × effectors − energy. Skip hostiles that are R7-blocked or unprofitable.
3. **Fly high (≥125 m) to ignore zones.** One scout observation point can cover several clustered contacts (back-to-back observe waypoints, 20 s each, within 150 m 3D).
4. Then search: ALNS (remove some contacts, re-insert, keep the result if it's valid and better) for the rest of the 60 s.
5. **Always** run the official `validate` on the final plan, and fall back to the greedy baseline if it fails.

## Link-loss part: it exists, but ships separately
`cli.py` hides the `events` and `linkloss` commands until a `fleetkit.linkloss` module is present ("the link-loss part ships separately"). What we know so far:
- A policy file, `policy.py`. The built-in baselines are `continue`, `hold`, `return` and `broadcast`.
- Metrics: retention (points kept), failed runs, messages per aircraft per minute, `S_loss`, ms per call.
- Sizing: a grid of radio range (m) × capacity (B/s). A cell "meets the bar" when retention is ≥ 0.9 with no failure. The result is a sizing score plus a frontier (the smallest capacity that meets the bar, per range).

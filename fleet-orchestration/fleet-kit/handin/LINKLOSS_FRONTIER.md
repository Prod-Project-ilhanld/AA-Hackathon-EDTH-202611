# Link-loss frontier (hand-in policy)

`policy.py` in this folder, measured with the kit's official sizing grid. The policy is byte-identical to `main` at the freeze (PRs #19, #23, #35, #36).

## Sizing

| Seeds | Sizing score | Frontier: lowest bandwidth that meets the bar, B/s, at 250 / 500 / 1000 / 2000 m | Failed runs (all 20 cells × 200 runs) |
|---|---|---|---|
| 5–14 | **1.00** | 50 / 50 / 50 / 50 | **0** |
| 15–24 (fresh) | **1.00** | 50 / 50 / 50 / 50 | **0** |

50 B/s is the lowest bandwidth on the grid, so the policy meets the bar at every range and bandwidth we tested.

## Per range at 200 B/s

| Seeds | Range | Retention | Failed runs | Messages per aircraft per minute | S_loss | Policy step |
|---|---|---|---|---|---|---|
| 5–14 | 250 m | 0.971 | 0 | 19.0 | 0.933 | 0.08 ms |
| 5–14 | 500 m | 0.986 | 0 | 17.6 | 0.951 | 0.07 ms |
| 5–14 | 1000 m | 0.986 | 0 | 18.3 | 0.949 | 0.07 ms |
| 5–14 | 2000 m | 0.986 | 0 | 19.0 | 0.948 | 0.07 ms |
| 15–24 | 250 m | 0.987 | 0 | 18.1 | 0.951 | 0.05 ms |
| 15–24 | 500 m | 1.000 | 0 | 17.2 | 0.966 | 0.05 ms |
| 15–24 | 1000 m | 0.999 | 0 | 16.9 | 0.965 | 0.06 ms |
| 15–24 | 2000 m | 1.000 | 0 | 17.4 | 0.965 | 0.06 ms |

S_loss = retention − 0.002 × messages per aircraft per minute. Messages are compact positional lists, about 8.5 B each.

`check_policy` L1–L4 at 1000×200 (kit greedy plans): mean retention 0.990 on seeds 0–9 and 0.995 on seeds 20–29, 0 failed runs.

## How it was measured

Baseline plans, events seed 1, 5 comm seeds, all 20 cells (4 ranges × 5 bandwidths), 40 scenarios per seed set (L1–L4). From `fleet-kit/`:

    python3 tools/linkloss_diag.py --policy handin/policy.py --sizing --seeds 5-14  -o runs/linkloss-t10-sizing-5-14.json
    python3 tools/linkloss_diag.py --policy handin/policy.py --sizing --seeds 15-24 -o runs/linkloss-t10-sizing-15-24.json
    python3 handin/check_policy.py --levels L1,L2,L3,L4 --seeds 0-9

Raw JSON: `runs/linkloss-t10-sizing-5-14.json`, `runs/linkloss-t10-sizing-15-24.json`.

## Known limits

- We trade messages for safety. A lower-traffic variant (aborted aircraft beacon only when a peer closes in, ~9 messages per minute, S_loss 0.967 at 1000×200) was measured and rejected: it brought back 1 failed run at 250 m and dropped the sizing score to 0.75.
- L3-6 keeps retention 0.611: two aircraft abort seconds after take-off and hover over the base, head-on with departing aircraft. Flying them home fixed it but broke three other scenarios, so it is not in.

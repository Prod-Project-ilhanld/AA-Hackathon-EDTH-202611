# EDTH Paris 2026 · SUB-15 Fleet Orchestration (team repo)

Our hand-in: `fleet-orchestration/fleet-kit/handin/planner.py` reads a scenario and writes a plan that tasks scouts and effector drones under the ten rules. **Hand-in Sun 22 Nov, 11:00 (deadline 12:00).**

**Start here:** [docs/ROADMAP.md](docs/ROADMAP.md) (§0 status, §1–§3 vision and owners) · [docs/PLAN.md](docs/PLAN.md) (hard constraints) · [docs/KIT_NOTES.md](docs/KIT_NOTES.md) (rules explained) · [CONTRIBUTING.md](CONTRIBUTING.md) (git rules) · [fleet-orchestration/docs/spec.md](fleet-orchestration/docs/spec.md) (Louis's spec, FR).

## Run it (from `fleet-orchestration/fleet-kit`)
```bash
python3 tools/bench.py --levels L1 L2 L3 L4 --seeds 0-1 --jobs 1 --python /usr/bin/python3   # like the jury, vs baseline
python3 -m pytest -q tests                                                                 # unit tests
python3 -m fleetkit generate L4 3 -o scenario.json && python3 handin/planner.py scenario.json plan.json
python3 -m fleetkit view scenario.json plan.json --open                                    # watch it fly
python3 demo/swann_demo.py scenario.json plan.json -o out/                                  # jury report + viewer layers
```
Planner knobs (environment): `PLANNER_BUDGET_S` (default 38, from process start), `PLANNER_ALARM_S` (52), `PLANNER_WORKERS` (8).

## Layout
| Path | Who | What |
|---|---|---|
| `fleet-orchestration/fleet-kit/handin/planner.py` | Louis (+ safety by A) | Track 1 planner: restarts and hill-climb over the contact order, pre-filtered validation, safety net |
| `fleet-orchestration/fleet-kit/handin/routing.py` | 7thwardlord1 | 3D minimum-energy routing, visibility-graph detours, cost API |
| `fleet-orchestration/fleet-kit/handin/fk/` | — | Vendored kit helpers (never edit, never rename to `fleetkit`) |
| `fleet-orchestration/fleet-kit/tools/bench.py` | Louis / E | Jury-style multi-seed bench (the judge) |
| `fleet-orchestration/fleet-kit/demo/` | Swann | Jury report, viewer layers, demo script |
| `fleet-orchestration/fleet-kit/fleetkit/` | Alta Ares | **Official kit: never edit** |
| `docs/` | team | Roadmap, plan, kit notes, research |

## Rules
- `main` must always pass CI. Work on short `feat/…` branches, one PR each, merged at the 2-hour windows.
- Python 3.9 + standard library only in `handin/`. Never edit `fleetkit/`. Never iterate over a `set`, never branch on `scenario.level`.
- A PR that changes the planner shows `tools/bench.py` before/after on the same seeds.

## Official starter material
Alta Ares' original README for both subjects is in [fleet-orchestration/README.md](fleet-orchestration/README.md) and [search-destroy/README.md](search-destroy/README.md). Everything in the kit is synthetic.

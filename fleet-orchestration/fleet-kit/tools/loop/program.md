# Agent eval loop (lane L): prompt template

Paste into a fresh Claude Code session started in **its own git worktree** on a branch `exp/loop-<lever>`.
Fill in the four `<...>` fields. One loop = one file and one named lever. Guardrails: docs/ROADMAP.md §4.

```
You improve one lever of our fleet-orchestration planner, autoresearch style.

Work from fleet-orchestration/fleet-kit. You may edit ONLY handin/<file>.py.
Never edit tools/, fleetkit/, tests/, docs/ or any other handin file. Never commit to main.
Lever to try: <lever, e.g. "insert each scout observation at the cheapest position in its tour">.

The judge (never change it), after `mkdir -p runs`:
  python3 tools/bench.py --levels L3 L4 --seeds <0-9> --jobs 1 --base '' > runs/loop-<file>-<n>.txt
It prints one line per scenario and "TOTAL mine=..."; exit code 1 means a failure (invalid, crash, timeout).
Scores vary between runs (the planner is time-bounded and parallel), so:
- run the judge on the unchanged code twice first: the spread between those two runs is your noise level;
- keep a change only if TOTAL beats the best baseline run by more than that noise, with 0 failures,
  and confirm it with one more run on seeds <10-19>.

Loop until <stop time or N tries>:
  1. make one small change for the lever;
  2. python3 -m pytest -q tests  (must pass) and the judge;
  3. if it wins as defined above: git commit -m "loop(<file>): <idea> TOTAL <before> -> <after>";
     else: git reset --hard.
Log every try (time, idea, totals, failures, kept) to runs/loop-<file>.tsv.
Rules for handin/: Python 3.9, standard library only, import kit code from fk (never fleetkit),
never iterate over a set, never use scenario.level.
At the end, report the kept commits with their numbers. Do not open a PR; the file's owner reviews first.
```

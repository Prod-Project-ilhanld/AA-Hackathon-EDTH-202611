"""Tuning loop for the planner's numbers. Starter file, not built yet.

Plan (docs/ROADMAP.md §4, lane T):
- the knobs: environment variables the planner already reads (PLANNER_BUDGET_S, PLANNER_WORKERS) plus the
  constants worth exposing (N_SCOUTS, the alphas in `_search`, layer choices...): expose each as an env var;
- random search: try a setting on TRAIN seeds only (0-199) with tools/bench.py, keep the best few, re-test
  them on more seeds (successive halving); compare settings on the SAME seeds (paired);
- confirm the winner once on holdout seeds (5000-5049); never tune on the 8 board scenarios;
- reject any setting with a failure or a run over 50 s.
Scores vary between runs, so repeat the baseline setting to know the noise before trusting a gain.
"""
import sys

if __name__ == "__main__":
    sys.exit("tools/tune.py is a starter file: see its docstring for the plan")

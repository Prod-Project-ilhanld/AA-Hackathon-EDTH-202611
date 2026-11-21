# Team dev rules

A living list: anyone can add a rule when we hit a problem. Add it with a one-line reason.

## Branches
1. `main` always works: CI (`.github/workflows/ci.yml`) is green on it. Nobody pushes straight to `main`; everything goes through a PR with green CI.
2. One branch per feature, made from an up-to-date `main`:
   ```bash
   git switch main && git pull && git switch -c feat/<short-name>
   ```
   Use `feat/` for features, `fix/` for bug fixes and `exp/` for experiments that might be thrown away.
3. Keep branches short-lived (hours, not days). Merge into `main` often.
4. Before merging: pull `main` into your branch, rerun the checks, then open a PR. One teammate glances at it before it's merged.

## Rules we add as we go
<!-- Format: N. Rule. — why (date) -->

"""Margin-hardened scenarios: plan against stricter rules so that the plan survives timing drift without a radio.

The planner is not touched. We hand it a copy of the scenario whose rules are tighter (bigger separation,
bigger confirmation margin, narrower synchronisation window, narrower contact windows); a plan valid for the
copy is also valid for the real scenario, and it keeps slack when aircraft arrive late.
"""
import copy
from typing import Dict, Tuple

# level -> (extra separation m, extra confirmation margin and window shrink s, synchronisation window s)
LEVELS: Dict[int, Tuple[float, float, float]] = {
    0: (0.0, 0.0, 20.0),
    1: (20.0, 5.0, 10.0),
    2: (40.0, 10.0, 6.0),
    3: (60.0, 20.0, 4.0),
}


def harden(data: dict, level: int) -> dict:
    """Returns a copy of the scenario dictionary planned against the margins of `level` (0 = unchanged)."""
    sep, margin, sync = LEVELS[level]
    out = copy.deepcopy(data)
    if level == 0:
        return out
    rules = out["rules"]
    rules["d_sep_m"] = rules["d_sep_m"] + sep
    rules["confirm_margin_s"] = rules["confirm_margin_s"] + margin
    rules["sync_window_s"] = min(rules["sync_window_s"], sync)
    for c in out["contacts"]:
        w = c.get("window_s")
        if w:
            lo, hi = w[0] + margin, w[1] - margin
            c["window_s"] = [lo, hi] if hi > lo else list(w)
    return out

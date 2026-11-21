"""Every tunable number and flag of the planner, read once at import. Python 3.9, standard library only."""
import os

BUDGET_S = float(os.environ.get("PLANNER_BUDGET_S", "38"))  # search deadline, seconds from process start
ALARM_S = float(os.environ.get("PLANNER_ALARM_S", "52"))    # backstop: write the last kept plan and exit
MAX_WORKERS = int(os.environ.get("PLANNER_WORKERS", "8"))   # worker processes (capped by the core count)
FLEET_ITERS = int(os.environ.get("FLEET_ITERS", "0"))       # >0: exactly this many builds per worker, reproducible plan
INJECT_FAIL = os.environ.get("FLEET_INJECT_FAIL", "0") == "1"  # test hook: solve() raises at its start
INJECT_HANG = os.environ.get("FLEET_INJECT_HANG", "0") == "1"  # test hook: hang after the best plan is kept
TARGETS = os.environ.get("PLANNER_TARGETS", "1") != "0"        # targets.py: R7 skip, ON by default (Louis: L4 +1.27%, 0 seeds worse)
DECONFLICT = os.environ.get("PLANNER_DECONFLICT", "1") != "0"  # deconflict.py: R8 departure scheduler, ON by default (paired L4 0-19: +5.9% ± 0.9%, 1/20 worse)
R10_GUARD = os.environ.get("PLANNER_R10_GUARD", "1") == "1"   # deconflict.py: reject candidates that break R10 with accepted strikes (Martin)

N_SCOUTS = 15          # nearest scouts tried with every option
BOTH_ROUTERS = 20      # up to this many aircraft (L1, L2) both routers are used
SMALL_FLEET = 8        # up to this many aircraft (L1) the search converges in seconds
STAGNATION_S = 12.0    # ... and stops when nothing better was found for this long
MIN_BUILDS = 30        # ... but not before this many builds
ALPHAS = (0.0, 1.0, 0.5, 1.5)  # starting exponent on the effector count in the contact order, per worker
SIGMA_EVEN = 0.12      # noise on the order around the best one, even workers
SIGMA_ODD = 0.3        # ... odd workers
FALLBACK_MIN_LEFT_S = 8.0  # greedy fallback only when at least this many seconds remain before the alarm
POOL_GRACE_S = 8.0     # how long past the deadline the pool waits for a worker
BUDGET_FLOOR_S = 10.0         # large fleets: the budget never shrinks below this
BUDGET_SHRINK_FROM = 100      # ... shrinks above this many aircraft
BUDGET_SHRINK_PER_AC = 0.04   # ... by this many seconds per extra aircraft

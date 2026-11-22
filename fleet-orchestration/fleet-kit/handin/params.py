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
KEEP_BETTER_GREEDY = os.environ.get("PLANNER_KEEP_GREEDY", "1") != "0"  # task 11: return the kit greedy plan when it scores strictly higher

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

# Scout cruise levels tried, in order. PLANNER_LOW_SCOUT=1 tries 35 m first (less climb, wider ground reach of an
# observation); OFF by default: paired L3 0-11 -3.7 +- 3.7 per seed (6/12 worse), L4 +12.9 +- 11.4 (4/12 worse).
LOW_SCOUT = os.environ.get("PLANNER_LOW_SCOUT", "0") == "1"
SCOUT_LEVELS = (35.0, 70.0, 110.0) if LOW_SCOUT else (70.0, 110.0)

# Repair phase (ruin and recreate around the best plan, as in a large neighbourhood search), ON by default (paired,
# FLEET_ITERS=3, seeds 0-11: L3 +2.4 +- 1.3 per seed, L4 +19.0 +- 5.0, 0/24 worse, 0 invalid). The last LNS_SHARE of
# the budget drops 1 or 2 scouts with the strikes they confirm and re-serves every unserved contact, keeping the
# result only when the kit scorer says it is valid and strictly better. Fleets above LNS_MIN_AC only (L3, L4).
LNS = os.environ.get("PLANNER_LNS", "1") != "0"
LNS_SHARE = float(os.environ.get("PLANNER_LNS_SHARE", "0.35"))
LNS_MIN_AC = 21
LNS_ITERS = 6          # with FLEET_ITERS > 0: exactly this many repairs per worker, reproducible plan

# Extending a scout tour keeps the observations of the contacts already struck early enough for R4 (latest_ends
# of the team router): without it the rebuilt tour drifts later, breaks R4 and the contact goes to a new scout.
LATEST_ENDS = os.environ.get("PLANNER_LATEST_ENDS", "1") != "0"

# Tours first (as in a team orienteering model): one worker in TOURS_EVERY builds its plans by following scout
# tours planned for the whole fleet at once (tours.py), the others keep the contact-by-contact search.
TOURS = os.environ.get("PLANNER_TOURS", "1") != "0"
TOURS_EVERY = 4
TOURS_MIN_AC = 21
TOURS_MAX_AC = 60      # L3 only: on L4 (100 aircraft) the guided worker cost more search than it found (paired
                       # FLEET_ITERS=3 PLANNER_WORKERS=4, L4 seeds 0-19: about -6 per seed, 6/20 worse)
TOURS_ITERS = 60       # ruin-and-recreate moves of the tours model per guided build

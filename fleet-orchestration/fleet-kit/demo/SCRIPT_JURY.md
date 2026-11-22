# Jury pitch: 2:30, English

SUB-15 Fleet Orchestration. Slot **2:30** (hard window 2:00 to 3:00), with a **2:00 cut** below. Jury: army officers and
investors. **One presenter**, who also drives the laptop: switch tabs with Cmd+1 to Cmd+5, play and pause with Space,
and click only where the table says "click". Demo scenario: **L4 seed 3** (100 drones: 15 scouts, 50 light and 35 heavy
strikers; 90 contacts), every page built from the tag `handin-final` (`c33b1ef`).

This is a sales pitch. Its structure follows a classic investor pitch:

1. **Hook:** one sentence that frames the problem.
2. **Problem:** make the jury feel how hard it is, then show what the simple approach gets.
3. **Solution, shown live:** the same scenario solved, then the radio link cut.
4. **Why us:** four reasons, each one measured.
5. **Close:** restate the problem and our answer in one breath.

What the jury must leave with: the problem is coordination, not drones; our solution is the one that wins, never
breaks a rule, survives losing comms and explains itself. Every number is measured; the "Facts behind the lines"
section says where each comes from.

## Pitch (2:30)

Times are targets: the spoken text runs 2:13 at 140 words per minute, and clicks bring it to about 2:25 (see "How it
was timed").

### 1. Hook (0:00 to 0:15)

| Time | On screen / click | Say |
|---|---|---|
| 0:00 | Tab 1 `view_greedy.html`, at t = 0: the whole map, 90 contacts, the base at the bottom left. | "Europe builds excellent drones, for every kind of mission. On the front line, the hard part is no longer the drone. It's making a hundred of them fight as one team." |

### 2. The problem (0:15 to 0:58)

| Time | On screen / click | Say |
|---|---|---|
| 0:15 | Still tab 1. Press **Space** (play the kit's simple plan); set **32×** first if it isn't. | "A striker may only fire after a scout has watched and confirmed the target. Some targets need three or four strikers hitting within the same twenty seconds. Each striker flies once." |
| 0:28 | Point at the base, bottom left, as the drones leave it. Then at a green civilian square next to red hostiles. | "All of them leave one base, stay forty metres apart, and never strike within two hundred metres of a civilian or a friendly. Every target has a time window, every drone a battery." |
| 0:42 | Point at the score panel: **532.9**. | "And when the radio link dies, each drone decides alone. Plan it the simple way, one target at a time, and on this hundred-drone scenario you serve 18 contacts out of 70." |

### 3. Our solution, shown (0:58 to 1:25)

| Time | On screen / click | Say |
|---|---|---|
| 0:58 | **Cmd+2** `view_ours.html` (Layers tab open, **Won vs greedy** ticked, 32× selected). Press **Space**. Point at **1064.6**, **VALID** and the green rings. | "We built the planner that solves it. Same scenario: 39 contacts instead of 18, twice the score, every rule respected. It builds a plan, then keeps improving it on every core." |
| 1:11 | **Cmd+3** `view_linkloss.html` (Link tab open). Click **`popup_zone t = 618 · r 82 m`**: the page jumps to 615 s, banner `LINK CUT · POLICY IN COMMAND`. | "When the link is cut, our policy flies on board: a no-fly zone pops up across a strike," |
| 1:16 | Press **Space**, count **four** seconds, press **Space** (about t = 645 s). Point at the four orange hold rings next to the zone labelled `NEW`, just right of `Z02`. | "and the whole group holds." |

The four are H02, L02, L10 and L27, all due to strike C47: L02 holds at 639 s, the other three at 640 s, on its message.
Three seconds of playback stops at 639 s, before the hold: count four.

### 4. Why us (1:25 to 2:08)

| Time | On screen / click | Say |
|---|---|---|
| 1:25 | **Cmd+4**: the numbers slide (text below). | "Why us? Four reasons. One: it wins where it matters. On fifty large scenarios we never tuned on, 2.2 times the baseline, and never below it on any of 200." |
| 1:37 | Point at "0 invalid plans". | "Two: it never breaks a rule. Zero invalid plans, and a safety net that always hands in a valid one." |
| 1:45 | Point at the link-loss lines. | "Three: it survives losing comms. Zero failed runs on the official grid, down to fifty bytes per second." |
| 1:53 | **Cmd+5** `view_ops.html`, **Why** tab, card **C35** already open (`SERVED H+00:05:34`). | "Four: the operator stays in charge. Every decision is explained: who saw the target, who confirmed it, who struck, how far the nearest friendly was." |

### 5. Close (2:08 to 2:25)

| Time | On screen / click | Say |
|---|---|---|
| 2:08 | Stay on the C35 card. Look at the jury, not the screen. | "Europe has the drones. The difference now is the brain that makes them fight as one team, safely, even when the link goes dark. We built it, and it runs on a laptop today. Thank you." |

About 5 s spare before 2:30.

## The 2:00 cut

Use it if the slot turns out to be 2:00, or if the timer shows more than 0:58 when you switch to tab 2. Same clicks;
drop these lines:

| Part | Line that goes | Saves |
|---|---|---|
| 1 | "...for every kind of mission" | ~2 s |
| 2 | "Each striker flies once." | ~2 s |
| 2 | "Every target has a time window, every drone a battery." | ~5 s |
| 3 | "It builds a plan, then keeps improving it on every core." | ~5 s |
| 4 | "...and a safety net that always hands in a valid one" | ~5 s |
| 5 | "We built it, and it runs on a laptop today." | ~4 s |

The cut spoken text runs 1:51 at 140 words per minute, about 2:01 with clicks. Never cut the 18-out-of-70 line, the
link cut, or any of the four reasons: they are the pitch.

## Numbers slide (one screen)

```
Why us, measured

1  IT WINS WHERE IT MATTERS
   Final test: seeds 9000–9049, never used for tuning · 200 runs
   Total ×1.605 vs the kit baseline (99,580 vs 62,029)
   L1 ×1.088 · L2 ×1.073 · L3 ×1.265 · L4 (100 drones) ×2.22
   0 of 200 seeds below baseline

2  IT NEVER BREAKS A RULE
   0 invalid plans in 200 + 125 + 8 runs
   8 public scenarios: 8/8 valid · slowest 39.5 s of the 60 s limit

3  IT SURVIVES LOSING COMMS
   Official link-loss grid, two seed sets: sizing score 1.00 / 1.00
   0 failed runs · meets the bar down to 50 B/s at every range

4  THE OPERATOR STAYS IN CHARGE
   A Why card for every contact · Python standard library · no GPU
```

## Q&A reserve

Sales questions first, then technical ones.

| Likely question | Answer (1–2 sentences) |
|---|---|
| Why is yours better than the other teams'? | We can't see their numbers. What we can show: results on seeds we never tuned on, never below the baseline, zero invalid plans, zero failed link-loss runs, and an explanation for every decision. Ask every team for those five. |
| Who uses it, and when? | The drone unit's mission planner, before launch: fleet, contacts and zones in; a valid plan and a one-page brief out in under a minute. If the link drops in flight, the policy on each drone takes over. |
| What would it take to field it? | Real sensor data with its uncertainty, real radios, the unit's own data formats, and a legal review of the engagement rules. None of that is in the challenge kit, so we don't claim it. |
| Why does the simple plan only get 18 of 70? | It takes targets one at a time in a fixed order and never revisits a choice, so early picks block later ones; in our rejection counts its main wall is the 40 m separation. Our search reorders the targets so more of them fit: on our plan all 50 light strikers are in use. |
| How many cores does it need? | We measured the final set with only 2 cores per run. It uses up to 8 worker processes, capped by the machine's core count; on one core it is still valid and never below baseline, because the kit's plan is always the floor. |
| Why not machine learning? | Learned solvers need torch and a GPU, and they don't handle synchronised strikes or the 40 m separation; in 60 s on a laptop, a search over explicit rules did better. It also lets us explain every decision by rule, which a network can't. |
| What happens at 500 drones? | The search budget shrinks with fleet size (38 s at 100, 22 s at 500) to keep the run under 60 s, and the safety net always writes a valid plan. An earlier version was valid up to 500; we haven't re-timed the final version at that size, so we claim no ratio there. |
| What if the planner crashes or runs out of time? | A plan file is written before the search starts, the search has a time limit, a 52 s alarm writes the best valid plan found, any error falls back to the kit's plan, and we keep the kit's plan whenever it scores better. Each fault is tested by injecting it. |
| How do you know a plan is legal? | Every plan goes through the kit's own validator before we write it; an invalid plan is never handed in. |
| How do the drones learn about the zone? | Two drones within 300 m sense it the second it appears and broadcast it; drones whose route stays clear carry on. L02 holds at 639 s before its route enters the zone, and the rest of its strike group holds one second later, on its message. |
| Where does the link-loss policy fail? | One known case: on scenario L3-6, retention is 0.611, because two drones abort just after take-off and hover over the base, head-on with departing drones. Flying them home fixed it but broke three other scenarios, so we didn't ship that. |
| Why so many messages? Could you cut traffic? | We tried a lower-traffic variant: better on paper (0.967 against 0.949) but one failed run at 250 m. A failed run scores zero, so we kept the safer policy. |
| What did you try that didn't work? | Squeaky Wheel reordering +0.13 % (noise), light-striker pricing ±0.5 %, scout tours +0.12 %, altitude layers for strike groups (noise), constant tuning (not enough compute to prove a gain). We keep a change only if it beats the noise. |
| Why leave an 85-point target? | Three reasons, each on a Why card: a rule (C27 is 140 m from a civilian), resources (C50 needs 4 light strikers and all 50 are in use), or reach (C37: no route reaches it in its time window). |
| Is ×2 cherry-picked? | The demo is one seed (×2.0). The ×2.22 is the total over 50 unseen L4 seeds, and none of the 200 final runs is below baseline. |

If asked about margins: the **Alerts** tab of `view_ops.html` ranks the tightest ones. Top line: L07 and L34 come
within 41 m at H+00:06:48 (limit 40 m); the tightest confirmation is C04, struck 10.3 s after its observation (minimum
10 s).

## Facts behind the lines

| Line | Fact | Source |
|---|---|---|
| "watched and confirmed" | A scout observes for 20 s; the strike comes at least 10 s after the observation ends (R4). | scenario `rules`, kit README |
| "three or four strikers within the same twenty seconds" | All the strikers a contact needs must hit inside a 20 s window (R10); C16 and C50 need 4 light strikers each. | scenario `rules`, `explication.md` |
| "Each striker flies once" | A striker's route ends with its strike. | kit README, R1 |
| "forty metres apart", "two hundred metres" | `d_sep_m` 40 (R8); `collateral_radius_m` 200 (R7). | scenario `rules` |
| "18 contacts out of 70" | Kit plan: 18 served of 70 hostile or unknown contacts; ours: 39. | `explication.md` |
| "twice the score" | 532.9 → 1064.6, valid. | kit scorer, on screen |
| "the whole group holds" | Cut at 434 s; zone at 618 s; L02 holds at 639 s, H02, L10, L27 at 640 s; run completed, 2086 of 2086 reachable points. | simulator rerun at 1 Hz |
| "2.2 times", "never below on any of 200" | Final set 9000–9049: L4 ×2.22, total ×1.605, 0 of 200 below. | final-set bench (CP5) |
| "zero invalid plans" | 0 invalid in the final set (200), the shift suite (125) and the 8 public scenarios. | bench, shift suite, `check_handin.py` |
| "zero failed runs, down to fifty bytes per second" | Sizing score 1.00 / 1.00, 0 failed runs, frontier 50 B/s at 250 to 2000 m. | `handin/LINKLOSS_FRONTIER.md` |
| "who saw, who confirmed, who struck, how far the nearest friendly was" | C35: S01 observed, confirmed 41.3 s later, H14, H11, L48 struck; nearest friendly C72 at 1189 m. | `view_ops.html` Why card |
| "runs on a laptop" | Python standard library only, no GPU; slowest public scenario 39.5 s of 60 s. | `check_handin.py` |

Link-loss times against the kit's rules (`LINKLOSS.md`), rerun at the simulator's 1 Hz step (the viewer samples every
2 s):

| Moment | Time | Rule it follows |
|---|---|---|
| Link cut | 434 s, 0.48 of the plan (last waypoint 899.5 s) | the cut falls a quarter to half of the way through the plan |
| L47 fails | 500 s, on the ground (planned take-off 513.7 s) | `failure` removes the drone; nobody senses it |
| Pop-up zone | 618 s; H02 and L22 sense it that second and broadcast it | sensed by drones within 300 m |
| L02 holds | 639 s, before its route enters the zone | the policy decides once per second; `hold` is the only way to avoid a danger |
| H02, L10, L27 hold | 640 s | messages arrive one step later; the group aborts together |
| End | 900 s; 2086 of 2086 reachable points (C47 and L47's C32 are lost for the reference too) | judged on real times; retention = points / reference points |

## If the live demo fails

1. **Server down or browser stuck:** open the same files straight from the demo folder (double-click). The pages are
   self-contained and make no network calls. Reload a stuck tab with Cmd+R: it restarts at t = 0, and the Link tab's
   event buttons jump straight to the right moment.
2. **The `popup_zone` button does nothing:** drag the timeline to the second orange diamond (t ≈ 618 s;
   the red dashed line before it is the cut at 434 s), press Space, pause at t ≈ 645 s.
3. **Laptop, browser or projector fails:** present from the backup deck (exported PDF on the laptop and a phone); its
   speaker notes carry these lines, slide by slide.
4. **Any number disputed:** point to the "Facts behind the lines" table and offer the repo.

## Pre-pitch checklist (5 minutes)

- [ ] Start the server: the `demo` preview in the Claude app, or
      `/usr/bin/python3 -m http.server 8766 --bind 127.0.0.1 --directory <demo folder>`. Check that
      `http://localhost:8766/view_ours.html` loads.
- [ ] Open the tabs in this order (Cmd+1 to Cmd+5):
  1. `view_greedy.html`: at t = 0, **32×** selected, score **532.9**.
  2. `view_ours.html`: **Layers** tab open, **Won vs greedy** ticked, **32×** selected, at t = 0, score **1064.6**.
  3. `view_linkloss.html`: **Link** tab open, at t = 0, speed **8×** (default), banner `LINK UP`.
  4. The numbers slide.
  5. `view_ops.html`: **Why** tab, click **C35** so its card is open.
- [ ] Dry-run tab 3 once: `popup_zone`, Space, four seconds, Space (~645 s), see the four orange rings. Then reload the
      tab so it starts again at t = 0.
- [ ] Browser full screen; zoom until the score panel reads from the back of the room.
- [ ] Do Not Disturb on, sound off, charger in.
- [ ] Timer where you can see it. Rule: more than 0:58 when you switch to tab 2 → the 2:00 cut.
- [ ] Backup deck exported as PDF on the laptop; this Q&A table on paper or a phone.

## Demo assets

Built from `handin-final` on L4 seed 3:

| File | Shows |
|---|---|
| `view_greedy.html` | Kit plan: 532.9, 1140 points, 35 strikers. |
| `view_ours.html` | Our plan with Swann's comparison layers: 1064.6, valid, 2207 points, 63 strikers; 39 contacts served against 18; won 21, lost 0. |
| `view_ours_plain.html` | The same plan without the comparison layers (spare). |
| `view_linkloss.html` | Link-loss replay, `handin/policy.py`, 1000 m × 200 B/s, events seed 4 (cut at 434 s, L47 fails at 500 s, pop-up zone at 618 s): run completed without failure, 100 % retention, 2626 messages, 13.3 per drone per minute. |
| `view_ops.html` | Louis's operator view: Why, Feed, Alerts tabs; Brief on key B. |
| `explication.md` | Swann's report for the same plan: the reason for every contact not served. |

To rebuild into `/tmp/jury/`, from `fleet-kit/` at the tag (the planner is time-limited, so a rebuilt plan can score
slightly differently from 1064.6; check the numbers on screen against this script):

```
mkdir -p /tmp/jury
python3 -m fleetkit generate L4 3 -o /tmp/jury/scenario.json
python3 -m fleetkit baseline /tmp/jury/scenario.json -o /tmp/jury/greedy.json
python3 handin/planner.py /tmp/jury/scenario.json /tmp/jury/plan.json
python3 -m fleetkit events /tmp/jury/scenario.json /tmp/jury/plan.json --seed 4 -o /tmp/jury/events.json
python3 -m fleetkit view /tmp/jury/scenario.json /tmp/jury/greedy.json -o /tmp/jury/view_greedy.html
python3 demo/swann_demo.py /tmp/jury/scenario.json /tmp/jury/plan.json -o /tmp/jury/out   # out/view.html = view_ours.html
python3 -m fleetkit view /tmp/jury/scenario.json /tmp/jury/plan.json --events /tmp/jury/events.json --policy handin/policy.py --setting 1000,200 -o /tmp/jury/view_linkloss.html
python3 demo/opsview/opsview.py /tmp/jury/scenario.json /tmp/jury/plan.json -o /tmp/jury/view_ops.html
```

`swann_demo.py` names its layers in French (`Gagnés vs glouton` = Won vs greedy, `Perdus` = lost, `À gagner` = still
winnable, `Concurrence ressources` = resource conflict, `Bloqués` = blocked). The live copy has them translated to
English.

## How it was timed

- Each part's spoken text was read by macOS `say` (voice Samantha, default rate) and measured with `afinfo`, then
  checked against a slower human pace of 140 words per minute.
- 2:30 version: 310 words, 1:44 by `say`, 2:13 at 140 wpm. Add about 12 s for four tab switches, the `popup_zone`
  click and the four-second playback: **about 2:25**.
- 2:00 cut: 259 words, 1:29 by `say`, 1:51 at 140 wpm, **about 2:01** with clicks.
- Playback speeds were measured in the browser: 8× moves 16 s of mission per 2 s, so t = 615 to 645 s takes about 4 s;
  32× plays the whole 900 s mission in 28 s.
- Still to do: one rehearsal out loud, clicking for real, with a stopwatch. People presenting in a second language
  often speak slower than 140 wpm; if the run goes over 2:30, use the 2:00 cut.

# Jury script: 2:30, English

SUB-15 Fleet Orchestration. Slot **2:30** (hard window 2:00 to 3:00), with a **2:00 cut** below. Jury: army officers and
investors. **One presenter**, who also drives the laptop: switch tabs with Cmd+1 to Cmd+5, play and pause with Space,
and click only where the table says "click". Demo scenario: **L4 seed 3** (100 aircraft, 90 contacts), every page built from the tag `handin-final`
(`c33b1ef`). Every number below is measured; the numbers slide says where each one comes from.

What we want the jury to remember:
1. On the largest scenarios we score **2.2 times** the kit baseline, on seeds we never used for tuning, and never
   below it.
2. When the link drops, our aircraft finish safely: **zero failed runs** on the official link-loss grid.
3. Every decision can be explained to an operator, rule by rule.

## Script (2:30)

Times are targets. The spoken text runs 2:13 at 140 words per minute; the rest is clicks (see
"How it was timed").

### Beat 1: why we're different (0:00 to 0:20)

| Time | On screen / click | Say |
|---|---|---|
| 0:00 | Tab 1 `view_greedy.html`, at t = 0. | "Every team got the same kit. Two things set us apart. On the largest scenarios, a hundred aircraft, we score 2.2 times the kit baseline, on seeds we never saw. And when the radio link drops, our aircraft carry on safely: zero failed runs on the official grid." |

### Beat 2: ours against the kit greedy plan (0:20 to 0:52)

| Time | On screen / click | Say |
|---|---|---|
| 0:20 | Still tab 1: score panel **532.9**. | "Same scenario for both. Kit greedy: 533 points." |
| 0:24 | **Tab 2** `view_ours.html` (Layers tab open, **Won vs greedy** ticked, 32× selected). Score **1064.6**, **VALID**. Press Space to play. | "Ours: 1065, valid on all ten rules." |
| 0:28 | Point at the green rings (`+88 pts`, `+91 pts`, ...). Playback runs the whole mission in 28 s. | "Each green ring is a contact we serve and greedy misses: 21 of them, and we lose none. How: a fast builder, then a search over target order on every core, inside the time limit." |
| 0:42 | Leave it playing. | "Aircraft stay 40 metres apart, take-offs are staggered on the shared pad, and hostiles that can never be legally struck are skipped." |

### Beat 3: proof on unseen seeds (0:52 to 1:17)

| Time | On screen / click | Say |
|---|---|---|
| 0:52 | **Tab 3**: numbers slide (text below). | "One scenario proves nothing. Final test: 200 runs on fresh seeds, never used for tuning. 1.6 times the baseline overall, 2.2 on the largest level." |
| 1:03 | Point at the "0 of 200" line. | "Zero invalid plans, and zero seeds below baseline, by construction: we hand in the better of our plan and the kit's. Five shifted generators, like low battery: 1.98 times." |

### Beat 4: the link drops (1:17 to 1:52)

| Time | On screen / click | Say |
|---|---|---|
| 1:17 | **Tab 4** `view_linkloss.html`, at t = 0, **Link** tab open. Banner: `LINK UP · FOLLOWING THE PLAN`. | "Now the link is cut, at 434 seconds." |
| 1:20 | Click **`popup_zone t = 618 · r 82 m`** in the Link tab. The page jumps to t = 615 s; banner turns to `LINK CUT · POLICY IN COMMAND`. | "Each aircraft decides alone, with our policy on board. At 618 seconds a no-fly zone pops up across a four-aircraft strike." |
| 1:30 | Press Space (8×). Count **four** seconds, press Space again: about **t = 645 s**. Three seconds stops at 639 s, before the hold. | "Watch:" |
| 1:34 | Point at the **four orange hold rings** next to the zone labelled `NEW`, just right of `Z02`. They are H02, L02, L10, L27, all due to strike C47; they hold from t = 640 s. | "all four stop and hold, in orange. The strike is dropped as a group, and nobody fires without a confirmed observation." |
| 1:43 | Point at the top right: `RUN COMPLETED WITHOUT FAILURE`, **100 % retention**, points 2086 of 2086. | "Every reachable point kept. On the official grid: zero failed runs, down to 50 bytes per second." |

### Beat 5: every decision explained (1:52 to 2:12)

| Time | On screen / click | Say |
|---|---|---|
| 1:52 | **Tab 5** `view_ops.html`, **Why** tab, card **C35** already open (`SERVED H+00:05:34`). | "Every decision is explained. Contact C35: seen by scout S01, confirmed 41 seconds later, struck by three aircraft. Nearest friendly: 1.2 kilometres; we never strike within 200 metres." |
| 2:04 | Click **C27** in the Why list (verdict `R7`). Card: "Forbidden by R7: 140 m from C84 (civilian), limit 200 m. No valid plan can serve it." | "Refused targets show the rule, like C27, 140 metres from a civilian." |

### Beat 6: close (2:12 to 2:25)

| Time | On screen / click | Say |
|---|---|---|
| 2:12 | Stay on the C27 card. | "Standard Python, no GPU: it runs on a laptop in under a minute. As a product: it proposes the plan, explains each choice, and the operator decides. Thank you." |

About 5 s spare before 2:30.

## The 2:00 cut

Use it if the slot turns out to be 2:00, or if the clock shows more than 0:55 at the start of beat 3. Drop these lines
and keep everything else, with the same clicks:

| Beat | Line that goes | Saves |
|---|---|---|
| 2 | "...take-offs are staggered on the shared pad, and hostiles that can never be legally struck are skipped." Keep only "Aircraft stay 40 metres apart." | ~7 s |
| 3 | "One scenario proves nothing." | ~2 s |
| 3 | "Five shifted generators, like low battery: 1.98 times." | ~4 s |
| 5 | "Refused targets show the rule, like C27, 140 metres from a civilian." Skip the C27 click. | ~6 s |
| 6 | "Standard Python, no GPU: it runs on a laptop in under a minute." | ~5 s |

The cut spoken text runs 1:50 at 140 words per minute, about 2:00 with clicks. Never cut beat 1, the numbers in beat 3
or the link-loss beat: they are the two edges.

## Numbers slide (one screen)

```
Measured, not estimated

FINAL TEST: seeds 9000–9049, never used for tuning
200 runs · Python 3.9.6 · 2 cores per run
  Total vs kit greedy     ×1.605   (99,580 vs 62,029)
  By level                L1 ×1.088 · L2 ×1.073 · L3 ×1.265 · L4 ×2.22
  Invalid plans           0
  Seeds below baseline    0 of 200 (we return the better of ours and the kit's)

8 PUBLIC SCENARIOS        8/8 valid · 4252.9 vs 2748.6 · slowest 39.5 s of 60 s
5 SHIFTED GENERATORS      125 runs · 0 invalid · none below baseline · ×1.98
(low battery, more points, no feasibility, L3-on-L4, half scouts)

LINK LOSS (official sizing grid, seeds 5–14 and 15–24)
  Sizing score 1.00 / 1.00 · 0 failed runs
  Meets the bar down to 50 B/s at 250, 500, 1000 and 2000 m

Python standard library only · no GPU
```

Sources: final-set bench (Mahmoud, CP5); `handin/check_handin.py` on an idle machine; shift suite measured on `main`
`f0a5f14`, just before the keep-better-greedy guard (that guard can only raise a seed's score);
`handin/LINKLOSS_FRONTIER.md`.

## Q&A reserve

| Likely question | Answer (1–2 sentences) |
|---|---|
| How many cores does it need? | We measured the final set with only 2 cores per run. It uses up to 8 worker processes, capped by the machine's core count; on one core it is still valid and never below baseline, because the kit greedy plan is always the floor. |
| Why not machine learning? | Learned solvers need torch and a GPU, and they don't handle synchronised strikes or the 40 m separation; in 60 s on a laptop, a local search over explicit rules did better. It also lets us explain every decision by rule, which a network can't. |
| What happens at 500 aircraft? | The search budget shrinks with fleet size (38 s at 100 aircraft, 22 s at 500) to keep the run under 60 s, and the safety net always writes a valid plan. An earlier version was valid up to 500 aircraft; we haven't re-timed the final version at that size, so we claim no ratio there. |
| What if the planner crashes or runs out of time? | A plan file is written before the search starts, the search has a time limit, a 52 s alarm writes the best valid plan found, any error falls back to the kit greedy plan, and we keep greedy's plan whenever it scores better. Each fault is tested by injecting it. |
| How do you know a plan is legal? | Every plan goes through the kit's own validator before we write it; an invalid plan is never handed in. Zero invalid across the 200 + 125 + 8 runs above. |
| Where does the link-loss policy fail? | One known case: on scenario L3-6, retention is 0.611, because two aircraft abort just after take-off and hover over the base, head-on with departing aircraft. Flying them home fixed it but broke three other scenarios, so we didn't ship that. |
| Why so many messages? Could you cut traffic? | We tried a lower-traffic variant: better on paper (0.967 against 0.949) but one failed run at 250 m. A failed run scores zero, so we kept the safer policy. |
| What did you try that didn't work? | Squeaky Wheel reordering +0.13 % (noise), light-effector pricing ±0.5 %, scout tours +0.12 %, altitude layers for strike groups (noise), constant tuning (not enough compute to prove a gain). We keep a change only if it beats the noise. |
| Why leave an 85-point target? | Three reasons, each on a Why card: a rule (C27 is 140 m from a civilian), resources (C50 needs 4 light effectors and all 50 are in use), or reach (C37: the real router finds no route in its time window). |
| Is ×2 cherry-picked? | The demo is one seed (×2.0). The ×2.22 is the total over 50 unseen L4 seeds, and none of the 200 final runs is below baseline. |
| What does the product look like? | A planning aid next to the operator: it takes the fleet, contacts and zones, returns a valid plan in under a minute on a laptop, with a Why card per contact, a ranked list of the tightest margins and a one-page brief (key B). The operator approves; if the link drops, the on-board policy keeps the aircraft safe. |
| Why small gains on L1 and L2? | On small scenarios the greedy plan already gets most of what's possible. The gain comes where aircraft and effectors are contested: on the L4 demo all 50 light effectors are in use. |

If asked about margins: the **Alerts** tab of `view_ops.html` ranks the tightest ones. Top line: L07 and L34 come
within 41 m at H+00:06:48 (limit 40 m); the tightest confirmation is C04, engaged 10.3 s after its observation (minimum
10 s).

## If the live demo fails

1. **Server down or browser stuck:** open the same files straight from the demo folder (double-click). The pages are
   self-contained and make no network calls. Reload a stuck tab with Cmd+R: it restarts at t = 0, and the Link tab's
   event buttons jump straight to the right moment.
2. **The `popup_zone` button does nothing:** drag the timeline to the second orange diamond (t ≈ 618 s;
   the red dashed line before it is the cut at 434 s), press ▶, pause at t ≈ 645 s.
3. **Laptop or projector fails:** play the backup video (`VIDEO_SECOURS.md`). That plan predates these numbers and the
   video, if recorded, shows the older plan (1076.7 instead of 1064.6): say "this is an earlier build". If there is no
   video, give the script from the printed numbers slide, without the screen.
4. **Any number disputed:** give the numbers slide source line and offer the repo.

## Pre-pitch checklist (5 minutes)

- [ ] Start the server: the `demo` preview in the Claude app, or
      `/usr/bin/python3 -m http.server 8766 --bind 127.0.0.1 --directory <demo folder>`. Check that
      `http://localhost:8766/view_ours.html` loads.
- [ ] Open the tabs in this order (Cmd+1 to Cmd+5):
  1. `view_greedy.html`: at t = 0, score **532.9**.
  2. `view_ours.html`: **Layers** tab open, **Won vs greedy** ticked, **32×** selected, at t = 0, score **1064.6**.
  3. The numbers slide.
  4. `view_linkloss.html`: **Link** tab open, at t = 0, speed **8×** (default), banner `LINK UP`.
  5. `view_ops.html`: **Why** tab, click **C35** so its card is open.
- [ ] Dry-run tab 4 once: `popup_zone`, Space, four seconds, Space (~645 s), see the four orange rings. Then click `popup_zone` again so
      it sits at 615 s, or reload the tab.
- [ ] Browser full screen; zoom until the score panel reads from the back of the room.
- [ ] Do Not Disturb on, sound off, charger in.
- [ ] Stopwatch or phone timer where you can see it. Rule: if it shows more than 0:55 when you open tab 3, switch to
      the 2:00 cut.
- [ ] Numbers slide printed, and this Q&A table on paper or a phone.

## Demo assets

Built from `handin-final` on L4 seed 3:

| File | Shows |
|---|---|
| `view_greedy.html` | Kit greedy plan: 532.9, 1140 points, 35 effectors. |
| `view_ours.html` | Our plan with Swann's comparison layers: 1064.6, valid, 2207 points, 63 effectors; 39 contacts served against 18; won 21, lost 0. |
| `view_ours_plain.html` | The same plan without the comparison layers (spare). |
| `view_linkloss.html` | Link-loss replay, `handin/policy.py`, 1000 m × 200 B/s, events seed 4 (cut at 434 s, L47 fails at 500 s, pop-up zone at 618 s): run completed without failure, 100 % retention, 2626 messages, 13.3 per aircraft per minute. |
| `view_ops.html` | Louis's operator view: Why, Feed, Alerts tabs; Brief on key B. |
| `explication.md` | Swann's report for the same plan: reason for every contact not served. |

To rebuild into `/tmp/jury/`, from `fleet-kit/` at the tag (the planner is time-limited, so a rebuilt plan can score slightly differently
from 1064.6; check the numbers on screen against this script):

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

- Each beat's spoken text was read by macOS `say` (voice Samantha, default rate, about 155 words per minute with
  pauses) and measured with `afinfo`, then checked against a slower human pace of 140 words per minute.
- 2:30 version: 311 words, 2:05 by `say`, 2:13 at 140 wpm. Add about 12 s for four tab switches, three clicks and
  the four-second playback in beat 4: **about 2:25**.
- 2:00 cut: 257 words, 1:43 by `say`, 1:50 at 140 wpm, **about 2:00** with clicks.
- Playback speeds were measured in the browser: 8× moves 16 s of mission per 2 s, so t = 615 to 645 s takes about 4 s;
  32× plays the whole 900 s mission in 28 s.
- Still to do: one rehearsal out loud, clicking for real, with a stopwatch. People presenting in a second language
  often speak slower than 140 wpm; if the run goes over 2:30, use the 2:00 cut.

# Jury pitch: 2:30, English

SUB-15 Fleet Orchestration. Slot **2:30** (hard window 2:00 to 3:00), with a **2:00 cut** below. Jury: army officers,
investors, potential military customers, mostly **not technical**. **One presenter**, who also drives the laptop.
Every figure comes from the tag `handin-final` (`c33b1ef`) or the team brief, as "Facts behind the lines" says.

The pitch is **planning-first**: the core challenge is planning a hundred drones as one team before the mission.
Link loss is a **bonus**, one slide near the end, with **no figures** (the link-loss PRs #19 and #23 are not merged).

**Plain words on stage.** Outcomes first, no kit jargon in the spoken lines or on the slides: no "seeds", "validator",
"R4", "hill-climbing", "worker processes". The exact figures sit in the deck's speaker notes ("If asked"), in the Q&A
table and in "Facts behind the lines".

**Never say on stage or in answers:**

- "never below the baseline": two test cases are a hair under it;
- "same score on one core": not measured (the scores were measured with 2 cores per run);
- "same situation, same plan": not guaranteed, the search is time-limited and spread over the available cores;
- any link-loss figure (runs, failures, retention, messages, times).

Story:

1. **Hook:** a hundred drones, one safe plan, in under 40 seconds.
2. **Problem:** nobody can plan that by hand in real time.
3. **Goal:** most mission value, zero rule violations.
4. **Solution:** who confirms, who strikes, which route, what time, in under 40 seconds.
5. **Results:** ×2.1 at full scale, ×1.6 across all sizes, under 40 seconds.
6. **Safe by design.** 7. **Explainable.** 8. **Light and deployable.** 9. **Predictable and auditable.**
10. **Bonus: link loss.** 11. **Next.** 12. **Close.**

**One browser tab only:** the deck, in presentation mode. Advance with the right arrow. No live viewer in the main
flow; the demo pages are spares for the Q&A.

## Pitch (2:30)

Times are targets: the spoken text is **305 words, 2:11 at 140 words per minute**; one second per slide change brings
it to **about 2:23** (see "How it was timed").

### 1. Hook (0:00 to 0:10)

| Time | On screen / click | Say |
|---|---|---|
| 0:00 | Slide 1 (**A hundred drones. One safe plan. In under 40 seconds.**). | "Europe builds excellent drones. The hard part is planning a hundred of them as one team, safely, in the time you have." |

### 2. The problem (0:10 to 0:32)

| Time | On screen / click | Say |
|---|---|---|
| 0:10 | **→** slide 2 (**No commander can hand-plan a 100-drone strike in real time**). | "A commander has a hundred drones, scouts and strikers, dozens of targets, civilians nearby, no-fly zones." |
| 0:18 | Point at the 40 m and 20 s cards. | "Every strike confirmed first, drones forty metres apart, strikes within twenty seconds of each other." |
| 0:24 | Point at the bottom line. | "Nobody can plan that by hand in real time, and one mistake means a wrong target or a collision." |

### 3. The goal (0:32 to 0:40)

| Time | On screen / click | Say |
|---|---|---|
| 0:32 | **→** slide 3 (**Most mission value. Zero rule violations.**). | "Our goal: the most mission value, with zero rule violations. Safety is never traded for score." |

### 4. The solution (0:40 to 0:55)

| Time | On screen / click | Say |
|---|---|---|
| 0:40 | **→** slide 4 (**Every drone assigned, every route planned, in under 40 seconds**). Left to right: In, Planner, Out. | "In under forty seconds, our planner decides who confirms what, who strikes where, on which route, at what time." |
| 0:49 | Point at the middle box. | "It tries many variants in parallel and keeps the best safe one." |

### 5. Results (0:55 to 1:09)

| Time | On screen / click | Say |
|---|---|---|
| 0:55 | **→** slide 5 (**×2.1 mission value at full scale**). Look at the jury. | "On missions it had never seen: two point one times the mission value of the standard method at full scale, one point six times across all sizes, always under forty seconds." |

Check before the pitch which full-scale figure the team says: **×2.1** (team brief, 100 drones and 70 reachable
targets) or **×2.22** (this repo's final set, L4). The slide says ×2.1.

### 6. Safe by design (1:09 to 1:23)

| Time | On screen / click | Say |
|---|---|---|
| 1:09 | **→** slide 6 (**Zero invalid plans. Zero crashes.**). | "Safe by design: every plan is checked against all ten rules of engagement before release, a known-safe plan goes out if anything fails, and no strike happens without a scout's confirmation." |

### 7. Explainable (1:23 to 1:34)

| Time | On screen / click | Say |
|---|---|---|
| 1:23 | **→** slide 7 (**Every decision has a reason**). Point at the green card, then the red one. | "Every decision has a reason: this target was struck, this one skipped because a civilian is too close." |
| 1:32 | Look at the jury. | "The commander stays in control." |

### 8. Light and deployable (1:34 to 1:43)

| Time | On screen / click | Say |
|---|---|---|
| 1:34 | **→** slide 8 (**Runs on the laptop you already have**). | "Plain Python, no GPU, no training data. One core is enough; more cores mean more search, same safety." |

### 9. Predictable and auditable (1:43 to 1:51)

| Time | On screen / click | Say |
|---|---|---|
| 1:43 | **→** slide 9 (**Nothing hidden, nothing left to chance**). | "Every plan passes the same checks, and every improvement was kept only if it won on blind tests." |

### 10. Bonus: link loss (1:51 to 2:09)

| Time | On screen / click | Say |
|---|---|---|
| 1:51 | **→** slide 10 (**When comms fail, our drones get more careful, not more dangerous**). | "One bonus: when the radio is cut, the drones carry on alone." |
| 1:57 | Point at steps 2 and 3. | "If a target turns friendly or a no-fly zone appears, they warn each other and stop." |
| 2:04 | Look at the jury. | "When comms fail, our drones get more careful, not more dangerous." |

### 11. Next (2:09 to 2:13)

| Time | On screen / click | Say |
|---|---|---|
| 2:09 | **→** slide 11 (**From the planning table to the field**). | "Next: re-tasking in flight, then field trials." |

### 12. Close (2:13 to 2:23)

| Time | On screen / click | Say |
|---|---|---|
| 2:13 | **→** slide 12 (**We promise the best safe plan in the time you have.**). Look at the jury, not the screen. | "We don't promise the theoretical optimum. We promise the best safe plan in the time you have. Thank you." |

About 7 s spare before 2:30.

## The 2:00 cut

Use it if the slot turns out to be 2:00, or if the timer shows more than **1:05** when you reach slide 5 (planned 0:55).
Same slides, same clicks; drop these lines:

| Part | Line that goes | Saves |
|---|---|---|
| 2 | "Every strike confirmed first, drones forty metres apart, strikes within twenty seconds of each other." (the slide still shows it) | ~6 s |
| 4 | "It tries many variants in parallel and keeps the best safe one." (the middle box still shows it) | ~5 s |
| 9 | The whole line: leave the slide up one beat, say nothing, advance. | ~8 s |
| 10 | "If a target turns friendly or a no-fly zone appears, they warn each other and stop." | ~7 s |

The cut spoken text is **244 words, 1:45** at 140 words per minute, **about 1:57** with slide changes. Never cut the
results, "safe by design", the explained decision or the close: they are the pitch.

## Deck

The deck is a Claude Slides artifact (https://claude.ai/artifact/Sa6b5ogCyT77EG7GL9apLi, **private** until its owner
shares it); sources in `pitch/deck-final/`. Its speaker notes carry the lines above, slide by slide, plus the exact
figures under "If asked". The live deck needs internet: the offline fallback is `pitch/deck-final/deck_final.pdf`
(12 pages, **no speaker notes**, so keep this script on paper or a phone).

| # | Slide | Shows |
|---|---|---|
| 1 | Hook | A hundred drones. One safe plan. In under 40 seconds. Still of our full-scale plan. |
| 2 | The problem | No commander can hand-plan a 100-drone strike in real time. Cards: 100 drones, 90 contacts, 40 m, 20 s. No-fly zones, confirmation first; one mistake means a wrong target or a collision. |
| 3 | Our goal | Most mission value. Zero rule violations. |
| 4 | Our solution | In (the situation) → Our planner (many plans, one kept) → Out (the mission plan: who, where, which 3D route, when). |
| 5 | Results | ×2.1 at 100 drones and 70 reachable targets, ×1.6 across all sizes, under 40 s against a limit of 60 s. Standard method = the organisers' baseline planner. |
| 6 | Safe by design | Checked before release, a safe plan always ready, no strike without confirmation, 0 invalid plans in 333 test runs. |
| 7 | Explainable | Two decision cards: a target engaged (who confirmed, who struck) and one skipped (civilian 140 m away, inside 200 m). |
| 8 | Light and deployable | Plain Python, no GPU, no training data, no dependencies. Runs from a single core up. |
| 9 | Predictable and auditable | The same checks every time, every choice written down, every improvement proven before it was kept. |
| 10 | Bonus: link loss | Four steps: link cut, a surprise appears, the drones warn each other, the drones concerned call off their strike together. Still of the moment. No figures. |
| 11 | Next | Today: plan before take-off. Next: re-tasking in flight. Then: field trials. |
| 12 | Close | The closing line. |

## Q&A reserve

Answer in plain words first; the figures in brackets are there if someone presses. Be ready for the score questions.

| Likely question | Answer (1–2 sentences) |
|---|---|
| Your total score is behind other teams. Why pick you? | Some teams score more points, and we say so. We put our effort where a front line needs it: no rule ever broken, a safe plan always ready, every decision explained, on an ordinary laptop. |
| How do you compare with the standard method? | On 200 missions we never tuned on, from 5 to 100 drones, we get 1.6 times the mission value of the organisers' standard planner; at full scale about twice. (Final set, seeds 9000–9049, L1–L4: 99,580 against 62,029. L4 alone: ×2.22 in this repo; the slide's ×2.1 comes from the team brief.) Do not add "never below": two test cases are a hair under it. |
| Why is yours better than the other teams'? | We can't see their plans, so we don't claim it. What we can show: zero invalid plans in 333 runs, a safe plan always ready, and a reason for every decision. Ask every team for those. |
| Same situation, same plan? | Not always the exact same plan: the search has a time limit and uses the cores it finds, so two runs can differ a little. Every plan passes the same ten-rule check, every time. |
| Does it really run on one core? | Yes, it falls back to a single process. More cores give the search more tries, never weaker safety. (Our scores were measured with 2 cores per run; we have not measured the score on one core.) |
| Why under 40 seconds when the limit is 60? | Margin. The search stops at 38 seconds and an alarm writes the best safe plan at 52, so the plan is always in before the deadline. (Slowest run 39.5 s.) |
| What if the planning computer crashes or runs out of time? | A safe plan is saved before it starts thinking; if anything fails, the best safe plan found so far goes out, or the organisers' standard plan. We tested each fault by causing it on purpose. |
| Why leave a valuable target alone? | Three kinds of reasons, each shown to the commander: a rule (this one is 140 m from a civilian, the limit is 200 m), no drones left (one target needs four light strikers and all fifty are busy), or out of reach in its time window. |
| What happens when the radio is cut? | The drones carry on with their plan. The ones that see a surprise, a new no-fly zone or a target turning friendly, warn the others with short messages, and the drones concerned stop their strike together. No figures for now: that work is still being merged. |
| Why stop instead of flying around the zone? | The challenge gives a drone no way to invent a new route once the radio is cut: it can follow its plan, wait, slow down or turn back. Stopping is the safe answer, and it costs one strike, not the mission. |
| Who uses it, and when? | The drone unit's mission planner, before launch: fleet, targets and no-fly zones in; a safe plan with a reason for every choice out in under 40 seconds. |
| What would it take to field it? | Real sensor data with its uncertainty, real radios, the unit's own data formats, and a legal review of the engagement rules. None of that is in the challenge, so we don't claim it. |
| Why not machine learning? | Learned solvers need a graphics card and training data, and they handle badly strikes that must arrive together or the 40 m spacing. A search over explicit rules ran on a laptop in under a minute and lets us explain every decision by a rule. |
| What happens at 500 drones? | The search time shrinks with fleet size to stay under the limit, and the safety net always hands in a valid plan. We have not re-timed the final version at that size. |

## Facts behind the lines

| Line | Fact | Source |
|---|---|---|
| "a hundred drones, scouts and strikers" | Full scale (L4) is 100 aircraft: 15 scouts, 50 light and 35 heavy strikers. | scenario L4 seed 3 |
| "dozens of targets, civilians nearby, no-fly zones" (slide: 90 contacts) | L4 seed 3 has 90 contacts, with civilians, friendlies and no-fly zones. | scenario L4 seed 3 |
| "Every strike confirmed first" | R4: a scout observes the target at least 10 s before the strike. | `spec.md` (R4) |
| "drones forty metres apart" | R8: 40 m separation at all times. | `spec.md` (R8) |
| "strikes within twenty seconds of each other" | R10: all strikers of one target arrive within `sync_window_s` = 20 s. | `spec.md` (R10), scenario `rules` |
| "one mistake means a wrong target or a collision" | A plan breaking any rule is invalid and scores 0. | `spec.md` |
| "In under forty seconds" | Search stops at 38 s (`BUDGET_S`), alarm at 52 s (`ALARM_S`), limit 60 s; slowest final-set run 39.5 s. Budget shrinks above 100 aircraft (floor 10 s). | `handin/params.py`, `handin/planner.py`, final-set bench |
| "tries many variants in parallel and keeps the best safe one" | Restarts and hill-climbing over the contact order, up to 8 worker processes (`MAX_WORKERS`, capped by the core count), serial fallback; every kept step passes the official scorer, the final plan is re-validated. | `handin/planner.py` |
| "On missions it had never seen" | Final set, seeds 9000–9049, run once, never used for tuning. | `docs/ROADMAP.md` (seed sets) |
| "two point one times ... at full scale" (slide: 100 drones, 70 reachable targets) | **Team brief.** This repo has ×2.22 on L4 (final set). Confirm which one to say. | team brief; final-set bench |
| "one point six times across all sizes" | 99,580 against 62,029 on the final set, L1–L4 (200 missions, 5 to 100 drones). | final-set bench |
| "the standard method" | The organisers' greedy baseline planner, run on the same missions. | `fleetkit` baseline |
| "all ten rules of engagement" | R1–R10. | `spec.md` |
| "a known-safe plan goes out if anything fails" | `main()` writes an empty valid plan first; any exception falls back to the kit's greedy plan; the alarm writes the last kept plan. | `handin/planner.py` (`main`) |
| (slide 6) "0 invalid plans in 333 test runs" | 200 final set + 125 shift suite + 8 public scenarios, 0 invalid. | final-set bench, shift suite, `check_handin.py` |
| "this target was struck" | C35: observed by S01, struck by H14, H11, L48; nearest friendly 1189 m. | `view_ops.html` Why card |
| "this one skipped because a civilian is too close" | C27: 140 m from a civilian, inside the 200 m collateral radius (R7). | `view_ops.html` Why card, `explication.md` |
| (slide 7) three reasons | C50 needs 4 light strikers, all 50 busy; C37 has no route in its time window. | `view_ops.html`, `explication.md` |
| "Plain Python, no GPU, no training data" | Python standard library only; explicit rules, no learned model. | `check_handin.py`, `handin/` |
| "One core is enough; more cores mean more search, same safety" | Serial fallback; more workers only add search tries; the same check runs on every plan. Scores measured with 2 cores per run; the score on 1 core is not measured. | `handin/planner.py` |
| "Every plan passes the same checks" | Official validation on every kept step and on the final plan. | `handin/planner.py` |
| "every improvement was kept only if it won on blind tests" | A change was accepted only if it improved on the training seeds and the holdout seeds (5000–5049, never tuned on) agreed at checkpoints; final set run once at the end. | `docs/PLAN.md` (anti-overfitting), `docs/ROADMAP.md` |
| "when the radio is cut, the drones carry on alone" | After the cut, each drone runs its own on-board policy once per second. | `LINKLOSS.md`, `handin/policy.py` |
| "If a target turns friendly or a no-fly zone appears, they warn each other and stop" | Drones broadcast sensed dangers; a drone stops on a sensed or heard zone across its route, before a reclassified target, and when a teammate on the same target aborts. | `handin/policy.py` |
| "Next: re-tasking in flight, then field trials" | Roadmap, not a result. | team brief |

## If something fails

1. **No internet, or the deck does not load:** present from `pitch/deck-final/deck_final.pdf` (laptop or phone). The
   PDF has no speaker notes: say the lines from this script.
2. **Laptop or projector fails:** same PDF from a phone; keep going on the lines.
3. **Any number disputed:** point to the "Facts behind the lines" table and offer the repo.

## Pre-pitch checklist (5 minutes)

- [ ] The deck open in presentation mode, on slide 1, browser full screen.
- [ ] `deck_final.pdf` on the laptop and a phone.
- [ ] This script (lines and Q&A table) on paper or a phone, the score answer first.
- [ ] Team agreed on ×2.1 or ×2.22 for full scale.
- [ ] Do Not Disturb on, sound off, charger in.
- [ ] Timer where you can see it. Rule: more than 1:05 on slide 5 → the 2:00 cut.
- [ ] Optional, for the Q&A: the demo pages server running (see "Demo assets").

## Demo assets (Q&A spares only)

Built from `handin-final` on L4 seed 3; copies in `pitch/demo-pages/`, inputs in `pitch/demo-inputs/`. Serve them with
`python3 -m http.server 8766 --bind 127.0.0.1 --directory pitch/demo-pages` from `demo/`, or double-click the files.

| File | Shows | Use |
|---|---|---|
| `view_ops.html` | Louis's operator view: Why (C35 served, C27 refused), Feed, Alerts tabs; Brief on key B. | "Why skip a target?", "Who uses it?" |
| `view_greedy.html`, `view_ours.html` | Kit plan and our plan on the same mission (39 contacts handled against 18). | Score questions, if someone wants to see it. |
| `view_linkloss.html` | Link-loss replay. **Its panel shows figures: do not quote them.** | Only if asked to see link loss. |
| `explication.md` | The reason for every contact not served. | Paper backup for "why skip". |

If asked about margins: the **Alerts** tab of `view_ops.html` ranks the tightest ones (top line: L07 and L34 within
41 m, limit 40 m; tightest confirmation C04, 10.3 s, minimum 10 s).

## How it was timed

- Words counted per line and converted at 140 words per minute (a slower human pace), plus one second per slide change.
  Counted on Windows, so there is no macOS `say` measure for this version.
- 2:30 version: **305 words, 2:11** spoken, **about 2:23** with eleven slide changes.
- 2:00 cut: **244 words, 1:45** spoken, **about 1:57** with slide changes.
- Still to do: one rehearsal out loud with a stopwatch. People presenting in a second language often speak slower than
  140 wpm; if the run goes over 2:30, use the 2:00 cut.

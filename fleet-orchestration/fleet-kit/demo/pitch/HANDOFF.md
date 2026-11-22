# Jury pitch: handoff

## Update, Sun 22 Nov afternoon: link-loss pitch

The pitch is now built around **link loss and safety** (branch `feature/pitch-linkloss`):

- `../SCRIPT_JURY.md` rewritten in this order: hook, the link-cut problem, live link-loss demo, official sizing grid,
  five on-board rules, the rejected variant, planner safety nets, close. 312 words, about 2:25 with clicks; 2:00 cut
  240 words, about 1:55. Two tabs only: the deck and `view_linkloss.html`. Facts table updated.
- New deck: 8 pitch slides + 3 Q&A slides (Why cards, known limit, score if asked). Claude Slides artifact
  https://claude.ai/artifact/Sa6b5ogCyT77EG7GL9apLi (**private** until its owner shares it). Sources in
  `deck-linkloss/` (same layout as `deck/`, speaker notes = the spoken lines), offline backup
  `deck-linkloss/deck_linkloss.pdf` (11 pages, rendered from those sources, no speaker notes).
- `deck/`, `timing/` and the rest of this file describe the earlier sales-pitch version and are kept as they were.

Written Sun 22 Nov, 10:47 CET, by Mahmoud's session, for whoever picks up the pitch. Everything below is in this
folder or one level up, in `demo/`.

## Where it stands

| Piece | State | Where |
|---|---|---|
| **The script** (the source of truth) | Done, not rehearsed | `../SCRIPT_JURY.md` |
| Script in `main` | Old version only: PR #38 merged at 10:11 with the numbers-led draft | `main` |
| **Current script** | In **PR #39**, open, docs only, waiting for CI | branch `docs/jury-script` |
| **Backup deck** | Done, 15 slides, matches the current script | claude.ai artifact (private, see below); sources in `deck/` |
| Demo pages | Built from the frozen hand-in, checked click by click | `demo-pages/` (copies), inputs in `demo-inputs/` |
| Timing | 2:24 with clicks; 2:00 cut ≈ 1:58 | `timing/`, and "How it was timed" in the script |

PR #39: https://github.com/Prod-Project-ilhanld/AA-Hackathon-EDTH-202611/pull/39 (three commits on top of #38: exact
link-loss times, the sales-pitch rewrite, and the switch away from score ratios).

The deck: https://claude.ai/artifact/PBy8AFPkFLjKP7ZLHviVuG. **It is private.** Mahmoud has to share it with you from
the deck's Share menu (give edit access if you will change it). Until then, `deck/` holds every slide's source and
`tools/preview_deck.py` renders them locally.

## The decisions, and why

1. **English, 2:30 slot** (hard window 2:00 to 3:00), with a marked 2:00 cut. Jury: army officers and investors.
2. **One presenter**, who also drives the laptop: Cmd+1 to Cmd+5 for tabs, Space to play and pause.
3. **A sales pitch**, not a technical demo: hook, problem, solution shown live, four reasons why us, close.
4. **No score ratios on stage.** Other teams are ahead of us on total score, so the pitch sells what a front line needs:
   no rule ever broken, holds when the link drops, every decision explained, runs on a laptop. The ratios (×1.6, ×2.22)
   stay in the Q&A, behind an honest first answer ("some teams score more points, and we say so...").
5. **No product name.** It's framed as the answer to a front-line problem: "Europe builds excellent drones... the hard
   part is making a hundred of them fight as one team." ("Excellent", not "the best": nobody in the room can dispute it.)
6. **Never claim we beat the other teams.** We can't see their plans. The Q&A answer lists what we can prove instead.
7. **Every spoken claim has a source**: the "Facts behind the lines" table in the script. Keep it that way.

## What's left

- [ ] **Rehearse out loud with a stopwatch**, clicking for real. Not done yet. If it runs over 2:30, use the 2:00 cut.
- [ ] **Merge PR #39** once CI is green.
- [ ] **Share the deck** (Mahmoud), then **export it as PDF** (Share › Export) onto the laptop and a phone: it's the
      fallback if the laptop or Wi-Fi fails, and the live link needs internet.
- [ ] Before the pitch, run the script's **pre-pitch checklist** (server, five tabs in order, dry-run of the link cut).
- [ ] Optional: French docs `REPETITION_22H.md`, `VIDEO_SECOURS.md` and the reference section of `demo/README.md` still
      quote old numbers (1076.7, ×1.53, 81.6 %). Nobody presents from them; fix or ignore.
- [ ] Unknown: whether the backup video in `VIDEO_SECOURS.md` was ever recorded. If it was, it shows the older plan.

## This folder

| Path | What |
|---|---|
| `deck/` | The deck's sources: `deck.json` (order, sections, fonts), `deck.css` (shared look), `slides/*.html` (one slide each, speaker notes in `<aside>`), `assets.json` (uploaded image id → file in `stills/`). |
| `stills/` | The six screenshots used in the deck, rendered at 3200×1800 from the demo pages. |
| `demo-pages/` | Copies of the five pages the live demo uses, plus `explication.md` (the reason for every contact not served). |
| `demo-inputs/` | The exact scenario, kit plan, our plan and link-loss events behind every page and every number on screen. |
| `timing/` | The spoken text of each part, `full/` and `cut/`, as timed. |
| `drafts/` | Earlier versions: `v0` French demo script, `v1` numbers-led demo script (what `main` has), `v2` first sales pitch with numbers, and `deck_v1_removed_slides/` (the first deck's cover, "two things", versus and product slides). |
| `tools/` | `preview_deck.py` (render the deck offline), `make_stills.py` (re-render the screenshots), `translate_layers.py` (English layer names on `view_ours.html`). Standard library; the two Chrome tools need Google Chrome and macOS `sips`. |

## How to do the common jobs

Run these from `fleet-orchestration/fleet-kit/demo/pitch/`.

**Run the live demo from this folder** (pages are self-contained, no network):

```
python3 -m http.server 8766 --bind 127.0.0.1 --directory demo-pages
```

Then open `http://localhost:8766/view_greedy.html` and the others in the order the script's checklist gives. Double-clicking
the files also works.

**Change a line of the pitch:** edit `../SCRIPT_JURY.md`, the speaker notes in the matching `deck/slides/*.html`, and
the text in `timing/`. Re-time with `say -v Samantha -o x.aiff -f timing/full/b2.txt && afinfo x.aiff` (macOS) and
check against 140 words per minute. Update the "Facts behind the lines" row if the claim changes.

**Change a slide:** best done in the live deck once it's shared with you (open it in claude.ai and edit, or ask Claude
there). To try a change offline: edit `deck/slides/<id>.html` or `deck/deck.css`, then
`python3 tools/preview_deck.py --png` and look at `out/deck_preview.png`. Copy the change into the live deck afterwards.

**Rebuild a demo page:** commands are in the script's "Demo assets" section. Use `demo-inputs/plan.json`, not a fresh
planner run: the planner is time-limited, so a new run can give a different plan, and then the C35 card, the C47 strike
group and the hold times in the script no longer match. After `swann_demo.py`, run
`python3 tools/translate_layers.py <its view.html>` for English layer names.

**Re-render the screenshots:** `python3 tools/make_stills.py` (writes `stills/`). Check them by eye, then upload them
to the deck in place of the old ones.

## Facts that are easy to get wrong

- In the link-loss demo, count **four** seconds after Space: three stops at 639 s, one second before the hold shows.
- L02 holds at **639 s**; H02, L10 and L27 at **640 s** (one step later, on L02's message). The viewer samples every
  2 s and shows them all at 640.
- The link-loss page shows **2626 messages**, not 2826.
- Stale numbers, never quote: ×1.56, ×1.53, 78.9 % or 81.6 % of the bound, 1076.7, "planner v7".
- The screenshots still show the scores (532.9, 1064.6) in small print on the viewer's panel. That's real output; it was
  left on purpose.

## People

- Louis: the operator view (`demo/opsview/`), the planner.
- Swann: the comparison layers and `explication.md` (`demo/swann_demo.py`).
- Mahmoud: owner, merges, presents, holds the deck.

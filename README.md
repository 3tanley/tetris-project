# tetris-project

Tetris project in which I develop an app that can give VOD reviews and live feedback.

## TETR.IO Blitz bot (macOS)

Plays TETR.IO **Blitz** by reading the screen and pressing your keys. It runs the
perfect-clear loop from the three guides you picked:

1. **Opener (bag 1):** one of the openers switched on in the Handling window (see
   [Openers](#openers)): [SingleYou](https://harddrop.com/wiki/SingleYou) (the
   [four.lol SD-PC](https://four.lol/openers/sd-pc) build with the O on the left is the same
   opener mirrored), [Mountainous Stacking 2](https://harddrop.com/wiki/Mountainous_Stacking#Mountainous_Stacking_2),
   Mountainous Stacking (1), Mountainous Stacking 3, and the
   [Jigsaw PC loop](https://harddrop.com/wiki/Jigsaw_PC_Loop). Mirrored versions are included.
2. **Bag 2:** that opener's own setup from the wiki (SDPC TSD, MS setups A–E with the TST,
   or Jigsaw's 3-line solve with T S J I stacked on top).
3. **8-line perfect clear:** after SingleYou it uses four.lol's SD-PC solutions (including
   the T-spin-single ones), after Jigsaw the wiki's 3rd-bag PCs, otherwise the live solver.
   It uses 20 pieces, so one piece of bag 3 is left over.
4. **DPC:** the leftover piece goes into a TSD → PC setup from
   [four.lol/perfect-clears/dpc](https://four.lol/perfect-clears/dpc) (extra O / I / S / J / T,
   with mirrors for Z / L). Then a 4-line PC leaves an empty field and a fresh bag, so it goes back to step 1.

If a setup or PC can't be made with the pieces it gets, it plays safe "free" stacking and
keeps looking for perfect clears, and goes back to the loop when the field is empty.

## Setup (once)

```bash
./setup.sh            # creates .venv and installs numpy, pillow, pyobjc
```

macOS permissions, for the app you launch it from (Terminal, iTerm or VS Code):

* **System Settings → Privacy & Security → Accessibility**: needed to press keys.
* **System Settings → Privacy & Security → Screen & System Audio Recording**: needed to see the board.

Restart that app after granting them.

## Run

```bash
./run_bot.command          # or double-click it in Finder
```

A small translucent panel appears in the top-right corner with the **MODE** row, the
**BOT PLAYS** switch, a stats readout, **Start/Stop**, **Openers…**, **Handling…** and **Quit**.
You can drag it anywhere. Clicking it does not take keyboard focus away from the browser.

1. Open TETR.IO Blitz so the whole board (hold, field, next queue) is visible. Any window
   size or aspect ratio works.
2. Press **⌘⇧K** (or click Start). You can press it before or during the countdown; it
   waits for the first piece.
   * **BOT PLAYS off** (the default, every launch): **advisor**. You play; the bot only
     watches and shows what you're building and where the next piece should go. No keys
     are pressed. See [Advisor](#advisor-bot-plays-off).
   * **BOT PLAYS on**: the bot plays.
3. Press **⌘⇧K** again (or Stop) to stop it. When a game ends it waits for the next one.

Flipping BOT PLAYS while running switches right away: the session restarts in the new mode
and joins the game in progress (free play until the field is empty, then the loop).

### Modes

The **MODE** row has one toggle per game mode, saved in settings.json. **Blitz** is the
only mode so far. **Sprint** and **VOD Review** are there but greyed out ("coming soon"
tooltip) until they are built.

Options (`./run_bot.command --help`):

| option | what it does |
|---|---|
| `--no-overlay` | no panel, hotkey only |
| `--gravity high` | soft drop after every input. Safe at 20G but slower. Default `auto` switches on when it sees pieces falling fast |
| `--no-verify` | skip the per-piece screen check (faster, can't recover from desyncs) |
| `--locate` | find the board once, print what it sees, save `debug/screen.png` |
| `--sim 300` | play a simulated game in the terminal (no TETR.IO needed) |
| `--bot-plays` | start with BOT PLAYS on (useful with `--no-overlay`, where there is no switch) |
| `--train 42` | retrain the advisor's setup prior (7 self-play games per opener, ~45 s) |

## Advisor (BOT PLAYS off)

You play; the bot reads the screen every frame and keeps up with your game.

* **What you're building:** every piece you lock is matched against all setups the bot
  knows (every opener, enabled or not, their 2nd-bag setups, the four.lol SD-PC / Jigsaw /
  2nd-PC solutions, every DPC setup and DPC PC solution). Every setup that contains all
  the pieces you've placed so far stays a candidate; the others drop out. The solve panel
  shows the best candidate. Build the first 3 pieces of Mountainous Stacking 2 and it shows
  "Opener: Mountainous Stacking 2" with your pieces dimmed and the rest still to place.
* **Next placement:** the bot then plans as if it were playing, from your board, hold and
  the next 5 pieces. Its best placement for the current piece is outlined in white on the
  diagram, and the status line says e.g. `next: hold T, place O`. With only 1-2 pieces
  down, many setups still fit; the status says `guess, 14 setups fit` until it's clear.
* **DPC:** after your 8-line PC it works out the extra piece from what you placed, picks
  the DPC setup whose four.lol order rules fit the queue, and shows it with its piece
  dependencies (`priority: J › S › O › T`). After the TSD it picks the four.lol PC solution
  the next 5 pieces can build (or its own solver) and shows that.
* **Settings apply:** the suggestions use your Handling and Openers settings (a fresh
  bag suggests one of the openers you switched on). Recognition doesn't: whatever you
  build is recognised.
* **When you leave the setup:** if a piece doesn't fit any candidate, it says so and
  falls back to free play (keep the stack low, look for perfect clears). When the setup it
  guessed can't be finished with the queue but another candidate still fits, it switches
  to that one.
* **Stats:** `followed 30/36 suggestions` counts how often your piece went exactly where
  it suggested.
* Text over the board (ALL CLEAR, combos) is handled: rows it covers are left out of the
  comparison while it's there, so it keeps up while you play through the banner. If a
  board change can't be explained by one piece for 1.2 s, it re-reads the whole game.

### The model

The setups are exact piece layouts, so recognising them is done by elimination against
the setup library above. That is more accurate than a trained network and needs no data.
Training a neural network or an RL agent to play from scratch would take millions of
games and still play worse than the planner here. What is learned is a **prior**
(`tetrisbot/model.py`, saved in `model/setup_prior.json`): when several setups still fit,
which one is most likely.

* **Self-play:** `--train` runs the bot in the simulator, the same number of games with
  each opener, and records which variant of each family it actually finishes, as a share
  of that family (e.g. SingleYou-A 59%, mirrored 35%, SingleYou-B 3%).
* **You:** every setup the advisor sees you finish adds to its score (`user` in the
  file), so over time the display leans toward the setups you actually use. Delete the
  `user` entries in the file to forget them.

The ranking of candidates is: the one already shown, then openers you switched on, then the
prior, then the published PC chance.

## Handling window

**Handling…** opens a copy of TETR.IO's HANDLING panel. Set it to the same values as in
the game. Changes are saved to `settings.json` and apply right away, even mid-game.

* **Taps** are held for 75% of your DAS, up to MAX TAP (e.g. DAS 10 ms → 7.5 ms). Holding a
  key for the full DAS would start auto-shift.
* **DAS moves** ("hold left until the wall") are held for DAS + DCD (+ ARR × 9 if ARR > 0)
  plus one frame.
* **SDF ∞**: soft drop is held for one frame. **Finite SDF**: soft drop is held while it
  watches the screen, and released when the piece lands.
* **Input optimization**: FINESSE uses the fewest key presses, following
  [four.lol/mid-game/finesse](https://four.lol/mid-game/finesse) (DAS to the wall counts
  as one press, never tap three times). SPEED uses the shortest total time instead.
  FINESSE is the default: about 3.3 keys per piece in simulation, like the Blitz world
  record and other top players (every placement uses its fewest presses; the rest is
  holds). SPEED taps instead of using DAS (with a short DAS) and costs ~4.5 keys per piece.
* **High gravity and soft drops:** a soft-drop press after a move is only added when
  gravity (as measured, with a 2x margin) can't pull the piece down before the next key;
  from ~1000 rows/s a new piece is on the stack before the first key, so no soft drop there.
* **Check ghost before hard drop**: after the moves and before the hard drop, it reads the
  screen. The ghost must sit exactly on the planned cells (if the piece was soft dropped, the
  piece itself must). The screen lags the keys by tens of milliseconds, and the bot measures
  that lag. It only steers a piece after the same wrong position has stayed on screen longer
  than the lag. If the piece is somewhere it passes on its planned path, it waits even longer.
  Then it steers the piece from where it actually is. The overlay shows "ghost fixes": it
  should stay near 0. If it climbs with every piece, something is wrong.
* Text TETR.IO draws over the board ("ALL CLEAR", combo numbers) is not mistaken for blocks.
  A block must be solid and one colour across the whole cell, and blocks floating in mid-air
  are ignored. A board mismatch must show on two pieces in a row before it resyncs.
* **TEST** shows the key sequences the current settings produce.

Controls (from your screenshot): J/L move, K soft drop, Space hard drop, Z/C/X rotate
CCW/CW/180, Left Shift hold. To change keys, edit `DEFAULT_BINDINGS` in `tetrisbot/keys.py`.
It expects the default skin colours. Pieces in the previews are also recognised by shape.

## Openers

The overlay has four buttons: **Start/Stop**, **Openers…**, **Handling…** and **Quit**.
**Openers…** opens a window with a switch per opener (saved in settings.json, used from the
next opener on).

* **Which one:** of the openers switched on, the one with the best chance of a perfect
  clear: the chance to build it with the pieces in view × the published PC chance of what
  follows (Jaws 100%, SD-PC 99.4%, MS2 98.5%, MS 97.5%, MS3 96.4% (averages of their
  2nd-bag setups), Jigsaw 100%).
* **Failsafe:** if none of the openers switched on can be built for sure with this bag (e.g.
  only SD-PC is on and the O comes after S, Z and T), it may use one that is switched off.
  The log says so: `[opener] ... - failsafe: none of the selected openers can be built`.

### Jaws (ILSZ) → 2nd PC → DPC

From the [Hard Drop wiki](https://harddrop.com/wiki/Jaws) and
[four.lol 2nd PC](https://four.lol/perfect-clears/2nd) (`setups_jaws.py`, `setups_fourlol_2pc.py`):

* **1st PC:** I L S Z on the left, then one of the wiki's 22 solutions (plus mirrors) with
  the other 6 pieces. The bot commits to a solution once the visible pieces can finish it,
  preferring the one whose 4 leftover pieces have the best 2nd PC pattern.
* **When Jaws is used:** only at a fresh bag with an empty hold, and only if the bag lets
  I L S Z (or the mirror) go in while every other piece waits in hold, one at a time.
  Otherwise O, T or J would have to go into a solution before the queue shows which
  solution works, and the build fails often (in simulation about 40% of the time). That
  is about 1 bag in 11 (440 of 5040 orders); other bags use another opener.
* **2nd PC:** every four.lol 2nd PC setup whose pieces are on hand is considered (exact
  leftover match and higher PC chance first); then the PC solution that leaves the best
  DPC extra piece. The one piece left over goes into the DPC.

### Jigsaw PC loop (off by default)

From the [Hard Drop wiki](https://harddrop.com/wiki/Jigsaw_PC_Loop) (`tetrisbot/setups_jigsaw.py`):

* **Bag 1:** the PCO build (holds L) or the Jaws build (holds T). When both work it uses PCO
  (the wiki: higher chance of an early PC). Each clears one line.
* **Bag 2:** the 3-line solve (the held piece + Z O L) with T S J I stacked on top; when
  the 3 lines clear, the same field is always left. If Z, O and L come early, the solve
  can finish first: an early perfect clear, then T S J I go on the empty field. The
  alternate build is only for the IO > Z > L order. The wiki's early-PC solves (ZOTI etc.)
  are kept as a last resort, because they end the loop.
* **Bag 3:** one of the six 4-line PCs, chosen by which DPC the leftover piece allows:
  S or Z left (S/Z DPC), or O left (the Tetris-PC solves).

## Speed and high gravity

* **Planning ahead:** while a piece's keys are being checked on screen, the next piece is
  already planned on a copy of the model, as if this piece lands as planned. The moment this
  piece is hard dropped, the next piece's keys go out with no screen wait. The screen read
  that reveals the newest queue piece happens during that next piece's check. A new choice
  (opener, 2nd-bag setup, PC solution, DPC setup) waits for that read. If a piece doesn't land
  as planned, the pre-plan is thrown away.
* **Measured gravity:** it measures how fast pieces fall (rows/s, shown on the overlay). It
  compares the piece's actual position with where its keys should have left it, so
  rotations and kicks are never mistaken for falling. When a
  piece would reach the stack before its inputs finish, it switches to high-gravity moves:
  * normal moves while the piece is still well above the stack (time budget from the measured
    gravity, with a 2× margin)
  * then soft drop after every input, so the result is the same at any gravity, up to 20G
  * a DAS move counts its first one-cell step, the wait, then the slide
* **Failsafes instead of blind hard drops:**
  * **Already locked:** if the piece locked by itself (the next piece is already falling),
    it doesn't hard drop. That would slam the next piece down. It records where the piece
    actually locked.
  * **Off target:** at most one correction. If the planned spot can't be reached in time,
    it places the piece in the best spot reachable from where it really is, and the plan
    adapts.
  * **About to lock:** without TETR.IO's "prevent accidental hard drops", a piece on the
    ground that is about to lock is left to lock by itself.
* **S/Z DPC (and other DPCs) ready in advance:** while it has nothing else to do (menus,
  waiting for a piece), the look-ahead thread works out the moves for every stage of the
  S/Z DPC setups, the PC solutions that follow them, the Jigsaw builds and the other DPC
  setups. When a DPC setup is chosen, the PC solutions that start from what it leaves are
  done next. Choosing the PC after an S/Z DPC then takes a few milliseconds.
* **Place first, plan later:** during a DPC build the PC that follows is only planned once 3
  slots are left (the last two pieces and the T). Earlier, the queue doesn't show enough of
  the next bag yet, and the planning would compete with the pieces being placed.
* **Soft drops (tucks and spins):** the piece is moved sideways in the air first, then
  soft dropped, then rotated in. Before the soft drop the bot looks at the screen: if the
  piece isn't in the planned column + rotation (e.g. a DAS slide that only moved one cell),
  it re-plans from where the piece is, up to 3 times. Once soft dropped it can't go back up.
* **Rotation system:** TETR.IO SRS+ (tetrio.wiki.gg). Clockwise and counter-clockwise kicks
  are mirror images, so a mirrored setup uses the mirrored spin (an S-spin done CW, CW is
  done CCW, CCW with a Z). When two rotations are equally good, S and L use CW first, Z and
  J CCW first.
* **Thinking time limits:** in high gravity the piece is already on the stack while the bot
  thinks. A perfect-clear search on the bot thread gets 0.3 s at most (0.1 s in free play)
  instead of 2.5 s. The look-ahead thread keeps the long limits. While the bot thread
  decides, the look-ahead thread pauses so it doesn't slow the bot thread down.
* **Faster searches:**
  * Perfect clears are searched twice: first with straight hard drops only (plus every T
    placement, for T-spins), which finds most PCs about 4x faster. Tucks and slides are
    added only if that finds nothing.
  * The rotate/shift/DAS part of a straight drop is the same on every low stack. It is
    worked out once per piece; after that, a drop costs one fall per column.
  * When a setup's chance is checked against every order of the unseen pieces, each order
    only asks "can it be finished?". The search stops at the first way that works.
  * The measured gravity is rounded down to a few fixed steps, so planned moves stay
    cached while the reading drifts.

## Building from the bottom up

When several piece orders can finish a setup or a perfect clear, the bot ranks them:
1. fewest **tucks** (non-T-spin pieces that need a soft drop to slide under something)
2. fewest pieces placed **over a slot that is still open** below them
3. **then** fewest holds
4. then lowest-first order in general

So with L before S in the four.lol TSD setup it holds L and places S first. If a piece
depends on another (I resting on O), it holds the I until the O is down. Among builds of the
same opener family that are certain to finish, it picks the one needing the fewest tucks. In
simulation this cut tucks by a third with the same number of perfect clears.

TETR.IO allows one hold per piece (the hold box turns grey). The bot reads that and never
plans a second hold for the same piece.

## Line clears

TETR.IO ignores moves pressed while a line clear is still animating. After a hard drop that
clears lines, the bot waits until the next piece has actually spawned, and the queue has moved
on, before sending its keys. If a different piece than planned is falling anyway (a hold or
the moves were lost), it doesn't hard drop. It re-plans for the piece that is really there,
from where it is. In perfect clears the solver prefers plain hard drops over tucks that depend
on exact timing.

## Bag counter and choosing the extra piece

* The overlay shows a pieces counter for the current 7-bag: pieces that have spawned (solid,
  in order), pieces already in the queue (faint), and pieces not seen yet (empty). It resets
  every bag. During DPC it also shows the extra piece.
* The bot records which piece of each bag was used for each placement. While doing the
  SingleYou / Mountainous Stacking 8-line PC, it looks at several PC solutions that leave
  a different piece unused. It checks which DPC setup each leftover allows with the visible
  next pieces, and picks the PC that leaves the best one. The solve panel shows it, e.g.
  "then extra S -> DPC OS".
* If it falls out of the loop, free-play PCs prefer endings that land on a bag boundary
  (opener next) or leave one piece (DPC next). Mid-bag, it only starts a setup that is
  certain to finish.

## Priority lists (piece dependencies)

Every setup and solution gets a dependency list, shown in the solve and Next windows, e.g.
`priority: I S › J L T O › Z`. Pieces on the left go first:
* **must wait:** four.lol draws some pieces across rows that clear before they go in (like
  the Z in the extra-T DPC solutions). Those wait until every piece in those rows is down.
* **bottom-up:** a slot directly below another goes first.
* **T-spin last:** in a setup the T-spin goes in after every other piece (an early T is held),
  e.g. SDPC 2nd bag `Z S I › J O › L › T`. PC solutions are exempt (pieces may go on top of a T).

When several setups are certain to finish, the bot picks the one whose dependencies fit the
order the pieces arrive in (fewest pieces that must wait in hold), then the fewest soft-drop
tucks. Example (Hard Drop wiki, MS2 2nd bag): setup A puts the I on top of the O, so "not if
the O comes after the I"; with S before O it builds setup C (I on the floor, O on the S).
The wiki's "compromise" setups are used only when nothing else works.

The chance that a setup or solution can be finished is checked against every order of the
pieces not seen yet. If every piece it needs is already visible and no order works, it
scores 0 and is never started. For a DPC perfect clear the bot then uses its own solver
right away, before anything is misplaced. Solves planned ahead are re-checked against the
pieces visible when they start.

SDPC's 2nd bag always uses the four.lol layout when possible: the O next to the I, not the
"alternate O" on top of the L, which has to wait for the L.

## Planning ahead (Next window)

While a T-spin setup is being built (2nd bag of SingleYou / Mountainous Stacking, or a DPC
setup), the bot already knows how the setup will end. It searches the perfect clear that
follows on a background thread, using the pieces it can see. A third translucent window,
**Next**, shows that solve and its piece order (e.g. `order: S Z hold>J O …`). When the setup
is done, the solve is used immediately with no search.

**Never pressing space at the wrong time:**
* A piece that is already resting on the stack (soft-dropped or spun in, with the lock
  delay running) is hard dropped first. Any planning happens after.
* Right before space, if more than 60 ms have passed since the last look, it takes a fresh
  look. If the piece has meanwhile locked by itself, it doesn't press space (that would hard
  drop the next piece where it spawned).
* Before every hard drop the ghost must sit exactly on the planned cells (or the piece
  itself must, after a soft drop).

**Queue pieces are identified by colour and shape.** Colour first, learned for your skin
while playing, and confirmed by shape. A clearly identified colour wins when the shape
reading is broken.

## Solve panel

A second translucent panel sits under the main one. It shows the setup or solution the bot
is building, drawn in four.lol's colours:
SingleYou → SDPC TSD setup → the 8-line PC solution → the DPC setup (leftover piece in grey)
→ the four.lol PC solution. Pieces already placed are dimmed. The picture changes whenever the
next pieces change the choice.

## DPC: how it picks a setup and a solution

After the 8-line PC it works out the extra piece by bookkeeping. Every placement is recorded
by its position in the piece stream, so for each 7-bag it knows which pieces were used. The
one piece of the third bag that was never placed (in hold or still in the queue) is the extra,
e.g. `bag 3: placed LTSJIO, Z never placed (in hold)`. Only setups for that piece are
considered. For every four.lol setup for that piece, it checks the order criteria from
the setup's title against the hold and the next pieces. For example, JO needs J before O,
and OJ+ZS needs O before J and Z before S. It logs the result, e.g.
`extra S | next SZILSJTO | OS: O<S ✗ | SO: S<O ✓`, and builds the first setup in four.lol's
order that meets its criteria and can be built. For the PC after the TSD it checks four.lol's
own solutions for that setup against the next pieces and builds one that works. Its own PC
solver is only a backup.

Both orientations of every setup and solution are included. four.lol's "mirror" view shows
the same setups flipped (e.g. JO appears as LO), and the bot logs whichever orientation it builds.

## How it works

| file | role |
|---|---|
| `tetrisbot/core.py` | rules: pieces, TETR.IO SRS+ kicks (incl. 180), T-spin detection, cost-based (finesse/speed) move search producing exact key sequences |
| `tetrisbot/handling.py`, `settings_ui.py` | handling settings → key timings, and the HANDLING window |
| `tetrisbot/setups_wiki.py` | SingleYou / MS / MS2 / MS3 diagrams, extracted by script from the Hard Drop wiki source |
| `tetrisbot/setups_jigsaw.py` | Jigsaw PC loop: bag 1/2 builds, 3rd-bag PCs, early-PC solves (Hard Drop wiki) |
| `tetrisbot/setups_fourlol_sdpc.py` | four.lol SD-PC data: its 8-line PC solutions |
| `tetrisbot/setups_dpc.py` + `fumen.py` | DPC setups as the fumen codes from four.lol, decoded at load |
| `tetrisbot/templates.py` | turns diagrams into piece "slots", adds mirrors, finds each DPC TSD slot |
| `tetrisbot/planner.py` | template filling with hold, perfect-clear solver, fallback heuristic |
| `tetrisbot/brain.py` | stage machine (opener → bag 2 → PC → DPC → PC → …) and 7-bag tracking |
| `tetrisbot/vision.py` | finds the board by its white frame at any scale; reads the field, next queue and hold |
| `tetrisbot/controller.py` | live loop: read screen → decide → press keys → verify → resync if needed |
| `tetrisbot/app.py`, `hotkey.py`, `keys.py` | overlay panel, global ⌘⇧K, synthetic key presses |
| `tetrisbot/coach.py` | advisor: Watcher (screen frames → "piece spawned" / "piece locked" events) and Coach (recognises the setup, keeps a Brain in step with the user's game) |
| `tetrisbot/model.py`, `model/setup_prior.json` | the advisor's learned setup prior and its self-play training |
| `tetrisbot/sim.py`, `tests/` | headless simulator and tests (including a fake TETR.IO screen) |

Tests: `.venv/bin/python -m pytest tests -q`

In simulation (30 games × 150 pieces) it averages about 7.9 perfect clears per 150 pieces.
The loop's maximum is about 8.6. In a fake-screen test with 15% of taps randomly dropped,
the ghost check caught and fixed them before hard drop.

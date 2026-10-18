"""Advisor mode ("Bot plays" off): the user plays, the bot watches and shows what they are
building and where the next piece should go. No keys are pressed.

  Watcher  reads the screen every frame and turns it into events: a piece spawned
           (current, hold, next 5) or a piece locked (where, with or without hold).
  Coach    keeps a Brain in step with the user's game. Every locked piece is matched
           against the setup templates (openers, 2nd-bag setups, DPC setups, four.lol PC
           solutions): every template that contains all the pieces placed so far stays
           a candidate, the rest drop out. Ties are broken by the learned prior
           (model.SetupPrior). The Brain then plans as if it were playing, so the
           overlay shows the recognised setup, its piece dependencies, the DPC choice
           and the PC that follows, plus the best next placement (outlined).
"""
import queue as _queue
import threading
import time
from collections import Counter

from . import core, planner, vision
from . import templates as T
from .brain import Brain, _rebase, all_pc, opener_priority, sibling_pool
from .model import SetupPrior

SETUP_STAGES = ("OPENER", "BAG2", "DPC", "PC2")


def _same(a, b, unk):
    """Boards equal on every cell that could be read (`unk` = per-row masks of unreadable cells)."""
    return all(((a.rows[y] ^ b.rows[y]) & ~unk[y]) == 0 for y in range(core.H))


def fit_placement(before, after, pieces, unk=None):
    """Which piece, where, turns `before` into `after` (line clears included)?
    `unk`: per-row bit masks of cells that couldn't be read (text over the board).
    Returns (piece, rot, x, y, cleared_rows, board) - `board` is the result as simulated,
    with the unreadable cells filled in - or None. Only resting placements count."""
    unk = unk or [0] * core.H
    added = [(x, y) for y in range(core.H) for x in range(core.W) if after.filled(x, y) and not before.filled(x, y)]
    if len(added) == 4 and not any(unk) and all(before.rows[y] | after.rows[y] == after.rows[y] for y in range(core.H)):
        # a piece in the air isn't locked (2026-10-18: an L moved at the top, then held,
        # was taken as locked at rows 16-17)
        if not any(cy == 0 or before.filled(cx, cy - 1) for cx, cy in added):
            return None
        for p in pieces:                                   # no line clear: the new cells are the piece
            for x, y, r in core.identify(p, added):
                b = before.copy()
                if not b.place_cells(core.cells_of(p, r, x, y)) and b == after:
                    return p, r, x, y, [], b
    for p in pieces:                                       # line clear / hidden cells: try every resting spot
        for r, x, y, cells in _resting(before, p):
            b = before.copy()
            cleared = b.place_cells(cells)
            if _same(b, after, unk):
                return p, r, x, y, cleared, b
    return None


def _resting(board, p):
    """Every spot where piece `p` rests on `board`: (rot, x, y, cells)."""
    for r in range(4):
        for x in range(-2, core.W + 2):
            for y in range(-2, 20):
                cells = core.cells_of(p, r, x, y)
                if any(not (0 <= cx < core.W and 0 <= cy < 20) or board.filled(cx, cy) for cx, cy in cells):
                    continue
                if any(cy == 0 or board.filled(cx, cy - 1) for cx, cy in cells):
                    yield r, x, y, cells


def _slot_at(ts, piece, cells):
    """The open slot of `ts` that is exactly this piece in these cells, or None."""
    cells = tuple(sorted(cells))
    for sid in ts.remaining:
        if ts.tmpl.slots[sid].ptype == piece and ts.slot_cells(sid) == cells:
            return sid
    return None


def _plan_still_works(board, plan):
    b = board.copy()
    for st in plan:
        if any(b.filled(x, y) for x, y in st.pl.cells):
            return False
        b.place_cells(st.pl.cells)
    return b.rows[0] == 0


class Events:
    """The Watcher's events (begin / spawned / locked). They can be called from the screen
    thread; with threaded=True the handlers run on a worker thread so slow planning never
    makes the watcher miss a piece."""

    def __init__(self, log=print, threaded=False):
        self.log = log
        self.threaded = threaded
        self._q = _queue.Queue()
        self._closed = False
        if threaded:
            threading.Thread(target=self._loop, daemon=True).start()

    # ------------------------------------------------------------ events
    def begin(self, board, cur, hold, queue, fresh):
        """A game is visible: `fresh` = it just started (empty field, empty hold)."""
        self._post("_begin", board, cur, hold, list(queue), fresh)

    def spawned(self, board, cur, hold, queue):
        self._post("_spawned", board, cur, hold, list(queue))

    def locked(self, before, piece, rot, x, y, used_hold, after, cleared):
        self._post("_locked", before, piece, rot, x, y, used_hold, after, cleared)

    def close(self):
        self._closed = True
        self._q.put(None)

    def idle(self):
        """True when every event has been handled (tests)."""
        return self._q.unfinished_tasks == 0

    def _post(self, name, *args):
        if self.threaded:
            self._q.put((name, args))
        else:
            getattr(self, name)(*args)

    def _loop(self):
        while not self._closed:
            item = self._q.get()
            try:
                if item is not None:
                    getattr(self, item[0])(*item[1])
            except Exception as e:      # keep watching; report
                import traceback
                traceback.print_exc()
                self.log(f"[coach] error: {e}")
            finally:
                self._q.task_done()


class Coach(Events):
    """Follows the user's Blitz game (setups, PCs, DPC)."""

    def __init__(self, log=print, lookahead=None, prior=None, threaded=False):
        self.lookahead = lookahead
        self.prior = prior if prior is not None else SetupPrior.load()
        self.brain = Brain(log=log, lookahead=lookahead)
        self.brain.advisor = True
        self.spawn = None          # (current, hold, queue) when the piece in play spawned
        self.rec = None            # the suggested Step for the piece in play
        self.suggested = 0         # pieces with a suggestion
        self.followed = 0          # ...that the user placed exactly there
        self.pieces = 0
        self.fits = 0              # setups that still fit what the user has built
        super().__init__(log, threaded)

    # ------------------------------------------------------------ handlers
    def _begin(self, board, cur, hold, queue, fresh):
        if self.lookahead is not None:
            self.lookahead.reset()
        self.brain = Brain(log=self.log, lookahead=self.lookahead)
        self.brain.advisor = True
        self.brain.bag.reset(aligned=fresh)
        if not fresh:
            self.brain.stage = "FREE"
            self.log("[coach] joined mid-game: following free play until the field is empty")
        self.pieces = 0
        self._spawned(board, cur, hold, queue)

    def _spawned(self, board, cur, hold, queue):
        br = self.brain
        self.spawn = (cur, hold, list(queue))
        br.bag.update(br.cur_index, cur, queue)
        br.empty_field_stage(board)
        if self.threaded and self._q.qsize() > 0:
            self.rec = None       # the user is already further: don't plan for a past piece
            return
        stage, ts = br.stage, br.ts
        alts = [h for h in self._still_fit(board) if h.tmpl is not ts.tmpl] if ts is not None else []
        self.rec = br.decide(board, cur, hold, queue)
        if alts and br.ts is None and br.stage == "FREE" and stage in SETUP_STAGES:
            # the setup we guessed can't be finished with these pieces, but the user's
            # pieces also fit other setups: follow the best one that can still be finished
            best = None
            for h in alts:
                p, steps = br._chance(h, board, hold)
                if steps and p > 0 and (best is None or (p, self._rank(h)) > best[0]):
                    best = ((p, self._rank(h)), h)
            if best is not None:
                h = best[1]
                self.log(f"[coach] {ts.tmpl.name} can't be finished - following "
                         f"{h.tmpl.label or h.tmpl.name} ({best[0][0]:.0%})")
                br.ts, br.family, br.plan = h, h.tmpl.family, []
                br._set_stage(stage)
                self.rec = br.decide(board, cur, hold, queue)

    def _locked(self, before, piece, rot, x, y, used_hold, after, cleared):
        br = self.brain
        if self.spawn is None:
            return
        cur, hold0, _ = self.spawn
        spin = core.tspin_kind(before, rot, x, y, True, 0) if piece == "T" and cleared else None
        pl = core.Placement(piece, rot, x, y, [], spin)
        rec = self.rec
        self.pieces += 1
        if rec is not None:
            self.suggested += 1
            if rec.pl.piece == piece and rec.pl.cells == pl.cells:
                self.followed += 1
        if rec is not None and rec.pl.cells == pl.cells and rec.pl.piece == piece and rec.hold == used_hold:
            step = rec
        else:
            slot = rec.slot if (rec is not None and rec.pl.cells == pl.cells and rec.pl.piece == piece) \
                else self._recognize(before, piece, pl.cells)
            step = planner.Step(used_hold, pl, slot)
            if slot is None and br.plan:
                self._follow_plan(before, piece, pl.cells)
        built = Counter(br.built)
        br.on_lock(step, hold0 is None, cleared, after)
        if br.plan and not _plan_still_works(after, br.plan):
            br.plan = []
        for name in br.built - built:          # the user finished a setup: learn it
            self.prior.learn(name)
        self.fits = len(self._still_fit(after)) if br.ts is not None else 0
        self.rec = None

    # ------------------------------------------------------------ recognition
    def _openers(self):
        """Opener families the advisor may recognise: the ones switched on in the Openers
        window, plus the one it is showing (the bot's failsafe can suggest a switched-off
        opener when none of the others fits the bag). Nothing switched on: all of them."""
        fams = set(opener_priority())
        ts = self.brain.ts
        if ts is not None and ts.tmpl.stage in ("bag1", "pc1_pc"):
            fams.add(ts.tmpl.family)
        return fams or set(T.FAMILY_PRIORITY)

    def _stage_pool(self):
        """Templates the user may be starting in the current stage."""
        br = self.brain
        st = br.stage
        if st == "OPENER":
            return T.openers(self._openers()) + ([] if all_pc() else T.dpc())
        if st == "BAG2":
            if br.family:
                return T.second_bag(br.family)
            return [t for t in T.library()["wiki"] if t.stage in ("bag2", "bag2_pc")]
        if st == "PC8":
            return T.pc8_solutions(br.family) or []
        if st == "DPC":
            return T.dpc()
        if st == "PCDPC":
            return T.dpc_solutions()
        if st == "PC2":
            return T.pc2_setups()
        return []

    def _still_fit(self, board):
        """Every template of the current kind that contains all pieces placed so far."""
        ts = self.brain.ts
        if ts.tmpl.stage in ("bag1", "pc1_pc"):
            # an opener can turn into another family's opener as long as everything fits -
            # but only the openers switched on
            pool = T.openers(self._openers())
        else:
            pool = [t for t in sibling_pool(ts.tmpl) if t.stage == ts.tmpl.stage]
        return [h for h in (ts if t is ts.tmpl else _rebase(t, ts, board) for t in pool) if h is not None]

    def _rank(self, ts):
        """Higher = more likely what the user is building: the setup already shown, then
        the openers switched on in the user's priority order, then the learned prior."""
        t = self.brain.ts.tmpl if self.brain.ts is not None else None
        order = opener_priority()
        prio = 0
        if ts.tmpl.stage in ("bag1", "pc1_pc"):
            prio = len(order) - order.index(ts.tmpl.family) if ts.tmpl.family in order else -1
        return (ts.tmpl is t, prio, self.prior.score(ts.tmpl.name), not ts.tmpl.fallback,
                ts.tmpl.pc_rate or 0.0)

    def _recognize(self, before, piece, cells):
        """The user put `piece` on `cells`, which is not the suggestion. Find the setup it
        belongs to (switching the brain to it) and return the slot, or None."""
        br = self.brain
        ts = br.ts
        if ts is not None and ts.matches(before):
            sid = _slot_at(ts, piece, cells)
            if sid is not None:
                return sid
            cands = [h for h in self._still_fit(before) if h.tmpl is not ts.tmpl]
        else:
            cands = [h for h in (T.TState.fresh_on(t, before) for t in self._stage_pool()) if h]
        hits = [(h, sid) for h in cands for sid in [_slot_at(h, piece, cells)] if sid is not None]
        if not hits:
            if ts is not None and ts.tmpl.stage in ("bag1", "pc1_pc"):
                self.log(f"[coach] {piece} at {sorted(cells)} doesn't fit any opener switched on "
                         f"({', '.join(sorted(self._openers()))})")
                br.ts = None
                br._set_stage("FREE", "(not one of the selected openers)")
                br.free_note = "doesn't match any opener switched on (" + \
                    ", ".join(T.FAMILY_NAMES[f] for f in sorted(self._openers())) + ")"
            elif ts is not None:
                self.log(f"[coach] {piece} at {sorted(cells)} is not part of {ts.tmpl.name} "
                         "or any setup like it")
                br.ts = None
                if br.stage in SETUP_STAGES:
                    br._set_stage("FREE", "(left the setup)")
            elif br.stage in SETUP_STAGES and before.rows[0] == 0 and not br.plan:
                br._set_stage("FREE", "(no known setup starts like this)")
            return None
        h, sid = max(hits, key=lambda hs: self._rank(hs[0]))
        if ts is None or h.tmpl is not ts.tmpl:
            others = len({x.tmpl.name for x, _ in hits}) - 1
            self.log(f"[coach] you are building {h.tmpl.label or h.tmpl.name} ({h.tmpl.family})"
                     + (f" - {others} other setup(s) still fit" if others else ""))
        br.ts, br.plan = h, []
        br.family = h.tmpl.family
        if h.tmpl.family == "DPC" and h.tmpl.stage == "dpc":
            br._set_stage("DPC")
        elif h.tmpl.stage == "bag1" and br.stage not in ("OPENER",):
            br._set_stage("OPENER")
        return sid

    def _follow_plan(self, before, piece, cells):
        """Perfect clears from the solver: the user may place the pieces of the planned
        solution in another order. Drop the placed one from the plan (if nothing before
        it in the plan clears a line, its cells are still right); else forget the plan."""
        br = self.brain
        cells = tuple(sorted(cells))
        k = next((i for i, st in enumerate(br.plan) if st.pl.piece == piece and tuple(sorted(st.pl.cells)) == cells),
                 None)
        if k is not None:
            b = before.copy()
            if not any(b.place_cells(st.pl.cells) for st in br.plan[:k]):
                br.plan.pop(k)
                return
        br.plan = []

    # ------------------------------------------------------------ overlay
    def advice(self):
        """One line for the overlay: the suggested move for the piece in play."""
        rec = self.rec
        if rec is None:
            return "watching…" if self.spawn else "waiting for a game"
        cur, hold, q = self.spawn
        what = rec.pl.piece
        if rec.hold:
            what = f"hold {cur}, place {what}"
        else:
            what = f"place {what}"
        guess = f" · {self.fits} setups fit" if self.fits > 1 else ""
        return f"next: {what}{guess}"         # the placement is outlined on the diagram


class Watcher:
    """Turns screen frames into Coach events. Call poll() for every frame."""

    STABLE_FRAMES = 2          # a changed board must look the same this many reads in a row
    RESYNC_S = 1.2             # board stays unexplained this long -> re-read everything

    def __init__(self, coach, log=print):
        self.coach = coach
        self.log = log
        self.model = None      # board of locked pieces, None until a game is seen
        self.pending, self.pending_n, self.diff_since = None, 0, None
        self.need_spawn = False

    def poll(self, img, geo, now=None):
        now = time.time() if now is None else now
        board, _, unknown = vision.read_board_ex(img, geo)
        if self.model is None:
            if not unknown:
                self._start(img, geo, board)
            return
        # text / effects over the board ("ALL CLEAR", combos) make some cells unreadable and
        # can make a few others look solid. The user keeps playing meanwhile, so rows with
        # any unreadable cell are left out of the comparison until the text is gone.
        unk = [0] * core.H
        for _, y in unknown:
            unk[y] = core.FULL
        p, cells = vision.read_active(img, geo, self.model)
        scr = board.copy()
        for x, y in cells or ():
            if y < 20:
                scr.rows[y] &= ~(1 << x)
        if _same(scr, self.model, unk):
            self.pending, self.pending_n, self.diff_since = None, 0, None
            if self.need_spawn and p is not None:
                q = vision.read_queue(img, geo)
                if len(q) == 5:
                    self._spawn(vision.read_hold(img, geo), q)
            return
        if self.diff_since is None:
            self.diff_since = now
        if (scr, unk) != self.pending:
            self.pending, self.pending_n = (scr, unk), 1
            return
        self.pending_n += 1
        if self.pending_n < self.STABLE_FRAMES:
            return
        if self.need_spawn:
            # the next piece spawned and locked between two reads: it was in play
            self._spawn(self.hold, vision.read_queue(img, geo), moved_on=True)
        hold_now = vision.read_hold(img, geo)
        if self._lock(scr, unk, hold_now):
            return
        # the falling piece may not be the topmost tetromino: a piece that locked between
        # two reads with the next one tucked under it (2026-10-18 recording: J locked, Z
        # spun in below it before the next read - the J was taken for the falling piece)
        for _, other in vision.active_groups(img, geo, self.model)[1:]:
            alt = board.copy()
            for x, y in other:
                if y < 20:
                    alt.rows[y] &= ~(1 << x)
            if self._lock(alt, unk, hold_now):
                return
        if self._lock2(scr, unk, hold_now):
            return
        if now - self.diff_since > self.RESYNC_S:
            self.log("[coach] can't explain the board change with one piece - re-reading the game")
            self.model = None
            self._start(img, geo, board)

    # ------------------------------------------------------------ internals
    def _start(self, img, geo, board):
        """Wait for a piece at the top with a full queue, then start following."""
        p, cells = vision.read_active(img, geo, None)
        q = vision.read_queue(img, geo)
        if p is None or len(q) != 5 or min(y for _, y in cells) < 10:
            return
        for x, y in cells:
            if y < 20:
                board.rows[y] &= ~(1 << x)
        hold = vision.read_hold(img, geo)
        fresh = board.rows[0] == 0 and hold is None
        self.model = board
        self.cur, self.hold, self.queue = p, hold, list(q)
        self.need_spawn = False
        self.pending, self.pending_n, self.diff_since = None, 0, None
        self.log(f"[coach] following the game: current {p}, next {''.join(q)}, hold {hold or '-'}")
        self.coach.begin(board, p, hold, q, fresh)

    def _lock(self, scr, unk, hold_now):
        """The board changed: find the piece that locked. False if it can't be explained."""
        used_hold = hold_now is not None and hold_now != self.hold
        swap = self.hold if self.hold is not None else self.queue[0]
        expect = swap if used_hold else self.cur
        order = [expect] + [p for p in (self.cur, swap) if p != expect]
        fit = fit_placement(self.model, scr, order, unk)
        if fit is None:
            return False
        piece, r, x, y, cleared, after = fit
        used_hold = piece != self.cur
        self.coach.locked(self.model, piece, r, x, y, used_hold, after, cleared)
        self.model = after
        # what spawns next, and what the queue / hold were before the next read
        shift = 2 if (used_hold and self.hold is None) else 1
        self.next_cur = self.queue[shift - 1] if shift - 1 < len(self.queue) else None
        self.known = self.queue[shift:]
        self.hold = self.cur if used_hold else self.hold
        self.need_spawn = True
        self.pending, self.pending_n, self.diff_since = None, 0, None
        return True

    def _lock2(self, scr, unk, hold_now):
        """Two pieces locked between two steady reads (slow reads while the falling piece
        kept the screen changing - 2026-10-18 recording at 3 reads/s: J locked, Z spun in
        under it). Every way to use hold is tried; it has to end with the hold on screen."""
        q = self.queue
        grew = all(self.model.rows[y] | scr.rows[y] == scr.rows[y] for y in range(core.H)) and not any(unk)
        for h1 in (False, True):
            p1, hold1, rest = self.cur, self.hold, q
            if h1:
                p1 = self.hold if self.hold is not None else (q[0] if q else None)
                hold1, rest = self.cur, (q[1:] if self.hold is None else q)
            if p1 is None or not rest:
                continue
            c2, rest2 = rest[0], rest[1:]
            for h2 in (False, True):
                p2, hold2 = c2, hold1
                if h2:
                    p2, hold2 = (hold1 if hold1 is not None else (rest2[0] if rest2 else None)), c2
                if p2 is None or hold2 != hold_now:
                    continue
                for r, x, y, cells in _resting(self.model, p1):
                    if grew and not all(scr.filled(cx, cy) for cx, cy in cells):
                        continue                    # no line clear: both pieces are on screen
                    mid = self.model.copy()
                    cleared1 = mid.place_cells(cells)
                    fit = fit_placement(mid, scr, [p2], unk)
                    if fit is None:
                        continue
                    _, r2, x2, y2, cleared2, after = fit
                    self.log(f"[coach] two pieces locked between reads: {p1}, then {p2}")
                    self.coach.locked(self.model, p1, r, x, y, h1, mid, cleared1)
                    self.coach.spawned(mid, c2, hold1, rest)
                    self.coach.locked(mid, p2, r2, x2, y2, h2, after, cleared2)
                    self.model = after
                    shift = 2 if (h2 and hold1 is None) else 1
                    self.next_cur = rest2[shift - 1] if shift - 1 < len(rest2) else None
                    self.known = rest2[shift:]
                    self.hold = hold2
                    self.need_spawn = True
                    self.pending, self.pending_n, self.diff_since = None, 0, None
                    return True
        return False

    def _spawn(self, hold_scr, q, moved_on=False):
        """The next piece is in play. Its spawn state: current = the queue piece that was
        due, hold = what the last lock left, next 5 = the screen queue (one step back if
        the user already pressed hold on an empty hold before this read, or `moved_on`:
        the piece may already be down and the next one in play)."""
        known = self.known
        if q[:len(known)] == known:
            queue = q
        elif (moved_on or self.hold is None and hold_scr is not None) and q[:len(known) - 1] == known[1:]:
            queue = known[:1] + q[:4]          # the queue moved on once more
        else:
            self.log(f"[coach] queue {''.join(q)} doesn't follow {''.join(known)} - trusting the screen")
            queue = q
        self.cur, self.queue = self.next_cur, list(queue)
        self.need_spawn = False
        self.coach.spawned(self.model, self.cur, self.hold, self.queue)

"""The live bot: reads TETR.IO from the screen and plays with synthetic key presses."""
import sys
import threading
import time

import numpy as np
import Quartz

from . import core, planner, vision
from .brain import Brain, Lookahead
from .handling import Handling
from .keys import Keyboard

DEFAULTS = {
    "settle_ms": 18,          # wait after hard drop before reading the screen
    "spawn_timeout_ms": 600,  # give up waiting for the next piece after this
    "verify_board": True,     # compare the screen with the simulated board every piece
}


class Screen:
    """Quartz screen capture in pixel coordinates of the full-desktop image."""

    def __init__(self):
        err, ids, n = Quartz.CGGetActiveDisplayList(16, None, None)
        rects = [Quartz.CGDisplayBounds(d) for d in ids[:n]]
        self.ox = min(r.origin.x for r in rects)
        self.oy = min(r.origin.y for r in rects)
        self.scale = 1.0

    @staticmethod
    def _to_array(img):
        if img is None:
            return None
        w, h = Quartz.CGImageGetWidth(img), Quartz.CGImageGetHeight(img)
        bpr = Quartz.CGImageGetBytesPerRow(img)
        data = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(img))
        a = np.frombuffer(data, np.uint8).reshape(h, bpr // 4, 4)[:, :w, :3]
        return a[:, :, ::-1]  # BGRA -> RGB

    def full(self):
        img = Quartz.CGWindowListCreateImage(Quartz.CGRectInfinite, Quartz.kCGWindowListOptionOnScreenOnly,
                                             Quartz.kCGNullWindowID, Quartz.kCGWindowImageDefault)
        a = self._to_array(img)
        err, ids, n = Quartz.CGGetActiveDisplayList(16, None, None)
        width_pts = max(Quartz.CGDisplayBounds(d).origin.x + Quartz.CGDisplayBounds(d).size.width for d in ids[:n]) - self.ox
        self.scale = a.shape[1] / width_pts
        return a

    def grab(self, box):
        """box = (x0, y0, x1, y1) in full-image pixels. Returns (array, x0, y0)."""
        x0, y0, x1, y1 = box
        s = self.scale
        rect = Quartz.CGRectMake(self.ox + x0 / s, self.oy + y0 / s, (x1 - x0) / s, (y1 - y0) / s)
        img = Quartz.CGWindowListCreateImage(rect, Quartz.kCGWindowListOptionOnScreenOnly,
                                             Quartz.kCGNullWindowID, Quartz.kCGWindowImageDefault)
        return self._to_array(img)


def screen_access_ok(prompt=False):
    if Quartz.CGPreflightScreenCaptureAccess():
        return True
    if prompt:
        Quartz.CGRequestScreenCaptureAccess()
    return False


class Bot:
    """Runs in a background thread. status() is safe to call from the UI thread."""

    def __init__(self, config=None, log=print, handling=None):
        self.cfg = dict(DEFAULTS)
        self.cfg.update(config or {})
        self._log = log
        self.stop_event = threading.Event()
        self.thread = None
        self.state = "idle"
        self.last_msg = ""
        self.lookahead = Lookahead(threaded=True)
        self.brain = Brain(log=self.log, lookahead=self.lookahead)
        self.h = handling or Handling.load()
        self.kb = Keyboard(self.h)
        self.screen = Screen()
        self.geo = None       # Geometry in full-image pixels
        self.pieces = 0
        self.t_start = None
        self.corrections = 0
        self.lag = 0.08          # measured seconds between a key press and seeing it on screen
        self.pending_diff = None # board difference seen on the previous piece
        self.grav_rps = 0.0      # measured gravity, rows per second
        self.lock_est = None     # measured lock delay (s), from pieces that locked by themselves
        self.t_last_key = time.time()
        self.t_spawn = time.time()
        self.resynced = False
        self.start_state = None   # set when the piece was moved before its own keys
        self.wrong = None
        self.wrong_count = 0
        self.confirm_time = time.time()
        self.confirm_resting = False
        self.autoplay = False     # "Bot plays" switch: off = advisor (watch the user, no keys)
        self.coach = None
        self.prior = None         # advisor's setup prior (None = model/setup_prior.json)
        self.set_handling(self.h)

    # ------------------------------------------------------------- control
    def set_handling(self, h):
        """Apply new handling settings (safe to call while running). A new game mode
        restarts a running session in that mode."""
        mode_changed = h.mode != getattr(self, "h", h).mode
        self.h = h
        self.kb.h = h
        for obj in (self.coach, self.brain):     # sprint: pieces shown on the panel
            if hasattr(obj, "preview"):
                obj.preview = int(h.sprint_preview)
        planner.configure(h, safe=(h.gravity == "HIGH") or (planner.SETTINGS["safe"] and h.gravity == "AUTO"))
        if mode_changed:
            self.log(f"[mode] {h.mode.lower()}")
            self._restart()

    def sprint(self):
        """Sprint mode: 6-3 stacking (advice, or the bot plays it with BOT PLAYS on)."""
        return self.h.mode == "SPRINT"

    def log(self, msg):
        self.last_msg = msg
        self._log(msg)

    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self):
        if self.running():
            return
        # Python runs one thread at a time and by default hands over every 5 ms: with the
        # look-ahead searching in the background, the bot thread would wait up to 5 ms after
        # every screen grab / key press. 1 ms keeps it responsive.
        sys.setswitchinterval(0.001)
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._main, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def toggle(self):
        self.stop() if self.running() else self.start()

    def set_autoplay(self, on):
        """Switch between playing and advising. Takes effect right away: a running session
        restarts in the new mode (the bot then joins the game in progress)."""
        if on == self.autoplay:
            return
        self.autoplay = on
        self.log(f"[mode] {'bot plays' if on else 'advisor: you play, the bot suggests'}")
        self._restart()

    def _restart(self):
        if self.running():
            old = self.thread

            def restart():             # off the UI thread: a search in progress may take a moment
                self.stop()
                old.join(10)
                self.start()
            threading.Thread(target=restart, daemon=True).start()

    def status(self):
        from .sprint import SprintBrain, SprintCoach
        if self.sprint():
            if self.autoplay and isinstance(self.brain, SprintBrain):
                return self._sprint_bot_status()
            if isinstance(self.coach, SprintCoach):
                return self._sprint_status()
        elif not self.autoplay and self.coach is not None and not isinstance(self.coach, SprintCoach):
            return self._coach_status()
        pps = 0.0
        if self.t_start and self.pieces:
            pps = self.pieces / max(1e-6, time.time() - self.t_start)
        st = self.brain.stats
        return {
            "state": self.state, "stage": self.brain.stage, "pieces": self.pieces,
            "pps": pps, "pcs": st.get("pc", 0), "tspins": sum(v for k, v in st.items() if k.startswith("tspin")),
            "msg": self.last_msg, "safe": planner.SETTINGS["safe"], "fixes": self.corrections,
            "lag_ms": self.lag * 1000, "display": self.brain.display, "grav": self.grav_rps,
            "bag": getattr(self.brain, "bag_view", None),
            "next": self.lookahead.display,
        }

    def _coach_status(self):
        c = self.coach
        br = c.brain
        st = br.stats
        pps = c.pieces / max(1e-6, time.time() - self.t_start) if self.t_start and c.pieces else 0.0
        return {
            "state": self.state, "stage": br.stage, "pieces": c.pieces, "pps": pps,
            "pcs": st.get("pc", 0), "tspins": sum(v for k, v in st.items() if k.startswith("tspin")),
            "msg": self.last_msg, "safe": False, "fixes": 0, "lag_ms": 0.0, "grav": 0.0,
            "display": br.display, "bag": getattr(br, "bag_view", None), "next": self.lookahead.display,
            "advice": c.advice(), "followed": c.followed, "suggested": c.suggested,
        }

    def _sprint_status(self):
        c = self.coach
        pps = c.pieces / max(1e-6, time.time() - self.t_start) if self.t_start and c.pieces else 0.0
        return {
            "state": self.state, "stage": "6-3", "pieces": c.pieces, "pps": pps, "pcs": 0, "tspins": 0,
            "msg": self.last_msg, "safe": False, "fixes": 0, "lag_ms": 0.0, "grav": 0.0,
            "display": c.display, "bag": None, "next": None, "sprint": True,
            "lines": c.lines, "tetrises": c.tetrises,
            "advice": c.advice(), "followed": c.followed, "suggested": c.suggested,
        }

    def _sprint_bot_status(self):
        br = self.brain
        pps = self.pieces / max(1e-6, time.time() - self.t_start) if self.t_start and self.pieces else 0.0
        return {
            "state": self.state, "stage": "6-3", "pieces": self.pieces, "pps": pps, "pcs": 0, "tspins": 0,
            "msg": self.last_msg, "safe": planner.SETTINGS["safe"], "fixes": self.corrections,
            "lag_ms": self.lag * 1000, "grav": self.grav_rps,
            "display": br.display, "bag": None, "next": None, "sprint": True,
            "lines": br.lines, "tetrises": br.tetrises,
            "advice": "bot plays 6-3" + ("  ·  done" if br.done() else ""),
        }

    # ------------------------------------------------------------- vision
    def _locate(self):
        img = self.screen.full()
        geo = vision.locate(img)
        if geo is None:
            return False
        self.geo = geo
        self.box = geo.bounds()
        x0, y0 = self.box[0], self.box[1]
        self.lgeo = geo.at(x0, y0)            # geometry inside a grab
        return True

    def _grab(self):
        return self.screen.grab(self.box)

    def _wait(self, ms):
        return self.stop_event.wait(ms / 1000.0)

    # ------------------------------------------------------------- main loop
    def _main(self):
        # the look-ahead searches on another thread: switch threads often so key timing
        # stays precise
        sys.setswitchinterval(0.0005)
        try:
            planner.configure(self.h, safe=self.h.gravity == "HIGH")
            while not self.stop_event.is_set():
                self.state = "looking for board"
                if not self._locate():
                    self.log("Board not found - is TETR.IO visible on screen?")
                    if self._wait(1000):
                        break
                    continue
                self.log(f"Board found: {self.geo}")
                if self.autoplay:
                    self._play_one_game()
                else:
                    self._watch_game()
        except Exception as e:  # keep the UI alive and report
            import traceback
            traceback.print_exc()
            self.log(f"Error: {e}")
        finally:
            self.kb.release_all()
            self.state = "stopped"

    def _watch_game(self):
        """Advisor mode: follow the user's game until stopped (new games are picked up
        automatically). No keys are pressed."""
        from .coach import Coach, Watcher
        from .sprint import SprintCoach
        self.state = "watching"
        self.lookahead.reset()
        if self.sprint():
            self.coach = SprintCoach(log=self.log, threaded=True, preview=int(self.h.sprint_preview))
        else:
            self.coach = Coach(log=self.log, lookahead=self.lookahead, prior=self.prior, threaded=True)
        w = Watcher(self.coach, self.log)
        self.t_start = time.time()
        missing = 0
        try:
            while not self.stop_event.is_set():
                img = self._grab()
                if img is None:
                    missing += 1
                else:
                    w.poll(img, self.lgeo)
                    missing = missing + 1 if w.model is None else 0
                if missing > 400:          # ~5 s without a game in view: look for the board again
                    return
                self._wait(4)
        finally:
            self.coach.close()

    def _play_one_game(self):
        self.state = "waiting for game start"
        self.board = core.Board()
        # Wait until a piece is falling and the queue is full.
        while not self.stop_event.is_set():
            img = self._grab()
            p, cells = vision.read_active(img, self.lgeo, None)
            q = vision.read_queue(img, self.lgeo)
            if p is not None and len(q) == 5 and min(y for _, y in cells) >= 10:
                break
            if self._wait(15):
                return
        if self.stop_event.is_set():
            return
        hold = vision.read_hold(img, self.lgeo)
        board = vision.read_board(img, self.lgeo)[0]
        for x, y in cells:
            if y < 20:
                board.rows[y] &= ~(1 << x)
        fresh = board.rows[0] == 0 and hold is None
        self.board = board
        self.lookahead.reset()
        if self.sprint():
            from .sprint import SprintBrain
            self.brain = SprintBrain(log=self.log, preview=int(self.h.sprint_preview))
            if not fresh:
                self.log("[sprint] joined mid-game: lines are counted from here")
        else:
            self.brain = Brain(log=self.log, lookahead=self.lookahead)
            self.brain.bag.reset(aligned=fresh)
            if not fresh:
                self.brain.stage = "FREE"
                self.log("Joined mid-game: free play until the field is empty")
        cur, queue = p, q
        self.hold = hold
        self.pieces = 0
        self.t_start = self.t_spawn = time.time()
        self.state = "playing"
        self.log(f"Game started: current {cur}, next {''.join(queue)}")
        step = self._decide(self.brain, self.board, cur, self.hold, queue)
        while not self.stop_event.is_set():
            if self.sprint() and self.brain.done():
                self.state = "finished"
                return                          # 40 lines: TETR.IO ends the game
            if step is None:
                self.log("No legal move - stopping")
                return
            # 1. inputs (everything except the hard drop)
            keys = step.keys()[:-1]
            if self.start_state is not None:
                # the piece is not at spawn (keys meant for another piece moved it):
                # steer it from where it is - unless the new plan holds it away first
                p0, st0 = self.start_state
                if not step.hold and step.pl.piece == p0 and st0 is not None:
                    fix = planner.generate(self.board, p0, start=st0).get(step.pl.cells)
                    keys = fix.inputs[:-1] if fix is not None else keys
                self.start_state = None
            # a soft drop can't be undone: move in the air first, check on screen that the
            # piece is in the planned column + rotation, and only then soft drop and kick it
            # in with the rotation(s). A correction is checked the same way (up to 3 rounds).
            from_state = self.start_state[1] if self.start_state and self.start_state[0] == step.pl.piece else None
            for _ in range(3):
                if core.SOFT not in keys:
                    break
                i_sd = keys.index(core.SOFT)
                air, rest = keys[:i_sd], keys[i_sd:]
                for k in air:
                    if self.stop_event.is_set():
                        return
                    self._press(k)
                keys, from_state, fixed = self._check_before_softdrop(step, air, rest, from_state)
                if not fixed:
                    break
            for k in keys:
                if self.stop_event.is_set():
                    return
                self._press(k)
            t_keys = time.time()
            # 2. plan the next piece now (on copies), assuming this one lands as planned.
            #    This overlaps with the screen lag, so the next piece's keys can go out
            #    the instant this one is hard dropped. A new setup / PC choice waits for
            #    the newly revealed queue piece, which _confirm reads before the drop.
            self.pre = self._preplan(step, cur, queue, None)
            # 3. look at the screen
            self.resynced = False
            res, actual, fresh_q = self._confirm(step, cur, queue)
            if res in ("unknown", "wrong") and self._new_game_on_screen(queue):
                self.log("[game] TETR.IO restarted (empty field, nothing falling) - waiting for the next game")
                return
            if fresh_q:                          # screen queue -> this piece's full queue
                queue = ([queue[0]] + fresh_q) if (step.hold and self.hold is None) else fresh_q
                ncur_f, nqueue_f, _, _ = _advance(cur, queue, self.hold, step)
                if ncur_f == self.pre["cur"]:
                    self.pre["queue"] = nqueue_f
            plan_after = self.pre["deferred"] or self._mode_changed(self.pre)
            if plan_after and not self.pre.get("after_drop") and not (res == "ok" and self.confirm_resting):
                # piece still in the air: plan the next one now, drop after
                self.pre = self._preplan(step, cur, queue, True)
                plan_after = False
            # (otherwise the piece is on the stack with its lock delay running:
            #  drop it first, plan the next piece afterwards)
            if self.stop_event.is_set():
                return
            # 4. hard drop - unless the piece already locked by itself (then a hard drop
            #    would slam the next piece down where it spawned). Failsafe: on the ground
            #    close to its lock delay, without TETR.IO's "prevent accidental hard drops",
            #    let it lock by itself instead of risking a hard drop on the next piece.
            if res == "ok" and self._lock_imminent():
                self.log(f"[check] {step.pl.piece} is about to lock by itself - not hard dropping")
                res, actual = self._wait_autolock(step, cur, queue)
            if res == "wrong":
                # a different piece is falling (e.g. a hold press or the moves were lost):
                # do NOT hard drop - plan again for the piece that is really there
                p_real, st_real = self.wrong
                img = self._grab()
                hold_real = vision.read_hold(img, self.lgeo)
                locked = vision.hold_locked(img, self.lgeo)
                q_real = vision.read_queue(img, self.lgeo)
                self.wrong_count += 1
                self.log(f"[check] expected {step.pl.piece} but {p_real} is falling - not hard dropping, "
                         f"re-planning{' (hold is used up for this piece)' if locked else ''}")
                if hold_real is not None or self.hold is None:
                    self.hold = hold_real
                if len(q_real) == 5:
                    queue = q_real
                cur = p_real
                self.start_state = (p_real, st_real)
                self.brain.plan = []
                if self.wrong_count >= 3:
                    # something about the model is off: re-read everything, play this piece
                    # without hold and continue in free play
                    self.log("[sync] repeated wrong piece - re-reading the board, free play")
                    self._resync_from_screen()
                    locked = True
                planner.SETTINGS["hold_locked"] = locked
                try:
                    step = self._decide(self.brain, self.board, cur, self.hold, queue)
                finally:
                    planner.SETTINGS["hold_locked"] = False
                continue
            self.wrong_count = 0
            if res != "locked" and time.time() - self.confirm_time > 0.06:
                # never press space on a stale look: is the piece still the one in play?
                res2, cells2 = self._predrop_check(step, cur, queue)
                if res2 == "locked":
                    res, actual = "locked", cells2
            if res != "locked":
                self._press(core.HARD)
            waited = time.time() - t_keys
            if waited > 0.3:
                self.log(f"[slow] {step.pl.piece}: {waited * 1000:.0f} ms from its last key to the hard drop"
                         + (" (it locked by itself)" if res == "locked" else ""))
            self.t_spawn = time.time()
            self.pieces += 1
            if plan_after:
                self.pre = self._preplan(step, cur, queue, True)
            nb, nbrain, nstep = self.pre["board"], self.pre["brain"], self.pre["step"]
            ncur, nqueue, nhold = self.pre["cur"], self.pre["queue"], self.pre["hold"]
            cleared_now = bool(self.pre.get("cleared"))
            # 5. commit
            if res == "locked" and actual == set(step.pl.cells):
                res = "ok"                      # it locked by itself, but in the right place
            if self.resynced:
                # the model was wrong: keep the piece bookkeeping, re-read the board
                ncur, nqueue, nhold, _ = _advance(cur, queue, self.hold, step)
                self.brain = nbrain.adopt()
                time.sleep(self.lag + 0.02)
                self._resync_from_screen()
                cur, queue, self.hold = ncur, nqueue, nhold
                step = self._decide(self.brain, self.board, cur, self.hold, queue)
                continue
            if res in ("ok", "unknown"):
                self.board, self.brain = nb, nbrain.adopt()
                cur, queue, self.hold = ncur, nqueue, nhold
                step = nstep
                if cleared_now:
                    # TETR.IO ignores moves pressed during the line clear: wait for the spawn
                    self._wait_spawn(cur, queue)
                continue
            # the piece ended somewhere else: record the truth and plan again
            ncur, nqueue, nhold, hwe = _advance(cur, queue, self.hold, step)
            if actual is not None:
                a = core.Placement(step.pl.piece, *_state_of(step.pl.piece, actual), [], None)
                cl = self.board.place_cells(a.cells)
                self.brain.on_lock(planner.Step(step.hold, a, None), hwe, cl, self.board)
                self.log(f"[check] {step.pl.piece} ended at {sorted(actual)} instead of the plan")
            else:
                self.brain.on_lock(planner.Step(step.hold, step.pl, None), hwe, [], self.board)
                self._resync_from_screen()
            cur, queue, self.hold = ncur, nqueue, nhold
            step = self._decide(self.brain, self.board, cur, self.hold, queue)

    def _preplan(self, step, cur, queue, final):
        """Decide the next piece on copies of the model, as if `step` lands as planned.
        final=None: skip (defer) if a new setup / PC choice is due - that should see
        the queue piece revealed by this piece's spawn first."""
        nb = self.board.copy()
        ncleared = nb.place_cells(step.pl.cells)
        ncur, nqueue, nhold, hwe = _advance(cur, queue, self.hold, step)
        nbrain = self.brain.clone()
        nbrain.on_lock(step, hwe, ncleared, nb)
        out = dict(board=nb, brain=nbrain, cur=ncur, queue=nqueue, hold=nhold, step=None, deferred=False,
                   cleared=len(ncleared))
        # a new setup / PC choice (free play looks for PCs every piece while the field is
        # low) should see the queue piece this piece's spawn reveals. A search for a PC in
        # view during a setup may take a while: only after this piece is hard dropped.
        pc_due = False
        if ncur and not self.sprint():
            nbrain.bag.update(nbrain.cur_index, ncur, nqueue)     # as decide() will: same pieces in view
            pc_due = nbrain.pc_check_due(nb, nhold)
        choosing = not self.sprint() and nbrain.ts is None and not nbrain.plan and (
            nbrain.stage != "FREE" or (0 < nb.height() <= 6 and not planner.SETTINGS["safe"]))
        # a soft-dropped (tucked / spun) piece rests on the stack with its lock delay running:
        # hard drop it first, plan after (at high gravity every piece soft drops: keep the
        # pipelining there, _lock_imminent guards it)
        resting = core.SOFT in step.keys() and not planner.SETTINGS["safe"]
        if (choosing or pc_due or resting) and not final:
            out["deferred"], out["after_drop"] = True, pc_due or resting
            return out
        out["step"] = self._decide(nbrain, nb, ncur, nhold, nqueue) if ncur else None
        out["mode"] = (planner.SETTINGS["safe"], planner._air_ms(nb))
        return out

    def _mode_changed(self, pre):
        """Did the gravity measured meanwhile change how the next piece must move?"""
        if pre.get("mode") is None:
            return False
        self._update_safe(pre["board"])
        return (planner.SETTINGS["safe"], planner._air_ms(pre["board"])) != pre["mode"]

    def _wait_spawn(self, cur, queue, timeout_s=0.6):
        """After a line clear: wait until the next piece is on screen near the top AND the
        queue has moved on (a stale frame of an identical previous piece must not count)."""
        t_end = time.time() + timeout_s
        k = min(4, len(queue))
        while time.time() < t_end and not self.stop_event.is_set():
            img = self._grab()
            p, act = vision.read_active(img, self.lgeo, self.board, cur)
            q = vision.read_queue(img, self.lgeo)
            if p == cur and act and min(y for _, y in act) >= 17 and len(q) == 5 and q[:k] == list(queue[:k]):
                return True
            time.sleep(0.004)
        return False

    def _decide(self, brain, board, cur, hold, queue):
        self._update_safe(board)
        return brain.decide(board, cur, hold, queue)

    # ------------------------------------------------------------- gravity
    def _update_safe(self, board):
        """High-gravity mode (soft drop after every input) only when the piece would
        reach the stack before the inputs are done."""
        g = self.h.gravity
        if g == "HIGH" or g == "LOW":
            planner.configure(safe=(g == "HIGH"))
            return
        headroom = 20 - board.height() - 1
        safe = self.grav_rps * 0.3 >= headroom
        if safe != planner.SETTINGS["safe"]:
            self.log(f"[gravity] {self.grav_rps:.0f} rows/s, {headroom} rows free -> "
                     + ("soft drop after every input" if safe else "normal inputs"))
            planner.configure(safe=safe)

    def _note_gravity(self, rate, lower_bound=False):
        rate = min(max(rate, 0.0), 2400.0)
        if rate >= self.grav_rps:
            self.grav_rps = rate
        elif not lower_bound:                   # gravity only creeps down (noisy readings)
            self.grav_rps = 0.8 * self.grav_rps + 0.2 * rate
        planner.configure(gravity_rps=self.grav_rps)

    # ------------------------------------------------------------- inputs
    def _press(self, k):
        if k == core.SOFT and not self.h.sdf_infinite:
            self._softdrop_until_landed()
        else:
            self.kb.press(k)

    def _softdrop_until_landed(self, timeout_s=3.0):
        """Finite SDF: hold soft drop and watch the screen until the piece rests."""
        self.kb.down(core.SOFT)
        t_end = time.time() + timeout_s
        try:
            while time.time() < t_end and not self.stop_event.is_set():
                time.sleep(0.008)
                p, cells = vision.read_active(self._grab(), self.lgeo, self.board)
                if p and cells:
                    if any(y == 0 or self.board.filled(x, y - 1) for x, y in cells):
                        break
        finally:
            self.kb.up(core.SOFT)
            time.sleep(self.h.key_gap_ms / 1000.0)

    def _check_before_softdrop(self, step, air, rest, start=None):
        """The piece should now be up in the air in the column + rotation the soft drop
        needs. If the screen shows it elsewhere (e.g. a DAS slide that only moved one cell,
        2026-10-09 23:20 recording), re-plan the keys from where it really is.
        Returns (keys to press next, state they start from, corrected?)."""
        piece = step.pl.piece
        want = core.walk(self.board, piece, [k for k in air if k != core.HOLD], start=start)[-1]
        t0 = time.time()
        settle = max(0.04, 2.0 * self.lag)
        wrong, wrong_since = None, None
        while time.time() - t0 < max(0.15, 3.0 * self.lag + 0.05) and not self.stop_event.is_set():
            time.sleep(0.004)
            p, act = vision.read_active(self._grab(), self.lgeo, self.board, piece)
            if p != piece or not act:
                continue
            sts = core.identify(piece, act, want[2])
            if any((x, r) == (want[0], want[2]) for x, _, r in sts):
                return rest, start, False                 # where the soft drop needs it
            st = sts[0] if sts else None
            if st != wrong:
                wrong, wrong_since = st, time.time()
            elif wrong is not None and time.time() - wrong_since >= settle:
                break                                     # stayed wrong: not screen lag
        if wrong is None:
            return rest, start, False                     # couldn't see it: carry on
        if any(y == 0 or self.board.filled(x, y - 1) for x, y in core.cells_of(piece, wrong[2], wrong[0], wrong[1])):
            return rest, start, False                     # already down: the hard-drop check handles it
        fix = planner.generate(self.board, piece, start=wrong).get(step.pl.cells)
        if fix is None:
            return rest, start, False
        self.corrections += 1
        self.log(f"[check] {piece} at column {wrong[0]} rot {wrong[2]} before the soft drop, planned "
                 f"column {want[0]} rot {want[2]} - correcting: {' '.join(fix.inputs[:-1])}")
        return list(fix.inputs[:-1]), wrong, True

    def _observe(self, expect=None):
        img = self._grab()
        p, act = vision.read_active(img, self.lgeo, self.board, expect)
        act = set(act or ())
        excl = set(act)
        excl |= {(x, y) for y in range(20) for x in range(core.W) if self.board.filled(x, y)}
        colour = np.mean([vision.cell_color(img, self.lgeo, x, y) for x, y in act], axis=0) if act else None
        ghost = vision.read_ghost(img, self.lgeo, excl, color=colour)
        return p, act, ghost

    def _landing(self, piece, act, prefer_rot):
        for x, y, r in core.identify(piece, act, prefer_rot):
            return set(core.cells_of(piece, r, x, self.board.drop_y(piece, r, x, y))), (x, y, r)
        return None, None

    @staticmethod
    def _on_target(target, act, ghost, land, piece):
        """Is the piece going to land on `target`?

        `land` is where a hard drop lands according to the model board (from the
        falling piece's position); the ghost on screen is the game's own answer.
        Text drawn over the board can hide or fake bits of ghost, so the ghost only
        overrules the model when it shows a clean tetromino somewhere else."""
        if act == target:                                  # soft-dropped / spun into place
            return True
        clean = _ghost_shapes(ghost, piece)
        if land is None:
            return target in clean
        if land != target:
            return False
        return not any(g != target for g in clean)

    def _confirm(self, step, cur, queue):
        """Check the piece on screen before the hard drop.

        Returns (result, cells, fresh_queue):
          "ok"      the ghost / piece is on the planned cells
          "moved"   it could not reach the plan in time; it was steered to `cells` instead
          "locked"  it already locked by itself at `cells` (None = unknown) - don't hard drop
          "unknown" the piece couldn't be seen; hard drop as planned
        The screen lags the keys, so a wrong-looking frame is only acted on once it has
        stayed the same for longer than the measured lag. Each frame is also used to
        read the newly revealed queue piece, check the board and measure gravity."""
        piece = step.pl.piece
        target = set(step.pl.cells)
        ncur, nqueue, _, _ = _advance(cur, queue, self.hold, step)
        # queue shown while this piece falls (holding into an empty hold pulls one out)
        qk = list(queue[1:]) if (step.hold and self.hold is None) else list(queue)
        after = [ncur] + list(nqueue)          # queue order once it has locked
        t_key = time.time()
        high = planner.SETTINGS["safe"] or self.grav_rps >= 40
        max_fixes = 2
        keys = [k for k in step.keys() if k not in (core.HOLD, core.HARD)]
        # where the keys leave the piece if gravity did nothing (for measuring gravity)
        expect = core.walk(self.board, piece, keys)[-1] if core.SOFT not in keys else None
        on_path = set()
        for x, y, r in core.walk(self.board, piece, keys)[:-1]:
            on_path.add(frozenset(core.cells_of(piece, r, x, self.board.drop_y(piece, r, x, y))))
        fixes, fresh_q, checked = 0, None, False
        wrong_since = None
        self.t_last_key = t_key
        last, since, state = None, None, None
        fall = None                            # (t, y) of the piece while untouched, for gravity
        first_seen = True
        while not self.stop_event.is_set():
            time.sleep(0.005)
            img = self._grab()
            now = time.time()
            p, act = vision.read_active(img, self.lgeo, self.board, piece)
            q = vision.read_queue(img, self.lgeo)
            act = set(act or ())
            # already locked by itself? The queue moved on, so the next piece has spawned.
            # Never judge by the falling piece: a piece that locked right on the target looks
            # just like it resting there (2026-10-18 recording: a tucked L locked while the
            # next piece was planned, read as "on target", and space slammed the Z)
            if len(q) == 5 and ncur and q[:min(4, len(after) - 1)] == after[1:5]:
                cells = self._autolock_cells(img, piece)
                est = now - self.lag - self.t_last_key
                if est >= 0.1:                  # shorter readings are just screen lag
                    self.lock_est = est if self.lock_est is None else min(self.lock_est, est)
                self.log(f"[check] {piece} locked by itself before the hard drop - not hard dropping")
                return "locked", cells, None
            if p is not None and p != piece and act and wrong_since is None:
                wrong_since = now
            elif p == piece:
                wrong_since = None
            if p is not None and p != piece and act and wrong_since is not None \
                    and now - wrong_since > max(0.08, 2.5 * self.lag) and now - t_key > max(0.08, 2.5 * self.lag):
                sts = core.identify(p, act)
                self.wrong = (p, sts[0] if sts else None)
                return "wrong", None, fresh_q
            if p != piece or not act:
                if now - t_key > (0.5 if high else 0.8):
                    return "unknown", None, fresh_q
                continue
            land, st = self._landing(p, act, step.pl.rot)
            state = st or state
            resting = any(y == 0 or self.board.filled(x, y - 1) for x, y in act)
            self.confirm_time, self.confirm_resting = now, resting
            if fresh_q is None and len(q) == 5 and q[:len(qk)] == qk[:5]:
                fresh_q = q
                if self.cfg["verify_board"] and not checked:
                    checked = True
                    self._verify(img, act)
                if getattr(self, "pre", None) and self.pre["deferred"] and not self.pre.get("after_drop") \
                        and not self.resynced and not resting:
                    # still in the air: use the wait to plan the next piece
                    t_plan = time.time()
                    full = ([queue[0]] + q) if (step.hold and self.hold is None) else q
                    self.pre = self._preplan(step, cur, full, True)
                    spent = time.time() - t_plan
                    t_key += spent                     # planning time is not screen lag
                    if since is not None:
                        since += spent
                    continue                           # look again before deciding anything
            # gravity: compare the piece's position with where the keys put it. Only the
            # same column + rotation counts (rotations/kicks move cells, not gravity).
            # (TETR.IO may show a fresh piece a row lower than the model's spawn row, so
            # a single row means nothing: need >= 2 rows, and >= 0.1 s between readings)
            if expect is not None and fixes == 0 and st is not None and (st[0], st[2]) == (expect[0], expect[2]):
                fallen = expect[1] - st[1]
                elapsed = now - self.lag - self.t_spawn
                if first_seen and fallen >= 2 and elapsed >= 0.03:
                    self._note_gravity(fallen / elapsed, lower_bound=resting)
                elif first_seen and fallen <= 1 and elapsed >= 0.1 and not resting:
                    self._note_gravity(fallen / elapsed)      # hardly fell: gravity is low
                if not resting:
                    if fall is None:
                        fall = (now, st[1])
                    elif fall[1] - st[1] >= 2 and now - fall[0] >= 0.1:
                        self._note_gravity((fall[1] - st[1]) / (now - fall[0]))
            first_seen = False
            ghost = self._ghost(img, act)
            if self._on_target(target, act, ghost, land, piece):
                if fixes == 0:
                    self.lag = 0.7 * self.lag + 0.3 * min(0.3, now - t_key)
                return "ok", None, fresh_q
            key = (frozenset(ghost), frozenset(land or ()))
            if key != last:
                last, since = key, now
            settle = max(0.05, (1.5 if high else 2.5) * self.lag)
            if fixes == 0 and land is not None and frozenset(land) in on_path:
                settle = max(0.1 if high else 0.15, (2.5 if high else 4.0) * self.lag)
            timed_out = now - t_key > max(0.5 if high else 0.8, 3 * settle + 0.1)
            if not timed_out and (now - since < settle or now - t_key < settle):
                continue
            if state is None:
                if timed_out:
                    return "unknown", None, fresh_q
                continue
            fix = planner.generate(self.board, piece, start=state).get(step.pl.cells)
            # the planned spot is still reachable: always steer it there (the failsafe
            # below is only for a target that can no longer be reached)
            if fix is not None and fixes < max_fixes:
                fixes += 1
                self.corrections += 1
                self.log(f"[check] {piece} off target, correcting: {' '.join(fix.inputs[:-1]) or '(none)'}")
                for k in fix.inputs[:-1]:
                    self._press(k)
                t_key, last, fall = time.time(), None, None
                self.t_last_key = t_key
                continue
            # failsafe: don't force a placement that can't happen - take the best spot
            # reachable from where the piece really is
            alt = self._salvage(piece, state)
            if alt is None:
                return "unknown", None, fresh_q
            self.log(f"[check] {piece} can't reach the plan in time; placing it at {sorted(alt.cells)} instead")
            for k in alt.inputs[:-1]:
                self._press(k)
            return "moved", set(alt.cells), fresh_q
        return "unknown", None, fresh_q

    def _predrop_check(self, step, cur, queue, timeout_s=0.25):
        """Fresh look right before pressing space: ("ok", None) if the planned piece is
        still the one in play, ("locked", cells) if it has locked by itself meanwhile."""
        piece = step.pl.piece
        ncur, nqueue, _, _ = _advance(cur, queue, self.hold, step)
        after = [ncur] + list(nqueue)
        t_end = time.time() + timeout_s
        while not self.stop_event.is_set():
            img = self._grab()
            p, act = vision.read_active(img, self.lgeo, self.board, piece)
            q = vision.read_queue(img, self.lgeo)
            if ncur and len(q) == 5 and q[:min(4, len(after) - 1)] == after[1:5]:
                self.log(f"[check] {piece} locked by itself while planning - not hard dropping")
                return "locked", self._autolock_cells(img, piece)
            if p == piece and act:
                return "ok", None
            if time.time() > t_end:
                return "ok", None
            time.sleep(0.004)
        return "ok", None

    def _lock_imminent(self):
        if self.h.prevent_accidental_hard_drops or self.lock_est is None or not planner.SETTINGS["safe"]:
            return False
        return time.time() - self.t_last_key > 0.7 * self.lock_est

    def _wait_autolock(self, step, cur, queue, timeout_s=1.0):
        """Wait for the piece to lock by itself (next piece falling, queue moved on)."""
        ncur, nqueue, _, _ = _advance(cur, queue, self.hold, step)
        after = [ncur] + list(nqueue)
        t_end = time.time() + timeout_s
        while time.time() < t_end and not self.stop_event.is_set():
            img = self._grab()
            p, act = vision.read_active(img, self.lgeo, self.board, ncur)
            q = vision.read_queue(img, self.lgeo)
            if p == ncur and len(q) == 5 and q[:min(4, len(after) - 1)] == after[1:5]:
                return "locked", self._autolock_cells(img, step.pl.piece)
            time.sleep(0.005)
        return "ok", None                       # never saw it lock: hard drop after all

    def _ghost(self, img, act):
        excl = set(act)
        excl |= {(x, y) for y in range(20) for x in range(core.W) if self.board.filled(x, y)}
        colour = np.mean([vision.cell_color(img, self.lgeo, x, y) for x, y in act], axis=0) if act else None
        return vision.read_ghost(img, self.lgeo, excl, color=colour)

    def _salvage(self, piece, state):
        """Best placement reachable from the piece's current state (heuristic score)."""
        opts = planner.generate(self.board, piece, start=state)
        best = None
        for pl in opts.values():
            b = self.board.copy()
            n = len(b.place_cells(pl.cells))
            sc = planner.evaluate(b, n, pl.spin) - 0.5 * len(pl.inputs)
            if best is None or sc > best[0]:
                best = (sc, pl)
        return best[1] if best else None

    def _new_game_on_screen(self, queue):
        """TETR.IO restarted under the bot (2026-10-18 recording: the bot began playing from
        the last frames of the previous game, then kept the old pieces through READY / SET /
        GO and lost track): no piece falling, an empty matrix, and either blocks in the model
        or a queue that isn't the expected one."""
        for look in range(2):                  # two looks: a line-clear flash is not a restart
            if look:
                self._wait(150)
            img = self._grab()
            p, _ = vision.read_active(img, self.lgeo, None)
            if p is not None:
                return False
            vb, _, _ = vision.read_board_ex(img, self.lgeo)
            if vb.rows[0] != 0:
                return False
            q = vision.read_queue(img, self.lgeo)
            if not (self.board.rows[0] != 0 or (len(q) == 5 and q != list(queue)[1:6] and q != list(queue)[:5])):
                return False
        return True

    def _autolock_cells(self, img, piece):
        """Where a piece locked by itself: the 4 new blocks on screen, if they form it."""
        vb, _, unknown = vision.read_board_ex(img, self.lgeo)
        p, act = vision.read_active(img, self.lgeo, self.board)
        new = {(x, y) for y in range(20) for x in range(core.W)
               if vb.filled(x, y) and not self.board.filled(x, y) and (x, y) not in set(act or ())}
        if len(new) == 4 and core.identify(piece, new):
            return new
        return None

    def _resync_from_screen(self):
        img = self._grab()
        vb, _, _ = vision.read_board_ex(img, self.lgeo)
        p, act = vision.read_active(img, self.lgeo, None)
        for x, y in act or ():
            if y < 20:
                vb.rows[y] &= ~(1 << x)
        self.log("[sync] reading the board from the screen")
        self.board = vb
        self.brain.ts = None
        self.brain.plan = []
        if self.brain.stage != "OPENER" or vb.rows[0]:
            self.brain.stage = "FREE"
        self.resynced = True

    def _verify(self, img, active_cells):
        """Compare the screen with the model on one frame. Cells hidden by text (ALL
        CLEAR, combo numbers) and blocks floating in mid-air are ignored, and a
        difference must show up on two pieces in a row before the model is replaced."""
        sim = self.board.copy()
        for y in range(20, core.H):
            sim.rows[y] = 0
        vb, _, unknown = vision.read_board_ex(img, self.lgeo)
        skip = set(unknown) | set(active_cells or ())
        diff = {(x, y) for y in range(20) for x in range(core.W)
                if (x, y) not in skip and vb.filled(x, y) != sim.filled(x, y)}
        diff -= _floating_extras(vb, sim, diff)
        if not diff:
            self.pending_diff = None
            return
        if self.pending_diff is None or not (diff & self.pending_diff):
            self.pending_diff = diff
            self.log(f"[sync] screen differs in {len(diff)} cells - checking again next piece")
            return
        self.pending_diff = None
        for x, y in active_cells or ():
            if y < 20:
                vb.rows[y] &= ~(1 << x)
        self.log(f"[sync] board differs from the model by {len(diff)} cells two pieces running - resyncing")
        self.board = vb
        self.brain.ts = None
        self.brain.plan = []
        if self.brain.stage != "OPENER" or vb.rows[0]:
            self.brain.stage = "FREE"
        self.resynced = True


def _advance(cur, queue, hold, step):
    """Hold/spawn bookkeeping for `step`: (next current, next queue, hold, hold_was_empty)."""
    q = list(queue)
    hold_was_empty = hold is None
    if step.hold:
        if hold_was_empty:
            q = q[1:]
        hold = cur
    return (q[0] if q else None), q[1:], hold, hold_was_empty


def _state_of(piece, cells):
    st = core.identify(piece, cells)
    x, y, r = st[0]
    return r, x, y


def _floating_extras(screen, model, diff):
    """Screen-only blocks that hang in mid-air (nothing under any of them) - text or
    effects drawn over the board. A real misplaced piece was hard dropped, so it
    always rests on the floor or on another block."""
    extra = {c for c in diff if screen.filled(*c) and not model.filled(*c)}
    out, seen = set(), set()
    for c in extra:
        if c in seen:
            continue
        grp, stack = set(), [c]
        seen.add(c)
        while stack:
            x, y = stack.pop()
            grp.add((x, y))
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in extra and n not in seen:
                    seen.add(n)
                    stack.append(n)
        supported = any(y == 0 or ((x, y - 1) not in grp and screen.filled(x, y - 1)) for x, y in grp)
        if not supported:
            out |= grp
    return out


def _ghost_shapes(ghost, piece):
    """4-cell connected groups of ghost cells that form `piece` (as frozensets)."""
    out, seen = [], set()
    for c in ghost:
        if c in seen:
            continue
        grp, stack = [], [c]
        seen.add(c)
        while stack:
            x, y = stack.pop()
            grp.append((x, y))
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if n in ghost and n not in seen:
                    seen.add(n)
                    stack.append(n)
        if len(grp) == 4 and core.identify(piece, grp):
            out.append(set(grp))
    return out

"""A fake TETR.IO screen + keyboard backed by the simulator, for end-to-end tests
of the controller loop (vision -> brain -> keys -> ghost check) without a browser.

The falling piece moves key by key, a ghost outline is drawn like TETR.IO's, and
taps can be randomly dropped (drop_rate) to exercise the pre-hard-drop correction."""
import random
import time

import numpy as np

from tetrisbot import core, sim, vision

BG = (22, 24, 40)


class FakeTetrio:
    def __init__(self, seed=1, cell=20, left=300, top=120, size=(900, 1400), gravity_rows=0, drop_rate=0.0,
                 latency_ms=0.0, banner_s=0.0, g_rps=0.0, lock_ms=500.0, timed_keys=False,
                 prevent_hd_ms=150.0, g_ramp_pieces=0, clear_delay_ms=0.0, ihs_buffer=True,
                 lock_always=False, das_fail_rate=0.0):
        self.game = sim.Game(seed)
        self.rng = random.Random(seed + 99)
        self.c, self.left, self.top = cell, left, top
        self.size = size
        self.gravity_rows = gravity_rows   # rows a new piece falls right after spawning
        self.drop_rate = drop_rate         # chance a movement tap is ignored
        self.over = False
        self.pieces = 0
        self.limit = 10 ** 9
        self.dropped = 0
        self.h = None                      # handling (set by the controller)
        self.latency = latency_ms / 1000.0 # screen shows the game as it was this long ago
        self.snaps = []
        self.banner_s = banner_s            # show an "ALL CLEAR" banner this long after each PC
        self.banner_until = 0.0
        self.pcs = 0
        # real-time gravity / lock delay (TETR.IO-like)
        self.g_max = g_rps                 # rows per second the piece falls by itself
        self.g_ramp = g_ramp_pieces        # >0: gravity grows from 0 to g_max over this many pieces
        self.lock_s = lock_ms / 1000.0
        self.timed_keys = timed_keys       # key presses take real time (from handling)
        self.prevent_hd_s = prevent_hd_ms / 1000.0
        self.autolocks = 0
        self.ignored_hd = 0
        self.slammed = 0                   # hard drops that hit a freshly spawned piece
        self.last_autolock = -1.0
        self.clear_delay = clear_delay_ms / 1000.0   # line clear delay: next piece spawns late
        self.spawn_at = None
        self.buffered = []                 # IRS/IHS: rotations / hold pressed before spawn
        self.lost_inputs = 0
        self.ihs_buffer = ihs_buffer       # False: a hold pressed during the line clear is lost
        self.hold_used = False
        self.prev_autolocked = False
        self.lock_always = lock_always     # lock delay also without gravity (pieces resting on the stack)
        self.das_fail_rate = das_fail_rate # chance a DAS slide only moves one cell (frame hitch)
        self.das_failed = 0
        self.wrong_tucks = 0               # pieces soft-dropped away from where they were meant to go
        self._spawn()

    # ------------------------------------------------------------ piece state
    def _snap(self):
        g = self.game
        state = None if self.spawn_at is not None else tuple(self.state)
        self.snaps.append((time.time(), (g.board.copy(), g.current, state, g.hold, list(g.visible()),
                                         self.over, self.hold_used)))
        self.snaps = self.snaps[-200:]

    def _view(self):
        """State as currently visible on the fake screen (render latency)."""
        cutoff = time.time() - self.latency
        view = self.snaps[0][1]
        for t, snap in self.snaps:
            if t <= cutoff:
                view = snap
        return view

    def _spawn(self):
        g = self.game
        x, y, r = core.SPAWN_X, core.SPAWN_Y, 0
        if g.board.collides(g.current, r, x, y):
            y += 1
        y = max(g.board.drop_y(g.current, r, x, y), y - self.gravity_rows)
        self.state = [x, y, r]
        self.t_tick = time.time()
        self.fall = 0.0
        self.rest_since = None
        self.resets = 0
        self.inputs_since_spawn = 0
        self._snap()

    def _resting(self):
        x, y, r = self.state
        return self.game.board.collides(self.game.current, r, x, y - 1)

    @property
    def g_rps(self):
        if self.g_ramp:
            return self.g_max * min(1.0, self.pieces / self.g_ramp)
        return self.g_max

    def _tick(self):
        """Advance real-time gravity and lock delay up to now."""
        if self.spawn_at is not None:
            if time.time() < self.spawn_at:
                return
            self.spawn_at = None
            self._spawn()
            for k in self.buffered:                  # IRS / IHS (TAP)
                self._apply(k)
            self.buffered = []
        if self.over:
            self.t_tick = time.time()
            return
        now = time.time()
        self.fall += (now - self.t_tick) * self.g_rps
        self.t_tick = now
        moved = False
        while self.fall >= 1 and not self._resting():
            self.state[1] -= 1
            self.fall -= 1
            moved = True
        if self._resting() and (self.g_rps or self.lock_always):
            self.fall = 0.0
            if self.rest_since is None:
                self.rest_since = now
            elif now - self.rest_since >= self.lock_s:
                self.autolocks += 1
                self.prev_autolocked = True
                self.last_autolock = now
                self._lock()
                return
        if moved:
            self._snap()

    def _lock(self):
        self.hold_used = False
        g = self.game
        x, y, r = self.state
        p = g.current
        y = g.board.drop_y(p, r, x, y)
        cleared = g.board.place_cells(core.cells_of(p, r, x, y))
        g.lines += len(cleared)
        if cleared and g.board.rows[0] == 0:
            self.pcs += 1
            self.banner_until = time.time() + self.banner_s
        g.current = g.queue.pop(0)
        g._fill()
        self.pieces += 1
        if self.pieces >= self.limit:
            self.over = True
        if cleared and self.clear_delay:
            self.spawn_at = time.time() + self.clear_delay
            self._snap()
            return
        self._spawn()

    def _apply(self, k):
        self._tick()
        if self.spawn_at is not None:                # line clear delay: no piece yet
            if k in (core.CW, core.CCW, core.R180) or (k == core.HOLD and self.ihs_buffer):
                self.buffered.append(k)
            else:
                self.lost_inputs += 1
            return
        g, (x, y, r) = self.game, self.state
        p = g.current
        if k in (core.LEFT, core.RIGHT) and self.drop_rate and self.rng.random() < self.drop_rate:
            self.dropped += 1
            return
        before = (x, y, r)
        if k != core.HARD:
            self.inputs_since_spawn += 1
        if k in (core.LEFT, core.RIGHT):
            nx = x + (-1 if k == core.LEFT else 1)
            if not g.board.collides(p, r, nx, y):
                x = nx
        elif k in (core.DAS_LEFT, core.DAS_RIGHT):
            d = -1 if k == core.DAS_LEFT else 1
            if self.das_fail_rate and self.rng.random() < self.das_fail_rate:
                self.das_failed += 1               # TETR.IO only saw a tap
                if not g.board.collides(p, r, x + d, y):
                    x += d
            else:
                x = core.slide(g.board, p, r, x, y, d)
        elif k in (core.CW, core.CCW, core.R180):
            nr = (r + {core.CW: 1, core.CCW: 3, core.R180: 2}[k]) % 4
            for kx, ky in core.kicks(p, r, nr):
                if not g.board.collides(p, nr, x + kx, y + ky):
                    x, y, r = x + kx, y + ky, nr
                    break
        elif k == core.SOFT:
            y = g.board.drop_y(p, r, x, y)
        elif k == core.HOLD:
            if self.hold_used:                    # TETR.IO: one hold per piece
                return
            self.hold_used = True
            if g.hold is None:
                g.hold, g.current = g.current, g.queue.pop(0)
                g._fill()
            else:
                g.hold, g.current = g.current, g.hold
            self._spawn()
            return
        elif k == core.HARD:
            since = time.time() - self.last_autolock
            if since < self.prevent_hd_s:
                self.ignored_hd += 1          # TETR.IO "prevent accidental hard drops"
                return
            if self.inputs_since_spawn == 0 and self.prev_autolocked:
                self.slammed += 1             # meant for the piece that locked by itself
            self.prev_autolocked = False
            self._lock()
            return
        if self.gravity_rows:
            y = g.board.drop_y(p, r, x, y)
        self.state = [x, y, r]
        if (x, y, r) != before and self.rest_since is not None and self.resets < 15:
            self.rest_since = time.time()      # move reset of the lock delay
            self.resets += 1
        self._snap()

    # ------------------------------------------------------------ "Keyboard"
    def press(self, k):
        if not self.timed_keys or self.h is None:
            self._apply(k)
            return
        h = self.h
        if k in (core.DAS_LEFT, core.DAS_RIGHT):
            self._apply(core.LEFT if k == core.DAS_LEFT else core.RIGHT)   # first step on key down
            time.sleep(h.das_ms / 1000.0)
            self._apply(k)                                                   # auto-shift to the wall
            time.sleep(max(0.0, h.das_hold_ms() - h.das_ms) / 1000.0)
        else:
            self._apply(k)
            time.sleep((h.softdrop_ms() if k == core.SOFT else h.tap_ms()) / 1000.0)
        time.sleep(h.key_gap_ms / 1000.0)

    def down(self, k):
        self._apply(k)

    def up(self, k):
        pass

    def release_all(self):
        pass

    # ------------------------------------------------------------ "Screen"
    def full(self):
        self._tick()
        return self.render()

    def grab(self, box):
        self._tick()
        img = self.render()
        x0, y0, x1, y1 = (int(v) for v in box)
        out = np.zeros((y1 - y0, x1 - x0, 3), np.uint8)
        out[:] = BG
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(img.shape[1], x1), min(img.shape[0], y1)
        out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = img[sy0:sy1, sx0:sx1]
        return out

    def _rect(self, img, x0, y0, x1, y1, color):
        img[int(y0):int(y1), int(x0):int(x1)] = color

    def _cell(self, img, x, y, color):
        c = self.c
        px = self.left + x * c
        py = self.top + (19 - y) * c
        self._rect(img, px + 1, py + 1, px + c, py + c, color)

    def _ghost(self, img, cells, color):
        """Outline around the whole piece, a quarter cell thick."""
        c, t = self.c, max(2, self.c // 4)
        cs = set(cells)
        for x, y in cells:
            px, py = self.left + x * c, self.top + (19 - y) * c
            if (x - 1, y) not in cs:
                self._rect(img, px + 1, py + 1, px + 1 + t, py + c, color)
            if (x + 1, y) not in cs:
                self._rect(img, px + c - t, py + 1, px + c, py + c, color)
            if (x, y + 1) not in cs:
                self._rect(img, px + 1, py + 1, px + c, py + 1 + t, color)
            if (x, y - 1) not in cs:
                self._rect(img, px + 1, py + c - t, px + c, py + c, color)

    def render(self):
        h, w = self.size
        img = np.zeros((h, w, 3), np.uint8)
        img[:] = BG
        c, L, T = self.c, self.left, self.top
        board, current, state, hold, visible, over, hold_used = self._view()
        if over:
            return img
        self._rect(img, L, T, L + 10 * c, T + 20 * c, (4, 4, 4))
        for i in range(11):
            self._rect(img, L + i * c, T, L + i * c + 1, T + 20 * c, (23, 23, 23))
        for j in range(21):
            self._rect(img, L, T + j * c, L + 10 * c, T + j * c + 1, (23, 23, 23))
        self._rect(img, L - 3, T, L, T + 20 * c + 2, (252, 252, 252))
        self._rect(img, L + 10 * c, T, L + 10 * c + 3, T + 20 * c + 2, (252, 252, 252))
        self._rect(img, L - 3, T + 20 * c - 1, L + 10 * c + 3, T + 20 * c + 2, (252, 252, 252))
        self._rect(img, L + 10 * c + 3, T + 10 * c, L + 10.6 * c, T + 20 * c, (171, 84, 34))
        nx0, nx1 = L + 10.7 * c, L + 15.85 * c
        self._rect(img, nx0, T, nx1, T + 15.5 * c, (4, 4, 4))
        self._rect(img, nx0 - 3, T, nx0, T + 15.5 * c, (252, 252, 252))
        self._rect(img, nx1, T, nx1 + 3, T + 15.5 * c, (252, 252, 252))
        self._rect(img, nx0, T, nx1, T + 0.8 * c, (252, 252, 252))
        hx0 = L - 5.2 * c
        self._rect(img, hx0, T, L - 3, T + 3.85 * c, (4, 4, 4))
        self._rect(img, hx0 - 3, T, hx0, T + 3.85 * c, (252, 252, 252))
        self._rect(img, hx0, T, L - 3, T + 0.8 * c, (252, 252, 252))
        for y in range(20):
            for x in range(10):
                if board.filled(x, y):
                    self._cell(img, x, y, (150, 150, 150))
        if state is not None:
            x, y, r = state
            col = vision.PALETTE[current]
            gy = board.drop_y(current, r, x, y)
            if gy != y:
                self._ghost(img, core.cells_of(current, r, x, gy), col)
            for cx, cy in core.cells_of(current, r, x, y):
                self._cell(img, cx, cy, col)
        if time.time() < self.banner_until:
            self._banner(img)
        for i, p in enumerate(visible):
            self._preview(img, p, nx0 + 1.0 * c, T + (1.5 + 3 * i) * c)
        if hold:
            self._preview(img, hold, hx0 + 1.0 * c, T + 1.4 * c, grey=hold_used)
        return img

    def _banner(self, img):
        """Big gradient text strokes over rows 8-12, like TETR.IO's ALL CLEAR."""
        c, L, T = self.c, self.left, self.top
        y_top = T + (19 - 12) * c
        for i in range(9):                     # vertical strokes, some fully covering cells
            x0 = L + (0.6 + i * 1.05) * c
            for j in range(int(5 * c)):
                t = j / (5 * c)
                col = (int(250 - 60 * t), int(235 - 110 * t), int(120 - 80 * t))
                img[int(y_top + j), int(x0):int(x0 + 0.9 * c)] = col
        for k in (0.5, 2.5, 4.4):              # horizontal bars
            yy = int(y_top + k * c)
            img[yy:yy + int(0.4 * c), int(L + 0.5 * c):int(L + 9.5 * c)] = (245, 225, 110)

    def _preview(self, img, p, x0, y0, grey=False):
        c = self.c
        col = (40, 40, 40) if grey else vision.PALETTE[p]
        for j, row in enumerate(vision._PREVIEW[p]):
            for i, ch in enumerate(row):
                if ch == "X":
                    self._rect(img, x0 + i * c + 1, y0 + j * c + 1, x0 + (i + 1) * c, y0 + (j + 1) * c, col)

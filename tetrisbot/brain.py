"""Decision making: which setup to build, perfect clears, DPC loop, fallback play.

Flow (the PC loop the user asked for):
  OPENER  SingleYou > Mountainous Stacking 2 > Mountainous Stacking / MS3   (bag 1)
  BAG2    that opener's second-bag setup (TSD / TST)                         (bag 2)
  PC8     8-line perfect clear (solver)                                      (bag 3, 6 pieces)
  DPC     TSD setup from four.lol/DPC built from the 1 leftover piece + bag 4
  PCDPC   4-line perfect clear (solver) -> empty field, fresh bag -> OPENER
Anything that can't be built falls back to FREE: heuristic stacking that keeps
looking for perfect clears and restarts the loop when the field is empty.
"""
import threading
from collections import Counter
from itertools import permutations

from . import core, planner, templates as T

ALL = set(core.PIECES)
DPC_LOOKAHEAD_SLOTS = 3
JAWS_BUILD_FIRST = True     # before a Jaws solve is chosen: only place I L S Z (or hold)   # a DPC build plans its PC once this many slots are left (incl. the T)


def _stable_seed(*parts):
    """Same seed for the same inputs in every run (hash() of strings is randomised per
    process, which made planning differ between runs)."""
    import zlib
    return zlib.crc32("|".join(parts).encode())


def _hurry():
    """High gravity on the bot thread: the piece is already falling - keep searches short."""
    return planner.SETTINGS["safe"] and not planner.background()


def all_pc():
    """ALL PC mode (Openers window): Jaws, then four.lol's 2nd-7th PCs, looped."""
    return getattr(planner.SETTINGS["handling"], "all_pc", False)


# a 4-line PC uses 10 pieces, a bag has 7: the pieces of the oldest bag still unplaced
# after a PC say which PC of the loop comes next
PC_NO = {0: 1, 4: 2, 1: 3, 5: 4, 2: 5, 6: 6, 3: 7}


def opener_priority():
    """Opener families switched on in the Openers window, in the user's priority order."""
    if all_pc():
        return ["JAWS"]
    txt = getattr(planner.SETTINGS["handling"], "openers", None)
    if txt is None:
        return list(T.FAMILY_PRIORITY)
    return [f.strip() for f in txt.split(",") if f.strip() in T.PC_RATE]


def enabled_openers():
    """Opener families switched on in the Openers window."""
    return set(opener_priority())
_OUTLOOK = {}          # Brain._dpc_outlook results, see there


class BagTracker:
    """Every piece seen in spawn order, plus 7-bag inference of what comes next."""

    def __init__(self):
        self.history = []
        self.offset = None   # history index where some bag starts (mod 7); None = unknown

    def reset(self, aligned):
        self.history = []
        self.offset = 0 if aligned else None

    def update(self, idx, current, queue):
        """Record that history[idx] is `current` followed by `queue`."""
        obs = [current] + list(queue)
        h = self.history
        while len(h) < idx:
            h.append("?")
        for k, p in enumerate(obs):
            j = idx + k
            if j < len(h):
                if h[j] != p:
                    h[j] = p
                    del h[j + 1:]
            else:
                h.append(p)
        if self.offset is None:
            self._align()

    def _align(self):
        h, n = self.history, len(self.history)
        ok = []
        for o in range(7):
            good = True
            for s in range(o - 7, n, 7):
                w = [p for p in h[max(s, 0):s + 7] if p != "?"]
                if len(set(w)) != len(w):
                    good = False
                    break
            if good:
                ok.append(o)
        if len(ok) == 1:
            self.offset = ok[0]

    def known(self, idx):
        """Known pieces from history[idx] on, plus the last piece of a bag if inferable."""
        seq = list(self.history[idx:])
        if self.offset is not None and "?" not in seq:
            n = len(self.history)
            pos = (n - self.offset) % 7
            seen = set(self.history[max(n - pos, 0):n])
            if pos == 6 and len(seen) == 6:
                seq.append(next(iter(ALL - seen)))
        return seq

    def future(self, idx):
        """Counter of piece types that may arrive right after known(idx); None = unknown."""
        if self.offset is None:
            return None
        ext = self.history[:idx] + self.known(idx)
        m = len(ext)
        pos = (m - self.offset) % 7
        rest = Counter(ALL - set(ext[max(m - pos, 0):m])) if pos else Counter()
        rest.update(ALL)
        return rest


class Lookahead:
    """Plans the NEXT stage ahead of time. While a T-spin setup is being built (2nd bag
    of SingleYou / Mountainous Stacking, or a DPC setup) the bot already knows how that
    setup will end, so it searches the perfect clear that follows - on a background
    thread - using the pieces it can see. When the setup is finished the solve is ready
    instantly (no searching while a piece sits on the stack), and the overlay's "Next"
    window shows it."""

    def __init__(self, threaded=True):
        self.threaded = threaded
        self._warm_sig, self._warm_todo, self._warm_done = None, [], set()
        self.sig = None
        self.results = {}          # key -> result dict (latest per key)
        self.display = None
        self.display_board = None
        self._job = None
        self._cv = threading.Condition()
        if threaded:
            threading.Thread(target=self._loop, daemon=True).start()

    def reset(self):
        with self._cv:
            self.sig, self._job, self.display, self.display_board = None, None, None, None
            self.results = {}

    def submit(self, sig, fn, label=""):
        if sig == self.sig:
            return
        if self.display_board != sig[0]:
            # planning for a different setup: don't keep showing the old solve
            self.display = {"title": "Next: planning…", "sub": label, "rows": []}
            self.display_board = sig[0]
        self.sig = sig
        if not self.threaded:
            self._run(sig, fn)
            return
        with self._cv:
            self._job = (sig, fn)
            self._cv.notify()

    def get(self, key):
        return self.results.get(key)

    def _run(self, sig, fn):
        try:
            with planner.as_background():
                res = fn()
        except Exception:  # never let a background search take the bot down
            import traceback
            traceback.print_exc()
            return
        if res is None or sig != self.sig:
            if res is not None:
                self.results[res["key"]] = res      # still usable if that state comes up
            return
        if len(self.results) > 8:
            self.results.pop(next(iter(self.results)))
        self.results[res["key"]] = res
        self.display = res["display"]

    def close(self):
        """Stop the background thread (tests; the app keeps it for its whole life)."""
        with self._cv:
            self._closed = True
            self._cv.notify()

    def _loop(self):
        while not getattr(self, "_closed", False):
            with self._cv:
                job, self._job = self._job, None
            if job is not None:
                self._run(*job)
            elif not self.warm_step():            # idle: precompute instead of waiting
                with self._cv:
                    while self._job is None and not getattr(self, "_closed", False):
                        self._cv.wait()

    # ------------------------------------------------------------ warm-up
    def is_warm(self, templates):
        """Have these templates been precomputed (for the current settings)?"""
        return self._warm_sig == planner.warm_signature() and all(id(t) in self._warm_done for t in templates)

    def focus(self, templates):
        """Precompute these next (e.g. the PC solutions of the DPC setup being built)."""
        if self._warm_sig is None:
            return
        todo = [t for t in self._warm_todo if all(t is not f for f in templates)]
        self._warm_todo = list(templates) + todo

    def warm_step(self):
        """Idle time: generate the moves of one more template the loop will need, so the
        searches on it later are cache hits. The S/Z DPC (always next after the Jigsaw
        loop) and the Jigsaw templates go first. Returns False when nothing is left.
        Stops as soon as a real job arrives (the template is resumed later)."""
        sig = planner.warm_signature()
        if sig != self._warm_sig:
            self._warm_sig, self._warm_todo, self._warm_done = sig, warm_order(), set()
        if not self._warm_todo:
            return False
        tm = self._warm_todo[0]
        with planner.as_background():
            done = planner.warm_template(tm, stop=lambda: self._job is not None or getattr(self, "_closed", False))
        if done and self._warm_todo and self._warm_todo[0] is tm:
            self._warm_todo.pop(0)
            self._warm_done.add(id(tm))
        return True


def warm_order():
    """Templates to precompute while idle, most needed first: S/Z DPC setups and their PC
    solutions (the Jigsaw loop always lands there), the Jigsaw templates, then the rest
    of the DPC loop."""
    lib = T.library()
    sz = lambda t: t.leftover in ("S", "Z")
    out = list(lib["jaws"]) + [t for t in lib["dpc"] if sz(t)]
    seen = set()
    for st in out[:]:
        for sol in T.solutions_after(st):
            if id(sol) not in seen:
                seen.add(id(sol))
                out.append(sol)
    out += [t for t in lib["wiki"] if t.family == "JIGSAW" and not t.fallback] + list(lib["jigsaw_pc"])
    out += [t for t in lib["dpc"] if not sz(t)]
    return out


def _lookahead_job(br0, board, hold, steps):
    """Play the rest of the current setup on a copy, then let a copy of the brain choose
    the perfect clear exactly as it would when it gets there."""
    br, b, h = br0._simulate(board, hold, steps)
    br.lookahead = None
    seq = br._seq()
    if not seq or b.rows[0] == 0:
        return None
    stage_from = br.stage
    key = (b.key(), br.cur_index, h, stage_from)
    br.decide(b, seq[0], h, seq[1:6])
    order_steps = []
    if br.ts is not None:
        _, _, order_steps, _ = planner.fill_template(b, br.ts, seq, h, br._future())
    elif br.plan:
        order_steps = list(br.plan_full)
    if not order_steps:
        disp = {"title": f"Next: {Brain._TITLES.get(stage_from, stage_from)}",
                "sub": f"no solve found yet with {''.join(seq[:7])} (hold {h or '-'})", "rows": []}
        return {"key": key, "ts": None, "plan": None, "display": disp, "stage": br.stage}
    order = " ".join(("hold>" if st.hold else "") + st.pl.piece for st in order_steps)
    left = len(br.ts.remaining) - len(order_steps) if br.ts is not None else 0
    if left > 0:
        order += f" + {left} not in view yet"
    d = br.display or {"title": "", "sub": "", "rows": []}
    sub = f"order: {order}"
    if stage_from == "PC8" and getattr(br, "pc_outlook", ""):
        sub += f" · then {br.pc_outlook}"
    if br.ts is not None:
        sub += f"\npriority: {T.priority_text(br.ts.tmpl, br.ts.remaining)}"
    disp = {"title": "Next · " + d["title"], "sub": sub, "rows": d["rows"]}
    return {"key": key, "ts": br.ts, "plan": list(br.plan) if br.plan else None,
            "plan_full": list(getattr(br, "plan_full", []) or []), "plan_board": getattr(br, "plan_board", None),
            "outlook": getattr(br, "pc_outlook", ""), "family": br.family, "stage": br.stage,
            "order": order, "title": d["title"], "display": disp}


class Brain:
    advisor = False        # set by the Coach: suggestions for the player, the bot doesn't play

    def __init__(self, log=print, lookahead=None):
        self.log = log
        self.bag = BagTracker()
        self.lookahead = lookahead
        self.reset()

    def reset(self):
        self.setup_steps = None
        self.stage = "OPENER"
        self.family = None
        self.ts = None          # TState of the setup being built
        self.plan = []          # queued Steps for perfect clears
        self.cur_index = 0      # index of the current piece in bag.history
        self.hold_index = None  # history index of the piece in hold
        self.placed = set()     # history indices of every piece placed so far
        self.stats = Counter()
        self.built = Counter()  # template name -> times finished (trains model.SetupPrior)
        self.display = None     # what the overlay draws: the setup / solution being built
        self.next_step = None   # the placement just decided (outlined on the diagram)
        self._pc_display_for = None

    def clone(self):
        """Independent copy, used to plan the next piece before this one has locked."""
        b = Brain.__new__(Brain)
        b.__dict__.update(self.__dict__)
        b._real_log = getattr(self, "_real_log", self.log)
        b._buffer = []
        b.log = b._buffer.append              # held back until this copy is adopted
        b.bag = BagTracker()
        b.bag.history, b.bag.offset = list(self.bag.history), self.bag.offset
        b.ts = self.ts.copy() if self.ts is not None else None
        b.plan = list(self.plan)
        b.placed = set(self.placed)
        b.stats = Counter(self.stats)
        b.built = Counter(self.built)
        if hasattr(self, "plan_full"):
            b.plan_full = list(self.plan_full)
        return b

    def adopt(self):
        """This copy becomes the real brain: release its held-back log lines."""
        real = getattr(self, "_real_log", None)
        if real is not None:
            for m in getattr(self, "_buffer", []):
                real(m)
            self.log, self._buffer = real, []
        return self

    # ------------------------------------------------------------ helpers
    def _seq(self):
        return self.bag.known(self.cur_index)

    def _future(self):
        """Pieces still to come after the visible ones (order unknown): the rest of this
        bag plus the next bag (a setup like Jaws needs pieces of the next bag too)."""
        f = self.bag.future(self.cur_index)
        return None if f is None else list(f) + list(core.PIECES)

    def _set_stage(self, stage, why=""):
        if stage != self.stage:
            self.log(f"[stage] {self.stage} -> {stage} {why}".rstrip())
            self.free_note = ""
        self.stage = stage

    def _unknown_chunk(self, seq):
        """Types still to come in the current bag after `seq` (order unknown), or None."""
        if self.bag.offset is None:
            return None
        ext = self.bag.history[: self.cur_index] + seq
        pos = (len(ext) - self.bag.offset) % 7
        if pos == 0:
            return []
        return sorted(ALL - set(ext[len(ext) - pos:]))

    def _chance(self, ts, board, hold):
        """(probability the setup completes, steps).

        1.0 when the visible pieces already complete it. Otherwise every order of the
        pieces not seen yet (rest of this 7-bag, then the next bags) is checked against
        the setup's piece dependencies with one hold slot; the chance is the share of
        orders that work. A setup the visible pieces can never finish scores 0."""
        seq, fut = self._seq(), self._future()
        complete, viable, steps, _ = planner.fill_template(board, ts, seq, hold, fut)
        if complete:
            return 1.0, steps
        if not steps or not viable:
            return 0.0, steps
        # every piece the setup needs is already visible (it uses the next N pieces, plus
        # at most one left in hold): if the search can't finish it, nothing later can
        if len(seq) + (1 if hold else 0) >= len(ts.remaining) + 1:
            return 0.0, steps
        # orders that break a "must wait for a line clear" dependency are impossible
        p_dep = self._order_chance(ts, seq, hold)
        if p_dep == 0:
            return 0.0, steps
        # exact check by actually placing every order of the few unseen bag pieces
        chunk = self._unknown_chunk(seq)
        if not chunk or len(chunk) > 4:
            return min(0.5, p_dep), steps
        perms = set(permutations(chunk))       # duplicates in the chunk give equal orders
        ok, fail = 0, set()
        for perm in perms:
            ok += planner.can_fill(board, ts, seq + list(perm), hold, fail)
        return min(ok / len(perms), p_dep), steps

    def _order_chance(self, ts, seq, hold, samples=48):
        import random
        hard, _ = T.dependencies(ts.tmpl)
        need = len(ts.remaining) + 2
        chunk = self._unknown_chunk(seq)
        if chunk is None:
            return 0.5                      # bag position unknown: no basis for a number
        rng = random.Random(_stable_seed("".join(seq), hold or "-", ts.tmpl.name))
        ok = 0
        for _ in range(samples):
            tail = list(chunk)
            rng.shuffle(tail)
            while len(seq) + len(tail) < need + 7:
                bag = list(core.PIECES)
                rng.shuffle(bag)
                tail += bag
            if planner.order_feasible(ts.tmpl, ts.remaining, hard, seq + tail, hold):
                ok += 1
        return ok / samples

    def _select(self, cands, board, hold, min_p=0.0):
        """Highest-priority setup family that can be built; within that family, among the
        builds that are certain to finish, the one needing the fewest soft-drop tucks."""
        best = None
        certain_family = None
        for prio, tm in enumerate(cands):
            if certain_family is not None and tm.family != certain_family:
                break
            ts = T.TState.fresh_on(tm, board)
            if ts is None:
                continue
            p, steps = self._chance(ts, board, hold)
            if p <= min_p or not steps:
                continue
            # four.lol layouts first (O next to the I, not the "alternate O" spot on top
            # of the L, which has to wait for the L); the wiki's "compromise" setups only
            # when every other setup fails
            preferred = 0 if tm.fallback else 1
            # then the build whose dependencies fit the order the pieces arrive in (e.g.
            # with the I before the O, not MS2 setup A with its I on top of the O), then
            # the fewest soft-drop tucks, then the fewest holds
            certain = p >= 1.0
            conflicts = T.order_conflicts(tm, ts.remaining, ([hold] if hold else []) + self._seq())
            holds = sum(1 for st in steps if st.hold) if certain else 0
            score = (p, preferred, tm.pc_rate or 0.0, -conflicts, -planner.tucks(steps) if certain else 0,
                     -holds, -prio)
            if best is None or score > best[0]:
                best = (score, ts, steps)
            if p >= 1.0 and certain_family is None:
                certain_family = tm.family
        return best

    def _select_opener(self, board, hold, min_p=0.0):
        """Opener from the families switched on in the Openers window: the first one in the
        user's priority order that is certain to be built with these pieces.
        None certain: the one with the best chance of a perfect clear = chance to build it
        x the published PC chance of what follows (templates.PC_RATE); failsafe: the
        switched-off openers may be used too - not by the advisor when only one opener is
        switched on: the player builds that one (user's choice, 2026-10-18; when the bot
        plays, the failsafe stays: forcing Jaws on every bag cut ALL PC runs of 10+ PCs
        from 17 to 9 of 28 games). Last resort: a DPC build from the empty field."""
        order = opener_priority()
        single = self.advisor and len(order) == 1
        enabled = set(order)
        fams = {}

        def consider(families):
            for fam in families:
                if fam == "JAWS":
                    best = self._select_jaws(board, hold, min_p, force=single)
                else:
                    best = self._select(T.openers([fam]), board, hold, min_p)
                if best:
                    fams[fam] = best

        def rank(fam):
            sc = fams[fam][0]
            return (sc[0] * T.PC_RATE[fam], sc[1:], -T.FAMILY_PRIORITY.index(fam))

        consider(order)
        mine = list(fams)
        pool, why = mine, ""
        # Jaws' chance is a sampled estimate (12 futures): 0.9 counts as certain
        sure = lambda f: fams[f][0][0] >= (0.9 if f == "JAWS" else 1.0)
        first = next((f for f in order if f in fams and sure(f)), None)
        if first is not None:
            n = order.index(first) + 1
            self.log(f"[opener] {T.FAMILY_NAMES[first]}: build {fams[first][0][0]:.0%} x PC "
                     f"{T.PC_RATE[first]:.1%} (priority {n} of {len(order)})")
            return fams[first]
        if not any(sure(f) for f in mine) and not single:
            # failsafe: only now look at the openers that are switched off
            # (ALL PC: only Jigsaw - its build leads to a 4-line 1st PC, or a sure 8-line one)
            consider([f for f in T.FAMILY_PRIORITY if f not in enabled and (not all_pc() or f == "JIGSAW")])
            pool = list(fams)
            if set(pool) != set(mine):
                why = " - failsafe: none of the selected openers can be built with this bag"
        if pool:
            fam = max(pool, key=rank)
            p = fams[fam][0][0]
            self.log(f"[opener] {T.FAMILY_NAMES[fam]}: build {p:.0%} x PC {T.PC_RATE[fam]:.1%}{why}")
            return fams[fam]
        # last resort: a DPC build from the empty field - only at a real DPC spot (one piece
        # of the bag left over) and only setups for that extra piece
        extra, _ = self.extra_piece()
        return self._select(T.dpc(extra), board, hold, min_p) if extra else None

    # ------------------------------------------------------------ Jaws
    JAWS_FUTURES = 12

    def _jaws_futures(self, need):
        """Sampled piece orders (hold excluded) long enough for `need` placements: the visible
        queue, every order of the rest of this bag (sampled if many), then random next bags."""
        import random
        seq = self._seq()
        chunk = self._unknown_chunk(seq)
        rng = random.Random(_stable_seed("".join(seq), "".join(chunk or ())))
        out = []
        n = self.JAWS_FUTURES if not _hurry() else 4
        perms = list(set(permutations(chunk))) if chunk and len(chunk) <= 4 else None
        for k in range(n):
            tail = list(perms[k % len(perms)]) if perms else (rng.sample(chunk, len(chunk)) if chunk else [])
            f = seq + tail
            while len(f) < need + 1:
                bag = list(core.PIECES)
                rng.shuffle(bag)
                f += bag
            out.append(f)
        return out

    def _jaws_counts(self, states, hold, board):
        """For each Jaws template state: in how many sampled futures it can really be
        finished (moves, tucks and spins included), and the share of futures where at
        least one of them can. Templates that work more often are tried first and each
        future stops at its first success, so this stays cheap."""
        need = max(len(ts.remaining) for ts in states)
        futures = self._jaws_futures(need)
        counts = [0] * len(states)
        union = 0
        for f in futures:
            order = sorted(range(len(states)), key=lambda i: -counts[i])
            for i in order:
                if planner.can_fill(board, states[i].copy(), f, hold, node_limit=2500):
                    counts[i] += 1
                    union += 1
                    break
        return counts, union / len(futures)

    def _select_jaws(self, board, hold, min_p=0.0, force=False):
        """Jaws as a family: 100% because SOME of its 22 solutions fits whatever bag 2 brings.
        Its chance = share of sampled futures where at least one solution can be built;
        the template to start = the one that works in the most futures (then the best
        2nd PC chance for the pieces it leaves). `force` (Jaws is the only opener on): also
        bags that can't build I L S Z without a piece going into a solve first."""
        # Jaws is only available at a fresh bag with an empty hold: a carried piece or a
        # half-used bag forces pieces into solve spots before the bag shows which solve
        # works (in simulation 0 of 4 clean starts failed, 14 of 24 other starts did)
        if hold is not None or self.unplaced_in_open_bag() not in (0, 7):
            return None
        if _hurry() and (self.lookahead is None or not self.lookahead.is_warm(T.openers(["JAWS"]))):
            # high gravity and Jaws not precomputed yet: choosing it would take ~1 s here
            return None
        sides = self._jaws_build_sides(hold) or ({False, True} if force else None)
        if not sides:
            return None                     # this bag can't build I L S Z without committing
        states = [ts for ts in (T.TState.fresh_on(t, board) for t in T.openers(["JAWS"]))
                  if ts is not None and ts.tmpl.mirrored in sides]
        if not states:
            return None
        counts, p = self._jaws_counts(states, hold, board)
        if p <= min_p:
            return None
        order = sorted(range(len(states)), key=lambda i: (-counts[i], -(states[i].tmpl.pc_rate or 0)))
        for i in order:
            ts = states[i]
            complete, viable, steps, _ = planner.fill_template(board, ts, self._seq(), hold, self._future())
            if steps and (complete or viable):
                return ((p, 1, ts.tmpl.pc_rate or 0.0, 0, 0, 0, 0), ts, steps)
        return None

    def _jaws_build_sides(self, hold):
        """Which Jaws orientations (False = I L S Z on the left, True = mirrored) this bag can
        build bottom-up while every other piece waits in hold (one at a time) - so no piece
        has to go into a solve before the queue shows which solve works (8.7% of bags).
        ALL PC (the user's choice, 2026-10-18): tucks allowed, and one piece may go straight
        to its spot in a solve whose other pieces under it are build pieces (57% of bags;
        in simulation about 1 such start in 7 missed its PC)."""
        seq = self._seq()[:7]
        loose = all_pc()
        out = set()
        for mirrored in (False, True):
            tm = [x for x in T.openers(["JAWS"]) if x.mirrored == mirrored]
            t = tm[0]
            hard, soft = T.dependencies(t)
            build = {sid: t.slots[sid].ptype for sid in t.slots if sid.startswith("b")}
            need = {sid: (hard[sid] if loose else hard[sid] | soft[sid]) & set(build) for sid in build}
            early = set()               # (type, build slots it sits on) of solve pieces that can go first
            if loose:
                for x in tm:
                    xh, xs = T.dependencies(x)
                    for sid, sl in x.slots.items():
                        if not sid.startswith("b") and not ((xh[sid] | xs[sid]) - set(build)):
                            early.add((sl.ptype, frozenset(xh[sid] | xs[sid])))
            memo = {}

            def ok(i, h, placed, spent=False):
                if len(placed) == len(build):
                    return True
                key = (i, h, placed, spent)
                if key in memo:
                    return memo[key]
                r = False
                if i < len(seq):
                    def put(p, ni, nh):
                        for sid, bt in build.items():
                            if bt == p and sid not in placed and need[sid] <= placed:
                                if ok(ni, nh, placed | {sid}, spent):
                                    return True
                        return not spent and p not in build.values() and any(
                            et == p and on <= placed for et, on in early) and ok(ni, nh, placed, True)
                    cur = seq[i]
                    r = put(cur, i + 1, h)
                    if not r and h is not None and h != cur:
                        r = put(h, i + 1, cur)                     # place the held piece, hold this one
                    if not r and h is None and i + 1 < len(seq):
                        r = put(seq[i + 1], i + 2, cur)            # hold this one, place the next
                memo[key] = r
                return r

            if ok(0, hold, frozenset()):
                out.add(mirrored)
        return out

    def _jaws_step(self, board, hold):
        """Jaws: commit to a solve the bag allows. While the current solve can still be
        finished with the visible pieces, keep it. Otherwise scan all 22 solves (and
        mirrors) that fit what is already placed: take one the visible pieces can finish
        (best 2nd PC pattern for the pieces it leaves); if none can be finished yet, the
        one whose plan for the visible pieces works best. Returns a Step or None."""
        seq, fut = self._seq(), self._future()
        cur = self.ts
        lim = 600 if _hurry() else 3000
        if planner.can_fill(board, cur.copy(), seq, hold, node_limit=lim):
            steps = planner.fill_template(board, cur, seq, hold, fut)[2]
            return steps[0] if steps else None
        sibs = [cur] + [ts for ts in (_rebase(t, cur, board) for t in T.openers(["JAWS"]) if t is not cur.tmpl)
                        if ts is not None]
        done = [ts for ts in sibs if planner.can_fill(board, ts.copy(), seq, hold, node_limit=lim)]
        if done:
            ts = max(done, key=lambda t: (t.tmpl.pc_rate or 0.0, t is cur))
            self.log(f"[jaws] committing to {ts.tmpl.label}: these pieces finish it "
                     f"(2nd PC {ts.tmpl.pc_rate or 0:.0%} for the pieces it leaves)")
        else:
            # no solve can be finished with what's visible yet: don't commit. Place the
            # I L S Z build (shared by every solve) or hold; a piece that must go in anyway
            # goes where, over sampled next bags, a solve can most often still be finished.
            cands = {}
            for p, used_hold, ni, nh in planner._choices(seq, 0, hold):
                gen = planner.movegen(board, p)
                for t in sibs:
                    hard, _ = T.dependencies(t.tmpl)
                    for sid in t.remaining:
                        if t.tmpl.slots[sid].ptype != p or hard[sid] & t.remaining:
                            continue
                        pl = gen.get(t.slot_cells(sid))
                        if pl is None:
                            continue
                        c = cands.setdefault((used_hold, pl.cells), dict(pl=pl, hold=used_hold, ni=ni, nh=nh,
                                                                        build=False, opts=[]))
                        c["build"] |= sid.startswith("b")
                        c["opts"].append((t, sid))
            if not cands:
                return None
            build = [c for c in cands.values() if c["build"]]
            pool = build if (JAWS_BUILD_FIRST and build) else list(cands.values())
            # high gravity, bot thread: no time to sample futures - most solves still fitting
            futures = [] if len(pool) == 1 or _hurry() else self._jaws_futures(max(len(t.remaining) for t in sibs))[:8]
            best = None
            for c in pool:
                nb = board.copy()
                cleared = nb.place_cells(c["pl"].cells)
                states = []
                for t, sid in c["opts"]:
                    nts = t.copy()
                    nts.apply(sid, cleared)
                    states.append(nts)
                ok = sum(1 for f in futures if any(
                    planner.can_fill(nb, nts.copy(), f[c["ni"]:], c["nh"], node_limit=1200) for nts in states))
                alive = sum(1 for o in sibs if any(o.tmpl.slots[x].ptype == c["pl"].piece
                                                   and o.slot_cells(x) == c["pl"].cells for x in o.remaining))
                t, sid = c["opts"][0]
                key = (ok, c["build"], alive, not c["hold"], t is cur)
                if best is None or key > best[0]:
                    best = (key, t, planner.Step(c["hold"], c["pl"], sid))
            if best is None:
                return None
            self.ts = best[1]
            return best[2]
        self.ts = ts
        steps = planner.fill_template(board, ts, seq, hold, fut)[2]
        return steps[0] if steps else None

    def _bag_leftover(self):
        """Types of the pieces of the oldest open bag that are still to be placed (the 4
        pieces of bag 2 after a Jaws 1st PC). None if the bag position is unknown."""
        ob = self._open_bag()
        if ob is None:
            return None
        _, _, unplaced, unseen = ob
        h = self.bag.history
        return sorted([h[i] for i in unplaced] + list(unseen))

    def _candidates(self):
        if self.stage == "OPENER":
            return T.openers(enabled_openers()) + T.dpc()
        if self.stage == "BAG2":
            return T.second_bag(self.family)
        if self.stage == "DPC":
            return T.dpc()
        if self.stage == "PCDPC":
            return T.dpc_solutions()
        return []

    def _open_bag(self):
        """Oldest bag that still has unused pieces: (bag_no, start, unplaced_known, unseen_types)."""
        off, h = self.bag.offset, self.bag.history
        if off is None:
            return None
        start, k = off, 0
        while start < len(h):
            end = start + 7
            known = range(start, min(end, len(h)))
            unplaced = [i for i in known if i not in self.placed]
            unseen = sorted(ALL - {h[i] for i in known}) if end > len(h) else []
            if unplaced or unseen:
                return k, start, unplaced, unseen
            start, k = end, k + 1
        return k, start, [], sorted(ALL)

    def unplaced_in_open_bag(self):
        """Pieces of the oldest open bag not placed yet (0 = exactly at a bag boundary)."""
        ob = self._open_bag()
        if ob is None:
            return -1
        _, start, unplaced, unseen = ob
        if start >= len(self.bag.history) and len(unseen) == 7:
            return 0
        return len(unplaced) + len(unseen)

    def extra_piece(self, avail=None):
        """The DPC "extra" piece: the one piece of an earlier bag that was never placed.

        Every placement is recorded by its index in the piece stream, so per 7-bag we
        know exactly which pieces were used. After an 8-line PC (20 pieces = 2 bags +
        6) the third bag has exactly one unplaced piece - that is the extra one, whether
        it sits in hold, is in the queue, or has not even appeared yet (then its type is
        the one missing from the bag). Returns (type, explanation)."""
        h = self.bag.history
        ob = self._open_bag()
        if ob is not None:
            k, start, unplaced, unseen = ob
            if start >= len(h) and len(unseen) == 7:
                return None, "every bag fully used"
            if len(unplaced) + len(unseen) == 1:
                used = "".join(h[x] for x in range(start, min(start + 7, len(h))) if x in self.placed)
                if unplaced:
                    i = unplaced[0]
                    where = "in hold" if i == self.hold_index else (
                        "current piece" if i == self.cur_index else f"queue slot {i - self.cur_index}")
                    return h[i], f"bag {k + 1}: placed {used}, {h[i]} never placed ({where})"
                return unseen[0], f"bag {k + 1}: placed {used}, {unseen[0]} not spawned yet"
            return None, f"bag {k + 1} has {len(unplaced) + len(unseen)} unplaced pieces - not a DPC spot"
        if avail:
            dup = [p for p, n in Counter(avail[:8]).items() if n >= 2]
            if len(dup) == 1:
                return dup[0], "bag position unknown; guessed from the duplicate in the next pieces"
        return None, "bag position unknown"

    def _select_dpc(self, board, hold):
        """Pick a DPC setup by checking each one's order criteria against the
        upcoming pieces (hold first, then current + next queue), four.lol order."""
        avail = ([hold] if hold else []) + self._seq()
        extra, why = self.extra_piece(avail)
        self.log(f"[dpc] extra piece: {extra or '?'} ({why})")
        self.extra = extra
        groups = {}
        for t in T.dpc(extra):
            order = list(avail)
            if t.leftover in order:
                order.remove(t.leftover)          # the rest is the next bag, in order
            ok, unknown, text = T.criteria_status(t, order)
            groups.setdefault(t.leftover, []).append((t, ok, unknown, text))
        lines = []
        for lo, items in groups.items():
            seen = set()
            parts = []
            for t, ok, unknown, text in items:
                if t.label in seen:
                    continue
                seen.add(t.label)
                parts.append(f"{t.label}: {text}")
            lines.append(f"extra {lo} | next {''.join(avail[:8])} | " + " | ".join(parts))
        for ln in lines:
            self.log(f"[dpc] {ln}")
        ranked = [t for items in groups.values() for t, ok, unk, _ in items if ok and not unk]
        ranked += [t for items in groups.values() for t, ok, unk, _ in items if ok and unk]
        best = self._select(ranked, board, hold)
        if best is None:
            rest = [t for items in groups.values() for t, ok, _, _ in items if not ok]
            best = self._select(rest, board, hold)
            if best:
                self.log("[dpc] no setup meets its order criteria; using one the search can still build")
        if best:
            self.log(f"[dpc] -> {best[1].tmpl.label} ({best[1].tmpl.name})")
        return best

    def _select_pc_setup(self, board, hold):
        """four.lol setup for the next PC of the 4-line loop. Ranked by how many of the
        pieces left of the last bag it uses (four.lol draws each setup for those), then
        build chance x published PC chance. Setups may need up to 2 pieces not in view
        yet (the 5th PC's are 5-7 pieces); candidates are tried best-first and the search
        stops once no later one can beat the best found."""
        n = self.pc_n = self.pc_no()
        seq = self._seq()
        have = Counter(([hold] if hold else []) + seq)
        left = self._bag_leftover()
        lc = Counter(left or ())
        pool = T.pc2_setups(n)
        cands = []
        for t in pool:
            need = Counter(t.types())
            if sum((need - have).values()) <= 2:
                cands.append((sum((need & lc).values()), t.pc_rate or 0.0, t))
        cands.sort(key=lambda c: (-c[0], -c[1]))
        if _hurry():
            cands = cands[:6]               # high gravity: the piece is already falling
        self.log(f"[pc{n or ''}] left of this bag: {''.join(left) if left else '?'}; "
                 f"{len(cands)} of {len(pool)} {T.ORDINAL.get(n, '')} PC setups fit the pieces in view")
        best = None
        for overlap, rate, t in cands:
            if best is not None and (overlap, rate) <= best[0]:
                break                       # p <= 1: nothing further down can win
            b = self._select([t], board, hold)
            if b and (best is None or (overlap, b[0][0] * rate) > best[0]):
                best = ((overlap, b[0][0] * rate), b)
        return best[1] if best else None

    def _select_pc8(self, board, hold):
        """8-line PC after the 2nd bag, from the family's known solutions (four.lol SD-PC,
        Jigsaw 3rd bag). Among those the next pieces can build, prefer the one leaving the
        best DPC extra piece and needing the fewest tucks."""
        best = None
        for prio, tm in enumerate(T.pc8_solutions(self.family) or ()):
            ts = T.TState.fresh_on(tm, board)
            if ts is None:
                continue
            p, steps = self._chance(ts, board, hold)
            if p < 1 or not steps:
                continue
            br, b, h = self._simulate(board, hold, steps)
            if b.rows[0] != 0:
                continue
            sc, text = self._dpc_outlook(br, h)
            spins = sum(1 for st in steps if st.pl.spin == "full")
            key = (sc, -planner.tucks(steps), spins, -prio)
            if best is None or key > best[0]:
                best = (key, ts, steps, text)
        if best is None:
            return None
        self.pc_outlook = best[3]
        self.log(f"[pc] {best[1].tmpl.label} (four.lol) fits; then {best[3]}")
        return ((1.0, 0), best[1], best[2])

    def _select_dpc_pc(self, board, hold, tmpls=None):
        """Choose which of four.lol's PC solutions (default: the DPC ones) the next pieces
        can build."""
        seq = self._seq()
        marks, best = [], None
        for prio, tm in enumerate(T.dpc_solutions() if tmpls is None else tmpls):
            ts = T.TState.fresh_on(tm, board)
            if ts is None:
                continue
            p, steps = self._chance(ts, board, hold)
            marks.append(tm.name[tm.name.index("-") + 1:] + ("✓" if p >= 1 else "?" if p > 0 else "✗"))
            if steps and p > 0:
                spins = sum(1 for st in steps if st.slot and ts.tmpl.slots[st.slot].spin and st.pl.spin == "full")
                score = (p, spins, -prio)
                if best is None or score > best[0]:
                    best = (score, ts, steps)
        if marks:
            self.log(f"[{'dpc' if tmpls is None else 'pc'}] PC solutions for "
                     f"{''.join(([hold] if hold else []) + seq[:7])}: {' '.join(marks)}")
        return best

    # ------------------------------------------------------------ main API
    def decide(self, board, current, hold, queue):
        """Return the Step for the current piece (None if nothing is possible)."""
        self.setup_steps = None
        with planner.foreground_busy():
            step = self._decide(board, current, hold, queue)
        self.next_step = step
        self._refresh_display()
        self._maybe_lookahead(board, hold)
        return step

    def pc_check_due(self, board, hold):
        """Does decide() look for a perfect clear in view before the setup? While a Jigsaw
        or four.lol 2nd-7th PC setup is built or chosen (the T-spin loops keep their TSD),
        once the pieces in view are enough for one within 4 lines (the controller then
        plans after the hard drop: the search may take a moment)."""
        fam = self.ts.tmpl.family if self.ts is not None else self.family
        building = (self.stage in ("OPENER", "BAG2") and fam == "JIGSAW") or self.stage == "PC2" or (
            self.stage == "PC8" and self.family == "PC2")
        if not building or self.plan or board.rows[0] == 0 or (
                self.ts is not None and self.ts.tmpl.stage.endswith("_pc")):
            return False
        avail = len(self._seq()) + (1 if hold else 0)
        return any((10 * h - board.count()) // 4 <= avail for h in planner.pc_heights(board, 4))

    # ------------------------------------------------------------ look-ahead
    def _maybe_lookahead(self, board, hold):
        """During a T-spin setup, hand the perfect clear that follows it to the look-ahead."""
        if self.lookahead is None or self.ts is None or not self.setup_steps:
            return
        if self.ts.tmpl.stage not in ("bag2", "dpc", "pc2"):
            return
        if self.ts.tmpl.stage == "dpc" and len(self.ts.remaining) > DPC_LOOKAHEAD_SLOTS:
            # place the next pieces first: by the last few the queue shows more of what
            # the PC will get, and nothing competes with the piece being placed now
            return
        br, b, h = self._simulate(board, hold, self.setup_steps)
        if b.rows[0] == 0:
            return
        sig = (b.key(), br.cur_index, h, tuple(br._seq()[:8]))
        br0, board0, steps = self.clone(), board.copy(), list(self.setup_steps)
        self.lookahead.submit(sig, lambda: _lookahead_job(br0, board0, hold, steps),
                              f"after {self.ts.tmpl.label or self.ts.tmpl.name}, with {''.join(br._seq()[:7])}")

    def _adopt_lookahead(self, board, hold):
        if self.lookahead is None or self.ts is not None or self.plan:
            return
        la = self.lookahead.get((board.key(), self.cur_index, hold, self.stage))
        if not la or (la["ts"] is None and not la["plan"]):
            return
        if la["ts"] is not None:
            ts = la["ts"].copy()
            done, _, _, _ = planner.fill_template(board, ts, self._seq(), hold, self._future())
            if not done and self._order_chance(ts, self._seq(), hold) < 1.0:
                self.log(f"[lookahead] {la['title']} is no longer certain with these pieces - choosing again")
                return
            self.ts = ts
        else:
            self.plan = list(la["plan"])
            self.plan_full, self.plan_board = list(la["plan_full"]), la["plan_board"].copy()
        self.pc_outlook = la["outlook"]
        if la["family"]:
            self.family = la["family"]
        if la["stage"] != self.stage:
            self._set_stage(la["stage"])
        self.log(f"[lookahead] planned ahead: {la['title']} ({la['order']})")

    def _decide(self, board, current, hold, queue):
        self.bag.update(self.cur_index, current, queue)
        self._adopt_lookahead(board, hold)
        seq = self._seq()

        self.empty_field_stage(board)

        # A perfect clear the pieces in view can finish comes before building (or choosing)
        # any setup - the PC is the priority, not setting up the next one
        if self.pc_check_due(board, hold):
            sol = planner.find_pc(board, seq, hold, max_h=4, time_limit=0.05 if _hurry() else 0.25)
            if sol:
                sol = self._best_pc_ending(board, seq, hold, sol)
                if self.ts is not None:
                    self.log(f"[pc] the pieces in view finish a perfect clear - leaving {self.ts.tmpl.name}")
                self.ts = None
                self.plan, self.plan_full, self.plan_board = sol, list(sol), board.copy()
                self._set_stage("PC", "(perfect clear in view)")
                self.log(f"[pc] found {len(sol)}-piece perfect clear")
                return sol[0]

        # Setup stages ------------------------------------------------------------
        choosing = self.ts is None and not self.plan and (
            self.stage in ("OPENER", "BAG2", "DPC", "PCDPC", "PC2")
            or (self.stage == "PC8" and T.pc8_solutions(self.family) and board.rows[0] != 0))
        if choosing:
            if self.stage == "OPENER" and board.rows[0] == 0 and self.bag.offset is not None:
                n = self.unplaced_in_open_bag()
                if n > 1:
                    self.log(f"[setup] {n} pieces of this bag are still to come - only starting a "
                             "setup that is certain to finish")
            if self.stage == "DPC":
                best = self._select_dpc(board, hold)
            elif self.stage == "PCDPC":
                best = self._select_dpc_pc(board, hold)
            elif self.stage == "PC8" and self.family == "PC2":
                # four.lol's solutions on this setup: certain ones first, else the likeliest
                best = self._select_dpc_pc(board, hold, T.pc2_solutions(board))
            elif self.stage == "PC8":
                best = self._select_pc8(board, hold)
            elif self.stage == "PC2":
                best = self._select_pc_setup(board, hold)
            elif self.stage == "OPENER":
                mid_bag = self.bag.offset is not None and self.unplaced_in_open_bag() > 1
                best = self._select_opener(board, hold, min_p=0.99 if mid_bag else 0.0)
            else:
                best = self._select(self._candidates(), board, hold)
            if best is None:
                if self.stage not in ("PCDPC", "PC8"):
                    self._set_stage("FREE", "(no setup fits this bag)")
                else:
                    self.log("[pc] no four.lol solution fits these pieces; using the PC solver")
            else:
                p = best[0][0]
                self.ts = best[1]
                self.family = self.ts.tmpl.family
                if self.ts.tmpl.stage == "dpc" and self.lookahead is not None:
                    # the PC solutions that follow this DPC setup: precompute while building
                    self.lookahead.focus(T.solutions_after(self.ts.tmpl))
                if self.family == "DPC" and self.ts.tmpl.stage == "dpc":
                    self._set_stage("DPC")
                self.log(f"[setup] building {self.ts.tmpl.name} ({p:.0%}) - {self.ts.tmpl.note}")
        if self.ts is not None and self.ts.tmpl.family == "JAWS" and self.ts.matches(board):
            step = self._jaws_step(board, hold)
            if step is not None:
                return step
        if self.ts is not None:
            if not self.ts.matches(board):
                self.log(f"[warn] board no longer matches {self.ts.tmpl.name}")
                self.ts = None
                self._set_stage("FREE", "(board mismatch)")
            else:
                complete, viable, steps, _ = planner.fill_template(board, self.ts, seq, hold, self._future())
                if steps and (complete or viable):
                    if complete:
                        self.setup_steps = steps
                    return steps[0]
                alt = self._reselect(board, hold)
                if alt:
                    return alt
                self.log(f"[warn] {self.ts.tmpl.name} cannot be finished with {''.join(seq)} hold={hold}")
                failed_pc = self.ts.tmpl.stage == "dpc_pc"
                self.ts = None
                if not failed_pc:
                    self._set_stage("FREE", "(setup failed)")

        # Perfect clears ----------------------------------------------------------
        if board.rows[0] != 0:
            if self.plan and self._plan_valid(board, seq, hold):
                return self.plan[0]
            self.plan = []
            if self.stage == "FREE" and board.height() > 6:
                return planner.heuristic_move(board, seq, hold)
            max_h = 8 if self.stage == "PC8" and self.family != "PC2" else 4
            budget = 2.5 if self.stage != "FREE" else 0.3
            if planner.SETTINGS["safe"] and not planner.background():
                # high gravity: the piece is already on the stack and locks after ~0.5 s -
                # a long search would let it lock where it fell (the look-ahead thread
                # keeps the long budget)
                budget = 0.3 if self.stage != "FREE" else 0.1
            sol = planner.find_pc(board, seq, hold, max_h=max_h, time_limit=budget)
            if sol and self.stage in ("PC8", "FREE", "PC"):
                sol = self._best_pc_ending(board, seq, hold, sol)
            if sol:
                self.plan = sol
                self.plan_full, self.plan_board = list(sol), board.copy()
                self.log(f"[pc] found {len(sol)}-piece perfect clear")
                return sol[0]
            if self.stage != "FREE":
                self._set_stage("FREE", "(no perfect clear found)")
        hs = planner.pc_heights(board, 4)
        return planner.heuristic_move(board, seq, hold, pc_h=hs[-1] if hs else None)

    # ------------------------------------------------------------ PC endings
    def _simulate(self, board, hold, steps):
        """Copy of this brain after playing `steps` (quietly). Returns (brain, board, hold)."""
        br = self.clone()
        br.lookahead = None                    # simulations never touch the real look-ahead
        b = board.copy()
        h = hold
        for st in steps:
            hold_was_empty = h is None
            if st.hold:
                h = br.bag.history[br.cur_index] if br.cur_index < len(br.bag.history) else "?"
            cl = b.place_cells(st.pl.cells)
            br.plan = []
            br.on_lock(st, hold_was_empty, cl, b)
        return br, b, h

    def _dpc_outlook(self, br, hold):
        """How good is the DPC that follows if the bot is in state `br` (field empty)?
        Returns (score, text)."""
        extra, _ = br.extra_piece()
        n = br.unplaced_in_open_bag()
        if n == 0:
            return (1, 0.5, ""), "fresh bag -> opener next"
        if n > 0 and (extra is None or all_pc()):
            # four.lol's setup for the next PC of the loop: with the hold free, a piece no
            # setup uses can wait there (with it taken, often no setup can be built)
            return (1, 0.4 if hold is None else 0.1, ""), \
                f"{T.ORDINAL[PC_NO[n % 7]]} PC setup next, hold {hold or 'free'}"
        if extra is None:
            return (0, 0.0, ""), f"{n} pieces left in the bag (no opener/DPC fits)"
        seq = br._seq()
        # PCs that end alike (same extra piece, hold and queue) have the same outlook:
        # score each of those once
        fut = br._future()
        key = (extra, hold, tuple(seq), tuple(fut) if fut is not None else None,
               planner.SETTINGS["safe"], planner.SETTINGS["handling"].signature(),
               planner._air_ms(core.Board()))
        hit = _OUTLOOK.get(key)
        if hit is not None:
            return hit
        res = self._dpc_outlook_uncached(br, hold, extra, seq)
        if len(_OUTLOOK) > 256:
            _OUTLOOK.clear()
        _OUTLOOK[key] = res
        return res

    def _dpc_outlook_uncached(self, br, hold, extra, seq):
        avail = ([hold] if hold else []) + seq
        best = ((0, 0.0, ""), f"extra {extra}: no DPC fits")
        for t in T.dpc(extra):
            order = list(avail)
            if t.leftover in order:
                order.remove(t.leftover)
            ok, unknown, _ = T.criteria_status(t, order)
            if not ok:
                continue
            ts = T.TState.fresh_on(t, core.Board())
            p, steps = br._chance(ts, core.Board(), hold)
            if steps and p > 0:
                sc = (2 if p >= 1 else 1, p, "")
                if sc > best[0]:
                    best = (sc, f"extra {extra} -> DPC {t.label} ({p:.0%})")
        return best

    def _best_pc_ending(self, board, seq, hold, first):
        """The user's idea: while doing the PC, choose WHICH piece is left over so the
        next DPC case fits the upcoming pieces. Collects PCs that end differently and
        keeps the one with the best DPC outlook."""
        h_lines = (board.count() + 4 * len(first)) // core.W
        # at high gravity the current piece waits on the ground meanwhile: keep it short
        budget = 0.08 if planner.SETTINGS["safe"] and not planner.background() else 0.5
        sols = [first] + planner.pc_solutions(board, seq, hold, h_lines, time_limit=budget, want=6)
        best = None
        for sol in sols:
            br, b, h = self._simulate(board, hold, sol)
            if b.rows[0] != 0:
                continue
            sc, text = self._dpc_outlook(br, h)
            spins = sum(1 for st in sol if st.pl.spin == "full")
            key = (sc, -planner.tucks(sol), spins, -len(sol))
            if best is None or key > best[0]:
                best = (key, sol, text)
        if best is None:
            return first
        self.pc_outlook = best[2]
        if len(sols) > 1:
            self.log(f"[pc] {len(sols)} ways to clear; picked the one that leaves: {best[2]}")
        return best[1]

    def empty_field_stage(self, board):
        """After a perfect clear the bag position says what comes next: a fresh bag -> an
        opener; one piece over -> the DPC (ALL PC: the 3rd PC); otherwise four.lol's setup
        for that PC of the 4-line loop (4 over -> 2nd PC, 1 -> 3rd, 5 -> 4th, ...)."""
        if self.stage in ("FREE", "PC8", "PCDPC", "PC") and board.rows[0] == 0 and not self.plan:
            n = self.unplaced_in_open_bag()
            if n < 0:
                nxt = "DPC" if self.stage == "PC8" else "OPENER"
            elif n % 7 == 0:
                nxt = "OPENER"
            elif n == 1 and not all_pc():
                nxt = "DPC"
            else:
                nxt = "PC2"
            self._set_stage(nxt, "(field empty)")

    def pc_no(self):
        """Which PC of the 4-line loop comes next (1-7); None if the bag position is unknown."""
        n = self.unplaced_in_open_bag()
        return None if n < 0 else PC_NO[n % 7]

    def _plan_valid(self, board, seq, hold):
        st = self.plan[0]
        if st.hold:
            piece = hold if hold is not None else (seq[1] if len(seq) > 1 else None)
        else:
            piece = seq[0]
        return st.pl.piece == piece and st.pl.cells in planner.movegen(board, piece)

    def _reselect(self, board, hold):
        """Swap to a sibling template consistent with what has been built so far."""
        cur = self.ts
        pool = sibling_pool(cur.tmpl)
        best = None
        for tm in pool:
            if tm.stage != cur.tmpl.stage or tm is cur.tmpl:
                continue
            ts = _rebase(tm, cur, board)
            if ts is None:
                continue
            p, steps = self._chance(ts, board, hold)
            if steps and p > 0 and (best is None or p > best[0]):
                best = (p, ts, steps)
        if best:
            self.log(f"[setup] switching {cur.tmpl.name} -> {best[1].tmpl.name} ({best[0]:.0%})")
            self.ts = best[1]
            return best[2][0]
        return None

    def on_lock(self, step, hold_was_empty, cleared, board):
        """Update state after `step` locked; `board` is the post-lock board."""
        i = self.cur_index
        if not step.hold:
            self.placed.add(i)
        elif hold_was_empty:
            self.placed.add(i + 1)
            self.hold_index = i
        else:
            if self.hold_index is not None:
                self.placed.add(self.hold_index)
            self.hold_index = i
        self.cur_index += 2 if (step.hold and hold_was_empty) else 1
        self.stats["pieces"] += 1
        if step.pl.spin and cleared:
            self.stats[f"tspin{len(cleared)}" + ("m" if step.pl.spin == "mini" else "")] += 1
        if cleared and board.rows[0] == 0:
            if self.lookahead is not None:     # that plan is done: show the next one when ready
                self.lookahead.display = None
                self.lookahead.display_board = None
            self.stats["pc"] += 1
            self.log(f"[pc] PERFECT CLEAR #{self.stats['pc']}")
        if self.plan and step is self.plan[0]:
            self.plan.pop(0)
        if self.ts is not None and step.slot is not None:
            self.ts.apply(step.slot, cleared)
            if not self.ts.remaining:
                done = self.ts.tmpl
                self.ts = None
                self.built[done.name] += 1
                self.log(f"[setup] finished {done.name}")
                self._set_stage({"bag1": "BAG2", "bag2": "PC8", "dpc": "PCDPC", "dpc_pc": "PCDPC",
                                 "sdpc_pc": "PC8", "pc8_pc": "PC8", "bag2_pc": "PC8",
                                 "pc1_pc": "PC2", "pc2": "PC8", "pc2_pc": "PC8"}[done.stage])
        self.next_step = None
        self._refresh_display()

    # ------------------------------------------------------------ overlay diagram
    _TITLES = {"OPENER": "Opener", "BAG2": "2nd bag", "PC8": "8-line PC", "DPC": "DPC setup",
               "PCDPC": "DPC perfect clear", "FREE": "Free play", "PC2": "PC setup", "PC": "Perfect clear"}

    def bag_status(self):
        """Pieces counter for the overlay: which pieces of the current 7-bag have spawned
        (resets every bag), and the DPC extra piece if there is one."""
        off, h = self.bag.offset, self.bag.history
        if off is None or self.cur_index >= len(h) or self.cur_index < off:
            return None
        b = (self.cur_index - off) // 7
        start = off + 7 * b
        spawned = h[start:self.cur_index + 1]
        upcoming = h[self.cur_index + 1:start + 7]
        extra = None
        if self.stage in ("DPC", "PC8"):
            extra = getattr(self, "extra", None) if self.stage == "DPC" else None
        return {"bag": b + 1, "spawned": list(spawned), "upcoming": list(upcoming),
                "missing": sorted(ALL - set(spawned) - set(upcoming)), "extra": extra}

    def _refresh_display(self):
        """Snapshot of what is being built, for the overlay (read from the UI thread)."""
        self.bag_view = self.bag_status()
        title = self._TITLES.get(self.stage, self.stage)
        if self.stage == "PC2" or (self.stage == "PC8" and self.family == "PC2"):
            title = f"{T.ORDINAL.get(getattr(self, 'pc_n', None), '')} {'PC setup' if self.stage == 'PC2' else 'PC'}".strip()
        extra = getattr(self, "extra", None)
        if self.ts is not None:
            t = self.ts.tmpl
            # Jaws is a 4-piece opener (I L S Z): until those are down, show just the build
            # (and pieces already placed); the solution on top is chosen from the queue
            jaws_build = t.family == "JAWS" and any(s.startswith("b") for s in self.ts.remaining)
            rows = []
            for row in reversed(t.grid):
                line = ""
                for tok in row:
                    if tok is None or (jaws_build and tok not in ("G", "X") and not tok.startswith("b")
                                       and tok in self.ts.remaining):
                        line += "."
                    elif tok == "G":
                        line += "G"
                    else:
                        p = "X" if tok == "X" else t.slots[tok].ptype   # DPC leftover: grey like four.lol
                        line += p if tok in self.ts.remaining else p.lower()
                rows.append(line)
            sub = t.note
            if t.family == "DPC" and t.stage == "dpc":
                sub = f"extra {t.leftover} · {t.label}: " + (" ".join(f"{a}<{b}" for a, b in t.criteria) or "any order")
            elif t.stage in ("dpc_pc", "sdpc_pc"):
                sub = f"four.lol solution · {t.note.split('(')[-1].rstrip(')')}"
                if t.stage == "sdpc_pc" and getattr(self, "pc_outlook", ""):
                    sub += f" · then {self.pc_outlook}"
            if self.ts.remaining:
                sub += f"\npriority: {T.priority_text(t, self.ts.remaining)}"
            name = t.label or t.name
            if t.family == "JAWS":
                kind = "ILJOSZ" if "ILJOSZ" in t.name else "ILOSZ" if "ILOSZ" in t.name else "ILSZ"
                if jaws_build:
                    name = f"Jaws ({_jaws_field(t, self.ts.remaining)}){' (mirrored)' if t.mirrored else ''}"
                    sub = (f"4-piece build; the 1st PC on top is picked from the queue "
                           f"(four.lol {kind} #{t.label.split('#')[-1]} fits so far)")
                    sub += f"\npriority: {T.priority_text(t, [s for s in self.ts.remaining if s.startswith('b')])}"
                else:
                    title = "1st PC"
            elif t.stage == "bag1" and t.family in T.FAMILY_NAMES:
                name = T.FAMILY_NAMES[t.family]
                if t.mirrored:
                    sub = "mirrored · " + sub
            st = self.next_step
            hint = []
            if st is not None and st.slot in self.ts.remaining:
                n = len(t.grid)
                hint = [(n - 1 - y, x) for y, row in enumerate(t.grid) for x, tok in enumerate(row) if tok == st.slot]
            self.display = {"title": f"{title}: {name}", "sub": sub, "rows": rows, "hint": hint}
        elif self.plan and getattr(self, "plan_full", None):
            rows, hint = _plan_picture(self.plan_board, self.plan_full, self.plan,
                                       self.next_step if self.next_step in self.plan else None)
            self.display = {"title": f"{title}: solver",
                            "sub": f"{len(self.plan_full)}-piece perfect clear"
                                   + (f" · then {self.pc_outlook}" if getattr(self, "pc_outlook", "") else ""),
                            "rows": rows, "hint": hint}
        elif self.stage == "FREE":
            note = getattr(self, "free_note", "")
            self.display = {"title": title, "rows": [],
                            "sub": (note + "\n" if note else "") + "keeping the stack low, looking for perfect clears"}
        elif not (self.display and self.display["rows"]):
            self.display = {"title": title, "sub": "choosing…", "rows": []}
        # otherwise keep showing the last diagram until the next one is chosen


_ILOSZ_O = frozenset({(8, 0), (9, 0), (8, 1), (9, 1)})
_ILJOSZ_J = frozenset({(5, 1), (6, 1), (7, 1), (7, 0)})


def _jaws_field(t, remaining):
    """four.lol's name for the Jaws field built so far: ILSZ, ILOSZ (an O on the far
    right) or ILJOSZ (and the J next to it); mirrored templates are checked mirrored."""
    placed = {(t.slots[s].ptype, frozenset((9 - x, y) for x, y in t.slots[s].cells) if t.mirrored
               else t.slots[s].cells) for s in t.slots if s not in remaining}
    if ("O", _ILOSZ_O) not in placed:
        return "ILSZ"
    return "ILJOSZ" if ((T.MIRROR_TYPE["J"] if t.mirrored else "J"), _ILJOSZ_J) in placed else "ILOSZ"


def _plan_picture(board, steps, remaining, nxt=None):
    """Draw a PC solution the way four.lol does: every piece in the original rows
    (pieces placed after a line clear are mapped back above/below the cleared row).
    Steps not in `remaining` are dimmed. Returns (rows, hint cells of step `nxt`)."""
    h = max(board.height(), max(max(y for _, y in st.pl.cells) for st in steps) + 1)
    grid = {(x, y): "G" for y in range(h) for x in range(10) if board.filled(x, y)}
    b = board.copy()
    rowmap = list(range(core.H))          # current row -> original row
    todo = {id(st) for st in remaining}
    nxt_cells = []
    for st in steps:
        for x, y in st.pl.cells:
            grid[(x, rowmap[y])] = st.pl.piece if id(st) in todo else st.pl.piece.lower()
            if st is nxt:
                nxt_cells.append((x, rowmap[y]))
        cleared = b.place_cells(st.pl.cells)
        if cleared:
            keep = [r for i, r in enumerate(rowmap) if i not in cleared]
            rowmap = keep + list(range(max(rowmap) + 1, max(rowmap) + 1 + len(cleared)))
    top = max([y for _, y in grid] + [0]) + 1
    rows = ["".join(grid.get((x, y), ".") for x in range(10)) for y in range(top - 1, -1, -1)]
    return rows, [(top - 1 - y, x) for x, y in nxt_cells]


def sibling_pool(tmpl):
    """Templates of the same kind as `tmpl` (a setup can turn into any of its siblings
    that contains every piece placed so far)."""
    return T.library()[{"dpc": "dpc", "dpc_pc": "dpc_pc", "sdpc_pc": "sdpc_pc",
                        "pc8_pc": "jigsaw_pc", "pc1_pc": "jaws", "pc2": "pc2",
                        "pc2_pc": "pc2_pc"}.get(tmpl.stage, "wiki")]


def _rebase(tmpl, cur_ts, board):
    """Start `tmpl` mid-build if every piece placed so far is one of its slots (same type,
    same cells). Line clears are fine: whichever order the pieces went in, the rows that
    are full by now (template G + those pieces) are exactly the rows that cleared."""
    placed = [cur_ts.tmpl.slots[s] for s in cur_ts.tmpl.slots if s not in cur_ts.remaining]
    rem = set(tmpl.slots)
    filled = {(x, y) for y, row in enumerate(tmpl.grid) for x, t in enumerate(row) if t == "G"}
    for s in placed:
        match = [sid for sid in rem if tmpl.slots[sid].ptype == s.ptype and tmpl.slots[sid].cells == s.cells]
        if not match:
            return None
        rem.discard(match[0])
        filled |= s.cells
    full = {y for y in range(len(tmpl.grid)) if all((x, y) in filled for x in range(core.W))}
    grid = [row for y, row in enumerate(tmpl.grid) if y not in full]
    ts = T.TState(tmpl, grid, frozenset(rem))
    return ts if ts.matches(board) else None
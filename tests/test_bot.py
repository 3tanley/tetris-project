"""Run with:  .venv/bin/python -m pytest tests -q"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tetrisbot import core, planner, sim, templates, vision  # noqa: E402

SHOT = os.environ.get("TETRIO_SCREENSHOT", os.path.join(os.path.dirname(__file__), "data", "tetrio_board.png"))


def test_kicks_and_spawn():
    b = core.Board()
    g = core.generate(b, "I")
    assert len(g) == 17                  # 7 flat + 10 vertical columns
    assert core.cells_of("I", 0, core.SPAWN_X, core.SPAWN_Y) == ((3, 21), (4, 21), (5, 21), (6, 21))


def test_tsd_spin_detected():
    b = core.Board.from_strings([
        "##........",
        "#...######",
        "##.#######",
    ])
    tsd = [p for p in core.generate(b, "T").values() if p.spin == "full" and core.lock(b, p)[1] == 2]
    assert tsd, "TSD not found"


def test_templates_chain():
    for op in templates.openers():
        if op.stage != "bag1":
            continue                     # Jaws: the opener is a whole 4-line PC
        b = core.Board()
        b.place_cells([c for s in op.slots.values() for c in s.cells])
        assert any(t.g_board() == b for t in templates.second_bag(op.family)), op.name
    assert len(templates.dpc()) >= 30


def test_singleyou_dependency():
    # SingleYou only fails when O comes after S, Z and T.
    ops = [t for t in templates.openers() if t.family == "SDPC"]
    for bag in ("TZLJOIS", "SILZJTO"):
        ok = any(planner.fill_template(core.Board(), templates.TState(t), list(bag), None)[0] for t in ops)
        assert ok == (bag == "TZLJOIS")


def test_sim_loop_runs_pc_loop():
    st = sim.run(120, seed=3, verbose=False)
    assert st["pc"] >= 5


def test_safe_mode_keys_gravity_independent():
    planner.SETTINGS["safe"] = True
    try:
        b = core.Board.from_strings(["#.........", "##....####", "###..#####"])
        for p in core.PIECES:
            for pl in core.generate(b, p, safe=True).values():
                keys = [k for k in pl.inputs]
                r, x, y, _, _ = sim.replay(b, p, keys)
                assert core.cells_of(p, r, x, y) == pl.cells
    finally:
        planner.SETTINGS["safe"] = False


def test_vision_on_screenshot():
    if not SHOT or not os.path.exists(SHOT):
        return
    from PIL import Image
    im = np.array(Image.open(SHOT).convert("RGB"))
    geo = vision.locate(im)
    assert geo is not None
    assert vision.read_queue(im, geo) == ["T", "O", "Z", "L", "J"]
    assert vision.read_hold(im, geo) == "S"


def _run_fake(limit=60, **kw):
    from fakegame import FakeTetrio
    from tetrisbot.controller import Bot
    from tetrisbot.handling import Handling

    planner.configure(safe=False, gravity_rps=0)
    fake = FakeTetrio(**kw)
    fake.limit = limit
    logs = []
    bot = Bot({"settle_ms": 0}, log=logs.append, handling=Handling())
    bot.autoplay = True          # "Bot plays" on (default is the advisor)
    bot.screen = fake
    bot.kb = fake
    bot.set_handling(bot.h)
    bot.start()
    t = time.time()
    while fake.pieces < fake.limit and time.time() - t < 120 and bot.running():
        time.sleep(0.05)
    bot.stop()
    bot.thread.join(5)
    bot.lookahead.close()          # its idle warm-up must not run into later tests
    planner.configure(safe=False)
    return fake, bot, logs


def test_controller_end_to_end():
    fake, bot, logs = _run_fake(seed=5)
    assert fake.pieces >= fake.limit, logs[-10:]
    assert not any("resyncing" in m for m in logs), [m for m in logs if "sync" in m]
    assert bot.brain.stats.get("pc", 0) >= 2, logs


def test_ghost_check_fixes_dropped_inputs():
    fake, bot, logs = _run_fake(seed=7, drop_rate=0.15)
    assert fake.pieces >= fake.limit, logs[-10:]
    assert fake.dropped > 0 and bot.corrections > 0
    assert not any("resyncing" in m for m in logs), [m for m in logs if "sync" in m or "check" in m]


def test_high_gravity_pipeline():
    """Blitz-like gravity ramping to 150 rows/s, real key timing, 60 ms screen lag:
    the bot must switch to high-gravity moves without pieces locking on their own."""
    from fakegame import FakeTetrio
    from tetrisbot.controller import Bot
    from tetrisbot.handling import Handling

    planner.configure(Handling(), safe=False, gravity_rps=0)
    fake = FakeTetrio(seed=8, latency_ms=60, banner_s=1.0, g_rps=150, timed_keys=True, g_ramp_pieces=60)
    fake.limit = 100
    logs = []
    bot = Bot({"settle_ms": 18}, log=logs.append, handling=Handling())
    bot.autoplay = True          # "Bot plays" on (default is the advisor)
    bot.screen = bot.kb = fake
    bot.set_handling(bot.h)
    fake.h = bot.h
    bot.start()
    t = time.time()
    while fake.pieces < fake.limit and time.time() - t < 120 and bot.running():
        time.sleep(0.05)
    bot.stop()
    bot.thread.join(5)
    bot.lookahead.close()
    planner.configure(safe=False, gravity_rps=0)
    assert fake.pieces >= fake.limit, logs[-10:]
    assert any("soft drop after every input" in m for m in logs)
    assert fake.autolocks <= 2 and fake.slammed == 0   # rare self-locks are handled, never slammed
    assert not any("resyncing" in m or "reading the board" in m for m in logs)
    assert fake.pcs >= 4


def test_ground_paths_work_at_any_gravity():
    import random
    rnd = random.Random(4)
    for _ in range(60):
        b = core.Board()
        for x in range(10):
            for y in range(rnd.randint(0, 6)):
                b.rows[y] |= 1 << x
        for p in core.PIECES:
            for pl in core.generate(b, p, safe=True).values():
                keys = [k for k in pl.inputs if k != core.HARD]
                x, y, r = core.walk(b, p, keys, gravity=True)[-1]
                assert core.cells_of(p, r, x, b.drop_y(p, r, x, y)) == pl.cells   # 20G
                r0, x0, y0, _, _ = sim.replay(b, p, pl.inputs)
                assert core.cells_of(p, r0, x0, y0) == pl.cells                  # no gravity


def test_finesse_matches_guide():
    from tetrisbot.handling import Handling
    planner.configure(Handling(optimize="FINESSE"), safe=False)
    g = planner.movegen(core.Board(), "O")
    by_col = {min(x for x, _ in cells): " ".join(p.inputs[:-1]) for cells, p in g.items()}
    assert by_col == {0: "DL", 1: "DL R", 2: "L L", 3: "L", 4: "", 5: "R", 6: "R R", 7: "DR L", 8: "DR"}


def test_tap_shorter_than_das():
    from tetrisbot.handling import Handling
    for das in (1, 10, 110):
        h = Handling(das_ms=das)
        assert h.tap_ms() < das and h.das_hold_ms() > das


def test_screen_lag_no_false_corrections():
    # the browser/capture shows the game ~80 ms late: must not "fix" pieces that are fine
    fake, bot, logs = _run_fake(limit=60, seed=8, latency_ms=80)
    assert fake.pieces >= fake.limit, logs[-10:]
    assert bot.corrections == 0, [m for m in logs if "[check]" in m][:5]
    assert not any("resyncing" in m for m in logs)


def test_screen_lag_with_dropped_inputs():
    fake, bot, logs = _run_fake(limit=60, seed=9, latency_ms=60, drop_rate=0.1)
    assert fake.pieces >= fake.limit, logs[-10:]
    assert fake.dropped > 0 and bot.corrections <= fake.dropped + 1
    assert not any("resyncing" in m for m in logs), [m for m in logs if "sync" in m or "check" in m]


def test_live_screenshot_reads():
    from PIL import Image
    im = np.array(Image.open(os.path.join(os.path.dirname(__file__), "data", "tetrio_live.png")).convert("RGB"))
    geo = vision.locate(im)
    assert vision.read_queue(im, geo) == ["L", "J", "T", "I", "S"]
    assert vision.read_hold(im, geo) == "O"
    board, _ = vision.read_board(im, geo)
    board.rows[19] = 0                      # the falling S has dipped into row 19
    p, cells = vision.read_active(im, geo, board)
    assert p == "S"
    excl = {(x, y) for y in range(20) for x in range(10) if board.filled(x, y)} | set(cells)
    assert vision.read_ghost(im, geo, excl) == {(3, 4), (4, 4), (4, 5), (5, 5)}


def test_dpc_mirrors_match_four_lol_mirrored_view():
    # four.lol's mirrored view of Extra O "JO": I in column 0, leftover O in columns 8-9
    lo = [t for t in templates.dpc("O") if t.label == "LO"][0]
    slot_at = {c: s for s in lo.slots.values() for c in s.cells}
    assert {slot_at[(0, y)].ptype for y in range(4)} == {"I"}
    assert slot_at[(8, 0)].ptype == "O" and slot_at[(9, 1)].ptype == "O"
    labels = {t.label for t in templates.dpc()}
    assert {"JO", "LO", "OJ", "OL", "OS", "OZ", "SO", "ZO", "JI", "LI", "IJO", "ILO"} <= labels
    for t in templates.dpc():
        b = core.Board()
        b.place_cells([c for s in t.slots.values() for c in s.cells])
        assert any(s.g_board() == b for s in templates.dpc_solutions()), t.name


def test_extra_piece_tracking_picks_matching_dpc():
    from tetrisbot.brain import Brain
    from tetrisbot.handling import Handling
    planner.configure(Handling(), safe=False, gravity_rps=0)
    for seed in (1, 3, 7, 11):
        g = sim.Game(seed)
        br = Brain(log=lambda m: None)
        br.bag.reset(aligned=True)
        checked = False
        for _ in range(60):
            step = br.decide(g.board, g.current, g.hold, g.visible())
            if br.ts is not None and br.ts.tmpl.stage == "dpc" and not checked:
                extra, why = br.extra_piece()
                h = br.bag.history
                _, start, unplaced, unseen = br._open_bag()   # the bag the extra piece is from
                assert len(unplaced) + len(unseen) == 1, why
                assert extra == (h[unplaced[0]] if unplaced else unseen[0]), why
                assert br.ts.tmpl.leftover == extra, (br.ts.tmpl.name, extra)
                checked = True
            _, cleared, _, hwe = g.apply(step)
            br.on_lock(step, hwe, cleared, g.board)
        assert checked, f"seed {seed} never reached DPC"


def test_all_clear_banner_does_not_break_the_loop():
    fake, bot, logs = _run_fake(limit=90, seed=7, latency_ms=40, banner_s=2.0)
    assert fake.pieces >= fake.limit, logs[-10:]
    assert fake.pcs >= 4
    assert not any("resyncing" in m for m in logs), [m for m in logs if "sync" in m]


def test_real_all_clear_frame_has_no_phantom_blocks():
    from PIL import Image
    im = np.array(Image.open(os.path.join(os.path.dirname(__file__), "data", "tetrio_allclear.png")).convert("RGB"))
    geo = vision.locate(im)
    board, _, unknown = vision.read_board_ex(im, geo)
    p, cells = vision.read_active(im, geo, None)
    assert p == "Z"                         # the falling piece, dipping into row 19
    for x, y in cells:
        if y < 20:
            board.rows[y] &= ~(1 << x)
    assert all(board.rows[y] == 0 for y in range(20)), "banner text read as blocks"
    assert len(unknown) >= 10


def test_no_false_high_gravity_without_gravity():
    """Zen-like game (no gravity), real key timing: rotations must not be mistaken for
    falling, so the bot must never switch to high-gravity moves."""
    from fakegame import FakeTetrio
    from tetrisbot.controller import Bot
    from tetrisbot.handling import Handling

    planner.configure(Handling(), safe=False, gravity_rps=0)
    fake = FakeTetrio(seed=3, latency_ms=60, timed_keys=True)
    fake.limit = 60
    logs = []
    bot = Bot({"settle_ms": 18}, log=logs.append, handling=Handling())
    bot.autoplay = True          # "Bot plays" on (default is the advisor)
    bot.screen = bot.kb = fake
    bot.set_handling(bot.h)
    fake.h = bot.h
    bot.start()
    t = time.time()
    while fake.pieces < fake.limit and time.time() - t < 90 and bot.running():
        time.sleep(0.05)
    bot.stop()
    bot.thread.join(5)
    bot.lookahead.close()
    assert not any("soft drop after every input" in m for m in logs), [m for m in logs if "gravity" in m]
    assert bot.grav_rps < 10
    assert fake.pcs >= 2


def test_recovers_into_the_loop_from_free_play():
    from tetrisbot.brain import Brain
    pcs = 0
    for seed in (2, 5):
        g = sim.Game(seed)
        br = Brain(log=lambda m: None)
        br.bag.reset(aligned=True)
        br.stage = "FREE"
        for _ in range(120):
            st = br.decide(g.board, g.current, g.hold, g.visible())
            _, cl, _, hwe = g.apply(st)
            br.on_lock(st, hwe, cl, g.board)
        pcs += br.stats["pc"]
    assert pcs >= 9


def test_bag_counter():
    from tetrisbot.brain import Brain
    br = Brain(log=lambda m: None)
    br.bag.reset(aligned=True)
    br.bag.update(0, "T", list("ZSIOJ"))
    br.cur_index = 3
    st = br.bag_status()
    assert st["bag"] == 1 and st["spawned"] == list("TZSI") and st["upcoming"] == list("OJ")
    assert st["missing"] == ["L"]


def test_line_clear_delay_keeps_hold_and_moves():
    """TETR.IO drops moves (and here also the hold) pressed during a line clear. The bot
    must wait for the spawn, and never hard drop a piece it didn't plan for."""
    fake, bot, logs = _run_fake(limit=80, seed=7, latency_ms=60, clear_delay_ms=150, timed_keys=True,
                                ihs_buffer=False)
    assert fake.pieces >= fake.limit, logs[-10:]
    assert fake.lost_inputs <= 3
    assert not any("resyncing" in m or "reading the board" in m for m in logs)
    assert fake.pcs >= 3


def test_wrong_piece_is_never_hard_dropped():
    from tetrisbot import controller
    real = controller.Bot._wait_spawn
    controller.Bot._wait_spawn = lambda self, cur, queue, timeout_s=0.6: True     # keys get lost
    try:
        fake, bot, logs = _run_fake(limit=60, seed=8, latency_ms=60, clear_delay_ms=150, timed_keys=True,
                                    ihs_buffer=False)
    finally:
        controller.Bot._wait_spawn = real
    assert fake.pieces >= fake.limit, logs[-10:]
    assert any("not hard dropping, re-planning" in m for m in logs)
    assert not any("resyncing" in m or "reading the board" in m for m in logs)


def test_fourlol_sdpc_solutions_match_the_sdpc_residue():
    lib = templates.library()
    for name in ("SDPC-TSD", "SDPC-TSD(m)"):
        tm = [t for t in lib["wiki"] if t.name == name][0]
        b = tm.g_board()
        b.place_cells([c for s in tm.slots.values() for c in s.cells])
        assert len([t for t in templates.sdpc_solutions() if t.g_board() == b]) >= 10
    assert any(t.label == "SD-PC #1" for t in templates.sdpc_solutions())          # not "ZD-PC"


def test_builds_bottom_up_even_if_it_needs_a_hold():
    # four.lol SD-PC TSD (= SDPC-TSD mirrored): with L before S, hold L and place S first,
    # so nothing has to be soft-dropped underneath (only the TSD's T uses soft drop)
    tm = [t for t in templates.library()["wiki"] if t.name == "SDPC-TSD(m)"][0]
    b = tm.g_board()
    comp, _, steps, _ = planner.fill_template(b, templates.TState.fresh_on(tm, b), list("LSZJOIT"), None)
    assert comp
    assert steps[0].hold and steps[0].pl.piece == "S"
    assert [st.pl.piece for st in steps if core.SOFT in st.pl.inputs] == ["T"]


def test_hold_lock_is_read_from_screen():
    from PIL import Image
    im = np.array(Image.open(os.path.join(os.path.dirname(__file__), "data", "tetrio_board.png")).convert("RGB"))
    geo = vision.locate(im)
    assert vision.read_hold(im, geo) == "S" and vision.hold_locked(im, geo)        # grey S = used


def test_slow_planning_never_slams_the_next_piece():
    """A T spun into its slot rests on the stack with its lock delay running. Even if
    planning the perfect clear is slow, the bot must not press space after the T has
    locked by itself (that would hard drop the next piece at spawn)."""
    import tetrisbot.brain as brain_mod
    orig = planner.find_pc

    def slow(*a, **k):
        time.sleep(0.7)
        return orig(*a, **k)

    planner.find_pc = brain_mod.planner.find_pc = slow
    try:
        fake, bot, logs = _run_fake(limit=60, seed=7, latency_ms=60, timed_keys=True, lock_always=True,
                                    prevent_hd_ms=0)
    finally:
        planner.find_pc = brain_mod.planner.find_pc = orig
    assert fake.pieces >= fake.limit, logs[-10:]
    assert fake.slammed == 0
    assert fake.pcs >= 2


def test_lookahead_plans_the_pc_during_the_tspin_setup():
    from tetrisbot.brain import Brain, Lookahead
    g = sim.Game(3)
    logs = []
    br = Brain(log=logs.append, lookahead=Lookahead(threaded=False))
    br.bag.reset(aligned=True)
    for _ in range(40):
        st = br.decide(g.board, g.current, g.hold, g.visible())
        _, cl, _, hwe = g.apply(st)
        br.on_lock(st, hwe, cl, g.board)
    assert sum("[lookahead] planned ahead" in m for m in logs) >= 2
    assert br.stats["pc"] >= 2


def test_queue_colour_beats_a_broken_shape():
    vision.CALIBRATED.clear()
    geo = vision.Geometry(0, 0, 10, 10)
    pix = np.zeros((10, 20, 3), dtype=np.uint8)
    pix[:] = vision.PALETTE["T"]
    occ = np.ones((10, 20), dtype=bool)            # looks like a 2x1 bar - no tetromino shape
    assert vision._classify_blob(pix, occ, geo) == "T"


def test_impossible_dpc_solution_scores_zero():
    """12:44 recording: extra-T DPC, hold L, then I T O Z J S S L Z. Solution 4 needs J and
    Z both to wait for line clears, but S (which J waits for) only comes after J - with one
    hold slot that can't work. It must score 0 and the certain ones 1."""
    from tetrisbot.brain import Brain
    b = core.Board.from_strings(["....#.....", "..###....#", ".#####..##"])
    br = Brain(log=lambda m: None)
    br.bag.reset(aligned=True)
    br.bag.history = list("ZSILJOT") + list("LITOZJS") + list("SLZ")
    br.cur_index = 8
    ps = {}
    for tm in templates.dpc_solutions():
        ts = templates.TState.fresh_on(tm, b)
        if ts is not None:
            ps[tm.name] = br._chance(ts, b, "L")[0]
    # every piece is visible and none of four.lol's extra-T solutions can be finished in
    # this order -> all 0, so the solver is used straight away; it finds the PC that
    # exists (hold L, hold I, O Z J S S - keeping the T)
    assert ps and all(p == 0 for p in ps.values()), ps
    assert br._select_dpc_pc(b, "L") is None
    br.stage = "PCDPC"
    br.decide(b, "I", "L", list("TOZJS"))
    assert br.plan and len(br.plan) == 7


def test_priority_list_puts_split_pieces_last():
    tm = [t for t in templates.dpc_solutions() if t.name == "PC-T-T-4"][0]
    groups = templates.priority_groups(tm)
    assert [tm.slots[s].ptype for s in groups[-1]] == ["Z"]
    assert {tm.slots[s].ptype for s in groups[0]} == {"I", "S"}


def test_prefers_o_next_to_the_i():
    """SDPC 2nd bag: when both work, build the four.lol layout (O beside the I), not the
    alternate O on top of the L."""
    from tetrisbot.brain import Brain
    op = [t for t in templates.library()["wiki"] if t.name == "SingleYou-A"][0]
    b = core.Board()
    b.place_cells([c for s in op.slots.values() for c in s.cells])
    b.clear_lines()
    picked = []
    import itertools, random
    rng = random.Random(1)
    for _ in range(12):
        bag = list(core.PIECES)
        rng.shuffle(bag)
        br = Brain(log=lambda m: None)
        br.bag.reset(aligned=True)
        br.bag.history = list("IJLOSTZ") + bag
        br.cur_index = 7
        br.stage, br.family = "BAG2", "SDPC"
        best = br._select(templates.second_bag("SDPC"), b, None)
        if best:
            picked.append(best[1].tmpl.name)
    alt = [n for n in picked if "altO" in n]
    std = [n for n in picked if "altO" not in n]
    assert std and len(alt) <= 2, picked


def test_tspin_goes_last_in_every_setup():
    """The T-spin finishes a setup: every other piece of the setup goes in first."""
    lib = templates.library()
    for tm in lib["wiki"] + lib["dpc"]:
        if not tm.spin_last or tm.stage.endswith("_pc"):
            continue          # Jigsaw 2nd bag: T S J I may go on top after the T-spin
        groups = templates.priority_groups(tm)
        spins = {s for s, sl in tm.slots.items() if sl.spin}
        if spins:
            assert set(groups[-1]) == spins, (tm.name, templates.priority_text(tm))


def test_sdpc_tsd_holds_an_early_t_until_the_end():
    """Live run: SDPC 2nd bag placed the T and then the J. With the T first in the queue
    it must be held and spun in last."""
    op = [t for t in templates.library()["wiki"] if t.name == "SingleYou-A"][0]
    b = core.Board()
    b.place_cells([c for s in op.slots.values() for c in s.cells])
    b.clear_lines()
    tsd = [t for t in templates.second_bag("SDPC") if t.name == "SDPC-TSD"][0]
    ts = templates.TState.fresh_on(tsd, b)
    for bag in ("TJZSOIL", "ZTJSLIO", "ZSTIJLO"):
        done, _, steps, _ = planner.fill_template(b, ts.copy(), list(bag), None)
        assert done, bag
        assert [st.piece for st in steps][-1] == "T" and steps[-1].pl.spin == "full", bag


def test_ms2_second_bag_follows_the_piece_order():
    """MS2 setup A has its I on top of the O; with S before O and the I early, the wiki
    says stack setup C (I on the floor, O on the S)."""
    from tetrisbot.brain import Brain
    op = [t for t in templates.library()["wiki"] if t.name == "MS2"][0]
    b = core.Board()
    b.place_cells([c for s in op.slots.values() for c in s.cells])
    b.clear_lines()
    for bag, want in (("SIZJTOL", "MS2-C"), ("ISZTJOL", "MS2-C"), ("OTJZILS", "MS2-A"),
                      ("JIOSLZT", "not A"), ("IOSZJTL", "not A")):
        br = Brain(log=lambda m: None)
        br.bag.reset(aligned=True)
        br.bag.history = list("IZJOTSL") + list(bag)
        br.cur_index = 7
        br.stage, br.family = "BAG2", "MS2"
        best = br._select(templates.second_bag("MS2"), b, "L")
        got = best and best[1].tmpl.name
        assert got and (got != "MS2-A" if want == "not A" else got == want), (bag, got)
        assert "compromise" not in best[1].tmpl.note, (bag, got)


def test_order_conflicts_counts_pieces_that_must_wait():
    ms2a = [t for t in templates.library()["wiki"] if t.name == "MS2-A"][0]
    ts = templates.TState(ms2a)
    assert templates.order_conflicts(ms2a, ts.remaining, list("LOZJISLT")) == 0
    assert templates.order_conflicts(ms2a, ts.remaining, list("LIZJOSLT")) == 1   # I before O


def _sample_boards(n=40, seed=0):
    import random
    rng = random.Random(seed)
    lib = templates.library()
    out = []
    for t in rng.sample(lib["dpc"] + lib["wiki"] + lib["dpc_pc"], n):
        b = t.g_board()
        slots = list(t.slots.values())
        rng.shuffle(slots)
        for s in slots[: rng.randint(0, len(slots) - 1)]:
            b.place_cells(s.cells)
        out.append(b)
    return out


def test_air_drops_are_real_placements():
    """The straight-drop table (computed once on an empty board) must give placements the
    full move search also finds, with keys that land exactly there - at normal gravity
    and in high-gravity mode with air time."""
    for safe, g in ((False, 0.0), (True, 20.0)):
        planner.SETTINGS["safe"], planner.SETTINGS["gravity_rps"] = safe, g
        try:
            for b in _sample_boards():
                if not planner._air_ok(b):
                    continue
                for p in core.PIECES:
                    full = planner.generate(b, p)
                    for cells, pl in planner.air_drops(b, p).items():
                        assert cells in full, (safe, p, cells)
                        r, x, y, _, _ = sim.replay(b, p, [k for k in pl.inputs])
                        assert core.cells_of(p, r, x, y) == cells, (safe, p, pl.inputs)
        finally:
            planner.SETTINGS["safe"], planner.SETTINGS["gravity_rps"] = False, 0.0


def test_two_pass_pc_finds_what_the_full_search_finds():
    import random
    rng = random.Random(3)
    boards = []
    for t in templates.dpc():
        b = core.Board()
        for s in t.slots.values():
            b.place_cells(s.cells)
        if b.height() <= 4:
            boards.append(b)
    for b in rng.sample(boards, 12):
        bag = list(core.PIECES)
        rng.shuffle(bag)
        hold = rng.choice(core.PIECES)
        for h in planner.pc_heights(b, 4):
            full = planner._pc_solve(b, bag, hold, h, time.time() + 5, False, False)
            fast = planner.pc_solve(b, bag, hold, h, time_limit=10, strict=False)
            assert bool(full) == bool(fast), (str(b), bag, hold, h)
            if fast:                                  # and it really clears the field
                nb = b.copy()
                for st in fast:
                    nb.place_cells(st.pl.cells)
                assert nb.rows[0] == 0


def test_can_fill_agrees_with_fill_template():
    import random
    rng = random.Random(4)
    tms = [t for t in templates.dpc() if not t.mirrored][:8]
    for tm in tms:
        ts = templates.TState(tm)
        for _ in range(6):
            seq = list(core.PIECES)
            rng.shuffle(seq)
            seq = ([tm.leftover] if tm.leftover else []) + seq
            done = planner.fill_template(core.Board(), ts.copy(), seq, None, node_limit=100000)[0]
            assert planner.can_fill(core.Board(), ts.copy(), seq, None, node_limit=100000) == done, \
                (tm.name, seq)


def test_high_gravity_main_thread_stays_fast():
    """High gravity: a decide on the bot thread must leave time before the piece locks."""
    import random
    from tetrisbot.brain import Brain, Lookahead
    rng = random.Random(5)
    g = sim.Game(12)
    br = Brain(log=lambda m: None, lookahead=Lookahead(threaded=False))
    br.bag.reset(aligned=True)
    worst = 0.0
    try:
        for _ in range(150):
            planner.SETTINGS["safe"] = True
            planner.SETTINGS["gravity_rps"] = 20.0 * (1 + 0.15 * rng.random())   # noisy reading
            t = time.perf_counter()
            with planner.foreground_busy():
                step = br._decide(g.board, g.current, g.hold, g.visible())
            worst = max(worst, time.perf_counter() - t)
            br._maybe_lookahead(g.board, g.hold)
            cells, cleared, spin, hold_was_empty = g.apply(step)
            br.on_lock(step, hold_was_empty, cleared, g.board)
    finally:
        planner.SETTINGS["safe"], planner.SETTINGS["gravity_rps"] = False, 0.0
    assert worst < 0.45, worst


def test_jigsaw_chain():
    """Jigsaw: every bag-1 build leads to a bag-2 build, every bag-2 build (main and
    alternate) leaves the same residue, and the 3rd-bag PCs start from it."""
    lib = templates.library()
    bag1 = [t for t in lib["wiki"] if t.family == "JIGSAW" and t.stage == "bag1"]
    bag2 = [t for t in lib["wiki"] if t.family == "JIGSAW" and t.stage == "bag2"]
    assert len(bag1) == 4 and len(bag2) == 8
    for op in bag1:
        r1 = templates.residue(op)
        nxt = [t for t in bag2 if t.g_board() == r1]
        assert len(nxt) == 2 and {t.fallback for t in nxt} == {False, True}, op.name
        r2 = {tuple(templates.residue(t).rows) for t in nxt}
        assert len(r2) == 1, op.name               # main and alternate: same residue
        r2b = templates.residue(nxt[0])
        sols = [t for t in lib["jigsaw_pc"] if t.g_board() == r2b]
        assert len(sols) == 6, op.name
    early = [t for t in lib["wiki"] if t.stage == "bag2_pc"]
    assert early and all(t.fallback for t in early)
    for t in early:                                 # each early PC really clears the field
        assert templates.residue(t).rows[0] == 0, t.name


def _opener_brain(bag, openers):
    from tetrisbot.brain import Brain
    from tetrisbot.handling import Handling
    h = Handling()
    h.openers = openers
    planner.configure(h)
    br = Brain(log=lambda m: None)
    br.bag.reset(aligned=True)
    br.bag.history = list(bag)
    br.cur_index = 0
    return br


def test_opener_toggles_and_failsafe():
    try:
        # everything on: the user's priority order decides among openers that can be built
        br = _opener_brain("SOZTJIL", "SDPC,MS2,MS,MS3,JIGSAW")
        assert br._select_opener(core.Board(), None)[1].tmpl.family == "SDPC"
        br = _opener_brain("SOZTJIL", "JIGSAW,SDPC,MS2,MS,MS3")
        assert br._select_opener(core.Board(), None)[1].tmpl.family == "JIGSAW"
        # the top one can't be built for sure with this bag (O after S, Z, T): the next one
        br = _opener_brain("SILZJTO", "SDPC,MS2")
        assert br._select_opener(core.Board(), None)[1].tmpl.family == "MS2"
        # only SD-PC on, and SingleYou can be built with this bag: SD-PC
        br = _opener_brain("TZLJOIS", "SDPC")
        assert br._select_opener(core.Board(), None)[1].tmpl.family == "SDPC"
        # only SD-PC on, but SingleYou fails when O comes after S, Z and T: failsafe
        br = _opener_brain("SILZJTO", "SDPC")
        best = br._select_opener(core.Board(), None)
        assert best and best[1].tmpl.family != "SDPC" and best[0][0] >= 1.0
        # MS3 off and MS2 on: never MS3 when MS2 can be built
        br = _opener_brain("IZJOTSL", "MS2")
        assert br._select_opener(core.Board(), None)[1].tmpl.family == "MS2"
    finally:
        from tetrisbot.handling import Handling
        planner.configure(Handling())


def test_jigsaw_loop_runs():
    from tetrisbot.handling import Handling
    h = Handling()
    h.openers = "JIGSAW"
    planner.configure(h)
    try:
        st = sim.run(130, seed=4, verbose=False)
    finally:
        planner.configure(Handling())
    assert st["pc"] >= 6, st


def test_openers_setting_round_trip(tmp_path):
    from tetrisbot.handling import Handling
    h = Handling()
    h.set_opener("MS3", False)
    h.set_opener("JIGSAW", True)
    h.move_opener("JIGSAW", 0)                  # dragged to the top
    h.save(tmp_path / "s.json")
    h2 = Handling.load(tmp_path / "s.json")
    assert not h2.opener_on("MS3") and h2.opener_on("JIGSAW") and h2.opener_on("SDPC")
    assert h2.opener_order() == ["JIGSAW", "JAWS", "SDPC", "MS2", "MS"]
    h2.set_opener("MS3", True)                   # switched on: bottom of the list
    assert h2.opener_order()[-1] == "MS3"


def test_dpc_plans_its_pc_only_near_the_end(monkeypatch):
    """User: place the S/Z DPC pieces first and plan the PC once the last ones are known
    (more of the next bag is visible, and nothing competes with the pieces being placed)."""
    from tetrisbot import brain
    from tetrisbot.handling import Handling
    seen = []
    orig = brain.Brain._maybe_lookahead

    def spy(self, board, hold):
        before = self.lookahead.sig if self.lookahead else None
        orig(self, board, hold)
        if self.ts is not None and self.ts.tmpl.stage == "dpc" and self.lookahead.sig != before:
            seen.append(len(self.ts.remaining))

    monkeypatch.setattr(brain.Brain, "_maybe_lookahead", spy)
    h = Handling()
    h.openers = "JIGSAW"
    planner.configure(h)
    try:
        st = sim.run(110, seed=2, verbose=False)
    finally:
        planner.configure(Handling())
    assert st["pc"] >= 5 and seen, (st, seen)
    assert max(seen) <= brain.DPC_LOOKAHEAD_SLOTS, seen


def test_warm_up_covers_the_sz_dpc_and_stops_for_a_job():
    from tetrisbot.brain import Lookahead, warm_order
    la = Lookahead(threaded=False)
    order = warm_order()
    jaws = templates.library()["jaws"]
    sz = [t for t in templates.dpc() if t.leftover in ("S", "Z")]
    assert order[: len(jaws)] == jaws                  # the opener choice first
    assert order[len(jaws): len(jaws) + len(sz)] == sz
    first_other = min(order.index(t) for t in templates.dpc() if t.leftover not in ("S", "Z"))
    for t in sz:                                   # their PC solutions before other DPCs
        for sol in templates.solutions_after(t):
            assert order.index(sol) < first_other
    la._job = ("sig", lambda: None)                # a job is waiting: warm-up yields
    n0 = len(planner._GEN_CACHE)
    planner._GEN_CACHE.clear()
    assert la.warm_step() is True and la._warm_todo[0] is order[0]
    la._job = None
    for _ in range(len(jaws) + len(sz)):
        la.warm_step()
    n = len(planner._GEN_CACHE)
    for t in sz:
        planner.warm_template(t)
    assert len(planner._GEN_CACHE) == n            # nothing left to compute for them


def _recording_2320(check):
    """2026-10-09 23:20 recording, 5 s: the S was meant to tuck into the bottom right
    (CCW, DAS right, soft drop, CCW) but TETR.IO took the DAS as a single step; the S was
    soft dropped 4 columns too far left and kicked onto the stack."""
    sys.path.insert(0, os.path.dirname(__file__))
    from fakegame import FakeTetrio
    from tetrisbot.controller import Bot
    from tetrisbot.handling import Handling
    planner.configure(Handling(), safe=False, gravity_rps=0)
    board = core.Board.from_strings([".......#..", "##.#####..", "########..", "#######..#"])
    target = tuple(sorted([(7, 0), (8, 0), (8, 1), (9, 1)]))
    fake = FakeTetrio(seed=1)
    fake.game.board = board.copy()
    fake.game.current = "S"
    fake._spawn()
    bot = Bot({"settle_ms": 0}, log=lambda m: None, handling=Handling())
    bot.autoplay = True          # "Bot plays" on (default is the advisor)
    bot.lookahead.close()
    bot.screen, bot.kb = fake, fake
    bot.board, bot.lag = board.copy(), 0.0
    assert bot._locate()
    pl = planner.generate(board, "S")[target]
    step = planner.Step(False, pl)
    keys = pl.inputs[:-1]
    i = keys.index(core.SOFT)
    air, rest = keys[:i], keys[i:]
    for k in air:                                   # the DAS slide only moves one cell
        fake.press(core.RIGHT if k == core.DAS_RIGHT else (core.LEFT if k == core.DAS_LEFT else k))
    if check:
        rest, _, fixed = bot._check_before_softdrop(step, air, rest)
        assert fixed
    for k in rest:
        fake.press(k)
    x, y, r = fake.state
    return tuple(sorted(core.cells_of("S", r, x, y))), target


def test_soft_drop_waits_for_the_slide():
    got, target = _recording_2320(check=False)
    assert got != target                            # what happened in the recording
    got, target = _recording_2320(check=True)
    assert got == target                            # the check re-planned before the soft drop


def test_kicks_are_mirror_images():
    """tetrio.wiki.gg Spins: setups can be mirrored, but so must the piece - CW/CCW kicks
    of mirrored rotations are mirror images (also SRS+ I kicks)."""
    for tab in (core._K, core._IK):
        for (a, b), ks in tab.items():
            if (a - b) % 2:
                assert [(-x, y) for x, y in ks] == tab[((4 - a) % 4, (4 - b) % 4)], (a, b)


def test_mirrored_tuck_uses_mirrored_rotations():
    from tetrisbot.handling import Handling
    h = Handling()
    planner.configure(h, safe=False, gravity_rps=0)
    rows = [".......#..", "##.#####..", "########..", "#######..#"]
    b = core.Board.from_strings(rows)
    bm = core.Board.from_strings([r[::-1] for r in rows])
    t = tuple(sorted([(7, 0), (8, 0), (8, 1), (9, 1)]))
    tm = tuple(sorted((9 - x, y) for x, y in t))
    s = [k for k in planner.generate(b, "S")[t].inputs if k in (core.CW, core.CCW)]
    z = [k for k in planner.generate(bm, "Z")[tm].inputs if k in (core.CW, core.CCW)]
    flip = {core.CW: core.CCW, core.CCW: core.CW}
    assert s and z == [flip[k] for k in s], (s, z)


def test_sideways_moves_happen_before_the_soft_drop():
    """Move horizontally in the air, then soft drop, then kick in - never slide on the
    stack when an equally cheap air path exists."""
    from tetrisbot.handling import Handling
    planner.configure(Handling(), safe=False, gravity_rps=0)
    for b in _sample_boards(30, seed=7):
        for p in core.PIECES:
            for pl in planner.generate(b, p).values():
                if core.SOFT in pl.inputs:
                    after = pl.inputs[pl.inputs.index(core.SOFT) + 1:]
                    slides = [k for k in after if k in (core.LEFT, core.RIGHT, core.DAS_LEFT, core.DAS_RIGHT)]
                    if slides:
                        # only when the slide really has to happen on the stack (under an overhang)
                        alt = [k for k in pl.inputs if k != core.SOFT]
                        r, x, y, _, _ = sim.replay(b, p, alt + ([core.HARD] if alt[-1] != core.HARD else []))
                        assert core.cells_of(p, r, x, y) != pl.cells, (p, pl.inputs)


def test_jaws_and_second_pc_templates_clear_the_field():
    """Jaws (four.lol ILSZ: 22 + ILOSZ 31 + ILJOSZ 15 solutions, mirrors, duplicates
    removed) and four.lol's 2nd PC solutions are perfect clears; every 2nd PC setup has
    solutions that start from it."""
    lib = templates.library()
    assert len(lib["jaws"]) == 108
    for t in lib["jaws"] + lib["pc2_pc"]:
        assert templates.residue(t).rows[0] == 0, t.name
    sol_fields = {tuple(t.g_board().rows) for t in lib["pc2_pc"]}
    for t in lib["pc2"]:
        assert tuple(templates.residue(t).rows) in sol_fields, t.name
    # every Jaws solution leaves 4 pieces that some 2nd PC pattern takes - except #22,
    # which leaves two O's (no four.lol pattern; rated 0, so it's the last choice)
    assert all(t.pc_rate >= 0.8 for t in lib["jaws"] if t.leftover2 and len(set(t.leftover2)) == 4)


def test_jaws_only_at_a_clean_bag_start():
    from tetrisbot.handling import Handling
    try:
        br = _opener_brain("ILSZOTJ", "JAWS")
        assert br._select_jaws(core.Board(), None) is not None
        assert br._select_jaws(core.Board(), "T") is None      # a piece carried in hold
    finally:
        planner.configure(Handling())


def test_second_pc_scans_every_pattern(monkeypatch):
    """After the Jaws PC: any four.lol 2nd PC setup whose pieces are on hand is considered."""
    from tetrisbot.brain import Brain
    from tetrisbot.handling import Handling
    planner.configure(Handling())
    br = Brain(log=lambda m: None)
    br.bag.reset(aligned=True)
    br.bag.history = list("ILSZOTJ") + list("OSLJTZI") + list("SOJLITZ")
    br.cur_index = 10                       # bag 2: J T Z I left
    br.stage = "PC2"
    step = br.decide(core.Board(), "J", None, list("TZISO"))
    assert br.ts is not None and br.ts.tmpl.stage == "pc2", br.stage
    assert sorted(br.ts.tmpl.types()) == sorted("JTZI")


def test_keys_per_piece_like_top_players():
    """Finesse: fewest presses (a DAS slide is one), ~3.3 keys per piece like the Blitz WR."""
    from tetrisbot.brain import Brain, Lookahead
    from tetrisbot.handling import Handling
    planner.configure(Handling(), safe=False, gravity_rps=0)
    keys = pieces = 0
    for seed in (1, 2):
        g = sim.Game(seed)
        br = Brain(log=lambda m: None, lookahead=Lookahead(threaded=False))
        br.bag.reset(aligned=True)
        for _ in range(100):
            step = br.decide(g.board, g.current, g.hold, g.visible())
            keys += len(step.keys())
            pieces += 1
            fewest = min(len(pl.inputs) for c, pl in planner.generate(g.board, step.pl.piece).items()
                         if c == step.pl.cells)
            assert len(step.pl.inputs) == fewest, step       # finesse: no wasted presses
            _, cl, _, hwe = g.apply(step)
            br.on_lock(step, hwe, cl, g.board)
    assert keys / pieces <= 3.5, keys / pieces          # the rest is holds (~0.3 per piece)


def test_20g_plans_skip_pointless_soft_drops():
    """At 20G gravity pulls the piece down between keys: no soft-drop presses for that, and
    the keys still land exactly where planned when the piece falls after every key."""
    from tetrisbot.handling import Handling
    planner.configure(Handling(), safe=True, gravity_rps=1200)
    try:
        sds = 0
        for b in _sample_boards(25, seed=11):
            for p in core.PIECES:
                for cells, pl in planner.generate(b, p).items():
                    sds += pl.inputs.count(core.SOFT)
                    r, x, y, _, _ = sim.replay(b, p, list(pl.inputs), gravity=True)
                    assert core.cells_of(p, r, x, y) == cells, (p, pl.inputs)
        planner.configure(safe=True, gravity_rps=0)
        sds_slow = sum(pl.inputs.count(core.SOFT) for b in _sample_boards(25, seed=11) for p in core.PIECES
                       for pl in planner.generate(b, p).values())
        assert sds < sds_slow / 2, (sds, sds_slow)
    finally:
        planner.configure(safe=False, gravity_rps=0)


# ------------------------------------------------------------------ advisor (coach)
def _follow(user_openers, coach_openers, seed, pieces):
    """The "user" is a bot restricted to `user_openers`; the coach watches each placement
    with the overlay's settings (`coach_openers`). Returns (coach, user, per-piece log)."""
    from contextlib import contextmanager
    from tetrisbot.brain import Brain, Lookahead
    from tetrisbot.coach import Coach
    from tetrisbot.handling import Handling
    from tetrisbot.model import SetupPrior

    @contextmanager
    def openers(txt):
        h = Handling()
        h.openers = txt
        old = planner.SETTINGS["handling"]
        planner.configure(h, safe=False)
        try:
            yield
        finally:
            planner.configure(old, safe=False)

    g = sim.Game(seed)
    user = Brain(log=lambda *a: None, lookahead=Lookahead(threaded=False))
    user.bag.reset(aligned=True)
    coach = Coach(log=lambda *a: None, lookahead=Lookahead(threaded=False), prior=SetupPrior(path=None))
    with openers(coach_openers):
        coach.begin(g.board.copy(), g.current, g.hold, g.visible(), True)
    trace = []
    for n in range(pieces):
        if n:
            with openers(coach_openers):
                coach.spawned(g.board.copy(), g.current, g.hold, g.visible())
        with openers(user_openers):
            step = user.decide(g.board, g.current, g.hold, g.visible())
        before = g.board.copy()
        _, cleared, _, hwe = g.apply(step)
        user.on_lock(step, hwe, cleared, g.board)
        with openers(coach_openers):
            coach.locked(before, step.pl.piece, step.pl.rot, step.pl.x, step.pl.y, step.hold, g.board.copy(), cleared)
        trace.append((user.stage, coach.brain.stage, (coach.brain.display or {}).get("title", "")))
    return coach, user, trace


def test_coach_agrees_with_the_bot_it_watches():
    # same settings on both sides: every suggestion is exactly what the bot plays
    coach, user, trace = _follow("JAWS,SDPC,MS2,MS,MS3", "JAWS,SDPC,MS2,MS,MS3", seed=3, pieces=60)
    assert coach.followed == coach.suggested == 60
    assert all(u == c for u, c, _ in trace), trace
    assert coach.brain.stats["pc"] == user.stats["pc"] >= 2


def test_coach_recognises_the_users_opener():
    # the user builds MS2 although SD-PC is first in the overlay's order: by the 3rd piece
    # the display says MS2 and stays with it through the 2nd bag, the PC, the DPC and its PC
    coach, user, trace = _follow("MS2", "SDPC,MS2", seed=3, pieces=36)
    assert "Mountainous Stacking 2" in trace[2][2], trace[:4]
    assert all(u == c for u, c, _ in trace), trace
    assert any(t.startswith("DPC setup") for _, _, t in trace)
    assert any(t.startswith("DPC perfect clear") for _, _, t in trace)
    assert coach.brain.stats["pc"] == user.stats["pc"] == 2


def test_coach_switches_to_a_setup_that_can_still_be_finished():
    # Jigsaw's Jaws-style build fits Jaws #13 too; when the queue rules Jaws out the coach
    # follows Jigsaw instead of giving up
    coach, user, trace = _follow("JIGSAW", "JAWS,JIGSAW", seed=5, pieces=30)
    assert "FREE" not in [c for _, c, _ in trace[3:]], trace
    assert coach.brain.stats["pc"] == user.stats["pc"]


def test_fit_placement_with_line_clear():
    from tetrisbot.coach import fit_placement
    before = core.Board.from_strings(["#########."] * 2)
    after = before.copy()
    after.place_cells(core.cells_of("I", 1, 8, 2))       # vertical I in the well: clears 2
    assert after.rows[:2] == [1 << 9, 1 << 9, 0][:2]
    p, r, x, y, cleared, b = fit_placement(before, after, ["I"])
    assert p == "I" and len(cleared) == 2 and b == after


def test_watcher_follows_the_screen():
    # the user plays on the fake TETR.IO screen (ALL CLEAR banners, line clear delay,
    # screen lag); the watcher must explain every lock without re-reading the game
    from fakegame import FakeTetrio
    from tetrisbot.brain import Brain, Lookahead
    from tetrisbot.coach import Coach, Watcher
    from tetrisbot.model import SetupPrior

    planner.configure(safe=False, gravity_rps=0)
    fake = FakeTetrio(seed=7, banner_s=0.3, clear_delay_ms=150, latency_ms=40)
    geo = vision.locate(fake.full())
    box = geo.bounds()
    lgeo = vision.Geometry(geo.left - box[0], geo.top - box[1], geo.cw, geo.ch)
    logs = []
    coach = Coach(log=logs.append, lookahead=Lookahead(threaded=False), prior=SetupPrior(path=None))
    w = Watcher(coach, logs.append)
    user = Brain(log=lambda *a: None, lookahead=Lookahead(threaded=False))
    user.bag.reset(aligned=True)
    g = fake.game
    for _ in range(36):
        w.poll(fake.grab(box), lgeo)
        step = user.decide(g.board, g.current, g.hold, g.visible())
        hwe = g.hold is None
        cleared = g.board.copy().place_cells(step.pl.cells)
        for k in step.keys():
            fake.press(k)
            w.poll(fake.grab(box), lgeo)
        user.on_lock(step, hwe, cleared, g.board)
        t = time.time()
        while time.time() - t < 0.2:          # human pace
            w.poll(fake.grab(box), lgeo)
            time.sleep(0.01)
    assert coach.pieces == fake.pieces == 36, logs
    assert not any("re-reading" in m for m in logs), logs
    assert coach.followed == coach.suggested
    assert coach.brain.stats["pc"] == fake.pcs >= 1


def test_setup_prior_learns_from_the_user(tmp_path):
    from tetrisbot.model import SetupPrior, USER_WEIGHT
    p = SetupPrior({"MS2": 3}, path=str(tmp_path / "prior.json"))
    assert p.score("MS2") == 4 and p.score("never-seen") == 1
    p.learn("SingleYou-A")
    q = SetupPrior.load(str(tmp_path / "prior.json"))
    assert q.score("SingleYou-A") == 1 + USER_WEIGHT and q.score("MS2") == 4


def test_mode_setting_round_trip(tmp_path):
    from tetrisbot.handling import Handling
    h = Handling()
    assert h.mode == "BLITZ"
    path = str(tmp_path / "s.json")
    h.save(path)
    assert Handling.load(path).mode == "BLITZ"


def test_advisor_mode_never_presses_keys():
    # "Bot plays" off: the live loop only watches - every piece on the fake screen is the user's
    from fakegame import FakeTetrio
    from tetrisbot.brain import Brain, Lookahead
    from tetrisbot.controller import Bot
    from tetrisbot.handling import Handling
    from tetrisbot.model import SetupPrior

    planner.configure(safe=False, gravity_rps=0)
    fake = FakeTetrio(seed=5, banner_s=1.5, latency_ms=40)
    bot = Bot({"settle_ms": 0}, log=lambda *a: None, handling=Handling())
    bot.prior = SetupPrior(path=None)          # don't learn the fake user's setups into the repo
    bot.screen = bot.kb = fake
    bot.set_handling(bot.h)
    assert not bot.autoplay
    bot.start()
    time.sleep(0.4)
    user = Brain(log=lambda *a: None, lookahead=Lookahead(threaded=False))
    user.bag.reset(aligned=True)
    g = fake.game
    try:
        for _ in range(24):
            step = user.decide(g.board, g.current, g.hold, g.visible())
            hwe = g.hold is None
            cleared = g.board.copy().place_cells(step.pl.cells)
            for k in step.keys():
                fake.press(k)
            user.on_lock(step, hwe, cleared, g.board)
            time.sleep(0.25)
        time.sleep(0.5)
        s = bot.status()
    finally:
        bot.stop()
        bot.thread.join(5)
        bot.lookahead.close()
    assert fake.pieces == 24 and s["pieces"] == 24
    assert s["followed"] == s["suggested"] and s["advice"].startswith("next:")
    assert s["display"]["title"]


def test_opener_priority_order_drives_the_suggestion():
    # MS2 and SingleYou on, SingleYou dragged above MS2: the advisor suggests SingleYou
    # first, and switches to MS2 once the user's pieces show MS2
    from tetrisbot.brain import Lookahead
    from tetrisbot.coach import Coach
    from tetrisbot.handling import Handling
    from tetrisbot.model import SetupPrior

    old = planner.SETTINGS["handling"]
    try:
        for order, expect in (("SDPC,MS2", "SingleYou"), ("MS2,SDPC", "Mountainous Stacking 2")):
            h = Handling()
            h.openers = order
            planner.configure(h, safe=False)
            g = sim.Game(3)
            coach = Coach(log=lambda *a: None, lookahead=Lookahead(threaded=False), prior=SetupPrior(path=None))
            coach.begin(g.board.copy(), g.current, g.hold, g.visible(), True)
            assert expect in coach.brain.display["title"], (order, coach.brain.display)
    finally:
        planner.configure(old, safe=False)
    coach, user, trace = _follow("MS2", "SDPC,MS2", seed=3, pieces=8)
    assert "Mountainous Stacking 2" in trace[2][2], trace[:4]


def _coach_replay(openers, seq, placements):
    """Advisor with these openers on; the user places `placements` (piece, cells) with the
    7-bag order `seq`. Returns the coach."""
    from tetrisbot.brain import Lookahead
    from tetrisbot.coach import Coach
    from tetrisbot.handling import Handling
    from tetrisbot.model import SetupPrior

    h = Handling()
    h.openers = openers
    planner.configure(h, safe=False)
    c = Coach(log=lambda *a: None, lookahead=Lookahead(threaded=False), prior=SetupPrior(path=None))
    b = core.Board()
    c.begin(b.copy(), seq[0], None, seq[1:6], True)
    for i, (piece, cells) in enumerate(placements):
        before = b.copy()
        x, y, r = core.identify(piece, cells)[0]
        cleared = b.place_cells(core.cells_of(piece, r, x, y))
        c.locked(before, piece, r, x, y, False, b.copy(), cleared)
        c.spawned(b.copy(), seq[i + 1], None, seq[i + 2:i + 7])
    return c


def test_advisor_only_recognises_openers_that_are_switched_on():
    # 2026-10-13 screenshot: Jaws + Jigsaw on, Z flat in columns 5-7 and O on the right
    # fit only MS / MS2 (switched off): no MS2 on the display
    seq = list("ZOSITLJZITLJOSIJLOSTZ")
    O = [(8, 0), (9, 0), (8, 1), (9, 1)]
    try:
        c = _coach_replay("JAWS,JIGSAW", seq, [("Z", [(4, 1), (5, 1), (5, 0), (6, 0)]), ("O", O)])
        assert "Mountainous" not in c.brain.display["title"] and c.brain.stage == "FREE"
        assert "doesn't match any opener switched on" in c.brain.display["sub"]
        # one column to the right it is four.lol's ILOSZ (O on the far right)
        c = _coach_replay("JAWS,JIGSAW", seq, [("Z", [(5, 1), (6, 1), (6, 0), (7, 0)]), ("O", O)])
        assert c.brain.display["title"] == "Opener: Jaws (ILOSZ)", c.brain.display
        # Jaws is shown as its 4-piece build: no solution pieces that aren't placed yet
        assert sum(ch.isupper() and ch not in "G" for row in c.brain.display["rows"] for ch in row) == 4 * 4
        # with MS2 switched on the same pieces are MS2
        c = _coach_replay("MS2", seq, [("Z", [(4, 1), (5, 1), (5, 0), (6, 0)]), ("O", O)])
        assert "Mountainous Stacking 2" in c.brain.display["title"]
    finally:
        from tetrisbot.handling import Handling
        planner.configure(Handling(), safe=False)


def test_jaws_is_the_fourlol_ilsz_data():
    raw = templates._jaws_templates()
    kinds = {k: sum(1 for t in raw if t.name.startswith(k + "-") and t.name[len(k) + 1].isdigit())
             for k in ("Jaws", "Jaws-ILOSZ", "Jaws-ILJOSZ")}
    # 22 minimal ILSZ solutions, 33 ILOSZ (2 draw a piece across a clearing row), 15 ILJOSZ
    assert kinds == {"Jaws": 22, "Jaws-ILOSZ": 31, "Jaws-ILJOSZ": 15}, kinds
    for t in raw:
        build = sorted(t.slots[s].ptype for s in t.slots if s.startswith("b"))
        assert build == ["I", "L", "S", "Z"] and len(t.slots) == 10, t.name
        assert templates.residue(t).rows[0] == 0, t.name


# ------------------------------------------------------------------ sprint (6-3)
def test_sprint_63_advice_scores_tetrises():
    # following the advice: 40 lines almost only by tetrises, well (column 7) kept open,
    # no soft drops, no holes outside the well
    from tetrisbot import sprint
    for seed in (1, 4):
        g = sim.Game(seed)
        n = tetrises = soft = 0
        while g.lines < 40:
            st = sprint.plan(g.board, g.current, g.hold, g.visible())[0][0]
            soft += core.SOFT in st.keys()
            _, cleared, _, _ = g.apply(st)
            n += 1
            tetrises += len(cleared) == 4
            hs = g.board.col_heights()
            if st.pl.piece != "I":
                assert hs[sprint.WELL] == 0, f"seed {seed} piece {n}: well covered\n{g.board}"
        assert tetrises >= 9 and n <= 115 and soft <= 2, (seed, n, tetrises, soft)


def test_sprint_right_side_patterns():
    # the 3-wide side is built only from the six patterns of the user's screenshot
    from tetrisbot import sprint
    for rows in sprint.RIGHT_PATTERNS:
        pieces = sprint._pattern_pieces(rows)
        assert len(pieces) == 3 and all(len(cs) == 4 for _, cs in pieces), rows
    assert sprint._NEXT[0] == frozenset("JLOT")             # S, Z and I never start a block
    assert sprint._FULL3 in sprint._NEXT                    # every pattern can be finished
    # bottom-up only: the J of pattern 1 can't hang over the empty middle column
    flat_l = core.Board.from_strings([".........#", "######.###"])
    assert sprint.right_blocks(flat_l)[1] == frozenset("OZ")
    # following the advice keeps the 3-wide side on the patterns (a forced exception at most)
    for seed in (2, 3):
        g = sim.Game(seed)
        offs = 0
        while g.lines < 40:
            before = sprint.right_blocks(g.board, sprint.align(g.board))[0]
            g.apply(sprint.plan(g.board, g.current, g.hold, g.visible())[0][0])
            offs += sprint.right_blocks(g.board, sprint.align(g.board))[0] > before
        assert offs <= 1, (seed, offs)


def test_sprint_display_shows_preview_pieces():
    from tetrisbot import sprint
    ready = core.Board.from_strings(["######.###"] * 4)
    steps = sprint.plan(ready, "I", None, list("TLJOS"), sprint.depth_for(5))
    assert steps[0][2] == 4 and len(steps) == 6
    assert sprint.display(ready, steps, 0, preview=0)["labels"] == []
    d = sprint.display(ready, steps, 0, preview=5)
    assert [t for _, _, t in d["labels"]] == ["2", "3", "4", "5", "6"]
    n = len(d["rows"])
    # the pieces after the tetris sit above the 4 cleared rows, never on top of them
    later = sum(ch.islower() for row in d["rows"] for ch in row)
    assert later == 5 * 4 and all(not ch.islower() for row in d["rows"][n - 4:] for ch in row)
    assert "TETRIS" in d["sub"]


def test_sprint_bot_plays_40_lines():
    # BOT PLAYS in Sprint: the controller drives SprintBrain on the fake TETR.IO screen
    # (screen lag, line-clear delay, a few dropped inputs) to 40 lines, then stops
    from fakegame import FakeTetrio
    from tetrisbot.controller import Bot
    from tetrisbot.handling import Handling

    planner.configure(safe=False, gravity_rps=0)
    fake = FakeTetrio(seed=8, latency_ms=40, clear_delay_ms=150, drop_rate=0.05)
    fake.limit = 200
    logs = []
    bot = Bot({"settle_ms": 0}, log=logs.append, handling=Handling(mode="SPRINT", sprint_preview=5))
    bot.autoplay = True
    bot.screen = bot.kb = fake
    bot.set_handling(bot.h)
    bot.start()
    t = time.time()
    while time.time() - t < 120 and bot.running() and not any("40 lines" in m for m in logs):
        time.sleep(0.05)
    bot.stop()
    bot.thread.join(5)
    bot.lookahead.close()
    done = [m for m in logs if "40 lines" in m]
    assert done, logs[-10:]
    assert int(done[0].split(": ")[1].split()[0]) >= 9           # tetrises
    assert not any("resyncing" in m for m in logs), [m for m in logs if "sync" in m]


def test_sprint_tetris_when_ready_and_i_not_burnt():
    from tetrisbot import sprint
    ready = core.Board.from_strings(["######.###"] * 4)
    st, _, lines = sprint.plan(ready, "I", None, list("TLJOS"))[0]
    assert lines == 4 and all(x == sprint.WELL for x, _ in st.pl.cells)
    # only 2 rows ready: the I is held (kept in reserve), not burnt in the well
    low = core.Board.from_strings(["######.###"] * 2)
    st, _, lines = sprint.plan(low, "I", None, list("TLJOS"))[0]
    assert lines == 0 and not any(x == sprint.WELL for x, _ in st.pl.cells)


def test_sprint_display_marks_piece_in_play_and_order():
    from tetrisbot import sprint
    b = core.Board.from_strings(["###...####"])
    steps = sprint.plan(b, "T", None, list("OLJSZ"))
    d = sprint.display(b, steps, 0)
    assert d["well"] == sprint.WELL and d["title"].endswith("40 lines to go")
    n = len(d["rows"])
    for j, i in d["hint"]:                      # outlined = the piece in play, in colour
        assert d["rows"][j][i] == steps[0][0].pl.piece
    assert len(d["hint"]) == 4
    assert [t for _, _, t in d["labels"]] == [str(k + 2) for k in range(len(d["labels"]))]
    assert all(row[i] == "G" for i in range(3) for row in d["rows"][n - 1:])


def test_sprint_coach_follows_the_screen():
    # the user plays the advice on the fake TETR.IO screen; the sprint coach counts every
    # lock, line and tetris through the same Watcher as the Blitz advisor
    from fakegame import FakeTetrio
    from tetrisbot import sprint
    from tetrisbot.coach import Watcher

    planner.configure(safe=False, gravity_rps=0)
    fake = FakeTetrio(seed=3, banner_s=0.3, clear_delay_ms=150, latency_ms=40)
    geo = vision.locate(fake.full())
    box = geo.bounds()
    lgeo = vision.Geometry(geo.left - box[0], geo.top - box[1], geo.cw, geo.ch)
    logs = []
    coach = sprint.SprintCoach(log=logs.append)
    w = Watcher(coach, logs.append)
    g = fake.game
    lines = 0
    for _ in range(30):
        w.poll(fake.grab(box), lgeo)
        step = sprint.plan(g.board, g.current, g.hold, g.visible())[0][0]
        lines += len(g.board.copy().place_cells(step.pl.cells))
        for k in step.keys():
            fake.press(k)
            w.poll(fake.grab(box), lgeo)
        t = time.time()
        while time.time() - t < 0.2:
            w.poll(fake.grab(box), lgeo)
            time.sleep(0.01)
    assert coach.pieces == fake.pieces == 30, logs
    assert not any("re-reading" in m for m in logs), logs
    assert coach.followed == coach.suggested == 30
    assert coach.lines == lines and coach.tetrises >= 1


def test_sprint_mode_switch_uses_sprint_coach():
    from dataclasses import replace
    from tetrisbot.controller import Bot
    from tetrisbot.handling import Handling
    from tetrisbot.sprint import SprintCoach
    bot = Bot(log=lambda *a: None, handling=Handling(mode="BLITZ"))
    bot.autoplay = True
    bot.set_handling(replace(bot.h, mode="SPRINT"))
    assert bot.sprint()
    bot.coach = SprintCoach(log=lambda *a: None)
    s = bot.status()
    assert s["sprint"] and s["lines"] == 0 and s["advice"] == "waiting for a game"
    bot.set_handling(replace(bot.h, mode="BLITZ"))
    assert "sprint" not in bot.status()


def test_controls_from_settings(tmp_path):
    """Key bindings come from settings.json, bad names fall back to TETR.IO's defaults,
    and the keyboard picks up changed bindings with new handling settings."""
    import json
    from dataclasses import replace
    from tetrisbot.handling import Handling
    from tetrisbot.keys import KEYCODES, Keyboard
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({"bind_left": "j", "bind_hold": "lshift", "bind_cw": "nope"}))
    h = Handling.load(str(p))
    b = h.bindings()
    assert b[core.LEFT] == "j" and b[core.HOLD] == "lshift"
    assert b[core.CW] == "up" and b[core.HARD] == "space"      # unknown name / not set -> default
    kb = Keyboard(h)
    assert kb.codes[core.DAS_LEFT] == kb.codes[core.LEFT] == KEYCODES["j"]
    kb.h = replace(h, bind_left="left", bind_right="d")
    assert kb.codes[core.DAS_LEFT] == KEYCODES["left"] and kb.codes[core.DAS_RIGHT] == KEYCODES["d"]

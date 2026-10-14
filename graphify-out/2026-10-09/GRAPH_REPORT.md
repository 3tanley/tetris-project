# Graph Report - Tetris Scripts  (2026-10-09)

## Corpus Check
- 26 files · ~98,506 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 3, .graphify-bak 1, .command 1)

## Summary
- 655 nodes · 1349 edges · 34 communities (24 shown, 10 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 79 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Brain
- vision.py
- Bot
- planner.py
- test_bot.py
- settings_ui.py
- generate
- Board
- FakeTetrio
- HandlingWindow
- templates.py
- brain.py
- fumen.py
- BagView
- TETR.IO Blitz bot (macOS)
- library
- Overlay
- fill_template
- _build
- run
- register
- Lookahead
- Step
- test_air_drops_are_real_placements
- dependencies
- app.py
- CLAUDE.md
- setup.sh
- controller.py
- movegen
- time
- rec
- _bottom_up

## God Nodes (most connected - your core abstractions)
1. `Brain` - 47 edges
2. `Bot` - 46 edges
3. `Board` - 32 edges
4. `FakeTetrio` - 26 edges
5. `HandlingWindow` - 24 edges
6. `Handling` - 23 edges
7. `library()` - 19 edges
8. `_run_fake()` - 18 edges
9. `generate()` - 18 edges
10. `Lookahead` - 16 edges

## Surprising Connections (you probably didn't know these)
- `test_wrong_piece_is_never_hard_dropped()` --uses--> `Bot`  [INFERRED]
  tests/test_bot.py → tetrisbot/controller.py
- `test_kicks_and_spawn()` --calls--> `Board`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/core.py
- `test_templates_chain()` --calls--> `Board`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/core.py
- `test_singleyou_dependency()` --calls--> `Board`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/core.py
- `test_singleyou_dependency()` --calls--> `openers()`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/templates.py

## Import Cycles
- None detected.

## Communities (34 total, 10 thin omitted)

### Community 0 - "Brain"
Cohesion: 0.05
Nodes (12): test_bag_counter(), test_extra_piece_tracking_picks_matching_dpc(), test_high_gravity_main_thread_stays_fast(), test_impossible_dpc_solution_scores_zero(), test_lookahead_plans_the_pc_during_the_tspin_setup(), test_recovers_into_the_loop_from_free_play(), test_sim_loop_runs_pc_loop(), BagTracker (+4 more)

### Community 1 - "vision.py"
Cohesion: 0.06
Nodes (28): test_hold_lock_is_read_from_screen(), test_live_screenshot_reads(), test_queue_colour_beats_a_broken_shape(), test_real_all_clear_frame_has_no_phantom_blocks(), test_vision_on_screenshot(), Screen, locate_once(), cell_color() (+20 more)

### Community 2 - "Bot"
Cohesion: 0.08
Nodes (4): _advance(), Bot, _floating_extras(), Keyboard

### Community 3 - "planner.py"
Cohesion: 0.24
Nodes (7): _after_cells(), _air_table(), _costs(), evaluate(), heuristic_move(), _Timeout, tucks()

### Community 4 - "test_bot.py"
Cohesion: 0.09
Nodes (16): _run_fake(), _sample_boards(), test_all_clear_banner_does_not_break_the_loop(), test_controller_end_to_end(), test_finesse_matches_guide(), test_ghost_check_fixes_dropped_inputs(), test_high_gravity_pipeline(), test_line_clear_delay_keeps_hold_and_moves() (+8 more)

### Community 5 - "settings_ui.py"
Cohesion: 0.09
Nodes (11): Box, Button, Check, _draw_text(), FlippedView, _font(), Label, _round_rect() (+3 more)

### Community 6 - "generate"
Cohesion: 0.09
Nodes (18): test_ground_paths_work_at_any_gravity(), test_kicks_and_spawn(), test_safe_mode_keys_gravity_independent(), test_tsd_spin_detected(), cells_of(), drop_cells(), generate(), coll() (+10 more)

### Community 10 - "templates.py"
Cohesion: 0.11
Nodes (11): _blocks(), criteria_status(), _dedupe(), _dpc_templates(), _find_tsd_slot(), _norm(), _parse_criteria(), shape_type() (+3 more)

### Community 11 - "brain.py"
Cohesion: 0.15
Nodes (3): _lookahead_job(), _plan_picture(), _rebase()

### Community 12 - "fumen.py"
Cohesion: 0.18
Nodes (6): _blocks(), _coord(), decode(), op_cells(), Page, _Reader

### Community 13 - "BagView"
Cohesion: 0.22
Nodes (3): BagView, _c(), DiagramView

### Community 14 - "TETR.IO Blitz bot (macOS)"
Cohesion: 0.14
Nodes (13): Bag counter and choosing the extra piece, Building from the bottom up, DPC: how it picks a setup and a solution, Handling window, How it works, Line clears, Planning ahead (Next window), Priority lists (piece dependencies) (+5 more)

### Community 15 - "library"
Cohesion: 0.22
Nodes (12): test_dpc_mirrors_match_four_lol_mirrored_view(), test_fourlol_sdpc_solutions_match_the_sdpc_residue(), test_ms2_second_bag_follows_the_piece_order(), test_prefers_o_next_to_the_i(), test_sdpc_tsd_holds_an_early_t_until_the_end(), test_templates_chain(), dpc(), dpc_solutions() (+4 more)

### Community 17 - "fill_template"
Cohesion: 0.15
Nodes (6): test_builds_bottom_up_even_if_it_needs_a_hold(), test_can_fill_agrees_with_fill_template(), test_singleyou_dependency(), fill_template(), bottom_up_costs(), TState

### Community 18 - "_build"
Cohesion: 0.12
Nodes (5): _build(), _partition(), _sdpc_pc_templates(), Slot, Template

### Community 19 - "run"
Cohesion: 0.28
Nodes (4): run(), on_hotkey(), _wait_modifiers_released(), main()

### Community 20 - "register"
Cohesion: 0.33
Nodes (4): _EventTypeSpec, _fourcc(), _HotKeyID, register()

### Community 22 - "Step"
Cohesion: 0.15
Nodes (8): _groups_ok(), rec(), _pc_solve(), rec(), _pocket_type(), _regions_ok(), Step, _types()

### Community 23 - "test_air_drops_are_real_placements"
Cohesion: 0.18
Nodes (7): test_air_drops_are_real_placements(), air_drops(), _air_ms(), _air_ok(), generate(), pc_solutions(), _pc_solutions()

### Community 24 - "dependencies"
Cohesion: 0.18
Nodes (8): test_order_conflicts_counts_pieces_that_must_wait(), test_priority_list_puts_split_pieces_last(), test_tspin_goes_last_in_every_setup(), _ancestors(), dependencies(), order_conflicts(), priority_groups(), priority_text()

### Community 29 - "controller.py"
Cohesion: 0.22
Nodes (4): _ghost_shapes(), screen_access_ok(), _state_of(), identify()

### Community 30 - "movegen"
Cohesion: 0.18
Nodes (4): as_background, background(), foreground_busy, movegen()

### Community 31 - "time"
Cohesion: 0.28
Nodes (4): test_two_pass_pc_finds_what_the_full_search_finds(), find_pc(), pc_heights(), pc_solve()

### Community 32 - "rec"
Cohesion: 0.22
Nodes (6): can_fill(), rec(), _choices(), rec(), order_feasible(), rec()

## Knowledge Gaps
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Brain` connect `Brain` to `Bot`, `test_bot.py`, `brain.py`, `library`, `core.py`, `controller.py`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `Bot` (e.g. with `test_wrong_piece_is_never_hard_dropped()` and `Brain`) actually correct?**
  _`Bot` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `Brain` be split into smaller, more focused modules?**
  _Cohesion score 0.05221518987341772 - nodes in this community are weakly interconnected._
- **Why does `Bot` connect `Bot` to `Brain`, `test_bot.py`, `run`, `Lookahead`, `app.py`, `controller.py`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `HandlingWindow` (e.g. with `Overlay` and `Handling`) actually correct?**
  _`HandlingWindow` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `vision.py` be split into smaller, more focused modules?**
  _Cohesion score 0.060814383923849816 - nodes in this community are weakly interconnected._
- **Why does `Handling` connect `test_bot.py` to `Bot`, `planner.py`, `settings_ui.py`, `HandlingWindow`, `run`, `controller.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
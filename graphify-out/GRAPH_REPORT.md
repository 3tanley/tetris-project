# Graph Report - Tetris Scripts  (2026-10-13)

## Corpus Check
- 31 files · ~115,525 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .command 1)

## Summary
- 893 nodes · 1938 edges · 47 communities (33 shown, 14 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 142 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `991c7105`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Brain
- vision.py
- Bot
- planner.py
- test_bot.py
- _round_rect
- generate
- Board
- FakeTetrio
- python_method
- templates.py
- Lookahead
- fumen.py
- controller.py
- tetris-project
- library
- Overlay
- Handling
- Template
- ._decide
- ._jaws_futures
- _build
- Step
- configure
- dependencies
- register
- train
- CLAUDE.md
- setup.sh
- BagTracker
- background
- pc_solve
- can_fill
- ._seq
- ._refresh_display
- _dpc_templates
- app.py
- .action_cost
- SetupPrior
- Coach
- run
- cells_of
- core.py
- test_extra_piece_tracking_picks_matching_dpc
- FlippedView
- _jigsaw_templates
- settings_ui.py

## God Nodes (most connected - your core abstractions)
1. `Brain` - 68 edges
2. `Bot` - 54 edges
3. `Handling` - 49 edges
4. `Board` - 37 edges
5. `Coach` - 30 edges
6. `FakeTetrio` - 29 edges
7. `Lookahead` - 29 edges
8. `library()` - 29 edges
9. `HandlingWindow` - 24 edges
10. `configure()` - 23 edges

## Surprising Connections (you probably didn't know these)
- `test_sim_loop_runs_pc_loop()` --calls--> `run()`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/sim.py
- `test_wrong_piece_is_never_hard_dropped()` --uses--> `Bot`  [INFERRED]
  tests/test_bot.py → tetrisbot/controller.py
- `test_dpc_plans_its_pc_only_near_the_end()` --uses--> `Brain`  [INFERRED]
  tests/test_bot.py → tetrisbot/brain.py
- `openers()` --calls--> `Handling`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/handling.py
- `test_kicks_and_spawn()` --calls--> `Board`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/core.py

## Import Cycles
- None detected.

## Communities (47 total, 14 thin omitted)

### Community 1 - "vision.py"
Cohesion: 0.06
Nodes (28): test_hold_lock_is_read_from_screen(), test_live_screenshot_reads(), test_queue_colour_beats_a_broken_shape(), test_real_all_clear_frame_has_no_phantom_blocks(), test_vision_on_screenshot(), screen_access_ok(), locate_once(), cell_color() (+20 more)

### Community 2 - "Bot"
Cohesion: 0.05
Nodes (9): test_advisor_mode_never_presses_keys(), test_high_gravity_pipeline(), test_no_false_high_gravity_without_gravity(), _advance(), Bot, restart(), _floating_extras(), Screen (+1 more)

### Community 3 - "planner.py"
Cohesion: 0.09
Nodes (19): _after_cells(), air_drops(), _air_ms(), _air_ok(), _air_table(), _bottom_up(), _choices(), _costs() (+11 more)

### Community 4 - "test_bot.py"
Cohesion: 0.13
Nodes (16): _follow(), openers(), _run_fake(), test_all_clear_banner_does_not_break_the_loop(), test_coach_agrees_with_the_bot_it_watches(), test_coach_recognises_the_users_opener(), test_coach_switches_to_a_setup_that_can_still_be_finished(), test_controller_end_to_end() (+8 more)

### Community 5 - "_round_rect"
Cohesion: 0.19
Nodes (5): Button, _draw_text(), _round_rect(), Seg, SliderCell

### Community 6 - "generate"
Cohesion: 0.15
Nodes (11): test_kicks_and_spawn(), test_tsd_spin_detected(), rank(), generate(), coll(), drop(), offer(), push() (+3 more)

### Community 7 - "Board"
Cohesion: 0.06
Nodes (20): _coach_replay(), test_builds_bottom_up_even_if_it_needs_a_hold(), test_can_fill_agrees_with_fill_template(), test_dpc_mirrors_match_four_lol_mirrored_view(), test_ground_paths_work_at_any_gravity(), test_ms2_second_bag_follows_the_piece_order(), test_prefers_o_next_to_the_i(), test_sdpc_tsd_holds_an_early_t_until_the_end() (+12 more)

### Community 8 - "FakeTetrio"
Cohesion: 0.09
Nodes (6): FakeTetrio, _recording_2320(), test_soft_drop_waits_for_the_slide(), test_watcher_follows_the_screen(), _same(), Watcher

### Community 9 - "python_method"
Cohesion: 0.11
Nodes (3): HandlingWindow, OpenerList, OpenersWindow

### Community 10 - "templates.py"
Cohesion: 0.10
Nodes (5): criteria_status(), _norm(), shape_type(), _wiki_templates(), _wiki_type()

### Community 11 - "Lookahead"
Cohesion: 0.12
Nodes (5): test_warm_up_covers_the_sz_dpc_and_stops_for_a_job(), Lookahead, warm_order(), warm_template(), rec()

### Community 12 - "fumen.py"
Cohesion: 0.17
Nodes (6): _blocks(), _coord(), decode(), op_cells(), Page, _Reader

### Community 13 - "controller.py"
Cohesion: 0.09
Nodes (6): enabled_openers(), opener_priority(), sibling_pool(), _slot_at(), _sleep(), share_of_kind()

### Community 14 - "tetris-project"
Cohesion: 0.10
Nodes (20): Advisor (BOT PLAYS off), Bag counter and choosing the extra piece, Building from the bottom up, DPC: how it picks a setup and a solution, Handling window, How it works, Jaws (ILSZ) → 2nd PC → DPC, Jigsaw PC loop (off by default) (+12 more)

### Community 15 - "library"
Cohesion: 0.12
Nodes (14): test_fourlol_sdpc_solutions_match_the_sdpc_residue(), test_jaws_and_second_pc_templates_clear_the_field(), test_jaws_is_the_fourlol_ilsz_data(), test_jigsaw_chain(), _dedupe(), library(), openers(), pc2_setups() (+6 more)

### Community 17 - "Handling"
Cohesion: 0.27
Nodes (3): test_mode_setting_round_trip(), test_openers_setting_round_trip(), Handling

### Community 21 - "_build"
Cohesion: 0.17
Nodes (7): _build(), _jaws_templates(), type_of(), _partition(), _pc2_templates(), _placements_in(), _sdpc_pc_templates()

### Community 22 - "Step"
Cohesion: 0.16
Nodes (7): _groups_ok(), rec(), rec(), _pocket_type(), _regions_ok(), Step, _types()

### Community 23 - "configure"
Cohesion: 0.20
Nodes (10): _opener_brain(), test_advisor_only_recognises_openers_that_are_switched_on(), test_dpc_plans_its_pc_only_near_the_end(), test_finesse_matches_guide(), test_jaws_only_at_a_clean_bag_start(), test_jigsaw_loop_runs(), test_opener_priority_order_drives_the_suggestion(), test_opener_toggles_and_failsafe() (+2 more)

### Community 24 - "dependencies"
Cohesion: 0.17
Nodes (9): test_order_conflicts_counts_pieces_that_must_wait(), test_priority_list_puts_split_pieces_last(), test_tspin_goes_last_in_every_setup(), _ancestors(), dependencies(), dpc_solutions(), order_conflicts(), priority_groups() (+1 more)

### Community 25 - "register"
Cohesion: 0.33
Nodes (4): _EventTypeSpec, _fourcc(), _HotKeyID, register()

### Community 26 - "train"
Cohesion: 0.26
Nodes (7): test_high_gravity_main_thread_stays_fast(), test_keys_per_piece_like_top_players(), test_lookahead_plans_the_pc_during_the_tspin_setup(), test_recovers_into_the_loop_from_free_play(), train(), Game, run()

### Community 30 - "background"
Cohesion: 0.20
Nodes (3): as_background, background(), foreground_busy

### Community 31 - "pc_solve"
Cohesion: 0.25
Nodes (4): find_pc(), pc_heights(), pc_solve(), _pc_solve()

### Community 34 - "._refresh_display"
Cohesion: 0.22
Nodes (3): test_bag_counter(), _jaws_field(), _plan_picture()

### Community 35 - "_dpc_templates"
Cohesion: 0.29
Nodes (4): _blocks(), _dpc_templates(), _find_tsd_slot(), _parse_criteria()

### Community 36 - "app.py"
Cohesion: 0.15
Nodes (3): BagView, _c(), DiagramView

### Community 39 - "Coach"
Cohesion: 0.10
Nodes (3): _rebase(), Coach, _plan_still_works()

### Community 40 - "run"
Cohesion: 0.24
Nodes (5): run(), on_hotkey(), _wait_modifiers_released(), accessibility_ok(), main()

### Community 41 - "cells_of"
Cohesion: 0.18
Nodes (11): _sample_boards(), test_20g_plans_skip_pointless_soft_drops(), test_air_drops_are_real_placements(), test_fit_placement_with_line_clear(), test_mirrored_tuck_uses_mirrored_rotations(), test_safe_mode_keys_gravity_independent(), test_sideways_moves_happen_before_the_soft_drop(), fit_placement() (+3 more)

### Community 42 - "core.py"
Cohesion: 0.12
Nodes (8): _ghost_shapes(), _state_of(), drop_cells(), identify(), kicks(), Placement, slide(), walk()

### Community 44 - "FlippedView"
Cohesion: 0.20
Nodes (4): Box, Check, FlippedView, Label

### Community 46 - "settings_ui.py"
Cohesion: 0.16
Nodes (5): _font(), OpenerRow, _sys_text(), _text(), _white()

## Knowledge Gaps
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Brain` connect `Brain` to `._seq`, `Bot`, `._refresh_display`, `test_bot.py`, `SetupPrior`, `Board`, `FakeTetrio`, `Coach`, `test_extra_piece_tracking_picks_matching_dpc`, `controller.py`, `._decide`, `._jaws_futures`, `configure`, `train`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Brain` (e.g. with `test_dpc_plans_its_pc_only_near_the_end()` and `Coach`) actually correct?**
  _`Brain` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `vision.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06253652834599649 - nodes in this community are weakly interconnected._
- **Why does `Bot` connect `Bot` to `Brain`, `test_bot.py`, `app.py`, `Coach`, `FakeTetrio`, `run`, `Lookahead`, `controller.py`, `Handling`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Bot` (e.g. with `test_wrong_piece_is_never_hard_dropped()` and `Brain`) actually correct?**
  _`Bot` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `Bot` be split into smaller, more focused modules?**
  _Cohesion score 0.051131354687040845 - nodes in this community are weakly interconnected._
- **Why does `Handling` connect `Handling` to `Bot`, `planner.py`, `test_bot.py`, `.action_cost`, `Board`, `FakeTetrio`, `cells_of`, `run`, `test_extra_piece_tracking_picks_matching_dpc`, `python_method`, `controller.py`, `settings_ui.py`, `._decide`, `configure`, `train`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
# Graph Report - Tetris Scripts  (2026-10-18)

## Corpus Check
- 32 files · ~145,923 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .command 1)

## Summary
- 1050 nodes · 2354 edges · 56 communities (37 shown, 19 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 183 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8a4d7723`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- vision.py
- Bot
- planner.py
- test_bot.py
- test_openers_setting_round_trip
- sprint.py
- Board
- FakeTetrio
- python_method
- templates.py
- .action_cost
- fumen.py
- Lookahead
- tetris-project
- library
- Overlay
- TState
- Template
- settings_ui.py
- ._confirm
- test_advisor_mode_never_presses_keys
- Step
- Keyboard
- dpc_solutions
- coach.py
- Game
- CLAUDE.md
- setup.sh
- BagTracker
- background
- locate
- fill_template
- ._chance
- generate
- Geometry
- locate_once
- test_live_screenshot_reads
- Handling
- Coach
- app.py
- __main__.py
- test_warm_up_covers_the_sz_dpc_and_stops_for_a_job
- heuristic_move
- register
- generate
- controller.py
- model.py
- test_all_pc_counts_the_loop_from_the_bag
- read_board_ex
- _classify_blob
- ._decide
- ._verify
- Brain
- test_all_pc_builds_setup_and_solution_together_when_needed

## God Nodes (most connected - your core abstractions)
1. `Brain` - 80 edges
2. `Bot` - 65 edges
3. `Handling` - 61 edges
4. `Board` - 44 edges
5. `configure()` - 32 edges
6. `FakeTetrio` - 31 edges
7. `Lookahead` - 31 edges
8. `library()` - 30 edges
9. `HandlingWindow` - 29 edges
10. `Coach` - 26 edges

## Surprising Connections (you probably didn't know these)
- `test_sim_loop_runs_pc_loop()` --calls--> `run()`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/sim.py
- `test_wrong_piece_is_never_hard_dropped()` --uses--> `Bot`  [INFERRED]
  tests/test_bot.py → tetrisbot/controller.py
- `test_dpc_plans_its_pc_only_near_the_end()` --uses--> `Brain`  [INFERRED]
  tests/test_bot.py → tetrisbot/brain.py
- `test_sprint_coach_follows_the_screen()` --uses--> `SprintCoach`  [INFERRED]
  tests/test_bot.py → tetrisbot/sprint.py
- `test_controls_from_settings()` --uses--> `Handling`  [INFERRED]
  tests/test_bot.py → tetrisbot/handling.py

## Import Cycles
- None detected.

## Communities (56 total, 19 thin omitted)

### Community 1 - "vision.py"
Cohesion: 0.24
Nodes (8): active_groups(), cell_color(), cell_state(), classify_color(), is_filled(), _patch(), read_ghost(), _same_hue()

### Community 2 - "Bot"
Cohesion: 0.18
Nodes (5): _recording_2320(), test_restart_is_noticed(), bot_on(), test_sprint_mode_switch_uses_sprint_coach(), Bot

### Community 3 - "planner.py"
Cohesion: 0.08
Nodes (20): air_drops(), _air_ms(), _air_ok(), _air_table(), _bottom_up(), _choices(), _costs(), find_pc() (+12 more)

### Community 4 - "test_bot.py"
Cohesion: 0.12
Nodes (17): _run_fake(), test_all_clear_banner_does_not_break_the_loop(), test_coach_agrees_with_the_bot_it_watches(), test_coach_recognises_the_users_opener(), test_coach_switches_to_a_setup_that_can_still_be_finished(), test_controller_end_to_end(), test_ghost_check_fixes_dropped_inputs(), test_kicks_are_mirror_images() (+9 more)

### Community 6 - "sprint.py"
Cohesion: 0.06
Nodes (20): test_sprint_display_marks_piece_in_play_and_order(), test_sprint_display_shows_preview_pieces(), test_sprint_right_side_patterns(), test_sprint_tetris_when_ready_and_i_not_burnt(), align(), depth_for(), display(), evaluate() (+12 more)

### Community 7 - "Board"
Cohesion: 0.12
Nodes (9): test_dpc_mirrors_match_four_lol_mirrored_view(), test_ms2_second_bag_follows_the_piece_order(), test_prefers_o_next_to_the_i(), test_sdpc_tsd_holds_an_early_t_until_the_end(), test_templates_chain(), test_two_pass_pc_finds_what_the_full_search_finds(), Board, dpc() (+1 more)

### Community 8 - "FakeTetrio"
Cohesion: 0.08
Nodes (7): FakeTetrio, _Events, test_sprint_coach_follows_the_screen(), test_watcher_explains_a_piece_tucked_under_the_last_one(), test_watcher_follows_the_screen(), _tuck_frames(), Watcher

### Community 9 - "python_method"
Cohesion: 0.09
Nodes (3): HandlingWindow, OpenerList, OpenersWindow

### Community 10 - "templates.py"
Cohesion: 0.06
Nodes (18): _blocks(), _build(), criteria_status(), _dpc_templates(), _jaws_templates(), type_of(), _jig_rows(), _jigsaw_templates() (+10 more)

### Community 12 - "fumen.py"
Cohesion: 0.10
Nodes (9): BagView, _c(), DiagramView, _blocks(), _coord(), decode(), op_cells(), Page (+1 more)

### Community 14 - "tetris-project"
Cohesion: 0.08
Nodes (24): Advisor (BOT PLAYS off), ALL PC, Bag counter and choosing the extra piece, Building from the bottom up, Controls, DPC: how it picks a setup and a solution, Handling window, How it works (+16 more)

### Community 15 - "library"
Cohesion: 0.13
Nodes (13): test_fourlol_sdpc_solutions_match_the_sdpc_residue(), test_jaws_and_second_pc_templates_clear_the_field(), test_jaws_is_the_fourlol_ilsz_data(), test_jigsaw_chain(), test_seventh_pc_solutions_from_four_lol(), _dedupe(), library(), pc2_setups() (+5 more)

### Community 17 - "TState"
Cohesion: 0.10
Nodes (8): test_can_fill_agrees_with_fill_template(), test_order_conflicts_counts_pieces_that_must_wait(), can_fill(), rec(), _ancestors(), dependencies(), order_conflicts(), TState

### Community 18 - "Template"
Cohesion: 0.14
Nodes (4): pc2_solutions(), pc_full(), Slot, Template

### Community 19 - "settings_ui.py"
Cohesion: 0.10
Nodes (14): Box, Button, Check, _draw_text(), FlippedView, _font(), Label, OpenerRow (+6 more)

### Community 21 - "test_advisor_mode_never_presses_keys"
Cohesion: 0.24
Nodes (5): test_advisor_mode_never_presses_keys(), test_high_gravity_pipeline(), test_no_false_high_gravity_without_gravity(), test_sprint_bot_plays_40_lines(), restart()

### Community 22 - "Step"
Cohesion: 0.16
Nodes (7): _groups_ok(), rec(), rec(), _pocket_type(), _regions_ok(), Step, _types()

### Community 24 - "dpc_solutions"
Cohesion: 0.33
Nodes (5): test_priority_list_puts_split_pieces_last(), test_tspin_goes_last_in_every_setup(), dpc_solutions(), priority_groups(), priority_text()

### Community 25 - "coach.py"
Cohesion: 0.15
Nodes (5): all_pc(), enabled_openers(), opener_priority(), _rebase(), sibling_pool()

### Community 26 - "Game"
Cohesion: 0.15
Nodes (13): _follow(), test_all_pc_keeps_clearing(), test_extra_piece_tracking_picks_matching_dpc(), test_high_gravity_main_thread_stays_fast(), test_jigsaw_takes_the_pc_in_view_before_stacking_for_the_next(), test_keys_per_piece_like_top_players(), test_lookahead_plans_the_pc_during_the_tspin_setup(), test_opener_priority_order_drives_the_suggestion() (+5 more)

### Community 30 - "background"
Cohesion: 0.20
Nodes (3): as_background, background(), foreground_busy

### Community 31 - "locate"
Cohesion: 0.17
Nodes (7): test_real_all_clear_frame_has_no_phantom_blocks(), test_zen_queue_is_read_inside_its_panel(), locate(), _locate_left_only(), _longest_runs(), _next_panel(), read_active()

### Community 32 - "fill_template"
Cohesion: 0.25
Nodes (7): test_builds_bottom_up_even_if_it_needs_a_hold(), test_singleyou_dependency(), _lookahead_job(), fill_template(), bottom_up_costs(), rec(), openers()

### Community 34 - "generate"
Cohesion: 0.06
Nodes (28): test_fit_placement_ignores_a_piece_in_the_air(), test_fit_placement_with_line_clear(), test_ground_paths_work_at_any_gravity(), test_kicks_and_spawn(), test_safe_mode_keys_gravity_independent(), test_tsd_spin_detected(), rank(), fit_placement() (+20 more)

### Community 37 - "test_live_screenshot_reads"
Cohesion: 0.24
Nodes (8): test_hold_lock_is_read_from_screen(), test_live_screenshot_reads(), test_vision_on_screenshot(), hold_locked(), piece_pixels(), _pieces_in_box(), read_hold(), read_queue()

### Community 38 - "Handling"
Cohesion: 0.20
Nodes (10): openers(), _opener_brain(), test_advisor_only_recognises_openers_that_are_switched_on(), test_advisor_shows_the_only_opener_switched_on(), test_dpc_plans_its_pc_only_near_the_end(), test_jaws_only_at_a_clean_bag_start(), test_jigsaw_loop_runs(), test_opener_toggles_and_failsafe() (+2 more)

### Community 39 - "Coach"
Cohesion: 0.06
Nodes (8): _coach_replay(), test_all_pc_never_goes_to_the_dpc(), test_setup_prior_learns_from_the_user(), Coach, Events, _plan_still_works(), _slot_at(), SetupPrior

### Community 40 - "app.py"
Cohesion: 0.16
Nodes (5): file_logger(), run(), on_hotkey(), _wait_modifiers_released(), accessibility_ok()

### Community 41 - "__main__.py"
Cohesion: 0.25
Nodes (3): test_controls_from_settings(), test_mode_setting_round_trip(), main()

### Community 42 - "test_warm_up_covers_the_sz_dpc_and_stops_for_a_job"
Cohesion: 0.29
Nodes (4): test_warm_up_covers_the_sz_dpc_and_stops_for_a_job(), warm_order(), warm_template(), rec()

### Community 43 - "heuristic_move"
Cohesion: 0.29
Nodes (5): drop_cells(), _after_cells(), evaluate(), heuristic_move(), holes_covered()

### Community 44 - "register"
Cohesion: 0.33
Nodes (4): _EventTypeSpec, _fourcc(), _HotKeyID, register()

### Community 45 - "generate"
Cohesion: 0.20
Nodes (8): _sample_boards(), test_20g_plans_skip_pointless_soft_drops(), test_air_drops_are_real_placements(), test_finesse_matches_guide(), test_mirrored_tuck_uses_mirrored_rotations(), test_sideways_moves_happen_before_the_soft_drop(), generate(), movegen()

### Community 46 - "controller.py"
Cohesion: 0.11
Nodes (4): _jaws_field(), _plan_picture(), screen_access_ok(), _sleep()

### Community 49 - "read_board_ex"
Cohesion: 0.33
Nodes (3): test_40_lines_number_behind_the_field_reads_as_empty(), read_board(), read_board_ex()

### Community 50 - "_classify_blob"
Cohesion: 0.40
Nodes (3): test_queue_colour_beats_a_broken_shape(), _classify_blob(), preview_colour_class()

### Community 54 - "Brain"
Cohesion: 0.08
Nodes (6): test_bag_counter(), test_jaws_build_rate_over_every_bag_order(), count(), test_second_pc_scans_every_pattern(), Brain, ok()

## Knowledge Gaps
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Bot` connect `Bot` to `._play_one_game`, `test_bot.py`, `Handling`, `Coach`, `app.py`, `FakeTetrio`, `sprint.py`, `Lookahead`, `controller.py`, `._confirm`, `test_advisor_mode_never_presses_keys`, `Brain`, `._update_safe`, `Keyboard`, `._verify`?**
  _High betweenness centrality (0.163) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Brain` (e.g. with `test_dpc_plans_its_pc_only_near_the_end()` and `test_tucked_piece_that_locks_while_planning_is_not_slammed()`) actually correct?**
  _`Brain` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `planner.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07807807807807808 - nodes in this community are weakly interconnected._
- **Why does `Brain` connect `Brain` to `._play_one_game`, `._chance`, `Bot`, `test_bot.py`, `Handling`, `Coach`, `Board`, `FakeTetrio`, `Lookahead`, `controller.py`, `model.py`, `test_all_pc_counts_the_loop_from_the_bag`, `._decide`, `test_advisor_mode_never_presses_keys`, `test_all_pc_builds_setup_and_solution_together_when_needed`, `coach.py`, `Game`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Bot` (e.g. with `test_wrong_piece_is_never_hard_dropped()` and `Brain`) actually correct?**
  _`Bot` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_bot.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11956521739130435 - nodes in this community are weakly interconnected._
- **Why does `Handling` connect `Handling` to `Bot`, `planner.py`, `test_bot.py`, `test_openers_setting_round_trip`, `Coach`, `__main__.py`, `python_method`, `.action_cost`, `generate`, `controller.py`, `model.py`, `test_all_pc_counts_the_loop_from_the_bag`, `settings_ui.py`, `test_advisor_mode_never_presses_keys`, `Brain`, `test_all_pc_builds_setup_and_solution_together_when_needed`, `Game`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
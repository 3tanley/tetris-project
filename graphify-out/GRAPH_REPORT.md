# Graph Report - Tetris Scripts  (2026-10-19)

## Corpus Check
- 32 files · ~146,130 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .command 1)

## Summary
- 1051 nodes · 2360 edges · 63 communities (43 shown, 20 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 183 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `57e3338f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ._play_one_game
- vision.py
- Bot
- planner.py
- test_bot.py
- .load
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
- test_advisor_mode_never_presses_keys
- Step
- Keyboard
- priority_groups
- brain.py
- Game
- CLAUDE.md
- setup.sh
- BagTracker
- background
- cells_of
- fill_template
- ._chance
- generate
- core.py
- Screen
- ._refresh_display
- Handling
- coach.py
- app.py
- sim.py
- dependencies
- heuristic_move
- register
- ._select
- controller.py
- _build
- Brain
- Watcher
- test_ms2_second_bag_follows_the_piece_order
- ._future
- BagView
- _dpc_templates
- ._dpc_outlook
- test_all_pc_never_goes_to_the_dpc
- pc_solve
- _choices
- _Events
- _Timeout
- _bottom_up
- Placement

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
- `test_wrong_piece_is_never_hard_dropped()` --uses--> `Bot`  [INFERRED]
  tests/test_bot.py → tetrisbot/controller.py
- `test_dpc_plans_its_pc_only_near_the_end()` --uses--> `Brain`  [INFERRED]
  tests/test_bot.py → tetrisbot/brain.py
- `openers()` --calls--> `Handling`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/handling.py
- `test_sprint_coach_follows_the_screen()` --uses--> `SprintCoach`  [INFERRED]
  tests/test_bot.py → tetrisbot/sprint.py
- `test_controls_from_settings()` --uses--> `Handling`  [INFERRED]
  tests/test_bot.py → tetrisbot/handling.py

## Import Cycles
- None detected.

## Communities (63 total, 20 thin omitted)

### Community 1 - "vision.py"
Cohesion: 0.06
Nodes (31): test_hold_lock_is_read_from_screen(), test_live_screenshot_reads(), test_queue_colour_beats_a_broken_shape(), test_real_all_clear_frame_has_no_phantom_blocks(), test_vision_on_screenshot(), test_warm_up_does_not_starve_the_bot_thread(), test_zen_queue_is_read_inside_its_panel(), locate_once() (+23 more)

### Community 2 - "Bot"
Cohesion: 0.15
Nodes (4): test_restart_is_noticed(), bot_on(), test_sprint_mode_switch_uses_sprint_coach(), Bot

### Community 3 - "planner.py"
Cohesion: 0.17
Nodes (12): test_air_drops_are_real_placements(), air_drops(), _air_ms(), _air_ok(), _air_table(), _costs(), generate(), _gravity_step() (+4 more)

### Community 4 - "test_bot.py"
Cohesion: 0.12
Nodes (18): _follow(), openers(), _run_fake(), test_all_clear_banner_does_not_break_the_loop(), test_coach_agrees_with_the_bot_it_watches(), test_coach_recognises_the_users_opener(), test_coach_switches_to_a_setup_that_can_still_be_finished(), test_controller_end_to_end() (+10 more)

### Community 5 - ".load"
Cohesion: 0.18
Nodes (3): test_controls_from_settings(), test_mode_setting_round_trip(), test_openers_setting_round_trip()

### Community 6 - "sprint.py"
Cohesion: 0.06
Nodes (19): test_sprint_display_marks_piece_in_play_and_order(), test_sprint_display_shows_preview_pieces(), test_sprint_tetris_when_ready_and_i_not_burnt(), drop_cells(), align(), depth_for(), display(), evaluate() (+11 more)

### Community 7 - "Board"
Cohesion: 0.13
Nodes (3): test_ground_paths_work_at_any_gravity(), test_kicks_and_spawn(), Board

### Community 8 - "FakeTetrio"
Cohesion: 0.16
Nodes (3): FakeTetrio, test_sprint_coach_follows_the_screen(), test_watcher_follows_the_screen()

### Community 9 - "python_method"
Cohesion: 0.09
Nodes (3): HandlingWindow, OpenerList, OpenersWindow

### Community 10 - "templates.py"
Cohesion: 0.09
Nodes (7): criteria_status(), _jig_rows(), _jigsaw_templates(), _norm(), shape_type(), _wiki_templates(), _wiki_type()

### Community 12 - "fumen.py"
Cohesion: 0.18
Nodes (6): _blocks(), _coord(), decode(), op_cells(), Page, _Reader

### Community 14 - "tetris-project"
Cohesion: 0.08
Nodes (24): Advisor (BOT PLAYS off), ALL PC, Bag counter and choosing the extra piece, Building from the bottom up, Controls, DPC: how it picks a setup and a solution, Handling window, How it works (+16 more)

### Community 15 - "library"
Cohesion: 0.12
Nodes (17): test_dpc_mirrors_match_four_lol_mirrored_view(), test_fourlol_sdpc_solutions_match_the_sdpc_residue(), test_jaws_and_second_pc_templates_clear_the_field(), test_jaws_is_the_fourlol_ilsz_data(), test_jigsaw_chain(), test_seventh_pc_solutions_from_four_lol(), test_warm_up_covers_the_sz_dpc_and_stops_for_a_job(), _dedupe() (+9 more)

### Community 17 - "TState"
Cohesion: 0.13
Nodes (5): test_can_fill_agrees_with_fill_template(), test_order_conflicts_counts_pieces_that_must_wait(), test_singleyou_dependency(), order_conflicts(), TState

### Community 18 - "Template"
Cohesion: 0.14
Nodes (4): pc2_solutions(), pc_full(), Slot, Template

### Community 19 - "settings_ui.py"
Cohesion: 0.09
Nodes (14): Box, Button, Check, _draw_text(), FlippedView, _font(), Label, OpenerRow (+6 more)

### Community 21 - "test_advisor_mode_never_presses_keys"
Cohesion: 0.24
Nodes (5): test_advisor_mode_never_presses_keys(), test_high_gravity_pipeline(), test_no_false_high_gravity_without_gravity(), test_sprint_bot_plays_40_lines(), restart()

### Community 22 - "Step"
Cohesion: 0.15
Nodes (8): _groups_ok(), rec(), _pc_solve(), rec(), _pocket_type(), _regions_ok(), Step, _types()

### Community 24 - "priority_groups"
Cohesion: 0.40
Nodes (4): test_priority_list_puts_split_pieces_last(), test_tspin_goes_last_in_every_setup(), priority_groups(), priority_text()

### Community 25 - "brain.py"
Cohesion: 0.16
Nodes (5): all_pc(), ok(), enabled_openers(), opener_priority(), openers()

### Community 26 - "Game"
Cohesion: 0.20
Nodes (11): test_all_pc_keeps_clearing(), test_extra_piece_tracking_picks_matching_dpc(), test_high_gravity_main_thread_stays_fast(), test_jigsaw_takes_the_pc_in_view_before_stacking_for_the_next(), test_keys_per_piece_like_top_players(), test_lookahead_plans_the_pc_during_the_tspin_setup(), test_recovers_into_the_loop_from_free_play(), test_sprint_63_advice_scores_tetrises() (+3 more)

### Community 30 - "background"
Cohesion: 0.20
Nodes (3): as_background, background(), foreground_busy

### Community 31 - "cells_of"
Cohesion: 0.17
Nodes (9): test_fit_placement_ignores_a_piece_in_the_air(), test_fit_placement_with_line_clear(), fit_placement(), _resting(), _ghost_shapes(), _state_of(), cells_of(), identify() (+1 more)

### Community 32 - "fill_template"
Cohesion: 0.47
Nodes (5): test_builds_bottom_up_even_if_it_needs_a_hold(), fill_template(), bottom_up_costs(), leaf_viable(), rec()

### Community 34 - "generate"
Cohesion: 0.15
Nodes (11): test_tsd_spin_detected(), rank(), generate(), coll(), drop(), offer(), push(), sld() (+3 more)

### Community 35 - "core.py"
Cohesion: 0.21
Nodes (5): test_safe_mode_keys_gravity_independent(), kicks(), slide(), walk(), replay()

### Community 37 - "._refresh_display"
Cohesion: 0.18
Nodes (3): test_bag_counter(), _jaws_field(), _plan_picture()

### Community 38 - "Handling"
Cohesion: 0.13
Nodes (17): _opener_brain(), _recording_2320(), _sample_boards(), test_20g_plans_skip_pointless_soft_drops(), test_advisor_only_recognises_openers_that_are_switched_on(), test_advisor_shows_the_only_opener_switched_on(), test_finesse_matches_guide(), test_jaws_build_rate_over_every_bag_order() (+9 more)

### Community 39 - "coach.py"
Cohesion: 0.05
Nodes (8): _coach_replay(), test_setup_prior_learns_from_the_user(), Coach, Events, _plan_still_works(), _slot_at(), SetupPrior, share_of_kind()

### Community 40 - "app.py"
Cohesion: 0.15
Nodes (6): file_logger(), run(), on_hotkey(), _wait_modifiers_released(), screen_access_ok(), accessibility_ok()

### Community 41 - "sim.py"
Cohesion: 0.20
Nodes (5): test_dpc_plans_its_pc_only_near_the_end(), test_jigsaw_loop_runs(), test_sim_loop_runs_pc_loop(), main(), run()

### Community 42 - "dependencies"
Cohesion: 0.33
Nodes (4): warm_template(), rec(), _ancestors(), dependencies()

### Community 43 - "heuristic_move"
Cohesion: 0.40
Nodes (4): _after_cells(), evaluate(), heuristic_move(), holes_covered()

### Community 44 - "register"
Cohesion: 0.33
Nodes (4): _EventTypeSpec, _fourcc(), _HotKeyID, register()

### Community 47 - "_build"
Cohesion: 0.20
Nodes (6): _build(), _jaws_templates(), type_of(), _partition(), _placements_in(), _sdpc_pc_templates()

### Community 48 - "Brain"
Cohesion: 0.14
Nodes (3): test_all_pc_counts_the_loop_from_the_bag(), test_impossible_dpc_solution_scores_zero(), Brain

### Community 49 - "Watcher"
Cohesion: 0.15
Nodes (5): test_40_lines_number_behind_the_field_reads_as_empty(), test_watcher_explains_a_piece_tucked_under_the_last_one(), _tuck_frames(), _same(), Watcher

### Community 50 - "test_ms2_second_bag_follows_the_piece_order"
Cohesion: 0.33
Nodes (5): test_ms2_second_bag_follows_the_piece_order(), test_prefers_o_next_to_the_i(), test_sdpc_tsd_holds_an_early_t_until_the_end(), test_templates_chain(), second_bag()

### Community 52 - "BagView"
Cohesion: 0.22
Nodes (3): BagView, _c(), DiagramView

### Community 53 - "_dpc_templates"
Cohesion: 0.22
Nodes (5): _blocks(), _dpc_templates(), _parse_criteria(), _pc_templates(), _ungrey()

### Community 55 - "test_all_pc_never_goes_to_the_dpc"
Cohesion: 0.29
Nodes (4): _pc_brain(), test_all_pc_builds_setup_and_solution_together_when_needed(), test_all_pc_never_goes_to_the_dpc(), sibling_pool()

### Community 56 - "pc_solve"
Cohesion: 0.25
Nodes (4): test_two_pass_pc_finds_what_the_full_search_finds(), find_pc(), pc_heights(), pc_solve()

### Community 57 - "_choices"
Cohesion: 0.25
Nodes (5): can_fill(), rec(), _choices(), order_feasible(), rec()

## Knowledge Gaps
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Brain` connect `Brain` to `._play_one_game`, `Bot`, `test_bot.py`, `FakeTetrio`, `test_advisor_mode_never_presses_keys`, `brain.py`, `Game`, `._chance`, `Screen`, `._refresh_display`, `Handling`, `coach.py`, `sim.py`, `._select`, `controller.py`, `test_ms2_second_bag_follows_the_piece_order`, `._future`, `._dpc_outlook`, `test_all_pc_never_goes_to_the_dpc`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Brain` (e.g. with `test_dpc_plans_its_pc_only_near_the_end()` and `test_tucked_piece_that_locks_while_planning_is_not_slammed()`) actually correct?**
  _`Brain` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `vision.py` be split into smaller, more focused modules?**
  _Cohesion score 0.057539682539682536 - nodes in this community are weakly interconnected._
- **Why does `Bot` connect `Bot` to `._play_one_game`, `test_bot.py`, `Screen`, `Handling`, `coach.py`, `app.py`, `sprint.py`, `Lookahead`, `controller.py`, `Brain`, `Watcher`, `._confirm`, `test_advisor_mode_never_presses_keys`, `Keyboard`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Bot` (e.g. with `test_wrong_piece_is_never_hard_dropped()` and `Brain`) actually correct?**
  _`Bot` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `Bot` be split into smaller, more focused modules?**
  _Cohesion score 0.14761904761904762 - nodes in this community are weakly interconnected._
- **Why does `Handling` connect `Handling` to `Bot`, `planner.py`, `test_bot.py`, `.load`, `coach.py`, `sim.py`, `python_method`, `.action_cost`, `controller.py`, `Brain`, `settings_ui.py`, `test_advisor_mode_never_presses_keys`, `test_all_pc_never_goes_to_the_dpc`, `Game`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
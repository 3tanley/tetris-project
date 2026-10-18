# Graph Report - Tetris Scripts  (2026-10-18)

## Corpus Check
- 32 files · ~124,604 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .command 1)

## Summary
- 1002 nodes · 2234 edges · 55 communities (39 shown, 16 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 172 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `112adfb2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Brain
- vision.py
- plan
- planner.py
- test_bot.py
- .__init__
- sprint.py
- Board
- FakeTetrio
- python_method
- templates.py
- test_watcher_follows_the_screen
- fumen.py
- brain.py
- tetris-project
- library
- Overlay
- TState
- Template
- settings_ui.py
- ._chance
- _build
- Step
- Bot
- dpc_solutions
- register
- Lookahead
- CLAUDE.md
- setup.sh
- BagTracker
- background
- pc_solve
- _choices
- ._decide
- dependencies
- _dpc_templates
- BagView
- .action_cost
- Handling
- Coach
- Events
- test_advisor_mode_never_presses_keys
- generate
- ._select
- identify
- cells_of
- controller.py
- SprintCoach
- core.py
- coach.py
- SprintBrain
- test_all_pc_counts_the_loop_from_the_bag
- fill_template
- heuristic_move
- ._jaws_build_sides

## God Nodes (most connected - your core abstractions)
1. `Brain` - 76 edges
2. `Bot` - 62 edges
3. `Handling` - 58 edges
4. `Board` - 38 edges
5. `FakeTetrio` - 31 edges
6. `Lookahead` - 31 edges
7. `configure()` - 29 edges
8. `HandlingWindow` - 29 edges
9. `library()` - 29 edges
10. `Coach` - 24 edges

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

## Communities (55 total, 16 thin omitted)

### Community 0 - "Brain"
Cohesion: 0.11
Nodes (3): test_bag_counter(), Brain, _lookahead_job()

### Community 1 - "vision.py"
Cohesion: 0.07
Nodes (27): test_hold_lock_is_read_from_screen(), test_live_screenshot_reads(), test_queue_colour_beats_a_broken_shape(), test_real_all_clear_frame_has_no_phantom_blocks(), test_vision_on_screenshot(), locate_once(), cell_color(), cell_state() (+19 more)

### Community 2 - "plan"
Cohesion: 0.18
Nodes (8): test_sprint_display_marks_piece_in_play_and_order(), test_sprint_display_shows_preview_pieces(), test_sprint_tetris_when_ready_and_i_not_burnt(), drop_cells(), depth_for(), display(), plan(), reward()

### Community 3 - "planner.py"
Cohesion: 0.13
Nodes (14): test_air_drops_are_real_placements(), air_drops(), _air_ms(), _air_ok(), _air_table(), _costs(), generate(), _gravity_step() (+6 more)

### Community 4 - "test_bot.py"
Cohesion: 0.19
Nodes (10): _run_fake(), test_all_clear_banner_does_not_break_the_loop(), test_controller_end_to_end(), test_ghost_check_fixes_dropped_inputs(), test_kicks_are_mirror_images(), test_line_clear_delay_keeps_hold_and_moves(), test_screen_lag_no_false_corrections(), test_screen_lag_with_dropped_inputs() (+2 more)

### Community 5 - ".__init__"
Cohesion: 0.16
Nodes (3): test_controls_from_settings(), test_mode_setting_round_trip(), test_openers_setting_round_trip()

### Community 6 - "sprint.py"
Cohesion: 0.17
Nodes (7): align(), evaluate(), _fits(), Node, ready_rows(), right_blocks(), _windows()

### Community 7 - "Board"
Cohesion: 0.11
Nodes (9): test_dpc_mirrors_match_four_lol_mirrored_view(), test_ground_paths_work_at_any_gravity(), test_ms2_second_bag_follows_the_piece_order(), test_prefers_o_next_to_the_i(), test_sdpc_tsd_holds_an_early_t_until_the_end(), test_templates_chain(), Board, openers() (+1 more)

### Community 9 - "python_method"
Cohesion: 0.09
Nodes (3): HandlingWindow, OpenerList, OpenersWindow

### Community 10 - "templates.py"
Cohesion: 0.08
Nodes (7): criteria_status(), _jig_rows(), _jigsaw_templates(), _norm(), shape_type(), _wiki_templates(), _wiki_type()

### Community 11 - "test_watcher_follows_the_screen"
Cohesion: 0.23
Nodes (3): test_sprint_coach_follows_the_screen(), test_watcher_follows_the_screen(), Watcher

### Community 12 - "fumen.py"
Cohesion: 0.18
Nodes (6): _blocks(), _coord(), decode(), op_cells(), Page, _Reader

### Community 13 - "brain.py"
Cohesion: 0.11
Nodes (7): all_pc(), enabled_openers(), _jaws_field(), opener_priority(), _plan_picture(), _rebase(), sibling_pool()

### Community 14 - "tetris-project"
Cohesion: 0.08
Nodes (24): Advisor (BOT PLAYS off), ALL PC, Bag counter and choosing the extra piece, Building from the bottom up, Controls, DPC: how it picks a setup and a solution, Handling window, How it works (+16 more)

### Community 15 - "library"
Cohesion: 0.10
Nodes (17): test_fourlol_sdpc_solutions_match_the_sdpc_residue(), test_jaws_and_second_pc_templates_clear_the_field(), test_jaws_is_the_fourlol_ilsz_data(), test_jigsaw_chain(), test_order_conflicts_counts_pieces_that_must_wait(), test_warm_up_covers_the_sz_dpc_and_stops_for_a_job(), _dedupe(), dpc() (+9 more)

### Community 17 - "TState"
Cohesion: 0.17
Nodes (3): test_can_fill_agrees_with_fill_template(), test_singleyou_dependency(), TState

### Community 19 - "settings_ui.py"
Cohesion: 0.09
Nodes (14): Box, Button, Check, _draw_text(), FlippedView, _font(), Label, OpenerRow (+6 more)

### Community 21 - "_build"
Cohesion: 0.20
Nodes (6): _build(), _jaws_templates(), type_of(), _partition(), _placements_in(), _sdpc_pc_templates()

### Community 22 - "Step"
Cohesion: 0.13
Nodes (9): _bottom_up(), _groups_ok(), _pc_order(), rec(), rec(), _pocket_type(), _regions_ok(), Step (+1 more)

### Community 23 - "Bot"
Cohesion: 0.06
Nodes (4): _advance(), Bot, Screen, Keyboard

### Community 24 - "dpc_solutions"
Cohesion: 0.33
Nodes (5): test_priority_list_puts_split_pieces_last(), test_tspin_goes_last_in_every_setup(), dpc_solutions(), priority_groups(), priority_text()

### Community 25 - "register"
Cohesion: 0.33
Nodes (4): _EventTypeSpec, _fourcc(), _HotKeyID, register()

### Community 26 - "Lookahead"
Cohesion: 0.07
Nodes (22): _follow(), openers(), test_all_pc_keeps_clearing(), test_coach_agrees_with_the_bot_it_watches(), test_coach_recognises_the_users_opener(), test_coach_switches_to_a_setup_that_can_still_be_finished(), test_extra_piece_tracking_picks_matching_dpc(), test_high_gravity_main_thread_stays_fast() (+14 more)

### Community 30 - "background"
Cohesion: 0.20
Nodes (3): as_background, background(), foreground_busy

### Community 31 - "pc_solve"
Cohesion: 0.22
Nodes (5): test_two_pass_pc_finds_what_the_full_search_finds(), find_pc(), pc_heights(), pc_solve(), _pc_solve()

### Community 32 - "_choices"
Cohesion: 0.25
Nodes (5): can_fill(), rec(), _choices(), order_feasible(), rec()

### Community 34 - "dependencies"
Cohesion: 0.33
Nodes (4): warm_template(), rec(), _ancestors(), dependencies()

### Community 35 - "_dpc_templates"
Cohesion: 0.18
Nodes (6): _blocks(), _dpc_templates(), _find_tsd_slot(), _parse_criteria(), _pc_templates(), _ungrey()

### Community 36 - "BagView"
Cohesion: 0.22
Nodes (3): BagView, _c(), DiagramView

### Community 38 - "Handling"
Cohesion: 0.15
Nodes (14): _opener_brain(), test_advisor_only_recognises_openers_that_are_switched_on(), test_dpc_plans_its_pc_only_near_the_end(), test_finesse_matches_guide(), test_jaws_build_rate_over_every_bag_order(), test_jaws_only_at_a_clean_bag_start(), test_jigsaw_loop_runs(), test_mirrored_tuck_uses_mirrored_rotations() (+6 more)

### Community 39 - "Coach"
Cohesion: 0.10
Nodes (5): _coach_replay(), test_setup_prior_learns_from_the_user(), Coach, _slot_at(), SetupPrior

### Community 41 - "test_advisor_mode_never_presses_keys"
Cohesion: 0.30
Nodes (5): test_advisor_mode_never_presses_keys(), test_high_gravity_pipeline(), test_no_false_high_gravity_without_gravity(), test_sprint_bot_plays_40_lines(), restart()

### Community 42 - "generate"
Cohesion: 0.12
Nodes (12): test_kicks_and_spawn(), test_tsd_spin_detected(), rank(), generate(), coll(), drop(), offer(), push() (+4 more)

### Community 44 - "identify"
Cohesion: 0.20
Nodes (6): _ghost_shapes(), _state_of(), identify(), _locate(), _pattern_pieces(), _pattern_states()

### Community 45 - "cells_of"
Cohesion: 0.16
Nodes (9): _recording_2320(), _sample_boards(), test_20g_plans_skip_pointless_soft_drops(), test_fit_placement_with_line_clear(), test_sideways_moves_happen_before_the_soft_drop(), test_soft_drop_waits_for_the_slide(), fit_placement(), _same() (+1 more)

### Community 46 - "controller.py"
Cohesion: 0.15
Nodes (7): run(), on_hotkey(), _wait_modifiers_released(), _floating_extras(), screen_access_ok(), accessibility_ok(), _sleep()

### Community 48 - "core.py"
Cohesion: 0.15
Nodes (5): test_safe_mode_keys_gravity_independent(), kicks(), slide(), walk(), replay()

### Community 52 - "fill_template"
Cohesion: 0.47
Nodes (5): test_builds_bottom_up_even_if_it_needs_a_hold(), fill_template(), bottom_up_costs(), leaf_viable(), rec()

### Community 53 - "heuristic_move"
Cohesion: 0.40
Nodes (4): _after_cells(), evaluate(), heuristic_move(), holes_covered()

## Knowledge Gaps
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Brain` connect `Brain` to `test_bot.py`, `.__init__`, `Board`, `test_watcher_follows_the_screen`, `brain.py`, `._chance`, `Bot`, `Lookahead`, `._decide`, `Handling`, `Coach`, `test_advisor_mode_never_presses_keys`, `._select`, `controller.py`, `SprintCoach`, `core.py`, `coach.py`, `test_all_pc_counts_the_loop_from_the_bag`, `._jaws_build_sides`?**
  _High betweenness centrality (0.154) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Brain` (e.g. with `test_dpc_plans_its_pc_only_near_the_end()` and `Coach`) actually correct?**
  _`Brain` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Brain` be split into smaller, more focused modules?**
  _Cohesion score 0.11076923076923077 - nodes in this community are weakly interconnected._
- **Why does `Handling` connect `Handling` to `planner.py`, `test_bot.py`, `.__init__`, `.action_cost`, `Coach`, `test_advisor_mode_never_presses_keys`, `python_method`, `cells_of`, `controller.py`, `coach.py`, `test_all_pc_counts_the_loop_from_the_bag`, `settings_ui.py`, `._jaws_build_sides`, `Bot`, `Lookahead`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Bot` (e.g. with `test_wrong_piece_is_never_hard_dropped()` and `Brain`) actually correct?**
  _`Bot` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `vision.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06734006734006734 - nodes in this community are weakly interconnected._
- **Why does `Bot` connect `Bot` to `Brain`, `test_bot.py`, `.__init__`, `Handling`, `Coach`, `test_advisor_mode_never_presses_keys`, `test_watcher_follows_the_screen`, `cells_of`, `controller.py`, `SprintCoach`, `SprintBrain`, `Lookahead`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
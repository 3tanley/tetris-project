# Graph Report - Tetris Scripts  (2026-10-18)

## Corpus Check
- 32 files · ~129,805 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .command 1)

## Summary
- 1017 nodes · 2264 edges · 50 communities (31 shown, 19 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 175 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `015b9b82`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Brain
- vision.py
- Bot
- planner.py
- test_bot.py
- Handling
- plan
- Board
- FakeTetrio
- python_method
- templates.py
- fumen.py
- controller.py
- tetris-project
- library
- app.py
- TState
- Template
- settings_ui.py
- ._confirm
- _build
- Step
- Keyboard
- dpc_solutions
- test_tucked_piece_that_locks_while_planning_is_not_slammed
- Lookahead
- CLAUDE.md
- setup.sh
- as_background
- pc_solve
- rec
- ._decide
- foreground_busy
- _dpc_templates
- .action_cost
- test_dpc_plans_its_pc_only_near_the_end
- Coach
- test_advisor_mode_never_presses_keys
- core.py
- ._select
- cells_of
- ._verify
- test_all_pc_counts_the_loop_from_the_bag
- heuristic_move
- all_pc

## God Nodes (most connected - your core abstractions)
1. `Brain` - 77 edges
2. `Bot` - 65 edges
3. `Handling` - 58 edges
4. `Board` - 39 edges
5. `FakeTetrio` - 31 edges
6. `Lookahead` - 31 edges
7. `configure()` - 29 edges
8. `HandlingWindow` - 29 edges
9. `library()` - 29 edges
10. `Coach` - 24 edges

## Surprising Connections (you probably didn't know these)
- `test_sim_loop_runs_pc_loop()` --calls--> `run()`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/sim.py
- `test_wrong_piece_is_never_hard_dropped()` --uses--> `Bot`  [INFERRED]
  tests/test_bot.py → tetrisbot/controller.py
- `test_dpc_plans_its_pc_only_near_the_end()` --uses--> `Brain`  [INFERRED]
  tests/test_bot.py → tetrisbot/brain.py
- `test_sprint_coach_follows_the_screen()` --uses--> `SprintCoach`  [INFERRED]
  tests/test_bot.py → tetrisbot/sprint.py
- `test_tucked_piece_that_locks_while_planning_is_not_slammed()` --uses--> `Brain`  [INFERRED]
  tests/test_bot.py → tetrisbot/brain.py

## Import Cycles
- None detected.

## Communities (50 total, 19 thin omitted)

### Community 1 - "vision.py"
Cohesion: 0.05
Nodes (30): test_hold_lock_is_read_from_screen(), test_live_screenshot_reads(), test_queue_colour_beats_a_broken_shape(), test_real_all_clear_frame_has_no_phantom_blocks(), test_vision_on_screenshot(), test_zen_queue_is_read_inside_its_panel(), Screen, screen_access_ok() (+22 more)

### Community 2 - "Bot"
Cohesion: 0.18
Nodes (5): _recording_2320(), test_restart_is_noticed(), bot_on(), test_sprint_mode_switch_uses_sprint_coach(), Bot

### Community 3 - "planner.py"
Cohesion: 0.09
Nodes (21): test_air_drops_are_real_placements(), test_mirrored_tuck_uses_mirrored_rotations(), air_drops(), _air_ms(), _air_ok(), _air_table(), background(), _bottom_up() (+13 more)

### Community 4 - "test_bot.py"
Cohesion: 0.13
Nodes (18): _opener_brain(), _run_fake(), test_advisor_only_recognises_openers_that_are_switched_on(), test_all_clear_banner_does_not_break_the_loop(), test_coach_agrees_with_the_bot_it_watches(), test_coach_recognises_the_users_opener(), test_coach_switches_to_a_setup_that_can_still_be_finished(), test_controller_end_to_end() (+10 more)

### Community 5 - "Handling"
Cohesion: 0.16
Nodes (5): openers(), test_controls_from_settings(), test_mode_setting_round_trip(), test_openers_setting_round_trip(), Handling

### Community 6 - "plan"
Cohesion: 0.06
Nodes (18): test_sprint_display_marks_piece_in_play_and_order(), test_sprint_display_shows_preview_pieces(), test_sprint_right_side_patterns(), test_sprint_tetris_when_ready_and_i_not_burnt(), align(), depth_for(), display(), evaluate() (+10 more)

### Community 7 - "Board"
Cohesion: 0.10
Nodes (10): test_dpc_mirrors_match_four_lol_mirrored_view(), test_finesse_matches_guide(), test_ground_paths_work_at_any_gravity(), test_ms2_second_bag_follows_the_piece_order(), test_prefers_o_next_to_the_i(), test_sdpc_tsd_holds_an_early_t_until_the_end(), test_templates_chain(), Board (+2 more)

### Community 8 - "FakeTetrio"
Cohesion: 0.10
Nodes (5): FakeTetrio, test_sprint_coach_follows_the_screen(), test_watcher_follows_the_screen(), _same(), Watcher

### Community 9 - "python_method"
Cohesion: 0.09
Nodes (3): HandlingWindow, OpenerList, OpenersWindow

### Community 10 - "templates.py"
Cohesion: 0.08
Nodes (9): test_order_conflicts_counts_pieces_that_must_wait(), _ancestors(), criteria_status(), dependencies(), _norm(), order_conflicts(), shape_type(), _wiki_templates() (+1 more)

### Community 12 - "fumen.py"
Cohesion: 0.18
Nodes (6): _blocks(), _coord(), decode(), op_cells(), Page, _Reader

### Community 13 - "controller.py"
Cohesion: 0.09
Nodes (6): _jaws_field(), _plan_picture(), _rebase(), sibling_pool(), _sleep(), share_of_kind()

### Community 14 - "tetris-project"
Cohesion: 0.08
Nodes (24): Advisor (BOT PLAYS off), ALL PC, Bag counter and choosing the extra piece, Building from the bottom up, Controls, DPC: how it picks a setup and a solution, Handling window, How it works (+16 more)

### Community 15 - "library"
Cohesion: 0.10
Nodes (16): test_fourlol_sdpc_solutions_match_the_sdpc_residue(), test_jaws_and_second_pc_templates_clear_the_field(), test_jaws_is_the_fourlol_ilsz_data(), test_jigsaw_chain(), test_warm_up_covers_the_sz_dpc_and_stops_for_a_job(), warm_order(), _dedupe(), library() (+8 more)

### Community 16 - "app.py"
Cohesion: 0.05
Nodes (15): BagView, _c(), DiagramView, file_logger(), Overlay, run(), on_hotkey(), SolvePanel (+7 more)

### Community 17 - "TState"
Cohesion: 0.07
Nodes (12): test_builds_bottom_up_even_if_it_needs_a_hold(), test_can_fill_agrees_with_fill_template(), test_singleyou_dependency(), BagTracker, _lookahead_job(), fill_template(), bottom_up_costs(), leaf_viable() (+4 more)

### Community 19 - "settings_ui.py"
Cohesion: 0.10
Nodes (14): Box, Button, Check, _draw_text(), FlippedView, _font(), Label, OpenerRow (+6 more)

### Community 21 - "_build"
Cohesion: 0.14
Nodes (8): _build(), _jaws_templates(), type_of(), _jig_rows(), _jigsaw_templates(), _partition(), _placements_in(), _sdpc_pc_templates()

### Community 22 - "Step"
Cohesion: 0.16
Nodes (7): _groups_ok(), rec(), rec(), _pocket_type(), _regions_ok(), Step, _types()

### Community 24 - "dpc_solutions"
Cohesion: 0.33
Nodes (5): test_priority_list_puts_split_pieces_last(), test_tspin_goes_last_in_every_setup(), dpc_solutions(), priority_groups(), priority_text()

### Community 25 - "test_tucked_piece_that_locks_while_planning_is_not_slammed"
Cohesion: 0.33
Nodes (3): test_slow_planning_never_slams_the_next_piece(), slow(), test_tucked_piece_that_locks_while_planning_is_not_slammed()

### Community 26 - "Lookahead"
Cohesion: 0.14
Nodes (16): _follow(), test_all_pc_keeps_clearing(), test_extra_piece_tracking_picks_matching_dpc(), test_high_gravity_main_thread_stays_fast(), test_jigsaw_loop_runs(), test_jigsaw_takes_the_pc_in_view_before_stacking_for_the_next(), test_keys_per_piece_like_top_players(), test_lookahead_plans_the_pc_during_the_tspin_setup() (+8 more)

### Community 31 - "pc_solve"
Cohesion: 0.22
Nodes (5): test_two_pass_pc_finds_what_the_full_search_finds(), find_pc(), pc_heights(), pc_solve(), _pc_solve()

### Community 33 - "._decide"
Cohesion: 0.10
Nodes (4): test_impossible_dpc_solution_scores_zero(), test_second_pc_scans_every_pattern(), _hurry(), _stable_seed()

### Community 35 - "_dpc_templates"
Cohesion: 0.18
Nodes (6): _blocks(), _dpc_templates(), _find_tsd_slot(), _parse_criteria(), _pc_templates(), _ungrey()

### Community 39 - "Coach"
Cohesion: 0.05
Nodes (10): _coach_replay(), test_setup_prior_learns_from_the_user(), enabled_openers(), opener_priority(), Coach, Events, _plan_still_works(), _slot_at() (+2 more)

### Community 41 - "test_advisor_mode_never_presses_keys"
Cohesion: 0.24
Nodes (5): test_advisor_mode_never_presses_keys(), test_high_gravity_pipeline(), test_no_false_high_gravity_without_gravity(), test_sprint_bot_plays_40_lines(), restart()

### Community 42 - "core.py"
Cohesion: 0.08
Nodes (16): test_safe_mode_keys_gravity_independent(), test_tsd_spin_detected(), rank(), generate(), coll(), drop(), offer(), push() (+8 more)

### Community 45 - "cells_of"
Cohesion: 0.15
Nodes (11): _sample_boards(), test_20g_plans_skip_pointless_soft_drops(), test_fit_placement_with_line_clear(), test_kicks_and_spawn(), test_sideways_moves_happen_before_the_soft_drop(), fit_placement(), _ghost_shapes(), _state_of() (+3 more)

### Community 53 - "heuristic_move"
Cohesion: 0.29
Nodes (5): drop_cells(), _after_cells(), evaluate(), heuristic_move(), holes_covered()

### Community 54 - "all_pc"
Cohesion: 0.22
Nodes (4): test_jaws_build_rate_over_every_bag_order(), count(), all_pc(), ok()

## Knowledge Gaps
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Brain` connect `Brain` to `._decide`, `Bot`, `test_bot.py`, `Handling`, `test_dpc_plans_its_pc_only_near_the_end`, `Board`, `FakeTetrio`, `test_advisor_mode_never_presses_keys`, `Coach`, `._select`, `._play_one_game`, `controller.py`, `test_all_pc_counts_the_loop_from_the_bag`, `all_pc`, `test_tucked_piece_that_locks_while_planning_is_not_slammed`, `Lookahead`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Brain` (e.g. with `test_dpc_plans_its_pc_only_near_the_end()` and `test_tucked_piece_that_locks_while_planning_is_not_slammed()`) actually correct?**
  _`Brain` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `Brain` be split into smaller, more focused modules?**
  _Cohesion score 0.12333333333333334 - nodes in this community are weakly interconnected._
- **Why does `Handling` connect `Handling` to `._decide`, `Bot`, `planner.py`, `test_bot.py`, `.action_cost`, `test_dpc_plans_its_pc_only_near_the_end`, `Coach`, `Board`, `test_advisor_mode_never_presses_keys`, `core.py`, `python_method`, `cells_of`, `controller.py`, `app.py`, `test_all_pc_counts_the_loop_from_the_bag`, `settings_ui.py`, `all_pc`, `Lookahead`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Bot` (e.g. with `test_wrong_piece_is_never_hard_dropped()` and `Brain`) actually correct?**
  _`Bot` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `vision.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05200341005967604 - nodes in this community are weakly interconnected._
- **Why does `Bot` connect `Bot` to `Brain`, `test_bot.py`, `Handling`, `plan`, `Coach`, `FakeTetrio`, `test_advisor_mode_never_presses_keys`, `._play_one_game`, `controller.py`, `._verify`, `app.py`, `._confirm`, `Keyboard`, `Lookahead`, `._update_safe`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
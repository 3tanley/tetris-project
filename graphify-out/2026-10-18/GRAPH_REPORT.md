# Graph Report - Tetris Scripts  (2026-10-18)

## Corpus Check
- 32 files · ~132,897 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .command 1)

## Summary
- 1025 nodes · 2288 edges · 47 communities (33 shown, 14 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 180 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `df7bbea3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- SetupPrior
- vision.py
- Bot
- planner.py
- test_bot.py
- .load
- plan
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
- _build
- settings_ui.py
- Events
- heuristic_move
- dpc_solutions
- brain.py
- Game
- CLAUDE.md
- setup.sh
- BagTracker
- background
- _choices
- ._chance
- core.py
- _dpc_templates
- locate_once
- Handling
- Coach
- app.py
- ._select
- register
- cells_of
- controller.py
- BagView
- all_pc
- ._decide
- _follow
- Brain

## God Nodes (most connected - your core abstractions)
1. `Brain` - 77 edges
2. `Bot` - 65 edges
3. `Handling` - 59 edges
4. `Board` - 41 edges
5. `FakeTetrio` - 31 edges
6. `Lookahead` - 31 edges
7. `configure()` - 30 edges
8. `HandlingWindow` - 29 edges
9. `library()` - 29 edges
10. `Coach` - 25 edges

## Surprising Connections (you probably didn't know these)
- `test_sim_loop_runs_pc_loop()` --calls--> `run()`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/sim.py
- `test_wrong_piece_is_never_hard_dropped()` --uses--> `Bot`  [INFERRED]
  tests/test_bot.py → tetrisbot/controller.py
- `test_dpc_plans_its_pc_only_near_the_end()` --uses--> `Brain`  [INFERRED]
  tests/test_bot.py → tetrisbot/brain.py
- `openers()` --calls--> `Handling`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/handling.py
- `test_sprint_coach_follows_the_screen()` --uses--> `SprintCoach`  [INFERRED]
  tests/test_bot.py → tetrisbot/sprint.py

## Import Cycles
- None detected.

## Communities (47 total, 14 thin omitted)

### Community 1 - "vision.py"
Cohesion: 0.06
Nodes (28): test_hold_lock_is_read_from_screen(), test_live_screenshot_reads(), test_queue_colour_beats_a_broken_shape(), test_real_all_clear_frame_has_no_phantom_blocks(), test_vision_on_screenshot(), test_zen_queue_is_read_inside_its_panel(), cell_color(), cell_state() (+20 more)

### Community 2 - "Bot"
Cohesion: 0.05
Nodes (12): _recording_2320(), test_advisor_mode_never_presses_keys(), test_high_gravity_pipeline(), test_no_false_high_gravity_without_gravity(), test_restart_is_noticed(), bot_on(), test_sprint_bot_plays_40_lines(), test_sprint_mode_switch_uses_sprint_coach() (+4 more)

### Community 3 - "planner.py"
Cohesion: 0.09
Nodes (18): test_two_pass_pc_finds_what_the_full_search_finds(), air_drops(), _air_ms(), _air_ok(), _air_table(), _bottom_up(), _costs(), find_pc() (+10 more)

### Community 4 - "test_bot.py"
Cohesion: 0.14
Nodes (14): _run_fake(), test_all_clear_banner_does_not_break_the_loop(), test_controller_end_to_end(), test_ghost_check_fixes_dropped_inputs(), test_kicks_are_mirror_images(), test_line_clear_delay_keeps_hold_and_moves(), test_screen_lag_no_false_corrections(), test_screen_lag_with_dropped_inputs() (+6 more)

### Community 5 - ".load"
Cohesion: 0.18
Nodes (3): test_controls_from_settings(), test_mode_setting_round_trip(), test_openers_setting_round_trip()

### Community 6 - "plan"
Cohesion: 0.10
Nodes (9): test_sprint_display_marks_piece_in_play_and_order(), test_sprint_display_shows_preview_pieces(), test_sprint_tetris_when_ready_and_i_not_burnt(), depth_for(), display(), plan(), reward(), SprintBrain (+1 more)

### Community 7 - "Board"
Cohesion: 0.11
Nodes (8): test_dpc_mirrors_match_four_lol_mirrored_view(), test_ground_paths_work_at_any_gravity(), test_ms2_second_bag_follows_the_piece_order(), test_prefers_o_next_to_the_i(), test_sdpc_tsd_holds_an_early_t_until_the_end(), test_templates_chain(), Board, second_bag()

### Community 8 - "FakeTetrio"
Cohesion: 0.09
Nodes (6): FakeTetrio, test_40_lines_number_behind_the_field_reads_as_empty(), test_sprint_coach_follows_the_screen(), test_watcher_follows_the_screen(), _same(), Watcher

### Community 9 - "python_method"
Cohesion: 0.09
Nodes (3): HandlingWindow, OpenerList, OpenersWindow

### Community 10 - "templates.py"
Cohesion: 0.08
Nodes (7): criteria_status(), _jig_rows(), _jigsaw_templates(), _norm(), shape_type(), _wiki_templates(), _wiki_type()

### Community 12 - "fumen.py"
Cohesion: 0.18
Nodes (6): _blocks(), _coord(), decode(), op_cells(), Page, _Reader

### Community 14 - "tetris-project"
Cohesion: 0.08
Nodes (24): Advisor (BOT PLAYS off), ALL PC, Bag counter and choosing the extra piece, Building from the bottom up, Controls, DPC: how it picks a setup and a solution, Handling window, How it works (+16 more)

### Community 15 - "library"
Cohesion: 0.12
Nodes (15): test_fourlol_sdpc_solutions_match_the_sdpc_residue(), test_jaws_and_second_pc_templates_clear_the_field(), test_jaws_is_the_fourlol_ilsz_data(), test_jigsaw_chain(), test_warm_up_covers_the_sz_dpc_and_stops_for_a_job(), _dedupe(), dpc(), library() (+7 more)

### Community 17 - "TState"
Cohesion: 0.09
Nodes (12): test_builds_bottom_up_even_if_it_needs_a_hold(), test_can_fill_agrees_with_fill_template(), test_order_conflicts_counts_pieces_that_must_wait(), test_singleyou_dependency(), fill_template(), warm_template(), rec(), _ancestors() (+4 more)

### Community 18 - "_build"
Cohesion: 0.10
Nodes (8): _build(), _jaws_templates(), type_of(), _partition(), _placements_in(), _sdpc_pc_templates(), Slot, Template

### Community 19 - "settings_ui.py"
Cohesion: 0.09
Nodes (14): Box, Button, Check, _draw_text(), FlippedView, _font(), Label, OpenerRow (+6 more)

### Community 22 - "heuristic_move"
Cohesion: 0.12
Nodes (11): _after_cells(), evaluate(), _groups_ok(), heuristic_move(), holes_covered(), rec(), rec(), _pocket_type() (+3 more)

### Community 24 - "dpc_solutions"
Cohesion: 0.33
Nodes (5): test_priority_list_puts_split_pieces_last(), test_tspin_goes_last_in_every_setup(), dpc_solutions(), priority_groups(), priority_text()

### Community 25 - "brain.py"
Cohesion: 0.07
Nodes (14): _jaws_field(), _lookahead_job(), _plan_picture(), _rebase(), sibling_pool(), _plan_still_works(), share_of_kind(), align() (+6 more)

### Community 26 - "Game"
Cohesion: 0.20
Nodes (12): test_all_pc_keeps_clearing(), test_extra_piece_tracking_picks_matching_dpc(), test_high_gravity_main_thread_stays_fast(), test_jigsaw_takes_the_pc_in_view_before_stacking_for_the_next(), test_keys_per_piece_like_top_players(), test_lookahead_plans_the_pc_during_the_tspin_setup(), test_recovers_into_the_loop_from_free_play(), test_sprint_63_advice_scores_tetrises() (+4 more)

### Community 30 - "background"
Cohesion: 0.20
Nodes (3): as_background, background(), foreground_busy

### Community 32 - "_choices"
Cohesion: 0.20
Nodes (7): can_fill(), rec(), _choices(), bottom_up_costs(), rec(), order_feasible(), rec()

### Community 34 - "core.py"
Cohesion: 0.06
Nodes (22): test_kicks_and_spawn(), test_tsd_spin_detected(), rank(), _ghost_shapes(), _state_of(), drop_cells(), generate(), coll() (+14 more)

### Community 35 - "_dpc_templates"
Cohesion: 0.18
Nodes (6): _blocks(), _dpc_templates(), _find_tsd_slot(), _parse_criteria(), _pc_templates(), _ungrey()

### Community 36 - "locate_once"
Cohesion: 0.21
Nodes (3): Screen, locate_once(), main()

### Community 38 - "Handling"
Cohesion: 0.19
Nodes (12): _opener_brain(), test_advisor_only_recognises_openers_that_are_switched_on(), test_advisor_shows_the_only_opener_switched_on(), test_dpc_plans_its_pc_only_near_the_end(), test_finesse_matches_guide(), test_jaws_only_at_a_clean_bag_start(), test_jigsaw_loop_runs(), test_mirrored_tuck_uses_mirrored_rotations() (+4 more)

### Community 39 - "Coach"
Cohesion: 0.12
Nodes (5): _coach_replay(), enabled_openers(), opener_priority(), Coach, _slot_at()

### Community 40 - "app.py"
Cohesion: 0.20
Nodes (6): file_logger(), run(), on_hotkey(), _wait_modifiers_released(), screen_access_ok(), accessibility_ok()

### Community 44 - "register"
Cohesion: 0.33
Nodes (4): _EventTypeSpec, _fourcc(), _HotKeyID, register()

### Community 45 - "cells_of"
Cohesion: 0.16
Nodes (12): _sample_boards(), test_20g_plans_skip_pointless_soft_drops(), test_air_drops_are_real_placements(), test_fit_placement_ignores_a_piece_in_the_air(), test_fit_placement_with_line_clear(), test_safe_mode_keys_gravity_independent(), test_sideways_moves_happen_before_the_soft_drop(), fit_placement() (+4 more)

### Community 48 - "BagView"
Cohesion: 0.22
Nodes (3): BagView, _c(), DiagramView

### Community 52 - "_follow"
Cohesion: 0.33
Nodes (5): _follow(), openers(), test_coach_agrees_with_the_bot_it_watches(), test_coach_recognises_the_users_opener(), test_coach_switches_to_a_setup_that_can_still_be_finished()

### Community 54 - "Brain"
Cohesion: 0.09
Nodes (5): test_bag_counter(), test_jaws_build_rate_over_every_bag_order(), count(), test_second_pc_scans_every_pattern(), Brain

## Knowledge Gaps
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Handling` connect `Handling` to `Bot`, `planner.py`, `test_bot.py`, `.load`, `locate_once`, `Coach`, `python_method`, `.action_cost`, `cells_of`, `controller.py`, `handling.py`, `._decide`, `_follow`, `settings_ui.py`, `Brain`, `brain.py`, `Game`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Brain` (e.g. with `test_dpc_plans_its_pc_only_near_the_end()` and `test_tucked_piece_that_locks_while_planning_is_not_slammed()`) actually correct?**
  _`Brain` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `vision.py` be split into smaller, more focused modules?**
  _Cohesion score 0.059322033898305086 - nodes in this community are weakly interconnected._
- **Why does `Bot` connect `Bot` to `test_bot.py`, `Handling`, `Coach`, `app.py`, `FakeTetrio`, `plan`, `Lookahead`, `controller.py`, `Brain`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Bot` (e.g. with `test_wrong_piece_is_never_hard_dropped()` and `Brain`) actually correct?**
  _`Bot` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `Bot` be split into smaller, more focused modules?**
  _Cohesion score 0.05056179775280899 - nodes in this community are weakly interconnected._
- **Why does `Brain` connect `Brain` to `SetupPrior`, `._chance`, `Bot`, `test_bot.py`, `Handling`, `Board`, `FakeTetrio`, `Coach`, `._select`, `Lookahead`, `controller.py`, `all_pc`, `._decide`, `_follow`, `brain.py`, `Game`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
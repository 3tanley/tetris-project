# Graph Report - Tetris Scripts  (2026-10-18)

## Corpus Check
- 32 files · ~132,443 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .command 1)

## Summary
- 1023 nodes · 2281 edges · 61 communities (42 shown, 19 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 176 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ad192db0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ._maybe_lookahead
- vision.py
- Bot
- planner.py
- test_bot.py
- Handling
- sprint.py
- Board
- FakeTetrio
- python_method
- templates.py
- ._play_one_game
- fumen.py
- Lookahead
- tetris-project
- library
- Overlay
- TState
- Template
- settings_ui.py
- _build
- Step
- Keyboard
- test_warm_up_covers_the_sz_dpc_and_stops_for_a_job
- brain.py
- Game
- CLAUDE.md
- setup.sh
- ._seq
- background
- pc_solve
- _choices
- ._jaws_futures
- generate
- _dpc_templates
- _recording_2320
- test_ms2_second_bag_follows_the_piece_order
- configure
- coach.py
- run
- test_advisor_mode_never_presses_keys
- core.py
- ._select
- register
- cells_of
- controller.py
- handling.py
- BagView
- ._refresh_display
- ._select_jaws
- ._decide
- _follow
- heuristic_move
- Brain
- ._chance
- fill_template
- dependencies
- OpenerRow
- lock
- Placement

## God Nodes (most connected - your core abstractions)
1. `Brain` - 77 edges
2. `Bot` - 65 edges
3. `Handling` - 59 edges
4. `Board` - 40 edges
5. `FakeTetrio` - 31 edges
6. `Lookahead` - 31 edges
7. `configure()` - 30 edges
8. `HandlingWindow` - 29 edges
9. `library()` - 29 edges
10. `Coach` - 25 edges

## Surprising Connections (you probably didn't know these)
- `test_wrong_piece_is_never_hard_dropped()` --uses--> `Bot`  [INFERRED]
  tests/test_bot.py → tetrisbot/controller.py
- `test_dpc_plans_its_pc_only_near_the_end()` --uses--> `Brain`  [INFERRED]
  tests/test_bot.py → tetrisbot/brain.py
- `openers()` --calls--> `Handling`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/handling.py
- `test_sprint_coach_follows_the_screen()` --uses--> `SprintCoach`  [INFERRED]
  tests/test_bot.py → tetrisbot/sprint.py
- `test_tucked_piece_that_locks_while_planning_is_not_slammed()` --uses--> `Brain`  [INFERRED]
  tests/test_bot.py → tetrisbot/brain.py

## Import Cycles
- None detected.

## Communities (61 total, 19 thin omitted)

### Community 1 - "vision.py"
Cohesion: 0.06
Nodes (29): test_hold_lock_is_read_from_screen(), test_live_screenshot_reads(), test_queue_colour_beats_a_broken_shape(), test_real_all_clear_frame_has_no_phantom_blocks(), test_vision_on_screenshot(), test_zen_queue_is_read_inside_its_panel(), locate_once(), cell_color() (+21 more)

### Community 2 - "Bot"
Cohesion: 0.15
Nodes (4): test_restart_is_noticed(), bot_on(), test_sprint_mode_switch_uses_sprint_coach(), Bot

### Community 3 - "planner.py"
Cohesion: 0.13
Nodes (14): test_air_drops_are_real_placements(), air_drops(), _air_ms(), _air_ok(), _air_table(), _costs(), generate(), _gravity_step() (+6 more)

### Community 4 - "test_bot.py"
Cohesion: 0.13
Nodes (14): _run_fake(), test_all_clear_banner_does_not_break_the_loop(), test_controller_end_to_end(), test_ghost_check_fixes_dropped_inputs(), test_kicks_are_mirror_images(), test_line_clear_delay_keeps_hold_and_moves(), test_screen_lag_no_false_corrections(), test_screen_lag_with_dropped_inputs() (+6 more)

### Community 5 - "Handling"
Cohesion: 0.12
Nodes (5): test_controls_from_settings(), test_mode_setting_round_trip(), test_openers_setting_round_trip(), test_tap_shorter_than_das(), Handling

### Community 6 - "sprint.py"
Cohesion: 0.06
Nodes (20): test_sprint_display_marks_piece_in_play_and_order(), test_sprint_display_shows_preview_pieces(), test_sprint_right_side_patterns(), test_sprint_tetris_when_ready_and_i_not_burnt(), align(), depth_for(), display(), evaluate() (+12 more)

### Community 7 - "Board"
Cohesion: 0.13
Nodes (3): test_finesse_matches_guide(), test_ground_paths_work_at_any_gravity(), Board

### Community 8 - "FakeTetrio"
Cohesion: 0.10
Nodes (5): FakeTetrio, test_40_lines_number_behind_the_field_reads_as_empty(), test_sprint_coach_follows_the_screen(), test_watcher_follows_the_screen(), Watcher

### Community 9 - "python_method"
Cohesion: 0.09
Nodes (3): HandlingWindow, OpenerList, OpenersWindow

### Community 10 - "templates.py"
Cohesion: 0.09
Nodes (5): criteria_status(), _norm(), shape_type(), _wiki_templates(), _wiki_type()

### Community 12 - "fumen.py"
Cohesion: 0.18
Nodes (6): _blocks(), _coord(), decode(), op_cells(), Page, _Reader

### Community 13 - "Lookahead"
Cohesion: 0.10
Nodes (6): test_jigsaw_loop_runs(), test_sim_loop_runs_pc_loop(), Lookahead, share_of_kind(), train(), run()

### Community 14 - "tetris-project"
Cohesion: 0.08
Nodes (24): Advisor (BOT PLAYS off), ALL PC, Bag counter and choosing the extra piece, Building from the bottom up, Controls, DPC: how it picks a setup and a solution, Handling window, How it works (+16 more)

### Community 15 - "library"
Cohesion: 0.11
Nodes (15): test_fourlol_sdpc_solutions_match_the_sdpc_residue(), test_jaws_and_second_pc_templates_clear_the_field(), test_jaws_is_the_fourlol_ilsz_data(), test_jigsaw_chain(), test_order_conflicts_counts_pieces_that_must_wait(), _dedupe(), library(), openers() (+7 more)

### Community 17 - "TState"
Cohesion: 0.17
Nodes (3): test_can_fill_agrees_with_fill_template(), test_singleyou_dependency(), TState

### Community 19 - "settings_ui.py"
Cohesion: 0.12
Nodes (11): Box, Button, Check, _draw_text(), FlippedView, _font(), Label, _round_rect() (+3 more)

### Community 21 - "_build"
Cohesion: 0.14
Nodes (8): _build(), _jaws_templates(), type_of(), _jig_rows(), _jigsaw_templates(), _partition(), _placements_in(), _sdpc_pc_templates()

### Community 22 - "Step"
Cohesion: 0.13
Nodes (9): _bottom_up(), _groups_ok(), _pc_order(), rec(), rec(), _pocket_type(), _regions_ok(), Step (+1 more)

### Community 24 - "test_warm_up_covers_the_sz_dpc_and_stops_for_a_job"
Cohesion: 0.20
Nodes (9): test_dpc_mirrors_match_four_lol_mirrored_view(), test_priority_list_puts_split_pieces_last(), test_tspin_goes_last_in_every_setup(), test_warm_up_covers_the_sz_dpc_and_stops_for_a_job(), dpc(), dpc_solutions(), priority_groups(), priority_text() (+1 more)

### Community 25 - "brain.py"
Cohesion: 0.16
Nodes (5): all_pc(), enabled_openers(), opener_priority(), _rebase(), sibling_pool()

### Community 26 - "Game"
Cohesion: 0.23
Nodes (9): test_all_pc_keeps_clearing(), test_extra_piece_tracking_picks_matching_dpc(), test_high_gravity_main_thread_stays_fast(), test_jigsaw_takes_the_pc_in_view_before_stacking_for_the_next(), test_keys_per_piece_like_top_players(), test_lookahead_plans_the_pc_during_the_tspin_setup(), test_recovers_into_the_loop_from_free_play(), test_sprint_63_advice_scores_tetrises() (+1 more)

### Community 30 - "background"
Cohesion: 0.20
Nodes (3): as_background, background(), foreground_busy

### Community 31 - "pc_solve"
Cohesion: 0.22
Nodes (5): test_two_pass_pc_finds_what_the_full_search_finds(), find_pc(), pc_heights(), pc_solve(), _pc_solve()

### Community 32 - "_choices"
Cohesion: 0.25
Nodes (5): can_fill(), rec(), _choices(), order_feasible(), rec()

### Community 34 - "generate"
Cohesion: 0.21
Nodes (8): rank(), generate(), coll(), drop(), offer(), push(), sld(), tspin_kind()

### Community 35 - "_dpc_templates"
Cohesion: 0.18
Nodes (6): _blocks(), _dpc_templates(), _find_tsd_slot(), _parse_criteria(), _pc_templates(), _ungrey()

### Community 37 - "test_ms2_second_bag_follows_the_piece_order"
Cohesion: 0.33
Nodes (5): test_ms2_second_bag_follows_the_piece_order(), test_prefers_o_next_to_the_i(), test_sdpc_tsd_holds_an_early_t_until_the_end(), test_templates_chain(), second_bag()

### Community 38 - "configure"
Cohesion: 0.16
Nodes (11): _opener_brain(), _sample_boards(), test_20g_plans_skip_pointless_soft_drops(), test_advisor_only_recognises_openers_that_are_switched_on(), test_advisor_shows_the_only_opener_switched_on(), test_dpc_plans_its_pc_only_near_the_end(), test_jaws_only_at_a_clean_bag_start(), test_mirrored_tuck_uses_mirrored_rotations() (+3 more)

### Community 39 - "coach.py"
Cohesion: 0.06
Nodes (7): _coach_replay(), test_setup_prior_learns_from_the_user(), Coach, Events, _plan_still_works(), _slot_at(), SetupPrior

### Community 40 - "run"
Cohesion: 0.28
Nodes (4): run(), on_hotkey(), _wait_modifiers_released(), main()

### Community 41 - "test_advisor_mode_never_presses_keys"
Cohesion: 0.24
Nodes (5): test_advisor_mode_never_presses_keys(), test_high_gravity_pipeline(), test_no_false_high_gravity_without_gravity(), test_sprint_bot_plays_40_lines(), restart()

### Community 42 - "core.py"
Cohesion: 0.21
Nodes (5): test_safe_mode_keys_gravity_independent(), kicks(), slide(), walk(), replay()

### Community 44 - "register"
Cohesion: 0.33
Nodes (4): _EventTypeSpec, _fourcc(), _HotKeyID, register()

### Community 45 - "cells_of"
Cohesion: 0.16
Nodes (9): test_fit_placement_with_line_clear(), test_kicks_and_spawn(), fit_placement(), _same(), _ghost_shapes(), _state_of(), cells_of(), drop_cells() (+1 more)

### Community 46 - "controller.py"
Cohesion: 0.16
Nodes (3): _floating_extras(), screen_access_ok(), accessibility_ok()

### Community 48 - "BagView"
Cohesion: 0.22
Nodes (3): BagView, _c(), DiagramView

### Community 52 - "_follow"
Cohesion: 0.29
Nodes (6): _follow(), openers(), test_coach_agrees_with_the_bot_it_watches(), test_coach_recognises_the_users_opener(), test_coach_switches_to_a_setup_that_can_still_be_finished(), test_opener_priority_order_drives_the_suggestion()

### Community 53 - "heuristic_move"
Cohesion: 0.40
Nodes (4): _after_cells(), evaluate(), heuristic_move(), holes_covered()

### Community 54 - "Brain"
Cohesion: 0.21
Nodes (4): test_bag_counter(), test_jaws_build_rate_over_every_bag_order(), count(), Brain

### Community 56 - "fill_template"
Cohesion: 0.47
Nodes (5): test_builds_bottom_up_even_if_it_needs_a_hold(), fill_template(), bottom_up_costs(), leaf_viable(), rec()

### Community 57 - "dependencies"
Cohesion: 0.33
Nodes (4): warm_template(), rec(), _ancestors(), dependencies()

### Community 58 - "OpenerRow"
Cohesion: 0.33
Nodes (3): OpenerRow, _sys_text(), _white()

## Knowledge Gaps
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Brain` connect `Brain` to `._maybe_lookahead`, `Bot`, `test_bot.py`, `FakeTetrio`, `._play_one_game`, `Lookahead`, `brain.py`, `Game`, `._seq`, `._jaws_futures`, `_recording_2320`, `test_ms2_second_bag_follows_the_piece_order`, `configure`, `coach.py`, `test_advisor_mode_never_presses_keys`, `._select`, `controller.py`, `._refresh_display`, `._select_jaws`, `._decide`, `_follow`, `._chance`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `Brain` (e.g. with `test_dpc_plans_its_pc_only_near_the_end()` and `test_tucked_piece_that_locks_while_planning_is_not_slammed()`) actually correct?**
  _`Brain` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `vision.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05654761904761905 - nodes in this community are weakly interconnected._
- **Why does `Handling` connect `Handling` to `Bot`, `planner.py`, `test_bot.py`, `_recording_2320`, `configure`, `coach.py`, `Board`, `test_advisor_mode_never_presses_keys`, `run`, `python_method`, `Lookahead`, `controller.py`, `handling.py`, `._decide`, `_follow`, `settings_ui.py`, `Brain`, `Game`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Bot` (e.g. with `test_wrong_piece_is_never_hard_dropped()` and `Brain`) actually correct?**
  _`Bot` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `Bot` be split into smaller, more focused modules?**
  _Cohesion score 0.14761904761904762 - nodes in this community are weakly interconnected._
- **Why does `Bot` connect `Bot` to `test_bot.py`, `_recording_2320`, `Handling`, `coach.py`, `run`, `test_advisor_mode_never_presses_keys`, `FakeTetrio`, `._play_one_game`, `sprint.py`, `Lookahead`, `controller.py`, `._confirm`, `Brain`, `Keyboard`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
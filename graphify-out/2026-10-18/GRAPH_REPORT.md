# Graph Report - Tetris Scripts  (2026-10-15)

## Corpus Check
- 31 files · ~121,290 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .command 1)

## Summary
- 974 nodes · 2149 edges · 50 communities (33 shown, 17 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 161 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6a2af6cd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Brain
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
- Lookahead
- fumen.py
- brain.py
- tetris-project
- library
- Overlay
- TState
- Template
- ._decide
- ._chance
- _build
- Step
- sim.py
- test_warm_up_covers_the_sz_dpc_and_stops_for_a_job
- register
- train
- CLAUDE.md
- setup.sh
- BagTracker
- background
- pc_solve
- _choices
- ._seq
- dependencies
- _dpc_templates
- BagView
- Handling
- Coach
- run
- _rebase
- core.py
- ._select
- test_air_drops_are_real_placements
- _bottom_up
- controller.py
- .action_cost
- model.py
- fill_template

## God Nodes (most connected - your core abstractions)
1. `Brain` - 68 edges
2. `Bot` - 62 edges
3. `Handling` - 53 edges
4. `Board` - 37 edges
5. `FakeTetrio` - 31 edges
6. `Lookahead` - 29 edges
7. `HandlingWindow` - 29 edges
8. `library()` - 29 edges
9. `configure()` - 25 edges
10. `Coach` - 24 edges

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

## Communities (50 total, 17 thin omitted)

### Community 1 - "vision.py"
Cohesion: 0.06
Nodes (28): test_hold_lock_is_read_from_screen(), test_live_screenshot_reads(), test_queue_colour_beats_a_broken_shape(), test_real_all_clear_frame_has_no_phantom_blocks(), test_vision_on_screenshot(), Screen, locate_once(), cell_color() (+20 more)

### Community 2 - "Bot"
Cohesion: 0.06
Nodes (9): test_advisor_mode_never_presses_keys(), test_high_gravity_pipeline(), test_no_false_high_gravity_without_gravity(), test_sprint_bot_plays_40_lines(), test_sprint_mode_switch_uses_sprint_coach(), _advance(), Bot, restart() (+1 more)

### Community 3 - "planner.py"
Cohesion: 0.15
Nodes (14): _after_cells(), air_drops(), _air_ms(), _air_table(), _costs(), evaluate(), generate(), _gravity_step() (+6 more)

### Community 4 - "test_bot.py"
Cohesion: 0.13
Nodes (16): _follow(), openers(), _run_fake(), test_all_clear_banner_does_not_break_the_loop(), test_coach_agrees_with_the_bot_it_watches(), test_coach_recognises_the_users_opener(), test_coach_switches_to_a_setup_that_can_still_be_finished(), test_controller_end_to_end() (+8 more)

### Community 5 - ".load"
Cohesion: 0.18
Nodes (3): test_controls_from_settings(), test_mode_setting_round_trip(), test_openers_setting_round_trip()

### Community 6 - "sprint.py"
Cohesion: 0.07
Nodes (20): test_sprint_display_marks_piece_in_play_and_order(), test_sprint_display_shows_preview_pieces(), test_sprint_right_side_patterns(), test_sprint_tetris_when_ready_and_i_not_burnt(), align(), depth_for(), display(), evaluate() (+12 more)

### Community 7 - "Board"
Cohesion: 0.12
Nodes (7): test_finesse_matches_guide(), test_ms2_second_bag_follows_the_piece_order(), test_prefers_o_next_to_the_i(), test_sdpc_tsd_holds_an_early_t_until_the_end(), test_templates_chain(), Board, second_bag()

### Community 8 - "FakeTetrio"
Cohesion: 0.10
Nodes (6): FakeTetrio, _recording_2320(), test_soft_drop_waits_for_the_slide(), test_sprint_coach_follows_the_screen(), test_watcher_follows_the_screen(), Watcher

### Community 9 - "python_method"
Cohesion: 0.05
Nodes (17): Box, Button, Check, _draw_text(), FlippedView, _font(), HandlingWindow, Label (+9 more)

### Community 10 - "templates.py"
Cohesion: 0.09
Nodes (7): criteria_status(), _jig_rows(), _jigsaw_templates(), _norm(), shape_type(), _wiki_templates(), _wiki_type()

### Community 12 - "fumen.py"
Cohesion: 0.18
Nodes (6): _blocks(), _coord(), decode(), op_cells(), Page, _Reader

### Community 13 - "brain.py"
Cohesion: 0.14
Nodes (5): _jaws_field(), _lookahead_job(), _plan_picture(), sibling_pool(), _plan_still_works()

### Community 14 - "tetris-project"
Cohesion: 0.09
Nodes (22): Advisor (BOT PLAYS off), Bag counter and choosing the extra piece, Building from the bottom up, Controls, DPC: how it picks a setup and a solution, Handling window, How it works, Jaws (ILSZ) → 2nd PC → DPC (+14 more)

### Community 15 - "library"
Cohesion: 0.14
Nodes (12): test_fourlol_sdpc_solutions_match_the_sdpc_residue(), test_jaws_and_second_pc_templates_clear_the_field(), test_jaws_is_the_fourlol_ilsz_data(), test_jigsaw_chain(), _dedupe(), library(), pc2_setups(), pc2_solutions() (+4 more)

### Community 17 - "TState"
Cohesion: 0.12
Nodes (6): test_can_fill_agrees_with_fill_template(), test_order_conflicts_counts_pieces_that_must_wait(), test_singleyou_dependency(), openers(), order_conflicts(), TState

### Community 21 - "_build"
Cohesion: 0.17
Nodes (7): _build(), _jaws_templates(), type_of(), _partition(), _pc2_templates(), _placements_in(), _sdpc_pc_templates()

### Community 22 - "Step"
Cohesion: 0.15
Nodes (8): _groups_ok(), rec(), _pc_solve(), rec(), _pocket_type(), _regions_ok(), Step, _types()

### Community 24 - "test_warm_up_covers_the_sz_dpc_and_stops_for_a_job"
Cohesion: 0.20
Nodes (9): test_dpc_mirrors_match_four_lol_mirrored_view(), test_priority_list_puts_split_pieces_last(), test_tspin_goes_last_in_every_setup(), test_warm_up_covers_the_sz_dpc_and_stops_for_a_job(), dpc(), dpc_solutions(), priority_groups(), priority_text() (+1 more)

### Community 25 - "register"
Cohesion: 0.33
Nodes (4): _EventTypeSpec, _fourcc(), _HotKeyID, register()

### Community 26 - "train"
Cohesion: 0.25
Nodes (9): test_extra_piece_tracking_picks_matching_dpc(), test_high_gravity_main_thread_stays_fast(), test_keys_per_piece_like_top_players(), test_lookahead_plans_the_pc_during_the_tspin_setup(), test_recovers_into_the_loop_from_free_play(), test_sprint_63_advice_scores_tetrises(), train(), Game (+1 more)

### Community 30 - "background"
Cohesion: 0.20
Nodes (3): as_background, background(), foreground_busy

### Community 31 - "pc_solve"
Cohesion: 0.25
Nodes (4): test_two_pass_pc_finds_what_the_full_search_finds(), find_pc(), pc_heights(), pc_solve()

### Community 32 - "_choices"
Cohesion: 0.25
Nodes (5): can_fill(), rec(), _choices(), order_feasible(), rec()

### Community 34 - "dependencies"
Cohesion: 0.33
Nodes (4): warm_template(), rec(), _ancestors(), dependencies()

### Community 35 - "_dpc_templates"
Cohesion: 0.29
Nodes (4): _blocks(), _dpc_templates(), _find_tsd_slot(), _parse_criteria()

### Community 36 - "BagView"
Cohesion: 0.22
Nodes (3): BagView, _c(), DiagramView

### Community 38 - "Handling"
Cohesion: 0.16
Nodes (13): _opener_brain(), _sample_boards(), test_20g_plans_skip_pointless_soft_drops(), test_advisor_only_recognises_openers_that_are_switched_on(), test_dpc_plans_its_pc_only_near_the_end(), test_jaws_only_at_a_clean_bag_start(), test_jigsaw_loop_runs(), test_mirrored_tuck_uses_mirrored_rotations() (+5 more)

### Community 39 - "Coach"
Cohesion: 0.06
Nodes (8): _coach_replay(), test_setup_prior_learns_from_the_user(), enabled_openers(), opener_priority(), Coach, Events, _slot_at(), SetupPrior

### Community 40 - "run"
Cohesion: 0.28
Nodes (4): run(), on_hotkey(), _wait_modifiers_released(), main()

### Community 42 - "core.py"
Cohesion: 0.06
Nodes (26): test_fit_placement_with_line_clear(), test_ground_paths_work_at_any_gravity(), test_kicks_and_spawn(), test_safe_mode_keys_gravity_independent(), test_tsd_spin_detected(), rank(), fit_placement(), _same() (+18 more)

### Community 44 - "test_air_drops_are_real_placements"
Cohesion: 0.29
Nodes (4): test_air_drops_are_real_placements(), _air_ok(), pc_solutions(), _pc_solutions()

### Community 46 - "controller.py"
Cohesion: 0.17
Nodes (3): _floating_extras(), screen_access_ok(), accessibility_ok()

### Community 52 - "fill_template"
Cohesion: 0.47
Nodes (5): test_builds_bottom_up_even_if_it_needs_a_hold(), fill_template(), bottom_up_costs(), leaf_viable(), rec()

## Knowledge Gaps
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Brain` connect `Brain` to `._seq`, `Bot`, `test_bot.py`, `._open_bag`, `Handling`, `Board`, `FakeTetrio`, `_rebase`, `Coach`, `._select`, `brain.py`, `controller.py`, `model.py`, `._decide`, `._chance`, `sim.py`, `train`?**
  _High betweenness centrality (0.131) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Brain` (e.g. with `test_dpc_plans_its_pc_only_near_the_end()` and `Coach`) actually correct?**
  _`Brain` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Brain` be split into smaller, more focused modules?**
  _Cohesion score 0.12333333333333334 - nodes in this community are weakly interconnected._
- **Why does `Bot` connect `Bot` to `Brain`, `test_bot.py`, `Handling`, `Coach`, `FakeTetrio`, `run`, `sprint.py`, `Lookahead`, `controller.py`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Bot` (e.g. with `test_wrong_piece_is_never_hard_dropped()` and `Brain`) actually correct?**
  _`Bot` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `vision.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05817028027498678 - nodes in this community are weakly interconnected._
- **Why does `Handling` connect `Handling` to `Bot`, `planner.py`, `test_bot.py`, `.load`, `Coach`, `FakeTetrio`, `Board`, `run`, `python_method`, `controller.py`, `.action_cost`, `model.py`, `._decide`, `train`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
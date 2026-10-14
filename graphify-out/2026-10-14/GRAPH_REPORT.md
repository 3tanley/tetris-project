# Graph Report - Tetris Scripts  (2026-10-13)

## Corpus Check
- 32 files · ~118,344 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .command 1)

## Summary
- 932 nodes · 2040 edges · 46 communities (30 shown, 16 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 152 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c067a450`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Brain
- vision.py
- Bot
- planner.py
- test_bot.py
- settings_ui.py
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
- ._chance
- _build
- Step
- sim.py
- dpc_solutions
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
- app.py
- opener_priority
- SetupPrior
- Coach
- run
- test_air_drops_are_real_placements
- core.py
- ._select
- controller.py

## God Nodes (most connected - your core abstractions)
1. `Brain` - 68 edges
2. `Bot` - 59 edges
3. `Handling` - 50 edges
4. `Board` - 37 edges
5. `FakeTetrio` - 30 edges
6. `Lookahead` - 29 edges
7. `library()` - 29 edges
8. `Coach` - 24 edges
9. `configure()` - 24 edges
10. `HandlingWindow` - 24 edges

## Surprising Connections (you probably didn't know these)
- `test_sim_loop_runs_pc_loop()` --calls--> `run()`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/sim.py
- `test_wrong_piece_is_never_hard_dropped()` --uses--> `Bot`  [INFERRED]
  tests/test_bot.py → tetrisbot/controller.py
- `test_dpc_plans_its_pc_only_near_the_end()` --uses--> `Brain`  [INFERRED]
  tests/test_bot.py → tetrisbot/brain.py
- `test_sprint_coach_follows_the_screen()` --uses--> `SprintCoach`  [INFERRED]
  tests/test_bot.py → tetrisbot/sprint.py
- `test_kicks_and_spawn()` --calls--> `Board`  [EXTRACTED]
  tests/test_bot.py → tetrisbot/core.py

## Import Cycles
- None detected.

## Communities (46 total, 16 thin omitted)

### Community 1 - "vision.py"
Cohesion: 0.06
Nodes (28): test_hold_lock_is_read_from_screen(), test_live_screenshot_reads(), test_queue_colour_beats_a_broken_shape(), test_real_all_clear_frame_has_no_phantom_blocks(), test_vision_on_screenshot(), Screen, locate_once(), cell_color() (+20 more)

### Community 2 - "Bot"
Cohesion: 0.06
Nodes (8): test_advisor_mode_never_presses_keys(), test_high_gravity_pipeline(), test_no_false_high_gravity_without_gravity(), test_sprint_mode_switch_uses_sprint_coach(), _advance(), Bot, restart(), Keyboard

### Community 3 - "planner.py"
Cohesion: 0.16
Nodes (13): _after_cells(), air_drops(), _air_ms(), _air_table(), _costs(), evaluate(), generate(), _gravity_step() (+5 more)

### Community 4 - "test_bot.py"
Cohesion: 0.06
Nodes (36): _follow(), openers(), _opener_brain(), _recording_2320(), _run_fake(), _sample_boards(), test_20g_plans_skip_pointless_soft_drops(), test_advisor_only_recognises_openers_that_are_switched_on() (+28 more)

### Community 5 - "settings_ui.py"
Cohesion: 0.10
Nodes (14): Box, Button, Check, _draw_text(), FlippedView, _font(), Label, OpenerRow (+6 more)

### Community 6 - "sprint.py"
Cohesion: 0.07
Nodes (11): test_sprint_display_marks_piece_in_play_and_order(), test_sprint_tetris_when_ready_and_i_not_burnt(), Events, display(), evaluate(), _fits(), Node, plan() (+3 more)

### Community 7 - "Board"
Cohesion: 0.12
Nodes (8): test_dpc_mirrors_match_four_lol_mirrored_view(), test_ms2_second_bag_follows_the_piece_order(), test_prefers_o_next_to_the_i(), test_sdpc_tsd_holds_an_early_t_until_the_end(), test_templates_chain(), Board, openers(), second_bag()

### Community 8 - "FakeTetrio"
Cohesion: 0.10
Nodes (5): FakeTetrio, test_sprint_coach_follows_the_screen(), test_watcher_follows_the_screen(), _same(), Watcher

### Community 9 - "python_method"
Cohesion: 0.11
Nodes (3): HandlingWindow, OpenerList, OpenersWindow

### Community 10 - "templates.py"
Cohesion: 0.09
Nodes (7): criteria_status(), _jig_rows(), _jigsaw_templates(), _norm(), shape_type(), _wiki_templates(), _wiki_type()

### Community 12 - "fumen.py"
Cohesion: 0.18
Nodes (6): _blocks(), _coord(), decode(), op_cells(), Page, _Reader

### Community 13 - "brain.py"
Cohesion: 0.10
Nodes (7): _jaws_field(), _lookahead_job(), _plan_picture(), sibling_pool(), _plan_still_works(), _slot_at(), share_of_kind()

### Community 14 - "tetris-project"
Cohesion: 0.09
Nodes (21): Advisor (BOT PLAYS off), Bag counter and choosing the extra piece, Building from the bottom up, DPC: how it picks a setup and a solution, Handling window, How it works, Jaws (ILSZ) → 2nd PC → DPC, Jigsaw PC loop (off by default) (+13 more)

### Community 15 - "library"
Cohesion: 0.10
Nodes (17): test_fourlol_sdpc_solutions_match_the_sdpc_residue(), test_jaws_and_second_pc_templates_clear_the_field(), test_jaws_is_the_fourlol_ilsz_data(), test_jigsaw_chain(), test_order_conflicts_counts_pieces_that_must_wait(), test_warm_up_covers_the_sz_dpc_and_stops_for_a_job(), _dedupe(), dpc() (+9 more)

### Community 17 - "TState"
Cohesion: 0.13
Nodes (8): test_builds_bottom_up_even_if_it_needs_a_hold(), test_can_fill_agrees_with_fill_template(), test_singleyou_dependency(), fill_template(), bottom_up_costs(), leaf_viable(), rec(), TState

### Community 20 - "._chance"
Cohesion: 0.15
Nodes (3): test_impossible_dpc_solution_scores_zero(), _rebase(), _stable_seed()

### Community 21 - "_build"
Cohesion: 0.17
Nodes (7): _build(), _jaws_templates(), type_of(), _partition(), _pc2_templates(), _placements_in(), _sdpc_pc_templates()

### Community 22 - "Step"
Cohesion: 0.13
Nodes (9): _bottom_up(), _groups_ok(), _pc_order(), rec(), rec(), _pocket_type(), _regions_ok(), Step (+1 more)

### Community 24 - "dpc_solutions"
Cohesion: 0.33
Nodes (5): test_priority_list_puts_split_pieces_last(), test_tspin_goes_last_in_every_setup(), dpc_solutions(), priority_groups(), priority_text()

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
Cohesion: 0.22
Nodes (5): test_two_pass_pc_finds_what_the_full_search_finds(), find_pc(), pc_heights(), pc_solve(), _pc_solve()

### Community 32 - "_choices"
Cohesion: 0.25
Nodes (5): can_fill(), rec(), _choices(), order_feasible(), rec()

### Community 34 - "dependencies"
Cohesion: 0.33
Nodes (4): warm_template(), rec(), _ancestors(), dependencies()

### Community 35 - "_dpc_templates"
Cohesion: 0.29
Nodes (4): _blocks(), _dpc_templates(), _find_tsd_slot(), _parse_criteria()

### Community 36 - "app.py"
Cohesion: 0.13
Nodes (4): BagView, _c(), DiagramView, accessibility_ok()

### Community 40 - "run"
Cohesion: 0.28
Nodes (4): run(), on_hotkey(), _wait_modifiers_released(), main()

### Community 41 - "test_air_drops_are_real_placements"
Cohesion: 0.29
Nodes (4): test_air_drops_are_real_placements(), _air_ok(), pc_solutions(), _pc_solutions()

### Community 42 - "core.py"
Cohesion: 0.06
Nodes (26): test_fit_placement_with_line_clear(), test_ground_paths_work_at_any_gravity(), test_kicks_and_spawn(), test_safe_mode_keys_gravity_independent(), test_tsd_spin_detected(), rank(), fit_placement(), _ghost_shapes() (+18 more)

## Knowledge Gaps
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Brain` connect `Brain` to `._seq`, `Bot`, `test_bot.py`, `sprint.py`, `Board`, `FakeTetrio`, `Coach`, `._select`, `brain.py`, `controller.py`, `._decide`, `._chance`, `sim.py`, `train`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Brain` (e.g. with `test_dpc_plans_its_pc_only_near_the_end()` and `Coach`) actually correct?**
  _`Brain` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Brain` be split into smaller, more focused modules?**
  _Cohesion score 0.12333333333333334 - nodes in this community are weakly interconnected._
- **Why does `Bot` connect `Bot` to `Brain`, `test_bot.py`, `app.py`, `sprint.py`, `Coach`, `run`, `FakeTetrio`, `Lookahead`, `controller.py`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Bot` (e.g. with `test_wrong_piece_is_never_hard_dropped()` and `Brain`) actually correct?**
  _`Bot` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `vision.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05817028027498678 - nodes in this community are weakly interconnected._
- **Why does `Handling` connect `test_bot.py` to `Bot`, `planner.py`, `settings_ui.py`, `Coach`, `run`, `python_method`, `brain.py`, `controller.py`, `train`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
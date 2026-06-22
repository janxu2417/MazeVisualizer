from __future__ import annotations

import pygame
import pytest

from app import (  # noqa: E402
    _adjust_speed,
    _adjust_weight,
    _apply_complexity_option,
    _apply_maze_option,
    _apply_size_option,
    _apply_size_preset,
    _build_cost_map,
    _create_state,
    _cycle_complexity,
    _empty_step_state,
    _export_comparison,
    _handle_keydown,
    _import_maze_grid,
    _make_solver,
    _navigate_history,
    _reset_maze,
    _reset_solver,
    _refresh_edited_maze,
    _set_help_visible,
    _step_solver,
)
from algorithms import RunStats  # noqa: E402
from config import AppConfig, COMPLEXITY_OPTIONS, MAZE_OPTIONS, SIZE_OPTIONS  # noqa: E402


@pytest.fixture
def pygame_ready():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


def test_apply_size_option_updates_config():
    config = AppConfig()
    _apply_size_option(config, SIZE_OPTIONS[2])
    assert (config.rows, config.cols, config.cell_size) == (41, 41, 15)
    assert config.side_padding == 18
    assert config.bottom_padding == 42


def test_apply_size_option_updates_small_top_bar_height():
    config = AppConfig()
    _apply_size_option(config, SIZE_OPTIONS[0])
    assert (config.rows, config.cols, config.cell_size) == (21, 21, 20)
    assert config.top_bar_height == 132


def test_apply_complexity_option_updates_loop_chance():
    config = AppConfig()
    _apply_complexity_option(config, COMPLEXITY_OPTIONS[0])
    assert config.loop_chance == 0.0


def test_apply_maze_option_overrides_loop_when_defined():
    config = AppConfig()
    label = _apply_maze_option(config, MAZE_OPTIONS[2])
    assert config.maze_method == "prim"
    assert config.loop_chance == 0.18
    assert label == "Dense"


def test_cycle_complexity_handles_custom_value():
    config = AppConfig(loop_chance=0.12)
    label = _cycle_complexity(config, COMPLEXITY_OPTIONS, "Custom 0.12")
    assert config.loop_chance == COMPLEXITY_OPTIONS[0][1]
    assert label is None


def test_adjust_speed_clamps_to_bounds():
    config = AppConfig(step_interval_ms=80, min_step_ms=30, max_step_ms=240)
    _adjust_speed(config, -1000)
    assert config.step_interval_ms == 30
    _adjust_speed(config, 1000)
    assert config.step_interval_ms == 240


def test_adjust_weight_clamps_to_bounds():
    config = AppConfig(weighted_a_star_w=1.5, min_weight=1.0, max_weight=3.0)
    _adjust_weight(config, -10.0)
    assert config.weighted_a_star_w == 1.0
    _adjust_weight(config, 10.0)
    assert config.weighted_a_star_w == 3.0


def test_build_cost_map_returns_none_when_terrain_disabled():
    config = AppConfig(terrain_mode=False)
    grid = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
    ]
    assert _build_cost_map(config, grid) is None


def test_build_cost_map_is_deterministic_and_weighted():
    config = AppConfig(terrain_mode=True, terrain_seed=2026, rows=5, cols=5)
    grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 0, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]
    cost_map_a = _build_cost_map(config, grid)
    cost_map_b = _build_cost_map(config, grid)
    assert cost_map_a == cost_map_b
    assert cost_map_a is not None
    values = {value for row in cost_map_a for value in row}
    assert values <= {0, 1, 3, 5}
    assert cost_map_a[0][0] == 0


def test_reset_solver_keeps_existing_cost_map_when_preserving_it(pygame_ready):
    config = AppConfig(rows=21, cols=21, terrain_mode=True)
    state = _create_state(config, "BFS")
    assert state.cost_map is not None
    state.cost_map[1][1] = 5
    state.cost_map[1][2] = 3
    original_cost_map = [row[:] for row in state.cost_map]

    _reset_solver(config, state, "A*", preserve_cost_map=True)

    assert state.algorithm_name == "A*"
    assert state.cost_map == original_cost_map


def test_refresh_edited_maze_syncs_current_snapshot_and_clears_results(pygame_ready):
    config = AppConfig(rows=21, cols=21)
    state = _create_state(config, "BFS")
    state.comparison_results["BFS"] = RunStats(
        visited_count=10,
        path_length=8,
        step_count=10,
        optimal=True,
        cost=8,
    )
    _reset_maze(config, state, preserve_comparison=True)
    state.comparison_results["A*"] = RunStats(
        visited_count=9,
        path_length=8,
        step_count=9,
        optimal=True,
        cost=8,
    )
    current_snapshot = state.maze_history[state.maze_index]
    edited_cell = (2, 2)
    state.grid[edited_cell[0]][edited_cell[1]] = 0 if state.grid[edited_cell[0]][edited_cell[1]] == 1 else 1
    state.start = (1, 2)
    state.goal = (config.rows - 2, config.cols - 3)
    if state.cost_map is not None:
        state.cost_map[1][2] = 5

    _refresh_edited_maze(config, state)

    assert state.comparison_results == {}
    assert current_snapshot.comparison_results == {}
    assert current_snapshot.grid == state.grid
    assert current_snapshot.start == state.start
    assert current_snapshot.goal == state.goal
    if state.cost_map is not None:
        assert current_snapshot.cost_map == state.cost_map


def test_reset_maze_clears_edit_history_for_new_current_maze(pygame_ready):
    config = AppConfig(rows=21, cols=21)
    state = _create_state(config, "BFS")
    state.edit_state.edit_history.append(object())

    _reset_maze(config, state, preserve_comparison=False)

    assert state.edit_state.edit_history == []
    assert state.maze_index == len(state.maze_history) - 1


def test_apply_size_preset_rebuilds_grid_to_match_config(pygame_ready):
    config = AppConfig(rows=31, cols=31)
    state = _create_state(config, "BFS")

    _apply_size_preset(config, state, SIZE_OPTIONS[0])

    assert len(state.grid) == config.rows == 21
    assert len(state.grid[0]) == config.cols == 21
    assert state.start == (1, 1)
    assert state.goal == (config.rows - 2, config.cols - 2)
    if state.cost_map is not None:
        assert len(state.cost_map) == config.rows
        assert len(state.cost_map[0]) == config.cols


def test_navigate_history_clears_edit_history_and_restores_snapshot(pygame_ready):
    config = AppConfig(rows=21, cols=21)
    state = _create_state(config, "BFS")
    state.comparison_results["BFS"] = RunStats(
        visited_count=12,
        path_length=8,
        step_count=12,
        optimal=True,
        cost=8,
    )
    _reset_maze(config, state, preserve_comparison=True)
    newer_snapshot = state.maze_history[state.maze_index]
    state.edit_state.edit_history.append(object())

    _navigate_history(config, state, -1)

    assert state.edit_state.edit_history == []
    assert state.grid == state.maze_history[state.maze_index].grid
    assert state.grid != newer_snapshot.grid


def test_empty_step_state_has_expected_defaults():
    start = (1, 1)
    state = _empty_step_state(start)
    assert state["current"] == start
    assert state["visited"] == set()
    assert state["frontier"] == set()
    assert state["path"] == []
    assert state["finished"] is False
    assert state["stats"].path_length == 0


def test_make_solver_rejects_unknown_algorithm():
    config = AppConfig()
    grid = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
    ]
    with pytest.raises(ValueError):
        _make_solver("Unknown", grid, (1, 1), (1, 1), config, None)


def test_set_help_visible_pauses_and_restores_state(pygame_ready):
    config = AppConfig(rows=21, cols=21)
    state = _create_state(config, "BFS")
    state.paused = False
    _set_help_visible(state, True)
    assert state.help_visible is True
    assert state.paused is True
    _set_help_visible(state, False)
    assert state.help_visible is False
    assert state.paused is False


def test_e_key_requests_edit_mode(pygame_ready):
    config = AppConfig(rows=21, cols=21)
    state = _create_state(config, "BFS")
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e, unicode="e")
    next_mode = _handle_keydown(event, config, state)
    assert next_mode == "edit"
    assert state.paused is True
    assert state.step_hold is False
    assert state.finished is False


def test_create_state_and_step_solver_update_runtime_state(pygame_ready):
    config = AppConfig(rows=21, cols=21, terrain_mode=True)
    state = _create_state(config, "BFS")
    assert state.cost_map is not None
    assert state.algorithm_name == "BFS"
    _step_solver(state)
    assert state.last_state["current"] is not None
    assert state.last_state["stats"].step_count >= 1
    assert len(state.visit_index) >= 1


def test_c_toggle_should_hide_compare_without_clearing_results(pygame_ready):
    config = AppConfig(rows=21, cols=21)
    state = _create_state(config, "BFS")
    state.comparison_results["BFS"] = RunStats(
        visited_count=10,
        path_length=8,
        step_count=10,
        optimal=True,
        cost=8,
    )
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c, unicode="c")
    _handle_keydown(event, config, state)
    assert state.show_comparison is False
    assert "BFS" in state.comparison_results
    _handle_keydown(event, config, state)
    assert state.show_comparison is True
    assert "BFS" in state.comparison_results


def test_m_key_preserves_old_results_in_history(pygame_ready):
    config = AppConfig(rows=21, cols=21)
    state = _create_state(config, "BFS")
    state.comparison_results["BFS"] = RunStats(
        visited_count=10,
        path_length=8,
        step_count=10,
        optimal=True,
        cost=8,
    )
    state.comparison_results["Dijkstra"] = RunStats(
        visited_count=7,
        path_length=8,
        step_count=7,
        optimal=True,
        cost=8,
    )
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m, unicode="m")
    _handle_keydown(event, config, state)
    assert len(state.maze_history) == 2
    assert state.maze_index == 1
    saved = state.maze_history[0]
    assert "BFS" in saved.comparison_results
    assert "Dijkstra" in saved.comparison_results
    assert saved.comparison_results["BFS"].path_length == 8
    assert len(state.comparison_results) == 0
    assert state.show_comparison is True


def test_history_navigate_back_and_forth_restores_comparison(pygame_ready):
    config = AppConfig(rows=21, cols=21)
    state = _create_state(config, "BFS")
    state.comparison_results["BFS"] = RunStats(
        visited_count=12,
        path_length=8,
        step_count=12,
        optimal=True,
        cost=8,
    )
    event_m = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m, unicode="m")
    _handle_keydown(event_m, config, state)
    assert state.maze_index == 1
    assert len(state.maze_history) == 2
    assert state.maze_history[0].comparison_results["BFS"].path_length == 8
    assert len(state.comparison_results) == 0

    state.comparison_results["A*"] = RunStats(
        visited_count=9,
        path_length=8,
        step_count=9,
        optimal=True,
        cost=8,
    )
    _handle_keydown(event_m, config, state)
    assert state.maze_index == 2
    assert len(state.maze_history) == 3
    assert state.maze_history[1].comparison_results["A*"].path_length == 8
    assert len(state.comparison_results) == 0

    event_left = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT, unicode="")
    _handle_keydown(event_left, config, state)
    assert state.maze_index == 1
    assert "A*" in state.comparison_results
    assert "BFS" not in state.comparison_results

    _handle_keydown(event_left, config, state)
    assert state.maze_index == 0
    assert "BFS" in state.comparison_results
    assert "A*" not in state.comparison_results

    event_right = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT, unicode="")
    _handle_keydown(event_right, config, state)
    assert state.maze_index == 1
    assert "A*" in state.comparison_results


def test_export_comparison_writes_valid_json(tmp_path, pygame_ready):
    config = AppConfig(rows=21, cols=21)
    state = _create_state(config, "BFS")
    state.comparison_results["BFS"] = RunStats(
        visited_count=10,
        path_length=5,
        step_count=10,
        optimal=True,
        cost=5,
    )
    filepath = tmp_path / "export.json"
    _export_comparison(state, str(filepath))
    assert filepath.exists()

    import json
    data = json.loads(filepath.read_text(encoding="utf-8"))
    assert data["algorithm"] == "BFS"
    assert data["comparison_results"]["BFS"]["path_length"] == 5
    assert data["comparison_results"]["BFS"]["optimal"] is True
    assert len(data["grid"]) == 21


def test_import_maze_grid_parses_valid_file(tmp_path):
    content = "0 0 0\n0 1 0\n0 0 0\n"
    filepath = tmp_path / "maze.txt"
    filepath.write_text(content)
    grid = _import_maze_grid(str(filepath))
    assert grid == [[0, 0, 0], [0, 1, 0], [0, 0, 0]]


def test_import_maze_grid_skips_comments_and_blanks(tmp_path):
    content = "# header\n0 0 0\n\n0 1 0\n# footer\n0 0 0\n"
    filepath = tmp_path / "maze.txt"
    filepath.write_text(content)
    grid = _import_maze_grid(str(filepath))
    assert grid == [[0, 0, 0], [0, 1, 0], [0, 0, 0]]


def test_import_maze_grid_rejects_inconsistent_rows(tmp_path):
    content = "0 0 0\n0 1\n"
    filepath = tmp_path / "bad.txt"
    filepath.write_text(content)
    with pytest.raises(ValueError):
        _import_maze_grid(str(filepath))

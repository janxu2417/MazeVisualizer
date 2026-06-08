from __future__ import annotations

import sys
from pathlib import Path

import pygame
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app import (  # noqa: E402
    _adjust_speed,
    _adjust_weight,
    _apply_complexity_option,
    _apply_maze_option,
    _apply_size_option,
    _build_cost_map,
    _create_state,
    _cycle_complexity,
    _empty_step_state,
    _handle_keydown,
    _make_solver,
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

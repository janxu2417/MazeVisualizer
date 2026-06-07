from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from algorithms import (  # noqa: E402
    RunStats,
    generate_maze,
    solve_bfs,
    solve_bidirectional_bfs,
    solve_dijkstra,
)


def _collect_states(iterator):
    states = list(iterator)
    assert states, "solver should yield at least one state"
    return states


def test_bfs_step_state_contains_expected_fields():
    grid = generate_maze(21, 21, seed=23, method="dfs")
    start = (1, 1)
    goal = (len(grid) - 2, len(grid[0]) - 2)

    states = _collect_states(solve_bfs(grid, start, goal))
    first = states[0]
    last = states[-1]

    assert set(first.keys()) == {
        "current",
        "visited",
        "frontier",
        "path",
        "finished",
        "stats",
        "visited_from_start",
        "visited_from_goal",
        "meet_point",
    }
    assert isinstance(first["stats"], RunStats)
    assert first["current"] == start
    assert start in first["visited"]
    assert isinstance(first["frontier"], set)
    assert last["finished"] is True


def test_bidirectional_bfs_exposes_two_side_search_state():
    grid = generate_maze(21, 21, seed=29, method="prim")
    start = (1, 1)
    goal = (len(grid) - 2, len(grid[0]) - 2)

    states = _collect_states(solve_bidirectional_bfs(grid, start, goal))
    last = states[-1]

    assert last["path"][0] == start
    assert last["path"][-1] == goal
    assert last["meet_point"] is not None
    assert start in last["visited_from_start"]
    assert goal in last["visited_from_goal"]
    assert last["visited_from_start"] | last["visited_from_goal"] <= last["visited"]


def test_bidirectional_bfs_handles_same_start_and_goal():
    grid = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
    ]
    start = goal = (1, 1)

    states = _collect_states(solve_bidirectional_bfs(grid, start, goal))
    state = states[-1]

    assert state["finished"] is True
    assert state["path"] == [start]
    assert state["meet_point"] == start
    assert state["stats"].path_length == 0


def test_bfs_marks_non_optimal_in_weighted_mode():
    grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0],
        [0, 1, 0, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]
    start = (1, 1)
    goal = (3, 3)
    cost_map = [
        [0, 0, 0, 0, 0],
        [0, 1, 5, 5, 0],
        [0, 1, 0, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]

    bfs_states = _collect_states(solve_bfs(grid, start, goal, cost_map=cost_map))
    dijkstra_states = _collect_states(solve_dijkstra(grid, start, goal, cost_map=cost_map))

    assert bfs_states[-1]["stats"].optimal is False
    assert dijkstra_states[-1]["stats"].optimal is True
    assert dijkstra_states[-1]["stats"].cost <= bfs_states[-1]["stats"].cost


def test_solver_returns_empty_path_when_goal_is_unreachable():
    grid = [
        [0, 0, 0, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0],
    ]
    start = (1, 1)
    goal = (1, 3)

    states = _collect_states(solve_bfs(grid, start, goal))
    last = states[-1]

    assert last["finished"] is True
    assert last["path"] == []
    assert last["stats"].path_length == 0


@pytest.mark.parametrize(
    ("rows", "cols"),
    [(2, 5), (5, 2), (2, 2)],
)
def test_generate_maze_rejects_too_small_size(rows, cols):
    with pytest.raises(ValueError):
        generate_maze(rows, cols)


def test_generate_maze_rejects_unknown_method():
    with pytest.raises(ValueError):
        generate_maze(21, 21, method="unknown")

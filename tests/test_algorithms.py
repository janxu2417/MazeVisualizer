from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from algorithms import (  # noqa: E402
    generate_maze,
    solve_a_star,
    solve_bfs,
    solve_dijkstra,
    solve_greedy_best_first,
    solve_weighted_a_star,
)


def _collect_states(iterator):
    states = list(iterator)
    assert states, "solver should yield at least one state"
    return states


def _final_path(states):
    return states[-1]["path"]


def _assert_path_valid(grid, path, start, goal):
    assert path[0] == start
    assert path[-1] == goal
    for (r1, c1), (r2, c2) in zip(path, path[1:]):
        assert abs(r1 - r2) + abs(c1 - c2) == 1
        assert grid[r2][c2] == 1


def test_generate_maze_normalizes_even_size_to_odd():
    grid = generate_maze(20, 22, seed=1, method="dfs")
    assert len(grid) == 21
    assert len(grid[0]) == 23


@pytest.mark.parametrize("method", ["dfs", "prim", "kruskal"])
def test_generated_mazes_are_solvable(method):
    grid = generate_maze(21, 21, seed=7, method=method)
    start = (1, 1)
    goal = (len(grid) - 2, len(grid[0]) - 2)
    grid[start[0]][start[1]] = 1
    grid[goal[0]][goal[1]] = 1
    states = _collect_states(solve_bfs(grid, start, goal))
    assert states[-1]["path"]


def test_bfs_returns_valid_shortest_path():
    grid = generate_maze(21, 21, seed=11, method="dfs")
    start = (1, 1)
    goal = (len(grid) - 2, len(grid[0]) - 2)
    states = _collect_states(solve_bfs(grid, start, goal))
    path = _final_path(states)
    _assert_path_valid(grid, path, start, goal)
    assert states[-1]["stats"].path_length == len(path) - 1


def test_dijkstra_matches_bfs_path_length_on_uniform_grid():
    grid = generate_maze(21, 21, seed=13, method="prim")
    start = (1, 1)
    goal = (len(grid) - 2, len(grid[0]) - 2)
    bfs_states = _collect_states(solve_bfs(grid, start, goal))
    dijkstra_states = _collect_states(solve_dijkstra(grid, start, goal))
    assert bfs_states[-1]["stats"].path_length == dijkstra_states[-1]["stats"].path_length


def test_a_star_matches_bfs_path_length_on_uniform_grid():
    grid = generate_maze(21, 21, seed=17, method="kruskal")
    start = (1, 1)
    goal = (len(grid) - 2, len(grid[0]) - 2)
    bfs_states = _collect_states(solve_bfs(grid, start, goal))
    a_star_states = _collect_states(solve_a_star(grid, start, goal))
    assert bfs_states[-1]["stats"].path_length == a_star_states[-1]["stats"].path_length


@pytest.mark.parametrize("solver", [solve_greedy_best_first, solve_weighted_a_star])
def test_greedy_and_weighted_astar_return_valid_paths_and_stats(solver):
    grid = generate_maze(21, 21, seed=19, method="dfs", loop_chance=0.1)
    start = (1, 1)
    goal = (len(grid) - 2, len(grid[0]) - 2)
    states = _collect_states(solver(grid, start, goal))
    path = _final_path(states)
    _assert_path_valid(grid, path, start, goal)
    assert states[-1]["stats"].visited_count >= len(path)
    assert states[-1]["stats"].step_count > 0


def test_weighted_terrain_changes_cost_model_for_dijkstra():
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
    states = _collect_states(solve_dijkstra(grid, start, goal, cost_map=cost_map))
    stats = states[-1]["stats"]
    assert stats.cost == 4
    assert stats.path_length == 4


def test_invalid_start_goal_raises_value_error():
    with pytest.raises(ValueError):
        list(solve_bfs([[0, 0], [0, 0]], (0, 0), (1, 1)))

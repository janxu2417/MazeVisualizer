from __future__ import annotations

import pytest

from algorithms import (  # noqa: E402
    RunStats,
    generate_maze,
    solve_a_star,
    solve_bfs,
    solve_bidirectional_bfs,
    solve_dijkstra,
    solve_greedy_best_first,
    solve_weighted_a_star,
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

    # stats assertions for the completed Bi-BFS
    stats = last["stats"]
    assert stats.path_length == len(last["path"]) - 1
    assert stats.cost == stats.path_length  # uniform grid, no terrain
    assert stats.visited_count == len(last["visited"])
    assert stats.optimal is True
    assert stats.step_count >= stats.visited_count // 2  # both sides advance


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
    assert state["stats"].cost == 0
    assert state["stats"].visited_count == 1
    assert state["stats"].step_count == 0


def test_bidirectional_bfs_optimal_is_false_with_terrain():
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
        [0, 1, 5, 1, 0],
        [0, 1, 0, 5, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]

    states = _collect_states(solve_bidirectional_bfs(grid, start, goal, cost_map=cost_map))
    last = states[-1]
    assert last["finished"] is True
    assert last["stats"].optimal is False
    # path and cost must be consistent; cost from full path, not half
    path = last["path"]
    assert len(path) >= 2
    assert last["stats"].path_length == len(path) - 1
    expected_cost = sum(cost_map[r][c] for r, c in path[1:])
    assert last["stats"].cost == expected_cost
    assert last["stats"].cost > 0
    assert last["stats"].visited_count == len(last["visited"])


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


def test_large_maze_is_solvable():
    grid = generate_maze(101, 101, seed=42, method="dfs")
    start = (1, 1)
    goal = (len(grid) - 2, len(grid[0]) - 2)
    grid[start[0]][start[1]] = 1
    grid[goal[0]][goal[1]] = 1
    states = _collect_states(solve_bfs(grid, start, goal))
    assert states[-1]["finished"] is True
    assert len(states[-1]["path"]) >= 2


@pytest.mark.parametrize(
    "solver",
    [
        solve_bfs,
        solve_dijkstra,
        solve_a_star,
        solve_bidirectional_bfs,
        solve_greedy_best_first,
        solve_weighted_a_star,
    ],
)
def test_minimal_3x3_maze_all_solvers(solver):
    grid = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
    ]
    start = (1, 1)
    goal = (1, 1)
    states = _collect_states(solver(grid, start, goal))
    last = states[-1]
    assert last["finished"] is True
    assert last["path"] == [start]
    assert last["stats"].path_length == 0


@pytest.mark.parametrize(
    "solver",
    [
        solve_bfs,
        solve_dijkstra,
        solve_a_star,
        solve_bidirectional_bfs,
    ],
)
def test_all_solvers_handle_start_equals_goal(solver):
    grid = generate_maze(21, 21, seed=99, method="prim")
    start = goal = (1, 1)
    grid[start[0]][start[1]] = 1
    states = _collect_states(solver(grid, start, goal))
    last = states[-1]
    assert last["finished"] is True
    assert last["path"] == [start]
    assert last["stats"].path_length == 0


@pytest.mark.parametrize("method", ["dfs", "prim", "kruskal"])
def test_extreme_loop_chance_still_solvable(method):
    grid = generate_maze(31, 31, seed=77, method=method, loop_chance=1.0)
    start = (1, 1)
    goal = (len(grid) - 2, len(grid[0]) - 2)
    grid[start[0]][start[1]] = 1
    grid[goal[0]][goal[1]] = 1
    states = _collect_states(solve_bfs(grid, start, goal))
    assert states[-1]["finished"] is True
    assert len(states[-1]["path"]) >= 2


def test_all_algorithms_on_same_maze_return_valid_paths():
    grid = generate_maze(21, 21, seed=53, method="dfs")
    start = (1, 1)
    goal = (len(grid) - 2, len(grid[0]) - 2)
    grid[start[0]][start[1]] = 1
    grid[goal[0]][goal[1]] = 1
    solvers = [
        ("BFS", solve_bfs),
        ("Dijkstra", solve_dijkstra),
        ("A*", solve_a_star),
        ("Bi-BFS", solve_bidirectional_bfs),
        ("Greedy", solve_greedy_best_first),
        ("Weighted A*", solve_weighted_a_star),
    ]
    results = {}
    for name, solver in solvers:
        states = _collect_states(solver(grid, start, goal))
        path = states[-1]["path"]
        results[name] = states[-1]["stats"]
        assert path[0] == start
        assert path[-1] == goal
        for (r1, c1), (r2, c2) in zip(path, path[1:]):
            assert abs(r1 - r2) + abs(c1 - c2) == 1
            assert grid[r2][c2] == 1
    assert results["BFS"].path_length == results["A*"].path_length == results["Dijkstra"].path_length

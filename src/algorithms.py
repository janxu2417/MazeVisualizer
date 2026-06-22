from __future__ import annotations

# Re-export compatibility layer — all types and functions are now maintained
# in the split modules below.  External callers use the same imports as
# before; no source changes are required.

from step_data import CostMap, Grid, Point, RunStats, StepState
from maze_gen import generate_maze
from pathfinding import (
    solve_a_star,
    solve_bfs,
    solve_bidirectional_bfs,
    solve_dijkstra,
    solve_greedy_best_first,
    solve_weighted_a_star,
)

__all__ = [
    "CostMap",
    "Grid",
    "Point",
    "RunStats",
    "StepState",
    "generate_maze",
    "solve_a_star",
    "solve_bfs",
    "solve_bidirectional_bfs",
    "solve_dijkstra",
    "solve_greedy_best_first",
    "solve_weighted_a_star",
]

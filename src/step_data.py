from __future__ import annotations

from dataclasses import dataclass
from typing import List, TypedDict

Grid = List[List[int]]
Point = tuple[int, int]
CostMap = list[list[int]]


@dataclass(frozen=True)
class RunStats:
    """Immutable statistics snapshot for one solver step.

    Attributes:
        visited_count: Number of distinct nodes visited (expanded + frontier).
        path_length: Number of steps (edges) on the current reconstructed path.
        step_count: How many solver iterations have executed so far.
        optimal: Whether the current path is guaranteed optimal by the algorithm.
        cost: Accumulated terrain cost of the reconstructed path.
    """

    visited_count: int
    path_length: int
    step_count: int
    optimal: bool
    cost: int


class StepState(TypedDict):
    """Unified state frame yielded by every solver iterator.

    Each frame captures the algorithm's internal state at one moment,
    decoupling algorithm logic from UI rendering.

    Fields:
        current: The node being expanded this step (None if idle).
        visited: All nodes that have been expanded so far.
        frontier: Nodes currently in the open set / queue.
        path: Reconstructed path from start to current (or final path when finished).
        finished: Whether the solver has terminated (reached goal or exhausted search).
        stats: Aggregated runtime statistics for this step.
        visited_from_start: Nodes visited from the start side (bidirectional BFS only).
        visited_from_goal: Nodes visited from the goal side (bidirectional BFS only).
        meet_point: The meeting point of the two searches (bidirectional BFS only).
    """

    current: Point | None
    visited: set[Point]
    frontier: set[Point]
    path: list[Point]
    finished: bool
    stats: RunStats
    visited_from_start: set[Point]
    visited_from_goal: set[Point]
    meet_point: Point | None

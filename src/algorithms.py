from __future__ import annotations

from collections import deque
import heapq
import random
from typing import Iterable, List, Tuple

Grid = List[List[int]]
Point = Tuple[int, int]
StepState = dict


def generate_maze(rows: int, cols: int, seed: int | None = None) -> Grid:
    """Generate a perfect maze using DFS backtracking.

    The maze uses a grid where 0 = wall, 1 = path. Rows/cols will be
    adjusted to odd numbers to simplify carving.
    """
    if rows < 3 or cols < 3:
        raise ValueError("rows and cols must be >= 3")

    if rows % 2 == 0:
        rows += 1
    if cols % 2 == 0:
        cols += 1

    rng = random.Random(seed)
    grid: Grid = [[0 for _ in range(cols)] for _ in range(rows)]

    start: Point = (1, 1)
    grid[start[0]][start[1]] = 1
    stack: list[Point] = [start]
    directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]

    while stack:
        r, c = stack[-1]
        rng.shuffle(directions)
        carved = False
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 1 <= nr < rows - 1 and 1 <= nc < cols - 1 and grid[nr][nc] == 0:
                grid[r + dr // 2][c + dc // 2] = 1
                grid[nr][nc] = 1
                stack.append((nr, nc))
                carved = True
                break
        if not carved:
            stack.pop()

    return grid


def solve_bfs(grid: Grid, start: Point, goal: Point) -> Iterable[StepState]:
    _validate_start_goal(grid, start, goal)

    queue = deque([start])
    came_from: dict[Point, Point | None] = {start: None}
    visited: set[Point] = {start}
    found = False

    while queue:
        current = queue.popleft()
        yield {
            "visited": set(visited),
            "path": _reconstruct_path(came_from, current),
        }
        if current == goal:
            found = True
            break
        for neighbor in _neighbors(grid, current):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            came_from[neighbor] = current
            queue.append(neighbor)

    if not found:
        yield {"visited": set(visited), "path": []}


def solve_dijkstra(grid: Grid, start: Point, goal: Point) -> Iterable[StepState]:
    _validate_start_goal(grid, start, goal)

    heap: list[tuple[int, Point]] = [(0, start)]
    dist: dict[Point, int] = {start: 0}
    came_from: dict[Point, Point | None] = {start: None}
    visited: set[Point] = set()
    found = False

    while heap:
        current_dist, current = heapq.heappop(heap)
        if current in visited:
            continue
        visited.add(current)
        yield {
            "visited": set(visited),
            "path": _reconstruct_path(came_from, current),
        }
        if current == goal:
            found = True
            break
        for neighbor in _neighbors(grid, current):
            if neighbor in visited:
                continue
            new_dist = current_dist + 1
            if new_dist < dist.get(neighbor, 1_000_000_000):
                dist[neighbor] = new_dist
                came_from[neighbor] = current
                heapq.heappush(heap, (new_dist, neighbor))

    if not found:
        yield {"visited": set(visited), "path": []}


def solve_a_star(grid: Grid, start: Point, goal: Point) -> Iterable[StepState]:
    _validate_start_goal(grid, start, goal)

    def heuristic(a: Point, b: Point) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    heap: list[tuple[int, int, Point]] = [(heuristic(start, goal), 0, start)]
    g_score: dict[Point, int] = {start: 0}
    came_from: dict[Point, Point | None] = {start: None}
    visited: set[Point] = set()
    found = False

    while heap:
        _, current_g, current = heapq.heappop(heap)
        if current in visited:
            continue
        visited.add(current)
        yield {
            "visited": set(visited),
            "path": _reconstruct_path(came_from, current),
        }
        if current == goal:
            found = True
            break
        for neighbor in _neighbors(grid, current):
            if neighbor in visited:
                continue
            tentative_g = current_g + 1
            if tentative_g < g_score.get(neighbor, 1_000_000_000):
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(heap, (f_score, tentative_g, neighbor))

    if not found:
        yield {"visited": set(visited), "path": []}


def _neighbors(grid: Grid, point: Point) -> list[Point]:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    r, c = point
    candidates = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
    return [
        (nr, nc)
        for nr, nc in candidates
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1
    ]


def _reconstruct_path(came_from: dict[Point, Point | None], end: Point) -> list[Point]:
    path: list[Point] = [end]
    current: Point = end
    next_point = came_from[current]
    while next_point is not None:
        current = next_point
        path.append(current)
        next_point = came_from[current]
    path.reverse()
    return path


def _validate_start_goal(grid: Grid, start: Point, goal: Point) -> None:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if rows == 0 or cols == 0:
        raise ValueError("grid must be non-empty")

    for name, point in ("start", start), ("goal", goal):
        r, c = point
        if not (0 <= r < rows and 0 <= c < cols):
            raise ValueError(f"{name} is out of bounds: {point}")
        if grid[r][c] != 1:
            raise ValueError(f"{name} must be on a path cell: {point}")

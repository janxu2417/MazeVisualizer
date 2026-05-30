from __future__ import annotations

from collections import deque
import heapq
import random
from typing import Iterable, List, Tuple

Grid = List[List[int]]
Point = Tuple[int, int]
StepState = dict


def generate_maze(
    rows: int,
    cols: int,
    seed: int | None = None,
    loop_chance: float = 0.0,
    method: str = "dfs",
) -> Grid:
    """Generate a maze using the selected method.

    The maze uses a grid where 0 = wall, 1 = path. Rows/cols will be
    adjusted to odd numbers to simplify carving. A small loop_chance
    can be used to punch extra openings and create cycles.
    """
    if rows < 3 or cols < 3:
        raise ValueError("rows and cols must be >= 3")

    rows, cols = _normalize_size(rows, cols)
    rng = random.Random(seed)

    if method == "dfs":
        grid = _generate_maze_dfs(rows, cols, rng)
    elif method == "prim":
        grid = _generate_maze_prim(rows, cols, rng)
    elif method == "kruskal":
        grid = _generate_maze_kruskal(rows, cols, rng)
    else:
        raise ValueError(f"unknown maze method: {method}")

    _add_loops(grid, rng, loop_chance)
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


def solve_bidirectional_bfs(grid: Grid, start: Point, goal: Point) -> Iterable[StepState]:
    _validate_start_goal(grid, start, goal)

    if start == goal:
        yield {"visited": {start}, "path": [start]}
        return

    queue_start = deque([start])
    queue_goal = deque([goal])
    parents_start: dict[Point, Point | None] = {start: None}
    parents_goal: dict[Point, Point | None] = {goal: None}
    visited_start: set[Point] = {start}
    visited_goal: set[Point] = {goal}
    meet: Point | None = None

    while queue_start and queue_goal:
        meet = _bidir_step(grid, queue_start, visited_start, parents_start, visited_goal)
        if meet is not None:
            break
        meet = _bidir_step(grid, queue_goal, visited_goal, parents_goal, visited_start)
        if meet is not None:
            break
        current = queue_start[0] if queue_start else start
        yield {
            "visited": set(visited_start | visited_goal),
            "path": _reconstruct_path(parents_start, current),
        }

    if meet is None:
        yield {"visited": set(visited_start | visited_goal), "path": []}
        return

    path_start = _reconstruct_path(parents_start, meet)
    path_goal = _reconstruct_path(parents_goal, meet)
    path = path_start + list(reversed(path_goal[:-1]))
    yield {"visited": set(visited_start | visited_goal), "path": path}


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


def solve_greedy_best_first(grid: Grid, start: Point, goal: Point) -> Iterable[StepState]:
    _validate_start_goal(grid, start, goal)

    def heuristic(a: Point, b: Point) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    heap: list[tuple[int, Point]] = [(heuristic(start, goal), start)]
    came_from: dict[Point, Point | None] = {start: None}
    visited: set[Point] = set()
    found = False

    while heap:
        _, current = heapq.heappop(heap)
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
            if neighbor not in came_from:
                came_from[neighbor] = current
            heapq.heappush(heap, (heuristic(neighbor, goal), neighbor))

    if not found:
        yield {"visited": set(visited), "path": []}


def solve_weighted_a_star(
    grid: Grid,
    start: Point,
    goal: Point,
    weight: float = 1.5,
) -> Iterable[StepState]:
    _validate_start_goal(grid, start, goal)

    def heuristic(a: Point, b: Point) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    heap: list[tuple[float, int, Point]] = [(heuristic(start, goal) * weight, 0, start)]
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
                f_score = tentative_g + weight * heuristic(neighbor, goal)
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


def _add_loops(grid: Grid, rng: random.Random, loop_chance: float) -> None:
    if loop_chance <= 0:
        return

    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid[r][c] != 0:
                continue
            vertical = grid[r - 1][c] == 1 and grid[r + 1][c] == 1
            horizontal = grid[r][c - 1] == 1 and grid[r][c + 1] == 1
            if vertical or horizontal:
                if rng.random() < loop_chance:
                    grid[r][c] = 1


def _normalize_size(rows: int, cols: int) -> tuple[int, int]:
    if rows % 2 == 0:
        rows += 1
    if cols % 2 == 0:
        cols += 1
    return rows, cols


def _generate_maze_dfs(rows: int, cols: int, rng: random.Random) -> Grid:
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
                _carve_passage(grid, (r, c), (nr, nc))
                stack.append((nr, nc))
                carved = True
                break
        if not carved:
            stack.pop()

    return grid


def _generate_maze_prim(rows: int, cols: int, rng: random.Random) -> Grid:
    grid: Grid = [[0 for _ in range(cols)] for _ in range(rows)]
    start: Point = (1, 1)
    grid[start[0]][start[1]] = 1

    visited: set[Point] = {start}
    frontier: list[Point] = []
    frontier_set: set[Point] = set()

    def add_frontier(cell: Point) -> None:
        for neighbor in _neighbors_two_steps(cell, rows, cols):
            if neighbor not in visited and neighbor not in frontier_set:
                frontier.append(neighbor)
                frontier_set.add(neighbor)

    add_frontier(start)

    while frontier:
        cell = rng.choice(frontier)
        frontier.remove(cell)
        frontier_set.discard(cell)
        if cell in visited:
            continue
        neighbors = [n for n in _neighbors_two_steps(cell, rows, cols) if n in visited]
        if not neighbors:
            continue
        neighbor = rng.choice(neighbors)
        _carve_passage(grid, cell, neighbor)
        visited.add(cell)
        add_frontier(cell)

    return grid


def _generate_maze_kruskal(rows: int, cols: int, rng: random.Random) -> Grid:
    grid: Grid = [[0 for _ in range(cols)] for _ in range(rows)]
    cells = [(r, c) for r in range(1, rows, 2) for c in range(1, cols, 2)]
    index = {cell: idx for idx, cell in enumerate(cells)}

    for r, c in cells:
        grid[r][c] = 1

    edges: list[tuple[Point, Point]] = []
    for r, c in cells:
        if r + 2 < rows:
            edges.append(((r, c), (r + 2, c)))
        if c + 2 < cols:
            edges.append(((r, c), (r, c + 2)))

    rng.shuffle(edges)
    dsu = _DisjointSet(len(cells))

    for a, b in edges:
        if dsu.union(index[a], index[b]):
            _carve_passage(grid, a, b)

    return grid


def _neighbors_two_steps(point: Point, rows: int, cols: int) -> list[Point]:
    r, c = point
    candidates = [(r - 2, c), (r + 2, c), (r, c - 2), (r, c + 2)]
    return [(nr, nc) for nr, nc in candidates if 1 <= nr < rows - 1 and 1 <= nc < cols - 1]


def _carve_passage(grid: Grid, a: Point, b: Point) -> None:
    ar, ac = a
    br, bc = b
    grid[ar][ac] = 1
    grid[br][bc] = 1
    grid[(ar + br) // 2][(ac + bc) // 2] = 1


def _bidir_step(
    grid: Grid,
    queue: deque[Point],
    visited: set[Point],
    parents: dict[Point, Point | None],
    other_visited: set[Point],
) -> Point | None:
    if not queue:
        return None
    current = queue.popleft()
    for neighbor in _neighbors(grid, current):
        if neighbor in visited:
            continue
        visited.add(neighbor)
        parents[neighbor] = current
        if neighbor in other_visited:
            return neighbor
        queue.append(neighbor)
    return None


class _DisjointSet:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, a: int, b: int) -> bool:
        root_a = self.find(a)
        root_b = self.find(b)
        if root_a == root_b:
            return False
        if self.rank[root_a] < self.rank[root_b]:
            self.parent[root_a] = root_b
        elif self.rank[root_a] > self.rank[root_b]:
            self.parent[root_b] = root_a
        else:
            self.parent[root_b] = root_a
            self.rank[root_a] += 1
        return True

from __future__ import annotations

from collections import deque
import heapq
from typing import Iterable

from step_data import Grid, Point, CostMap, RunStats, StepState

def solve_bfs(
    grid: Grid,
    start: Point,
    goal: Point,
    *,
    weight: float = 1.0,
    cost_map: CostMap | None = None,
) -> Iterable[StepState]:
    """Breadth-first search — layer-by-layer expansion from the start.

    Uses a FIFO queue (``collections.deque``).  On uniform grids BFS
    guarantees a shortest path in terms of step count.  When *cost_map*
    is provided, BFS still only considers step count, not terrain cost,
    so the result is marked *not* optimal for weighted problems.

    Algorithm summary
    -----------------
    1. Enqueue *start*, mark as visited.
    2. Dequeue a node, yield a :class:`StepState` frame.
    3. If it is the goal, terminate.
    4. Enqueue all unvisited, traversable neighbours.
    5. Repeat until the queue is empty.

    Complexity
    ----------
    - Time:  Θ(V + E) — each vertex and edge processed at most once.
    - Space: O(V)  — the queue and ``came_from`` dictionary.

    Course knowledge
    ----------------
    - Graph representation (implicit grid graph → adjacency by 4-directional
      traversal).
    - BFS traversal with a ``deque`` (FIFO queue).
    - Unweighted shortest-path property.

    Yields:
        :class:`StepState` frames.
    """
    del weight
    _validate_start_goal(grid, start, goal)

    queue = deque([start])
    came_from: dict[Point, Point | None] = {start: None}
    visited: set[Point] = {start}
    step_count = 0

    while queue:
        current = queue.popleft()
        step_count += 1
        path = _reconstruct_path(came_from, current)
        finished = current == goal
        yield _make_step_state(
            current=current,
            visited=visited,
            frontier=set(queue),
            path=path,
            finished=finished,
            step_count=step_count,
            optimal=cost_map is None,
            cost_map=cost_map,
            visited_count=step_count,
        )
        if finished:
            return
        for neighbor in _neighbors(grid, current):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            came_from[neighbor] = current
            queue.append(neighbor)

    yield _make_step_state(
        current=None,
        visited=visited,
        frontier=set(),
        path=[],
        finished=True,
        step_count=step_count,
        optimal=cost_map is None,
        cost_map=cost_map,
        visited_count=step_count,
    )


def solve_bidirectional_bfs(
    grid: Grid,
    start: Point,
    goal: Point,
    *,
    weight: float = 1.0,
    cost_map: CostMap | None = None,
) -> Iterable[StepState]:
    """Bidirectional BFS — expand from both start and goal simultaneously.

    Maintains two independent BFS frontiers.  When one side discovers a
    node already visited by the other side, the two partial paths are
    merged to form the complete solution.  On unweighted grids this
    guarantees a shortest path and often explores far fewer nodes than
    a single-direction BFS.

    Each frame reports *visited_from_start* and *visited_from_goal* so
    the UI can render both search fronts distinctly.  The *meet_point*
    is set when the two searches intersect.

    Complexity
    ----------
    - Time:  O(b^(d/2)) in the worst case on a branching-factor-b grid;
             practically much better than unidirectional BFS.
    - Space: O(V) for the two queues and parent dictionaries.

    Course knowledge
    ----------------
    - Bidirectional search strategy.
    - BFS as a building block for meet-in-the-middle.
    - Path reconstruction from two partial parent trees.
    """
    del weight
    _validate_start_goal(grid, start, goal)

    if start == goal:
        yield _make_step_state(
            current=start,
            visited={start},
            frontier=set(),
            path=[start],
            finished=True,
            step_count=0,
            optimal=cost_map is None,
            cost_map=cost_map,
            visited_from_start={start},
            visited_from_goal={goal},
            meet_point=start,
            visited_count=1,
        )
        return

    queue_start = deque([start])
    queue_goal = deque([goal])
    parents_start: dict[Point, Point | None] = {start: None}
    parents_goal: dict[Point, Point | None] = {goal: None}
    visited_start: set[Point] = {start}
    visited_goal: set[Point] = {goal}
    meet: Point | None = None
    current: Point | None = None
    step_count = 0

    while queue_start and queue_goal:
        step_count += 1
        meet, current = _bidir_step(grid, queue_start, visited_start, parents_start, visited_goal)
        if meet is not None:
            path = _merge_bidirectional_path(parents_start, parents_goal, meet)
            visited_union = visited_start | visited_goal
            yield _make_step_state(
                current=current,
                visited=visited_union,
                frontier=set(queue_start) | set(queue_goal),
                path=path,
                finished=True,
                step_count=step_count,
                optimal=cost_map is None,
                cost_map=cost_map,
                visited_from_start=visited_start,
                visited_from_goal=visited_goal,
                meet_point=meet,
                visited_count=len(visited_union),
            )
            return

        step_count += 1
        meet, current = _bidir_step(grid, queue_goal, visited_goal, parents_goal, visited_start)
        if meet is not None:
            path = _merge_bidirectional_path(parents_start, parents_goal, meet)
            visited_union = visited_start | visited_goal
            yield _make_step_state(
                current=current,
                visited=visited_union,
                frontier=set(queue_start) | set(queue_goal),
                path=path,
                finished=True,
                step_count=step_count,
                optimal=cost_map is None,
                cost_map=cost_map,
                visited_from_start=visited_start,
                visited_from_goal=visited_goal,
                meet_point=meet,
                visited_count=len(visited_union),
            )
            return

        if current is None:
            preview_path = []
        elif current in parents_start:
            preview_path = _reconstruct_path(parents_start, current)
        elif current in parents_goal:
            preview_path = list(reversed(_reconstruct_path(parents_goal, current)))
        else:
            preview_path = []
        visited_union = visited_start | visited_goal
        yield _make_step_state(
            current=current,
            visited=visited_union,
            frontier=set(queue_start) | set(queue_goal),
            path=preview_path,
            finished=False,
            step_count=step_count,
            optimal=cost_map is None,
            cost_map=cost_map,
            visited_from_start=visited_start,
            visited_from_goal=visited_goal,
            meet_point=None,
            visited_count=len(visited_union),
        )

    visited_union = visited_start | visited_goal
    yield _make_step_state(
        current=None,
        visited=visited_union,
        frontier=set(queue_start) | set(queue_goal),
        path=[],
        finished=True,
        step_count=step_count,
        optimal=cost_map is None,
        cost_map=cost_map,
        visited_from_start=visited_start,
        visited_from_goal=visited_goal,
        meet_point=None,
        visited_count=len(visited_union),
    )


def solve_dijkstra(
    grid: Grid,
    start: Point,
    goal: Point,
    *,
    weight: float = 1.0,
    cost_map: CostMap | None = None,
) -> Iterable[StepState]:
    """Dijkstra's shortest-path algorithm — greedy expansion by accumulated cost.

    Uses a binary min-heap (``heapq``).  At each step the node with the
    smallest known distance is extracted and expanded.  On uniform grids
    this behaves identically to BFS; with a non-uniform *cost_map* it
    guarantees a minimum-cost path.

    Algorithm summary
    -----------------
    1. Push *start* onto the heap with distance 0.
    2. Pop the minimum-distance node, mark as visited, yield a frame.
    3. If it is the goal, terminate (the path is optimal).
    4. For each unvisited neighbour, relax the edge: if a shorter
       distance is found, update and push onto the heap.
    5. Repeat until the heap is empty.

    Complexity
    ----------
    - Time:  O((V + E) log V) — each of E relaxations may trigger
             a O(log V) heap push.
    - Space: O(V) for the distance dictionary and heap.

    Course knowledge
    ----------------
    - Priority queue / binary heap (``heapq`` module).
    - Greedy algorithm paradigm.
    - Single-source shortest path on non-negative weighted graphs.
    - Edge relaxation.
    """
    del weight
    _validate_start_goal(grid, start, goal)
    active_cost_map = cost_map or _build_uniform_cost_map(grid)

    heap: list[tuple[int, Point]] = [(0, start)]
    dist: dict[Point, int] = {start: 0}
    came_from: dict[Point, Point | None] = {start: None}
    visited: set[Point] = set()
    step_count = 0

    while heap:
        current_dist, current = heapq.heappop(heap)
        if current in visited:
            continue
        visited.add(current)
        step_count += 1
        path = _reconstruct_path(came_from, current)
        finished = current == goal
        frontier = {point for _, point in heap if point not in visited}
        yield _make_step_state(
            current=current,
            visited=visited,
            frontier=frontier,
            path=path,
            finished=finished,
            step_count=step_count,
            optimal=True,
            cost_map=active_cost_map,
        )
        if finished:
            return
        for neighbor in _neighbors(grid, current):
            if neighbor in visited:
                continue
            new_dist = current_dist + _cell_cost(active_cost_map, neighbor)
            if new_dist < dist.get(neighbor, 1_000_000_000):
                dist[neighbor] = new_dist
                came_from[neighbor] = current
                heapq.heappush(heap, (new_dist, neighbor))

    yield _make_step_state(
        current=None,
        visited=visited,
        frontier=set(),
        path=[],
        finished=True,
        step_count=step_count,
        optimal=True,
        cost_map=active_cost_map,
    )


def solve_a_star(
    grid: Grid,
    start: Point,
    goal: Point,
    *,
    weight: float = 1.0,
    cost_map: CostMap | None = None,
) -> Iterable[StepState]:
    """A* search — Dijkstra augmented with an admissible heuristic.

    Evaluation function: ``f(n) = g(n) + h(n)``, where:
    - ``g(n)``: best-known cost from start to node *n*.
    - ``h(n)``: Manhattan-distance heuristic estimate from *n* to goal.

    With *h* admissible (never overestimates), A* guarantees optimality
    while expanding fewer nodes than Dijkstra on average.  The *weight*
    parameter allows tuning: ``weight=1.0`` gives standard A*; higher
    values bias toward the goal (behaving like Weighted A*).

    Complexity
    ----------
    - Time:  O((V + E) log V) worst-case; often sub-linear in practice
             with a good heuristic.
    - Space: O(V) for the g-score dictionary and heap.

    Course knowledge
    ----------------
    - Heuristic / informed search (contrast with blind BFS/Dijkstra).
    - Admissibility and consistency of heuristics.
    - Priority queue (min-heap) with composite key ``(f, g, node)``.
    - Manhattan distance on grid graphs.
    """
    _validate_start_goal(grid, start, goal)
    active_cost_map = cost_map or _build_uniform_cost_map(grid)

    heap: list[tuple[float, int, Point]] = [(_heuristic(start, goal), 0, start)]
    g_score: dict[Point, int] = {start: 0}
    came_from: dict[Point, Point | None] = {start: None}
    visited: set[Point] = set()
    step_count = 0

    while heap:
        _, current_g, current = heapq.heappop(heap)
        if current in visited:
            continue
        visited.add(current)
        step_count += 1
        path = _reconstruct_path(came_from, current)
        finished = current == goal
        frontier = {point for _, _, point in heap if point not in visited}
        yield _make_step_state(
            current=current,
            visited=visited,
            frontier=frontier,
            path=path,
            finished=finished,
            step_count=step_count,
            optimal=True,
            cost_map=active_cost_map,
        )
        if finished:
            return
        for neighbor in _neighbors(grid, current):
            if neighbor in visited:
                continue
            tentative_g = current_g + _cell_cost(active_cost_map, neighbor)
            if tentative_g < g_score.get(neighbor, 1_000_000_000):
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                f_score = tentative_g + weight * _heuristic(neighbor, goal)
                heapq.heappush(heap, (f_score, tentative_g, neighbor))

    yield _make_step_state(
        current=None,
        visited=visited,
        frontier=set(),
        path=[],
        finished=True,
        step_count=step_count,
        optimal=True,
        cost_map=active_cost_map,
    )



def solve_greedy_best_first(
    grid: Grid,
    start: Point,
    goal: Point,
    *,
    weight: float = 1.0,
    cost_map: CostMap | None = None,
) -> Iterable[StepState]:
    """Greedy Best-First Search — heuristic-only expansion.

    Uses only the heuristic ``h(n)`` to select the next node, ignoring
    the actual path cost ``g(n)``.  This makes it very fast in practice
    but **does not guarantee optimality** — it may produce longer or
    costlier paths than BFS/Dijkstra/A*.

    Useful for demonstrating the speed-vs-optimality trade-off and for
    contrasting with A* (which adds the g-cost term).

    Complexity
    ----------
    - Time:  O((V + E) log V) worst-case; often very fast on open mazes.
    - Space: O(V) for the frontier heap and came-from map.

    Course knowledge
    ----------------
    - Greedy algorithm paradigm (local heuristic choice).
    - Comparison between informed (heuristic) and uninformed (BFS) search.
    - Optimality vs. speed trade-off in heuristic search.
    """
    del weight
    _validate_start_goal(grid, start, goal)

    heap: list[tuple[int, Point]] = [(_heuristic(start, goal), start)]
    came_from: dict[Point, Point | None] = {start: None}
    visited: set[Point] = set()
    frontier: set[Point] = {start}
    step_count = 0

    while heap:
        _, current = heapq.heappop(heap)
        frontier.discard(current)
        if current in visited:
            continue
        visited.add(current)
        step_count += 1
        path = _reconstruct_path(came_from, current)
        finished = current == goal
        yield _make_step_state(
            current=current,
            visited=visited,
            frontier=frontier,
            path=path,
            finished=finished,
            step_count=step_count,
            optimal=False,
            cost_map=cost_map,
        )
        if finished:
            return
        for neighbor in _neighbors(grid, current):
            if neighbor in visited:
                continue
            if neighbor not in came_from:
                came_from[neighbor] = current
            heapq.heappush(heap, (_heuristic(neighbor, goal), neighbor))
            frontier.add(neighbor)

    yield _make_step_state(
        current=None,
        visited=visited,
        frontier=frontier,
        path=[],
        finished=True,
        step_count=step_count,
        optimal=False,
        cost_map=cost_map,
    )


def solve_weighted_a_star(
    grid: Grid,
    start: Point,
    goal: Point,
    *,
    weight: float = 1.5,
    cost_map: CostMap | None = None,
) -> Iterable[StepState]:
    """Weighted A* — A* with inflated heuristic for speed.

    Evaluation function: ``f(n) = g(n) + W * h(n)`` where ``W >= 1``.

    By multiplying the heuristic term by *weight* > 1, the search is
    biased more aggressively toward the goal, often reaching it in
    fewer expansions.  The trade-off is that the solution may be
    suboptimal — the cost is bounded by ``W * optimal_cost``
    (ε-admissible).

    In this project the user can tweak *W* at runtime (keys ``[`` / ``]``)
    to interactively observe the speed-vs-optimality spectrum.

    Complexity
    ----------
    - Time:  O((V + E) log V); fewer expansions than A* when W > 1.
    - Space: O(V) for g-score dictionary and heap.

    Course knowledge
    ----------------
    - Extension of A* with bounded sub-optimality.
    - Heuristic inflation / ε-admissibility.
    - Practical trade-off between search effort and solution quality.
    """
    _validate_start_goal(grid, start, goal)
    active_cost_map = cost_map or _build_uniform_cost_map(grid)

    heap: list[tuple[float, int, Point]] = [(_heuristic(start, goal) * weight, 0, start)]
    g_score: dict[Point, int] = {start: 0}
    came_from: dict[Point, Point | None] = {start: None}
    visited: set[Point] = set()
    step_count = 0

    while heap:
        _, current_g, current = heapq.heappop(heap)
        if current in visited:
            continue
        visited.add(current)
        step_count += 1
        path = _reconstruct_path(came_from, current)
        finished = current == goal
        frontier = {point for _, _, point in heap if point not in visited}
        yield _make_step_state(
            current=current,
            visited=visited,
            frontier=frontier,
            path=path,
            finished=finished,
            step_count=step_count,
            optimal=False,
            cost_map=active_cost_map,
        )
        if finished:
            return
        for neighbor in _neighbors(grid, current):
            if neighbor in visited:
                continue
            tentative_g = current_g + _cell_cost(active_cost_map, neighbor)
            if tentative_g < g_score.get(neighbor, 1_000_000_000):
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                f_score = tentative_g + weight * _heuristic(neighbor, goal)
                heapq.heappush(heap, (f_score, tentative_g, neighbor))

    yield _make_step_state(
        current=None,
        visited=visited,
        frontier=set(),
        path=[],
        finished=True,
        step_count=step_count,
        optimal=False,
        cost_map=active_cost_map,
    )


def _make_step_state(
    *,
    current: Point | None,
    visited: set[Point],
    frontier: set[Point],
    path: list[Point],
    finished: bool,
    step_count: int,
    optimal: bool,
    cost_map: CostMap | None = None,
    visited_from_start: set[Point] | None = None,
    visited_from_goal: set[Point] | None = None,
    meet_point: Point | None = None,
    visited_count: int | None = None,
) -> StepState:
    """Construct a :class:`StepState` frame from raw solver internals.

    Computes :class:`RunStats` (visited count, path length, path cost) and
    copies all collections to prevent shared-mutation bugs between the
    solver and the UI layer.  Optional bi-directional fields default to
    empty sets / ``None``.

    *visited_count* overrides the auto-calculated ``len(visited)`` — used
    by BFS-family solvers where *visited* tracks discovered (not yet
    expanded) nodes.
    """
    stats = RunStats(
        visited_count=visited_count if visited_count is not None else len(visited),
        path_length=max(0, len(path) - 1),
        step_count=step_count,
        optimal=optimal,
        cost=_path_cost(path, cost_map),
    )
    return StepState(
        current=current,
        visited=set(visited),
        frontier=set(frontier),
        path=list(path),
        finished=finished,
        stats=stats,
        visited_from_start=set(visited_from_start or set()),
        visited_from_goal=set(visited_from_goal or set()),
        meet_point=meet_point,
    )


def _neighbors(grid: Grid, point: Point) -> list[Point]:
    """Return the (up to 4) neighbouring path cells of *point*.

    Neighbours are checked in the order up, down, left, right.
    Only cells within grid bounds and with value ``1`` are included.
    """
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
    """Walk backwards from *end* through the *came_from* parent map.

    Returns the path as a list from start to *end* (inclusive).
    Assumes the parent map forms a valid tree rooted at the start node.
    """
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
    """Raise ``ValueError`` if *start* or *goal* is out of bounds or on a wall.

    Called by every solver before beginning search.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if rows == 0 or cols == 0:
        raise ValueError("grid must be non-empty")

    for name, point in (("start", start), ("goal", goal)):
        r, c = point
        if not (0 <= r < rows and 0 <= c < cols):
            raise ValueError(f"{name} is out of bounds: {point}")
        if grid[r][c] != 1:
            raise ValueError(f"{name} must be on a path cell: {point}")


def _bidir_step(
    grid: Grid,
    queue: deque[Point],
    visited: set[Point],
    parents: dict[Point, Point | None],
    other_visited: set[Point],
) -> tuple[Point | None, Point | None]:
    """Perform one expansion step for bidirectional BFS.

    Dequeues one node, explores its neighbours.  If any neighbour has
    already been visited by the *other* side, the search ends — returns
    ``(meet_point, neighbour)``.  Otherwise returns ``(None, current)``
    to continue.
    """
    if not queue:
        return None, None
    current = queue.popleft()
    for neighbor in _neighbors(grid, current):
        if neighbor in visited:
            continue
        visited.add(neighbor)
        parents[neighbor] = current
        if neighbor in other_visited:
            return neighbor, neighbor
        queue.append(neighbor)
    return None, current



def _merge_bidirectional_path(
    parents_start: dict[Point, Point | None],
    parents_goal: dict[Point, Point | None],
    meet: Point,
) -> list[Point]:
    """Merge the two partial paths from bidirectional BFS at the meeting point.

    Returns the full path: ``start → ... → meet → ... → goal``.
    """
    path_start = _reconstruct_path(parents_start, meet)
    path_goal = _reconstruct_path(parents_goal, meet)
    return path_start + list(reversed(path_goal[:-1]))


def _heuristic(a: Point, b: Point) -> int:
    """Manhattan distance: ``|r_a - r_b| + |c_a - c_b|``.

    An admissible heuristic for grid-based pathfinding (never overestimates
    the true cost, since each move changes exactly one coordinate by 1).
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])



def _path_cost(path: list[Point], cost_map: CostMap | None) -> int:
    """Compute the total terrain cost of *path*.

    If *cost_map* is ``None``, each step costs 1 (simple step count).
    The start cell's cost is excluded (only edge costs are summed).
    """
    if not path:
        return 0
    if cost_map is None:
        return max(0, len(path) - 1)
    return sum(_cell_cost(cost_map, point) for point in path[1:])


def _cell_cost(cost_map: CostMap, point: Point) -> int:
    """Look up the terrain cost at *point* in the cost map."""
    r, c = point
    return cost_map[r][c]


def _build_uniform_cost_map(grid: Grid) -> CostMap:
    """Build a cost map where every path cell has cost ``1``.

    Used when terrain mode is off, so all algorithms see a uniform grid.
    """
    return [[1 if cell == 1 else 0 for cell in row] for row in grid]



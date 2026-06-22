from __future__ import annotations

from collections import deque
import random
from typing import List

from step_data import Grid, Point, CostMap

def generate_maze(
    rows: int,
    cols: int,
    seed: int | None = None,
    loop_chance: float = 0.0,
    method: str = "dfs",
) -> Grid:
    """Generate a perfect (tree-structured) maze, optionally with loops.

    Uses one of three generation methods:
    - ``"dfs"``: Randomised depth-first search with explicit backtracking.
      Produces long corridors with few branches.
      Time O(rows*cols), Space O(rows*cols).
    - ``"prim"``: Frontier-based expansion analogous to Prim's MST algorithm.
      Produces many short dead-ends and local branches.
      Time O(rows*cols), Space O(rows*cols).
    - ``"kruskal"``: Randomised Kruskal's MST using disjoint-set union.
      Uniformly random among all possible spanning-tree mazes.
      Time O(rows*cols * α(V)), Space O(rows*cols).

    Rows/cols are normalised to odd integers internally.  Set *loop_chance*
    to a small positive value (e.g. 0.08) to punch extra openings and
    create cycles, making the maze non-perfect and enabling multiple
    solutions.

    Args:
        rows: Maze height; must be >= 3, adjusted to odd if even.
        cols: Maze width; must be >= 3, adjusted to odd if even.
        seed: Random seed for reproducibility.
        loop_chance: Probability of removing a wall that separates two
            already-connected path cells (default 0 = perfect maze).
        method: One of ``"dfs"``, ``"prim"``, ``"kruskal"``.

    Returns:
        A 2-D grid of ints: ``0`` = wall, ``1`` = path cell.

    Raises:
        ValueError: If *rows* or *cols* < 3, or *method* is unknown.

    Course knowledge:
        - DFS / backtracking (stack-based graph traversal)
        - Prim's algorithm (minimum spanning tree, frontier / cut-set)
        - Kruskal's algorithm + Union-Find / Disjoint-Set Union
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

def _add_loops(grid: Grid, rng: random.Random, loop_chance: float) -> None:
    """Punch extra openings in the maze to create cycles.

    For each internal wall cell that separates two existing path cells,
    remove it with probability *loop_chance*.  This converts a perfect
    (tree) maze into one with multiple solutions, making pathfinding
    more interesting and enabling shortest-path vs. alternate-path
    demonstrations.

    Complexity: O(rows * cols).
    """
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
            if (vertical or horizontal) and rng.random() < loop_chance:
                grid[r][c] = 1


def _normalize_size(rows: int, cols: int) -> tuple[int, int]:
    """Force odd dimensions so maze carving can work in 2-cell steps.

    Maze generation algorithms move two cells at a time to leave a wall
    layer between passages.  Odd dimensions ensure the border walls
    align properly.
    """
    if rows % 2 == 0:
        rows += 1
    if cols % 2 == 0:
        cols += 1
    return rows, cols


def _generate_maze_dfs(rows: int, cols: int, rng: random.Random) -> Grid:
    """Generate a maze using randomised depth-first search with backtracking.

    Starts at (1, 1), uses a stack to track the current carving path,
    and moves in 2-cell steps.  When the current cell has no unvisited
    neighbours, the algorithm backtracks by popping the stack.

    Produces long, winding corridors with relatively few branches —
    the "classic" maze look.

    Complexity: O(rows * cols) time and space.

    Course knowledge: DFS (explicit stack), backtracking.
    """
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
    """Generate a maze using Prim's-algorithm-style frontier expansion.

    Maintains a *frontier set* of cells just outside the growing tree.
    At each step a random frontier cell is chosen and connected back
    to a random already-visited neighbour.

    Compared to DFS, this produces many short dead-ends and a more
    "bushy" structure.

    Complexity: O(rows * cols) time and space.

    Course knowledge: Prim's MST, frontier / cut-set expansion.
    """
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
    """Generate a maze using randomised Kruskal's MST algorithm.

    Treats odd-index path cells as graph vertices and intervening wall
    cells as candidate edges.  Edges are shuffled and processed through
    a disjoint-set union (DSU / Union-Find) structure; an edge is kept
    only if its endpoints belong to different components, preventing
    cycles.

    Among the three methods this produces the most "uniformly random"
    spanning-tree maze distribution.

    Complexity
    ----------
    - Time:  O(rows * cols * α(V)) where α is the inverse Ackermann
             function (nearly constant).
    - Space: O(rows * cols).

    Course knowledge: Kruskal's MST, Union-Find / Disjoint-Set Union
    with path compression and union by rank.
    """
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
    """Return cells two steps away from *point* (used by maze generation).

    Maze carving moves two cells at a time so the intermediate cell
    becomes a wall between passages.  Only cells strictly within the
    interior (1 <= r < rows-1, 1 <= c < cols-1) are returned.
    """
    r, c = point
    candidates = [(r - 2, c), (r + 2, c), (r, c - 2), (r, c + 2)]
    return [(nr, nc) for nr, nc in candidates if 1 <= nr < rows - 1 and 1 <= nc < cols - 1]


def _carve_passage(grid: Grid, a: Point, b: Point) -> None:
    """Carve a passage between two cells (including the mid-wall cell).

    Sets *a*, *b*, and the cell halfway between them to ``1`` (path).
    Called by all three maze generation algorithms.
    """
    ar, ac = a
    br, bc = b
    grid[ar][ac] = 1
    grid[br][bc] = 1
    grid[(ar + br) // 2][(ac + bc) // 2] = 1


class _DisjointSet:
    """Disjoint-Set Union (Union-Find) with path compression and union by rank.

    Used by Kruskal's maze generator to efficiently test and merge
    connected components while preventing cycles.

    Complexity
    ----------
    - ``find``: nearly O(1) amortised (inverse Ackermann).
    - ``union``: nearly O(1) amortised.

    Course knowledge: Union-Find / DSU data structure.
    """

    def __init__(self, size: int) -> None:
        """Initialise *size* singleton sets labeled ``0 … size-1``."""
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item: int) -> int:
        """Find the representative (root) of *item*'s set.

        Applies path compression: every node on the lookup path is
        linked directly to the root.
        """
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, a: int, b: int) -> bool:
        """Merge the sets containing *a* and *b*.

        Uses union by rank: the shorter tree is attached under the
        taller tree's root.  Returns ``True`` if the sets were merged,
        ``False`` if they were already in the same set.
        """
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


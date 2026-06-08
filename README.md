# MazeVisualizer

[中文说明 / Chinese README](README_zh.md)

## Project Background

MazeVisualizer is a Python + Pygame project for visualizing maze generation and pathfinding algorithms step by step.
It is designed as a Data Structures and Algorithms course project with emphasis on:

- self-implemented maze generation and graph search logic
- clear separation between algorithm logic and UI rendering
- visual comparison between different search strategies
- explainable algorithm behavior rather than black-box library calls

## Features

- Maze generation: DFS backtracking, Prim, Kruskal
- Pathfinding: BFS, Dijkstra, A*, Bidirectional BFS, Greedy Best-First, Weighted A*
- Frontier / open-set visualization
- Bidirectional BFS two-side expansion visualization
- Weighted terrain mode for cost-sensitive shortest path
- Runtime stats: path length, visited nodes, search steps, path cost, optimality
- Comparison board for multiple algorithms on the same maze

## Project Structure

```text
MazeVisualizer/
├── src/
│   ├── algorithms.py
│   ├── app.py
│   ├── config.py
│   ├── menu.py
│   ├── render.py
│   ├── main.py
│   └── ui.py
├── docs/
├── tests/
│   ├── test_algorithms.py
│   ├── test_algorithm_states.py
│   ├── test_app_logic.py
│   └── test_render_smoke.py
├── pytest.ini
├── README.md
├── README_zh.md
├── LICENSE
└── requirements.txt
```

## Core Algorithms

### Maze Generation

#### 1. DFS Backtracking

- The maze grid uses `0 = wall`, `1 = path`
- The algorithm moves in steps of 2 cells to preserve wall layers
- A stack records the current carving path
- When no unvisited neighbor exists, it backtracks

This creates corridor-like mazes with long passages.

#### 2. Prim-based Maze Generation

- Treat each candidate cell as a graph node
- Maintain a frontier set around the carved region
- Randomly choose a frontier cell and connect it to the existing tree

This tends to create more local branches and dead ends.

#### 3. Kruskal-based Maze Generation

- Treat odd-index cells as graph vertices
- Treat removable walls as candidate edges
- Use a disjoint-set union structure to connect components without cycles

This is a direct application of minimum-spanning-tree style thinking.

### Pathfinding

| Algorithm | Idea | Optimal? | Typical Time | Typical Space | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| BFS | layer-by-layer expansion | Yes on unweighted grids | `O(V+E)` | `O(V)` | shortest step count |
| Dijkstra | greedy shortest path by accumulated cost | Yes with nonnegative weights | `O((V+E)logV)` | `O(V)` | needed for weighted terrain |
| A* | Dijkstra + heuristic | Yes if heuristic is admissible | usually better than Dijkstra | `O(V)` | uses Manhattan distance |
| Bi-BFS | expand from both start and goal | Yes on unweighted grids | often less search in practice | `O(V)` | strong teaching value |
| Greedy Best-First | heuristic only | No | often fast | `O(V)` | may find suboptimal routes |
| Weighted A* | `f(n)=g(n)+W*h(n)` | Not always | often faster than A* | `O(V)` | trades optimality for speed |

### Why Weighted Terrain Matters

On a uniform grid, BFS, Dijkstra, and A* often end with the same shortest path length.
To better demonstrate the difference between unweighted and weighted shortest-path problems, this project adds an optional weighted terrain mode:

- normal road cost = 1
- medium terrain cost = 3
- heavy terrain cost = 5

In this mode:

- BFS still minimizes step count only
- Dijkstra minimizes total path cost
- A* and Weighted A* use both cost and heuristic information

This makes the algorithm comparison more meaningful for a course project.

## Visualization Design

Each solver yields step-by-step state frames. Every frame contains:

- current node
- visited set
- frontier / open set
- final path
- runtime stats
- extra two-side visited sets for Bidirectional BFS

UI updates in the current version:

- `visited`, `frontier`, and `current` use stable A/B/C color layers instead of flashing path previews
- for non-DFS-style algorithms, the path is drawn only after the goal is reached, which avoids flicker at high speed
- a built-in legend explains search colors and weighted-terrain cost bands
- Small / Medium / Large presets also adjust outer padding and font sizes for better screen fit

This design keeps algorithm logic independent from Pygame rendering.

## Controls

- `Space`: pause / resume
- `H`: show help panel
- `+/-`: adjust speed
- `1-6`: switch algorithm and rerun on the same maze
- `R`: restart current solver
- `C`: toggle comparison board
- `M`: generate a new maze
- `ESC`: close help panel or return to menu

Additional controls such as single-step, weighted-terrain toggle, and Weighted A* parameter adjustment are documented in the help panel.

## Run

1. Install dependencies

```bash
python -m pip install -r requirements.txt
```

2. Start the program

```bash
python src/main.py
```

You can also run:

```bash
python src/ui.py
```

## Tests

### How to run

Run all tests from the project root:

```bash
python -m pytest
```

Because `pytest.ini` is included, test discovery is fixed to the `tests/` directory and `test_*.py` files.

If you only want one test group:

```bash
python -m pytest tests/test_algorithms.py
python -m pytest tests/test_algorithm_states.py
python -m pytest tests/test_app_logic.py
python -m pytest tests/test_render_smoke.py
```

### Current test coverage

Automated tests currently cover:

- maze size normalization
- solvability of DFS / Prim / Kruskal mazes
- BFS shortest-path validity
- Dijkstra vs BFS on uniform grids
- A* vs BFS on uniform grids
- validity of Greedy and Weighted A* paths
- weighted terrain shortest-path behavior
- invalid input handling
- `StepState` / `RunStats` interface checks
- Bidirectional BFS meet-point and two-side visited-state checks
- app-level non-GUI logic: option application, clamping, terrain cost-map generation, solver creation, pause/help state transitions
- headless Pygame smoke tests for base-surface creation, menu rendering, HUD/help rendering, and run-view drawing

### Test Design for Report / PDF

For the course report, the testing strategy can be summarized as three layers:

1. **Algorithm correctness**
   Verifies maze solvability, shortest-path properties, weighted-path behavior, and error handling.
2. **State and controller logic**
   Verifies configuration updates, runtime state transitions, and the unified step-state interface consumed by the UI.
3. **Rendering smoke tests**
   Uses headless Pygame (`SDL_VIDEODRIVER=dummy`) to confirm that the main rendering paths execute without crashing.

### Suggested report text

You can reuse the following short paragraph in the PDF report:

> The project includes automated tests for algorithm correctness, runtime state transitions, and rendering smoke checks.
> All current tests pass under Python 3.13 with `pytest`, providing evidence that the maze generation, pathfinding logic, weighted terrain behavior, and core visualization pipeline are stable.

## Engineering Notes

- `algorithms.py` contains all core algorithms and step-state output
- `app.py` controls state transitions and solver execution
- `render.py` handles visualization and HUD panels
- `menu.py` handles menu layout and click dispatch
- `config.py` stores UI constants and runtime options

This modular structure is intended to satisfy the course requirement that logic and GUI should be separated.

## Docs and Screenshots

Place screenshots or GIFs in `docs/` and reference them in the PDF report.

![MazeVisualizer menu](docs/menu_v2.png)
![MazeVisualizer running view](docs/run_searching_v2.png)
![MazeVisualizer result view](docs/run_finished_v2.png)

Recommended report screenshots:

1. start menu
2. algorithm running view with legend and search-state layers
3. final statistics panel with comparison board and complete path

## AI Tool Declaration

AI-assisted work:

- GitHub Copilot and Codex were used to help scaffold UI structure, refactor modules, and polish documentation
- core maze generation and pathfinding logic was reviewed and adjusted manually
- final algorithm explanation, testing strategy, and course-facing write-up were curated by the author

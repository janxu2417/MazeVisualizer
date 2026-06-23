# MazeVisualizer

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5+-2E8B57?style=for-the-badge)](https://www.pygame.org/)
[![Pytest](https://img.shields.io/badge/Tests-78%20passed-0A7D38?style=for-the-badge)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://github.com/janxu2417/MazeVisualizer/blob/main/LICENSE)

<div align="center">
  <h3>Maze generation and pathfinding visualization</h3>
  <p>A Data Structures and Algorithms course project built with Python and Pygame.</p>
  <p>
    <a href="https://github.com/janxu2417/MazeVisualizer/blob/main/README_zh.md"><strong>中文说明</strong></a>
    ·
    <a href="https://github.com/janxu2417/MazeVisualizer">GitHub Repository</a>
  </p>
</div>

## Table of Contents

- [About The Project](#about-the-project)
- [Built With](#built-with)
- [Screenshots](#screenshots)
- [Features](#features)
- [Project Structure](#project-structure)
- [Core Algorithms](#core-algorithms)
- [Comprehensive Complexity Comparison](#comprehensive-complexity-comparison)
- [Getting Started](#getting-started)
- [Controls](#controls)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [Reference and Attribution](#reference-and-attribution)
- [AI Tool Declaration](#ai-tool-declaration)
- [Contact](#contact)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## About The Project

MazeVisualizer is a Python + Pygame project for visualizing maze generation and pathfinding step by step. It was designed for a Data Structures and Algorithms course assignment, with emphasis on:

- self-implemented maze generation and graph search logic
- explicit visualization of search state, not just final answers
- direct comparison between unweighted and weighted shortest-path algorithms
- clear separation between algorithm logic, state management, and rendering

The project is not only a demo player. In its current form, it is an interactive experiment platform: users can generate mazes, switch algorithms, edit layouts, assign terrain costs, inspect cells, compare multiple runs, and export results.

## Built With

- [Python 3.13](https://www.python.org/)
- [Pygame 2.5+](https://www.pygame.org/)
- [Pytest](https://docs.pytest.org/)

## Screenshots

### Main Menu

![MazeVisualizer menu](https://raw.githubusercontent.com/janxu2417/MazeVisualizer/main/docs/menu.png)

### BFS Running View

![MazeVisualizer BFS running](https://raw.githubusercontent.com/janxu2417/MazeVisualizer/main/docs/run_searching_BFS.png)

### Bidirectional BFS Running View

![MazeVisualizer bidirectional BFS](https://raw.githubusercontent.com/janxu2417/MazeVisualizer/main/docs/run_searching_Bi-BFS.png)

### Final Result with Comparison Board

![MazeVisualizer final result](https://raw.githubusercontent.com/janxu2417/MazeVisualizer/main/docs/run_finished%26comparison.png)

### Edit Mode

![MazeVisualizer edit mode](https://raw.githubusercontent.com/janxu2417/MazeVisualizer/main/docs/edit_maze_inspect.png)

## Features

- Maze generation with DFS backtracking, Prim-style generation, and Kruskal-style generation
- Pathfinding with BFS, Dijkstra, A*, Bidirectional BFS, Greedy Best-First Search, and Weighted A*
- Unified step-by-step visualization through a shared `StepState` interface
- Weighted terrain mode with cost bands `x1`, `x3`, and `x5`
- Runtime HUD with path length, visited count, step count, total cost, and status
- Comparison board for multiple algorithms on the same maze
- Interactive edit mode with wall drawing, start/goal placement, terrain painting, cell inspection, and undo
- Maze history navigation across regenerated mazes
- Canvas zoom and pan for larger layouts
- JSON export of comparison results and text import of maze grids
- Multiple visual themes: `dark`, `ocean`, `forest`, `sunset`

## Project Structure

```text
MazeVisualizer/
├─ src/
│  ├─ step_data.py       # shared types: Grid, Point, CostMap, RunStats, StepState
│  ├─ maze_gen.py        # DFS / Prim / Kruskal maze generation
│  ├─ pathfinding.py     # 6 pathfinding algorithms
│  ├─ algorithms.py      # compatibility re-export layer
│  ├─ app.py             # FSM, event dispatch, solver driving, history, import/export
│  ├─ render.py          # HUD, help panel, legend, comparison board, edit/run drawing
│  ├─ edit.py            # edit-mode state machine and undo
│  ├─ menu.py            # menu layout and click dispatch
│  ├─ config.py          # runtime configuration, presets, help lines
│  ├─ theme.py           # visual themes
│  ├─ main.py            # main entry point
│  └─ ui.py              # alternative entry point
├─ docs/                 # screenshots
├─ tests/                # automated tests
├─ README.md
├─ README_zh.md
├─ LICENSE
├─ pytest.ini
└─ requirements.txt
```

## Core Algorithms

### Maze Generation

#### DFS Backtracking

- Uses an explicit stack to maintain the current carving path.
- Moves by two cells at a time to preserve wall layers.
- Backtracks when no unvisited neighbor is available.

Course concepts:

- DFS
- stack
- backtracking

#### Prim-style Maze Generation

- Maintains a frontier around the connected carved region.
- Randomly selects a frontier cell and attaches it to the existing tree.
- Produces many local branches and dead ends.

Course concepts:

- minimum spanning tree intuition
- frontier expansion

#### Kruskal-style Maze Generation

- Treats passable cells as vertices and removable walls as candidate edges.
- Uses Union-Find to decide whether two regions are already connected.
- Avoids cycles while constructing a spanning-tree-style maze.

Course concepts:

- disjoint set union
- path compression
- union by rank
- minimum spanning tree

### Pathfinding

| Algorithm | Core idea | Optimal? | Notes |
| :-- | :-- | :-- | :-- |
| BFS | layer-by-layer expansion with a FIFO queue | Yes on unweighted grids | minimizes step count |
| Dijkstra | greedy expansion by accumulated cost | Yes with nonnegative weights | needed for weighted terrain |
| A* | Dijkstra with Manhattan heuristic | Yes with admissible heuristic | usually explores less than Dijkstra |
| Bidirectional BFS | simultaneous BFS from start and goal | Yes on unweighted grids | strong visual contrast with BFS |
| Greedy Best-First | heuristic-only expansion | No | often faster but may be suboptimal |
| Weighted A* | `f(n)=g(n)+W*h(n)` | No in general | trades optimality for speed |

### Course Knowledge Points Coverage

| Course topic           | Where applied                             | Implementation detail                           |
| :--------------------- | :---------------------------------------- | :---------------------------------------------- |
| DFS / backtracking     | DFS maze generation                       | explicit stack, dead-end backtracking           |
| BFS                    | BFS, Bidirectional BFS                    | `collections.deque`, layered expansion          |
| Graph representation   | all solvers                               | implicit grid graph with 4-neighbor adjacency   |
| Priority queue / heap  | `Dijkstra`, `A*`, `Greedy`, `Weighted A*` | `heapq`                                         |
| Shortest path          | `Dijkstra`                                | edge relaxation on nonnegative weights          |
| Heuristic search       | `A*`, `Greedy`, `Weighted A*`             | Manhattan distance                              |
| Bidirectional search   | Bidirectional BFS                         | two simultaneous frontiers and meet-point merge |
| Union-Find             | Kruskal maze generation                   | path compression + union by rank                |
| Minimum spanning tree  | Prim / Kruskal maze generation            | frontier expansion / disjoint-set connectivity  |
| Separation of concerns | full project structure                    | solver logic separated from rendering and UI    |

## Comprehensive Complexity Comparison

Let `V` be the number of passable cells, `E` the number of passable-cell adjacencies, `b` the branching factor, and `d` the shortest-path depth. For 4-neighbor grid mazes, degree is bounded, so `E = O(V)`.

| Algorithm               | Typical / expected                          | Worst case          | Space  | Optimal? | Conditions / notes                                          |
| :---------------------- | :------------------------------------------ | :------------------ | :----- | :------- | :---------------------------------------------------------- |
| DFS Maze Generation     | `Theta(V)`                                  | `Theta(V)`          | `O(V)` | N/A      | each reachable cell is processed a constant number of times |
| Prim Maze Generation    | `Theta(V)`                                  | `Theta(V)`          | `O(V)` | N/A      | bounded-degree grid keeps frontier handling linear          |
| Kruskal Maze Generation | `Theta(V alpha(V))`                         | `Theta(V alpha(V))` | `O(V)` | N/A      | Union-Find with path compression and union by rank          |
| BFS                     | `Theta(V + E)`                              | `O(V + E)`          | `O(V)` | Yes      | optimal on unweighted or equal-weight graphs                |
| Dijkstra                | often near `Theta((V + E) log V)`           | `O((V + E) log V)`  | `O(V)` | Yes      | requires nonnegative weights                                |
| A*                      | input-dependent, often better than Dijkstra | `O((V + E) log V)`  | `O(V)` | Yes      | requires an admissible heuristic                            |
| Bidirectional BFS       | often `O(b^(d/2))` in tree-like search      | `O(V + E)`          | `O(V)` | Yes      | optimal on unweighted or equal-weight graphs                |
| Greedy Best-First       | often fast but unstable across inputs       | `O((V + E) log V)`  | `O(V)` | No       | heuristic guidance only                                     |
| Weighted A*             | often fewer expansions than A*              | `O((V + E) log V)`  | `O(V)` | No       | heuristic inflation with `W > 1`                            |

For reader-facing grid-maze interpretation, the main search bounds simplify to:

- BFS: `O(V)`
- Dijkstra: `O(V log V)`
- A*: `O(V log V)`
- Bidirectional BFS: `O(V)`
- Greedy Best-First: `O(V log V)`
- Weighted A*: `O(V log V)`

### Why Weighted Terrain Matters

On a uniform maze, BFS, Dijkstra, and A* often produce the same shortest path length. Weighted terrain makes the algorithmic differences clearer:

- `x1`: normal path
- `x3`: medium-cost terrain
- `x5`: heavy-cost terrain

Then:

- BFS still minimizes step count only
- Dijkstra minimizes total path cost
- A* combines cost and heuristic guidance
- Weighted A* trades exact optimality for fewer expansions

## Getting Started

### Prerequisites

- Python 3.13
- `pip`

### Installation

1. Clone the repository:

```bash
git clone https://github.com/janxu2417/MazeVisualizer.git
cd MazeVisualizer
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

### Run

Start the application with:

```bash
python src/main.py
```

Alternative entry point:

```bash
python src/ui.py
```

## Controls

- `Space`: pause / resume
- `H`: show help panel
- `N`: single-step when paused
- `+/-`: adjust speed
- `[` / `]`: adjust Weighted A* parameter `W`
- `1-6`: switch algorithm and rerun on the same maze
- `R`: restart current solver
- `T`: toggle weighted terrain mode
- `C`: toggle comparison board
- `E`: enter edit mode from run view
- `U`: switch theme
- `M`: generate a new maze and store the current one in history
- `Left / Right`: browse maze history
- `F5`: export comparison results to `comparison_export.json`
- `F6`: import a maze from `maze_import.txt`
- `Mouse wheel`: zoom canvas
- `Right mouse drag`: pan canvas
- `ESC`: close help panel or return to menu

### Edit Mode Controls

- `D`: draw wall / path
- `S`: place start
- `G`: place goal
- `T`: paint terrain
- `I`: inspect cell
- `Ctrl+Z`: undo
- `R`: run the edited maze

## Testing

### Current Status

The current test suite contains 78 tests:

- `tests/test_algorithm_states.py`: 25
- `tests/test_algorithms.py`: 11
- `tests/test_app_logic.py`: 26
- `tests/test_render_smoke.py`: 16

Verified command:

```bash
python -m pytest --basetemp .pytest_tmp_report
```

Verified result:

```text
78 passed in 46.15s
```

### What Is Covered

- maze size normalization and invalid size handling
- solvability of DFS / Prim / Kruskal mazes
- BFS shortest-path correctness
- Dijkstra and A* consistency with BFS on uniform grids
- validity of Greedy and Weighted A* paths
- weighted terrain behavior
- `StepState` and `RunStats` interface consistency
- bidirectional BFS meet-point and dual-front state reporting
- app-level non-GUI logic: history, edit refresh, import/export, toggles, solver creation
- headless Pygame smoke tests for menu, HUD, run view, help panel, zoom/pan rendering

### Note on Test Execution

In the current environment, using default system temporary directories may trigger permission errors for `tmp_path`-based tests. Running with project-local `--basetemp` avoids that issue and allows the full suite to pass.

## Roadmap

- [x] Implement core maze generation and pathfinding algorithms
- [x] Add weighted terrain and algorithm comparison board
- [x] Add interactive edit mode
- [x] Add multiple themes and compact HUD layout
- [x] Add zoom and pan for larger mazes
- [x] Split the codebase into focused modules
- [ ] Add GIF capture for report-ready demonstrations
- [ ] Add more curated challenge mazes

## Reference and Attribution

Template and documentation reference:

- [Best-README-Template](https://github.com/othneildrew/Best-README-Template)

Project reference sources:

- [Pygame documentation](https://www.pygame.org/docs/)

This project’s core algorithm logic and system organization were implemented and organized by the author. No third-party algorithm library was used as a black-box solver.

## AI Tool Declaration

AI tools were used in the following limited ways:

- scaffolding and polishing parts of the UI structure
- refactoring suggestions for module organization
- wording refinement for README and report writing

The maze generation logic, pathfinding logic, state interface design, and final project organization were reviewed and finalized manually by the author.

## Contact

- Author: Xu Qian
- Repository: [janxu2417/MazeVisualizer](https://github.com/janxu2417/MazeVisualizer)

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgments

- Data Structures and Algorithms course:  [GMyhf/2026spring-cs201](https://github.com/GMyhf/2026spring-cs201)
- Pygame documentation and community examples
- Best-README-Template for documentation structure inspiration

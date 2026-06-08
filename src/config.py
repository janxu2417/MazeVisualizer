from __future__ import annotations

from dataclasses import dataclass

Color = tuple[int, int, int]


@dataclass
class AppConfig:
    rows: int = 31
    cols: int = 31
    cell_size: int = 19
    top_bar_height: int = 126
    side_padding: int = 28
    bottom_padding: int = 56
    default_step_ms: int = 80
    step_interval_ms: int = 80
    min_step_ms: int = 30
    max_step_ms: int = 240
    step_delta_ms: int = 10
    loop_chance: float = 0.08
    maze_method: str = "dfs"
    weighted_a_star_w: float = 1.5
    weighted_step: float = 0.1
    min_weight: float = 1.0
    max_weight: float = 3.0
    terrain_mode: bool = False
    terrain_ratio: float = 0.18
    terrain_seed: int = 2026
    comparison_enabled: bool = True
    title_font_size: int = 30
    body_font_size: int = 18
    small_font_size: int = 14
    legend_font_size: int = 13
    algo_button_font_size: int = 20
    algo_subtitle_font_size: int = 16
    algo_weight_font_size: int = 15
    algo_weight_label_nudge_y: int = 4
    live_path_algorithms: tuple[str, ...] = ()


COLORS: dict[str, Color] = {
    "bg": (18, 20, 24),
    "panel": (28, 32, 38),
    "panel_alt": (34, 39, 47),
    "wall": (12, 13, 15),
    "path": (215, 215, 215),
    "terrain_light": (216, 225, 221),
    "terrain_mid": (173, 188, 181),
    "terrain_heavy": (122, 140, 132),
    # A/B/C search colors: tune these three entries first when adjusting the visualization.
    "search_visited": (103, 142, 197),
    "search_frontier": (244, 191, 117),
    "search_current": (240, 111, 92),
    "route": (220, 185, 110),
    "start": (80, 185, 120),
    "goal": (205, 90, 90),
    "grid": (36, 38, 44),
    "button": (50, 58, 70),
    "button_hover": (70, 80, 96),
    "button_active": (88, 108, 138),
    "button_border": (95, 105, 120),
    "text": (225, 225, 225),
    "text_dim": (180, 185, 195),
}


SIZE_OPTIONS = [
    ("Small", 21, 21, 20),
    ("Medium", 31, 31, 19),
    ("Large", 41, 41, 15),
]

COMPLEXITY_OPTIONS = [
    ("Low", 0.0),
    ("Medium", 0.08),
    ("High", 0.18),
]

MAZE_OPTIONS = [
    ("Maze: DFS Corridor", "dfs", None, None),
    ("Maze: Prim Dead-end", "prim", None, None),
    ("Maze: Prim Dense", "prim", 0.18, "Dense"),
    ("Maze: Kruskal Sparse", "kruskal", 0.02, "Sparse"),
    ("Maze: Kruskal Standard", "kruskal", None, None),
]

ALGORITHM_NAMES = [
    "BFS",
    "Dijkstra",
    "A*",
    "Bi-BFS",
    "Greedy",
    "Weighted A*",
]

HELP_LINES = [
    "Space: pause / resume",
    "H: help panel",
    "N: single step when paused",
    "+/-: speed up / slow down",
    "R: restart current algorithm",
    "1-6: switch algorithm and rerun",
    "[ / ]: adjust Weighted A* W",
    "T: toggle weighted terrain",
    "C: toggle comparison board",
    "M: generate new maze",
    "Legend: visited / frontier / current / path",
    "Terrain: x1 / x3 / x5 cost bands",
    "ESC: close help / back to menu",
]

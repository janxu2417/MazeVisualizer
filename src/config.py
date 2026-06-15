"""Application-wide configuration constants and the :class:`AppConfig` dataclass."""

from __future__ import annotations

from dataclasses import dataclass

Color = tuple[int, int, int]


@dataclass
class AppConfig:
    """Mutable runtime configuration for a single MazeVisualizer session.

    Holds grid dimensions, cell sizes, padding, algorithm speed, maze
    generation parameters, terrain options, font sizes, and weighted-A*
    tuning — all adjustable via the GUI menu.
    """
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


#: Master colour palette: bg, panel, panel_alt, wall, path, terrain tiers,
#: search layers, route, start/goal markers, grid lines, and button states.
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
"""Grid presets: ``(label, rows, cols, cell_size)``."""

COMPLEXITY_OPTIONS = [
    ("Low", 0.0),
    ("Medium", 0.08),
    ("High", 0.18),
]
"""Loop-chance presets: ``(label, loop_chance)``."""

MAZE_OPTIONS = [
    ("Maze: DFS Corridor", "dfs", None, None),
    ("Maze: Prim Dead-end", "prim", None, None),
    ("Maze: Prim Dense", "prim", 0.18, "Dense"),
    ("Maze: Kruskal Sparse", "kruskal", 0.02, "Sparse"),
    ("Maze: Kruskal Standard", "kruskal", None, None),
]
"""Maze-flavour presets: ``(label, method, override_loop_chance, custom_label)``."""

ALGORITHM_NAMES = [
    "BFS",
    "Dijkstra",
    "A*",
    "Bi-BFS",
    "Greedy",
    "Weighted A*",
]
"""Ordered list of supported pathfinding algorithm display names."""

HELP_LINES = [
    "Space: pause / resume",
    "H: help panel  /  Escape: close",
    "N: single step when paused",
    "+/-: speed up / slow down",
    "R: restart current algorithm",
    "1-6: switch algorithm and rerun",
    "[ / ]: adjust Weighted A* W",
    "T: toggle weighted terrain",
    "C: toggle comparison board",
    "M: generate new maze",
    "Left / Right: maze history  (switches comparison board)",
    "F5: export comparison  -->  comparison_export.json",
    "F6: import maze  <--  maze_import.txt",
    "Scroll wheel: scroll help panel",
    "",
    "---------  ----------",
    "空格: 暂停 / 继续",
    "H: 帮助面板  /  Escape: 返回菜单",
    "N: 暂停时单步执行",
    "+/-: 加速 / 减速",
    "R: 重启当前算法",
    "1-6: 切换算法并重新运行",
    "[ / ]: 调整 Weighted A* 权重 W",
    "T: 开关加权地形",
    "C: 开关对比面板",
    "M: 生成新迷宫 (保存历史)",
    "方向键 左/右: 浏览迷宫历史 (对比板随地图切换)",
    "F5: 导出对比结果  -->  comparison_export.json",
    "F6: 导入迷宫  <--  maze_import.txt",
    "鼠标滚轮: 滚动帮助面板",
    "",
    "---------  Legend /  图例  ----------",
    "   visited    frontier    current    path    x1    x3    x5",
]
"""Bilingual help-panel content: English, separator, Chinese, separator, legend.

Displayed line-by-line in the scrollable help overlay rendered by
:func:`render.draw_help_panel`.
"""

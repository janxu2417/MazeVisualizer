"""Pygame rendering layer for MazeVisualizer.

Responsible for all drawing operations: maze grid, search overlays (visited,
frontier, current, path), HUD, comparison board, menu screens, help panel,
legend, and status messages.  Separated from algorithm and application logic
to satisfy the GUI separation-of-concerns requirement.
"""

from __future__ import annotations

import pygame

from algorithms import CostMap, Point, StepState
from config import AppConfig, COLORS, HELP_LINES
from edit import EditTool, get_cell_info
from menu import ButtonSpec


def load_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Return a :class:`pygame.font.Font` of the given *size*.

    Tries a priority list of CJK-capable fonts (Microsoft YaHei, SimHei, etc.)
    and falls back to the system default if none match.
    """
    candidates = [
        "Microsoft YaHei",
        "SimHei",
        "Microsoft JhengHei",
        "PingFang SC",
        "Noto Sans CJK SC",
        "Arial",
    ]
    for name in candidates:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            font = pygame.font.Font(path, size)
            font.set_bold(bold)
            return font
    font = pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


def _board_pixel_size(grid: list[list[int]], config: AppConfig) -> tuple[int, int]:
    """Return (width, height) in pixels for the board area derived from *grid* dimensions."""
    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    width = cols * config.cell_size + config.side_padding * 2
    height = rows * config.cell_size + config.top_bar_height + config.bottom_padding
    return width, height


def build_base_surface(config: AppConfig, grid: list[list[int]], cost_map: CostMap | None) -> pygame.Surface:
    """Render the static maze grid onto a reusable surface.

    Walls are drawn with the wall colour; passable cells are tinted by
    terrain cost when *cost_map* is provided.  Grid lines are drawn on top.
    The returned surface is blitted as background every frame.
    """
    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    width = cols * config.cell_size + config.side_padding * 2
    height = rows * config.cell_size + config.top_bar_height + config.bottom_padding
    surface = pygame.Surface((width, height))
    surface.fill(COLORS["bg"])

    top = config.top_bar_height
    left = config.side_padding
    for r in range(rows):
        for c in range(cols):
            rect = pygame.Rect(
                left + c * config.cell_size,
                top + r * config.cell_size,
                config.cell_size,
                config.cell_size,
            )
            color = COLORS["wall"] if grid[r][c] == 0 else _terrain_color(cost_map, r, c)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, COLORS["grid"], rect, 1)

    return surface


def draw_run_view(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    config: AppConfig,
    app: object,
) -> None:
    """Top-level render call for the running / paused view.

    Composes the base surface, search overlay, HUD, comparison board, legend,
    and (if active) the help panel in draw order.  If the user has panned or
    zoomed the view (P2-2) the base surface and overlay are transformed
    accordingly.
    """
    screen.fill(COLORS["bg"])
    zoom = getattr(app, "zoom", 1.0)
    px = getattr(app, "pan_x", 0)
    py = getattr(app, "pan_y", 0)
    board_surface = app.base_surface.copy()
    draw_overlay(board_surface, config, app)
    if zoom == 1.0:
        screen.blit(board_surface, (px, py))
    else:
        sw = max(1, int(board_surface.get_width() * zoom))
        sh = max(1, int(board_surface.get_height() * zoom))
        scaled = pygame.transform.smoothscale(board_surface, (sw, sh))
        screen.blit(scaled, (px, py))
    draw_hud(screen, title_font, font, small_font, config, app)
    if app.help_visible:
        draw_help_panel(screen, font, small_font, app)


def draw_edit_view(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    config: AppConfig,
    app: object,
) -> None:
    screen.blit(app.base_surface, (0, 0))
    _draw_edit_topbar(screen, title_font, font, small_font, config, app)
    _draw_edit_markers(screen, small_font, config, app)
    _draw_edit_hover(screen, config, app)
    _draw_edit_toolbar(screen, small_font, config, app)
    if app.edit_state.tool == EditTool.INSPECT and app.edit_state.hover_cell is not None:
        _draw_cell_tooltip(screen, small_font, app, app.edit_state.hover_cell)


def _draw_edit_topbar(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    config: AppConfig,
    app: object,
) -> None:
    """Draw the edit-mode header bar.

    Layers a dark panel, an accent strip, the title ("Edit Maze"), the
    current tool name, a theme / shortcut hint line, and the start/goal
    coordinates right-aligned on the same row as the title.
    """
    width = _grid_width(config, app.grid)
    pygame.draw.rect(screen, COLORS["panel"], pygame.Rect(0, 0, width, config.top_bar_height))
    pygame.draw.rect(screen, COLORS["edit_cursor"], pygame.Rect(0, 0, width, 5))
    screen.blit(title_font.render("Edit Maze", True, COLORS["text"]), (12, 12))
    tool = app.edit_state.tool.value.replace("_", " ").title()
    screen.blit(font.render(f"Tool: {tool}", True, COLORS["text"]), (12, 46))
    info = f"theme {getattr(config, 'theme_name', 'dark')}  |  R run edited maze  |  Ctrl+Z undo"
    screen.blit(small_font.render(info, True, COLORS["text_dim"]), (12, 74))
    right = small_font.render(f"start {app.start}   goal {app.goal}", True, COLORS["text_dim"])
    screen.blit(right, (width - right.get_width() - 14, 18))


def _draw_edit_markers(screen: pygame.Surface, small_font: pygame.font.Font, config: AppConfig, app: object) -> None:
    top = config.top_bar_height
    for label, point, color in (("S", app.start, COLORS["start"]), ("G", app.goal, COLORS["goal"])):
        rect = _cell_rect(config, top, point)
        pygame.draw.rect(screen, color, rect, border_radius=max(2, config.cell_size // 5))
        text = small_font.render(label, True, COLORS["text"])
        screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))


def _draw_edit_hover(screen: pygame.Surface, config: AppConfig, app: object) -> None:
    cell = app.edit_state.hover_cell
    if cell is None:
        return
    color = _edit_hover_color(app.edit_state.tool)
    rect = _cell_rect(config, config.top_bar_height, cell)
    pygame.draw.rect(screen, color, rect, 3, border_radius=max(2, config.cell_size // 5))


def draw_button(
    screen: pygame.Surface,
    font: pygame.font.Font,
    rect: pygame.Rect,
    label: str,
    *,
    hover: bool = False,
    active: bool = False,
    text_color: tuple[int, int, int] | None = None,
) -> None:
    """Draw a single rounded-rect button with hover / active state coloring."""
    if active:
        color = COLORS["button_active"]
    elif hover:
        color = COLORS["button_hover"]
    else:
        color = COLORS["button"]
    pygame.draw.rect(screen, color, rect, border_radius=8)
    pygame.draw.rect(screen, COLORS["button_border"], rect, 2, border_radius=8)
    text = font.render(label, True, text_color if text_color is not None else COLORS["text"])
    screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))


def _draw_edit_toolbar(screen: pygame.Surface, font: pygame.font.Font, config: AppConfig, app: object) -> None:
    width = _grid_width(config, app.grid)
    top = config.top_bar_height + config.rows * config.cell_size
    bar = pygame.Rect(0, top, width, config.bottom_padding)
    pygame.draw.rect(screen, COLORS["panel"], bar)
    tool_labels = [
        (EditTool.DRAW_WALL, "D Draw"),
        (EditTool.PLACE_START, "S Start"),
        (EditTool.PLACE_GOAL, "G Goal"),
        (EditTool.PAINT_TERRAIN, "T Terrain"),
        (EditTool.INSPECT, "I Inspect"),
    ]
    x = 12
    y = bar.y + max(8, (bar.height - font.get_height()) // 2)
    for tool, label in tool_labels:
        active = tool == app.edit_state.tool
        text = font.render(label, True, COLORS["text"] if active else COLORS["text_dim"])
        rect = pygame.Rect(x, y - 5, text.get_width() + 18, text.get_height() + 10)
        draw_button(screen, font, rect, label, active=active, text_color=COLORS["text"] if active else COLORS["text_dim"])
        x = rect.right + 8


def _draw_cell_tooltip(screen: pygame.Surface, font: pygame.font.Font, app: object, cell: Point) -> None:
    lines = get_cell_info(app, cell).split("\n")
    width = max(font.size(line)[0] for line in lines) + 18
    height = len(lines) * (font.get_linesize() + 2) + 12
    x, y = app.edit_state.tooltip_pos
    panel = pygame.Rect(x + 14, y + 14, width, height)
    if panel.right > screen.get_width():
        panel.x = x - width - 14
    if panel.bottom > screen.get_height():
        panel.y = y - height - 14
    pygame.draw.rect(screen, COLORS["panel_alt"], panel, border_radius=8)
    pygame.draw.rect(screen, COLORS["button_border"], panel, 1, border_radius=8)
    text_y = panel.y + 7
    for line in lines:
        screen.blit(font.render(line, True, COLORS["text_dim"]), (panel.x + 9, text_y))
        text_y += font.get_linesize() + 2


def _edit_hover_color(tool: EditTool) -> tuple[int, int, int]:
    if tool == EditTool.DRAW_WALL:
        return COLORS["edit_wall_preview"]
    if tool == EditTool.PLACE_START:
        return COLORS["edit_start_preview"]
    if tool == EditTool.PLACE_GOAL:
        return COLORS["edit_goal_preview"]
    if tool == EditTool.PAINT_TERRAIN:
        return COLORS["edit_terrain_preview"]
    return COLORS["edit_cursor"]



def draw_overlay(surface: pygame.Surface, config: AppConfig, app: object) -> None:
    """Paint the per-frame search visualization layer onto a board-local surface.

    Renders visited cells, frontier cells, the current-expansion cell, the
    live/preview path, and start/goal markers using colours from ``COLORS``.
    """
    top = config.top_bar_height
    width, height = _board_pixel_size(app.grid, config)
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    state: StepState = app.last_state

    for point in state["visited"]:
        if point in (app.start, app.goal):
            continue
        pygame.draw.rect(overlay, (*COLORS["search_visited"], 118), _cell_rect(config, top, point))

    for point in state["frontier"]:
        if point in (app.start, app.goal):
            continue
        pygame.draw.rect(overlay, (*COLORS["search_frontier"], 142), _cell_rect(config, top, point))

    surface.blit(overlay, (0, 0))

    current = state["current"]
    if current and current not in (app.start, app.goal):
        rect = _cell_rect(config, top, current)
        inset = max(2, config.cell_size // 6)
        inner_rect = rect.inflate(-inset * 2, -inset * 2)
        pygame.draw.rect(surface, COLORS["search_current"], inner_rect, border_radius=max(3, config.cell_size // 4))

    show_live_path = app.algorithm_name in config.live_path_algorithms
    path_points = state["path"] if (state["finished"] or show_live_path) else []
    for point in path_points:
        if point in (app.start, app.goal):
            continue
        pygame.draw.rect(surface, COLORS["route"], _cell_rect(config, top, point), border_radius=2)

    for label, point in (("start", app.start), ("goal", app.goal)):
        pygame.draw.rect(surface, COLORS[label], _cell_rect(config, top, point))


def _grid_width(config: AppConfig, grid: list[list[int]]) -> int:
    """Pixel width of the board area derived from the actual grid columns."""
    return (len(grid[0]) if grid else 0) * config.cell_size + config.side_padding * 2


def _compact_stat_row_layout(width: int, title_width: int) -> tuple[int, int, int]:
    """Return ``(start_x, card_width, gap)`` for the compact 1x4 stat row."""
    gap = 4
    left_bound = 12 + title_width + 18
    usable_width = max(0, width - left_bound - 10)
    max_card_w = 72
    min_card_w = 58
    card_width = min(max_card_w, max(min_card_w, (usable_width - gap * 3) // 4))
    total_width = card_width * 4 + gap * 3
    start_x = left_bound + max(0, (usable_width - total_width) // 2)
    return start_x, card_width, gap


def _regular_stat_grid_layout(
    width: int,
    left_zone_right: int,
    right_zone_left: int,
    grid_width: int = 232,
) -> int:
    """Return the left edge for the regular 2x2 stat grid without side-text overlap."""
    preferred_x = width // 2 - grid_width // 2 - 10
    min_x = left_zone_right + 22
    max_x = right_zone_left - grid_width - 22
    if max_x < min_x:
        return min_x
    return max(min_x, min(preferred_x, max_x))


def draw_hud(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    config: AppConfig,
    app: object,
) -> None:
    """Render the top-bar heads-up display.

    Layout strategy (responsive by screen width):
      - Left zone (x=12): algorithm name, status, meta line (W / terrain / theme)
      - Centre zone: 4 stat cards (Path / Visited / Steps / Cost)
      - Right zone: speed / maze history / keyboard hints

    When the total board width is under 560 px (Small preset) the layout
    switches to *compact mode*:
      - the three right-zone lines merge into one abbreviated line
      - stat cards are laid out in a single horizontal row (1×4)
      - the legend font shrinks by 2 px and horizontal gaps are tightened

    Below the text zones a progress bar spans the full width; the colour
    legend and the comparison board are then drawn beneath it.
    """
    width = _grid_width(config, app.grid)
    compact = width < 560
    info_font = load_font(config.small_font_size + 2) if compact else small_font
    pygame.draw.rect(screen, COLORS["panel"], pygame.Rect(0, 0, width, config.top_bar_height))

    status = "DONE" if app.finished else ("PAUSED" if app.paused else "RUNNING")
    status_color = COLORS["status_done"] if app.finished else COLORS["status_paused"] if app.paused else COLORS["status_running"]
    pygame.draw.rect(screen, status_color, pygame.Rect(0, 0, width, 5))

    stats = app.last_state["stats"]
    terrain_text = "ON" if app.cost_map is not None else "OFF"
    history_info = f"{app.maze_index + 1}/{len(app.maze_history)}" if app.maze_history else "live"
    theme_name = getattr(config, "theme_name", "dark")
    meta_text = (
        f"W {config.weighted_a_star_w:.1f} | terrain {terrain_text} | theme {theme_name}"
        if compact
        else f"W {config.weighted_a_star_w:.1f} | terr {terrain_text} | theme {theme_name}"
    )

    title_surface = title_font.render(app.algorithm_name, True, COLORS["text"])
    screen.blit(title_surface, (12, 12))
    status_surface = info_font.render(status, True, status_color)
    screen.blit(status_surface, (14, 46))
    meta = info_font.render(
        meta_text,
        True,
        COLORS["text_dim"],
    )
    screen.blit(meta, (14, 68))
    left_zone_right = max(
        12 + title_surface.get_width(),
        14 + status_surface.get_width(),
        14 + meta.get_width(),
    )

    # --- stat cards ---
    stat_items = [
        ("Path", stats.path_length),
        ("Visited", stats.visited_count),
        ("Steps", stats.step_count),
        ("Cost", stats.cost),
    ]
    if compact:
        # 1×4 row spanning the centre, pushed left to leave right zone breathable
        card_h = 28
        center_x, card_w, card_gap = _compact_stat_row_layout(width, title_surface.get_width())
        for idx, (label, value) in enumerate(stat_items):
            rx = center_x + idx * (card_w + card_gap)
            rect = pygame.Rect(rx, 14, card_w, card_h)
            pygame.draw.rect(screen, COLORS["panel_alt"], rect, border_radius=6)
            pygame.draw.rect(screen, COLORS["button_border"], rect, 1, border_radius=6)
            screen.blit(small_font.render(label, True, COLORS["text_dim"]), (rect.x + 4, rect.y + 2))
            value_surface = small_font.render(str(value), True, COLORS["text"])
            screen.blit(value_surface, (rect.right - value_surface.get_width() - 5, rect.y + 2))
    else:
        # 2×2 grid for Medium / Large presets
        right_text = [
            f"speed {config.step_interval_ms}ms",
            f"maze {history_info}",
            "U theme  E edit  H help",
        ]
        right_surfaces = [small_font.render(line, True, COLORS["text_dim"]) for line in right_text]
        right_zone_left = width - 14 - max(surface.get_width() for surface in right_surfaces)
        card_w = 110
        col_step = 122
        grid_width = card_w * 2 + (col_step - card_w)
        center_x = _regular_stat_grid_layout(width, left_zone_right, right_zone_left, grid_width)
        for index, (label, value) in enumerate(stat_items):
            col = index % 2
            row = index // 2
            rect = pygame.Rect(center_x + col * col_step, 16 + row * 38, card_w, 30)
            pygame.draw.rect(screen, COLORS["panel_alt"], rect, border_radius=8)
            pygame.draw.rect(screen, COLORS["button_border"], rect, 1, border_radius=8)
            screen.blit(small_font.render(label, True, COLORS["text_dim"]), (rect.x + 8, rect.y + 4))
            value_surface = font.render(str(value), True, COLORS["text"])
            screen.blit(value_surface, (rect.right - value_surface.get_width() - 8, rect.y + 3))

    # --- right-zone hints ---
    if compact:
        right_line = f"spd{config.step_interval_ms} | {history_info} | U E H"
        surface = info_font.render(right_line, True, COLORS["text_dim"])
        screen.blit(surface, (width - surface.get_width() - 10, 46))
    else:
        y = 14
        for surface in right_surfaces:
            screen.blit(surface, (width - surface.get_width() - 14, y))
            y += 22

    passable = sum(cell == 1 for row in app.grid for cell in row)
    visited = min(len(app.last_state["visited"]), passable)
    progress = 0 if passable == 0 else visited / passable
    bar = pygame.Rect(12, config.top_bar_height - 13, width - 24, 5)
    pygame.draw.rect(screen, COLORS["panel_alt"], bar, border_radius=3)
    pygame.draw.rect(screen, status_color, pygame.Rect(bar.x, bar.y, int(bar.width * progress), bar.height), border_radius=3)

    _draw_status_message(screen, small_font, config, app)
    draw_legend(screen, config, app.grid, compact=compact)
    draw_comparison_board(screen, small_font, config, app)


def _draw_status_message(
    screen: pygame.Surface,
    font: pygame.font.Font,
    config: AppConfig,
    app: object,
) -> None:
    """Show a temporary status message (e.g. export/import feedback)."""
    if not app.status_message:
        return
    elapsed = pygame.time.get_ticks() - app.status_message_time
    if elapsed > 3000:
        app.status_message = ""
        return
    alpha = 255 if elapsed < 2000 else max(60, int(255 - (elapsed - 2000) / 1000 * 195))
    text = font.render(app.status_message, True, COLORS["text"])
    text.set_alpha(alpha)
    width = _grid_width(config, app.grid)
    screen.blit(text, ((width - text.get_width()) // 2, config.top_bar_height - 44))


def draw_comparison_board(
    screen: pygame.Surface,
    font: pygame.font.Font,
    config: AppConfig,
    app: object,
) -> None:
    """Draw the multi-algorithm comparison panel (C key toggle).

    Shows a per-maze comparison: path length, visited count, step count,
    and total path cost for every algorithm that has been run on the current
    maze.  Title includes `(current/total)` when multiple mazes are in the
    history.
    """
    if not app.show_comparison or not app.comparison_results:
        return

    total = len(app.maze_history)
    current = app.maze_index + 1
    title = f"Comparison  ({current}/{total})" if total > 0 else "Comparison"
    lines = [title]
    for algorithm, stats in app.comparison_results.items():
        lines.append(
            f"{algorithm}: path {stats.path_length}, visited {stats.visited_count}, "
            f"steps {stats.step_count}, cost {stats.cost}"
        )

    width = max(font.size(line)[0] for line in lines) + 20
    line_height = font.get_linesize() + 4
    panel = pygame.Rect(
        screen.get_width() - width - 12,
        config.top_bar_height + 12,
        width,
        len(lines) * line_height + 14,
    )
    pygame.draw.rect(screen, COLORS["panel_alt"], panel, border_radius=10)
    pygame.draw.rect(screen, COLORS["button_border"], panel, 2, border_radius=10)
    y = panel.y + 8
    for index, line in enumerate(lines):
        color = COLORS["text"] if index == 0 else COLORS["text_dim"]
        screen.blit(font.render(line, True, color), (panel.x + 10, y))
        y += line_height


def draw_menu(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    buttons: list[ButtonSpec],
    background: pygame.Surface,
    size_label: str,
    complexity_label: str,
    maze_label: str,
    algo_label: str,
    terrain_label: str,
    show_help: bool,
    app: object,
) -> None:
    """Render the main menu with setting buttons and current selections.

    Button labels reflect live configuration (size, complexity, maze flavour,
    algorithm, terrain).  The help panel overlay is shown when *show_help* is
    ``True``.
    """
    width, height = screen.get_size()
    screen.blit(background, (0, 0))
    title = title_font.render("MazeVisualizer", True, COLORS["text"])
    subtitle = font.render("Maze generation and pathfinding visualization", True, COLORS["text_dim"])
    screen.blit(title, (width // 2 - title.get_width() // 2, 56))
    screen.blit(subtitle, (width // 2 - subtitle.get_width() // 2, 102))

    mouse_pos = pygame.mouse.get_pos()
    for label, action, rect in buttons:
        if action == "size":
            label = f"Size: {size_label}"
        elif action == "complexity":
            label = f"Complexity: {complexity_label}"
        elif action == "maze":
            label = maze_label
        elif action == "algo":
            label = f"Algorithm: {algo_label}"
        elif action == "terrain":
            label = terrain_label
        elif action == "theme":
            label = "Theme: click / U"
        draw_button(screen, font, rect, label, hover=rect.collidepoint(mouse_pos))

    footer = small_font.render("Select settings, then click Start. ESC closes help.", True, COLORS["text_dim"])
    screen.blit(footer, (width // 2 - footer.get_width() // 2, height - 34))
    if show_help:
        draw_help_panel(screen, font, small_font, app)


def draw_algo_menu(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    config: AppConfig,
    background: pygame.Surface,
    buttons: list[ButtonSpec],
    selected_algo: str,
    weight: float,
) -> None:
    """Render the algorithm-selection overlay.

    Lists the six pathfinding algorithms as toggle buttons.  The currently
    selected algorithm is highlighted, and W+ / W- buttons adjust the
    Weighted A* parameter on screen.
    """
    width, height = screen.get_size()
    screen.blit(background, (0, 0))
    compact = width <= 440 or height <= 560
    button_font = load_font(config.algo_button_font_size)
    subtitle_font = load_font(config.algo_subtitle_font_size)
    weight_font = load_font(config.algo_weight_font_size)
    title_y = 52 if compact else 60
    subtitle_y = 96 if compact else 108
    title = title_font.render("Algorithm Selection", True, COLORS["text"])
    subtitle = subtitle_font.render("Choose solver and adjust W for Weighted A*.", True, COLORS["text_dim"])
    screen.blit(title, (width // 2 - title.get_width() // 2, title_y))
    screen.blit(subtitle, (width // 2 - subtitle.get_width() // 2, subtitle_y))

    mouse_pos = pygame.mouse.get_pos()
    for label, action, rect in buttons:
        is_selected = action == selected_algo
        hover = rect.collidepoint(mouse_pos)
        active = is_selected and not hover
        draw_button(screen, button_font, rect, label, hover=hover, active=active)

    weight_text = weight_font.render(f"Weighted A* parameter W = {weight:.1f}", True, COLORS["text_dim"])
    algo_rects = [rect for _, action, rect in buttons if action not in {"back", "w_minus", "w_plus"}]
    algo_bottom = max(rect.bottom for rect in algo_rects)
    control_rects = [rect for _, action, rect in buttons if action in {"w_minus", "w_plus"}]
    controls_top = min(rect.y for rect in control_rects)
    if compact:
        weight_y = algo_bottom + config.algo_weight_label_nudge_y
        min_gap = 4
        if controls_top - weight_y - weight_text.get_height() < min_gap:
            weight_y = max(subtitle_y + subtitle.get_height() + 12, controls_top - weight_text.get_height() - min_gap)
    else:
        weight_y = max(algo_bottom + 12 + config.algo_weight_label_nudge_y, controls_top - weight_text.get_height() - 10)
    screen.blit(weight_text, (width // 2 - weight_text.get_width() // 2, weight_y))


def build_menu_background(width: int, height: int) -> pygame.Surface:
    """Create a decorative background surface for menu screens.

    Draws diagonal lines, concentric circles, and small squares with
    translucent colours to give the menu a polished, non-flat appearance.
    """
    surface = pygame.Surface((width, height))
    surface.fill(COLORS["bg"])

    pattern = pygame.Surface((width, height), pygame.SRCALPHA)
    for x in range(-height, width, 60):
        pygame.draw.line(pattern, (70, 80, 95, 40), (x, 0), (x + height, height), 2)
    center = (width - 120, 140)
    for radius in range(40, 140, 18):
        pygame.draw.circle(pattern, (90, 105, 125, 35), center, radius, 1)
    for index in range(6):
        rect = pygame.Rect(60 + index * 26, height - 130, 14, 14)
        pygame.draw.rect(pattern, (80, 90, 110, 50), rect)
    surface.blit(pattern, (0, 0))
    return surface


def draw_help_panel(
    screen: pygame.Surface,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    app: object,
) -> None:
    """Render a scrollable help overlay with bilingual key bindings.

    Contents are defined in :data:`config.HELP_LINES`.  The user can scroll
    with the mouse wheel or arrow keys.  A scroll-position indicator is drawn
    in the top-right corner of the panel.
    """
    width, height = screen.get_size()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    line_height = small_font.get_linesize() + 5
    total_lines = len(HELP_LINES)
    content_height = line_height * total_lines
    panel_w = min(width - 40, 720)
    max_panel_h = height - 40
    visible_lines = (max_panel_h - 80) // line_height
    panel_h = min(max_panel_h, content_height + 80)

    max_scroll = max(0, total_lines - visible_lines)
    if app.help_scroll > max_scroll:
        app.help_scroll = max_scroll
    if app.help_scroll < 0:
        app.help_scroll = 0

    panel = pygame.Rect(
        width // 2 - panel_w // 2,
        height // 2 - panel_h // 2,
        panel_w,
        panel_h,
    )
    pygame.draw.rect(screen, COLORS["panel"], panel, border_radius=10)
    pygame.draw.rect(screen, COLORS["button_border"], panel, 2, border_radius=10)

    title = font.render("Help /  (scroll with mouse wheel)", True, COLORS["text"])
    screen.blit(title, (panel.x + 20, panel.y + 18))

    clip_rect = pygame.Rect(panel.x + 4, panel.y + 52, panel_w - 8, panel_h - 62)
    screen.set_clip(clip_rect)
    y = panel.y + 56 - app.help_scroll * line_height
    for i, line in enumerate(HELP_LINES):
        if y + line_height < clip_rect.top:
            y += line_height
            continue
        if y > clip_rect.bottom:
            break
        color = COLORS["text"] if not line or line.startswith("---") else COLORS["text_dim"]
        text_surface = small_font.render(line, True, color)
        screen.blit(text_surface, (panel.x + 22, y))
        y += line_height
    screen.set_clip(None)

    if max_scroll > 0:
        indicator_font = small_font
        scrolled = f"  {app.help_scroll + 1}-{min(app.help_scroll + visible_lines, total_lines)} / {total_lines}"
        indicator = indicator_font.render(scrolled, True, COLORS["text_dim"])
        screen.blit(indicator, (panel.right - indicator.get_width() - 16, panel.y + 22))


def _cell_rect(config: AppConfig, top: int, point: Point) -> pygame.Rect:
    r, c = point
    return pygame.Rect(
        config.side_padding + c * config.cell_size,
        top + r * config.cell_size,
        config.cell_size,
        config.cell_size,
    )


def _terrain_color(cost_map: CostMap | None, row: int, col: int) -> tuple[int, int, int]:
    if cost_map is None:
        return COLORS["path"]
    cost = cost_map[row][col]
    if cost <= 1:
        return COLORS["terrain_light"]
    if cost <= 3:
        return COLORS["terrain_mid"]
    return COLORS["terrain_heavy"]


def draw_legend(screen: pygame.Surface, config: AppConfig, grid: list[list[int]], *, compact: bool = False) -> None:
    """Draw colour legend inside the top-bar.

    Items are laid out left-to-right across the board width, wrapping to
    a second line when they would overflow.  ``base_y`` is computed from
    ``config.top_bar_height`` minus the total line block so the legend
    sits flush with the bottom of the top bar.

    In *compact* mode (Small preset) the font is reduced by 2 px and the
    horizontal gap between items is halved to fit within the narrower bar.
    """
    font_size = max(10, config.legend_font_size - 2) if compact else config.legend_font_size
    legend_font = load_font(font_size)
    gap = 4 if compact else 8
    swatch = 10 if compact else 12
    items = [
        ("Visited", COLORS["search_visited"]),
        ("Frontier", COLORS["search_frontier"]),
        ("Current", COLORS["search_current"]),
        ("Path", COLORS["route"]),
        ("x1", COLORS["terrain_light"]),
        ("x3", COLORS["terrain_mid"]),
        ("x5", COLORS["terrain_heavy"]),
    ]
    start_x = 10
    line_height = legend_font.get_height() + 2
    max_width = _grid_width(config, grid) - 16
    lines: list[list[tuple[str, tuple[int, int, int], pygame.Surface]]] = [[]]
    x = start_x
    for label, color in items:
        text_surface = legend_font.render(label, True, COLORS["text_dim"])
        item_width = swatch + 4 + text_surface.get_width()
        if x + item_width > max_width and lines[-1]:
            lines.append([])
            x = start_x
        lines[-1].append((label, color, text_surface))
        x += item_width + gap

    block_height = len(lines) * line_height
    base_y = config.top_bar_height - block_height - 6
    for row_idx, line in enumerate(lines):
        y = base_y + row_idx * line_height
        x = start_x
        for label, color, text_surface in line:
            pygame.draw.rect(screen, color, pygame.Rect(x, y, swatch, swatch), border_radius=3)
            x += swatch + 4
            screen.blit(text_surface, (x, y - 1))
            x += text_surface.get_width() + gap

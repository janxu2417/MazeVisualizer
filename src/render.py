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


def build_base_surface(config: AppConfig, grid: list[list[int]], cost_map: CostMap | None) -> pygame.Surface:
    """Render the static maze grid onto a reusable surface.

    Walls are drawn with the wall colour; passable cells are tinted by
    terrain cost when *cost_map* is provided.  Grid lines are drawn on top.
    The returned surface is blitted as background every frame.
    """
    width = config.cols * config.cell_size + config.side_padding * 2
    height = config.rows * config.cell_size + config.top_bar_height + config.bottom_padding
    surface = pygame.Surface((width, height))
    surface.fill(COLORS["bg"])

    top = config.top_bar_height
    left = config.side_padding
    for r in range(config.rows):
        for c in range(config.cols):
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
    and (if active) the help panel in draw order.
    """
    screen.blit(app.base_surface, (0, 0))
    draw_overlay(screen, config, app)
    draw_hud(screen, title_font, font, small_font, config, app)
    if app.help_visible:
        draw_help_panel(screen, font, small_font, app)


def draw_overlay(screen: pygame.Surface, config: AppConfig, app: object) -> None:
    """Paint the per-frame search visualization layer.

    Renders visited cells, frontier cells, the current-expansion cell, the
    live/preview path, and start/goal markers using colours from ``COLORS``.
    """
    top = config.top_bar_height
    width = config.cols * config.cell_size + config.side_padding * 2
    height = config.rows * config.cell_size + config.top_bar_height + config.bottom_padding
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

    screen.blit(overlay, (0, 0))

    current = state["current"]
    if current and current not in (app.start, app.goal):
        rect = _cell_rect(config, top, current)
        inset = max(2, config.cell_size // 6)
        inner_rect = rect.inflate(-inset * 2, -inset * 2)
        pygame.draw.rect(screen, COLORS["search_current"], inner_rect, border_radius=max(3, config.cell_size // 4))

    show_live_path = app.algorithm_name in config.live_path_algorithms
    path_points = state["path"] if (state["finished"] or show_live_path) else []
    for point in path_points:
        if point in (app.start, app.goal):
            continue
        pygame.draw.rect(screen, COLORS["route"], _cell_rect(config, top, point), border_radius=2)

    for label, point in (("start", app.start), ("goal", app.goal)):
        pygame.draw.rect(screen, COLORS[label], _cell_rect(config, top, point))


def draw_hud(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    config: AppConfig,
    app: object,
) -> None:
    """Render the top-bar heads-up display.

    Shows algorithm name, run status, speed, weighted W, terrain toggle,
    maze history index, path stats, key hints, the legend, comparison board,
    and temporary status messages.
    """
    width = config.cols * config.cell_size + config.side_padding * 2
    pygame.draw.rect(screen, COLORS["panel"], pygame.Rect(0, 0, width, config.top_bar_height))

    status = "DONE" if app.finished else ("PAUSED" if app.paused else "RUNNING")
    terrain_text = "ON" if app.cost_map is not None else "OFF"
    stats = app.last_state["stats"]
    history_info = f"map {app.maze_index + 1}/{len(app.maze_history)}" if app.maze_history else ""
    line1 = (
        f"{app.algorithm_name} | {status} | speed {config.step_interval_ms}ms | "
        f"W {config.weighted_a_star_w:.1f} | terrain {terrain_text} | {history_info}"
    )
    line2 = (
        f"path {stats.path_length} | visited {stats.visited_count} | steps {stats.step_count} | "
        f"cost {stats.cost}"
    )
    line3 = "Space pause  +/- speed  C compare  M new  \u2190\u2192 history  H help"

    screen.blit(title_font.render("MazeVisualizer", True, COLORS["text"]), (10, 4))
    screen.blit(font.render(line1, True, COLORS["text"]), (10, 34))
    screen.blit(small_font.render(line2, True, COLORS["text_dim"]), (10, 58))
    screen.blit(small_font.render(line3, True, COLORS["text_dim"]), (10, 78))
    _draw_status_message(screen, small_font, config, app)
    draw_legend(screen, config)
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
    width = config.cols * config.cell_size + config.side_padding * 2
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
        color = COLORS["button_hover"] if rect.collidepoint(mouse_pos) else COLORS["button"]
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, COLORS["button_border"], rect, 2, border_radius=8)
        text_surface = font.render(label, True, COLORS["text"])
        screen.blit(
            text_surface,
            (rect.centerx - text_surface.get_width() // 2, rect.centery - text_surface.get_height() // 2),
        )

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
        color = COLORS["button_active"] if is_selected else COLORS["button"]
        if rect.collidepoint(mouse_pos):
            color = COLORS["button_hover"]
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, COLORS["button_border"], rect, 2, border_radius=8)
        text_surface = button_font.render(label, True, COLORS["text"])
        screen.blit(
            text_surface,
            (rect.centerx - text_surface.get_width() // 2, rect.centery - text_surface.get_height() // 2),
        )

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


def draw_legend(screen: pygame.Surface, config: AppConfig) -> None:
    """Draw colour legend inside the top-bar, wrapping to a second line if
    the screen width is too narrow (e.g. Small size preset on a low-res
    display).
    """
    legend_font = load_font(config.legend_font_size)
    items = [
        ("Visited", COLORS["search_visited"]),
        ("Frontier", COLORS["search_frontier"]),
        ("Current", COLORS["search_current"]),
        ("Path", COLORS["route"]),
        ("x1", COLORS["terrain_light"]),
        ("x3", COLORS["terrain_mid"]),
        ("x5", COLORS["terrain_heavy"]),
    ]
    swatch = 12
    gap = 8
    start_x = 10
    line_height = 18
    max_width = config.cols * config.cell_size + config.side_padding * 2 - 16
    lines: list[list[tuple[str, tuple[int, int, int]]]] = [[]]
    x = start_x
    for label, color in items:
        text_surface = legend_font.render(label, True, COLORS["text_dim"])
        item_width = swatch + 4 + text_surface.get_width()
        if x + item_width > max_width and lines[-1]:
            lines.append([])
            x = start_x
        lines[-1].append((label, color, text_surface))
        x += item_width + gap

    for row_idx, line in enumerate(lines):
        y = config.top_bar_height - 24 + row_idx * line_height
        x = start_x
        for label, color, text_surface in line:
            pygame.draw.rect(screen, color, pygame.Rect(x, y, swatch, swatch), border_radius=3)
            x += swatch + 4
            screen.blit(text_surface, (x, y - 1))
            x += text_surface.get_width() + gap

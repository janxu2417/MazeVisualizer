from __future__ import annotations

import pygame

from algorithms import CostMap, Point, StepState
from config import AppConfig, COLORS, HELP_LINES
from menu import ButtonSpec


def load_font(size: int, bold: bool = False) -> pygame.font.Font:
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
    screen.blit(app.base_surface, (0, 0))
    draw_overlay(screen, config, app)
    draw_hud(screen, title_font, font, small_font, config, app)
    if app.help_visible:
        draw_help_panel(screen, font, small_font)


def draw_overlay(screen: pygame.Surface, config: AppConfig, app: object) -> None:
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
    width = config.cols * config.cell_size + config.side_padding * 2
    pygame.draw.rect(screen, COLORS["panel"], pygame.Rect(0, 0, width, config.top_bar_height))

    status = "DONE" if app.finished else ("PAUSED" if app.paused else "RUNNING")
    terrain_text = "ON" if app.cost_map is not None else "OFF"
    stats = app.last_state["stats"]
    line1 = (
        f"{app.algorithm_name} | {status} | speed {config.step_interval_ms}ms | "
        f"W {config.weighted_a_star_w:.1f} | terrain {terrain_text}"
    )
    line2 = (
        f"path {stats.path_length} | visited {stats.visited_count} | steps {stats.step_count} | "
        f"cost {stats.cost} | optimal {'Yes' if stats.optimal else 'No'}"
    )
    line3 = "Space pause  +/- speed  C toggle compare  M new maze  H help"

    screen.blit(title_font.render("MazeVisualizer", True, COLORS["text"]), (10, 4))
    screen.blit(font.render(line1, True, COLORS["text"]), (10, 34))
    screen.blit(small_font.render(line2, True, COLORS["text_dim"]), (10, 58))
    screen.blit(small_font.render(line3, True, COLORS["text_dim"]), (10, 78))
    draw_legend(screen, config)
    draw_comparison_board(screen, small_font, config, app)


def draw_comparison_board(
    screen: pygame.Surface,
    font: pygame.font.Font,
    config: AppConfig,
    app: object,
) -> None:
    if not app.show_comparison or not app.comparison_results:
        return

    lines = ["Comparison"]
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
) -> None:
    screen.blit(background, (0, 0))
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
        draw_help_panel(screen, font, small_font)


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
    screen.blit(background, (0, 0))
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
) -> None:
    width, height = screen.get_size()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    line_height = small_font.get_linesize() + 6
    content_height = line_height * len(HELP_LINES)
    panel_w = min(width - 40, 720)
    panel_h = min(height - 40, content_height + 88)
    panel = pygame.Rect(
        width // 2 - panel_w // 2,
        height // 2 - panel_h // 2,
        panel_w,
        panel_h,
    )
    pygame.draw.rect(screen, COLORS["panel"], panel, border_radius=10)
    pygame.draw.rect(screen, COLORS["button_border"], panel, 2, border_radius=10)

    title = font.render("Help / 操作说明", True, COLORS["text"])
    screen.blit(title, (panel.x + 20, panel.y + 18))
    y = panel.y + 60
    for line in HELP_LINES:
        text_surface = small_font.render(line, True, COLORS["text_dim"])
        screen.blit(text_surface, (panel.x + 22, y))
        y += line_height


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
    x = 10
    y = config.top_bar_height - 24
    for label, color in items:
        pygame.draw.rect(screen, color, pygame.Rect(x, y, swatch, swatch), border_radius=3)
        x += swatch + 4
        text_surface = legend_font.render(label, True, COLORS["text_dim"])
        screen.blit(text_surface, (x, y - 1))
        x += text_surface.get_width() + gap

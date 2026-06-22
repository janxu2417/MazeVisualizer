from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from app import _create_state, _step_solver, AppState  # noqa: E402
from config import ALGORITHM_NAMES, AppConfig, COLORS  # noqa: E402
from menu import build_algo_buttons, build_menu_buttons  # noqa: E402
from render import (  # noqa: E402
    _compact_stat_row_layout,
    _regular_stat_grid_layout,
    build_base_surface,
    build_menu_background,
    draw_algo_menu,
    draw_help_panel,
    draw_menu,
    draw_run_view,
    load_font,
)


@pytest.fixture
def screen_and_fonts():
    pygame.init()
    screen = pygame.display.set_mode((800, 720))
    title_font = load_font(32, bold=True)
    font = load_font(20)
    small_font = load_font(16)
    yield screen, title_font, font, small_font
    pygame.quit()


def test_build_base_surface_returns_surface_with_expected_size(screen_and_fonts):
    screen, _, _, _ = screen_and_fonts
    config = AppConfig(rows=21, cols=21, cell_size=20)
    grid = [[1 for _ in range(config.cols)] for _ in range(config.rows)]
    surface = build_base_surface(config, grid, None)
    assert surface.get_width() == config.cols * config.cell_size + config.side_padding * 2
    assert surface.get_height() == config.rows * config.cell_size + config.top_bar_height + config.bottom_padding


def test_build_menu_background_returns_surface(screen_and_fonts):
    _, _, _, _ = screen_and_fonts
    surface = build_menu_background(640, 480)
    assert surface.get_size() == (640, 480)


def test_draw_menu_smoke(screen_and_fonts):
    screen, title_font, font, small_font = screen_and_fonts
    buttons = build_menu_buttons(screen.get_width(), screen.get_height())
    background = build_menu_background(screen.get_width(), screen.get_height())
    config = AppConfig(rows=21, cols=21)
    app = _create_state(config, "BFS")
    draw_menu(
        screen,
        title_font,
        font,
        small_font,
        buttons,
        background,
        "Medium",
        "Medium",
        "Maze: DFS Corridor",
        "BFS",
        "Terrain: OFF",
        show_help=False,
        app=app,
    )
    pygame.display.flip()


def test_draw_menu_blits_background_before_widgets(screen_and_fonts):
    screen, title_font, font, small_font = screen_and_fonts
    screen.fill((255, 0, 0))
    background = pygame.Surface(screen.get_size())
    background.fill((1, 2, 3))
    buttons = build_menu_buttons(screen.get_width(), screen.get_height())
    config = AppConfig(rows=21, cols=21)
    app = _create_state(config, "BFS")
    draw_menu(
        screen,
        title_font,
        font,
        small_font,
        buttons,
        background,
        "Medium",
        "Medium",
        "Maze: DFS Corridor",
        "BFS",
        "Terrain: OFF",
        show_help=False,
        app=app,
    )
    assert screen.get_at((0, 0))[:3] == (1, 2, 3)


def test_draw_algo_menu_smoke(screen_and_fonts):
    screen, title_font, font, small_font = screen_and_fonts
    buttons = build_algo_buttons(screen.get_width(), screen.get_height(), ALGORITHM_NAMES)
    background = build_menu_background(screen.get_width(), screen.get_height())
    draw_algo_menu(
        screen,
        title_font,
        font,
        small_font,
        AppConfig(),
        background,
        buttons,
        "A*",
        1.5,
    )
    pygame.display.flip()


def test_draw_algo_menu_blits_background_before_widgets(screen_and_fonts):
    screen, title_font, font, small_font = screen_and_fonts
    screen.fill((255, 0, 0))
    background = pygame.Surface(screen.get_size())
    background.fill((4, 5, 6))
    buttons = build_algo_buttons(screen.get_width(), screen.get_height(), ALGORITHM_NAMES)
    draw_algo_menu(
        screen,
        title_font,
        font,
        small_font,
        AppConfig(),
        background,
        buttons,
        "A*",
        1.5,
    )
    assert screen.get_at((0, 0))[:3] == (4, 5, 6)


def test_draw_help_panel_smoke(screen_and_fonts):
    screen, _, font, small_font = screen_and_fonts
    config = AppConfig(rows=21, cols=21)
    app = _create_state(config, "BFS")
    draw_help_panel(screen, font, small_font, app)
    pygame.display.flip()


def test_draw_run_view_smoke(screen_and_fonts):
    screen, title_font, font, small_font = screen_and_fonts
    config = AppConfig(rows=21, cols=21, terrain_mode=True)
    app_state = _create_state(config, "Bi-BFS")
    _step_solver(app_state)
    draw_run_view(screen, title_font, font, small_font, config, app_state)
    pygame.display.flip()


def test_draw_run_view_clears_uncovered_pixels(screen_and_fonts):
    screen, title_font, font, small_font = screen_and_fonts
    screen.fill((255, 0, 0))
    config = AppConfig(rows=21, cols=21)
    app_state = _create_state(config, "BFS")
    draw_run_view(screen, title_font, font, small_font, config, app_state)
    assert screen.get_at((screen.get_width() - 1, screen.get_height() - 1))[:3] == COLORS["bg"]


def test_draw_run_view_transforms_overlay_markers_with_zoom(screen_and_fonts):
    screen, title_font, font, small_font = screen_and_fonts
    config = AppConfig(rows=21, cols=21, cell_size=20)
    app_state = _create_state(config, "BFS")
    app_state.zoom = 2.0
    app_state.pan_x = 18
    app_state.pan_y = 10
    draw_run_view(screen, title_font, font, small_font, config, app_state)

    local_x = config.side_padding + app_state.start[1] * config.cell_size + config.cell_size // 2
    local_y = config.top_bar_height + app_state.start[0] * config.cell_size + config.cell_size // 2
    transformed = (
        app_state.pan_x + int(local_x * app_state.zoom),
        app_state.pan_y + int(local_y * app_state.zoom),
    )
    original = (local_x, local_y)

    assert screen.get_at(transformed)[:3] == COLORS["start"]
    assert screen.get_at(original)[:3] != COLORS["start"]


def test_compact_stat_row_layout_leaves_room_for_title():
    width = 21 * 20 + 34 * 2
    title_width = 150
    start_x, card_width, gap = _compact_stat_row_layout(width, title_width)
    left_bound = 12 + title_width + 18
    total_width = card_width * 4 + gap * 3

    assert start_x >= left_bound
    assert start_x + total_width <= width - 10


def test_regular_stat_grid_layout_avoids_left_and_right_text():
    width = 31 * 19 + 28 * 2
    left_zone_right = 232
    right_zone_left = 540
    start_x = _regular_stat_grid_layout(width, left_zone_right, right_zone_left, 232)

    assert start_x >= left_zone_right + 22
    assert start_x + 232 <= right_zone_left - 22


def test_regular_stat_grid_layout_prioritizes_left_clearance_when_space_is_tight():
    start_x = _regular_stat_grid_layout(645, 232, 470, 232)
    assert start_x == 254


def test_build_menu_buttons_include_new_actions():
    buttons = build_menu_buttons(800, 720)
    actions = [action for _, action, _ in buttons]
    assert actions == [
        "size",
        "complexity",
        "maze",
        "algo",
        "terrain",
        "theme",
        "new_maze",
        "edit",
        "start",
        "help",
    ]


def test_build_menu_buttons_small_layout_keeps_help_inside_window():
    width = 488
    height = 612
    buttons = build_menu_buttons(width, height)
    last_rect = buttons[-1][2]

    assert buttons[0][2].y >= 148
    assert last_rect.bottom <= height - 30

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app import _create_state, _step_solver  # noqa: E402
from config import ALGORITHM_NAMES, AppConfig  # noqa: E402
from menu import build_algo_buttons, build_menu_buttons  # noqa: E402
from render import (  # noqa: E402
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
    )
    pygame.display.flip()


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


def test_draw_help_panel_smoke(screen_and_fonts):
    screen, _, font, small_font = screen_and_fonts
    draw_help_panel(screen, font, small_font)
    pygame.display.flip()


def test_draw_run_view_smoke(screen_and_fonts):
    screen, title_font, font, small_font = screen_and_fonts
    config = AppConfig(rows=21, cols=21, terrain_mode=True)
    app_state = _create_state(config, "Bi-BFS")
    _step_solver(app_state)
    draw_run_view(screen, title_font, font, small_font, config, app_state)
    pygame.display.flip()

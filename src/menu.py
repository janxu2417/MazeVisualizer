"""Menu button builders and click-dispatch for the MazeVisualizer GUI."""

from __future__ import annotations

import pygame


ButtonSpec = tuple[str, str, pygame.Rect]
"""Tuple type for a menu button: ``(label, action, rect)``."""


def build_menu_buttons(width: int, height: int) -> list[ButtonSpec]:
    """Create the ten buttons for the main menu screen.

    Returns a list of ``(label, action, rect)`` tuples for Size, Complexity,
    Maze, Algorithm, Terrain, Theme, New Maze, Edit, Start, and Help.
    """
    compact = width <= 520 or height <= 640
    horizontal_margin = 32 if compact else 40
    button_w = min(340, width - horizontal_margin)
    button_h = 34 if compact else 40
    gap = 6 if compact else 10
    labels = [
        ("Size", "size"),
        ("Complexity", "complexity"),
        ("Maze", "maze"),
        ("Algorithm", "algo"),
        ("Terrain", "terrain"),
        ("Theme", "theme"),
        ("New Maze", "new_maze"),
        ("Edit Maze", "edit"),
        ("Start", "start"),
        ("Help", "help"),
    ]
    total_h = button_h * len(labels) + gap * (len(labels) - 1)
    top_clearance = 148 if compact else 132
    bottom_clearance = 30 if compact else 24
    centered_y = height // 2 - total_h // 2 + (6 if compact else 10)
    start_y = max(top_clearance, centered_y)
    start_y = min(start_y, height - bottom_clearance - total_h)
    x = width // 2 - button_w // 2
    buttons: list[ButtonSpec] = []
    for idx, (label, action) in enumerate(labels):
        y = start_y + idx * (button_h + gap)
        buttons.append((label, action, pygame.Rect(x, y, button_w, button_h)))
    return buttons


def build_algo_buttons(width: int, height: int, labels: list[str]) -> list[ButtonSpec]:
    """Create the algorithm-selection button layout.

    Arranges six algorithm buttons in a 2×3 grid, plus Back, W-, and W+
    controls.  Switches to compact sizing when the window is small.
    """
    compact = width <= 440 or height <= 560
    horizontal_margin = 32 if compact else 40
    column_gap = 12 if compact else 16
    button_w = min(240, (width - horizontal_margin * 2 - column_gap) // 2)
    button_h = 38 if compact else 42
    row_gap = 10 if compact else 16
    total_h = button_h * 3 + row_gap * 2
    start_y = 184 if compact else height // 2 - total_h // 2 + 10
    right_x = width // 2 + column_gap // 2
    left_x = width // 2 - button_w - column_gap // 2

    buttons: list[ButtonSpec] = []
    for idx, label in enumerate(labels):
        col_x = left_x if idx < 3 else right_x
        row = idx if idx < 3 else idx - 3
        y = start_y + row * (button_h + row_gap)
        buttons.append((label, label, pygame.Rect(col_x, y, button_w, button_h)))

    back_w = 140
    back_h = 36
    back_y = height - 84 if compact else height - 86
    buttons.append(("Back", "back", pygame.Rect(width // 2 - back_w // 2, back_y, back_w, back_h)))

    w_button_w = 70
    w_button_h = 34
    w_y = back_y - (56 if compact else 76)
    buttons.append(("W -", "w_minus", pygame.Rect(width // 2 - 102, w_y, w_button_w, w_button_h)))
    buttons.append(("W +", "w_plus", pygame.Rect(width // 2 + 32, w_y, w_button_w, w_button_h)))
    return buttons


def handle_menu_click(
    pos: tuple[int, int],
    buttons: list[ButtonSpec],
    blocked: bool,
) -> str | None:
    """Return the *action* of the button under *pos*, or ``None``.

    If *blocked* is ``True`` (help panel is open), no clicks are dispatched.
    """
    if blocked:
        return None
    for _, action, rect in buttons:
        if rect.collidepoint(pos):
            return action
    return None

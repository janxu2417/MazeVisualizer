from __future__ import annotations

import pygame


ButtonSpec = tuple[str, str, pygame.Rect]


def build_menu_buttons(width: int, height: int) -> list[ButtonSpec]:
    button_w = min(340, width - 40)
    button_h = 40
    gap = 10
    total_h = button_h * 7 + gap * 6
    start_y = max(132, height // 2 - total_h // 2 + 10)
    x = width // 2 - button_w // 2
    labels = [
        ("Size", "size"),
        ("Complexity", "complexity"),
        ("Maze", "maze"),
        ("Algorithm", "algo"),
        ("Terrain", "terrain"),
        ("Start", "start"),
        ("Help", "help"),
    ]
    buttons: list[ButtonSpec] = []
    for idx, (label, action) in enumerate(labels):
        y = start_y + idx * (button_h + gap)
        buttons.append((label, action, pygame.Rect(x, y, button_w, button_h)))
    return buttons


def build_algo_buttons(width: int, height: int, labels: list[str]) -> list[ButtonSpec]:
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
    if blocked:
        return None
    for _, action, rect in buttons:
        if rect.collidepoint(pos):
            return action
    return None

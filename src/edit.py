from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TYPE_CHECKING

from algorithms import CostMap, Grid, Point
from config import AppConfig

if TYPE_CHECKING:
    from app import AppState


class EditTool(Enum):
    DRAW_WALL = "draw_wall"
    PLACE_START = "place_start"
    PLACE_GOAL = "place_goal"
    PAINT_TERRAIN = "paint_terrain"
    INSPECT = "inspect"


@dataclass
class EditAction:
    edit_type: str
    cell: Point
    old_value: Any
    new_value: Any


@dataclass
class EditState:
    tool: EditTool = EditTool.DRAW_WALL
    hover_cell: Point | None = None
    tooltip_pos: tuple[int, int] = (0, 0)
    edit_history: list[EditAction] = field(default_factory=list)
    is_dragging: bool = False
    last_drag_cell: Point | None = None


def cell_from_pos(pos: tuple[int, int], config: AppConfig) -> Point | None:
    x, y = pos
    left = config.side_padding
    top = config.top_bar_height
    col = (x - left) // config.cell_size
    row = (y - top) // config.cell_size
    if 0 <= row < config.rows and 0 <= col < config.cols:
        return int(row), int(col)
    return None


def handle_edit_motion(pos: tuple[int, int], edit_state: EditState, config: AppConfig) -> None:
    edit_state.hover_cell = cell_from_pos(pos, config)
    edit_state.tooltip_pos = pos


def handle_edit_click(pos: tuple[int, int], edit_state: EditState, config: AppConfig, app: AppState) -> bool:
    cell = cell_from_pos(pos, config)
    edit_state.hover_cell = cell
    edit_state.tooltip_pos = pos
    if cell is None:
        return False
    if edit_state.tool == EditTool.INSPECT:
        return False
    return apply_edit_to_grid(app, cell, edit_state.tool, edit_state, config)


def handle_edit_drag(pos: tuple[int, int], edit_state: EditState, config: AppConfig, app: AppState) -> bool:
    if not edit_state.is_dragging or edit_state.tool != EditTool.DRAW_WALL:
        handle_edit_motion(pos, edit_state, config)
        return False
    cell = cell_from_pos(pos, config)
    edit_state.hover_cell = cell
    edit_state.tooltip_pos = pos
    if cell is None or cell == edit_state.last_drag_cell:
        return False
    edit_state.last_drag_cell = cell
    return apply_edit_to_grid(app, cell, edit_state.tool, edit_state, config)


def apply_edit_to_grid(
    app: AppState,
    cell: Point,
    tool: EditTool,
    edit_state: EditState,
    config: AppConfig,
) -> bool:
    row, col = cell
    if not _is_editable_cell(app.grid, cell):
        return False

    if tool == EditTool.DRAW_WALL:
        if cell in (app.start, app.goal):
            return False
        old_value = app.grid[row][col]
        new_value = 0 if old_value == 1 else 1
        app.grid[row][col] = new_value
        _sync_cost_cell(app, cell, new_value)
        _record(edit_state, EditAction("grid", cell, old_value, new_value))
        return True

    if tool == EditTool.PLACE_START:
        if cell == app.goal:
            return False
        old_start = app.start
        app.grid[row][col] = 1
        _ensure_cost_map_for_path(app, cell)
        app.start = cell
        _record(edit_state, EditAction("start", cell, old_start, cell))
        return True

    if tool == EditTool.PLACE_GOAL:
        if cell == app.start:
            return False
        old_goal = app.goal
        app.grid[row][col] = 1
        _ensure_cost_map_for_path(app, cell)
        app.goal = cell
        _record(edit_state, EditAction("goal", cell, old_goal, cell))
        return True

    if tool == EditTool.PAINT_TERRAIN:
        if app.grid[row][col] == 0:
            return False
        config.terrain_mode = True
        _ensure_cost_map(app)
        old_cost = app.cost_map[row][col]
        new_cost = {1: 3, 3: 5, 5: 1}.get(old_cost, 1)
        app.cost_map[row][col] = new_cost
        _record(edit_state, EditAction("terrain", cell, old_cost, new_cost))
        return True

    return False


def undo_last_edit(app: AppState, edit_state: EditState) -> bool:
    if not edit_state.edit_history:
        return False
    action = edit_state.edit_history.pop()
    row, col = action.cell
    if action.edit_type == "grid":
        app.grid[row][col] = action.old_value
        _sync_cost_cell(app, action.cell, action.old_value)
        return True
    if action.edit_type == "start":
        app.start = action.old_value
        return True
    if action.edit_type == "goal":
        app.goal = action.old_value
        return True
    if action.edit_type == "terrain":
        _ensure_cost_map(app)
        app.cost_map[row][col] = action.old_value
        return True
    return False


def get_cell_info(app: AppState, cell: Point) -> str:
    row, col = cell
    cell_type = "Path" if app.grid[row][col] == 1 else "Wall"
    cost = "N/A"
    if app.cost_map is not None and app.grid[row][col] == 1:
        cost = f"x{app.cost_map[row][col]}"
    tags = []
    if cell == app.start:
        tags.append("Start")
    if cell == app.goal:
        tags.append("Goal")
    state = app.last_state
    if cell in state["path"]:
        tags.append("Path")
    elif cell in state["frontier"]:
        tags.append("Frontier")
    elif cell in state["visited"]:
        tags.append("Visited")
    tag_text = f" [{', '.join(tags)}]" if tags else ""
    return f"Cell ({row}, {col}){tag_text}\nType: {cell_type}\nTerrain: {cost}"


def _record(edit_state: EditState, action: EditAction) -> None:
    edit_state.edit_history.append(action)
    if len(edit_state.edit_history) > 50:
        edit_state.edit_history.pop(0)


def _is_editable_cell(grid: Grid, cell: Point) -> bool:
    row, col = cell
    return 0 < row < len(grid) - 1 and 0 < col < len(grid[0]) - 1


def _ensure_cost_map(app: AppState) -> None:
    if app.cost_map is None:
        app.cost_map = [[1 if cell == 1 else 0 for cell in row] for row in app.grid]


def _ensure_cost_map_for_path(app: AppState, cell: Point) -> None:
    if app.cost_map is None:
        return
    row, col = cell
    if app.cost_map[row][col] == 0:
        app.cost_map[row][col] = 1


def _sync_cost_cell(app: AppState, cell: Point, grid_value: int) -> None:
    if app.cost_map is None:
        return
    row, col = cell
    app.cost_map[row][col] = 1 if grid_value == 1 else 0

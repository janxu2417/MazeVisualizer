from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Iterator

import pygame

from algorithms import (
    CostMap,
    Grid,
    Point,
    RunStats,
    StepState,
    generate_maze,
    solve_a_star,
    solve_bfs,
    solve_bidirectional_bfs,
    solve_dijkstra,
    solve_greedy_best_first,
    solve_weighted_a_star,
)
from edit import (
    EditState,
    EditTool,
    handle_edit_click,
    handle_edit_drag,
    handle_edit_motion,
    undo_last_edit,
)
from config import (
    ALGORITHM_NAMES,
    COMPLEXITY_OPTIONS,
    HELP_LINES,
    MAZE_OPTIONS,
    SIZE_OPTIONS,
    ZOOM_MAX,
    ZOOM_MIN,
    ZOOM_STEP,
    AppConfig,
    cycle_theme,
    get_theme,
    set_theme,
)
from menu import build_algo_buttons, build_menu_buttons, handle_menu_click
from render import (
    build_base_surface,
    build_menu_background,
    draw_algo_menu,
    draw_edit_view,
    draw_menu,
    draw_run_view,
    load_font,
)


SolverIterator = Iterator[StepState]


@dataclass
class MazeSnapshot:
    """A saved maze + its accumulated comparison results for history navigation.

    Immutable snapshot taken before generating a new maze so the user can
    return to a previous configuration with ``←`` / ``→`` keys.
    """

    grid: Grid
    start: Point
    goal: Point
    maze_method: str
    algorithm_name: str
    comparison_results: dict[str, RunStats]
    cost_map: CostMap | None = None
    visit_index: dict[Point, int] | None = None
    base_surface: pygame.Surface | None = None


@dataclass
class AppState:
    """Mutable runtime state for a single maze + algorithm session.

    Separated from :class:`AppConfig` to allow hot-reloading of algorithm
    and terrain without losing the shared configuration.

    *maze_history* stores previous mazes as ``MazeSnapshot`` objects.
    *maze_index* is the current position in the history (-1 for the live
    maze that hasn't been archived yet).
    """

    grid: Grid
    start: Point
    goal: Point
    algorithm_name: str
    solver: SolverIterator
    base_surface: pygame.Surface
    last_state: StepState
    visit_index: dict[Point, int] = field(default_factory=dict)
    demo_mode: bool = False
    step_hold: bool = False
    help_visible: bool = False
    was_paused: bool = False
    paused: bool = False
    finished: bool = False
    finished_time: int | None = None
    last_step_time: int = 0
    cost_map: CostMap | None = None
    comparison_results: dict[str, RunStats] = field(default_factory=dict)
    show_comparison: bool = True
    maze_history: list[MazeSnapshot] = field(default_factory=list)
    maze_index: int = -1
    status_message: str = ""
    status_message_time: int = 0
    help_scroll: int = 0
    edit_state: EditState = field(default_factory=EditState)
    visit_time: dict[Point, int] = field(default_factory=dict)
    path_reveal_start: int | None = None
    pan_x: int = 0
    pan_y: int = 0
    zoom: float = 1.0


def _dispatch_menu_event(
    event: pygame.event.Event,
    config: AppConfig,
    app: AppState,
    menu_buttons: list,
    algo_buttons: list,
    screen: pygame.Surface,
    menu_background: pygame.Surface,
    size_index: int,
    maze_index: int,
    complexity_custom_label: str | None,
    show_help: bool,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
) -> tuple[str, int, int, int, str | None, bool, pygame.Surface, list, list, pygame.Surface, pygame.font.Font, pygame.font.Font, pygame.font.Font]:
    """Dispatch a single event while the FSM is in ``"menu"`` mode.

    Returns the updated local state values for the caller to destructure.
    A fresh interactive state is returned every call so the caller never
    holds stale references.
    """
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and show_help:
        show_help = False
    if show_help and event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
        app.help_scroll += 1
    elif show_help and event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
        app.help_scroll -= 1
    elif show_help and event.type == pygame.MOUSEWHEEL:
        app.help_scroll -= event.y
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        action = handle_menu_click(event.pos, menu_buttons, show_help)
        if action == "help":
            show_help = True
        elif action == "size":
            size_index = (size_index + 1) % len(SIZE_OPTIONS)
            _apply_size_preset(config, app, SIZE_OPTIONS[size_index])
            screen, menu_buttons, menu_background = _resize_window(config)
            algo_buttons = build_algo_buttons(screen.get_width(), screen.get_height(), ALGORITHM_NAMES)
            title_font, font, small_font = _build_fonts(config)
        elif action == "complexity":
            complexity_custom_label = _cycle_complexity(config, COMPLEXITY_OPTIONS, complexity_custom_label)
        elif action == "maze":
            maze_index = (maze_index + 1) % len(MAZE_OPTIONS)
            complexity_custom_label = _apply_maze_option(config, MAZE_OPTIONS[maze_index])
        elif action == "algo":
            show_help = False
            return ("algo", size_index, maze_index, maze_index, complexity_custom_label, show_help, screen, menu_buttons, algo_buttons, menu_background, title_font, font, small_font)
        elif action == "terrain":
            config.terrain_mode = not config.terrain_mode
        elif action == "theme":
            theme = cycle_theme(config.theme_name)
            config.theme_name = theme.name
            menu_background = build_menu_background(screen.get_width(), screen.get_height())
        elif action == "new_maze":
            show_help = False
            config.step_interval_ms = config.default_step_ms
            _reset_maze(config, app, preserve_comparison=False)
        elif action == "edit":
            show_help = False
            config.step_interval_ms = config.default_step_ms
            app.paused = True
            app.step_hold = False
            app.finished = False
            return ("edit", size_index, maze_index, maze_index, complexity_custom_label, show_help, screen, menu_buttons, algo_buttons, menu_background, title_font, font, small_font)
        elif action == "start":
            show_help = False
            config.step_interval_ms = config.default_step_ms
            _reset_solver(config, app, app.algorithm_name, preserve_cost_map=app.cost_map is not None)
            return ("run", size_index, maze_index, maze_index, complexity_custom_label, show_help, screen, menu_buttons, algo_buttons, menu_background, title_font, font, small_font)
    return ("menu", size_index, maze_index, maze_index, complexity_custom_label, show_help, screen, menu_buttons, algo_buttons, menu_background, title_font, font, small_font)


def _dispatch_algo_event(
    event: pygame.event.Event,
    config: AppConfig,
    app: AppState,
    algo_buttons: list,
) -> str | None:
    """Dispatch a single event while the FSM is in ``"algo"`` mode.

    Returns the next mode name (``"menu"`` or ``None`` to stay).
    """
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        return "menu"
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        action = handle_menu_click(event.pos, algo_buttons, False)
        if action == "back":
            return "menu"
        elif action == "w_minus":
            _adjust_weight(config, -config.weighted_step)
        elif action == "w_plus":
            _adjust_weight(config, config.weighted_step)
        elif action:
            app.algorithm_name = action
    return None


def _dispatch_edit_event(
    event: pygame.event.Event,
    config: AppConfig,
    app: AppState,
) -> str | None:
    """Dispatch a single event while the FSM is in ``"edit"`` mode.

    Returns ``"menu"``, ``"run"``, or ``None`` to stay in edit.
    """
    if event.type == pygame.MOUSEMOTION:
        if handle_edit_drag(event.pos, app.edit_state, config, app):
            _refresh_edited_maze(config, app)
        else:
            handle_edit_motion(event.pos, app.edit_state, config)
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        app.edit_state.is_dragging = True
        app.edit_state.last_drag_cell = None
        if handle_edit_click(event.pos, app.edit_state, config, app):
            _refresh_edited_maze(config, app)
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        app.edit_state.is_dragging = False
        app.edit_state.last_drag_cell = None
    elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            app.edit_state.is_dragging = False
            app.edit_state.last_drag_cell = None
            return "menu"
        elif event.key == pygame.K_r:
            _reset_solver(config, app, app.algorithm_name, preserve_cost_map=app.cost_map is not None)
            return "run"
        elif event.key == pygame.K_d:
            app.edit_state.tool = EditTool.DRAW_WALL
        elif event.key == pygame.K_s:
            app.edit_state.tool = EditTool.PLACE_START
        elif event.key == pygame.K_g:
            app.edit_state.tool = EditTool.PLACE_GOAL
        elif event.key == pygame.K_t:
            app.edit_state.tool = EditTool.PAINT_TERRAIN
        elif event.key == pygame.K_i:
            app.edit_state.tool = EditTool.INSPECT
        elif event.key == pygame.K_u:
            theme = cycle_theme(config.theme_name)
            config.theme_name = theme.name
            _refresh_edited_maze(config, app)
        elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
            if undo_last_edit(app, app.edit_state):
                _refresh_edited_maze(config, app)
    return None


def _dispatch_run_event(
    event: pygame.event.Event,
    config: AppConfig,
    app: AppState,
    show_help: bool,
) -> tuple[str | None, bool]:
    """Dispatch a single event while the FSM is in ``"run"`` mode.

    Returns ``(next_mode, show_help)`` where *next_mode* may be ``"menu"``
    (Esc), ``"edit"`` (E key), or ``None`` to stay.
    """
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        if app.help_visible:
            _set_help_visible(app, False)
            return (None, show_help)
        else:
            app.paused = True
            app.step_hold = False
            app.help_visible = False
            return ("menu", False)
    elif event.type == pygame.KEYDOWN and event.key == pygame.K_h:
        _set_help_visible(app, not app.help_visible)
    elif app.help_visible and event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
        app.help_scroll += 1
    elif app.help_visible and event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
        app.help_scroll -= 1
    elif app.help_visible and event.type == pygame.MOUSEWHEEL:
        app.help_scroll -= event.y
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and not app.help_visible:
        # Right-click / middle-click: start pan
        app.dragging = True
        app.pan_origin = event.pos
        return (None, show_help)
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 3 and not app.help_visible:
        app.dragging = False
        return (None, show_help)
    elif event.type == pygame.MOUSEMOTION and getattr(app, "dragging", False):
        mx, my = event.pos
        ox, oy = app.pan_origin
        app.pan_origin = event.pos
        app.pan_x += mx - ox
        app.pan_y += my - oy
        return (None, show_help)
    elif event.type == pygame.MOUSEWHEEL and not app.help_visible:
        app.zoom = max(ZOOM_MIN, min(ZOOM_MAX, app.zoom + event.y * ZOOM_STEP))
        return (None, show_help)
    elif event.type == pygame.KEYUP and event.key == pygame.K_n:
        app.step_hold = False
    elif event.type == pygame.KEYDOWN and not app.help_visible:
        next_mode = _handle_keydown(event, config, app)
        return (next_mode, show_help)
    return (None, show_help)


def run_app() -> None:
    """Main application entry point — initialise and run the event loop.

    Lifecycle
    ---------
    1. Init Pygame, build fonts, create the 3-state FSM (menu/algo/run).
    2. In ``"menu"`` mode: configure size, complexity, maze method, terrain.
    3. In ``"algo"`` mode: choose a pathfinding algorithm and adjust W.
    4. In ``"run"`` mode: step the solver, render overlays + HUD + comparison.
    5. ESC returns to menu; ^C or window-close quits.

    Runs at a fixed 60 FPS via ``pygame.time.Clock``.  Solver stepping is
    independent of render rate, controlled by *config.step_interval_ms*.
    """
    pygame.init()
    config = AppConfig()
    set_theme(config.theme_name)
    size_index = 1
    maze_index = 0
    complexity_custom_label: str | None = None
    show_help = False

    _apply_size_option(config, SIZE_OPTIONS[size_index])
    _apply_complexity_option(config, COMPLEXITY_OPTIONS[1])
    complexity_custom_label = _apply_maze_option(config, MAZE_OPTIONS[maze_index])

    screen, menu_buttons, menu_background = _resize_window(config)
    algo_buttons = build_algo_buttons(screen.get_width(), screen.get_height(), ALGORITHM_NAMES)

    title_font, font, small_font = _build_fonts(config)
    clock = pygame.time.Clock()

    app = _create_state(config, "BFS")
    _convert_base_surface(app)
    mode = "menu"
    running = True

    while running:
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if mode == "menu":
                result = _dispatch_menu_event(
                    event, config, app, menu_buttons, algo_buttons,
                    screen, menu_background, size_index, maze_index,
                    complexity_custom_label, show_help,
                    title_font, font, small_font,
                )
                next_mode = result[0]
                if next_mode != "menu":
                    mode = next_mode
                size_index = result[1]
                maze_index = result[2]
                complexity_custom_label = result[4]
                show_help = result[5]
                screen = result[6]
                menu_buttons = result[7]
                algo_buttons = result[8]
                menu_background = result[9]
                title_font = result[10]
                font = result[11]
                small_font = result[12]

            elif mode == "algo":
                next_mode = _dispatch_algo_event(event, config, app, algo_buttons)
                if next_mode == "menu":
                    mode = "menu"
                    show_help = False

            elif mode == "edit":
                next_mode = _dispatch_edit_event(event, config, app)
                if next_mode in ("menu", "run"):
                    mode = next_mode
                    show_help = False

            else:
                next_mode, show_help = _dispatch_run_event(event, config, app, show_help)
                if next_mode:
                    mode = next_mode

        if mode == "run":
            if app.paused and app.step_hold and not app.finished:
                if now - app.last_step_time >= config.step_interval_ms:
                    _step_solver(app)
                    app.last_step_time = now
            if not app.paused and not app.finished:
                if now - app.last_step_time >= config.step_interval_ms:
                    _step_solver(app)
                    app.last_step_time = now
            draw_run_view(screen, title_font, font, small_font, config, app)
        elif mode == "algo":
            draw_algo_menu(
                screen,
                title_font,
                font,
                small_font,
                config,
                menu_background,
                algo_buttons,
                app.algorithm_name,
                config.weighted_a_star_w,
            )
        elif mode == "edit":
            draw_edit_view(screen, title_font, font, small_font, config, app)
        else:
            complexity_label = _complexity_label(config.loop_chance, COMPLEXITY_OPTIONS)
            terrain_label = "Terrain: ON (weighted)" if config.terrain_mode else "Terrain: OFF"
            draw_menu(
                screen,
                title_font,
                font,
                small_font,
                menu_buttons,
                menu_background,
                SIZE_OPTIONS[size_index][0],
                complexity_label,
                MAZE_OPTIONS[maze_index][0],
                app.algorithm_name,
                terrain_label,
                show_help,
                app,
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def _create_state(config: AppConfig, algorithm_name: str) -> AppState:
    """Allocate a fresh :class:`AppState` with a new maze and solver.

    Generates the maze, builds the optional cost map, creates the solver
    iterator, pre-renders the static base surface, and seeds the current
    maze-history snapshot so all later mode switches operate on one source
    of truth.
    """
    grid = generate_maze(
        config.rows,
        config.cols,
        loop_chance=config.loop_chance,
        method=config.maze_method,
    )
    start = (1, 1)
    goal = (config.rows - 2, config.cols - 2)
    grid[start[0]][start[1]] = 1
    grid[goal[0]][goal[1]] = 1
    cost_map = _build_cost_map(config, grid)
    solver = _make_solver(algorithm_name, grid, start, goal, config, cost_map)
    last_state = _empty_step_state(start)
    base_surface = build_base_surface(config, grid, cost_map)
    app = AppState(
        grid=grid,
        start=start,
        goal=goal,
        algorithm_name=algorithm_name,
        solver=solver,
        base_surface=base_surface,
        last_state=last_state,
        last_step_time=pygame.time.get_ticks(),
        cost_map=cost_map,
    )
    _sync_current_snapshot(config, app)
    return app


def _copy_cost_map(cost_map: CostMap | None) -> CostMap | None:
    if cost_map is None:
        return None
    return [row[:] for row in cost_map]


def _clear_edit_history(app: AppState) -> None:
    app.edit_state.edit_history.clear()
    app.edit_state.hover_cell = None
    app.edit_state.is_dragging = False
    app.edit_state.last_drag_cell = None


def _sync_current_snapshot(config: AppConfig, app: AppState) -> None:
    comparison_results = app.comparison_results
    if 0 <= app.maze_index < len(app.maze_history):
        snapshot = app.maze_history[app.maze_index]
        snapshot.grid = [row[:] for row in app.grid]
        snapshot.start = app.start
        snapshot.goal = app.goal
        snapshot.maze_method = config.maze_method
        snapshot.algorithm_name = app.algorithm_name
        snapshot.cost_map = _copy_cost_map(app.cost_map)
        if snapshot.comparison_results is not comparison_results:
            snapshot.comparison_results = comparison_results
    else:
        snapshot = MazeSnapshot(
            grid=[row[:] for row in app.grid],
            start=app.start,
            goal=app.goal,
            maze_method=config.maze_method,
            algorithm_name=app.algorithm_name,
            comparison_results=comparison_results,
            cost_map=_copy_cost_map(app.cost_map),
        )
        app.maze_history = [snapshot]
        app.maze_index = 0
    app.comparison_results = snapshot.comparison_results


def _handle_keydown(event: pygame.event.Event, config: AppConfig, app: AppState) -> str | None:
    """Dispatch a ``KEYDOWN`` event to the appropriate action.

    Supports: Space (pause), N (single-step), +/- (speed), [/] (W adjust),
    1-6 (switch algorithm), R (restart), T (terrain), C (compare),
    M (new maze), Left/Right (history), E (export), Ctrl+I (import).
    """
    key = event.key
    if key == pygame.K_SPACE:
        app.paused = not app.paused
        return None

    if key == pygame.K_n:
        if not app.finished:
            if not app.paused:
                app.paused = True
            app.step_hold = True
            _step_solver(app)
            app.last_step_time = pygame.time.get_ticks()
        return

    if key in (pygame.K_EQUALS, pygame.K_KP_PLUS) or event.unicode == "+":
        _adjust_speed(config, -config.step_delta_ms)
        return

    if key in (pygame.K_MINUS, pygame.K_KP_MINUS) or event.unicode == "-":
        _adjust_speed(config, config.step_delta_ms)
        return

    if key == pygame.K_LEFTBRACKET:
        _adjust_weight(config, -config.weighted_step)
        if app.algorithm_name == "Weighted A*":
            _reset_solver(config, app, app.algorithm_name, preserve_cost_map=app.cost_map is not None)
        return

    if key == pygame.K_RIGHTBRACKET:
        _adjust_weight(config, config.weighted_step)
        if app.algorithm_name == "Weighted A*":
            _reset_solver(config, app, app.algorithm_name, preserve_cost_map=app.cost_map is not None)
        return

    if key == pygame.K_r:
        _reset_solver(config, app, app.algorithm_name, preserve_cost_map=app.cost_map is not None)
        return

    if key == pygame.K_t:
        config.terrain_mode = not config.terrain_mode
        _reset_solver(config, app, app.algorithm_name)
        return

    if key == pygame.K_c:
        app.show_comparison = not app.show_comparison
        return

    if key == pygame.K_e:
        app.paused = True
        app.step_hold = False
        app.finished = False
        return "edit"

    if key == pygame.K_u:
        theme = cycle_theme(config.theme_name)
        config.theme_name = theme.name
        app.base_surface = build_base_surface(config, app.grid, app.cost_map)
        _convert_base_surface(app)
        return

    if key == pygame.K_1:
        _reset_solver(config, app, "BFS", preserve_cost_map=app.cost_map is not None)
        return

    if key == pygame.K_2:
        _reset_solver(config, app, "Dijkstra", preserve_cost_map=app.cost_map is not None)
        return

    if key == pygame.K_3:
        _reset_solver(config, app, "A*", preserve_cost_map=app.cost_map is not None)
        return

    if key == pygame.K_4:
        _reset_solver(config, app, "Bi-BFS", preserve_cost_map=app.cost_map is not None)
        return

    if key == pygame.K_5:
        _reset_solver(config, app, "Greedy", preserve_cost_map=app.cost_map is not None)
        return

    if key == pygame.K_6:
        _reset_solver(config, app, "Weighted A*", preserve_cost_map=app.cost_map is not None)
        return

    if key == pygame.K_m:
        _reset_maze(config, app, preserve_comparison=True)

    if key == pygame.K_LEFT:
        _navigate_history(config, app, -1)

    if key == pygame.K_RIGHT:
        _navigate_history(config, app, 1)

    if key == pygame.K_F5:
        _export_comparison(app, "comparison_export.json")
        app.status_message = "Exported comparison_export.json"
        app.status_message_time = pygame.time.get_ticks()
        return

    if key == pygame.K_F6:
        try:
            grid = _import_maze_grid("maze_import.txt")
            app.grid = grid
            app.start = (1, 1)
            app.goal = (len(grid) - 2, len(grid[0]) - 2)
            app.grid[app.start[0]][app.start[1]] = 1
            app.grid[app.goal[0]][app.goal[1]] = 1
            # sync config logical dimensions to the imported grid
            config.rows = len(grid)
            config.cols = len(grid[0])
            app.cost_map = _build_cost_map(config, app.grid)
            app.base_surface = build_base_surface(config, app.grid, app.cost_map)
            _convert_base_surface(app)
            app.comparison_results = {}
            app.maze_history.clear()
            app.maze_index = -1
            _clear_edit_history(app)
            _sync_current_snapshot(config, app)
            app.show_comparison = True
            _reset_solver(config, app, app.algorithm_name, preserve_cost_map=app.cost_map is not None)
            app.status_message = "Imported maze_import.txt"
            app.status_message_time = pygame.time.get_ticks()
        except (FileNotFoundError, ValueError) as exc:
            app.status_message = f"Import failed: {exc}"
            app.status_message_time = pygame.time.get_ticks()
        return


def _refresh_edited_maze(config: AppConfig, app: AppState) -> None:
    app.base_surface = build_base_surface(config, app.grid, app.cost_map)
    _convert_base_surface(app)
    app.comparison_results.clear()
    _sync_current_snapshot(config, app)
    app.last_state = _empty_step_state(app.start)
    app.finished = False
    app.paused = True
    app.step_hold = False
    app.finished_time = None
    app.status_message = "Edited maze updated"
    app.status_message_time = pygame.time.get_ticks()



def _reset_solver(
    config: AppConfig,
    app: AppState,
    algorithm_name: str,
    preserve_cost_map: bool = False,
) -> None:
    """Rebuild the solver iterator for *algorithm_name* on the current maze.

    Resets all runtime state (visit index, pause, finished flags) without
    generating a new maze.  The cost map and base surface are rebuilt to
    reflect the current terrain setting.
    """
    app.algorithm_name = algorithm_name
    if not preserve_cost_map:
        app.cost_map = _build_cost_map(config, app.grid)
    elif app.cost_map is None and config.terrain_mode:
        app.cost_map = _build_cost_map(config, app.grid)
    app.base_surface = build_base_surface(config, app.grid, app.cost_map)
    _convert_base_surface(app)
    app.solver = _make_solver(algorithm_name, app.grid, app.start, app.goal, config, app.cost_map)
    app.visit_index = {}
    app.last_state = _empty_step_state(app.start)
    app.step_hold = False
    app.help_visible = False
    app.was_paused = False
    app.paused = False
    app.finished = False
    app.finished_time = None
    app.last_step_time = pygame.time.get_ticks()


def _reset_maze(config: AppConfig, app: AppState, preserve_comparison: bool) -> None:
    """Generate a brand-new maze and restart the current solver on it.

    Archives the current maze as a snapshot in *maze_history* then creates
    a fresh entry for the new maze.  *preserve_comparison* is ignored —
    every new maze gets its own clean comparison board.  ``Left`` / ``Right``
    arrow keys restore previous snapshots.
    """
    if not preserve_comparison:
        app.maze_history.clear()
        app.maze_index = -1
    elif app.maze_history:
        _sync_current_snapshot(config, app)
        if app.maze_index < len(app.maze_history) - 1:
            app.maze_history = app.maze_history[: app.maze_index + 1]

    app.grid = generate_maze(
        config.rows,
        config.cols,
        loop_chance=config.loop_chance,
        method=config.maze_method,
    )
    app.start = (1, 1)
    app.goal = (config.rows - 2, config.cols - 2)
    app.grid[app.start[0]][app.start[1]] = 1
    app.grid[app.goal[0]][app.goal[1]] = 1
    app.cost_map = _build_cost_map(config, app.grid)
    app.base_surface = build_base_surface(config, app.grid, app.cost_map)
    _convert_base_surface(app)
    app.comparison_results = {}
    snapshot = MazeSnapshot(
        grid=[row[:] for row in app.grid],
        start=app.start,
        goal=app.goal,
        maze_method=config.maze_method,
        algorithm_name=app.algorithm_name,
        comparison_results=app.comparison_results,
        cost_map=_copy_cost_map(app.cost_map),
    )
    app.maze_history.append(snapshot)
    app.maze_index = len(app.maze_history) - 1
    _clear_edit_history(app)
    app.show_comparison = True
    _reset_solver(config, app, app.algorithm_name, preserve_cost_map=app.cost_map is not None)


def _navigate_history(config: AppConfig, app: AppState, direction: int) -> None:
    """Move *direction* steps through the maze history (-1 back, +1 forward).

    Swaps in the target snapshot's grid, start, goal, algorithm, and
    ``comparison_results`` (by reference, so future solver runs auto-save).
    Does nothing when the target index is out of bounds.
    """
    target = app.maze_index + direction
    if target < 0 or target >= len(app.maze_history):
        return
    _sync_current_snapshot(config, app)
    app.maze_index = target
    snapshot = app.maze_history[target]
    app.comparison_results = snapshot.comparison_results
    app.grid = [row[:] for row in snapshot.grid]
    app.start = snapshot.start
    app.goal = snapshot.goal
    app.algorithm_name = snapshot.algorithm_name
    app.cost_map = _copy_cost_map(snapshot.cost_map)
    app.base_surface = build_base_surface(config, app.grid, app.cost_map)
    _convert_base_surface(app)
    _clear_edit_history(app)
    app.solver = _make_solver(app.algorithm_name, app.grid, app.start, app.goal, config, app.cost_map)
    app.visit_index = {}
    app.last_state = _empty_step_state(app.start)
    app.step_hold = False
    app.help_visible = False
    app.was_paused = False
    app.paused = False
    app.finished = False
    app.finished_time = None
    app.last_step_time = pygame.time.get_ticks()
    app.show_comparison = True


def _export_comparison(app: AppState, filepath: str) -> None:
    """Write the current comparison results to a JSON file.

    Includes per-algorithm stats and a compact representation of the maze
    grid (1 = path, 0 = wall) for reproducibility.
    """
    import json

    data = {
        "rows": len(app.grid),
        "cols": len(app.grid[0]) if app.grid else 0,
        "algorithm": app.algorithm_name,
        "comparison_results": {
            algo: {
                "path_length": s.path_length,
                "visited_count": s.visited_count,
                "step_count": s.step_count,
                "cost": s.cost,
                "optimal": s.optimal,
            }
            for algo, s in app.comparison_results.items()
        },
        "grid": app.grid,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Comparison exported to {filepath}")


def _import_maze_grid(filepath: str) -> Grid:
    """Load a maze grid from a text file.

    Supported format: lines of whitespace-separated ``0`` (wall) and ``1``
    (path) tokens.  Lines may have trailing whitespace.  The first and last
    lines are used as-is; start/goal are auto-detected as (1,1) and
    (rows-2, cols-2) after setting those cells to 1.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        grid = []
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            row = [int(tok) for tok in stripped.split()]
            grid.append(row)
    if not grid:
        raise ValueError("import file is empty")
    row_len = len(grid[0])
    for row in grid:
        if len(row) != row_len:
            raise ValueError("import grid has inconsistent row lengths")
    return grid


def _step_solver(app: AppState) -> None:
    """Advance the solver by one frame and update :class:`AppState`.

    Reads the next :class:`~algorithms.StepState` from the solver iterator.
    On completion, records the final stats in ``comparison_results`` and
    sets the ``finished`` / ``paused`` flags.
    """
    try:
        state = next(app.solver)
        app.last_state = state
        for point in state["visited"]:
            if point not in app.visit_index:
                app.visit_index[point] = len(app.visit_index)
        if state["finished"]:
            app.finished = True
            app.paused = True
            app.finished_time = pygame.time.get_ticks()
            app.step_hold = False
            app.comparison_results[app.algorithm_name] = state["stats"]
            if 0 <= app.maze_index < len(app.maze_history):
                app.maze_history[app.maze_index].comparison_results = app.comparison_results
    except StopIteration:
        app.finished = True
        app.paused = True
        app.finished_time = pygame.time.get_ticks()
        app.step_hold = False


def _convert_base_surface(app: AppState) -> None:
    """Call ``.convert()`` on the base surface for faster blitting.

    Should be called whenever the surface is rebuilt (maze regen, terrain
    toggle) while a display mode is active.
    """
    if pygame.display.get_surface() is not None:
        app.base_surface = app.base_surface.convert()


def _adjust_speed(config: AppConfig, delta_ms: int) -> None:
    """Change the solver step interval by *delta_ms*, clamped to bounds.

    Positive *delta_ms* = slower; negative = faster.
    """
    config.step_interval_ms = max(
        config.min_step_ms,
        min(config.max_step_ms, config.step_interval_ms + delta_ms),
    )


def _adjust_weight(config: AppConfig, delta: float) -> None:
    """Change the Weighted A* parameter *W* by *delta*, clamped to bounds."""
    config.weighted_a_star_w = max(
        config.min_weight,
        min(config.max_weight, config.weighted_a_star_w + delta),
    )


def _make_solver(
    algorithm_name: str,
    grid: Grid,
    start: Point,
    goal: Point,
    config: AppConfig,
    cost_map: CostMap | None,
) -> SolverIterator:
    """Factory: return a step-yielding solver iterator for the given algorithm.

    Maps algorithm names (``"BFS"``, ``"Dijkstra"``, etc.) to the
    corresponding solver function from :mod:`algorithms`.
    """
    if algorithm_name == "BFS":
        return iter(solve_bfs(grid, start, goal, cost_map=cost_map))
    if algorithm_name == "Dijkstra":
        return iter(solve_dijkstra(grid, start, goal, cost_map=cost_map))
    if algorithm_name == "A*":
        return iter(solve_a_star(grid, start, goal, cost_map=cost_map))
    if algorithm_name == "Bi-BFS":
        return iter(solve_bidirectional_bfs(grid, start, goal, cost_map=cost_map))
    if algorithm_name == "Greedy":
        return iter(solve_greedy_best_first(grid, start, goal, cost_map=cost_map))
    if algorithm_name == "Weighted A*":
        return iter(solve_weighted_a_star(grid, start, goal, weight=config.weighted_a_star_w, cost_map=cost_map))
    raise ValueError(f"unknown algorithm: {algorithm_name}")


def _apply_size_option(config: AppConfig, option: tuple[str, int, int, int]) -> None:
    """Apply a size preset (Small / Medium / Large) to *config*.

    Updates rows, cols, cell_size, padding, and font sizes.
    """
    label, rows, cols, cell_size = option
    config.rows = rows
    config.cols = cols
    config.cell_size = cell_size
    if label == "Small":
        config.top_bar_height = 132
        config.side_padding = 34
        config.bottom_padding = 60
        config.title_font_size = 28
        config.body_font_size = 16
        config.small_font_size = 12
        config.legend_font_size = 12
        config.algo_button_font_size = 18
        config.algo_subtitle_font_size = 15
        config.algo_weight_font_size = 13
        config.algo_weight_label_nudge_y = 8
    elif label == "Medium":
        config.top_bar_height = 126
        config.side_padding = 28
        config.bottom_padding = 56
        config.title_font_size = 30
        config.body_font_size = 18
        config.small_font_size = 14
        config.legend_font_size = 13
        config.algo_button_font_size = 20
        config.algo_subtitle_font_size = 16
        config.algo_weight_font_size = 15
        config.algo_weight_label_nudge_y = 4
    else:
        config.top_bar_height = 120
        config.side_padding = 18
        config.bottom_padding = 42
        config.title_font_size = 28
        config.body_font_size = 16
        config.small_font_size = 13
        config.legend_font_size = 12
        config.algo_button_font_size = 18
        config.algo_subtitle_font_size = 15
        config.algo_weight_font_size = 14
        config.algo_weight_label_nudge_y = 2


def _apply_size_preset(config: AppConfig, app: AppState, option: tuple[str, int, int, int]) -> None:
    """Apply a size preset and rebuild the current maze to match it.

    Size changes alter the logical grid dimensions, so the live maze, terrain,
    snapshot history, and solver must all be regenerated to keep rendering and
    pathfinding in sync with ``config.rows`` / ``config.cols``.
    """
    _apply_size_option(config, option)
    app.maze_history.clear()
    app.maze_index = -1
    _clear_edit_history(app)
    _reset_maze(config, app, preserve_comparison=False)


def _apply_complexity_option(config: AppConfig, option: tuple[str, float]) -> None:
    """Set *loop_chance* from a complexity preset (Low / Medium / High)."""
    _, loop_chance = option
    config.loop_chance = loop_chance


def _apply_maze_option(
    config: AppConfig,
    option: tuple[str, str, float | None, str | None],
) -> str | None:
    """Apply a maze-generation preset, optionally overriding *loop_chance*.

    Returns a custom label string (e.g. ``"Dense"``) when the preset
    overrides the default loop chance, or ``None`` otherwise.
    """
    _, method, loop_override, label_override = option
    config.maze_method = method
    if loop_override is not None:
        config.loop_chance = loop_override
        return label_override
    nearest = min(COMPLEXITY_OPTIONS, key=lambda opt: abs(config.loop_chance - opt[1]))
    config.loop_chance = nearest[1]
    return None


def _resize_window(config: AppConfig, *, grid: list[list[int]] | None = None) -> tuple[pygame.Surface, list[tuple[str, str, pygame.Rect]], pygame.Surface]:
    """Create or resize the Pygame window to match the display dimensions.

    When *grid* is provided its column count is used to derive the board
    width; otherwise *config.rows* / *config.cols* are used (menu-mode
    defaults).

    Returns the new screen surface, rebuilt menu buttons, and a
    pre-rendered background.  Explicitly reinitialises the display
    subsystem on every call to prevent orphaned windows on Windows.
    """
    cols = len(grid[0]) if grid else config.cols
    rows = len(grid) if grid else config.rows
    width = cols * config.cell_size + config.side_padding * 2
    height = rows * config.cell_size + config.top_bar_height + config.bottom_padding
    try:
        pygame.display.quit()
    except Exception:
        pass
    pygame.display.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("MazeVisualizer")
    menu_buttons = build_menu_buttons(width, height)
    menu_background = build_menu_background(width, height)
    return screen, menu_buttons, menu_background


def _build_fonts(config: AppConfig) -> tuple[pygame.font.Font, pygame.font.Font, pygame.font.Font]:
    """Load the three main font sizes (title, body, small) from system fonts."""
    return (
        load_font(config.title_font_size, bold=True),
        load_font(config.body_font_size),
        load_font(config.small_font_size),
    )


def _complexity_label(
    loop_chance: float,
    options: list[tuple[str, float]],
) -> str:
    """Return the nearest complexity preset name for *loop_chance*.

    Always maps to one of Low / Medium / High; never shows maze-specific
    labels such as ``"Sparse"`` or raw ``"Custom X.XX"`` strings.
    """
    nearest = min(options, key=lambda opt: abs(loop_chance - opt[1]))
    return nearest[0]


def _cycle_complexity(
    config: AppConfig,
    options: list[tuple[str, float]],
    custom_label: str | None,
) -> str | None:
    """Advance *loop_chance* to the next preset value (circular).

    If the current value is custom (not matching any preset), it is
    inserted temporarily so the user can cycle back to it.  Returns
    ``None`` when the new value matches a preset, or a custom label
    otherwise.
    """
    base_values = {value for _, value in options}
    cycle = list(options)
    if config.loop_chance not in base_values:
        label = custom_label or f"Custom {config.loop_chance:.2f}"
        cycle.insert(0, (label, config.loop_chance))

    index = 0
    for idx, (_, value) in enumerate(cycle):
        if abs(config.loop_chance - value) < 1e-6:
            index = idx
            break
    index = (index + 1) % len(cycle)
    next_label, next_value = cycle[index]
    config.loop_chance = next_value
    if next_value in base_values:
        return None
    return next_label


def _set_help_visible(app: AppState, visible: bool) -> None:
    """Toggle the help overlay, pausing/resuming the solver appropriately.

    When the help panel is shown the solver is paused; when dismissed it
    returns to its previous pause state.
    """
    if visible and not app.help_visible:
        app.help_visible = True
        app.was_paused = app.paused
        app.paused = True
        app.step_hold = False
        return
    if not visible and app.help_visible:
        app.help_visible = False
        app.paused = app.was_paused


def _build_cost_map(config: AppConfig, grid: Grid) -> CostMap | None:
    """Build a terrain cost map, or return ``None`` if terrain is off.

    When enabled, each passable cell is assigned a random cost of 1, 3,
    or 5 based on *terrain_ratio* and a deterministic seed derived from
    *terrain_seed* + grid dimensions.
    """
    if not config.terrain_mode:
        return None
    rng = random.Random(config.terrain_seed + len(grid) * 100 + len(grid[0]) if grid else 0)
    cost_map: CostMap = []
    for row in grid:
        cost_row: list[int] = []
        for cell in row:
            if cell == 0:
                cost_row.append(0)
                continue
            roll = rng.random()
            if roll < config.terrain_ratio:
                cost_row.append(5)
            elif roll < config.terrain_ratio * 2:
                cost_row.append(3)
            else:
                cost_row.append(1)
        cost_map.append(cost_row)
    return cost_map


def _empty_step_state(start: Point) -> StepState:
    """Return a blank :class:`~algorithms.StepState` initialised at *start*.

    Used to populate ``last_state`` before the solver has yielded its
    first frame.
    """
    return {
        "current": start,
        "visited": set(),
        "frontier": set(),
        "path": [],
        "finished": False,
        "stats": RunStats(visited_count=0, path_length=0, step_count=0, optimal=True, cost=0),
        "visited_from_start": set(),
        "visited_from_goal": set(),
        "meet_point": None,
    }


if __name__ == "__main__":
    run_app()

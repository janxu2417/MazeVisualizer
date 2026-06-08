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
from config import (
    ALGORITHM_NAMES,
    COMPLEXITY_OPTIONS,
    HELP_LINES,
    MAZE_OPTIONS,
    SIZE_OPTIONS,
    AppConfig,
)
from menu import build_algo_buttons, build_menu_buttons, handle_menu_click
from render import (
    build_base_surface,
    build_menu_background,
    draw_algo_menu,
    draw_menu,
    draw_run_view,
    load_font,
)


SolverIterator = Iterator[StepState]


@dataclass
class AppState:
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


def run_app() -> None:
    pygame.init()
    config = AppConfig()
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
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and show_help:
                    show_help = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = handle_menu_click(event.pos, menu_buttons, show_help)
                    if action == "help":
                        show_help = True
                    elif action == "size":
                        size_index = (size_index + 1) % len(SIZE_OPTIONS)
                        _apply_size_option(config, SIZE_OPTIONS[size_index])
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
                        mode = "algo"
                    elif action == "terrain":
                        config.terrain_mode = not config.terrain_mode
                    elif action == "start":
                        show_help = False
                        mode = "run"
                        config.step_interval_ms = config.default_step_ms
                        _reset_maze(config, app, preserve_comparison=False)

            elif mode == "algo":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    mode = "menu"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = handle_menu_click(event.pos, algo_buttons, False)
                    if action == "back":
                        mode = "menu"
                    elif action == "w_minus":
                        _adjust_weight(config, -config.weighted_step)
                    elif action == "w_plus":
                        _adjust_weight(config, config.weighted_step)
                    elif action:
                        app.algorithm_name = action

            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if app.help_visible:
                        _set_help_visible(app, False)
                    else:
                        mode = "menu"
                        show_help = False
                        app.paused = True
                        app.step_hold = False
                        app.help_visible = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                    _set_help_visible(app, not app.help_visible)
                elif event.type == pygame.KEYUP and event.key == pygame.K_n:
                    app.step_hold = False
                elif event.type == pygame.KEYDOWN and not app.help_visible:
                    _handle_keydown(event, config, app)

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
        else:
            complexity_label = _complexity_label(config.loop_chance, COMPLEXITY_OPTIONS, complexity_custom_label)
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
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def _create_state(config: AppConfig, algorithm_name: str) -> AppState:
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
    return AppState(
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


def _handle_keydown(event: pygame.event.Event, config: AppConfig, app: AppState) -> None:
    key = event.key
    if key == pygame.K_SPACE:
        app.paused = not app.paused
        return

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
            _reset_solver(config, app, app.algorithm_name)
        return

    if key == pygame.K_RIGHTBRACKET:
        _adjust_weight(config, config.weighted_step)
        if app.algorithm_name == "Weighted A*":
            _reset_solver(config, app, app.algorithm_name)
        return

    if key == pygame.K_r:
        _reset_solver(config, app, app.algorithm_name)
        return

    if key == pygame.K_t:
        config.terrain_mode = not config.terrain_mode
        _reset_solver(config, app, app.algorithm_name)
        return

    if key == pygame.K_c:
        app.show_comparison = not app.show_comparison
        return

    if key == pygame.K_1:
        _reset_solver(config, app, "BFS")
        return

    if key == pygame.K_2:
        _reset_solver(config, app, "Dijkstra")
        return

    if key == pygame.K_3:
        _reset_solver(config, app, "A*")
        return

    if key == pygame.K_4:
        _reset_solver(config, app, "Bi-BFS")
        return

    if key == pygame.K_5:
        _reset_solver(config, app, "Greedy")
        return

    if key == pygame.K_6:
        _reset_solver(config, app, "Weighted A*")
        return

    if key == pygame.K_m:
        _reset_maze(config, app, preserve_comparison=False)


def _reset_solver(config: AppConfig, app: AppState, algorithm_name: str) -> None:
    app.algorithm_name = algorithm_name
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
    if not preserve_comparison:
        app.comparison_results.clear()
    app.show_comparison = True
    _reset_solver(config, app, app.algorithm_name)


def _step_solver(app: AppState) -> None:
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
    except StopIteration:
        app.finished = True
        app.paused = True
        app.finished_time = pygame.time.get_ticks()
        app.step_hold = False


def _convert_base_surface(app: AppState) -> None:
    if pygame.display.get_surface() is not None:
        app.base_surface = app.base_surface.convert()


def _adjust_speed(config: AppConfig, delta_ms: int) -> None:
    config.step_interval_ms = max(
        config.min_step_ms,
        min(config.max_step_ms, config.step_interval_ms + delta_ms),
    )


def _adjust_weight(config: AppConfig, delta: float) -> None:
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
    label, rows, cols, cell_size = option
    config.rows = rows
    config.cols = cols
    config.cell_size = cell_size
    if label == "Small":
        config.top_bar_height = 118
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


def _apply_complexity_option(config: AppConfig, option: tuple[str, float]) -> None:
    _, loop_chance = option
    config.loop_chance = loop_chance


def _apply_maze_option(
    config: AppConfig,
    option: tuple[str, str, float | None, str | None],
) -> str | None:
    _, method, loop_override, label_override = option
    config.maze_method = method
    if loop_override is not None:
        config.loop_chance = loop_override
        return label_override
    return None


def _resize_window(config: AppConfig) -> tuple[pygame.Surface, list[tuple[str, str, pygame.Rect]], pygame.Surface]:
    width = config.cols * config.cell_size + config.side_padding * 2
    height = config.rows * config.cell_size + config.top_bar_height + config.bottom_padding
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("MazeVisualizer")
    menu_buttons = build_menu_buttons(width, height)
    menu_background = build_menu_background(width, height)
    return screen, menu_buttons, menu_background


def _build_fonts(config: AppConfig) -> tuple[pygame.font.Font, pygame.font.Font, pygame.font.Font]:
    return (
        load_font(config.title_font_size, bold=True),
        load_font(config.body_font_size),
        load_font(config.small_font_size),
    )


def _complexity_label(
    loop_chance: float,
    options: list[tuple[str, float]],
    custom_label: str | None,
) -> str:
    for label, value in options:
        if abs(loop_chance - value) < 1e-6:
            return label
    if custom_label:
        return custom_label
    return f"Custom {loop_chance:.2f}"


def _cycle_complexity(
    config: AppConfig,
    options: list[tuple[str, float]],
    custom_label: str | None,
) -> str | None:
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
    if not config.terrain_mode:
        return None
    rng = random.Random(config.terrain_seed + config.rows * 100 + config.cols)
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

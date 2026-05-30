from __future__ import annotations

from dataclasses import dataclass
import pygame

from algorithms import (
    generate_maze,
    solve_a_star,
    solve_bfs,
    solve_bidirectional_bfs,
    solve_dijkstra,
    solve_greedy_best_first,
    solve_weighted_a_star,
)


Color = tuple[int, int, int]


@dataclass
class AppConfig:
    rows: int = 31
    cols: int = 31
    cell_size: int = 20
    top_bar_height: int = 76
    default_step_ms: int = 80
    demo_step_ms: int = 120
    step_interval_ms: int = 80
    min_step_ms: int = 30
    max_step_ms: int = 240
    step_delta_ms: int = 10
    demo_reset_delay_ms: int = 1200
    loop_chance: float = 0.0
    maze_method: str = "dfs"
    weighted_a_star_w: float = 1.5
    weighted_step: float = 0.1
    min_weight: float = 1.0
    max_weight: float = 3.0


@dataclass
class AppState:
    grid: list[list[int]]
    start: tuple[int, int]
    goal: tuple[int, int]
    algorithm_name: str
    solver: object
    base_surface: pygame.Surface
    visited: set[tuple[int, int]]
    visit_index: dict[tuple[int, int], int]
    path: list[tuple[int, int]]
    current: tuple[int, int] | None
    demo_mode: bool
    step_hold: bool
    help_visible: bool
    was_paused: bool
    paused: bool
    finished: bool
    finished_time: int | None
    last_step_time: int


COLORS: dict[str, Color] = {
    "bg": (18, 20, 24),
    "panel": (28, 32, 38),
    "wall": (12, 13, 15),
    "path": (215, 215, 215),
    "visited_old": (140, 160, 185),
    "visited_new": (90, 120, 150),
    "route": (220, 185, 110),
    "current": (245, 155, 80),
    "start": (80, 185, 120),
    "goal": (205, 90, 90),
    "grid": (36, 38, 44),
    "button": (50, 58, 70),
    "button_hover": (70, 80, 96),
    "button_active": (88, 108, 138),
    "button_border": (95, 105, 120),
    "text": (225, 225, 225),
    "text_dim": (180, 185, 195),
}


def _load_font(size: int, bold: bool = False) -> pygame.font.Font:
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


def run_app() -> None:
    pygame.init()
    config = AppConfig()
    size_options = [
        ("Small", 21, 21, 20),
        ("Medium", 31, 31, 20),
        ("Large", 41, 41, 18),
    ]
    complexity_options = [
        ("Low", 0.0),
        ("Medium", 0.08),
        ("High", 0.18),
    ]
    maze_options = [
        ("生成迷宫(长廊型)", "dfs", None, None),
        ("生成迷宫(死胡同型)", "prim", None, None),
        ("Prim Dense", "prim", 0.18, "Dense"),
        ("Kruskal Sparse", "kruskal", 0.02, "Sparse"),
        ("生成迷宫(Kruskal)", "kruskal", None, None),
    ]
    size_index = 1
    maze_index = 0
    complexity_custom_label: str | None = None
    _apply_size_option(config, size_options[size_index])
    _apply_complexity_option(config, complexity_options[1])
    complexity_custom_label = _apply_maze_option(config, maze_options[maze_index])
    screen, menu_buttons, menu_background = _resize_window(config)
    algo_buttons = _build_algo_buttons(screen.get_width(), screen.get_height())
    font = _load_font(20)
    small_font = _load_font(16)
    title_font = _load_font(40, bold=True)
    clock = pygame.time.Clock()
    show_help = False

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
                    action = _handle_menu_click(event.pos, menu_buttons, show_help)
                    if action == "help":
                        show_help = True
                    elif action == "size":
                        size_index = (size_index + 1) % len(size_options)
                        _apply_size_option(config, size_options[size_index])
                        screen, menu_buttons, menu_background = _resize_window(config)
                        algo_buttons = _build_algo_buttons(screen.get_width(), screen.get_height())
                    elif action == "complexity":
                        complexity_custom_label = _cycle_complexity(
                            config,
                            complexity_options,
                            complexity_custom_label,
                        )
                    elif action == "maze":
                        maze_index = (maze_index + 1) % len(maze_options)
                        complexity_custom_label = _apply_maze_option(config, maze_options[maze_index])
                    elif action == "algo":
                        show_help = False
                        mode = "algo"
                    elif action == "start":
                        show_help = False
                        mode = "run"
                        app.demo_mode = False
                        config.step_interval_ms = config.default_step_ms
                        _reset_maze(config, app)
            elif mode == "algo":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    mode = "menu"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = _handle_menu_click(event.pos, algo_buttons, False)
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
            _draw(screen, font, small_font, config, app)
        elif mode == "algo":
            _draw_algo_menu(
                screen,
                title_font,
                font,
                small_font,
                menu_background,
                algo_buttons,
                app.algorithm_name,
                config.weighted_a_star_w,
            )
        else:
            complexity_label = _complexity_label(
                config.loop_chance,
                complexity_options,
                complexity_custom_label,
            )
            _draw_menu(
                screen,
                title_font,
                font,
                small_font,
                menu_buttons,
                menu_background,
                size_options[size_index][0],
                complexity_label,
                maze_options[maze_index][0],
                app.algorithm_name,
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
    solver = _make_solver(algorithm_name, grid, start, goal, config)
    base_surface = _build_base_surface(config, grid)
    return AppState(
        grid=grid,
        start=start,
        goal=goal,
        algorithm_name=algorithm_name,
        solver=solver,
        base_surface=base_surface,
        visited=set(),
        visit_index={},
        path=[],
        current=None,
        demo_mode=False,
        step_hold=False,
        help_visible=False,
        was_paused=False,
        paused=False,
        finished=False,
        finished_time=None,
        last_step_time=pygame.time.get_ticks(),
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
        _reset_maze(config, app)


def _reset_solver(config: AppConfig, app: AppState, algorithm_name: str) -> None:
    app.algorithm_name = algorithm_name
    app.solver = _make_solver(algorithm_name, app.grid, app.start, app.goal, config)
    app.visited = set()
    app.visit_index = {}
    app.path = []
    app.current = None
    app.step_hold = False
    app.help_visible = False
    app.was_paused = False
    app.paused = False
    app.finished = False
    app.finished_time = None
    app.last_step_time = pygame.time.get_ticks()


def _reset_maze(config: AppConfig, app: AppState) -> None:
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
    app.base_surface = _build_base_surface(config, app.grid)
    _convert_base_surface(app)
    _reset_solver(config, app, app.algorithm_name)


def _step_solver(app: AppState) -> None:
    try:
        state = next(app.solver) # type: ignore
        visited = state.get("visited", set())
        for point in visited:
            if point not in app.visit_index:
                app.visit_index[point] = len(app.visit_index)
        app.visited = visited
        path = state.get("path", [])
        if path:
            app.current = path[-1]
        if path and path[-1] == app.goal:
            app.path = path
    except StopIteration:
        app.finished = True
        app.paused = True
        app.finished_time = pygame.time.get_ticks()
        app.step_hold = False


def _draw(
    screen: pygame.Surface,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    config: AppConfig,
    app: AppState,
) -> None:
    screen.blit(app.base_surface, (0, 0))
    _draw_overlay(screen, config, app)
    _draw_hud(screen, font, small_font, config, app)
    if app.help_visible:
        _draw_help_panel(screen, font, small_font)


def _build_base_surface(config: AppConfig, grid: list[list[int]]) -> pygame.Surface:
    width = config.cols * config.cell_size
    height = config.rows * config.cell_size + config.top_bar_height
    surface = pygame.Surface((width, height))
    surface.fill(COLORS["bg"])

    top = config.top_bar_height
    for r in range(config.rows):
        for c in range(config.cols):
            color = COLORS["path"] if grid[r][c] == 1 else COLORS["wall"]
            rect = pygame.Rect(
                c * config.cell_size,
                top + r * config.cell_size,
                config.cell_size,
                config.cell_size,
            )
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, COLORS["grid"], rect, 1)

    return surface


def _draw_overlay(screen: pygame.Surface, config: AppConfig, app: AppState) -> None:
    top = config.top_bar_height
    width = config.cols * config.cell_size
    height = config.rows * config.cell_size + config.top_bar_height
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    total = max(1, len(app.visit_index))

    for (r, c), index in app.visit_index.items():
        if (r, c) in (app.start, app.goal):
            continue
        rect = pygame.Rect(
            c * config.cell_size,
            top + r * config.cell_size,
            config.cell_size,
            config.cell_size,
        )
        color = _lerp_color(COLORS["visited_old"], COLORS["visited_new"], index / total)
        pygame.draw.rect(overlay, (color[0], color[1], color[2], 120), rect)

    screen.blit(overlay, (0, 0))

    if app.current and app.current not in (app.start, app.goal):
        r, c = app.current
        rect = pygame.Rect(
            c * config.cell_size,
            top + r * config.cell_size,
            config.cell_size,
            config.cell_size,
        )
        radius = max(3, config.cell_size // 3)
        pygame.draw.circle(screen, COLORS["current"], rect.center, radius)

    for r, c in app.path:
        if (r, c) in (app.start, app.goal):
            continue
        rect = pygame.Rect(
            c * config.cell_size,
            top + r * config.cell_size,
            config.cell_size,
            config.cell_size,
        )
        pygame.draw.rect(screen, COLORS["route"], rect)

    for label, point in (("start", app.start), ("goal", app.goal)):
        r, c = point
        rect = pygame.Rect(
            c * config.cell_size,
            top + r * config.cell_size,
            config.cell_size,
            config.cell_size,
        )
        pygame.draw.rect(screen, COLORS[label], rect)


def _draw_hud(
    screen: pygame.Surface,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    config: AppConfig,
    app: AppState,
) -> None:
    width = config.cols * config.cell_size
    compact = width < 720
    pygame.draw.rect(screen, COLORS["panel"], pygame.Rect(0, 0, width, config.top_bar_height))
    status = "PAUSED" if app.paused else "RUNNING"
    if app.finished:
        status = "DONE"
    speed_text = f"Speed: {config.step_interval_ms}ms"
    weight_text = f"W: {config.weighted_a_star_w:.1f}" if app.algorithm_name == "Weighted A*" else ""
    status_text = f"Algo: {app.algorithm_name} | {status} | {speed_text} {weight_text}".strip()
    if compact:
        controls_text = "Space: Pause  H: Help  N: Step  +/-: Speed  R: Restart  M: New Maze"
    else:
        controls_text = "Space: Pause  H: Help  N: Step (hold)  +/-: Speed  R: Restart  M: New Maze"
    status_surface = font.render(status_text, True, COLORS["text"])
    controls_surface = small_font.render(controls_text, True, COLORS["text_dim"])
    screen.blit(status_surface, (10, 6))
    screen.blit(controls_surface, (10, 28))
    if compact:
        if width >= 520:
            _draw_demo_legend(screen, small_font, config)
    else:
        _draw_legend(screen, small_font, config)


def _draw_legend(screen: pygame.Surface, font: pygame.font.Font, config: AppConfig) -> None:
    items = [
        ("Wall", COLORS["wall"]),
        ("Path", COLORS["path"]),
        ("Visited", COLORS["visited_new"]),
        ("Current", COLORS["current"]),
        ("Route", COLORS["route"]),
        ("Start", COLORS["start"]),
        ("Goal", COLORS["goal"]),
    ]
    x = 10
    y = 50
    box = 10
    gap = 8
    for label, color in items:
        rect = pygame.Rect(x, y, box, box)
        pygame.draw.rect(screen, color, rect)
        text_surface = font.render(label, True, COLORS["text_dim"])
        screen.blit(text_surface, (x + box + 6, y - 2))
        x += box + 6 + text_surface.get_width() + gap


def _draw_demo_legend(screen: pygame.Surface, font: pygame.font.Font, config: AppConfig) -> None:
    items = [
        ("S", COLORS["start"]),
        ("G", COLORS["goal"]),
        ("C", COLORS["current"]),
        ("V", COLORS["visited_new"]),
        ("R", COLORS["route"]),
    ]
    width = config.cols * config.cell_size
    x = width - 10
    y = 8
    size = 10
    for label, color in reversed(items):
        x -= size
        rect = pygame.Rect(x, y, size, size)
        pygame.draw.rect(screen, color, rect)
        label_surface = font.render(label, True, COLORS["text_dim"])
        x -= label_surface.get_width() + 4
        screen.blit(label_surface, (x, y - 2))
        x -= 10


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


def _lerp_color(a: Color, b: Color, t: float) -> Color:
    clamped = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * clamped),
        int(a[1] + (b[1] - a[1]) * clamped),
        int(a[2] + (b[2] - a[2]) * clamped),
    )


def _make_solver(
    algorithm_name: str,
    grid: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
    config: AppConfig,
) -> object:
    if algorithm_name == "BFS":
        return solve_bfs(grid, start, goal)
    if algorithm_name == "Dijkstra":
        return solve_dijkstra(grid, start, goal)
    if algorithm_name == "A*":
        return solve_a_star(grid, start, goal)
    if algorithm_name == "Bi-BFS":
        return solve_bidirectional_bfs(grid, start, goal)
    if algorithm_name == "Greedy":
        return solve_greedy_best_first(grid, start, goal)
    if algorithm_name == "Weighted A*":
        return solve_weighted_a_star(grid, start, goal, weight=config.weighted_a_star_w)
    raise ValueError(f"unknown algorithm: {algorithm_name}")


def _build_menu_buttons(width: int, height: int) -> list[tuple[str, str, pygame.Rect]]:
    button_w = min(320, width - 40)
    button_h = 38
    gap = 10
    total_h = button_h * 6 + gap * 5
    start_y = max(140, height // 2 - total_h // 2 + 10)
    x = width // 2 - button_w // 2
    labels = [
        ("Size", "size"),
        ("Complexity", "complexity"),
        ("Maze", "maze"),
        ("Algo", "algo"),
        ("Start", "start"),
        ("Help", "help"),
    ]
    buttons: list[tuple[str, str, pygame.Rect]] = []
    for idx, (label, action) in enumerate(labels):
        y = start_y + idx * (button_h + gap)
        buttons.append((label, action, pygame.Rect(x, y, button_w, button_h)))
    return buttons


def _handle_menu_click(
    pos: tuple[int, int],
    buttons: list[tuple[str, str, pygame.Rect]],
    show_help: bool,
) -> str | None:
    if show_help:
        return None
    for _, action, rect in buttons:
        if rect.collidepoint(pos):
            return action
    return None


def _draw_menu(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    buttons: list[tuple[str, str, pygame.Rect]],
    background: pygame.Surface,
    size_label: str,
    complexity_label: str,
    maze_label: str,
    algo_label: str,
    show_help: bool,
) -> None:
    screen.blit(background, (0, 0))
    width, height = screen.get_size()
    title = title_font.render("MazeVisualizer", True, COLORS["text"])
    subtitle = font.render("Maze generation and pathfinding visualization", True, COLORS["text_dim"])
    screen.blit(title, (width // 2 - title.get_width() // 2, 60))
    screen.blit(subtitle, (width // 2 - subtitle.get_width() // 2, 104))

    mouse_pos = pygame.mouse.get_pos()
    for label, action, rect in buttons:
        if action == "size":
            label = f"Size: {size_label}"
        elif action == "complexity":
            label = f"Complexity: {complexity_label}"
        elif action == "maze":
            label = f"{maze_label}"
        elif action == "algo":
            label = f"Algo: {algo_label}"
        color = COLORS["button_hover"] if rect.collidepoint(mouse_pos) else COLORS["button"]
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, COLORS["button_border"], rect, 2, border_radius=8)
        text_surface = font.render(label, True, COLORS["text"])
        screen.blit(
            text_surface,
            (rect.centerx - text_surface.get_width() // 2, rect.centery - text_surface.get_height() // 2),
        )

    footer = small_font.render("ESC closes help. Close window to quit.", True, COLORS["text_dim"])
    screen.blit(footer, (width // 2 - footer.get_width() // 2, height - 32))

    if show_help:
        _draw_help_panel(screen, font, small_font)


def _build_menu_background(width: int, height: int) -> pygame.Surface:
    surface = pygame.Surface((width, height))
    surface.fill(COLORS["bg"])

    pattern = pygame.Surface((width, height), pygame.SRCALPHA)
    for x in range(-height, width, 60):
        pygame.draw.line(pattern, (70, 80, 95, 40), (x, 0), (x + height, height), 2)

    center = (width - 120, 140)
    for radius in range(40, 140, 18):
        pygame.draw.circle(pattern, (90, 105, 125, 35), center, radius, 1)

    for i in range(6):
        rect = pygame.Rect(60 + i * 26, height - 130, 14, 14)
        pygame.draw.rect(pattern, (80, 90, 110, 50), rect)

    surface.blit(pattern, (0, 0))
    return surface


def _draw_help_panel(
    screen: pygame.Surface,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
) -> None:
    width, height = screen.get_size()
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    lines = [
        "Space: pause/resume",
        "H: help panel (pause)",
        "N: single step (hold for continuous)",
        "+/-: speed up / slow down",
        "R: restart solver (same maze)",
        "1-3: BFS / Dijkstra / A*",
        "4-6: Bi-BFS / Greedy / Weighted A*",
        "[/]: adjust Weighted A* W",
        "M: generate new maze",
        "ESC: close help / back to menu",
    ]
    line_height = small_font.get_linesize() + 6
    content_height = line_height * len(lines)
    panel_w = min(width - 40, 660)
    panel_h = min(height - 40, content_height + 80)
    panel = pygame.Rect(
        width // 2 - panel_w // 2,
        height // 2 - panel_h // 2,
        panel_w,
        panel_h,
    )
    pygame.draw.rect(screen, COLORS["panel"], panel, border_radius=10)
    pygame.draw.rect(screen, COLORS["button_border"], panel, 2, border_radius=10)

    title = font.render("Help", True, COLORS["text"])
    screen.blit(title, (panel.x + 20, panel.y + 18))
    y = panel.y + 60
    for line in lines:
        text_surface = small_font.render(line, True, COLORS["text_dim"])
        screen.blit(text_surface, (panel.x + 22, y))
        y += line_height


def _apply_size_option(config: AppConfig, option: tuple[str, int, int, int]) -> None:
    _, rows, cols, cell_size = option
    config.rows = rows
    config.cols = cols
    config.cell_size = cell_size


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
    width = config.cols * config.cell_size
    height = config.rows * config.cell_size + config.top_bar_height
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("MazeVisualizer")
    menu_buttons = _build_menu_buttons(width, height)
    menu_background = _build_menu_background(width, height)
    return screen, menu_buttons, menu_background


def _build_algo_buttons(width: int, height: int) -> list[tuple[str, str, pygame.Rect]]:
    button_w = min(240, (width - 80) // 2)
    button_h = 42
    gap = 16
    total_h = button_h * 3 + gap * 2
    start_y = height // 2 - total_h // 2 + 10
    left_x = width // 2 - button_w - gap // 2
    right_x = width // 2 + gap // 2

    labels = [
        ("BFS", "BFS"),
        ("Dijkstra", "Dijkstra"),
        ("A*", "A*"),
        ("Bi-BFS", "Bi-BFS"),
        ("Greedy", "Greedy"),
        ("Weighted A*", "Weighted A*"),
    ]

    buttons: list[tuple[str, str, pygame.Rect]] = []
    for idx, (label, action) in enumerate(labels):
        col_x = left_x if idx < 3 else right_x
        row = idx if idx < 3 else idx - 3
        y = start_y + row * (button_h + gap)
        buttons.append((label, action, pygame.Rect(col_x, y, button_w, button_h)))

    back_w = 140
    back_h = 36
    back_y = height - 76
    buttons.append(("Back", "back", pygame.Rect(width // 2 - back_w // 2, back_y, back_w, back_h)))

    w_button_w = 70
    w_button_h = 34
    w_y = back_y - 70
    buttons.append(("W -", "w_minus", pygame.Rect(width // 2 - 120, w_y, w_button_w, w_button_h)))
    buttons.append(("W +", "w_plus", pygame.Rect(width // 2 + 50, w_y, w_button_w, w_button_h)))
    return buttons


def _draw_algo_menu(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    background: pygame.Surface,
    buttons: list[tuple[str, str, pygame.Rect]],
    selected_algo: str,
    weight: float,
) -> None:
    screen.blit(background, (0, 0))
    width, _ = screen.get_size()
    title = title_font.render("Algorithm / 算法选择", True, COLORS["text"])
    subtitle = small_font.render("Choose solver and adjust W for Weighted A*.", True, COLORS["text_dim"])
    screen.blit(title, (width // 2 - title.get_width() // 2, 60))
    screen.blit(subtitle, (width // 2 - subtitle.get_width() // 2, 108))

    mouse_pos = pygame.mouse.get_pos()
    for label, action, rect in buttons:
        is_selected = action == selected_algo
        color = COLORS["button_active"] if is_selected else COLORS["button"]
        if rect.collidepoint(mouse_pos):
            color = COLORS["button_hover"]
        pygame.draw.rect(screen, color, rect, border_radius=8)
        pygame.draw.rect(screen, COLORS["button_border"], rect, 2, border_radius=8)
        text_surface = font.render(label, True, COLORS["text"])
        screen.blit(
            text_surface,
            (rect.centerx - text_surface.get_width() // 2, rect.centery - text_surface.get_height() // 2),
        )

    weight_text = small_font.render(f"W = {weight:.1f}", True, COLORS["text_dim"])
    weight_y = buttons[-2][2].y - 24
    screen.blit(weight_text, (width // 2 - weight_text.get_width() // 2, weight_y))


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


if __name__ == "__main__":
    run_app()

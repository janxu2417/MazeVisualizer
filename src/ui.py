from __future__ import annotations

from dataclasses import dataclass
import pygame

from algorithms import generate_maze, solve_a_star, solve_bfs, solve_dijkstra


Color = tuple[int, int, int]


@dataclass
class AppConfig:
    rows: int = 31
    cols: int = 31
    cell_size: int = 20
    top_bar_height: int = 28
    step_interval_ms: int = 80


@dataclass
class AppState:
    grid: list[list[int]]
    start: tuple[int, int]
    goal: tuple[int, int]
    algorithm_name: str
    solver: object
    base_surface: pygame.Surface
    visited: set[tuple[int, int]]
    path: list[tuple[int, int]]
    current: tuple[int, int] | None
    paused: bool
    finished: bool
    last_step_time: int


COLORS: dict[str, Color] = {
    "bg": (20, 20, 20),
    "wall": (10, 10, 10),
    "path": (230, 230, 230),
    "visited": (160, 190, 220),
    "route": (245, 215, 110),
    "current": (255, 170, 80),
    "start": (80, 200, 120),
    "goal": (220, 90, 90),
    "grid": (40, 40, 40),
    "text": (230, 230, 230),
}


def run_app() -> None:
    pygame.init()
    config = AppConfig()
    app = _create_state(config, "BFS")

    width = config.cols * config.cell_size
    height = config.rows * config.cell_size + config.top_bar_height
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("MazeVisualizer")
    _convert_base_surface(app)

    font = pygame.font.SysFont(None, 20)
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if event.type == pygame.KEYDOWN:
                _handle_keydown(event.key, config, app)

        now = pygame.time.get_ticks()
        if not app.paused and not app.finished:
            if now - app.last_step_time >= config.step_interval_ms:
                _step_solver(app)
                app.last_step_time = now

        _draw(screen, font, config, app)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def _create_state(config: AppConfig, algorithm_name: str) -> AppState:
    grid = generate_maze(config.rows, config.cols)
    start = (1, 1)
    goal = (config.rows - 2, config.cols - 2)
    grid[start[0]][start[1]] = 1
    grid[goal[0]][goal[1]] = 1
    solver = _make_solver(algorithm_name, grid, start, goal)
    base_surface = _build_base_surface(config, grid)
    return AppState(
        grid=grid,
        start=start,
        goal=goal,
        algorithm_name=algorithm_name,
        solver=solver,
        base_surface=base_surface,
        visited=set(),
        path=[],
        current=None,
        paused=False,
        finished=False,
        last_step_time=pygame.time.get_ticks(),
    )


def _handle_keydown(key: int, config: AppConfig, app: AppState) -> None:
    if key == pygame.K_SPACE:
        app.paused = not app.paused
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

    if key == pygame.K_m:
        _reset_maze(config, app)


def _reset_solver(config: AppConfig, app: AppState, algorithm_name: str) -> None:
    app.algorithm_name = algorithm_name
    app.solver = _make_solver(algorithm_name, app.grid, app.start, app.goal)
    app.visited = set()
    app.path = []
    app.current = None
    app.paused = False
    app.finished = False
    app.last_step_time = pygame.time.get_ticks()


def _reset_maze(config: AppConfig, app: AppState) -> None:
    app.grid = generate_maze(config.rows, config.cols)
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
        app.visited = state.get("visited", set())
        path = state.get("path", [])
        if path:
            app.current = path[-1]
        if path and path[-1] == app.goal:
            app.path = path
    except StopIteration:
        app.finished = True
        app.paused = True


def _draw(screen: pygame.Surface, font: pygame.font.Font, config: AppConfig, app: AppState) -> None:
    screen.blit(app.base_surface, (0, 0))
    _draw_overlay(screen, config, app)
    _draw_hud(screen, font, config, app)


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
    for r, c in app.visited:
        if (r, c) in (app.start, app.goal):
            continue
        rect = pygame.Rect(
            c * config.cell_size,
            top + r * config.cell_size,
            config.cell_size,
            config.cell_size,
        )
        pygame.draw.rect(screen, COLORS["visited"], rect)

    if app.current and app.current not in (app.start, app.goal):
        r, c = app.current
        rect = pygame.Rect(
            c * config.cell_size,
            top + r * config.cell_size,
            config.cell_size,
            config.cell_size,
        )
        pygame.draw.rect(screen, COLORS["current"], rect)

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


def _draw_hud(screen: pygame.Surface, font: pygame.font.Font, config: AppConfig, app: AppState) -> None:
    status = "PAUSED" if app.paused else "RUNNING"
    if app.finished:
        status = "DONE"
    text = (
        f"Algo: {app.algorithm_name} | {status} | "
        "Space: Pause  R: Restart  1/2/3: BFS/Dijkstra/A*  M: New Maze"
    )
    surface = font.render(text, True, COLORS["text"])
    screen.blit(surface, (8, 6))


def _convert_base_surface(app: AppState) -> None:
    if pygame.display.get_surface() is not None:
        app.base_surface = app.base_surface.convert()


def _make_solver(
    algorithm_name: str,
    grid: list[list[int]],
    start: tuple[int, int],
    goal: tuple[int, int],
) -> object:
    solver_factory = {
        "BFS": solve_bfs,
        "Dijkstra": solve_dijkstra,
        "A*": solve_a_star,
    }[algorithm_name]
    return solver_factory(grid, start, goal)


if __name__ == "__main__":
    run_app()

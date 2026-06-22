from __future__ import annotations

from dataclasses import dataclass, fields

Color = tuple[int, int, int]


@dataclass(frozen=True)
class Theme:
    name: str
    bg: Color
    panel: Color
    panel_alt: Color
    wall: Color
    path: Color
    terrain_light: Color
    terrain_mid: Color
    terrain_heavy: Color
    search_visited: Color
    search_frontier: Color
    search_current: Color
    route: Color
    start: Color
    goal: Color
    grid: Color
    button: Color
    button_hover: Color
    button_active: Color
    button_border: Color
    text: Color
    text_dim: Color
    status_running: Color
    status_paused: Color
    status_done: Color
    edit_cursor: Color
    edit_wall_preview: Color
    edit_start_preview: Color
    edit_goal_preview: Color
    edit_terrain_preview: Color

    def to_dict(self) -> dict[str, Color]:
        return {field.name: getattr(self, field.name) for field in fields(self) if field.name != "name"}


PRESET_THEMES: dict[str, Theme] = {
    "dark": Theme(
        name="dark",
        bg=(18, 20, 24),
        panel=(28, 32, 38),
        panel_alt=(34, 39, 47),
        wall=(12, 13, 15),
        path=(215, 215, 215),
        terrain_light=(216, 225, 221),
        terrain_mid=(173, 188, 181),
        terrain_heavy=(122, 140, 132),
        search_visited=(103, 142, 197),
        search_frontier=(244, 191, 117),
        search_current=(240, 111, 92),
        route=(220, 185, 110),
        start=(80, 185, 120),
        goal=(205, 90, 90),
        grid=(36, 38, 44),
        button=(50, 58, 70),
        button_hover=(70, 80, 96),
        button_active=(88, 108, 138),
        button_border=(95, 105, 120),
        text=(225, 225, 225),
        text_dim=(180, 185, 195),
        status_running=(68, 194, 124),
        status_paused=(244, 191, 117),
        status_done=(240, 111, 92),
        edit_cursor=(255, 255, 255),
        edit_wall_preview=(242, 105, 92),
        edit_start_preview=(80, 185, 120),
        edit_goal_preview=(205, 90, 90),
        edit_terrain_preview=(244, 191, 117),
    ),
    "ocean": Theme(
        name="ocean",
        bg=(9, 24, 38),
        panel=(15, 43, 62),
        panel_alt=(22, 58, 80),
        wall=(5, 14, 24),
        path=(207, 234, 238),
        terrain_light=(200, 235, 230),
        terrain_mid=(137, 202, 205),
        terrain_heavy=(72, 148, 164),
        search_visited=(73, 178, 210),
        search_frontier=(255, 201, 112),
        search_current=(255, 111, 97),
        route=(255, 224, 122),
        start=(82, 210, 156),
        goal=(255, 96, 108),
        grid=(38, 79, 98),
        button=(27, 77, 103),
        button_hover=(39, 106, 137),
        button_active=(49, 129, 160),
        button_border=(91, 155, 178),
        text=(228, 247, 250),
        text_dim=(166, 207, 218),
        status_running=(78, 216, 169),
        status_paused=(255, 201, 112),
        status_done=(255, 111, 97),
        edit_cursor=(232, 250, 255),
        edit_wall_preview=(255, 111, 97),
        edit_start_preview=(82, 210, 156),
        edit_goal_preview=(255, 96, 108),
        edit_terrain_preview=(255, 201, 112),
    ),
    "forest": Theme(
        name="forest",
        bg=(18, 30, 22),
        panel=(30, 48, 36),
        panel_alt=(38, 61, 46),
        wall=(12, 22, 15),
        path=(221, 229, 204),
        terrain_light=(213, 226, 198),
        terrain_mid=(164, 190, 139),
        terrain_heavy=(105, 139, 93),
        search_visited=(105, 162, 125),
        search_frontier=(230, 177, 93),
        search_current=(210, 91, 78),
        route=(245, 214, 114),
        start=(73, 177, 101),
        goal=(201, 82, 76),
        grid=(47, 68, 51),
        button=(51, 76, 58),
        button_hover=(70, 99, 76),
        button_active=(85, 122, 90),
        button_border=(109, 134, 111),
        text=(230, 237, 220),
        text_dim=(184, 199, 177),
        status_running=(77, 191, 110),
        status_paused=(230, 177, 93),
        status_done=(210, 91, 78),
        edit_cursor=(246, 255, 238),
        edit_wall_preview=(210, 91, 78),
        edit_start_preview=(73, 177, 101),
        edit_goal_preview=(201, 82, 76),
        edit_terrain_preview=(230, 177, 93),
    ),
    "sunset": Theme(
        name="sunset",
        bg=(34, 22, 31),
        panel=(55, 34, 49),
        panel_alt=(73, 43, 59),
        wall=(22, 12, 18),
        path=(246, 224, 194),
        terrain_light=(247, 222, 190),
        terrain_mid=(232, 174, 134),
        terrain_heavy=(184, 116, 103),
        search_visited=(120, 143, 214),
        search_frontier=(255, 185, 97),
        search_current=(241, 91, 103),
        route=(255, 221, 117),
        start=(82, 190, 137),
        goal=(222, 78, 98),
        grid=(91, 55, 68),
        button=(84, 50, 67),
        button_hover=(113, 67, 79),
        button_active=(137, 77, 90),
        button_border=(166, 111, 119),
        text=(255, 239, 218),
        text_dim=(224, 190, 180),
        status_running=(82, 190, 137),
        status_paused=(255, 185, 97),
        status_done=(241, 91, 103),
        edit_cursor=(255, 244, 225),
        edit_wall_preview=(241, 91, 103),
        edit_start_preview=(82, 190, 137),
        edit_goal_preview=(222, 78, 98),
        edit_terrain_preview=(255, 185, 97),
    ),
}


def theme_names() -> list[str]:
    return list(PRESET_THEMES.keys())

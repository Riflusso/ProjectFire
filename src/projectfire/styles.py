def hex_to_rgb_float(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return (
        int(h[0:2], 16) / 255.0,
        int(h[2:4], 16) / 255.0,
        int(h[4:6], 16) / 255.0,
    )


def hex_to_rgba_int(hex_color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    h = hex_color.lstrip("#")
    return (
        int(h[0:2], 16),
        int(h[2:4], 16),
        int(h[4:6], 16),
        alpha,
    )


CATPPUCCIN_MOCHA = {
    "base": "#1e1e2e",
    "surface0": "#313244",
    "green": "#a6e3a1",
    "blue": "#89b4fa",
    "mauve": "#cba6f7",
    "peach": "#fab387",
    "text": "#cdd6f4",
}

BG_COLOR = hex_to_rgb_float(CATPPUCCIN_MOCHA["base"])
GRID_COLOR = hex_to_rgb_float(CATPPUCCIN_MOCHA["surface0"])
GROUND_COLOR = hex_to_rgb_float(CATPPUCCIN_MOCHA["green"])
CANNON_COLOR = hex_to_rgb_float(CATPPUCCIN_MOCHA["blue"])
TRAIL_COLOR = hex_to_rgb_float(CATPPUCCIN_MOCHA["mauve"])
BALL_COLOR = hex_to_rgb_float(CATPPUCCIN_MOCHA["peach"])
TEXT_COLOR_RGBA = hex_to_rgba_int(CATPPUCCIN_MOCHA["text"])

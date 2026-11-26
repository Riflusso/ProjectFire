import math

from OpenGL import GL

from .camera import setup_screen_ortho, setup_world_ortho
from .styles import BALL_COLOR, BG_COLOR, CANNON_COLOR, GROUND_COLOR, TRAIL_COLOR
from .ui import draw_label


def draw_circle(cx: float, cy: float, radius: float, segments: int = 24) -> None:
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glVertex2f(cx, cy)
    for i in range(segments + 1):
        theta = 2.0 * math.pi * i / segments
        GL.glVertex2f(cx + radius * math.cos(theta), cy + radius * math.sin(theta))
    GL.glEnd()


def draw_ground(cam_x: float, width: int, zoom: float, ground_y: float) -> None:
    GL.glColor3f(*GROUND_COLOR)
    GL.glLineWidth(3.0)
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2f(cam_x - 200.0, ground_y)
    GL.glVertex2f(cam_x + width / zoom + 200.0, ground_y)
    GL.glEnd()


def draw_cannon(x: float, y: float, angle_deg: float, zoom: float) -> None:
    inv_zoom = max(1.0, 0.7 / zoom)
    angle_rad = math.radians(angle_deg)
    end_x = x + 36.0 * inv_zoom * math.cos(angle_rad)
    end_y = y + 36.0 * inv_zoom * math.sin(angle_rad)

    GL.glColor3f(*CANNON_COLOR)
    GL.glLineWidth(min(10.0, 8.0 * inv_zoom))
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2f(x, y)
    GL.glVertex2f(end_x, end_y)
    GL.glEnd()

    draw_circle(x, y, 10.0 * inv_zoom)


def draw_trail(trail: list[tuple[float, float]]) -> None:
    if len(trail) < 2:
        return

    GL.glColor4f(*TRAIL_COLOR, 0.75)
    GL.glLineWidth(2.0)
    GL.glBegin(GL.GL_LINE_STRIP)
    for px, py in trail:
        GL.glVertex2f(px, py)
    GL.glEnd()


def render_scene(
    width: int,
    height: int,
    ground_y: float,
    start_x: float,
    has_projectile: bool,
    proj_x: float,
    proj_y: float,
    flight_time: float,
    trail: list[tuple[float, float]],
    state: str,
    input_buf: str,
    velocity: float,
    angle: float,
    cam_x: float,
    cam_y: float,
    zoom: float,
    auto_follow: bool,
) -> None:
    GL.glClearColor(*BG_COLOR, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    setup_world_ortho(width, height, cam_x, cam_y, zoom)
    draw_ground(cam_x, width, zoom, ground_y)

    if has_projectile:
        draw_trail(trail)

    draw_cannon(start_x, ground_y, angle, zoom)

    if has_projectile:
        GL.glColor3f(*BALL_COLOR)
        draw_circle(proj_x, proj_y, max(7.0, 6.0 / zoom))

        setup_screen_ortho(width, height)
    top_y = float(height) - 20.0
    follow_status = "ВКЛ" if auto_follow else "ВЫКЛ"

    time_info = f"  |  Время: {flight_time:.2f} с" if has_projectile else ""

    if state == "INPUT_V":
        draw_label(f"Введите скорость V (м/с): {input_buf}_{time_info}", 24.0, top_y)
    elif state == "INPUT_ANGLE":
        draw_label(f"V = {velocity} м/с | Введите угол α (0–90°): {input_buf}_{time_info}", 24.0, top_y)
    else:
        draw_label(f"V = {velocity} м/с  |  Угол α = {angle}°{time_info}", 24.0, top_y)

    draw_label(f"[ЛКМ] Двигать сцену  |  [F] Автослежение: {follow_status} (масштаб {zoom:.2f}x)", 24.0, top_y - 34.0, font_size=18)


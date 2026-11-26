import ctypes
import math
import time

import sdl3
from OpenGL import GL

from .physics import Projectile
from .ui import cleanup_ui, draw_label

# Палитра Catppuccin Mocha
BG_COLOR = (30 / 255, 30 / 255, 46 / 255)        # Base
GROUND_COLOR = (166 / 255, 227 / 255, 161 / 255) # Green
CANNON_COLOR = (137 / 255, 180 / 255, 250 / 255) # Blue
TRAIL_COLOR = (203 / 255, 166 / 255, 247 / 255)  # Mauve
BALL_COLOR = (250 / 255, 179 / 255, 135 / 255)   # Peach


def init_window(title: bytes, width: int, height: int):
    if not sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO):
        raise RuntimeError(f"SDL_Init failed: {sdl3.SDL_GetError().decode()}")

    sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MAJOR_VERSION, 2)
    sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MINOR_VERSION, 1)
    sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_DOUBLEBUFFER, 1)

    window = sdl3.SDL_CreateWindow(
        title, width, height, sdl3.SDL_WINDOW_OPENGL | sdl3.SDL_WINDOW_RESIZABLE
    )
    if not window:
        sdl3.SDL_Quit()
        raise RuntimeError(f"SDL_CreateWindow failed: {sdl3.SDL_GetError().decode()}")

    gl_context = sdl3.SDL_GL_CreateContext(window)
    if not gl_context:
        sdl3.SDL_DestroyWindow(window)
        sdl3.SDL_Quit()
        raise RuntimeError(f"SDL_GL_CreateContext failed: {sdl3.SDL_GetError().decode()}")

    sdl3.SDL_GL_MakeCurrent(window, gl_context)
    sdl3.SDL_GL_SetSwapInterval(1)

    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glEnable(GL.GL_LINE_SMOOTH)

    return window, gl_context


def setup_ortho(width: int, height: int) -> None:
    GL.glViewport(0, 0, width, height)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(0, width, 0, height, -1, 1)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def scancode_to_char(scancode: int) -> str | None:
    """Преобразует физический скан-код цифр и точки в символ независимо от раскладки."""
    digits = {
        sdl3.SDL_SCANCODE_0: "0", sdl3.SDL_SCANCODE_KP_0: "0",
        sdl3.SDL_SCANCODE_1: "1", sdl3.SDL_SCANCODE_KP_1: "1",
        sdl3.SDL_SCANCODE_2: "2", sdl3.SDL_SCANCODE_KP_2: "2",
        sdl3.SDL_SCANCODE_3: "3", sdl3.SDL_SCANCODE_KP_3: "3",
        sdl3.SDL_SCANCODE_4: "4", sdl3.SDL_SCANCODE_KP_4: "4",
        sdl3.SDL_SCANCODE_5: "5", sdl3.SDL_SCANCODE_KP_5: "5",
        sdl3.SDL_SCANCODE_6: "6", sdl3.SDL_SCANCODE_KP_6: "6",
        sdl3.SDL_SCANCODE_7: "7", sdl3.SDL_SCANCODE_KP_7: "7",
        sdl3.SDL_SCANCODE_8: "8", sdl3.SDL_SCANCODE_KP_8: "8",
        sdl3.SDL_SCANCODE_9: "9", sdl3.SDL_SCANCODE_KP_9: "9",
        sdl3.SDL_SCANCODE_PERIOD: ".", sdl3.SDL_SCANCODE_KP_PERIOD: ".",
        sdl3.SDL_SCANCODE_COMMA: ".",
    }
    return digits.get(scancode)


def handle_events(
    state: str, input_buf: str, velocity: float, angle: float, start_x: float, ground_y: float
) -> tuple[bool, str, str, float, float, Projectile | None]:
    event = sdl3.SDL_Event()
    new_projectile = None

    while sdl3.SDL_PollEvent(ctypes.byref(event)):
        if event.type == sdl3.SDL_EVENT_QUIT:
            return False, state, input_buf, velocity, angle, None

        if event.type == sdl3.SDL_EVENT_KEY_DOWN:
            scancode = event.key.scancode

            if scancode == sdl3.SDL_SCANCODE_ESCAPE:
                return False, state, input_buf, velocity, angle, None

            if state in ("INPUT_V", "INPUT_ANGLE"):
                ch = scancode_to_char(scancode)
                if ch is not None:
                    if ch == "." and "." in input_buf:
                        continue
                    if len(input_buf) < 7:
                        input_buf += ch

                elif scancode == sdl3.SDL_SCANCODE_BACKSPACE:
                    input_buf = input_buf[:-1]

                elif scancode in (sdl3.SDL_SCANCODE_RETURN, sdl3.SDL_SCANCODE_KP_ENTER):
                    try:
                        val = float(input_buf) if input_buf else 0.0
                    except ValueError:
                        val = 0.0

                    if state == "INPUT_V" and val > 0:
                        velocity = val
                        input_buf = ""
                        state = "INPUT_ANGLE"
                    elif state == "INPUT_ANGLE" and 0 <= val <= 90:
                        angle = val
                        input_buf = ""
                        state = "FLYING"
                        new_projectile = Projectile(start_x, ground_y, velocity, angle)

    return True, state, input_buf, velocity, angle, new_projectile


def draw_circle(cx: float, cy: float, radius: float, segments: int = 24) -> None:
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glVertex2f(cx, cy)
    for i in range(segments + 1):
        theta = 2.0 * math.pi * i / segments
        GL.glVertex2f(cx + radius * math.cos(theta), cy + radius * math.sin(theta))
    GL.glEnd()


def draw_ground(width: int, ground_y: float) -> None:
    GL.glColor3f(*GROUND_COLOR)
    GL.glLineWidth(3.0)
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2f(0.0, ground_y)
    GL.glVertex2f(float(width), ground_y)
    GL.glEnd()


def draw_cannon(x: float, y: float, angle_deg: float) -> None:
    angle_rad = math.radians(angle_deg)
    end_x = x + 36.0 * math.cos(angle_rad)
    end_y = y + 36.0 * math.sin(angle_rad)

    GL.glColor3f(*CANNON_COLOR)
    GL.glLineWidth(8.0)
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2f(x, y)
    GL.glVertex2f(end_x, end_y)
    GL.glEnd()

    draw_circle(x, y, 10.0)


def draw_trail(trail: list[tuple[float, float]]) -> None:
    if len(trail) < 2:
        return

    GL.glColor4f(*TRAIL_COLOR, 0.75)
    GL.glLineWidth(2.0)
    GL.glBegin(GL.GL_LINE_STRIP)
    for px, py in trail:
        GL.glVertex2f(px, py)
    GL.glEnd()


def render(
    width: int,
    height: int,
    ground_y: float,
    start_x: float,
    projectile: Projectile | None,
    state: str,
    input_buf: str,
    velocity: float,
    angle: float,
) -> None:
    setup_ortho(width, height)

    GL.glClearColor(*BG_COLOR, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    draw_ground(width, ground_y)

    if projectile is not None:
        draw_trail(projectile.trail)

    current_angle = projectile.angle_deg if projectile is not None else angle
    draw_cannon(start_x, ground_y, current_angle)

    if projectile is not None:
        GL.glColor3f(*BALL_COLOR)
        draw_circle(projectile.x, projectile.y, 7.0)

    top_y = float(height) - 24.0
    if state == "INPUT_V":
        draw_label(f"Введите скорость V (м/с): {input_buf}_", 24.0, top_y)
    elif state == "INPUT_ANGLE":
        draw_label(f"V = {velocity} м/с | Введите угол α (0–90°): {input_buf}_", 24.0, top_y)
    else:
        draw_label(f"V = {velocity} м/с  |  Угол α = {angle}°  |  Время: {projectile.time:.2f} с", 24.0, top_y)


def cleanup(window, gl_context) -> None:
    cleanup_ui()
    sdl3.SDL_GL_DestroyContext(gl_context)
    sdl3.SDL_DestroyWindow(window)
    sdl3.SDL_Quit()


def main() -> None:
    width, height = 1000, 600
    window, gl_context = init_window(b"ProjectFire - Projectile Motion", width, height)

    ground_y = 60.0
    start_x = 80.0

    state = "INPUT_V"
    input_buf = ""
    velocity = 0.0
    angle = 45.0
    projectile: Projectile | None = None

    w_ptr = ctypes.c_int(width)
    h_ptr = ctypes.c_int(height)
    last_time = time.perf_counter()

    running = True
    while running:
        now = time.perf_counter()
        dt = min(now - last_time, 0.05)
        last_time = now

        running, state, input_buf, velocity, angle, new_proj = handle_events(
            state, input_buf, velocity, angle, start_x, ground_y
        )
        if new_proj is not None:
            projectile = new_proj

        if state == "FLYING" and projectile is not None:
            projectile.update(dt, ground_y)
            if not projectile.is_flying:
                state = "INPUT_V"
                input_buf = ""

        sdl3.SDL_GetWindowSizeInPixels(window, ctypes.byref(w_ptr), ctypes.byref(h_ptr))
        render(w_ptr.value, h_ptr.value, ground_y, start_x, projectile, state, input_buf, velocity, angle)

        sdl3.SDL_GL_SwapWindow(window)

    cleanup(window, gl_context)


if __name__ == "__main__":
    main()

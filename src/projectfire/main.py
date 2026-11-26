import ctypes
import math
import time

import sdl3
from OpenGL import GL

from .physics import Projectile

# Палитра Catppuccin Mocha
BG_COLOR = (30 / 255, 30 / 255, 46 / 255)        # #1e1e2e — фон
GROUND_COLOR = (166 / 255, 227 / 255, 161 / 255) # #a6e3a1 — земля (Green)
CANNON_COLOR = (137 / 255, 180 / 255, 250 / 255) # #89b4fa — пушка (Blue)
TRAIL_COLOR = (203 / 255, 166 / 255, 247 / 255)  # #cba6f7 — траектория (Mauve)
BALL_COLOR = (250 / 255, 179 / 255, 135 / 255)   # #fab387 — снаряд (Peach)


def init_window(title: bytes, width: int, height: int):
    if not sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO):
        raise RuntimeError(f"SDL_Init failed: {sdl3.SDL_GetError().decode()}")

    sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MAJOR_VERSION, 2)
    sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MINOR_VERSION, 1)
    sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_DOUBLEBUFFER, 1)

    window = sdl3.SDL_CreateWindow(
        title,
        width,
        height,
        sdl3.SDL_WINDOW_OPENGL | sdl3.SDL_WINDOW_RESIZABLE,
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
    """Настраивает 2D-систему координат: (0, 0) в левом нижнем углу, ось Y вверх."""
    GL.glViewport(0, 0, width, height)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(0, width, 0, height, -1, 1)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def handle_events() -> bool:
    event = sdl3.SDL_Event()
    while sdl3.SDL_PollEvent(ctypes.byref(event)):
        if event.type == sdl3.SDL_EVENT_QUIT:
            return False

        if event.type == sdl3.SDL_EVENT_KEY_DOWN:
            if event.key.scancode == sdl3.SDL_SCANCODE_ESCAPE:
                return False

    return True


def draw_circle(cx: float, cy: float, radius: float, segments: int = 24) -> None:
    """Рисует закрашенный круг с центром в (cx, cy)."""
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glVertex2f(cx, cy)
    for i in range(segments + 1):
        theta = 2.0 * math.pi * i / segments
        GL.glVertex2f(cx + radius * math.cos(theta), cy + radius * math.sin(theta))
    GL.glEnd()


def draw_ground(width: int, ground_y: float) -> None:
    """Рисует линию горизонта (землю)."""
    GL.glColor3f(*GROUND_COLOR)
    GL.glLineWidth(3.0)
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2f(0.0, ground_y)
    GL.glVertex2f(float(width), ground_y)
    GL.glEnd()


def draw_cannon(x: float, y: float, angle_deg: float) -> None:
    """Рисует схематичную пушку, направленную под углом angle_deg."""
    angle_rad = math.radians(angle_deg)
    barrel_length = 36.0
    end_x = x + barrel_length * math.cos(angle_rad)
    end_y = y + barrel_length * math.sin(angle_rad)

    # Ствол
    GL.glColor3f(*CANNON_COLOR)
    GL.glLineWidth(8.0)
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2f(x, y)
    GL.glVertex2f(end_x, end_y)
    GL.glEnd()

    # Лафет (основание)
    draw_circle(x, y, 10.0)


def draw_trail(trail: list[tuple[float, float]]) -> None:
    """Рисует пройденную траекторию снаряда."""
    if len(trail) < 2:
        return

    GL.glColor4f(*TRAIL_COLOR, 0.75)
    GL.glLineWidth(2.0)
    GL.glBegin(GL.GL_LINE_STRIP)
    for px, py in trail:
        GL.glVertex2f(px, py)
    GL.glEnd()


def render(width: int, height: int, ground_y: float, projectile: Projectile) -> None:
    setup_ortho(width, height)

    GL.glClearColor(*BG_COLOR, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    draw_ground(width, ground_y)
    draw_trail(projectile.trail)
    draw_cannon(projectile.start_x, projectile.start_y, projectile.angle_deg)

    # Сам снаряд
    GL.glColor3f(*BALL_COLOR)
    draw_circle(projectile.x, projectile.y, 7.0)


def cleanup(window, gl_context) -> None:
    sdl3.SDL_GL_DestroyContext(gl_context)
    sdl3.SDL_DestroyWindow(window)
    sdl3.SDL_Quit()


def main() -> None:
    width, height = 1000, 600
    window, gl_context = init_window(b"ProjectFire - Projectile Motion", width, height)

    ground_y = 60.0
    start_x = 80.0
    projectile = Projectile(start_x=start_x, start_y=ground_y, velocity=85.0, angle_deg=45.0)

    w_ptr = ctypes.c_int(width)
    h_ptr = ctypes.c_int(height)
    last_time = time.perf_counter()

    running = True
    while running:
        now = time.perf_counter()
        dt = min(now - last_time, 0.05)  # Ограничиваем dt на случай подвисания окна
        last_time = now

        running = handle_events()
        projectile.update(dt, ground_y)

        sdl3.SDL_GetWindowSizeInPixels(window, ctypes.byref(w_ptr), ctypes.byref(h_ptr))
        render(w_ptr.value, h_ptr.value, ground_y, projectile)

        sdl3.SDL_GL_SwapWindow(window)

    cleanup(window, gl_context)


if __name__ == "__main__":
    main()

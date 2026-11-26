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


def setup_world_ortho(width: int, height: int, cam_x: float, cam_y: float, zoom: float) -> None:
    """Настраивает камеру мира с учетом смещения (cam_x, cam_y) и масштаба zoom."""
    GL.glViewport(0, 0, width, height)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(cam_x, cam_x + width / zoom, cam_y, cam_y + height / zoom, -1, 1)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def setup_screen_ortho(width: int, height: int) -> None:
    """Экранная проекция для неподвижного UI поверх сцены."""
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(0, width, 0, height, -1, 1)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def scancode_to_char(scancode: int) -> str | None:
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
    state: str,
    input_buf: str,
    velocity: float,
    angle: float,
    start_x: float,
    ground_y: float,
    cam_x: float,
    cam_y: float,
    zoom: float,
    is_dragging: bool,
    auto_follow: bool,
) -> tuple[bool, str, str, float, float, Projectile | None, float, float, float, bool, bool]:
    event = sdl3.SDL_Event()
    new_projectile = None

    while sdl3.SDL_PollEvent(ctypes.byref(event)):
        if event.type == sdl3.SDL_EVENT_QUIT:
            return False, state, input_buf, velocity, angle, None, cam_x, cam_y, zoom, is_dragging, auto_follow

        # Зажатие и отпускание ЛКМ для перетаскивания сцены
        elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_DOWN:
            if event.button.button == sdl3.SDL_BUTTON_LEFT:
                is_dragging = True
                auto_follow = False  # При ручном сдвиге отключаем автослежение

        elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_UP:
            if event.button.button == sdl3.SDL_BUTTON_LEFT:
                is_dragging = False

        # Перемещение сцены мышкой (как на карте)
        elif event.type == sdl3.SDL_EVENT_MOUSE_MOTION and is_dragging:
            cam_x -= event.motion.xrel / zoom
            cam_y += event.motion.yrel / zoom
            # Запрещаем опускать камеру ниже пола
            cam_y = max(0.0, cam_y)

        # Масштабирование колёсиком мыши
        elif event.type == sdl3.SDL_EVENT_MOUSE_WHEEL:
            zoom_factor = 1.15 if event.wheel.y > 0 else (1.0 / 1.15)
            zoom = max(0.1, min(5.0, zoom * zoom_factor))
            auto_follow = False

        elif event.type == sdl3.SDL_EVENT_KEY_DOWN:
            scancode = event.key.scancode

            if scancode == sdl3.SDL_SCANCODE_ESCAPE:
                return False, state, input_buf, velocity, angle, None, cam_x, cam_y, zoom, is_dragging, auto_follow

            # Клавиша F (русская 'А') — переключение автослежения и автомасштабирования
            if scancode == sdl3.SDL_SCANCODE_F:
                auto_follow = not auto_follow

            elif state in ("INPUT_V", "INPUT_ANGLE"):
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

    return True, state, input_buf, velocity, angle, new_projectile, cam_x, cam_y, zoom, is_dragging, auto_follow


def update_camera(
    width: int,
    height: int,
    projectile: Projectile | None,
    cam_x: float,
    cam_y: float,
    zoom: float,
    auto_follow: bool,
) -> tuple[float, float, float]:
    """Жёстко закрепляет камеру на пушке (0, 0) и масштабирует сцену под ядро."""
    if not auto_follow:
        return cam_x, max(0.0, cam_y), zoom

    # Жёстко привязываем левый нижний угол камеры к началу координат (пушка всегда на месте)
    cam_x = 0.0
    cam_y = 0.0

    if projectile is None:
        return cam_x, cam_y, 1.0

    # Габариты от левого нижнего угла (0, 0) до текущего положения ядра с запасом под края и UI
    max_x = max(float(width), projectile.x + 80.0)
    max_y = max(float(height), projectile.y + 120.0)

    zoom = min(1.0, width / max_x, height / max_y)
    return cam_x, cam_y, zoom



def draw_circle(cx: float, cy: float, radius: float, segments: int = 24) -> None:
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glVertex2f(cx, cy)
    for i in range(segments + 1):
        theta = 2.0 * math.pi * i / segments
        GL.glVertex2f(cx + radius * math.cos(theta), cy + radius * math.sin(theta))
    GL.glEnd()


def draw_ground(cam_x: float, width: int, zoom: float, ground_y: float) -> None:
    """Рисует бесконечную линию горизонта в пределах видимой области камеры."""
    GL.glColor3f(*GROUND_COLOR)
    GL.glLineWidth(3.0)
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2f(cam_x - 200.0, ground_y)
    GL.glVertex2f(cam_x + width / zoom + 200.0, ground_y)
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
    cam_x: float,
    cam_y: float,
    zoom: float,
    auto_follow: bool,
) -> None:
    GL.glClearColor(*BG_COLOR, 1.0)
    GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    # 1. Отрисовка игрового мира с учетом камеры
    setup_world_ortho(width, height, cam_x, cam_y, zoom)
    draw_ground(cam_x, width, zoom, ground_y)

    if projectile is not None:
        draw_trail(projectile.trail)

    current_angle = projectile.angle_deg if projectile is not None else angle
    draw_cannon(start_x, ground_y, current_angle)

    if projectile is not None:
        GL.glColor3f(*BALL_COLOR)
        # Сохраняем визуальный размер ядра при сильном отдалении
        draw_circle(projectile.x, projectile.y, max(7.0, 6.0 / zoom))

    # 2. Отрисовка неподвижного интерфейса поверх сцены
    setup_screen_ortho(width, height)
    top_y = float(height) - 20.0
    follow_status = "ВКЛ" if auto_follow else "ВЫКЛ"

    if state == "INPUT_V":
        draw_label(f"Введите скорость V (м/с): {input_buf}", 24.0, top_y)
    elif state == "INPUT_ANGLE":
        draw_label(f"V = {velocity} м/с | Введите угол α (0–90°): {input_buf}", 24.0, top_y)
    else:
        draw_label(f"V = {velocity} м/с | Угол α = {angle}° | Время: {projectile.time:.2f} с", 24.0, top_y)

    draw_label(
        f"[ЛКМ] Двигать сцену | [F] Автослежение: {follow_status} (масштаб {zoom:.2f}x)",
        24.0,
        top_y - 34.0,
        font_size=18,
    )


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

    cam_x = 0.0
    cam_y = 0.0
    zoom = 1.0
    is_dragging = False
    auto_follow = True

    w_ptr = ctypes.c_int(width)
    h_ptr = ctypes.c_int(height)

    last_time = time.perf_counter()
    running = True

    while running:
        now = time.perf_counter()
        dt = min(now - last_time, 0.05)
        last_time = now

        (
            running, state, input_buf, velocity, angle, new_proj,
            cam_x, cam_y, zoom, is_dragging, auto_follow
        ) = handle_events(
            state, input_buf, velocity, angle, start_x, ground_y,
            cam_x, cam_y, zoom, is_dragging, auto_follow
        )

        if new_proj is not None:
            projectile = new_proj

        if state == "FLYING" and projectile is not None:
            projectile.update(dt, ground_y)
            if not projectile.is_flying:
                state = "INPUT_V"
                input_buf = ""

        sdl3.SDL_GetWindowSizeInPixels(window, ctypes.byref(w_ptr), ctypes.byref(h_ptr))

        cam_x, cam_y, zoom = update_camera(
            w_ptr.value, h_ptr.value, projectile, cam_x, cam_y, zoom, auto_follow
        )

        render(
            w_ptr.value, h_ptr.value, ground_y, start_x, projectile,
            state, input_buf, velocity, angle, cam_x, cam_y, zoom, auto_follow
        )
        sdl3.SDL_GL_SwapWindow(window)

    cleanup(window, gl_context)


if __name__ == "__main__":
    main()
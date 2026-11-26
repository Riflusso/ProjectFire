import ctypes

import sdl3


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
    cam_x: float,
    cam_y: float,
    zoom: float,
    is_dragging: bool,
    auto_follow: bool,
) -> tuple[bool, str, str, float, float, bool, bool, float, float, float, bool, bool]:
    """Обрабатывает ввод. Возвращает флаги launched (новый выстрел) и reset_scene (полный сброс)."""
    event = sdl3.SDL_Event()
    launched = False
    reset_scene = False

    while sdl3.SDL_PollEvent(ctypes.byref(event)):
        if event.type == sdl3.SDL_EVENT_QUIT:
            return False, state, input_buf, velocity, angle, False, False, cam_x, cam_y, zoom, is_dragging, auto_follow

        elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_DOWN:
            if event.button.button == sdl3.SDL_BUTTON_LEFT:
                is_dragging = True
                auto_follow = False

        elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_UP:
            if event.button.button == sdl3.SDL_BUTTON_LEFT:
                is_dragging = False

        elif event.type == sdl3.SDL_EVENT_MOUSE_MOTION and is_dragging:
            cam_x -= event.motion.xrel / zoom
            cam_y = max(0.0, cam_y + event.motion.yrel / zoom)

        elif event.type == sdl3.SDL_EVENT_MOUSE_WHEEL:
            zoom_factor = 1.15 if event.wheel.y > 0 else (1.0 / 1.15)
            zoom = max(0.05, min(5.0, zoom * zoom_factor))
            auto_follow = False

        elif event.type == sdl3.SDL_EVENT_KEY_DOWN:
            scancode = event.key.scancode

            if scancode == sdl3.SDL_SCANCODE_ESCAPE:
                return False, state, input_buf, velocity, angle, False, False, cam_x, cam_y, zoom, is_dragging, auto_follow

            # Клавиша R — полный сброс сцены и возврат в начальное состояние
            if scancode == sdl3.SDL_SCANCODE_R:
                reset_scene = True
                state = "INPUT_V"
                input_buf = ""
                cam_x = 0.0
                cam_y = 0.0
                zoom = 1.0
                auto_follow = True

            elif scancode == sdl3.SDL_SCANCODE_F:
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
                        launched = True

    return True, state, input_buf, velocity, angle, launched, reset_scene, cam_x, cam_y, zoom, is_dragging, auto_follow

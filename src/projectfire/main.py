import ctypes
import time

import sdl3

from .camera import update_camera
from .input import handle_events
from .physics import step_projectile
from .renderer import render_scene
from .window import cleanup, init_window


def main() -> None:
    width, height = 1000, 600
    window, gl_context = init_window(b"ProjectFire - Projectile Motion", width, height)

    ground_y = 60.0
    start_x = 80.0

    state = "INPUT_V"
    input_buf = ""
    velocity = 0.0
    angle = 45.0

    has_projectile = False
    is_flying = False
    proj_x = start_x
    proj_y = ground_y
    flight_time = 0.0
    trail: list[tuple[float, float]] = []

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
            running, state, input_buf, velocity, angle, launched, reset_scene,
            cam_x, cam_y, zoom, is_dragging, auto_follow
        ) = handle_events(
            state, input_buf, velocity, angle, cam_x, cam_y, zoom, is_dragging, auto_follow
        )

        if reset_scene:
            has_projectile = False
            is_flying = False
            proj_x = start_x
            proj_y = ground_y
            flight_time = 0.0
            trail.clear()
            velocity = 0.0
            angle = 45.0

        if launched:
            has_projectile = True
            is_flying = True
            proj_x = start_x
            proj_y = ground_y
            flight_time = 0.0
            trail = [(proj_x, proj_y)]

        if state == "FLYING" and is_flying:
            proj_x, proj_y, flight_time, is_flying = step_projectile(
                start_x, ground_y, velocity, angle, flight_time, dt, ground_y, trail
            )
            if not is_flying:
                state = "INPUT_V"
                input_buf = ""

        sdl3.SDL_GetWindowSizeInPixels(window, ctypes.byref(w_ptr), ctypes.byref(h_ptr))
        cam_x, cam_y, zoom = update_camera(
            w_ptr.value, h_ptr.value, has_projectile, proj_x, proj_y, cam_x, cam_y, zoom, auto_follow
        )

        render_scene(
            w_ptr.value, h_ptr.value, ground_y, start_x,
            has_projectile, proj_x, proj_y, flight_time, trail,
            state, input_buf, velocity, angle, cam_x, cam_y, zoom, auto_follow
        )

        sdl3.SDL_GL_SwapWindow(window)

    cleanup(window, gl_context)


if __name__ == "__main__":
    main()

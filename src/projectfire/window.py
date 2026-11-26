import sdl3
from OpenGL import GL

from .ui import cleanup_ui


def init_window(title: bytes, width: int, height: int):
    if not sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO):
        raise RuntimeError(f"SDL_Init failed: {sdl3.SDL_GetError().decode()}")

    sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MAJOR_VERSION, 2)
    sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MINOR_VERSION, 1)
    sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_DOUBLEBUFFER, 1)

    sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_MULTISAMPLEBUFFERS, 1)
    sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_MULTISAMPLESAMPLES, 4)

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

    GL.glEnable(GL.GL_MULTISAMPLE)
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glEnable(GL.GL_LINE_SMOOTH)
    GL.glHint(GL.GL_LINE_SMOOTH_HINT, GL.GL_NICEST)

    return window, gl_context


def cleanup(window, gl_context) -> None:
    cleanup_ui()
    sdl3.SDL_GL_DestroyContext(gl_context)
    sdl3.SDL_DestroyWindow(window)
    sdl3.SDL_Quit()

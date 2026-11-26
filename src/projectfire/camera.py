from OpenGL import GL


def setup_world_ortho(width: int, height: int, cam_x: float, cam_y: float, zoom: float) -> None:
    """Настраивает мировую камеру с учётом смещения и масштаба."""
    GL.glViewport(0, 0, width, height)
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(cam_x, cam_x + width / zoom, cam_y, cam_y + height / zoom, -1, 1)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def setup_screen_ortho(width: int, height: int) -> None:
    """Настраивает экранную проекцию для статичного интерфейса."""
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(0, width, 0, height, -1, 1)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()


def update_camera(
    width: int,
    height: int,
    has_projectile: bool,
    proj_x: float,
    proj_y: float,
    cam_x: float,
    cam_y: float,
    zoom: float,
    auto_follow: bool,
) -> tuple[float, float, float]:
    """Закрепляет камеру на пушке (0, 0) и подбирает масштаб под ядро при автослежении."""
    if not auto_follow:
        return cam_x, max(0.0, cam_y), zoom

    cam_x = 0.0
    cam_y = 0.0

    if not has_projectile:
        return cam_x, cam_y, 1.0

    max_x = max(float(width), proj_x + 80.0)
    max_y = max(float(height), proj_y + 120.0)
    zoom = min(1.0, width / max_x, height / max_y)

    return cam_x, cam_y, zoom

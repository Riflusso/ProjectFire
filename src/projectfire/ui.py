from OpenGL import GL
from PIL import Image, ImageDraw, ImageFont

# Кэш текстур: текст -> (tex_id, width, height)
_text_cache: dict[str, tuple[int, int, int]] = {}


def draw_label(
    text: str,
    x: float,
    y: float,
    font_size: int = 24,
    color: tuple[int, int, int, int] = (205, 214, 244, 255),
) -> None:
    """Рисует текст через Pillow в координатах (x, y), где y — верхняя граница."""
    cache_key = f"{font_size}:{text}"
    if cache_key not in _text_cache:
        # Ограничиваем размер кэша, чтобы не копить старые введённые числа в видеопамяти
        if len(_text_cache) > 16:
            cleanup_ui()

        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

        left, top, right, bottom = font.getbbox(text)
        w = max(1, right - left + 4)
        h = max(1, bottom - top + 4)

        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((-left + 2, -top + 2), text, font=font, fill=color)

        tex_id = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex_id)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, w, h, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, img.tobytes()
        )
        _text_cache[cache_key] = (tex_id, w, h)

    tex_id, w, h = _text_cache[cache_key]

    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glBindTexture(GL.GL_TEXTURE_2D, tex_id)
    GL.glColor3f(1.0, 1.0, 1.0)

    GL.glBegin(GL.GL_QUADS)
    GL.glTexCoord2f(0.0, 0.0); GL.glVertex2f(x, y)
    GL.glTexCoord2f(1.0, 0.0); GL.glVertex2f(x + w, y)
    GL.glTexCoord2f(1.0, 1.0); GL.glVertex2f(x + w, y - h)
    GL.glTexCoord2f(0.0, 1.0); GL.glVertex2f(x, y - h)
    GL.glEnd()

    GL.glDisable(GL.GL_TEXTURE_2D)


def cleanup_ui() -> None:
    """Освобождает все закэшированные текстуры текста."""
    if _text_cache:
        GL.glDeleteTextures([tex_id for tex_id, _, _ in _text_cache.values()])
        _text_cache.clear()
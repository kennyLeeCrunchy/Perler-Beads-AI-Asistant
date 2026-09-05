from __future__ import annotations

import io

from PIL import Image, ImageDraw

from .quantizer import BeadPattern


def render_pattern_png(pattern: BeadPattern, cell_size: int = 16, show_grid: bool = True) -> bytes:
    image = Image.new("RGBA", (pattern.width * cell_size, pattern.height * cell_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    for y, row in enumerate(pattern.cells):
        for x, code in enumerate(row):
            if code is None:
                continue
            else:
                fill = pattern.colors[code].hex
            left = x * cell_size
            top = y * cell_size
            draw.rectangle(
                [left, top, left + cell_size - 1, top + cell_size - 1],
                fill=fill,
                outline="#D9D9D9" if show_grid else fill,
            )
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()

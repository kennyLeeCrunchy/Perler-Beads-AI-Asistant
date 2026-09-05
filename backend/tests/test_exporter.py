import io
import unittest

from PIL import Image

from app.core.exporter import render_pattern_png
from app.core.palette import PaletteColor
from app.core.quantizer import BeadPattern


class ExporterTests(unittest.TestCase):
    def test_render_pattern_png_keeps_empty_cells_transparent(self):
        pattern = BeadPattern(
            width=2,
            height=1,
            cells=[["R1", None]],
            color_counts={"R1": 1},
            colors={
                "R1": PaletteColor(
                    code="R1",
                    series="R",
                    name="red",
                    name_zh="red",
                    hex="#FF0000",
                    rgb=(255, 0, 0),
                )
            },
        )

        png = render_pattern_png(pattern, cell_size=2, show_grid=False)
        image = Image.open(io.BytesIO(png))

        self.assertEqual(image.mode, "RGBA")
        self.assertEqual(image.getpixel((0, 0)), (255, 0, 0, 255))
        self.assertEqual(image.getpixel((3, 0))[3], 0)


if __name__ == "__main__":
    unittest.main()

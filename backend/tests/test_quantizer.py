import unittest

from PIL import Image

from app.core.palette import PaletteColor
from app.core.quantizer import quantize_image


class QuantizerTests(unittest.TestCase):
    def test_quantize_image_maps_pixels_to_nearest_palette_colors(self):
        image = Image.new("RGB", (2, 1))
        image.putpixel((0, 0), (250, 5, 5))
        image.putpixel((1, 0), (5, 5, 250))
        palette = [
            PaletteColor(code="R1", series="R", name="red", name_zh="红", hex="#FF0000", rgb=(255, 0, 0)),
            PaletteColor(code="B1", series="B", name="blue", name_zh="蓝", hex="#0000FF", rgb=(0, 0, 255)),
        ]

        pattern = quantize_image(
            image,
            palette,
            width=2,
            height=1,
            max_colors=0,
            similarity_threshold=0,
            auto_cleanup=False,
            smooth_edges=False,
            preprocess=False,
        )

        self.assertEqual(pattern.width, 2)
        self.assertEqual(pattern.height, 1)
        self.assertEqual(pattern.cells, [["R1", "B1"]])
        self.assertEqual(pattern.color_counts, {"B1": 1, "R1": 1})

    def test_quantize_image_limits_to_most_common_colors(self):
        image = Image.new("RGB", (3, 1))
        image.putpixel((0, 0), (255, 0, 0))
        image.putpixel((1, 0), (255, 0, 0))
        image.putpixel((2, 0), (0, 0, 255))
        palette = [
            PaletteColor(code="R1", series="R", name="red", name_zh="红", hex="#FF0000", rgb=(255, 0, 0)),
            PaletteColor(code="B1", series="B", name="blue", name_zh="蓝", hex="#0000FF", rgb=(0, 0, 255)),
        ]

        pattern = quantize_image(
            image,
            palette,
            width=3,
            height=1,
            max_colors=1,
            similarity_threshold=0,
            auto_cleanup=False,
            smooth_edges=False,
            preprocess=False,
        )

        self.assertEqual(pattern.cells, [["R1", "R1", "R1"]])
        self.assertEqual(pattern.color_counts, {"R1": 3})

    def test_quantize_image_merges_similar_low_frequency_colors_into_frequent_colors(self):
        image = Image.new("RGB", (3, 1))
        image.putpixel((0, 0), (255, 0, 0))
        image.putpixel((1, 0), (255, 0, 0))
        image.putpixel((2, 0), (245, 10, 10))
        palette = [
            PaletteColor(code="R1", series="R", name="red", name_zh="red", hex="#FF0000", rgb=(255, 0, 0)),
            PaletteColor(code="R2", series="R", name="near red", name_zh="near red", hex="#F50A0A", rgb=(245, 10, 10)),
        ]

        pattern = quantize_image(
            image,
            palette,
            width=3,
            height=1,
            max_colors=0,
            similarity_threshold=30,
            auto_cleanup=False,
            smooth_edges=False,
            preprocess=False,
        )

        self.assertEqual(pattern.cells, [["R1", "R1", "R1"]])
        self.assertEqual(pattern.color_counts, {"R1": 3})

    def test_quantize_image_uses_beadcraft_mode_pool_pipeline(self):
        image = Image.new("RGB", (4, 4), (255, 0, 0))
        for x in range(3):
            image.putpixel((x, 0), (0, 0, 255))
        palette = [
            PaletteColor(code="R1", series="R", name="red", name_zh="red", hex="#FF0000", rgb=(255, 0, 0)),
            PaletteColor(code="B1", series="B", name="blue", name_zh="blue", hex="#0000FF", rgb=(0, 0, 255)),
        ]

        pattern = quantize_image(
            image,
            palette,
            width=1,
            height=1,
            max_colors=0,
            similarity_threshold=0,
            auto_cleanup=False,
            smooth_edges=False,
            preprocess=False,
        )

        self.assertEqual(pattern.cells, [["R1"]])

    def test_quantize_image_uses_alpha_as_empty_cells_when_removing_background(self):
        image = Image.new("RGBA", (2, 1))
        image.putpixel((0, 0), (255, 0, 0, 255))
        image.putpixel((1, 0), (255, 255, 255, 0))
        palette = [
            PaletteColor(code="R1", series="R", name="red", name_zh="red", hex="#FF0000", rgb=(255, 0, 0)),
            PaletteColor(code="W1", series="W", name="white", name_zh="white", hex="#FFFFFF", rgb=(255, 255, 255)),
        ]

        pattern = quantize_image(
            image,
            palette,
            width=2,
            height=1,
            max_colors=0,
            similarity_threshold=0,
            remove_bg=True,
            auto_cleanup=False,
            smooth_edges=False,
            preprocess=False,
        )

        self.assertEqual(pattern.cells, [["R1", None]])
        self.assertEqual(pattern.color_counts, {"R1": 1})

    def test_transparent_rgb_does_not_consume_foreground_palette_slots(self):
        image = Image.new("RGBA", (10, 10), (255, 255, 255, 0))
        for y in range(4, 6):
            for x in range(4, 6):
                image.putpixel((x, y), (255, 0, 0, 255))
        palette = [
            PaletteColor(code="R1", series="R", name="red", name_zh="red", hex="#FF0000", rgb=(255, 0, 0)),
            PaletteColor(code="W1", series="W", name="white", name_zh="white", hex="#FFFFFF", rgb=(255, 255, 255)),
        ]

        pattern = quantize_image(
            image,
            palette,
            width=10,
            height=10,
            max_colors=1,
            similarity_threshold=0,
            remove_bg=True,
            auto_cleanup=False,
            smooth_edges=False,
            preprocess=False,
        )

        self.assertEqual(pattern.color_counts, {"R1": 4})

    def test_palette_budget_reserves_a_rare_dark_detail_color(self):
        image = Image.new("RGB", (10, 10), (255, 255, 255))
        for y in range(5, 10):
            for x in range(10):
                image.putpixel((x, y), (255, 180, 190))
        image.putpixel((4, 4), (0, 0, 0))
        image.putpixel((5, 4), (0, 0, 0))
        palette = [
            PaletteColor(code="W1", series="W", name="white", name_zh="white", hex="#FFFFFF", rgb=(255, 255, 255)),
            PaletteColor(code="P1", series="P", name="pink", name_zh="pink", hex="#FFB4BE", rgb=(255, 180, 190)),
            PaletteColor(code="K1", series="K", name="black", name_zh="black", hex="#000000", rgb=(0, 0, 0)),
        ]

        pattern = quantize_image(
            image,
            palette,
            width=10,
            height=10,
            max_colors=2,
            similarity_threshold=0,
            auto_cleanup=False,
            smooth_edges=False,
            preprocess=False,
        )

        self.assertIn("K1", pattern.color_counts)
        self.assertLessEqual(len(pattern.color_counts), 2)

    def test_quantize_image_removes_light_neutral_checkerboard_background_before_quantization(self):
        image = Image.new("RGB", (4, 4), (255, 255, 255))
        for y in range(4):
            for x in range(4):
                if (x + y) % 2:
                    image.putpixel((x, y), (232, 238, 241))
        for y in (1, 2):
            for x in (1, 2):
                image.putpixel((x, y), (255, 0, 0))
        palette = [
            PaletteColor(code="R1", series="R", name="red", name_zh="red", hex="#FF0000", rgb=(255, 0, 0)),
            PaletteColor(code="W1", series="W", name="white", name_zh="white", hex="#FFFFFF", rgb=(255, 255, 255)),
            PaletteColor(code="G1", series="G", name="gray", name_zh="gray", hex="#E8EEF1", rgb=(232, 238, 241)),
        ]

        pattern = quantize_image(
            image,
            palette,
            width=4,
            height=4,
            max_colors=0,
            similarity_threshold=0,
            remove_bg=True,
            auto_cleanup=False,
            smooth_edges=False,
            preprocess=False,
        )

        self.assertEqual(
            pattern.cells,
            [
                [None, None, None, None],
                [None, "R1", "R1", None],
                [None, "R1", "R1", None],
                [None, None, None, None],
            ],
        )
        self.assertEqual(pattern.color_counts, {"R1": 4})

    def test_quantize_image_preserves_thin_black_facial_details(self):
        image = Image.new("RGB", (8, 8), (255, 255, 255))
        for y in range(4, 6):
            image.putpixel((3, y), (0, 0, 0))
            image.putpixel((4, y), (0, 0, 0))
        palette = [
            PaletteColor(code="H1", series="H", name="white", name_zh="white", hex="#FFFFFF", rgb=(255, 255, 255)),
            PaletteColor(code="H7", series="H", name="black", name_zh="black", hex="#000000", rgb=(0, 0, 0)),
        ]

        pattern = quantize_image(
            image,
            palette,
            width=4,
            height=4,
            max_colors=0,
            similarity_threshold=0,
            auto_cleanup=False,
            smooth_edges=True,
            preprocess=False,
        )

        self.assertGreaterEqual(pattern.color_counts.get("H7", 0), 2)

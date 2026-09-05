import unittest

from PIL import Image

from app.core.mask_processor import create_transparent_foreground


class MaskProcessorTests(unittest.TestCase):
    def test_create_transparent_foreground_uses_existing_alpha(self):
        image = Image.new("RGBA", (2, 1))
        image.putpixel((0, 0), (255, 0, 0, 255))
        image.putpixel((1, 0), (255, 255, 255, 0))

        result = create_transparent_foreground(image)

        self.assertEqual(result.method, "alpha")
        self.assertEqual(result.image.mode, "RGBA")
        self.assertEqual(result.image.getpixel((0, 0)), (255, 0, 0, 255))
        self.assertEqual(result.image.getpixel((1, 0))[3], 0)

    def test_create_transparent_foreground_removes_light_checkerboard_background(self):
        image = Image.new("RGB", (4, 4), (255, 255, 255))
        for y in range(4):
            for x in range(4):
                if (x + y) % 2:
                    image.putpixel((x, y), (232, 238, 241))
        for y in (1, 2):
            for x in (1, 2):
                image.putpixel((x, y), (255, 0, 0))

        result = create_transparent_foreground(image)

        self.assertEqual(result.method, "light_background")
        self.assertEqual(result.image.mode, "RGBA")
        self.assertEqual(result.image.getpixel((0, 0))[3], 0)
        self.assertEqual(result.image.getpixel((3, 3))[3], 0)
        self.assertEqual(result.image.getpixel((1, 1)), (255, 0, 0, 255))
        self.assertEqual(result.foreground_pixels, 4)

    def test_create_transparent_foreground_rejects_failed_mask_with_too_much_foreground(self):
        # Mid-gray is intentionally outside the light-background detector. A
        # 210-gray canvas is now a supported generated-background case and no
        # longer represents a failed mask.
        image = Image.new("RGB", (10, 10), (120, 120, 120))
        for y in range(2, 8):
            for x in range(2, 8):
                image.putpixel((x, y), (180, 80, 40))

        result = create_transparent_foreground(image)

        self.assertFalse(result.success)
        self.assertEqual(result.method, "failed")
        self.assertGreater(result.foreground_ratio, 0.75)


if __name__ == "__main__":
    unittest.main()

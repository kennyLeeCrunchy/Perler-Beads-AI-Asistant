import unittest

from app.api.routes_export import ExportColor, ExportPngRequest, export_png


class ExportApiTests(unittest.TestCase):
    def test_export_png_accepts_edited_pattern_cells(self):
        response = export_png(
            ExportPngRequest(
                width=2,
                height=2,
                cells=[["A01", None], ["A01", "A02"]],
                colors=[
                    ExportColor(code="A01", hex="#112233", name="深色"),
                    ExportColor(code="A02", hex="#F0E0D0", name="浅色"),
                ],
            )
        )

        self.assertEqual(response.media_type, "image/png")
        self.assertTrue(response.body.startswith(b"\x89PNG"))


if __name__ == "__main__":
    unittest.main()

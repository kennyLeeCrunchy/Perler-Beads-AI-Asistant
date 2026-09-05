from pathlib import Path
import unittest

from app.core.palette import load_mard_palette, load_palette, load_presets, resolve_palette


DATA_DIR = Path(__file__).resolve().parents[1] / "app" / "data"
MARD_PATH = Path(__file__).resolve().parents[1] / "color_standards" / "mard_221_colors_vertical.csv"


class PaletteTests(unittest.TestCase):
    def test_load_palette_reads_artkal_colors(self):
        colors = load_palette(DATA_DIR / "artkal_m_series.json")

        self.assertEqual(len(colors), 221)
        self.assertEqual(colors["A1"].code, "A1")
        self.assertEqual(colors["A1"].hex.upper(), "#FFF6D4")
        self.assertEqual(colors["M15"].series, "M")

    def test_resolve_palette_filters_named_preset(self):
        colors = load_palette(DATA_DIR / "artkal_m_series.json")
        presets = load_presets(DATA_DIR / "artkal_presets.json")

        selected = resolve_palette(colors, presets, "96")

        self.assertEqual(len(selected), 96)
        self.assertEqual(selected[0].code, "A3")
        self.assertTrue(all(color.code in presets["96"].codes for color in selected))

    def test_resolve_palette_full_set_when_codes_are_null(self):
        colors = load_palette(DATA_DIR / "artkal_m_series.json")
        presets = load_presets(DATA_DIR / "artkal_presets.json")

        selected = resolve_palette(colors, presets, "221")

        self.assertEqual(len(selected), 221)

    def test_load_mard_palette_reads_221_colors(self):
        colors = load_mard_palette(MARD_PATH)

        self.assertEqual(len(colors), 221)
        self.assertEqual(colors["A1"].hex, "#FAF4C8")
        self.assertEqual(colors["A1"].rgb, (250, 244, 200))
        self.assertEqual(colors["A1"].series, "Mard")

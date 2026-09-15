import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

import app.api.routes_export as routes_export
import app.api.routes_ai as routes_ai
import app.api.routes_pattern as routes_pattern
import app.core.bundle as bundle
from app.core.config import MARD_PALETTE_PATH
from app.core.palette import load_mard_palette
from app.api_main import app


class ApiIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.runtime = tempfile.TemporaryDirectory()
        runtime_path = Path(self.runtime.name)
        (runtime_path / "uploads").mkdir()
        (runtime_path / "generated").mkdir()
        self.runtime_patches = [
            patch.object(routes_pattern, "RUNTIME_DIR", runtime_path),
            patch.object(routes_export, "RUNTIME_DIR", runtime_path),
            patch.object(routes_ai, "RUNTIME_DIR", runtime_path),
            patch.object(bundle, "RUNTIME_DIR", runtime_path),
        ]
        for runtime_patch in self.runtime_patches:
            runtime_patch.start()
        self.client = TestClient(app)

    def tearDown(self):
        for runtime_patch in reversed(self.runtime_patches):
            runtime_patch.stop()
        self.runtime.cleanup()

    def test_upload_convert_and_edited_export_contract(self):
        source = Image.new("RGB", (48, 48), "white")
        draw = ImageDraw.Draw(source)
        draw.rectangle((10, 10, 37, 37), fill="#D96B3B")
        buffer = io.BytesIO()
        source.save(buffer, format="PNG")

        generated = self.client.post(
            "/api/pattern/generate",
            files={"image": ("sample.png", buffer.getvalue(), "image/png")},
            data={
                "width": "12",
                "height": "12",
                "preset": "96",
                "max_colors": "12",
                "similarity_threshold": "18",
                "use_transparent_mask": "false",
            },
        )
        self.assertEqual(generated.status_code, 200, generated.text)
        pattern = generated.json()
        self.assertEqual(pattern["width"], 12)
        self.assertEqual(len(pattern["cells"]), 12)
        self.assertTrue(pattern["counts"])

        exported = self.client.post(
            "/api/export/png",
            json={
                "pattern_id": pattern["pattern_id"],
                "width": pattern["width"],
                "height": pattern["height"],
                "cells": pattern["cells"],
                "colors": [
                    {"code": row["code"], "hex": row["hex"], "name": row["name"]}
                    for row in pattern["counts"]
                ],
            },
        )
        self.assertEqual(exported.status_code, 200, exported.text)
        self.assertEqual(exported.headers["content-type"], "image/png")
        self.assertTrue(exported.content.startswith(b"\x89PNG"))

    def test_upload_can_quantize_with_mard_palette(self):
        source = Image.new("RGB", (24, 24), "#FAF4C8")
        buffer = io.BytesIO()
        source.save(buffer, format="PNG")

        generated = self.client.post(
            "/api/pattern/generate",
            files={"image": ("mard.png", buffer.getvalue(), "image/png")},
            data={
                "brand": "Mard",
                "width": "8",
                "height": "8",
                "max_colors": "8",
                "similarity_threshold": "0",
                "use_transparent_mask": "false",
            },
        )

        self.assertEqual(generated.status_code, 200, generated.text)
        payload = generated.json()
        self.assertEqual(payload["brand"], "Mard")
        mard_colors = load_mard_palette(MARD_PALETTE_PATH)
        self.assertTrue(payload["counts"])
        for item in payload["counts"]:
            self.assertIn(item["code"], mard_colors)
            self.assertEqual(item["hex"].upper(), mard_colors[item["code"]].hex.upper())

    def test_palette_endpoint_returns_mard_221_colors(self):
        response = self.client.get("/api/palette", params={"brand": "Mard"})

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["brand"], "Mard")
        self.assertEqual(len(payload["colors"]), 221)
        self.assertEqual(payload["colors"][0]["code"], "A1")

    def test_bundle_returns_three_sizes_from_one_source(self):
        source = Image.new("RGB", (64, 64), "white")
        ImageDraw.Draw(source).ellipse((12, 8, 52, 56), fill="#D96B3B")
        buffer = io.BytesIO()
        source.save(buffer, format="PNG")

        response = self.client.post(
            "/api/pattern/bundle",
            files={"image": ("bundle.png", buffer.getvalue(), "image/png")},
            data={"brand": "Mard", "max_colors": "12", "similarity_threshold": "18"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["ai_passes"], 0)
        self.assertEqual([item["width"] for item in payload["variants"]], [52, 78, 104])
        self.assertEqual([item["height"] for item in payload["variants"]], [52, 78, 104])
        self.assertTrue(all(item["counts"] for item in payload["variants"]))

    def test_clean_reference_endpoint_preserves_single_pass_contract(self):
        fake = SimpleNamespace(
            clean_reference_id="a" * 32,
            task_id="task-clean",
            model="wan2.5-i2i-preview",
            pattern_source_path=Path("a.clean.raw.png"),
            raw_path=Path("a.clean.raw.png"),
            prompt_version="bead_ready_52_v2",
            source_type="scene",
            confidence=0.7,
            mask_method=None,
            foreground_ratio=None,
        )
        source = Image.new("RGB", (32, 32), "#D96B3B")
        buffer = io.BytesIO()
        source.save(buffer, format="PNG")
        with patch.object(routes_ai, "create_clean_reference", return_value=fake) as create:
            response = self.client.post(
                "/api/ai/clean-reference",
                files={"image": ("source.png", buffer.getvalue(), "image/png")},
                data={"mode": "auto"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["ai_passes"], 1)
        self.assertEqual(payload["algorithm_version"], "bead_ready_52_v2")
        self.assertEqual(create.call_count, 1)


if __name__ == "__main__":
    unittest.main()

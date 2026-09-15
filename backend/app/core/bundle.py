from __future__ import annotations

import base64
import json
from pathlib import Path
from uuid import uuid4

from PIL import Image

from .config import RUNTIME_DIR
from .exporter import render_pattern_png
from .image_pipeline import ALGORITHM_VERSION, PIPELINE_VERSION
from .palette import PaletteColor
from .quality import assess_color_fidelity, assess_pattern_quality, report_to_dict
from .quantizer import BeadPattern, quantize_image
from .schemas import pattern_counts_for_ui, pattern_to_dict


AUTO_BOARD_SIZES = ((52, 52), (78, 78), (104, 104))


def generate_pattern_bundle(
    image: Image.Image,
    *,
    palette: list[PaletteColor],
    max_colors: int = 20,
    similarity_threshold: float = 18,
    use_transparent_mask: bool = False,
    clean_reference_id: str | None = None,
) -> dict:
    variants: list[dict] = []
    for width, height in AUTO_BOARD_SIZES:
        pattern = quantize_image(
            image,
            palette=palette,
            width=width,
            height=height,
            max_colors=max_colors,
            similarity_threshold=similarity_threshold,
            remove_bg=use_transparent_mask,
            smooth_edges=True,
            auto_cleanup=True,
        )
        pattern_id = uuid4().hex
        path = RUNTIME_DIR / "generated" / f"{pattern_id}.json"
        path.write_text(json.dumps(pattern_to_dict(pattern), ensure_ascii=False), encoding="utf-8")
        preview = render_pattern_png(pattern, cell_size=8 if width >= 78 else 10)
        general_quality = assess_pattern_quality(
            pattern,
            max_colors=max_colors,
            require_transparent_background=use_transparent_mask,
        )
        fidelity_quality = assess_color_fidelity(image, pattern)
        variants.append({
            "pattern_id": pattern_id,
            "width": width,
            "height": height,
            "cells": pattern.cells,
            "counts": pattern_counts_for_ui(pattern),
            "preview_data_url": "data:image/png;base64," + base64.b64encode(preview).decode("ascii"),
            "quality": {
                "structure": report_to_dict(general_quality),
                "color": report_to_dict(fidelity_quality),
            },
        })
    return {
        "algorithm_version": ALGORITHM_VERSION,
        "pipeline": PIPELINE_VERSION,
        "ai_passes": 1 if clean_reference_id else 0,
        "clean_reference_id": clean_reference_id,
        "variants": variants,
    }

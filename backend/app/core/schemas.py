from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .quantizer import BeadPattern


def pattern_to_dict(pattern: BeadPattern) -> dict:
    return {
        "width": pattern.width,
        "height": pattern.height,
        "cells": pattern.cells,
        "color_counts": pattern.color_counts,
        "colors": {
            code: {
                "code": color.code,
                "series": color.series,
                "name": color.name,
                "name_zh": color.name_zh,
                "hex": color.hex,
                "rgb": list(color.rgb),
            }
            for code, color in pattern.colors.items()
        },
    }


def pattern_from_dict(payload: dict) -> BeadPattern:
    from .palette import PaletteColor

    colors = {
        code: PaletteColor(
            code=value["code"],
            series=value["series"],
            name=value["name"],
            name_zh=value["name_zh"],
            hex=value["hex"],
            rgb=tuple(value["rgb"]),
        )
        for code, value in payload["colors"].items()
    }
    return BeadPattern(
        width=payload["width"],
        height=payload["height"],
        cells=payload["cells"],
        color_counts=payload["color_counts"],
        colors=colors,
    )


def pattern_counts_for_ui(pattern: BeadPattern) -> list[dict]:
    rows = []
    for code, count in sorted(pattern.color_counts.items(), key=lambda item: item[1], reverse=True):
        color = pattern.colors[code]
        rows.append(
            {
                "code": code,
                "count": count,
                "hex": color.hex,
                "name": color.name_zh or color.name,
            }
        )
    return rows


def ensure_runtime_path(path: Path, runtime_root: Path) -> Path:
    resolved = path.resolve()
    resolved.relative_to(runtime_root.resolve())
    return resolved

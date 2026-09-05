from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PaletteColor:
    code: str
    series: str
    name: str
    name_zh: str
    hex: str
    rgb: tuple[int, int, int]


@dataclass(frozen=True)
class PalettePreset:
    key: str
    label: str
    codes: list[str] | None


def load_palette(path: Path) -> dict[str, PaletteColor]:
    raw_colors = json.loads(path.read_text(encoding="utf-8"))
    colors: dict[str, PaletteColor] = {}
    for item in raw_colors:
        color = PaletteColor(
            code=item["code"],
            series=item.get("series", ""),
            name=item.get("name", item["code"]),
            name_zh=item.get("name_zh", item.get("name", item["code"])),
            hex=item["hex"],
            rgb=tuple(item["rgb"]),
        )
        colors[color.code] = color
    return colors


def load_mard_palette(path: Path) -> dict[str, PaletteColor]:
    colors: dict[str, PaletteColor] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        for item in csv.DictReader(source):
            code = item["mard_code"].strip()
            color = PaletteColor(
                code=code,
                series="Mard",
                name=code,
                name_zh=code,
                hex=item["hex"].strip().upper(),
                rgb=(int(item["r"]), int(item["g"]), int(item["b"])),
            )
            colors[code] = color
    if not colors:
        raise ValueError("Mard palette is empty")
    return colors


def load_presets(path: Path) -> dict[str, PalettePreset]:
    raw_presets = json.loads(path.read_text(encoding="utf-8"))
    return {
        key: PalettePreset(key=key, label=value["label"], codes=value["codes"])
        for key, value in raw_presets.items()
    }


def resolve_palette(
    colors: dict[str, PaletteColor],
    presets: dict[str, PalettePreset],
    preset_key: str,
) -> list[PaletteColor]:
    preset = presets.get(preset_key)
    if preset is None:
        raise ValueError(f"Unknown palette preset: {preset_key}")
    if preset.codes is None:
        return list(colors.values())
    return [colors[code] for code in preset.codes if code in colors]

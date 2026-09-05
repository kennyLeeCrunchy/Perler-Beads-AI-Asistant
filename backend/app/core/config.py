from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "app" / "data"
MARD_PALETTE_PATH = ROOT_DIR / "color_standards" / "mard_221_colors_vertical.csv"
runtime_override = os.getenv("PINDOU_RUNTIME_DIR", "").strip()
RUNTIME_DIR = Path(runtime_override or ROOT_DIR / "runtime").resolve()
for runtime_child in ("uploads", "generated", "exports"):
    (RUNTIME_DIR / runtime_child).mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Settings:
    dashscope_api_key: str | None
    dashscope_base_url: str
    dashscope_model: str
    dashscope_size: str


def get_settings() -> Settings:
    return Settings(
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        dashscope_base_url=os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1"),
        dashscope_model=os.getenv("DASHSCOPE_IMAGE_MODEL", "wan2.6-t2i"),
        dashscope_size=os.getenv("DASHSCOPE_IMAGE_SIZE", "1280*1280"),
    )

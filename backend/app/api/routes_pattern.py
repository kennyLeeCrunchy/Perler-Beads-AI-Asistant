from __future__ import annotations

import base64
import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image

from app.core.config import DATA_DIR, MARD_PALETTE_PATH, RUNTIME_DIR
from app.core.bundle import generate_pattern_bundle
from app.core.exporter import render_pattern_png
from app.core.image_pipeline import read_clean_reference
from app.core.mask_processor import create_transparent_foreground
from app.core.palette import load_mard_palette, load_palette, load_presets, resolve_palette
from app.core.quantizer import quantize_image
from app.core.schemas import ensure_runtime_path, pattern_counts_for_ui, pattern_to_dict


router = APIRouter(prefix="/api/pattern", tags=["pattern"])
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("/generate")
async def generate_pattern(
    image: UploadFile | None = File(default=None),
    source_path: str | None = Form(default=None),
    brand: str = Form(default="Artkal"),
    width: int = Form(default=48, ge=1, le=200),
    height: int = Form(default=48, ge=1, le=200),
    preset: str = Form(default="221"),
    max_colors: int = Form(default=24, ge=0, le=221),
    similarity_threshold: float = Form(default=0, ge=0, le=100),
    use_transparent_mask: bool = Form(default=False),
) -> dict:
    try:
        input_path = await _resolve_input_image(image=image, source_path=source_path)
        normalized_brand = brand.strip().lower()
        if normalized_brand == "artkal":
            colors = load_palette(DATA_DIR / "artkal_m_series.json")
            presets = load_presets(DATA_DIR / "artkal_presets.json")
            palette = resolve_palette(colors, presets, preset)
        elif normalized_brand == "mard":
            palette = list(load_mard_palette(MARD_PALETTE_PATH).values())
        else:
            raise ValueError("Unsupported palette brand; use Artkal or Mard")
        effective_similarity_threshold = max(similarity_threshold, 18) if use_transparent_mask else similarity_threshold
        with Image.open(input_path) as source:
            source_for_pattern = source
            if use_transparent_mask:
                mask_result = create_transparent_foreground(source)
                if not mask_result.success:
                    raise ValueError(
                        f"透明底处理失败：{mask_result.reason or 'mask quality gate failed'}。"
                        "请使用纯白底、无阴影、无棋盘格的干净主体图。"
                    )
                source_for_pattern = mask_result.image
            pattern = quantize_image(
                source_for_pattern,
                palette=palette,
                width=width,
                height=height,
                max_colors=max_colors,
                similarity_threshold=effective_similarity_threshold,
                remove_bg=use_transparent_mask,
            )
        pattern_id = uuid4().hex
        pattern_path = RUNTIME_DIR / "generated" / f"{pattern_id}.json"
        pattern_path.write_text(json.dumps(pattern_to_dict(pattern), ensure_ascii=False), encoding="utf-8")
        preview_png = render_pattern_png(pattern, cell_size=12)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "pattern_id": pattern_id,
        "brand": "Mard" if normalized_brand == "mard" else "Artkal",
        "width": pattern.width,
        "height": pattern.height,
        "cells": pattern.cells,
        "counts": pattern_counts_for_ui(pattern),
        "preview_data_url": "data:image/png;base64," + base64.b64encode(preview_png).decode("ascii"),
    }


@router.post("/bundle")
async def generate_pattern_bundle_route(
    image: UploadFile | None = File(default=None),
    source_path: str | None = Form(default=None),
    clean_reference_id: str | None = Form(default=None),
    brand: str = Form(default="Mard"),
    preset: str = Form(default="221"),
    max_colors: int = Form(default=20, ge=0, le=221),
    similarity_threshold: float = Form(default=18, ge=0, le=100),
    use_transparent_mask: bool = Form(default=False),
) -> dict:
    try:
        input_path, resolved_reference_id = await _resolve_bundle_input(
            image=image,
            source_path=source_path,
            clean_reference_id=clean_reference_id,
        )
        palette = _resolve_palette(brand, preset)
        with Image.open(input_path) as source:
            bundle = generate_pattern_bundle(
                source,
                palette=palette,
                max_colors=max_colors,
                similarity_threshold=similarity_threshold,
                use_transparent_mask=use_transparent_mask,
                clean_reference_id=resolved_reference_id,
            )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"brand": "Mard" if brand.strip().lower() == "mard" else "Artkal", **bundle}


def _resolve_palette(brand: str, preset: str) -> list:
    normalized_brand = brand.strip().lower()
    if normalized_brand == "artkal":
        colors = load_palette(DATA_DIR / "artkal_m_series.json")
        presets = load_presets(DATA_DIR / "artkal_presets.json")
        return resolve_palette(colors, presets, preset)
    if normalized_brand == "mard":
        return list(load_mard_palette(MARD_PALETTE_PATH).values())
    raise ValueError("Unsupported palette brand; use Artkal or Mard")


async def _resolve_bundle_input(
    *,
    image: UploadFile | None,
    source_path: str | None,
    clean_reference_id: str | None,
) -> tuple[Path, str | None]:
    if clean_reference_id:
        metadata = read_clean_reference(clean_reference_id)
        return ensure_runtime_path(
            RUNTIME_DIR / "generated" / metadata["source_path"],
            RUNTIME_DIR / "generated",
        ), clean_reference_id
    return await _resolve_input_image(image=image, source_path=source_path), None


async def _resolve_input_image(image: UploadFile | None, source_path: str | None) -> Path:
    if image is not None and image.filename:
        suffix = Path(image.filename).suffix.lower() or ".png"
        if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError("Only PNG, JPG, JPEG, and WEBP images are supported")
        contents = await image.read(MAX_UPLOAD_BYTES + 1)
        if len(contents) > MAX_UPLOAD_BYTES:
            raise ValueError("Image exceeds the 10MB upload limit")
        destination = RUNTIME_DIR / "uploads" / f"{uuid4().hex}{suffix}"
        destination.write_bytes(contents)
        try:
            with Image.open(destination) as uploaded:
                uploaded.verify()
        except Exception as exc:
            destination.unlink(missing_ok=True)
            raise ValueError("Uploaded file is not a valid image") from exc
        return destination

    if source_path:
        candidate = Path(source_path)
        if candidate.name != source_path or candidate.suffix.lower() != ".png":
            raise ValueError("Invalid generated image identifier")
        return ensure_runtime_path(RUNTIME_DIR / "generated" / candidate.name, RUNTIME_DIR / "generated")

    raise ValueError("Upload an image or generate one with AI first")

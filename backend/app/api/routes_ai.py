from __future__ import annotations

import os
import io
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel, Field

from app.core.config import RUNTIME_DIR, get_settings
from app.core.dashscope_client import DashScopeClient, build_bead_prompt
from app.core.image_pipeline import PIPELINE_VERSION, create_clean_reference
from app.core.mask_processor import create_transparent_foreground


router = APIRouter(prefix="/api/ai", tags=["ai"])
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class GenerateImageRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)
    transparent_irregular: bool = False


@router.post("/generate")
def generate_image(payload: GenerateImageRequest) -> dict:
    user_prompt = payload.prompt.strip()
    if not user_prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    prompt = build_bead_prompt(user_prompt, transparent_irregular=payload.transparent_irregular)

    settings = get_settings()
    client = DashScopeClient(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
    )
    image_id = uuid4().hex
    destination = RUNTIME_DIR / "generated" / f"{image_id}.png"
    try:
        image_url = client.generate_image_url(
            prompt=prompt,
            model=settings.dashscope_model,
            size=settings.dashscope_size,
        )
        saved_path = client.download_image(image_url, Path(destination))
        processed_path = None
        mask_method = None
        foreground_ratio = None
        if payload.transparent_irregular:
            mask_provider = os.getenv("PINDOU_MASK_PROVIDER", "birefnet").strip()
            allow_fallback = os.getenv("PINDOU_MASK_ALLOW_FALLBACK", "1").strip().lower() in {
                "1",
                "true",
                "yes",
            }
            with Image.open(saved_path) as source:
                mask_result = create_transparent_foreground(
                    source,
                    provider=mask_provider,
                    allow_fallback=allow_fallback,
                )
            if not mask_result.success:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"透明底处理失败：{mask_result.reason or 'mask quality gate failed'}。"
                        "请重新生成更干净的扁平主体图，避免棋盘格、阴影、成品挂饰照片和复杂背景。"
                    ),
                )
            processed_path = RUNTIME_DIR / "generated" / f"{image_id}.transparent.png"
            mask_result.image.save(processed_path, format="PNG")
            mask_method = mask_result.method
            foreground_ratio = mask_result.foreground_ratio
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    response_path = processed_path or saved_path
    return {
        # 保留旧字段名以兼容现有页面，但值是不可越界的生成文件名，不再泄露服务器绝对路径。
        "source_path": response_path.name,
        "raw_source_path": saved_path.name,
        "image_url": f"/runtime/generated/{response_path.name}",
        "raw_image_url": f"/runtime/generated/{saved_path.name}",
        "prompt": user_prompt,
        "final_prompt": prompt,
        "transparent_irregular": payload.transparent_irregular,
        "mask_method": mask_method,
        "foreground_ratio": foreground_ratio,
    }


@router.post("/clean-reference")
async def clean_reference(
    image: UploadFile = File(...),
    mode: str = Form(default="auto"),
    subject_target: str = Form(default=""),
    prompt: str = Form(default=""),
) -> dict:
    if not image.filename:
        raise HTTPException(status_code=400, detail="请上传参考图片")
    suffix = Path(image.filename).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=400, detail="只支持 PNG、JPG、JPEG 和 WEBP 图片")
    contents = await image.read(MAX_UPLOAD_BYTES + 1)
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="图片不能超过 10MB")
    try:
        with Image.open(io.BytesIO(contents)) as uploaded:
            uploaded.verify()
        result = create_clean_reference(
            source_bytes=contents,
            mode=mode,
            subject_target=subject_target,
            user_prompt=prompt,
            output_dir=RUNTIME_DIR / "generated",
        )
    except HTTPException:
        raise
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "clean_reference_id": result.clean_reference_id,
        "task_id": result.task_id,
        "model": result.model,
        "algorithm_version": result.prompt_version,
        "pipeline": PIPELINE_VERSION,
        "ai_passes": 1,
        "source_type": result.source_type,
        "confidence": result.confidence,
        "mask_method": result.mask_method,
        "foreground_ratio": result.foreground_ratio,
        "image_url": f"/runtime/generated/{result.pattern_source_path.name}",
        "raw_image_url": f"/runtime/generated/{result.raw_path.name}",
    }

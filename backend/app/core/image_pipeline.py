from __future__ import annotations

import base64
import io
import json
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
import urllib.request

import numpy as np
from PIL import Image

from .config import RUNTIME_DIR, get_settings
from .mask_processor import create_transparent_foreground


ALGORITHM_VERSION = "bead_ready_52_v2"
PIPELINE_VERSION = "local_classify_single_redraw_three_sizes_v4"


@dataclass(frozen=True)
class EditPrompt:
    positive: str
    negative: str
    effective_style: str
    source_type: str


@dataclass(frozen=True)
class SourceAnalysis:
    source_type: str
    prepared_bytes: bytes
    confidence: float
    subject_bytes: bytes | None = None
    mask_method: str | None = None
    foreground_ratio: float | None = None
    reason: str = ""


@dataclass(frozen=True)
class CleanReference:
    clean_reference_id: str
    task_id: str
    model: str
    raw_path: Path
    pattern_source_path: Path
    transparent_path: Path | None
    source_type: str
    confidence: float
    mask_method: str | None
    foreground_ratio: float | None
    prompt_version: str


COMMON_OUTPUT = """统一输出要求：
- 输出 1:1 正方形高清平滑图，不拉伸主体；需要补边时保住完整内容。
- 这是拼豆网格化之前的视觉预处理，不要生成像素格、马赛克、网格线、圆珠、底板孔、色号或图例。
- 不添加文字、水印、边框、贴纸、装饰或输入图中不存在的内容。
- 目标是 bead_ready_52_v2：缩小到 52×52 后仍能辨认主体，颜色区域连续，轮廓清楚。
"""

COMMON_NEGATIVE = (
    "新增或删除主体，改变身份或物种，改变脸型五官、姿势、服装和道具，任意改构图，拉伸，"
    "文字，水印，边框，像素格，马赛克，网格，坐标，色号，圆形拼豆，塑料珠，底板孔，图例，"
    "粗黑描边，儿童简笔画，密集纹理，细碎渐变，复杂背景，棋盘格，阴影，地面，墙面，成品照片"
)


def build_edit_prompt(
    *,
    mode: str = "auto",
    subject_target: str = "",
    user_prompt: str = "",
) -> EditPrompt:
    normalized_mode = mode.strip().lower() or "auto"
    extra = user_prompt.strip() or "无"
    if normalized_mode not in {"auto", "subject", "scene"}:
        raise ValueError("处理模式只支持 auto、subject 或 scene")

    if normalized_mode == "subject":
        target = subject_target.strip() or "画面中最清晰、最主要的独立主体"
        positive = f"""这是一张有明确独立主体的真实照片。只提取：{target}。
去掉原场景，放在纯白背景 #FFFFFF 上并居中，主体占画面约 70%–82%，保持完整且不贴边。
严格保留身份、物种、外形比例、五官位置、姿势、表情、服装、配饰和关键识别特征。
将主体整理为适合拼豆降采样的商业角色清稿：使用大块连续色面，控制在约 12–16 个视觉主色；
关键轮廓和五官在 52×52 时仍需清楚，不使用粗黑线、细碎发丝或密集小色块。

{COMMON_OUTPUT}
用户补充要求：{extra}"""
        return EditPrompt(positive, COMMON_NEGATIVE, "cartoon", "subject")

    if normalized_mode == "scene":
        positive = f"""执行完整原图保真预处理，不提取主体，不删除、替换或虚化背景。
保留整幅原图的构图、裁切、透视、物体数量、相对位置、主要颜色和光照关系。
只清理压缩噪点、模糊边缘和无意义的近似色变化，将细节归纳为适合网格化的连续色面。

{COMMON_OUTPUT}
用户补充要求：{extra}"""
        return EditPrompt(positive, COMMON_NEGATIVE, "preserve", "scene")

    positive = f"""你正在为照片转拼豆图纸准备清晰参考图。输入图片是唯一视觉依据。
请在内部判断它是已有卡通/插画、完整场景，还是可独立提取的清晰主体，并只执行最合适的分支。
已有插画保留构图和画风；完整场景保留空间层次；明确主体放在纯白背景并保留身份。
所有情况下都要减少无意义纹理，让轮廓和主要色块在 52×52 网格中仍可读。

{COMMON_OUTPUT}
用户补充要求：{extra}"""
    return EditPrompt(positive, COMMON_NEGATIVE, "auto", "auto")


def analyze_source_image(
    source_bytes: bytes,
    *,
    mask_provider: str = "birefnet",
    allow_mask_fallback: bool = True,
) -> SourceAnalysis:
    with Image.open(io.BytesIO(source_bytes)) as opened:
        opened.load()
        image = opened.convert("RGBA")

    if _looks_like_existing_artwork(image):
        return SourceAnalysis(
            source_type="cartoon",
            prepared_bytes=_png_bytes(image),
            confidence=0.82,
            reason="低色彩复杂度或已有透明通道，按已有插画保真清理",
        )

    matte = create_transparent_foreground(
        image,
        provider=mask_provider,
        allow_fallback=allow_mask_fallback,
    )
    if matte.success and _is_independent_subject(matte.image, matte.foreground_ratio):
        return _subject_analysis(matte.image, matte.method, matte.foreground_ratio)

    return SourceAnalysis(
        source_type="scene",
        prepared_bytes=_png_bytes(image.convert("RGB")),
        confidence=0.70,
        mask_method=matte.method,
        foreground_ratio=matte.foreground_ratio,
        reason=matte.reason or "未获得可靠独立主体，按完整场景重绘",
    )


def prepare_subject_image(
    source_bytes: bytes,
    *,
    mask_provider: str = "birefnet",
    allow_mask_fallback: bool = True,
) -> SourceAnalysis:
    with Image.open(io.BytesIO(source_bytes)) as opened:
        opened.load()
        image = opened.convert("RGBA")
    matte = create_transparent_foreground(
        image,
        provider=mask_provider,
        allow_fallback=allow_mask_fallback,
    )
    if not matte.success:
        raise ValueError(f"主体提取失败：{matte.reason or '未获得可靠蒙版'}")
    return _subject_analysis(matte.image, matte.method, matte.foreground_ratio, confidence=1.0)


def create_clean_reference(
    *,
    source_bytes: bytes,
    mode: str,
    subject_target: str,
    user_prompt: str,
    output_dir: Path,
) -> CleanReference:
    settings = get_settings()
    analysis = (
        prepare_subject_image(source_bytes)
        if mode.strip().lower() == "subject"
        else analyze_source_image(source_bytes)
    )
    prompt = build_edit_prompt(
        mode=mode if mode.strip().lower() in {"subject", "scene"} else "auto",
        subject_target=subject_target,
        user_prompt=user_prompt,
    )
    editor = DashScopeImageEditClient(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        model=settings.dashscope_i2i_model,
    )
    task_id, remote_url = editor.edit(
        normalize_image_as_data_url(analysis.prepared_bytes),
        prompt.positive,
        negative_prompt=prompt.negative,
        timeout=settings.dashscope_i2i_timeout,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    reference_id = _new_id()
    raw_path = output_dir / f"{reference_id}.clean.raw.png"
    download_image(remote_url, raw_path)

    transparent_path: Path | None = None
    pattern_source_path = raw_path
    mask_method = analysis.mask_method
    foreground_ratio = analysis.foreground_ratio
    if prompt.source_type == "subject" or analysis.source_type == "subject":
        transparent_path = output_dir / f"{reference_id}.clean.transparent.png"
        with Image.open(raw_path) as raw_image:
            matte = create_transparent_foreground(raw_image, provider="birefnet", allow_fallback=True)
        if not matte.success:
            raise ValueError(f"清稿主体提取失败：{matte.reason or 'mask quality gate failed'}")
        matte.image.save(transparent_path, format="PNG")
        pattern_source_path = transparent_path
        mask_method = matte.method
        foreground_ratio = matte.foreground_ratio

    metadata = {
        "clean_reference_id": reference_id,
        "task_id": task_id,
        "model": editor.model,
        "raw_path": raw_path.name,
        "pattern_source_path": pattern_source_path.name,
        "transparent_path": transparent_path.name if transparent_path else None,
        "source_type": prompt.source_type if prompt.source_type != "auto" else analysis.source_type,
        "confidence": analysis.confidence,
        "mask_method": mask_method,
        "foreground_ratio": foreground_ratio,
        "prompt_version": ALGORITHM_VERSION,
        "pipeline": PIPELINE_VERSION,
        "ai_passes": 1,
        "created_at": int(time.time()),
    }
    (output_dir / f"{reference_id}.clean.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return CleanReference(
        clean_reference_id=reference_id,
        task_id=task_id,
        model=editor.model,
        raw_path=raw_path,
        pattern_source_path=pattern_source_path,
        transparent_path=transparent_path,
        source_type=metadata["source_type"],
        confidence=analysis.confidence,
        mask_method=mask_method,
        foreground_ratio=foreground_ratio,
        prompt_version=ALGORITHM_VERSION,
    )


class DashScopeImageEditClient:
    def __init__(self, api_key: str | None, base_url: str, model: str) -> None:
        if not api_key or api_key.strip() in {"", "sk-your-key-here"}:
            raise RuntimeError("DASHSCOPE_API_KEY is not configured")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def edit(
        self,
        image_data_url: str | list[str],
        prompt: str,
        *,
        negative_prompt: str = "",
        timeout: float = 180,
        poll_interval: float = 3,
    ) -> tuple[str, str]:
        task_id = self.create_task(image_data_url, prompt, negative_prompt)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            payload = self.get_task(task_id)
            output = payload.get("output") or {}
            status = output.get("task_status")
            if status == "SUCCEEDED":
                results = output.get("results") or []
                image_url = next((item.get("url") for item in results if item.get("url")), None)
                if not image_url:
                    raise RuntimeError("图生图已完成，但响应中没有图片地址")
                return task_id, image_url
            if status in {"FAILED", "CANCELED", "UNKNOWN"}:
                raise RuntimeError(f"图生图任务失败：{output.get('message') or status}")
            time.sleep(poll_interval)
        raise TimeoutError("图生图等待超时，请稍后重试或跳过清稿")

    def create_task(self, image_data_url: str | list[str], prompt: str, negative_prompt: str) -> str:
        images = [image_data_url] if isinstance(image_data_url, str) else list(image_data_url)
        payload = self._request_json(
            f"{self.base_url}/services/aigc/image2image/image-synthesis",
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            },
            body=json.dumps({
                "model": self.model,
                "input": {"prompt": prompt, "images": images, "negative_prompt": negative_prompt},
                "parameters": {"prompt_extend": False, "watermark": False, "n": 1},
            }, ensure_ascii=False).encode("utf-8"),
        )
        task_id = (payload.get("output") or {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"DashScope 没有返回图生图 task_id：{payload}")
        return str(task_id)

    def get_task(self, task_id: str) -> dict:
        return self._request_json(
            f"{self.base_url}/tasks/{quote(task_id, safe='')}",
            method="GET",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

    @staticmethod
    def _request_json(url: str, *, method: str, headers: dict[str, str], body: bytes | None = None) -> dict:
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"DashScope HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"无法连接 DashScope：{exc.reason}") from exc
        if payload.get("code"):
            raise RuntimeError(f"DashScope {payload['code']}: {payload.get('message') or '未知错误'}")
        return payload


def normalize_image_as_data_url(source: bytes) -> str:
    with Image.open(io.BytesIO(source)) as opened:
        image = opened.convert("RGB")
        image.thumbnail((1536, 1536), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=95, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(output.getvalue()).decode("ascii")


def download_image(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "pindou-app/0.3"})
    with urllib.request.urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())
    return destination


def read_clean_reference(reference_id: str) -> dict:
    if not reference_id or not reference_id.isalnum() or len(reference_id) != 32:
        raise ValueError("Invalid clean reference identifier")
    metadata_path = RUNTIME_DIR / "generated" / f"{reference_id}.clean.json"
    if not metadata_path.exists():
        raise ValueError("Clean reference does not exist or has expired")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    source_path = RUNTIME_DIR / "generated" / Path(metadata["pattern_source_path"]).name
    if not source_path.exists():
        raise ValueError("Clean reference image is missing")
    metadata["source_path"] = source_path.name
    return metadata


def _subject_analysis(image: Image.Image, method: str, foreground_ratio: float, *, confidence: float = 0.88) -> SourceAnalysis:
    white = Image.new("RGBA", image.size, (255, 255, 255, 255))
    white.alpha_composite(image)
    return SourceAnalysis(
        source_type="subject",
        prepared_bytes=_png_bytes(white.convert("RGB")),
        subject_bytes=_png_bytes(image),
        confidence=confidence,
        mask_method=method,
        foreground_ratio=foreground_ratio,
        reason="用户选择提取主体" if confidence == 1.0 else "本地主体蒙版通过占比与边缘接触门禁",
    )


def _looks_like_existing_artwork(image: Image.Image) -> bool:
    alpha = np.asarray(image.getchannel("A"), dtype=np.uint8)
    if np.any(alpha < 245):
        return True
    sample = np.asarray(image.convert("RGB").resize((96, 96), Image.Resampling.BILINEAR), dtype=np.uint8)
    return np.unique((sample // 16).reshape(-1, 3), axis=0).shape[0] <= 180


def _is_independent_subject(image: Image.Image, foreground_ratio: float) -> bool:
    if not 0.06 <= foreground_ratio <= 0.74:
        return False
    alpha = np.asarray(image.getchannel("A"), dtype=np.uint8) >= 128
    if not np.any(alpha):
        return False
    border = np.concatenate((alpha[0], alpha[-1], alpha[:, 0], alpha[:, -1]))
    ys, xs = np.where(alpha)
    bbox_ratio = ((xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1)) / alpha.size
    return float(np.mean(border)) <= 0.28 and bbox_ratio <= 0.86


def _png_bytes(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _new_id() -> str:
    import uuid

    return uuid.uuid4().hex

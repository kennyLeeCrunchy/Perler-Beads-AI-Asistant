from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_DIR = BACKEND_DIR / "runtime" / "models" / "birefnet-lite-matting"
DEFAULT_MODULES_CACHE = BACKEND_DIR / "runtime" / "hf_modules"
REQUIRED_MODEL_FILES = (
    "BiRefNet_config.py",
    "birefnet.py",
    "config.json",
    "model.safetensors",
)
os.environ.setdefault("HF_MODULES_CACHE", str(DEFAULT_MODULES_CACHE))


@dataclass(frozen=True)
class BiRefNetMattingResult:
    image: Image.Image
    alpha: np.ndarray
    device: str


class BiRefNetModelUnavailable(RuntimeError):
    pass


class BiRefNetLiteMatting:
    def __init__(self, model_dir: Path, *, device: str, resolution: int) -> None:
        self.model_dir = model_dir
        self.resolution = resolution
        self._inference_lock = threading.Lock()

        missing = [name for name in REQUIRED_MODEL_FILES if not (model_dir / name).is_file()]
        if missing:
            raise BiRefNetModelUnavailable(
                f"BiRefNet Lite Matting 本地权重不完整：缺少 {', '.join(missing)}"
            )

        os.environ.setdefault("HF_MODULES_CACHE", str(DEFAULT_MODULES_CACHE))
        DEFAULT_MODULES_CACHE.mkdir(parents=True, exist_ok=True)

        try:
            import torch
            from transformers import AutoModelForImageSegmentation
        except ImportError as exc:
            raise BiRefNetModelUnavailable(
                "BiRefNet 运行依赖未安装，请在 pindou-ai-demo Conda 环境安装模型依赖。"
            ) from exc

        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda" and not torch.cuda.is_available():
            raise BiRefNetModelUnavailable("配置要求使用 CUDA，但当前环境未检测到可用 GPU。")

        self.device = device
        self._torch = torch
        self.dtype = torch.float16 if device == "cuda" else torch.float32
        try:
            self.model = AutoModelForImageSegmentation.from_pretrained(
                model_dir,
                trust_remote_code=True,
                local_files_only=True,
                dtype=self.dtype,
            ).eval().to(device)
        except Exception as exc:
            raise BiRefNetModelUnavailable(f"BiRefNet Lite Matting 加载失败：{exc}") from exc

    def apply(self, image: Image.Image) -> BiRefNetMattingResult:
        torch = self._torch
        rgb = image.convert("RGB")
        original_size = rgb.size
        pixels = np.asarray(
            rgb.resize((self.resolution, self.resolution), Image.Resampling.BILINEAR),
            dtype=np.float32,
        )
        pixels = pixels / 255.0
        pixels = (pixels - np.array([0.485, 0.456, 0.406], dtype=np.float32)) / np.array(
            [0.229, 0.224, 0.225], dtype=np.float32
        )
        tensor = torch.from_numpy(pixels).permute(2, 0, 1).unsqueeze(0)
        tensor = tensor.to(self.device, dtype=self.dtype)

        with self._inference_lock, torch.inference_mode():
            prediction = self.model(tensor)[-1].sigmoid()
            prediction = torch.nn.functional.interpolate(
                prediction,
                size=(original_size[1], original_size[0]),
                mode="bilinear",
                align_corners=False,
            )
            alpha = prediction[0, 0].float().clamp(0, 1).mul(255).byte().cpu().numpy()

        rgba = np.asarray(rgb.convert("RGBA"), dtype=np.uint8).copy()
        rgba[:, :, 3] = alpha
        return BiRefNetMattingResult(
            image=Image.fromarray(rgba, mode="RGBA"),
            alpha=alpha,
            device=self.device,
        )


@lru_cache(maxsize=4)
def get_birefnet_lite_matting(
    model_dir: str,
    device: str = "auto",
    resolution: int = 1024,
) -> BiRefNetLiteMatting:
    return BiRefNetLiteMatting(Path(model_dir), device=device, resolution=resolution)


def create_birefnet_matte(image: Image.Image) -> BiRefNetMattingResult:
    model_dir = os.getenv("PINDOU_BIREFNET_MODEL_DIR", str(DEFAULT_MODEL_DIR)).strip()
    device = os.getenv("PINDOU_BIREFNET_DEVICE", "auto").strip().lower()
    resolution = int(os.getenv("PINDOU_BIREFNET_RESOLUTION", "1024"))
    if resolution < 256 or resolution > 2048 or resolution % 32:
        raise ValueError("PINDOU_BIREFNET_RESOLUTION 必须是 256–2048 之间且可被 32 整除。")
    return get_birefnet_lite_matting(model_dir, device, resolution).apply(image)

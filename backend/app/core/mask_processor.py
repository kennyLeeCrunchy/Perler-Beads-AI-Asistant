from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

from .birefnet_matting import (
    BiRefNetModelUnavailable,
    create_birefnet_matte,
)


@dataclass(frozen=True)
class TransparentForegroundResult:
    image: Image.Image
    method: str
    foreground_pixels: int
    total_pixels: int
    success: bool
    reason: str | None = None

    @property
    def foreground_ratio(self) -> float:
        return self.foreground_pixels / self.total_pixels if self.total_pixels else 0.0


def create_transparent_foreground(
    image: Image.Image,
    *,
    provider: str = "light_background",
    allow_fallback: bool = True,
) -> TransparentForegroundResult:
    if provider == "birefnet":
        try:
            result = create_birefnet_matte(image)
            foreground = result.alpha >= 128
            foreground_pixels = int(np.count_nonzero(foreground))
            total_pixels = int(foreground.size)
            transparent_pixels = int(np.count_nonzero(result.alpha < 250))
            success = foreground_pixels > 0 and transparent_pixels > 0
            return TransparentForegroundResult(
                image=result.image,
                method="birefnet_lite_matting",
                foreground_pixels=foreground_pixels,
                total_pixels=total_pixels,
                success=success,
                reason=None if success else "BiRefNet 输出的 alpha 退化为空白或完全不透明",
            )
        except (BiRefNetModelUnavailable, RuntimeError, ValueError) as exc:
            if not allow_fallback:
                return _failed_result(image, f"BiRefNet Lite Matting 不可用：{exc}")
            fallback = _create_algorithmic_foreground(image)
            return TransparentForegroundResult(
                image=fallback.image,
                method=(
                    "light_background_fallback"
                    if fallback.success
                    else fallback.method
                ),
                foreground_pixels=fallback.foreground_pixels,
                total_pixels=fallback.total_pixels,
                success=fallback.success,
                reason=(
                    f"BiRefNet Lite Matting 不可用，已尝试白底算法：{exc}"
                    if not fallback.success
                    else None
                ),
            )
    if provider != "light_background":
        return _failed_result(image, f"不支持的主体提取 provider：{provider}")
    return _create_algorithmic_foreground(image)


def _create_algorithmic_foreground(image: Image.Image) -> TransparentForegroundResult:
    foreground = _foreground_from_alpha(image)
    method = "alpha"
    if foreground is None:
        foreground = _foreground_from_light_background(image)
        method = "light_background"
    if foreground is None:
        foreground = np.ones((image.height, image.width), dtype=bool)
        method = "none"

    foreground_pixels = int(np.count_nonzero(foreground))
    total_pixels = int(foreground.size)
    foreground_ratio = foreground_pixels / total_pixels if total_pixels else 0.0
    success = method != "none" and foreground_ratio <= 0.75
    reason = None
    if method == "none":
        method = "failed"
        success = False
        reason = "未识别到可移除背景"
    elif foreground_ratio > 0.75:
        method = "failed"
        success = False
        reason = "透明处理后前景占比过高，疑似假透明背景或复杂阴影背景"

    rgba = image.convert("RGBA")
    pixels = np.array(rgba, dtype=np.uint8)
    pixels[:, :, 3] = np.where(foreground, pixels[:, :, 3], 0).astype(np.uint8)
    output = Image.fromarray(pixels)
    return TransparentForegroundResult(
        image=output,
        method=method,
        foreground_pixels=foreground_pixels,
        total_pixels=total_pixels,
        success=success,
        reason=reason,
    )


def _failed_result(image: Image.Image, reason: str) -> TransparentForegroundResult:
    total_pixels = image.width * image.height
    return TransparentForegroundResult(
        image=image.convert("RGBA"),
        method="failed",
        foreground_pixels=total_pixels,
        total_pixels=total_pixels,
        success=False,
        reason=reason,
    )


def _foreground_from_alpha(image: Image.Image, threshold: int = 128) -> np.ndarray | None:
    if "A" not in image.getbands():
        return None
    alpha = np.array(image.getchannel("A"), dtype=np.uint8)
    if np.min(alpha) >= 250:
        return None
    return alpha >= threshold


def _foreground_from_light_background(image: Image.Image) -> np.ndarray | None:
    pixels = np.array(image.convert("RGB"), dtype=np.int16)
    luma = 0.299 * pixels[:, :, 0] + 0.587 * pixels[:, :, 1] + 0.114 * pixels[:, :, 2]
    channel_spread = pixels.max(axis=2) - pixels.min(axis=2)
    edge_color = _median_edge_color(pixels)
    edge_distance = np.sqrt(np.sum((pixels - edge_color) ** 2, axis=2))

    # Text-to-image models often draw fake transparent checkerboards, subtle
    # gray shadows, or bead textures despite the white-background prompt. Treat
    # edge-connected near-neutral light regions as removable background, then
    # keep interior white areas that are not connected to the image border.
    light_neutral = (luma >= 188) & (channel_spread <= 70)
    edge_like = (luma >= 170) & (edge_distance <= 72)
    background_candidate = light_neutral | edge_like
    if not np.any(background_candidate):
        return None

    background = _flood_fill_from_edges(background_candidate)
    if not np.any(background):
        return None
    foreground = ~background
    grabcut_foreground = _foreground_from_grabcut(pixels, background, foreground, luma, channel_spread)
    if grabcut_foreground is not None:
        return grabcut_foreground
    return _refine_foreground_with_subject_seeds(pixels, foreground, luma, channel_spread)


def _median_edge_color(pixels: np.ndarray) -> np.ndarray:
    top = pixels[0, :, :]
    bottom = pixels[-1, :, :]
    left = pixels[:, 0, :]
    right = pixels[:, -1, :]
    edge_pixels = np.concatenate([top, bottom, left, right], axis=0)
    return np.median(edge_pixels, axis=0)


def _refine_foreground_with_subject_seeds(
    pixels: np.ndarray,
    foreground: np.ndarray,
    luma: np.ndarray,
    channel_spread: np.ndarray,
) -> np.ndarray:
    total_pixels = foreground.size
    min_component_area = max(16, int(total_pixels * 0.0008))
    important_component_area = max(64, int(total_pixels * 0.003))

    # Use colorful regions and dark outlines as high-confidence subject seeds.
    # Neutral gray shadows usually have low channel spread, so they are excluded
    # here even when the first background pass classified them as foreground.
    subject_seed = foreground & (
        ((channel_spread >= 42) & (luma <= 248))
        | (luma <= 64)
    )
    if int(np.count_nonzero(subject_seed)) < min_component_area:
        return _remove_small_components(foreground, min_component_area, important_component_area)

    subject_seed = _remove_small_components(subject_seed, min_component_area, important_component_area)
    expanded_seed = _dilate(subject_seed, iterations=5)
    closed_subject = _fill_enclosed_holes(expanded_seed) & foreground
    refined = closed_subject | (subject_seed & foreground)
    refined = _remove_far_neutral_regions(refined, subject_seed, luma, channel_spread)
    refined = _remove_small_components(refined, min_component_area, important_component_area)
    refined = _fill_enclosed_holes(refined)
    if int(np.count_nonzero(refined)) < min_component_area:
        return _remove_small_components(foreground, min_component_area, important_component_area)
    return refined


def _foreground_from_grabcut(
    pixels: np.ndarray,
    background: np.ndarray,
    foreground: np.ndarray,
    luma: np.ndarray,
    channel_spread: np.ndarray,
) -> np.ndarray | None:
    try:
        import cv2
    except ImportError:
        return None

    subject_seed = foreground & (
        ((channel_spread >= 42) & (luma <= 248))
        | (luma <= 64)
    )
    if int(np.count_nonzero(subject_seed)) < max(16, int(subject_seed.size * 0.0008)):
        return None

    height, width = foreground.shape
    min_component_area = max(16, int(foreground.size * 0.0008))
    important_component_area = max(64, int(foreground.size * 0.003))

    grabcut_mask = np.full((height, width), cv2.GC_PR_BGD, dtype=np.uint8)
    grabcut_mask[background] = cv2.GC_BGD
    grabcut_mask[foreground] = cv2.GC_PR_FGD
    grabcut_mask[_dilate(subject_seed, iterations=2)] = cv2.GC_FGD

    bg_model = np.zeros((1, 65), dtype=np.float64)
    fg_model = np.zeros((1, 65), dtype=np.float64)
    try:
        cv2.grabCut(
            pixels.astype(np.uint8),
            grabcut_mask,
            None,
            bg_model,
            fg_model,
            4,
            cv2.GC_INIT_WITH_MASK,
        )
    except cv2.error:
        return None

    refined = (grabcut_mask == cv2.GC_FGD) | (grabcut_mask == cv2.GC_PR_FGD)
    refined &= foreground
    refined = _remove_far_neutral_regions(refined, subject_seed, luma, channel_spread)
    refined = _remove_small_components(refined, min_component_area, important_component_area)
    refined = _fill_enclosed_holes(refined)
    if int(np.count_nonzero(refined)) < min_component_area:
        return None
    return refined


def _remove_far_neutral_regions(
    mask: np.ndarray,
    subject_seed: np.ndarray,
    luma: np.ndarray,
    channel_spread: np.ndarray,
) -> np.ndarray:
    try:
        import cv2
    except ImportError:
        return mask

    if not np.any(subject_seed):
        return mask
    distance_to_seed = cv2.distanceTransform((~subject_seed).astype(np.uint8), cv2.DIST_L2, 5)
    far_neutral = (
        mask
        & (channel_spread <= 36)
        & (luma <= 230)
        & (distance_to_seed >= 28)
    )
    if not np.any(far_neutral):
        return mask
    output = mask.copy()
    output[far_neutral] = False
    return output


def _dilate(mask: np.ndarray, iterations: int = 1) -> np.ndarray:
    output = mask
    for _ in range(iterations):
        padded = np.pad(output, 1, mode="constant", constant_values=False)
        output = (
            padded[1:-1, 1:-1]
            | padded[:-2, 1:-1]
            | padded[2:, 1:-1]
            | padded[1:-1, :-2]
            | padded[1:-1, 2:]
            | padded[:-2, :-2]
            | padded[:-2, 2:]
            | padded[2:, :-2]
            | padded[2:, 2:]
        )
    return output


def _fill_enclosed_holes(mask: np.ndarray) -> np.ndarray:
    exterior = _flood_fill_from_edges(~mask)
    return ~exterior


def _remove_small_components(
    mask: np.ndarray,
    min_area: int,
    important_area: int,
) -> np.ndarray:
    height, width = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    kept = np.zeros_like(mask, dtype=bool)
    components: list[tuple[int, list[tuple[int, int]]]] = []

    for start_y, start_x in np.argwhere(mask):
        y0 = int(start_y)
        x0 = int(start_x)
        if visited[y0, x0]:
            continue
        stack = [(y0, x0)]
        visited[y0, x0] = True
        points: list[tuple[int, int]] = []
        while stack:
            y_pos, x_pos = stack.pop()
            points.append((y_pos, x_pos))
            for next_y, next_x in (
                (y_pos - 1, x_pos),
                (y_pos + 1, x_pos),
                (y_pos, x_pos - 1),
                (y_pos, x_pos + 1),
            ):
                if (
                    0 <= next_y < height
                    and 0 <= next_x < width
                    and mask[next_y, next_x]
                    and not visited[next_y, next_x]
                ):
                    visited[next_y, next_x] = True
                    stack.append((next_y, next_x))
        components.append((len(points), points))

    if not components:
        return kept
    largest_area = max(area for area, _ in components)
    for area, points in components:
        if area == largest_area or area >= important_area or area >= min_area and area >= largest_area * 0.04:
            for y_pos, x_pos in points:
                kept[y_pos, x_pos] = True
    return kept


def _flood_fill_from_edges(candidate: np.ndarray) -> np.ndarray:
    height, width = candidate.shape
    background = np.zeros_like(candidate, dtype=bool)
    stack: list[tuple[int, int]] = []

    def push(y_pos: int, x_pos: int) -> None:
        if 0 <= y_pos < height and 0 <= x_pos < width and candidate[y_pos, x_pos] and not background[y_pos, x_pos]:
            background[y_pos, x_pos] = True
            stack.append((y_pos, x_pos))

    for x_pos in range(width):
        push(0, x_pos)
        push(height - 1, x_pos)
    for y_pos in range(1, height - 1):
        push(y_pos, 0)
        push(y_pos, width - 1)

    while stack:
        y_pos, x_pos = stack.pop()
        push(y_pos - 1, x_pos)
        push(y_pos + 1, x_pos)
        push(y_pos, x_pos - 1)
        push(y_pos, x_pos + 1)
    return background

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass

import numpy as np
from PIL import Image

from .perceptual_color import perceptual_pairwise_rgb
from .quantizer import BeadPattern


@dataclass(frozen=True)
class PatternQualityReport:
    score: int
    passed: bool
    feedback: list[str]
    filled_ratio: float
    largest_component_ratio: float
    enclosed_hole_ratio: float
    small_island_ratio: float
    fragmented_color_ratio: float
    border_touch_count: int


@dataclass(frozen=True)
class ColorFidelityReport:
    score: int
    mean_delta_e: float
    p90_delta_e: float
    alpha_iou: float
    feedback: list[str]


def assess_pattern_quality(
    pattern: BeadPattern,
    *,
    max_colors: int,
    pass_score: int = 72,
    require_transparent_background: bool = True,
) -> PatternQualityReport:
    filled = [[cell is not None for cell in row] for row in pattern.cells]
    filled_count = sum(sum(row) for row in filled)
    total = max(1, pattern.width * pattern.height)
    filled_ratio = filled_count / total
    components = _grid_components(filled, target=True)
    component_sizes = sorted((len(component) for component in components), reverse=True)
    largest_component_ratio = component_sizes[0] / filled_count if filled_count else 0.0
    small_island_cells = sum(size for size in component_sizes[1:] if size <= 4)
    small_island_ratio = small_island_cells / filled_count if filled_count else 1.0

    enclosed_hole_cells = 0
    for component in _grid_components(filled, target=False):
        if not any(x in {0, pattern.width - 1} or y in {0, pattern.height - 1} for y, x in component):
            enclosed_hole_cells += len(component)
    enclosed_hole_ratio = enclosed_hole_cells / filled_count if filled_count else 1.0

    fragmented_cells = 0
    for y, row in enumerate(pattern.cells):
        for x, code in enumerate(row):
            if code is not None and not any(pattern.cells[ny][nx] == code for ny, nx in _neighbors(y, x, pattern.height, pattern.width)):
                fragmented_cells += 1
    fragmented_color_ratio = fragmented_cells / filled_count if filled_count else 1.0
    border_touch_count = sum(filled[0]) + sum(filled[-1]) if filled else 0
    border_touch_count += sum(row[0] + row[-1] for row in filled[1:-1]) if pattern.width else 0

    score = 100
    feedback: list[str] = []
    if require_transparent_background and filled_ratio < 0.18:
        score -= min(30, round((0.18 - filled_ratio) * 160))
        feedback.append("主体在图纸中太小")
    elif require_transparent_background and filled_ratio > 0.88:
        score -= min(25, round((filled_ratio - 0.88) * 180))
        feedback.append("主体过满或背景未清除")
    if require_transparent_background and largest_component_ratio < 0.92:
        score -= min(28, round((0.92 - largest_component_ratio) * 80))
        feedback.append("主体存在断裂区域")
    if require_transparent_background and enclosed_hole_ratio > 0.015:
        score -= min(38, 8 + round(enclosed_hole_ratio * 100))
        feedback.append("主体内部出现异常镂空")
    if require_transparent_background and border_touch_count:
        score -= min(15, 4 + border_touch_count // 2)
        feedback.append("主体触碰图纸边缘")
    if small_island_ratio > 0.01:
        score -= min(18, round(small_island_ratio * 100))
        feedback.append("存在较多孤立拼豆")
    if fragmented_color_ratio > 0.08:
        score -= min(18, round(fragmented_color_ratio * 70))
        feedback.append("单颗碎色过多")
    color_count = len(pattern.color_counts)
    if color_count < 3:
        score -= 8
        feedback.append("颜色层次过少")
    elif color_count > max_colors:
        score -= min(15, color_count - max_colors)
        feedback.append("工作色超过限制")
    score = max(0, min(100, score))
    severe = filled_count == 0 or (
        require_transparent_background
        and (enclosed_hole_ratio > 0.08 or largest_component_ratio < 0.75 or filled_ratio < 0.1 or filled_ratio > 0.95)
    )
    return PatternQualityReport(
        score=score,
        passed=score >= pass_score and not severe,
        feedback=feedback[:4],
        filled_ratio=round(filled_ratio, 4),
        largest_component_ratio=round(largest_component_ratio, 4),
        enclosed_hole_ratio=round(enclosed_hole_ratio, 4),
        small_island_ratio=round(small_island_ratio, 4),
        fragmented_color_ratio=round(fragmented_color_ratio, 4),
        border_touch_count=border_touch_count,
    )


def assess_color_fidelity(source: Image.Image, pattern: BeadPattern) -> ColorFidelityReport:
    rgba = np.asarray(source.convert("RGBA"), dtype=np.uint8)
    height_px, width_px = rgba.shape[:2]
    color_by_code = {code: color.rgb for code, color in pattern.colors.items()}
    grid_rgb = np.zeros((pattern.height, pattern.width, 3), dtype=np.uint8)
    grid_alpha = np.zeros((pattern.height, pattern.width), dtype=np.uint8)
    for y, row in enumerate(pattern.cells):
        for x, code in enumerate(row):
            if code is not None and code in color_by_code:
                grid_rgb[y, x] = color_by_code[code]
                grid_alpha[y, x] = 255
    reconstructed_rgb = np.asarray(
        Image.fromarray(grid_rgb, mode="RGB").resize((width_px, height_px), Image.Resampling.NEAREST),
        dtype=np.uint8,
    )
    reconstructed_alpha = np.asarray(
        Image.fromarray(grid_alpha, mode="L").resize((width_px, height_px), Image.Resampling.NEAREST),
        dtype=np.uint8,
    )
    source_mask = rgba[:, :, 3] >= 128
    pattern_mask = reconstructed_alpha >= 128
    union = np.count_nonzero(source_mask | pattern_mask)
    intersection = np.count_nonzero(source_mask & pattern_mask)
    alpha_iou = intersection / union if union else 0.0
    compare_mask = source_mask & pattern_mask
    if not np.any(compare_mask):
        return ColorFidelityReport(0, 100.0, 100.0, round(alpha_iou, 4), ["主体与图纸没有有效重叠"])
    delta_e = perceptual_pairwise_rgb(
        rgba[:, :, :3][compare_mask].astype(np.float64),
        reconstructed_rgb[compare_mask].astype(np.float64),
        strategy="ciede2000",
    )
    mean_delta_e = float(np.mean(delta_e))
    p90_delta_e = float(np.percentile(delta_e, 90))
    score = max(0, min(100, round(100 - mean_delta_e * 1.35 - p90_delta_e * 0.22 - (1 - alpha_iou) * 35)))
    feedback: list[str] = []
    if mean_delta_e > 20:
        feedback.append("整体颜色重建误差较高")
    if p90_delta_e > 35:
        feedback.append("局部颜色失真明显")
    if alpha_iou < 0.88:
        feedback.append("轮廓与原始主体偏差较大")
    return ColorFidelityReport(score, round(mean_delta_e, 2), round(p90_delta_e, 2), round(alpha_iou, 4), feedback)


def report_to_dict(report: PatternQualityReport | ColorFidelityReport) -> dict:
    return asdict(report)


def _neighbors(y: int, x: int, height: int, width: int):
    for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
        if 0 <= ny < height and 0 <= nx < width:
            yield ny, nx


def _grid_components(filled: list[list[bool]], *, target: bool) -> list[list[tuple[int, int]]]:
    height = len(filled)
    width = len(filled[0]) if height else 0
    visited: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for y in range(height):
        for x in range(width):
            if filled[y][x] != target or (y, x) in visited:
                continue
            component: list[tuple[int, int]] = []
            queue = deque([(y, x)])
            visited.add((y, x))
            while queue:
                cy, cx = queue.popleft()
                component.append((cy, cx))
                for neighbor in _neighbors(cy, cx, height, width):
                    if neighbor in visited:
                        continue
                    ny, nx = neighbor
                    if filled[ny][nx] == target:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(component)
    return components

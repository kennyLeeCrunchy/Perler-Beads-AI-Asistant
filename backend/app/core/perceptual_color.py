from __future__ import annotations

from functools import lru_cache
from typing import Literal

import numpy as np

from .color_match import rgb_array_to_lab


ColorDistanceStrategy = Literal["ciede2000", "oklab", "delta_e_76"]


def normalize_strategy(strategy: str) -> ColorDistanceStrategy:
    normalized = strategy.strip().lower()
    if normalized not in {"ciede2000", "oklab", "delta_e_76"}:
        raise ValueError("颜色距离只支持 ciede2000、oklab 或 delta_e_76")
    return normalized  # type: ignore[return-value]


def rgb_array_to_oklab(rgb_array: np.ndarray) -> np.ndarray:
    rgb = np.asarray(rgb_array, dtype=np.float64) / 255.0
    rgb = np.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    lms = rgb @ np.array([
        [0.4122214708, 0.5363325363, 0.0514459929],
        [0.2119034982, 0.6806995451, 0.1073969566],
        [0.0883024619, 0.2817188376, 0.6299787005],
    ]).T
    lms_root = np.cbrt(lms)
    return lms_root @ np.array([
        [0.2104542553, 0.7936177850, -0.0040720468],
        [1.9779984951, -2.4285922050, 0.4505937099],
        [0.0259040371, 0.7827717662, -0.8086757660],
    ]).T


@lru_cache(maxsize=128)
def _cached_palette_space(
    rgb_values: tuple[tuple[int, int, int], ...],
    strategy: ColorDistanceStrategy,
) -> np.ndarray:
    rgb = np.asarray(rgb_values, dtype=np.float64)
    if strategy == "oklab":
        return rgb_array_to_oklab(rgb)
    return rgb_array_to_lab(rgb)


def perceptual_distance_matrix(
    source_rgb: np.ndarray,
    palette_rgb: np.ndarray,
    *,
    strategy: str = "ciede2000",
) -> np.ndarray:
    selected = normalize_strategy(strategy)
    source = np.asarray(source_rgb, dtype=np.float64).reshape(-1, 3)
    palette = np.asarray(palette_rgb, dtype=np.int64).reshape(-1, 3)
    palette_key = tuple(tuple(int(channel) for channel in row) for row in palette)
    palette_space = _cached_palette_space(palette_key, selected)
    if selected == "oklab":
        source_space = rgb_array_to_oklab(source)
        return np.linalg.norm(source_space[:, None, :] - palette_space[None, :, :], axis=2) * 100.0
    source_lab = rgb_array_to_lab(source)
    if selected == "delta_e_76":
        return np.linalg.norm(source_lab[:, None, :] - palette_space[None, :, :], axis=2)
    return ciede2000_distances(source_lab, palette_space)


def perceptual_pairwise_rgb(
    left_rgb: np.ndarray,
    right_rgb: np.ndarray,
    *,
    strategy: str = "ciede2000",
) -> np.ndarray:
    selected = normalize_strategy(strategy)
    left = np.asarray(left_rgb, dtype=np.float64).reshape(-1, 3)
    right = np.asarray(right_rgb, dtype=np.float64).reshape(-1, 3)
    if left.shape != right.shape:
        raise ValueError("逐项颜色比较要求两侧形状一致")
    if selected == "oklab":
        return np.linalg.norm(rgb_array_to_oklab(left) - rgb_array_to_oklab(right), axis=1) * 100.0
    left_lab = rgb_array_to_lab(left)
    right_lab = rgb_array_to_lab(right)
    if selected == "delta_e_76":
        return np.linalg.norm(left_lab - right_lab, axis=1)
    return _ciede2000(left_lab, right_lab)


def ciede2000_distances(source_lab: np.ndarray, palette_lab: np.ndarray) -> np.ndarray:
    left = np.asarray(source_lab, dtype=np.float64)[:, None, :]
    right = np.asarray(palette_lab, dtype=np.float64)[None, :, :]
    return _ciede2000(left, right)


def _ciede2000(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    l1, a1, b1 = left[..., 0], left[..., 1], left[..., 2]
    l2, a2, b2 = right[..., 0], right[..., 1], right[..., 2]
    c1, c2 = np.hypot(a1, b1), np.hypot(a2, b2)
    avg_c = (c1 + c2) / 2.0
    g = 0.5 * (1.0 - np.sqrt(avg_c**7 / (avg_c**7 + 25.0**7)))
    a1p, a2p = (1.0 + g) * a1, (1.0 + g) * a2
    c1p, c2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    avg_cp = (c1p + c2p) / 2.0
    h1p = np.mod(np.degrees(np.arctan2(b1, a1p)), 360.0)
    h2p = np.mod(np.degrees(np.arctan2(b2, a2p)), 360.0)
    h1p = np.where((a1p == 0) & (b1 == 0), 0.0, h1p)
    h2p = np.where((a2p == 0) & (b2 == 0), 0.0, h2p)
    dl, dc = l2 - l1, c2p - c1p
    dh_angle = h2p - h1p
    dh_angle = np.where(dh_angle > 180.0, dh_angle - 360.0, dh_angle)
    dh_angle = np.where(dh_angle < -180.0, dh_angle + 360.0, dh_angle)
    dh_angle = np.where((c1p * c2p) == 0, 0.0, dh_angle)
    dh = 2.0 * np.sqrt(c1p * c2p) * np.sin(np.radians(dh_angle / 2.0))
    avg_l = (l1 + l2) / 2.0
    hue_sum = h1p + h2p
    avg_h = np.where(
        (c1p * c2p) == 0,
        hue_sum,
        np.where(
            np.abs(h1p - h2p) <= 180.0,
            hue_sum / 2.0,
            np.where(hue_sum < 360.0, (hue_sum + 360.0) / 2.0, (hue_sum - 360.0) / 2.0),
        ),
    )
    t = 1.0 - 0.17 * np.cos(np.radians(avg_h - 30.0)) + 0.24 * np.cos(np.radians(2.0 * avg_h)) + 0.32 * np.cos(np.radians(3.0 * avg_h + 6.0)) - 0.20 * np.cos(np.radians(4.0 * avg_h - 63.0))
    dt = 30.0 * np.exp(-(((avg_h - 275.0) / 25.0) ** 2))
    rc = 2.0 * np.sqrt(avg_cp**7 / (avg_cp**7 + 25.0**7))
    sl = 1.0 + (0.015 * (avg_l - 50.0) ** 2) / np.sqrt(20.0 + (avg_l - 50.0) ** 2)
    sc, sh = 1.0 + 0.045 * avg_cp, 1.0 + 0.015 * avg_cp * t
    rt = -np.sin(np.radians(2.0 * dt)) * rc
    lt, ct, ht = dl / sl, dc / sc, dh / sh
    return np.sqrt(np.maximum(0.0, lt**2 + ct**2 + ht**2 + rt * ct * ht))

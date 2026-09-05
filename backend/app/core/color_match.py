from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from .palette import PaletteColor


def _rgb_to_xyz(red: float, green: float, blue: float) -> tuple[float, float, float]:
    red_lin = red / 255.0
    green_lin = green / 255.0
    blue_lin = blue / 255.0

    def linearize(channel: float) -> float:
        if channel > 0.04045:
            return ((channel + 0.055) / 1.055) ** 2.4
        return channel / 12.92

    red_lin = linearize(red_lin)
    green_lin = linearize(green_lin)
    blue_lin = linearize(blue_lin)

    return (
        red_lin * 0.4124564 + green_lin * 0.3575761 + blue_lin * 0.1804375,
        red_lin * 0.2126729 + green_lin * 0.7151522 + blue_lin * 0.0721750,
        red_lin * 0.0193339 + green_lin * 0.1191920 + blue_lin * 0.9503041,
    )


def _xyz_to_lab(x_val: float, y_val: float, z_val: float) -> tuple[float, float, float]:
    ref_x, ref_y, ref_z = 0.95047, 1.00000, 1.08883

    def transform(value: float) -> float:
        delta = 6.0 / 29.0
        if value > delta**3:
            return value ** (1.0 / 3.0)
        return value / (3.0 * delta * delta) + 4.0 / 29.0

    fx = transform(x_val / ref_x)
    fy = transform(y_val / ref_y)
    fz = transform(z_val / ref_z)

    return (
        116.0 * fy - 16.0,
        500.0 * (fx - fy),
        200.0 * (fy - fz),
    )


@lru_cache(maxsize=8192)
def rgb_to_lab(red: int, green: int, blue: int) -> tuple[float, float, float]:
    return _xyz_to_lab(*_rgb_to_xyz(float(red), float(green), float(blue)))


def rgb_array_to_lab(rgb_array: np.ndarray) -> np.ndarray:
    rgb = rgb_array.astype(np.float64) / 255.0
    mask = rgb > 0.04045
    rgb_lin = np.where(mask, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)

    matrix = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ]
    )
    xyz = rgb_lin @ matrix.T
    xyz_norm = xyz / np.array([0.95047, 1.00000, 1.08883])

    delta = 6.0 / 29.0
    mask = xyz_norm > delta**3
    f_xyz = np.where(mask, np.cbrt(xyz_norm), xyz_norm / (3.0 * delta * delta) + 4.0 / 29.0)

    return np.stack(
        [
            116.0 * f_xyz[:, 1] - 16.0,
            500.0 * (f_xyz[:, 0] - f_xyz[:, 1]),
            200.0 * (f_xyz[:, 1] - f_xyz[:, 2]),
        ],
        axis=-1,
    )


def lab_distance(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    delta_l = left[0] - right[0]
    delta_a = left[1] - right[1]
    delta_b = left[2] - right[2]
    return math.sqrt(delta_l * delta_l + delta_a * delta_a + delta_b * delta_b)


def color_distance(
    left: tuple[int, int, int],
    right: tuple[int, int, int],
    *,
    strategy: str = "ciede2000",
) -> float:
    from .perceptual_color import perceptual_pairwise_rgb

    return float(
        perceptual_pairwise_rgb(
            np.asarray([left]),
            np.asarray([right]),
            strategy=strategy,
        )[0]
    )


def nearest_color(
    rgb: tuple[int, int, int],
    palette: list[PaletteColor],
    *,
    strategy: str = "ciede2000",
) -> PaletteColor:
    if not palette:
        raise ValueError("Palette cannot be empty")
    from .perceptual_color import perceptual_distance_matrix

    distances = perceptual_distance_matrix(
        np.asarray([rgb]),
        np.asarray([color.rgb for color in palette]),
        strategy=strategy,
    )
    return palette[int(np.argmin(distances[0]))]

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageColor, ImageEnhance

from .color_match import color_distance, nearest_color
from .perceptual_color import perceptual_distance_matrix
from .palette import PaletteColor


@dataclass(frozen=True)
class BeadPattern:
    width: int
    height: int
    cells: list[list[str | None]]
    color_counts: dict[str, int]
    colors: dict[str, PaletteColor]


def quantize_image(
    image: Image.Image,
    palette: list[PaletteColor],
    width: int,
    height: int,
    max_colors: int = 0,
    use_dithering: bool = False,
    similarity_threshold: float = 0,
    remove_bg: bool = False,
    contrast: float = 0.0,
    saturation: float = 0.0,
    sharpness: float = 0.0,
    auto_cleanup: bool = True,
    cleanup_min_ratio: float = 0.005,
    smooth_edges: bool = True,
    preprocess: bool = True,
) -> BeadPattern:
    """Convert an image to a bead matrix using the BeadCraft mosaic pipeline.

    The pipeline intentionally separates coarse color blocking from detail preservation.
    A per-cell mode-pool gives stable large color regions, then dark detail protection
    restores small facial/outline features that are too thin to win the mode vote.
    """
    if width < 1 or height < 1:
        raise ValueError("Pattern width and height must be positive")
    if not palette:
        raise ValueError("Palette cannot be empty")

    # Transparent-mode conversion uses a foreground mask before color statistics,
    # so empty/background cells never enter palette counts or material counts.
    alpha_mask = _build_alpha_cell_mask(image, width, height) if remove_bg else None
    background_mask = (
        _build_light_background_cell_mask(image, width, height)
        if remove_bg and alpha_mask is None
        else None
    )
    source = image.convert("RGB")
    if preprocess:
        source = _preprocess_image(source, contrast, saturation, sharpness)
        source = _consolidate_extremes(source)

    # The RGB values underneath a transparent pixel are not visible, but used to
    # influence palette selection here. In subject mode that commonly made a large
    # white/gray transparent canvas consume color slots. Restrict color statistics
    # to visible foreground while keeping the later soft-alpha cell mask unchanged.
    selection_alpha = image.getchannel("A") if alpha_mask is not None else None
    sub_palette_size = (
        max_colors
        if max_colors > 0
        else _estimate_color_count(source, width, height, selection_alpha)
    )
    sub_palette_size = max(1, min(len(palette), sub_palette_size))
    sub_palette = _select_top_n_colors(
        source,
        palette,
        sub_palette_size,
        selection_alpha,
    )
    palette_image = _build_pil_palette_image(sub_palette)

    pool_factor = 4
    mid_width = width * pool_factor
    mid_height = height * pool_factor
    mid_image = source.resize((mid_width, mid_height), Image.Resampling.LANCZOS)

    # Detect dark micro-features on the high-resolution intermediate image before
    # quantization and smoothing can erase them. This protects eyes, noses, mouths,
    # and thin outlines on mostly light/orange/white cells.
    # Detail overrides must use the selected working palette. Using the full palette
    # here could re-introduce many one-off colors after max-color capping.
    dark_detail_codes = _build_dark_detail_codes(
        mid_image,
        sub_palette,
        width,
        height,
        pool_factor,
    )
    dither = Image.Dither.FLOYDSTEINBERG if use_dithering else Image.Dither.NONE
    quantized = mid_image.quantize(palette=palette_image, method=Image.Quantize.MEDIANCUT, dither=dither)

    quantized_indices = np.array(quantized, dtype=np.uint8)
    blocks = quantized_indices.reshape(height, pool_factor, width, pool_factor)
    blocks = blocks.transpose(0, 2, 1, 3).reshape(height, width, pool_factor * pool_factor)

    grid_indices = np.zeros((height, width), dtype=np.uint8)
    for y_pos in range(height):
        for x_pos in range(width):
            grid_indices[y_pos, x_pos] = np.bincount(
                blocks[y_pos, x_pos],
                minlength=256,
            ).argmax()

    palette_data = quantized.getpalette()
    palette_array = np.array(palette_data[: 256 * 3], dtype=np.uint8).reshape(256, 3)
    grid_rgb = palette_array[grid_indices]
    rgb_to_code = {color.rgb: color.code for color in sub_palette}

    code_matrix: list[list[str | None]] = []
    for y_pos in range(height):
        row: list[str | None] = []
        for x_pos in range(width):
            rgb = tuple(int(value) for value in grid_rgb[y_pos, x_pos])
            code = rgb_to_code.get(rgb)
            if code is None:
                code = nearest_color(rgb, sub_palette).code
            row.append(code)
        code_matrix.append(row)

    if alpha_mask is not None:
        code_matrix = _apply_alpha_mask(code_matrix, alpha_mask)
    if background_mask is not None:
        code_matrix = _apply_alpha_mask(code_matrix, background_mask)
    total_pixels = width * height
    if auto_cleanup:
        code_matrix = _cleanup_rare_colors(
            code_matrix,
            palette,
            total_pixels,
            min_ratio=max(0.0, cleanup_min_ratio),
        )
    if similarity_threshold > 0:
        code_matrix = _merge_similar_colors(code_matrix, palette, similarity_threshold)
    if max_colors > 0:
        code_matrix = _cap_max_colors(code_matrix, palette, max_colors)
    if smooth_edges:
        code_matrix = _smooth_edges(code_matrix, palette)

    # Apply detail overrides after smoothing. If this ran earlier, smoothing would
    # treat isolated black mouth/eye cells as noise and replace them again.
    code_matrix = _apply_detail_codes(code_matrix, dark_detail_codes)
    if remove_bg and alpha_mask is None and background_mask is None:
        code_matrix = _remove_background_flood_fill(code_matrix)

    color_counts = Counter(code for row in code_matrix for code in row if code is not None)
    used_colors = {color.code: color for color in palette if color.code in color_counts}
    return BeadPattern(
        width=width,
        height=height,
        cells=code_matrix,
        color_counts=dict(sorted(color_counts.items())),
        colors=used_colors,
    )


def _build_alpha_cell_mask(image: Image.Image, width: int, height: int, threshold: int = 128) -> list[list[bool]] | None:
    if "A" not in image.getbands():
        return None
    pool_factor = 4
    alpha = image.getchannel("A").resize((width * pool_factor, height * pool_factor), Image.Resampling.LANCZOS)
    alpha_values = np.array(alpha, dtype=np.uint8)
    blocks = alpha_values.reshape(height, pool_factor, width, pool_factor)
    blocks = blocks.transpose(0, 2, 1, 3).reshape(height, width, pool_factor * pool_factor)
    coverage = blocks >= threshold
    return [[bool(np.mean(coverage[y_pos, x_pos]) >= 0.5) for x_pos in range(width)] for y_pos in range(height)]


def _build_dark_detail_codes(
    mid_image: Image.Image,
    palette: list[PaletteColor],
    width: int,
    height: int,
    pool_factor: int,
    min_coverage: float = 0.08,
) -> list[list[str | None]]:
    """Return per-cell palette overrides for near-black facial and outline details.

    Mode-pooling is good for flat color regions, but it misses strokes that occupy
    only a small part of a bead cell. A cell is marked as a dark detail when at least
    ``min_coverage`` of its high-resolution samples are near black. The override uses
    the nearest real palette color rather than hard-coding H7, so it still respects
    the selected Artkal preset.
    """
    pixels = np.array(mid_image.convert("RGB"), dtype=np.uint8)
    luma = 0.299 * pixels[:, :, 0] + 0.587 * pixels[:, :, 1] + 0.114 * pixels[:, :, 2]
    max_channel = pixels.max(axis=2)
    dark_pixels = (luma <= 85) & (max_channel <= 145)
    dark_blocks = dark_pixels.reshape(height, pool_factor, width, pool_factor)
    dark_blocks = dark_blocks.transpose(0, 2, 1, 3).reshape(height, width, pool_factor * pool_factor)
    rgb_blocks = pixels.reshape(height, pool_factor, width, pool_factor, 3)
    rgb_blocks = rgb_blocks.transpose(0, 2, 1, 3, 4).reshape(height, width, pool_factor * pool_factor, 3)

    detail_codes: list[list[str | None]] = []
    for y_pos in range(height):
        row: list[str | None] = []
        for x_pos in range(width):
            mask = dark_blocks[y_pos, x_pos]
            if np.mean(mask) >= min_coverage:
                mean_rgb = tuple(int(value) for value in np.mean(rgb_blocks[y_pos, x_pos][mask], axis=0))
                row.append(nearest_color(mean_rgb, palette).code)
            else:
                row.append(None)
        detail_codes.append(row)
    return detail_codes


def _apply_detail_codes(
    cells: list[list[str | None]],
    detail_codes: list[list[str | None]],
) -> list[list[str | None]]:
    return [
        [detail_code if code is not None and detail_code is not None else code for code, detail_code in zip(row, detail_row)]
        for row, detail_row in zip(cells, detail_codes)
    ]


def _build_light_background_cell_mask(image: Image.Image, width: int, height: int) -> list[list[bool]] | None:
    pool_factor = 4
    rgb_image = image.convert("RGB").resize((width * pool_factor, height * pool_factor), Image.Resampling.LANCZOS)
    pixels = np.array(rgb_image, dtype=np.int16)
    luma = 0.299 * pixels[:, :, 0] + 0.587 * pixels[:, :, 1] + 0.114 * pixels[:, :, 2]
    channel_spread = pixels.max(axis=2) - pixels.min(axis=2)
    candidate = (luma >= 220) & (channel_spread <= 38)
    if not np.any(candidate):
        return None

    height_px, width_px = candidate.shape
    background = np.zeros_like(candidate, dtype=bool)
    stack: list[tuple[int, int]] = []

    def push(y_pos: int, x_pos: int) -> None:
        if 0 <= y_pos < height_px and 0 <= x_pos < width_px and candidate[y_pos, x_pos] and not background[y_pos, x_pos]:
            background[y_pos, x_pos] = True
            stack.append((y_pos, x_pos))

    for x_pos in range(width_px):
        push(0, x_pos)
        push(height_px - 1, x_pos)
    for y_pos in range(1, height_px - 1):
        push(y_pos, 0)
        push(y_pos, width_px - 1)

    while stack:
        y_pos, x_pos = stack.pop()
        push(y_pos - 1, x_pos)
        push(y_pos + 1, x_pos)
        push(y_pos, x_pos - 1)
        push(y_pos, x_pos + 1)

    if not np.any(background):
        return None
    blocks = background.reshape(height, pool_factor, width, pool_factor)
    blocks = blocks.transpose(0, 2, 1, 3).reshape(height, width, pool_factor * pool_factor)
    return [[bool(np.mean(blocks[y_pos, x_pos]) < 0.5) for x_pos in range(width)] for y_pos in range(height)]


def _apply_alpha_mask(cells: list[list[str | None]], alpha_mask: list[list[bool]]) -> list[list[str | None]]:
    return [
        [code if alpha_mask[y_pos][x_pos] else None for x_pos, code in enumerate(row)]
        for y_pos, row in enumerate(cells)
    ]


def _build_pil_palette_image(colors: list[PaletteColor]) -> Image.Image:
    rgb_values = [ImageColor.getrgb(color.hex) for color in colors]
    flat_palette = [channel for rgb in rgb_values for channel in rgb]
    full_palette = flat_palette + [0] * (256 - len(rgb_values)) * 3
    index_image = Image.fromarray(np.arange(len(rgb_values), dtype=np.uint8).reshape(len(rgb_values), 1), mode="P")
    index_image.putpalette(full_palette)
    return index_image


def _estimate_color_count(
    image: Image.Image,
    width: int,
    height: int,
    selection_alpha: Image.Image | None = None,
) -> int:
    small = image.resize((80, 80), Image.Resampling.LANCZOS)
    pixels = np.array(small, dtype=np.float64).reshape(-1, 3)
    if selection_alpha is not None:
        visible = np.array(
            selection_alpha.resize((80, 80), Image.Resampling.LANCZOS),
            dtype=np.uint8,
        ).reshape(-1) >= 128
        if np.any(visible):
            pixels = pixels[visible]
    total_variance = np.sum(np.var(pixels, axis=0))
    count = int(12 + (total_variance - 500) * 28 / 3500)
    count = max(12, min(40, count))
    if width * height > 48 * 48:
        count = min(40, count + 5)
    elif width * height < 29 * 29:
        count = max(12, count - 3)
    return count


def _select_top_n_colors(
    image: Image.Image,
    palette: list[PaletteColor],
    count: int,
    selection_alpha: Image.Image | None = None,
) -> list[PaletteColor]:
    sample = np.array(image.resize((120, 120), Image.Resampling.LANCZOS)).reshape(-1, 3).astype(np.float64)
    if selection_alpha is not None:
        visible = np.array(
            selection_alpha.resize((120, 120), Image.Resampling.LANCZOS),
            dtype=np.uint8,
        ).reshape(-1) >= 128
        if np.any(visible):
            sample = sample[visible]
    palette_rgb = np.array([color.rgb for color in palette], dtype=np.float64)
    distances = perceptual_distance_matrix(sample, palette_rgb, strategy="ciede2000")
    closest_indices = np.argmin(distances, axis=1)
    unique, frequencies = np.unique(closest_indices, return_counts=True)
    ranked_indices = unique[np.argsort(-frequencies)]
    top_indices = list(ranked_indices[:count])

    # Tiny eyes, mouths and outline strokes may be semantically essential while
    # covering too few pixels to enter a frequency-only palette. Reserve one slot
    # for the dominant near-black foreground color when the budget allows it.
    if count > 1:
        sample_luma = 0.299 * sample[:, 0] + 0.587 * sample[:, 1] + 0.114 * sample[:, 2]
        dark_pixels = (sample_luma <= 85) & (sample.max(axis=1) <= 145)
        if np.any(dark_pixels):
            dark_matches = closest_indices[dark_pixels]
            dark_index = int(np.bincount(dark_matches, minlength=len(palette)).argmax())
            if dark_index not in top_indices:
                if len(top_indices) >= count:
                    top_indices[-1] = dark_index
                else:
                    top_indices.append(dark_index)
    top_set = {int(index) for index in top_indices}
    return [color for index, color in enumerate(palette) if index in top_set]


def _preprocess_image(
    image: Image.Image,
    contrast: float = 0.0,
    saturation: float = 0.0,
    sharpness: float = 0.0,
) -> Image.Image:
    if contrast == 0.0:
        gray = image.convert("L")
        histogram = gray.histogram()
        total = sum(histogram)
        cumulative = 0
        p5 = 0
        p95 = 255
        for index, amount in enumerate(histogram):
            cumulative += amount
            if cumulative >= total * 0.05 and p5 == 0:
                p5 = index
            if cumulative >= total * 0.95:
                p95 = index
                break
        spread = p95 - p5
        factor = 1.25 if spread < 100 else 1.15 if spread < 160 else 1.05
    else:
        factor = max(0.5, min(1.5, 1.0 + contrast / 100.0))
    image = ImageEnhance.Contrast(image).enhance(factor)

    factor = 1.1 if saturation == 0.0 else max(0.5, min(1.5, 1.0 + saturation / 100.0))
    image = ImageEnhance.Color(image).enhance(factor)

    factor = 1.3 if sharpness == 0.0 else max(0.0, min(2.0, 1.0 + sharpness / 50.0))
    return ImageEnhance.Sharpness(image).enhance(factor)


def _consolidate_extremes(image: Image.Image) -> Image.Image:
    pixels = np.array(image, dtype=np.float64)
    luma = 0.299 * pixels[:, :, 0] + 0.587 * pixels[:, :, 1] + 0.114 * pixels[:, :, 2]

    dark_limit = 80.0
    dark_mask = luma < dark_limit
    if np.any(dark_mask):
        factor = (luma[dark_mask] / dark_limit)[:, np.newaxis]
        gray = luma[dark_mask][:, np.newaxis]
        pixels[dark_mask] = gray + factor * (pixels[dark_mask] - gray)

    light_limit = 210.0
    light_mask = luma > light_limit
    if np.any(light_mask):
        factor = ((255.0 - luma[light_mask]) / (255.0 - light_limit))[:, np.newaxis]
        gray = luma[light_mask][:, np.newaxis]
        pixels[light_mask] = gray + factor * (pixels[light_mask] - gray)

    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8), "RGB")


def _cleanup_rare_colors(
    cells: list[list[str | None]],
    palette: list[PaletteColor],
    total_pixels: int,
    min_ratio: float,
) -> list[list[str | None]]:
    counts = Counter(code for row in cells for code in row if code is not None)
    min_count = max(2, int(total_pixels * min_ratio))
    kept_codes = {code for code, amount in counts.items() if amount >= min_count}
    rare_codes = set(counts) - kept_codes
    if not rare_codes or not kept_codes:
        return cells

    palette_by_code = {color.code: color for color in palette}
    remap: dict[str, str] = {}
    for rare_code in rare_codes:
        rare_color = palette_by_code.get(rare_code)
        if rare_color is None:
            continue
        kept_colors = [palette_by_code[code] for code in kept_codes if code in palette_by_code]
        if kept_colors:
            remap[rare_code] = nearest_color(rare_color.rgb, kept_colors).code

    return _apply_remap(cells, remap)


def _merge_similar_colors(
    cells: list[list[str | None]],
    palette: list[PaletteColor],
    threshold: float,
) -> list[list[str | None]]:
    counts = Counter(code for row in cells for code in row if code is not None)
    sorted_codes = [code for code, _ in counts.most_common()]
    palette_by_code = {color.code: color for color in palette}
    remap: dict[str, str] = {}

    for index, current_code in enumerate(sorted_codes):
        if current_code in remap:
            continue
        current = palette_by_code.get(current_code)
        if current is None:
            continue
        for lower_code in sorted_codes[index + 1 :]:
            if lower_code in remap:
                continue
            lower = palette_by_code.get(lower_code)
            if lower is not None and color_distance(current.rgb, lower.rgb) < threshold:
                remap[lower_code] = current_code

    return _apply_remap(cells, remap)


def _cap_max_colors(
    cells: list[list[str | None]],
    palette: list[PaletteColor],
    max_colors: int,
) -> list[list[str | None]]:
    counts = Counter(code for row in cells for code in row if code is not None)
    if len(counts) <= max_colors:
        return cells

    top_codes = {code for code, _ in counts.most_common(max_colors)}
    removed_codes = set(counts) - top_codes
    palette_by_code = {color.code: color for color in palette}
    allowed_colors = [palette_by_code[code] for code in top_codes if code in palette_by_code]
    remap = {
        code: nearest_color(palette_by_code[code].rgb, allowed_colors).code
        for code in removed_codes
        if code in palette_by_code and allowed_colors
    }
    return _apply_remap(cells, remap)


def _smooth_edges(cells: list[list[str | None]], palette: list[PaletteColor]) -> list[list[str | None]]:
    height = len(cells)
    width = len(cells[0]) if height else 0
    if height < 3 or width < 3:
        return cells

    palette_by_code = {color.code: color for color in palette}
    result = [row[:] for row in cells]
    for y_pos in range(height):
        for x_pos in range(width):
            current = cells[y_pos][x_pos]
            if current is None:
                continue
            neighbors = []
            if y_pos > 0:
                neighbors.append(cells[y_pos - 1][x_pos])
            if y_pos < height - 1:
                neighbors.append(cells[y_pos + 1][x_pos])
            if x_pos > 0:
                neighbors.append(cells[y_pos][x_pos - 1])
            if x_pos < width - 1:
                neighbors.append(cells[y_pos][x_pos + 1])
            valid_neighbors = [code for code in neighbors if code is not None]
            if valid_neighbors and current not in valid_neighbors:
                replacement = Counter(valid_neighbors).most_common(1)[0][0]
                current_color = palette_by_code.get(current)
                replacement_color = palette_by_code.get(replacement)
                if current_color and replacement_color and color_distance(current_color.rgb, replacement_color.rgb) > 30:
                    continue
                result[y_pos][x_pos] = replacement
    return result


def _remove_background_flood_fill(cells: list[list[str | None]]) -> list[list[str | None]]:
    height = len(cells)
    width = len(cells[0]) if height else 0
    if not height or not width:
        return cells

    border_counts = Counter()
    for x_pos in range(width):
        if cells[0][x_pos] is not None:
            border_counts[cells[0][x_pos]] += 1
        if cells[height - 1][x_pos] is not None:
            border_counts[cells[height - 1][x_pos]] += 1
    for y_pos in range(1, height - 1):
        if cells[y_pos][0] is not None:
            border_counts[cells[y_pos][0]] += 1
        if cells[y_pos][width - 1] is not None:
            border_counts[cells[y_pos][width - 1]] += 1
    if not border_counts:
        return cells

    background = border_counts.most_common(1)[0][0]
    visited = [[False] * width for _ in range(height)]
    stack: list[tuple[int, int]] = []

    def push_if_background(y_pos: int, x_pos: int) -> None:
        if 0 <= y_pos < height and 0 <= x_pos < width and not visited[y_pos][x_pos]:
            if cells[y_pos][x_pos] == background:
                visited[y_pos][x_pos] = True
                stack.append((y_pos, x_pos))

    for x_pos in range(width):
        push_if_background(0, x_pos)
        push_if_background(height - 1, x_pos)
    for y_pos in range(1, height - 1):
        push_if_background(y_pos, 0)
        push_if_background(y_pos, width - 1)

    while stack:
        y_pos, x_pos = stack.pop()
        cells[y_pos][x_pos] = None
        push_if_background(y_pos - 1, x_pos)
        push_if_background(y_pos + 1, x_pos)
        push_if_background(y_pos, x_pos - 1)
        push_if_background(y_pos, x_pos + 1)
    return cells


def _apply_remap(cells: list[list[str | None]], remap: dict[str, str]) -> list[list[str | None]]:
    if not remap:
        return cells
    return [[remap.get(code, code) if code is not None else None for code in row] for row in cells]

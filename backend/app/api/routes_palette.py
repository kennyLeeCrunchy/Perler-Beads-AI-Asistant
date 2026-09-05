from __future__ import annotations

from fastapi import APIRouter

from fastapi import HTTPException, Query

from app.core.config import DATA_DIR, MARD_PALETTE_PATH
from app.core.palette import PalettePreset, load_mard_palette, load_palette, load_presets


router = APIRouter(prefix="/api/palette", tags=["palette"])


@router.get("")
def get_palette(brand: str = Query(default="Artkal")) -> dict:
    normalized_brand = brand.strip().lower()
    if normalized_brand == "artkal":
        resolved_brand = "Artkal"
        colors = load_palette(DATA_DIR / "artkal_m_series.json")
        presets = load_presets(DATA_DIR / "artkal_presets.json")
    elif normalized_brand == "mard":
        resolved_brand = "Mard"
        colors = load_mard_palette(MARD_PALETTE_PATH)
        presets = {"221": PalettePreset(key="221", label="Mard 221 colors", codes=None)}
    else:
        raise HTTPException(status_code=400, detail="Unsupported palette brand; use Artkal or Mard")
    return {
        "brand": resolved_brand,
        "colors": [
            {
                "code": color.code,
                "series": color.series,
                "name": color.name,
                "name_zh": color.name_zh,
                "hex": color.hex,
                "rgb": list(color.rgb),
            }
            for color in colors.values()
        ],
        "presets": {
            key: {"label": preset.label, "codes": preset.codes}
            for key, preset in presets.items()
        },
    }

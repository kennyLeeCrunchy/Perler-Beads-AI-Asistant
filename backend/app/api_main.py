from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_ai import router as ai_router
from app.api.routes_export import router as export_router
from app.api.routes_palette import router as palette_router
from app.api.routes_pattern import router as pattern_router
from app.core.config import RUNTIME_DIR


app = FastAPI(
    title="Pindou API",
    version="0.3.0",
    description="Perlabo 拼豆 AI 生图、图生图清稿、品牌色卡量化与导出 API。",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "PINDOU_CORS_ORIGINS",
        "http://127.0.0.1:5173,http://localhost:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)
app.include_router(export_router)
app.include_router(palette_router)
app.include_router(pattern_router)

# 只公开 AI 生成结果；不挂载旧 Demo、实验页面、原始上传或日志目录。
app.mount(
    "/runtime/generated",
    StaticFiles(directory=RUNTIME_DIR / "generated"),
    name="generated-runtime",
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "perlabo-api", "version": app.version}

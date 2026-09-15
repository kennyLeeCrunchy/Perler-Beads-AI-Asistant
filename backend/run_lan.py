from __future__ import annotations

import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "app.api_main:app",
        host=os.getenv("PINDOU_HOST", "0.0.0.0"),
        port=int(os.getenv("PINDOU_PORT", "8000")),
        reload=False,
    )

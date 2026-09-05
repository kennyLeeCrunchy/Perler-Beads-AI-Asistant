# Pindou FastAPI Backend

这是 `APP` 使用的纯 API 后端，不挂载旧版浏览器 Demo。

## 启动

```powershell
cd D:\vscodePro\pindou\APP\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.api_main:app --host 127.0.0.1 --port 8000
```

或者运行 `python run_api.py`。访问 `/docs` 查看 OpenAPI 文档；根路径 `/` 返回 404 是预期行为。

## 接口

- `POST /api/ai/generate`：DashScope 文生图。
- `POST /api/pattern/generate`：上传图片并转换为 Artkal M 或 Mard 221 图纸。
- `GET /api/palettes/{palette_id}`：读取完整品牌色卡。
- `POST /api/export/png`：根据编辑后的格子数据导出 PNG。

## 目录

- `app/`：生产 API 与核心算法。
- `app/data/`：Artkal 色卡数据。
- `color_standards/`：Mard 色卡及原始资料。
- `runtime/`：上传、生成和导出文件，不提交运行产物。
- `tests/`：生产后端测试。
- `tools/`：色卡数据整理脚本。

CIEDE2000、边缘感知实验页面及旧 HTML/CSS/JS 已移到 `demo/legacy_browser`。

## 测试

```powershell
python -m unittest discover -s tests -v
```

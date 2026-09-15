# Pindou FastAPI Backend

这是 `APP` 使用的 FastAPI 后端，供公开 Web 前端和内部微信小程序共用；不挂载旧版浏览器 Demo。

## 启动

```powershell
cd D:\vscodePro\pindou\APP\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY
python -m uvicorn app.api_main:app --host 127.0.0.1 --port 8000
```

或者运行 `python run_api.py`。局域网验证使用 `python run_lan.py`，它监听 `0.0.0.0:8000`。访问 `/docs` 查看 OpenAPI 文档；根路径 `/` 返回 404 是预期行为。

启动时会自动读取当前目录的 `.env`。如果系统环境变量中已经存在同名配置，则系统环境变量优先；`.env` 只用于本地开发，不要提交真实密钥到 GitHub。

## 接口

- `POST /api/ai/generate`：DashScope 文生图。
- `POST /api/ai/clean-reference`：一次 DashScope 图生图清稿，并保存可复用的清稿引用。
- `POST /api/pattern/generate`：上传图片并转换为 Artkal M 或 Mard 221 图纸。
- `POST /api/pattern/bundle`：从同一清稿生成 52×52、78×78、104×104 三档图纸，并返回结构 / CIEDE2000 质量报告。
- `GET /api/palettes/{palette_id}`：读取完整品牌色卡。
- `POST /api/export/png`：根据编辑后的格子数据导出 PNG。
- `POST /api/export/pdf`：导出含统计和色号的 PDF。
- `GET /api/health`：服务健康检查。

## 目录

- `app/`：生产 API 与核心算法。
- `app/data/`：Artkal 色卡数据。
- `color_standards/`：Mard 色卡及原始资料。
- `runtime/`：上传、生成和导出文件，不提交运行产物。
- `tests/`：生产后端测试。
- `tools/`：色卡数据整理脚本。

CIEDE2000、边缘感知实验页面及旧 HTML/CSS/JS 不属于公开 APP 目录；公开后端只保留生产 API 所需的颜色引擎和量化逻辑。

## 测试

```powershell
python -m unittest discover -s tests -v
```

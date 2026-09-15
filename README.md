# Perlabo APP

这是公开发布的“小豆点拼豆实验室 Perlabo”应用部分，只包含 Web 前端和 Web/小程序共用的 FastAPI 后端。

```text
APP/
├─ frontend/   React + TypeScript + Vite Web 应用
└─ backend/    FastAPI、AI、图纸算法、色卡与导出
```

## 功能链路

```text
Web 文生图 ─┐
Web 图生图 ─┼→ 单次 bead_ready_52_v2 清稿 → 52/78/104 三档图纸 → 编辑 → 制作 → PNG/PDF
小程序图生图 ─┘
```

Web 保留 AI 文生图；小程序通过同一后端只使用图生图清稿和图纸接口。

## 本地启动

后端：

```powershell
cd D:\vscodePro\pindou\APP\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DASHSCOPE_API_KEY="你的 DashScope Key"
$env:PINDOU_CORS_ORIGINS="http://127.0.0.1:5180,http://localhost:5180"
python run_api.py
```

前端另开终端：

```powershell
cd D:\vscodePro\pindou\APP\frontend
npm ci
npm run dev
```

访问 `http://127.0.0.1:5180`；FastAPI 文档位于 `http://127.0.0.1:8000/docs`。

## 局域网启动

后端：

```powershell
cd D:\vscodePro\pindou\APP\backend
.\.venv\Scripts\Activate.ps1
$env:PINDOU_CORS_ORIGINS="http://localhost:5180,http://127.0.0.1:5180,http://你的局域网IP:5180"
python run_lan.py
```

前端：

```powershell
cd D:\vscodePro\pindou\APP\frontend
npm run dev -- --host 0.0.0.0
```

然后在同一局域网的手机、平板或其他电脑打开 `http://你的局域网IP:5180`。Windows 防火墙需要允许 Python 和 Node/Vite 在“专用网络”访问 8000、5180 端口。

生产预览：

```powershell
npm run build
npm run preview -- --host 0.0.0.0
```

## API

- `POST /api/ai/generate`：Web AI 文生图。
- `POST /api/ai/clean-reference`：一次图生图清稿。
- `POST /api/pattern/generate`：兼容的单档传统转图接口。
- `POST /api/pattern/bundle`：同一清稿生成 52、78、104 三档图纸。
- `GET /api/palette?brand=Artkal|Mard`：读取完整色卡。
- `POST /api/export/png`：PNG 导出。
- `POST /api/export/pdf`：PDF 导出。
- `GET /api/health`：健康检查。

## 安全边界

公开仓库不包含 API Key、上传图片、生成图片、用户数据、模型缓存和 `.env`。后端运行文件写入 `backend/runtime`，只有生成结果目录通过 HTTP 暴露。局域网模式会让同一网络设备看到 Demo，请不要在不可信网络中直接暴露带有真实 AI Key 的服务。

## 验证

```powershell
cd APP\backend
python -m unittest discover -s tests -v

cd ..\frontend
npm ci
npm run build
```

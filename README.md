# APP 主产品

`APP` 只放当前产品实际使用的前后端代码。

```text
APP/
├─ frontend/   React + TypeScript + Vite
└─ backend/    FastAPI + 图像处理 + Artkal/Mard 色卡
```

## 联调地址

| 服务 | 地址 | 说明 |
|---|---|---|
| React 页面 | `http://127.0.0.1:5173` | 用户实际访问的产品 |
| FastAPI 文档 | `http://127.0.0.1:8000/docs` | 接口调试 |
| FastAPI 根路径 | `http://127.0.0.1:8000/` | 预期返回 404 |

## 后端

```powershell
cd D:\vscodePro\pindou\APP\backend
python -m pip install -r requirements.txt
python -m uvicorn app.api_main:app --host 127.0.0.1 --port 8000
```

当前生产 API：

- `POST /api/ai/generate`
- `POST /api/pattern/generate`
- `GET /api/palettes/{palette_id}`
- `POST /api/export/png`

运行文件写入 `APP/backend/runtime`，仅生成图目录通过 HTTP 暴露。色卡原始及整理数据位于 `APP/backend/color_standards`。

## 前端

```powershell
cd D:\vscodePro\pindou\APP\frontend
npm install
npm run dev
```

Vite 会把 `/api` 和 `/runtime` 代理到 `127.0.0.1:8000`。分离部署时可使用 `VITE_API_BASE_URL` 指定公开后端地址。

## 功能边界

完整对应关系见 [FRONTEND_BACKEND_GAP.md](./FRONTEND_BACKEND_GAP.md)。其中“本地真实”表示功能确实可用，但数据只保存在当前浏览器；“演示”表示页面已经呈现，但尚无完整业务实现。

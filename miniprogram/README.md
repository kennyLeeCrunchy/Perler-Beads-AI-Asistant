# 拼豆助手微信小程序

这是基于 Taro 4、React 与 TypeScript 的微信小程序端。Web 端仍以 `APP/frontend` 为唯一源码；小程序只复用业务契约和产品流程，不保存 Web 源码副本。

## 产品边界

- 核心路径：上传图片 → AI 图纸前清稿（可用时）→ 52×52、78×78、104×104 三档图纸 → 编辑 → 保存 → 制作辅助 → 导出。
- 小程序正式版不提供 AI 文生图，以控制模型 Token/调用成本；用户可从其他应用生成图片后上传。
- 小程序保留图片清稿（image-to-image）能力，后端不可用时应允许用户直接转图纸。
- Web 端仍保留 AI 文生图和完整服务，两端通过能力开关而不是复制两套业务实现来区分。

## 当前状态

- [x] Taro 小程序工程可构建并通过 TypeScript 检查。
- [x] 已有首页、转图、预览、编辑、作品、制作、设置和隐私页面。
- [x] 上传图片可调用 `POST /api/pattern/generate`。
- [x] 作品和制作进度可保存在微信本地存储。
- [ ] 接入正式的图纸前 AI 清稿及 52/78/104 三档同屏选择。
- [ ] 接入微信登录、云端作品库、对象存储和跨设备同步。
- [ ] 完成真机性能、弱网、隐私合规及审核验证。

## 目录结构

```text
APP/miniprogram/
├─ config/                  # Taro 环境和构建配置
├─ docs/
│  ├─ backend-api.md        # 小程序仍需调用的后端接口契约
│  └─ WEB_MIGRATION_REFERENCE.md
├─ src/
│  ├─ components/
│  ├─ pages/
│  ├─ services/
│  ├─ shared/
│  ├─ store/
│  └─ utils/
├─ REVIEW_CHECKLIST.md
├─ package.json
└─ project.config.json
```

原 `migration-baseline/web-frontend` 是 `APP/frontend` 的重复快照，容易随 Web 更新而失真，已删除。迁移页面或交互时直接查看当前 `APP/frontend`，差异和不可直接复用项记录在 `docs/WEB_MIGRATION_REFERENCE.md`。

## 本地运行

```bash
npm install
npm run typecheck
npm run build:weapp
```

将 `TARO_APP_API_BASE_URL` 配置为可由微信开发者工具和真机访问的 HTTPS 后端地址。不要把 AppSecret 或 DashScope Key 写入小程序代码。

## Web → 小程序迁移原则

| Web 能力 | 小程序处理 |
|---|---|
| React Router | 使用 Taro 页面配置和导航 API |
| DOM/CSS 网格 | 大图纸优先使用 Canvas 与触摸坐标换算 |
| `fetch` / `FormData` / `Blob` | 使用 Taro 上传、下载和文件 API |
| `localStorage` | 草稿可用 Taro Storage；正式作品迁移到云端 CRUD |
| 顶部导航 | 使用小程序页面导航和 `tabBar` |
| AI 文生图 | 不进入小程序正式版 |
| AI 图纸前清稿 | 保留，经后端 image-to-image 接口调用 |

## 上线前重点

1. 接入 OpenID 身份、作品 CRUD、对象存储和用户数据删除。
2. 将 v13 图纸前清稿链路接入小程序，并保证 AI 失败可降级为直接转图。
3. 同时展示 52×52、78×78、104×104 三档结果，用户选择后再进入编辑或导出。
4. 验证三档图纸的 Canvas 性能、内存和保存相册行为。
5. 移除生产 Mock 和可能误导用户的占位操作，确保显示色号、进度、镜像与导出语义一致。
6. 完成隐私指引、第三方模型说明、内容安全、调用额度和异常熔断。

## 相关资料

- 后端接口：[docs/backend-api.md](docs/backend-api.md)
- Web 与小程序差异：[docs/WEB_MIGRATION_REFERENCE.md](docs/WEB_MIGRATION_REFERENCE.md)
- 上线检查：[REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md)

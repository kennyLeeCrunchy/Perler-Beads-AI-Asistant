# 微信小程序开发与迁移计划

## 1. 目录定位

本目录用于开发“拼豆助手”微信小程序。

现有 `APP/frontend` 是 React + Vite 网页端，不能直接作为微信小程序上传。本目录采用“保留 Web 端、逐步迁移到 Taro React”的方式，避免在迁移过程中破坏现有可运行版本。

当前状态：

- [x] 已建立独立的小程序开发目录。
- [x] 已复制现有 Web 前端，作为迁移基线。
- [x] 已将可直接复用的业务类型复制到正式小程序源码目录。
- [x] 现有 FastAPI 图像算法与接口继续在 `../backend` 原地复用。
- [ ] 尚未安装或初始化 Taro，不应把当前目录当作可运行的小程序工程。
- [ ] 尚未接入微信登录、数据库、云存储和作品云同步。

## 2. 当前目录结构

```text
APP/miniprogram/
├─ README.md
├─ src/
│  ├─ shared/
│  │  └─ types.ts
│  ├─ pages/
│  ├─ components/
│  ├─ services/
│  ├─ store/
│  ├─ styles/
│  └─ utils/
└─ migration-baseline/
   ├─ web-frontend/
   │  ├─ src/
   │  ├─ public/
   │  ├─ package.json
   │  └─ 其他 Vite/TypeScript 配置
   └─ docs/
      ├─ FRONTEND_BACKEND_GAP.md
      └─ backend-api.md
```

`migration-baseline` 是迁移参考副本，不作为小程序构建输入。后续每迁移完一个页面，应以 `APP/frontend` 的最新实现为准核对一次，再在小程序端完成真机验证。

## 3. 已复用内容

### 3.1 可直接进入小程序源码

| 来源 | 新位置 | 复用方式 |
|---|---|---|
| `APP/frontend/src/types.ts` | `src/shared/types.ts` | 直接复用 `Work`、`BeadColor` 等业务类型；后续补充云端字段 |

### 3.2 作为逐页迁移基线

`migration-baseline/web-frontend` 已复制现有 Web 前端的源码、静态资源和项目配置，主要用于复用：

- 页面信息架构、字段、文案和交互流程。
- 图纸、作品、色卡、制作进度的数据结构。
- `BeadGrid` 中的格子数据计算和颜色编号规则。
- 编辑器的画笔、擦除、取色、替换、撤销和重做规则。
- 图片转图纸、AI 生图和 PNG 导出的接口契约。
- 现有 CSS 的颜色、间距和组件视觉规范。

这些文件不能原样放入小程序正式 `src`，因为其中使用了浏览器 DOM、`react-router-dom`、`fetch`、`FormData`、`Blob`、`localStorage` 和 `lucide-react`。

### 3.3 原地复用的后端

以下模块继续由 `APP/backend` 提供，不复制到小程序目录：

- 图片上传和拼豆色卡量化。
- Artkal M / Mard 221 色卡。
- 透明底和主体 mask 处理。
- AI 文生图调用。
- PNG 图纸渲染与导出。
- 现有后端测试。

小程序通过新的请求适配层调用这些接口。后端在上线前仍需完成用户、作品、数据库、对象存储和生产部署扩展。

## 4. Web 文件到小程序模块的迁移映射

| Web 端文件/模块 | 小程序目标 | 处理方式 |
|---|---|---|
| `App.tsx` | `src/app.ts`、`src/app.config.ts` | 重写入口、页面声明和全局生命周期 |
| `react-router-dom` 路由 | Taro 页面路由 | 使用 `Taro.navigateTo`、`redirectTo`、`switchTab` |
| `Navbar.tsx` | `tabBar` + 页面自定义导航 | 重写，不保留 Web 顶部导航 |
| `HomePage.tsx` | `src/pages/home` | 复用内容，重写组件标签 |
| `AIGeneratePage.tsx` | `src/pages/ai-generate` | 复用流程和参数；首版可通过功能开关关闭 |
| `ConvertPage.tsx` | `src/pages/convert` | 复用参数与接口响应；重写图片选择和上传 |
| `EditorPage.tsx` | `src/pages/editor` | 复用编辑规则；网格渲染改用 Canvas |
| `MakePage.tsx` | `src/pages/make` | 复用制作进度模型；先修复固定数据逻辑 |
| `WorksPage.tsx` | `src/pages/works` | 从本地数组改为云端作品接口 |
| `BeadGrid.tsx` | `src/components/BeadCanvas` | 保留网格计算，重写为 Canvas 和触摸事件 |
| `api.ts` | `src/services/api` | 保留类型，使用 `wx.cloud.callContainer` 重写请求 |
| `storage.ts` | `src/services/works` + 本地草稿缓存 | 云端 CRUD 为主，Taro Storage 只保存临时草稿 |
| `styles.css`、`advanced.css` | 页面和组件 SCSS | 复用设计 Token，重新适配 rpx 和安全区域 |
| `lucide-react` 图标 | 小程序图标资源/兼容图标库 | 替换，不能直接依赖 Web SVG 组件 |

## 5. 需要新开发的部分

### 5.1 小程序工程基础

- [ ] 初始化 Taro React + TypeScript 工程。
- [ ] 创建 `package.json`、`config/index.ts`、`project.config.json`。
- [ ] 创建 `src/app.ts`、`src/app.config.ts`、`src/app.scss`。
- [ ] 配置页面、分包、`tabBar`、主题色和安全区域。
- [ ] 建立开发、体验、生产三套环境配置。
- [ ] 配置微信小程序 AppID，但不得把 AppSecret 写入前端。

### 5.2 微信身份与账号

- [ ] `wx.cloud.init` 初始化。
- [ ] 封装 `wx.cloud.callContainer`。
- [ ] 后端从可信的 `X-WX-OPENID` 请求头识别用户。
- [ ] 首次访问自动创建用户，不设置强制注册页。
- [ ] 开发个人资料页，昵称和头像作为可选信息。
- [ ] 开发账号注销和云端数据删除入口。
- [ ] 增加用户协议、隐私保护指引和第三方服务说明。

### 5.3 小程序页面

- [ ] 首页。
- [ ] 图片选择和上传。
- [ ] 图片转图纸参数页。
- [ ] 图纸预览页。
- [ ] Canvas 图纸编辑器。
- [ ] 我的作品。
- [ ] 制作辅助。
- [ ] 导出和保存至相册。
- [ ] 设置、隐私和账号注销。
- [ ] AI 生图页（建议首个审核版本暂不开放）。

### 5.4 小程序组件

- [ ] `BeadCanvas`：Canvas 绘制、缩放、平移和局部重绘。
- [ ] 触摸坐标到图纸格子的换算。
- [ ] 画笔、擦除、取色、填充、框选和替换工具。
- [ ] 颜色列表、色号高亮和数量统计。
- [ ] 上传、空状态、加载、错误、确认弹窗。
- [ ] 适配刘海屏、底部安全区、横竖屏和不同像素密度。

### 5.5 请求与文件服务

- [ ] 将 Web `fetch` 请求改成 `callContainer` 请求适配器。
- [ ] 将 `File/FormData` 上传改成小程序图片选择和云存储上传。
- [ ] 将 `Blob` 下载改成云文件下载、临时文件和保存相册。
- [ ] 统一超时、重试、错误码和请求 ID 日志。
- [ ] 对上传大小、格式和图片尺寸做前后端双重校验。
- [ ] 为生成、转图和导出增加防重复提交。

### 5.6 后端账号和作品库

- [ ] 增加数据库连接、模型和迁移工具。
- [ ] 新增 `users`、`works`、`assets`、`generation_jobs` 表。
- [ ] 新增 `/api/me` 查询、修改和注销接口。
- [ ] 新增 `/api/works` 增删改查接口。
- [ ] 所有作品、文件和任务强制按 `user_id` 隔离。
- [ ] 本地 `runtime` 文件迁移到对象存储。
- [ ] 图片访问使用用户鉴权或短期签名地址。
- [ ] AI 生图改为异步任务和状态查询。
- [ ] 增加按用户的频率、并发和每日额度限制。
- [ ] 增加 `/healthz`、结构化日志和生产错误监控。
- [ ] 增加 Dockerfile，并部署到微信云托管。

### 5.7 上线前必须修复

- [ ] 修复制作页中固定颜色/区域编号的误导逻辑。
- [ ] 修复 PNG“显示色号”开关与实际导出不一致。
- [ ] 删除首页和作品库中的生产 Mock 数据。
- [ ] 验证 52×52、78×78、104×104 图纸的真机性能。
- [ ] 验证弱网、断网、重复提交和云端冲突处理。
- [ ] 完成小程序备案、服务类目、隐私指引和审核材料。

### 5.8 AI 功能开放前额外开发

- [ ] 提示词和生成结果内容安全审核。
- [ ] AI 生成图片的显式标识。
- [ ] 导出图片的显式标识和文件元数据隐式标识。
- [ ] 在产品内公示模型名称和备案信息。
- [ ] 生成记录、投诉、删除和封禁机制。
- [ ] 对 AI 调用费用设置用户额度、熔断和告警。

## 6. 推荐实施顺序

### 阶段 A：首个可审核版本

1. 初始化 Taro 工程和云托管环境。
2. 接入 OpenID 自动身份。
3. 完成用户、作品和文件持久化。
4. 迁移“上传图片 → 转图纸 → 编辑 → 云保存 → PNG 导出”。
5. 完成隐私、注销、错误状态和真机测试。
6. 关闭尚未合规的 AI 生图入口，提交首版审核。

### 阶段 B：上线后的核心增强

1. 修复并迁移制作辅助完整逻辑。
2. 加入完整色卡、镜像、分区和 PDF 导出。
3. 优化大尺寸图纸 Canvas 性能和草稿冲突。
4. 完成 AI 标识、内容安全和备案信息后开放 AI 生图。

## 7. 首版完成标准

- 用户打开小程序后能获得稳定的云端身份。
- 用户上传图片后能生成真实拼豆图纸。
- 用户能编辑、保存、再次打开和删除自己的作品。
- 不同微信用户之间的数据严格隔离。
- 导出图片能保存到手机相册。
- 容器重启和扩容不会丢失作品或图片。
- 核心路径在 Android、iOS 真机和弱网下均可完成。
- 隐私指引与实际调用的权限、接口、数据用途完全一致。


# 小程序后端接口契约

更新时间：2026-09-05

本文只记录小程序需要调用的生产接口。Demo 评测接口和 Web 专属 `POST /api/ai/generate` 不属于小程序契约。

## 当前可用接口

### `GET /api/palette?brand=Artkal|Mard`

返回品牌色卡和可用预设。小程序编辑器后续应使用该接口加载完整色卡，而不只展示当前图纸已使用颜色。

### `POST /api/pattern/generate`

`multipart/form-data`：

- `image`：上传图片；和 `source_path` 二选一。
- `source_path`：服务端生成图片标识；和 `image` 二选一。
- `brand`：`Artkal` 或 `Mard`，默认 `Artkal`。
- `width`、`height`：图纸尺寸；产品正式选择为 52、78、104。
- `preset`：默认 `221`。
- `max_colors`：默认 `24`，`0` 表示不限制。
- `similarity_threshold`：默认 `0`。
- `use_transparent_mask`：是否在量化前提取透明主体。

返回 `pattern_id`、尺寸、格子矩阵、颜色统计和 PNG data URL 预览。

当前小程序 `src/services/api.ts` 使用该接口。三档并发/批量生成接口尚未定稿；接入前应保证 52/78/104 共享同一份 AI 清稿结果，不重复产生模型费用。

### `POST /api/export/png`

可传 `pattern_id` 导出原始图纸，也可传编辑后的 `width`、`height`、`cells` 和 `colors` 导出当前矩阵。返回 PNG 文件。

## 待接入生产契约

### 图纸前 image-to-image 清稿

完整 App 尚需从 v13 Demo 迁入正式后端。接口必须支持：

- 上传原图和可选主体提取。
- 一次清稿输出供 52/78/104 共用。
- 超时、模型错误和额度不足时返回可识别错误，客户端允许“跳过清稿，直接转图”。
- 不暴露 DashScope Key，不接受客户端传任意模型密钥。

接口路径和最终响应字段以正式迁移实现及 OpenAPI 为准，未落地前不要在小程序中硬编码临时 Demo 路径。

### 用户与作品

待新增：用户信息/注销、作品 CRUD、素材上传与签名访问、制作进度同步。所有资源必须按可信 OpenID 对应的用户隔离，不能信任客户端自行提交的用户 ID。

## 明确不接入

- `POST /api/ai/generate`（AI 文生图）：Web 可保留，小程序正式版因 Token/调用成本不提供。
- CIEDE2000、边缘保护等历史评测端点：属于 Demo/测试，不是生产 API。
- 图纸后 AI 修整：实验结果不稳定，不进入正式链路。

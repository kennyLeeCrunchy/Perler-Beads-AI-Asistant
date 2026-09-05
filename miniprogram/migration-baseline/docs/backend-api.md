# API

## `GET /`

返回 demo 页面。

## `GET /api/palette`

通过 `brand=Artkal` 或 `brand=Mard` 返回对应品牌色卡；Mard 当前使用 221 色标准表。

## `POST /api/ai/generate`

JSON body:

```json
{
  "prompt": "可爱的橘猫头像，像素风，干净背景"
}
```

返回：

```json
{
  "source_path": "xxx.png",
  "image_url": "/runtime/generated/xxx.png",
  "prompt": "..."
}
```

## `POST /api/pattern/generate`

`multipart/form-data` 字段：

- `image`: 可选，上传图片。
- `source_path`: 可选，AI 生成图返回的不透明文件标识。
- `brand`: `Artkal` 或 `Mard`，默认 `Artkal`。
- `width`: 默认 `48`。
- `height`: 默认 `48`。
- `preset`: 默认 `221`。
- `max_colors`: 默认 `24`，`0` 表示不限制。
- `similarity_threshold`: 默认 `0`，`0` 表示不做额外相似色合并。

返回拼豆矩阵、统计和 PNG base64 预览。

## `POST /api/export/png`

JSON body:

```json
{
  "pattern_id": "生成图纸时返回的 pattern_id"
}
```

返回 PNG 文件。

## `POST /api/ciede2000-pattern/generate`

只用于评测 Lab + CIEDE2000 色卡匹配效果。`multipart/form-data` 字段：

- `image`: 必填，上传图片。
- `width`: 默认 `48`。
- `height`: 默认 `48`。
- `preset`: 默认 `221`。

返回拼豆统计和 PNG base64 预览。

## `POST /api/ciede2000-edge-pattern/generate`

用于评测白底主体边缘保护效果。`multipart/form-data` 字段：

- `image`: 必填，上传图片。
- `width`: 默认 `48`。
- `height`: 默认 `48`。
- `preset`: 默认 `221`。
- `remove_white_background`: 默认 `true`。
- `protect_edges`: 默认 `true`，只保护主体外轮廓，不增强眼睛、嘴巴和内部线稿。
- `edge_strength`: 默认 `75`，范围建议 `0-100`，用于控制外轮廓清晰的触发强度。

返回拼豆统计和 PNG base64 预览。

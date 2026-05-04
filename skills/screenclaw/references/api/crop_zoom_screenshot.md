---
name: crop_zoom_screenshot
description: 对已有截图进行裁剪并放大，用于看清局部细节、坐标数字、marker 位置。它不重新截图，也不重新绘制网格。
---

# crop_zoom_screenshot - 裁剪放大

## 快速决策

- 看不清局部目标或数字：使用 crop。
- 初次裁剪建议区域稍大，例如 `crop_width=25 crop_height=25 zoom_scale=2`。
- 目标在图中但太小：减小 `crop_width/crop_height`，增大 `zoom_scale`。
- 目标不在图中：中心坐标错了，扩大裁剪区域或回全局截图重新找。
- crop 只处理已有图片；如果需要更密网格，回到 `screenshot` 重新截图。
- 首次动态坐标或高风险坐标，应先 crop 看清局部，再 marker 反验。

## 脚本调用

基础裁剪：

```bash
python scripts/screenclaw.py crop_zoom_screenshot api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} source_image_path="{image_path}" center_x=55 center_y=65 crop_width=25 crop_height=25 zoom_scale=2
```

精细放大：

```bash
python scripts/screenclaw.py crop_zoom_screenshot api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} source_image_path="{image_path}" center_x=55 center_y=65 crop_width=10 crop_height=10 zoom_scale=4
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ai_app_type` | string | 是 | AI 应用类型 |
| `session_id` | string | 是 | 会话唯一标识 |
| `source_image_path` | string | 是 | 原始图片路径 |
| `center_x` | float | 是 | 裁剪中心横坐标百分比 |
| `center_y` | float | 是 | 裁剪中心纵坐标百分比 |
| `crop_width` | float | 是 | 裁剪区域宽度百分比 |
| `crop_height` | float | 是 | 裁剪区域高度百分比 |
| `zoom_scale` | float | 否 | 放大倍数，默认 2.0，最大 10.0 |

`crop_zoom_screenshot` 不需要 `window_id` 和 `main_window_id`。

远程场景下，统一脚本会自动把本地 `source_image_path` 转成 base64 发给服务端，并保存返回图片。

## 典型流程

```text
screenshot -> 得到 image_path -> crop_zoom_screenshot -> 读局部目标/数字 -> 必要时 marker 反验
```

## 与 screenshot marker 的区别

| 维度 | marker | crop_zoom_screenshot |
|------|--------|----------------------|
| 用途 | 在完整截图上标记候选坐标 | 放大已有截图局部 |
| 是否重新截图 | 是 | 否 |
| 是否重绘网格 | 是 | 否 |
| 适用 | 反验坐标位置 | 看清局部细节和数字 |

## 响应处理

- `data.image_path` 或 `data.image_base64` 是输出图片。
- `data.requested_params` 是裁剪请求摘要，不包含原始 base64。
- `data.effective_params` 是本次实际生效裁剪参数。
- `data.effective_crop` 包含源图尺寸、裁剪框像素和输出尺寸。
- 统一脚本输出图片路径和 message 后，会继续输出去掉 base64/null 的 `Data:` 摘要。

## 常见问题

1. **IMAGE_NOT_FOUND**：确认 `source_image_path` 是上一张截图返回的真实路径。
2. **裁剪后仍看不清**：缩小 `crop_width/crop_height`，增大 `zoom_scale`。
3. **没看到目标元素**：中心坐标错了，扩大裁剪区域或回全局截图。
4. **目标不完整**：增大 `crop_width/crop_height`。
5. **长截图太长**：也可以裁剪长截图，例如 `center_x=50 center_y=15 crop_width=100 crop_height=30` 查看头部区域。

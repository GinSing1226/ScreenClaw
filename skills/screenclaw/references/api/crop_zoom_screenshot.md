---
name: crop_zoom_screenshot
description: 对已有截图进行裁剪并放大（真实分辨率），用于看清局部细节。适用：截图中某区域元素太小看不清（小文字、小图标、密集元素、坐标数字）、确认某个UI元素的细节、marker标记点位置需要放大确认。不适用：需要重新截图（用screenshot）、需要看完整页面、需要看长页面的截图（用scroll_screenshot)。
---

# crop_zoom_screenshot - 裁剪放大

## 请求

**方法**：POST `/api/crop_zoom_screenshot`

**请求头**：
```
Authorization: Bearer {token}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `ai_app_type` | string | 是 | - | AI应用类型 |
| `session_id` | string | 是 | - | 会话唯一标识 |
| `source_image_path` | string | 是 | - | 原始图片路径（screenshot或scroll_screenshot返回的路径） |
| `center_x` | float | 是 | - | 裁剪区域中心点横坐标百分比（0-100） |
| `center_y` | float | 是 | - | 裁剪区域中心点纵坐标百分比（0-100） |
| `crop_width` | float | 是 | - | 裁剪区域总宽度百分比（0-100），如20表示截取20%宽度 |
| `crop_height` | float | 是 | - | 裁剪区域总高度百分比（0-100），如20表示截取20%高度 |
| `zoom_scale` | float | 否 | 2.0 | 放大倍数（1.0=不放大，最大10.0） |

> **注意**：此接口不需要 `window_id` 和 `main_window_id`，仅对已有图片文件进行处理。

### 请求示例

**基础裁剪放大**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "source_image_path": "D:/screenClaw/data/claude_code__session-123__2026-03-25/screenshot_143215_a7f2.png",
  "center_x": 55.0,
  "center_y": 65.0,
  "crop_width": 20,
  "crop_height": 20
}
```

**大幅放大看细节**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "source_image_path": "D:/screenClaw/data/claude_code__session-123__2026-03-25/screenshot_143215_a7f2.png",
  "center_x": 55.0,
  "center_y": 65.0,
  "crop_width": 10,
  "crop_height": 10,
  "zoom_scale": 4.0
}
```

### 参数说明

#### `center_x` / `center_y`
- 百分比坐标，基于原始图片尺寸计算
- 示例：`center_x=50, center_y=50` 表示裁剪图片正中央区域
- 通常从截图的网格坐标直接读取（坐标值即百分比）

#### `crop_width` / `crop_height`
- 裁剪区域大小，基于原始图片尺寸的百分比
- 示例：`crop_width=20, crop_height=20` 表示裁剪以中心点为中心的20%×20%区域
- 裁剪区域超出图片边界时自动clamp（部分超出），完全超出时返回错误

#### `zoom_scale`
- `1.0`：裁剪但不放大（与原图分辨率一致）
- `2.0`（默认）：放大2倍（适合看清文字和小图标）
- `4.0`+：大幅放大（可能模糊，取决于原图分辨率）

### 响应处理

**本地请求**（localhost/127.0.0.1/::1）：返回 `image_path`，直接使用路径。

**远程请求**（局域网IP）：返回 `image_base64`，必须使用脚本处理：
```bash
python scripts/crop_zoom_screenshot_cli.py <api_url> <token> <source_image_path> <session_id> <ai_app_type> center_x=<值> center_y=<值> crop_width=<值> crop_height=<值>
```

### 典型使用流程

```
1. AI调用 screenshot 获取截图 → 得到 image_path
2. AI发现某区域需要放大查看 → 调用 crop_zoom_screenshot，传入 source_image_path + center + crop参数
3. 如仍不清楚 → 调整参数（缩小crop区域、增大zoom_scale），对同一张 source_image_path 再次裁剪
```

### 与screenshot marker的区别

| 维度 | marker | crop_zoom_screenshot |
|------|--------|---------------------|
| **用途** | 在完整截图上标记坐标位置 | 裁剪局部区域并放大 |
| **输出** | 完整截图+标记圆圈 | 裁剪后的局部放大图 |
| **适用** | 确认坐标大致位置是否正确 | 看清局部细节（文字、小图标） |
| **是否重新截图** | 是 | 否（纯图像处理） |

## 常见问题

### 遇到问题时的排查顺序
1. **IMAGE_NOT_FOUND** → 检查screenshot返回的路径是否正确复制
2. **裁剪后仍看不清** → 缩小crop_width/crop_height，增大zoom_scale
3. **没看到目标元素** → 裁剪位置错了，也就是中心点坐标读错了，导致裁剪错误。可以增大crop的宽高，读放大图去找。也可以重新从全局里寻找大概坐标，重新裁剪放大找。
4. **有目标元素，但不全**  → 增大crop_width/crop_height

### 操作技巧
- **渐进式放大**：先用大crop区域（如30%）粗看，再缩小（如10%）精看
- **基于截图坐标**：center_x/center_y直接使用截图上的网格坐标值
- **可重复使用**：对同一张source_image_path可以多次裁剪，调整参数即可
- **滚动长截图适用**：如果某个长截图太长，不方便理解，也可以用裁剪，直接估算百分比就行，例如center坐标是（0,15），裁剪宽是100，高是30，那就可以将长截图的头部30%内容裁下来。

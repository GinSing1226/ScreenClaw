---
name: screenshot
description: 截取窗口画面并叠加坐标网格和标记点，用于定位元素坐标。也可以查看或分析单屏页面。适用：首次操作某个窗口、每次操作后验证结果、不确定目标元素的坐标位置、需要调整网格参数以精确定位。不适用：需要滚动页面截图，用scroll_screenshot
---

# screenshot - 截图

## 请求

**方法**：POST `/api/screenshot`

**请求头**：
```
Authorization: Bearer {token}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 默认值 | 说明 | 调整方案 |
|------|------|--------|------|----------|
| `ai_app_type` | string | 是 | - | AI应用类型 | |
| `session_id` | string | 是 | - | 会话唯一标识 | |
| `window_id` | int | 是 | - | 目标窗口句柄 | |
| `main_window_id` | int | 是 | - | 主窗口ID（用于激活最小化窗口） | |
| `coordinate_type` | string | 否 | "grid" | 坐标类型：grid（带网格）/no（无网格） | 定位坐标场景，带网格。内容汇报、分析内容场景，不带网格 |
| `color_mode` | string | 否 | "grayscale" | 颜色模式：grayscale（灰度）/color（原色） | 原色用于整体理解内容。灰度用于排除颜色干扰，增大网格与内容对比度，也排除彩色对关键内容的影响 |

### 网格参数（coordinate_type=grid时）

| 参数 | 类型 | 默认值 | 说明 | 调整方案 |
|------|------|--------|------|----------|
| `grid.density_x` | float | 5.0 | 水平网格密度百分比（0-100），支持1位小数。5.5就代表每5.5%就画一条线 | 网格横线之间间距大，没有覆盖到目标元素，就减小数值。若间距太小，看不到目标元素，或目标被遮挡，就增大 |
| `grid.density_y` | float | 5.0 | 垂直网格密度百分比（0-100），支持1位小数。5.5就代表每5.5%就画一条线 | 网格竖线之间间距大，没有覆盖到目标元素，减小数值。反之增大 |
| `grid.opacity` | int | 50 | 网格透明度(0-100) | 若网格密度不能增加，再增加就导致目标元素没有交叉点。那只能让网格更透明。数字越小越透明 |
| `grid.color` | string | "#ff0000" | 网格颜色(HEX) | 如果网格与截图内容的对比度不够大，就变更颜色，增大差异，让网格更明显 |

**density_x / density_y 说明**：
- 水平和垂直网格密度可独立设置，适用于不同宽高比的窗口（如竖屏手机模拟器 vs 横屏显示器）
- 示例：`density_x=5.0, density_y=10.0` 表示水平每5%一条竖线，垂直每10%一条横线
- 支持小数（如 `3.3`），适用于4K高分辨率截图的精细定位

**注意**：目标元素必须有网格的交叉点，才能让坐标精准。若无交叉点覆盖，就调整网格参数，不能推测坐标。

### 数字参数（coordinate_type=grid时）

| 参数 | 类型 | 默认值 | 说明 | 调整方案 |
|------|------|--------|------|----------|
| `coordinate.number_density` | int | 2 | 数字显示密度 | 数字是多少，就每隔多少个网格展示坐标数字。例如2就是，每隔2格才有坐标。数字越小越密，有坐标数字的交叉点就越多。但可能会遮挡目标元素。数字越大，有数字的交叉点越小，可能会导致你不知道目标元素的具体坐标数字，毕竟只有网格你会读不出来。配合网格密度，你就能从周围的坐标数字计算出目标坐标。网格密度越大，建议数字越稀疏 |
| `coordinate.number_decimal` | int | 0 | 小数位数(0-4) | 4位小数实际在坐标数字上会展示成2位，因为坐标是百分比。当网格密度大时，就需要更精细的数字 |
| `coordinate.number_size` | int | 14 | 字体大小(4-64) | 数字字体很小，你看不清楚时就增大。增大到不要遮挡太多元素就行。优先推荐调整。中度幅度增大，不要仅仅步进1 |
| `coordinate.number_color` | string | "#ff0000" | 数字颜色(HEX) | 数字颜色与截图内容的对比度不高，导致看不清时，就更换颜色 |
| `coordinate.number_opacity` | int | 100 | 数字透明度(0-100) | 数字遮挡了目标元素，但数字密度和大小都调整无效，就调整透明度。数字越小越透明 |

**注意**：如果裁剪放大后，目标元素周围的交叉点都看不到数字，就调整数字密度、数字大小。

### 标记点参数

`marker` 支持传入单个对象或数组，用于在截图上标记坐标位置（外圈空心圆 + 中心实心点）。你可通过标记预览或确认操作坐标是否准确，调整后再执行操作。

每个标记点参数：

| 参数 | 类型 | 默认值 | 说明 | 调整方案 |
|------|------|--------|------|----------|
| `x` | float | - | 标记点横坐标百分比（0-100） | 待确认的坐标 |
| `y` | float | - | 标记点纵坐标百分比（0-100） | 待确认的坐标 |
| `ring_radius` | int | 12 | 外圈空心圆半径（像素） | 标记点外圈的半径，数字越大，圆越大，但可能会遮挡其它元素 |
| `ring_line_width` | int | 2 | 外圈线宽（像素） | 数字越大越粗，但可能会遮挡其它元素 |
| `ring_color` | string | "#FF0000" | 外圈颜色（HEX） | 如果外圈与截图内容对比度不够大，就更换颜色。标记点的颜色不建议与网格颜色一致 |
| `dot_radius` | int | 3 | 中心实心圆半径（像素） | 数字越大越粗，但可能会遮挡其它元素 |
| `dot_color` | string | "#FF0000" | 中心实心圆颜色（HEX） | 如果内圈与截图内容对比度不够大，就更换颜色 |

**说明**：
- 多个标记点建议使用不同颜色区分（通过 `ring_color`/`dot_color`）
- 建议控制在 5-10 个以内，过多标记会影响截图可读性
- 向后兼容：传入单个对象时自动按单个标记处理

### 请求示例

**基础截图**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "coordinate_type": "grid"
}
```

**调整网格参数（密度x/y分离）**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "coordinate_type": "grid",
  "grid": {"density_x": 5.0, "density_y": 10.0, "opacity": 60, "color": "#FF0000"},
  "coordinate": {"number_size": 14, "number_density": 1}
}
```

**带标记点预览**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "coordinate_type": "grid",
  "marker": {"x": 55.0, "y": 65.0}
}
```

**多个标记点预览**（用不同颜色区分）：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "coordinate_type": "grid",
  "marker": [
    {"x": 55.0, "y": 65.0, "ring_color": "#FF0000", "dot_color": "#FF0000"},
    {"x": 30.0, "y": 20.0, "ring_color": "#00FF00", "dot_color": "#00FF00"}
  ]
}
```

**不带网格**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "coordinate_type": "no"
}
```

### 响应处理

**本地请求**（localhost/127.0.0.1/::1）：返回 `image_path`，图片已在服务端保存，直接使用路径。

**远程请求**（局域网IP）：返回 `image_base64`，必须使用脚本处理：
```bash
python scripts/fetch_screenshot_cli.py <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id>
```
脚本会自动解码base64、保存到正确位置、返回图片路径。

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但坐标找不到或网格看不清** → 先调整网格参数，无效后按照 skill.md 步骤8 的读坐标策略排查
2. **API调用失败** → 对照请求参数检查参数格式
3. PrintWindow 调用失败 → 窗口不正确，重新获取窗口

### 操作技巧
- 熟读参数的调整方案，灵活调整，不要一成不变。
---
name: screenshot
description: 截取窗口画面并叠加坐标网格和标记点，用于定位元素坐标、验证操作结果，也可不带网格分析单屏页面。长页面用 scroll_screenshot。
---

# screenshot - 截图

## 快速决策

- 读坐标：使用 `coordinate_type=grid`，默认先不传网格和数字参数，让服务端自适应。
- 看内容：使用 `coordinate_type=no`，避免网格遮挡。
- 目标没有被交叉点覆盖：减小对应方向的 `grid.density_x/y`。
- 数字看不清：优先裁剪放大；必要时调 `coordinate.number_size`、`coordinate.number_stroke_width/color`。
- 首次动态坐标、高风险坐标、新界面坐标：先裁剪放大或 marker 反验，再操作。
- 有候选坐标：使用 `marker.0.x/y` 反向验证；先找标记点实际落在哪里，再判断它是否等于目标。
- 返回 `SELF_CHECK_REQUIRED`：阅读并执行 `references/self_check.md` 自检程序，让关键上下文重新装载，带 `self_check=...` 总结执行内容后重试。
- 返回 `SELF_CHECK_NOT_ALLOWED`：去掉 `self_check` 后重试。

## 脚本调用

基础网格截图：

```bash
python scripts/screenclaw.py screenshot api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} coordinate_type=grid
```

不带网格截图：

```bash
python scripts/screenclaw.py screenshot api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} coordinate_type=no
```

调整网格和数字参数：

```bash
python scripts/screenclaw.py screenshot api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} coordinate_type=grid grid.density_x=3.3 grid.density_y=5 coordinate.number_size=24 coordinate.number_density=1
```

带 marker 反验候选坐标：

```bash
python scripts/screenclaw.py screenshot api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} coordinate_type=grid marker.0.x=55 marker.0.y=65
```

自检重试：

```bash
python scripts/screenclaw.py screenshot api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} coordinate_type=grid self_check="{按 references/self_check.md 复述的内容}"
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ai_app_type` | string | 是 | AI 应用类型 |
| `session_id` | string | 是 | 会话唯一标识 |
| `window_id` | int | 是 | 目标窗口句柄 |
| `main_window_id` | int | 是 | 主窗口 ID |
| `coordinate_type` | string | 否 | `grid` 带网格；`no` 不带网格 |
| `color_mode` | string | 否 | `grayscale` 灰度；`color` 原色 |
| `self_check` | string | 否 | 服务端要求自检时传入 |

## 网格参数

| 点号路径 | 类型 | 说明 | 什么时候调 |
|----------|------|------|------------|
| `grid.density_x` | float | 横向密度百分比，越小竖线越密 | 目标左右方向没有交叉点覆盖 |
| `grid.density_y` | float | 纵向密度百分比，越小横线越密 | 目标上下方向没有交叉点覆盖 |
| `grid.opacity` | int | 网格透明度 0-100 | 网格遮挡内容时降低 |
| `grid.color` | string | 网格颜色 HEX | 与内容对比不足时调整 |

## 数字参数

| 点号路径 | 类型 | 说明 | 什么时候调 |
|----------|------|------|------------|
| `coordinate.number_density` | int | 每隔多少格显示数字 | 周围交叉点没数字，且服务端没有自动调到可读 |
| `coordinate.number_decimal` | int | 小数位 0-4，默认 1 | 需要更精细坐标时 |
| `coordinate.number_size` | int | 数字大小像素 | 数字太小读不清时 |
| `coordinate.number_color` | string | 数字颜色 HEX | 与内容对比不足时 |
| `coordinate.number_opacity` | int | 数字透明度 0-100 | 数字遮挡目标时降低 |
| `coordinate.number_stroke_width` | int | 数字描边宽度，0 关闭 | 复杂背景下通常保持默认 1 |
| `coordinate.number_stroke_color` | string | 数字描边颜色 | 默认白色，不自动变色 |

## 自适应规则

- 服务端先压缩图片，再基于最终输出尺寸绘制网格、数字和 marker。
- 未显式传入的 `grid.density_x/y` 会按约 50px 物理间距自适应。
- 未显式传入的 `coordinate.number_size` 会按网格单元格短边约 0.5 倍自适应。
- `coordinate.number_density` 优先为 1；如果数字会重叠，服务端会自动增大。
- 响应 `data.effective_grid`、`data.effective_coordinate` 是实际生效参数。
- 响应 `data.adaptive_adjustments` 会说明哪些参数被服务端强制调整。

## marker 参数

`marker` 支持数组，用 `marker.0.x`、`marker.0.y` 这类点号路径传入。

marker 的读法是反证，不是确认偏见：

1. 先根据 marker 截图找到标记点实际落在图上的位置。
2. 描述标记点所在位置实际是什么元素、文字、空白或边界。
3. 再判断这个位置是否与目标一致。
4. 如果标记点只是“接近”或落在相邻元素上，坐标仍然错误，必须重新读坐标。

| 点号路径 | 类型 | 说明 |
|----------|------|------|
| `marker.0.x` | float | 标记点横坐标百分比 |
| `marker.0.y` | float | 标记点纵坐标百分比 |
| `marker.0.ring_radius` | int | 外圈半径 |
| `marker.0.ring_line_width` | int | 外圈线宽 |
| `marker.0.ring_color` | string | 外圈颜色 |
| `marker.0.dot_radius` | int | 中心点半径 |
| `marker.0.dot_color` | string | 中心点颜色 |

多个候选坐标可用 `marker.1.x/y`、`marker.2.x/y` 继续添加。建议控制在 5-10 个以内。

## 响应处理

- 本地请求：返回 `image_path`，直接使用路径读图。
- 远程请求：服务端返回 `image_base64`，必须通过统一脚本调用，脚本会自动保存为本地图片路径。
- `data.requested_params` 返回截图相关请求参数摘要。
- `data.effective_params` 返回本次截图实际生效的完整参数。
- `data.effective_grid`、`data.effective_coordinate`、`data.effective_marker` 返回实际生效参数。
- 统一脚本输出图片路径和 message 后，会继续输出去掉 base64/null 的 `Data:` 摘要，优先读取其中的 `effective_params`、`effective_*` 和 `adaptive_adjustments`。
- `data.adaptive_adjustments` 只在 data 中返回，不拼接到 success message。

## 常见问题

1. **看不清数字**：先 `crop_zoom_screenshot`；仍不清楚再调 `coordinate.number_size`、描边或颜色。
2. **目标没被交叉点覆盖**：减小 `grid.density_x/y`，不要推测坐标。
3. **数字重叠**：查看 `adaptive_adjustments`，以 `effective_coordinate` 为准。
4. **marker 不在目标上**：候选坐标错误，回到截图重新读坐标。
5. **返回 SELF_CHECK_NOT_ALLOWED**：当前不应自检，去掉 `self_check` 后重试。
6. **截图窗口不对**：重新 `get_window_list` 并截图候选窗口。

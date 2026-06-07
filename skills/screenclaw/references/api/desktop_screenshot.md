---
name: desktop_screenshot
description: 截取指定显示器画面并叠加坐标网格和标记点，用于桌面级操作的坐标定位和验证。坐标规则与窗口级截图一致。
---

# desktop_screenshot - 桌面截图

## 快速决策

- 读坐标：使用 `coordinate_type=grid`，默认先不传网格参数，让服务端自适应。
- 看内容：使用 `coordinate_type=no`。
- 坐标规则与窗口级 `screenshot` 完全一致，格式 `XxY`，百分比 0-100。
- 网格参数、数字参数、marker 参数与窗口级截图共享同一套体系，详见 `references/api/screenshot.md` 对应章节。
- 截图方式为 mss（所见即所得），不是后台截图。

## 脚本调用

基础网格截图：

```bash
python scripts/screenclaw.py desktop_screenshot api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} monitor_index=0 coordinate_type=grid
```

不带网格截图：

```bash
python scripts/screenclaw.py desktop_screenshot api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} monitor_index=0 coordinate_type=no
```

带 marker 反验：

```bash
python scripts/screenclaw.py desktop_screenshot api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} monitor_index=0 coordinate_type=grid marker.0.x=55 marker.0.y=65
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `monitor_index` | int | 是 | 目标显示器索引 |
| `coordinate_type` | string | 否 | `grid` 带网格；`no` 不带网格 |
| `color_mode` | string | 否 | `grayscale` 灰度；`color` 原色 |
| `self_check` | string | 否 | 服务端要求自检时传入 |

网格参数、数字参数、marker 参数与窗口级 `screenshot` 完全一致，详见 `references/api/screenshot.md` 对应章节。

## 响应处理

与窗口级 `screenshot` 一致：返回 `image_path`（本地）或 `image_base64`（远程）、`effective_grid`、`effective_coordinate`、`effective_marker`、`adaptive_adjustments`。

## 常见问题

1. **返回 MONITOR_NOT_FOUND**：`monitor_index` 越界，先调用 `desktop_get_monitors_list` 确认可用索引。
2. **截图是黑屏**：可能处于锁屏状态。
3. **其他参数问题**：参考窗口级 `screenshot` 的常见问题。

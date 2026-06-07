---
name: batch
description: 批量连续执行多条指令，支持混用窗口级和桌面级操作。适用于稳定流程、固定坐标流程、操作后需要立刻截图的流程。不适用于需要根据前一步结果动态决策的探索阶段。
---

# batch - 批量执行

## 快速决策

- 探索阶段用单步 API，方便读图和调整。
- 流程稳定后再用 batch。
- hover、右键菜单、长按菜单、操作后瞬间状态等易丢失场景，适合在 batch 中接 `wait` 和 `screenshot`/`desktop_screenshot`。
- batch 中多个 screenshot 对自检计数最多算 1 次。
- batch 失败会中断，查看 results 中已执行步骤和失败 message。
- `scroll_screenshot` 不支持 batch。
- `desktop_get_monitors_list` 不支持 batch（GET 端点，无操作意义）。

## 脚本调用

窗口级操作：

```bash
python scripts/screenclaw.py batch api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} step.0.action=click step.0.params.window_id={window_id} step.0.params.main_window_id={main_window_id} step.0.params.x=50 step.0.params.y=35 step.1.action=wait step.1.params.duration_ms=300 step.2.action=screenshot step.2.params.window_id={window_id} step.2.params.main_window_id={main_window_id} step.2.params.coordinate_type=grid
```

桌面级操作：

```bash
python scripts/screenclaw.py batch api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} step.0.action=desktop_click step.0.params.monitor_index=0 step.0.params.x=50 step.0.params.y=35 step.1.action=wait step.1.params.duration_ms=300 step.2.action=desktop_screenshot step.2.params.monitor_index=0 step.2.params.coordinate_type=grid
```

混用窗口级和桌面级（跨应用流程）：

```bash
python scripts/screenclaw.py batch api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} step.0.action=desktop_click step.0.params.monitor_index=0 step.0.params.x=30 step.0.params.y=50 step.1.action=wait step.1.params.duration_ms=500 step.2.action=click step.2.params.window_id={window_id} step.2.params.main_window_id={main_window_id} step.2.params.x=50 step.2.params.y=35
```

batch 内截图自检：

```bash
python scripts/screenclaw.py batch api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} step.0.action=screenshot step.0.params.window_id={window_id} step.0.params.main_window_id={main_window_id} step.0.params.coordinate_type=grid step.0.params.self_check="{按 references/self_check.md 复述的内容}"
```

## 请求参数

**顶层参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ai_app_type` | string | 是 | AI 应用类型 |
| `session_id` | string | 是 | 会话唯一标识 |
| `instructions` | array | 是 | 脚本中用 `step.N.action` 和 `step.N.params.*` 表达 |

**注意**：`window_id`、`main_window_id`、`monitor_index` 不在 batch 顶层，而是在每个 step 的 params 中指定。窗口级 step 需要 `window_id` + `main_window_id`，桌面级 step 需要 `monitor_index`。

## 支持的 action

### 窗口级 action

| action | 说明 | step params 必需项 |
|--------|------|-------------|
| `click` | 点击 | `window_id`, `main_window_id`, `x`, `y` |
| `long_press` | 长按 | `window_id`, `main_window_id`, `x`, `y` |
| `swipe` | 滑动 | `window_id`, `main_window_id`, `start_x`, `start_y`, `end_x`, `end_y` |
| `drag` | 拖拽 | `window_id`, `main_window_id`, `start_x`, `start_y`, `end_x`, `end_y` |
| `scroll` | 滚动 | `window_id`, `main_window_id`, `x`, `y`, `delta` |
| `right_click` | 右键 | `window_id`, `main_window_id`, `x`, `y` |
| `hover` | 悬浮 | `window_id`, `main_window_id`, `x`, `y` |
| `mouse_move` | 鼠标移动 | `window_id`, `main_window_id`, `delta_x`, `delta_y` |
| `input_text` | 输入文本 | `window_id`, `main_window_id`, `x`, `y`, `text` |
| `press_key` | 按键 | `window_id`, `main_window_id`, `key` |
| `wait` | 等待 | `duration_ms` |
| `screenshot` | 窗口截图 | `window_id`, `main_window_id` |
| `crop_zoom_screenshot` | 裁剪放大 | `source_image_path` 或 `source_image_base64` |

### 桌面级 action

| action | 说明 | step params 必需项 |
|--------|------|-------------|
| `desktop_click` | 桌面单击 | `monitor_index`, `x`, `y` |
| `desktop_double_click` | 桌面双击 | `monitor_index`, `x`, `y` |
| `desktop_right_click` | 桌面右键 | `monitor_index`, `x`, `y` |
| `desktop_drag` | 桌面拖拽 | `monitor_index`, `start_x`, `start_y`, `end_monitor_index`, `end_x`, `end_y` |
| `desktop_scroll` | 桌面滚动 | `monitor_index`, `x`, `y`, `delta` |
| `desktop_input_text` | 桌面文本输入 | `monitor_index`, `x`, `y`, `text` |
| `desktop_press_key` | 桌面按键 | `monitor_index`, `keys` |
| `desktop_hover` | 桌面悬浮 | `monitor_index`, `x`, `y` |
| `desktop_screenshot` | 桌面截图 | `monitor_index` |

## 点号路径规则

| 含义 | 点号路径 |
|------|----------|
| 第 0 步动作 | `step.0.action=click` |
| 第 0 步窗口级参数 | `step.0.params.window_id=12345 step.0.params.main_window_id=12345 step.0.params.x=50 step.0.params.y=35` |
| 第 2 步桌面级参数 | `step.2.params.monitor_index=0 step.2.params.x=50 step.2.params.y=35` |
| 第 3 步截图无网格 | `step.3.params.coordinate_type=no` |
| 第 3 步 marker | `step.3.params.marker.0.x=55 step.3.params.marker.0.y=65` |

## 响应处理

- 响应包含 `results` 数组，每条指令对应一个结果。
- 本地图片类结果返回 `image_path`。
- 远程图片类结果返回 `image_base64`，统一脚本会自动落盘。
- batch 内图片类结果同样返回 `requested_params` 和 `effective_*` 参数摘要。

## 常见问题

1. **batch 成功但结果不符合预期**：按最后一张截图验证，不要只看 success。
2. **batch 中断**：查看 results 中最后一个失败步骤的 `error_code/message`。
3. **前一步需要动态判断**：不要 batch，改为单步。
4. **需要保持按键或焦点状态**：把相关动作放在同一个 batch，中间用 `wait` 控制时序。
5. **混用窗口级和桌面级**：每个 step 各自带 `window_id`/`main_window_id` 或 `monitor_index`，互不干扰。

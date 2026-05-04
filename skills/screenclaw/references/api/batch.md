---
name: batch
description: 批量连续执行多条指令，适用于稳定流程、固定坐标流程、操作后需要立刻截图的流程。不适用于需要根据前一步结果动态决策的探索阶段。
---

# batch - 批量执行

## 快速决策

- 探索阶段用单步 API，方便读图和调整。
- 流程稳定后再用 batch。
- hover、右键菜单、长按菜单、操作后瞬间状态等易丢失场景，适合在 batch 中接 `wait` 和 `screenshot`。
- batch 中多个 screenshot 对自检计数最多算 1 次。
- batch 失败会中断，查看 results 中已执行步骤和失败 message。
- `scroll_screenshot` 不支持 batch。

## 脚本调用

点击、等待、截图：

```bash
python scripts/screenclaw.py batch api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} step.0.action=click step.0.params.x=50 step.0.params.y=35 step.1.action=wait step.1.params.duration_ms=300 step.2.action=screenshot step.2.params.coordinate_type=grid
```

hover 后立刻观察隐藏 UI：

```bash
python scripts/screenclaw.py batch api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} step.0.action=hover step.0.params.x=50 step.0.params.y=35 step.1.action=wait step.1.params.duration_ms=300 step.2.action=screenshot step.2.params.coordinate_type=no
```

batch 内截图自检：

```bash
python scripts/screenclaw.py batch api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} step.0.action=screenshot step.0.params.coordinate_type=grid step.0.params.self_check="{按 references/self_check.md 复述的内容}"
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ai_app_type` | string | 是 | AI 应用类型 |
| `session_id` | string | 是 | 会话唯一标识 |
| `window_id` | int | 是 | 默认目标窗口句柄 |
| `main_window_id` | int | 是 | 默认主窗口 ID |
| `instructions` | array | 是 | 脚本中用 `step.N.action` 和 `step.N.params.*` 表达 |

## 支持的 action

| action | 说明 |
|--------|------|
| `click` | 点击 |
| `long_press` | 长按 |
| `swipe` | 滑动 |
| `drag` | 拖拽 |
| `scroll` | 滚动 |
| `right_click` | 右键 |
| `hover` | 悬浮 |
| `mouse_move` | 游戏视角移动 |
| `input_text` | 输入文本 |
| `press_key` | 按键 |
| `wait` | 等待 |
| `screenshot` | 截图，结果在 results 中返回 |
| `crop_zoom_screenshot` | 裁剪放大已有截图 |

## 点号路径规则

| 含义 | 点号路径 |
|------|----------|
| 第 0 步动作 | `step.0.action=click` |
| 第 0 步参数 x | `step.0.params.x=50` |
| 第 2 步截图无网格 | `step.2.params.coordinate_type=no` |
| 第 2 步 marker | `step.2.params.marker.0.x=55 step.2.params.marker.0.y=65` |

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

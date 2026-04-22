---
name: batch
description: 批量连续执行多条指令，按顺序执行。适用：需要执行多个连续操作、操作步骤固定无需中间决策、执行已沉淀的场景模板。不适用：单步操作（用对应API）、需要根据前一步结果动态决策（逐步调用API）。
---

# batch - 批量执行

## 请求

**方法**：POST `/api/batch`

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
| `window_id` | int | 是 | - | 目标窗口句柄 |
| `main_window_id` | int | 是 | - | 主窗口ID |
| `instructions` | array | 是 | - | 多条单操作的指令列表 |

### instructions 结构

每条指令包含：
- `action`：指令类型
- `params`：指令参数（与单独调用该API时的参数相同）

**支持的指令类型**：

| 指令 | 说明 |
|------|------|
| `click` | 点击 |
| `long_press` | 长按 |
| `swipe` | 滑动 |
| `drag` | 拖拽（支持跨窗口：target_window_id/target_main_window_id） |
| `scroll` | 滚动 |
| `right_click` | 右键点击 |
| `hover` | 鼠标悬浮 |
| `mouse_move` | 鼠标移动（游戏视角控制） |
| `input_text` | 输入文本 |
| `press_key` | 按键 |
| `wait` | 等待 |
| `screenshot` | 截图（数据在响应results中返回） |
| `crop_zoom_screenshot` | 裁剪放大已有截图局部（不需要window_id） |

**注意**：`scroll_screenshot`（滚动长截图）不支持 batch，请单独调用。

### 请求示例

```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "instructions": [
    { "action": "screenshot", "params": { "coordinate_type": "grid" } },
    { "action": "click", "params": { "x": 50, "y": 35 } },
    { "action": "wait", "params": { "duration_ms": 300 } },
    { "action": "screenshot", "params": { "coordinate_type": "grid", "marker": {"x": 50, "y": 35} } }
  ]
}
```

### 响应处理

响应包含 `results` 数组，每条指令对应一个结果。batch执行失败时会中断，已执行指令的结果可查看。

- **本地请求**：截图数据返回 `image_path`，直接使用
- **远程请求**：截图数据返回 `image_base64`，需脚本处理：

```bash
python scripts/batch_results_processor.py <api_url> <token> <json_response_file>
```

## 常见问题

### 问题排查
1. **batch成功但某步效果与预期不同** → 按照 skill.md 步骤10 验证，检查该步的坐标和参数
2. **API调用失败** → 对照各操作类型的文档检查参数格式

### 操作技巧
- **操作间添加wait**：确保UI稳定后再执行下一步
- **使用场景模板**：已沉淀的场景模板可直接转换为batch格式
- **失败处理**：batch失败时会中断，检查results中的失败原因
- **操作后瞬间截图**：部分场景不能分步操作，分步会丢失焦点或页面被复原，或者需要立刻观察操作后的效果。可以操作指令后接截图指令。例如验证码场景，操作后需要立刻截图，观察距离正确结果有多大差异。hover效果，操作后需要立刻截图，才能知道hover时有什么新元素显示。

### 特殊说明

- **非阻塞持续时间**：指令内的 duration_ms 是非阻塞的。如 `press_key` 的 `duration_ms=10000`（按住ctrl 10秒），系统会立即执行下一条指令，但ctrl按键会持续10秒。适用于按住ctrl多选文件等场景
- **阻塞式等待**：需要暂停执行下一条指令时，使用 `wait` 指令
- **截图指令**：batch中可包含screenshot，截图数据在响应results对应位置返回
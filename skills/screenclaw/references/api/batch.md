---
name: batch
description: 批量执行多步骤固定流程，减少网络请求
---

# batch - 批量执行

## 使用前必读

### 使用目的和效果
批量执行多条指令，按顺序执行。用于多步骤固定流程（如登录、导航）、减少网络请求次数、执行已沉淀的场景模板。

### 适用场景
- 需要执行多个连续操作
- 操作步骤固定，无需中间决策
- 执行已沉淀的场景模板

### 不适用场景
- 单步操作 → 使用对应API
- 需要根据前一步结果动态决策 → 逐步调用API

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
| `instructions` | array | 是 | - | 指令列表 |

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
| `drag` | 拖拽（文件拖放、窗口拖动） |
| `scroll` | 滚动 |
| `right_click` | 右键点击 |
| `hover` | 鼠标悬浮 |
| `mouse_move` | 鼠标移动（游戏视角控制） |
| `input_text` | 输入文本 |
| `press_key` | 按键 |
| `wait` | 等待 |
| `screenshot` | 截图（数据在响应results中返回） |

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
    { "action": "screenshot", "params": { "coordinate_type": "grid" } }
  ]
}
```

### 脚本调用

**PowerShell（推荐）**：使用 `api_call_batch.ps1`，简化指令格式，无需JSON引号：
```powershell
powershell -ExecutionPolicy Bypass -File scripts/api_call_batch.ps1 -ApiUrl <url> -Token <token> -SessionId <id> -WindowId <id> -MainWindowId <id> -Instructions "screenshot(coordinate_type=grid);click(x=50,y=35);wait(duration_ms=300);screenshot(coordinate_type=grid)"
```

**Python**：使用 `api_call.py`，instructions 传 JSON 字符串：
```bash
python scripts/api_call.py <api_url> <token> batch ai_app_type=<值> session_id=<值> main_window_id=<值> instructions='[{"action":"click","params":{"x":50,"y":35}}]'
```

### 响应处理

响应包含 `results` 数组，每条指令对应一个结果。batch执行失败时会中断，已执行指令的结果可查看。

- **本地请求**：截图数据返回 `image_path`，直接使用
- **远程请求**：截图数据返回 `image_base64`，需脚本处理：

```bash
python scripts/batch_results_processor.py <api_url> <token> <json_response_file>
```

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `USER_DENIED` | 用户拒绝操作（hijack模式） | 用户取消了确认弹窗 |
| `OPERATION_FAILED` | 操作失败 | 1.换其他子窗口 2.大调坐标+网格参数重截图 3.Evaluator验证周边元素 4.仍失败才考虑hijack |

## 常见问题

### 遇到问题时的排查顺序
1. **batch成功但某步效果与预期不同** → 查阅 SKILL.md「常见问题排查」
2. **API调用失败** → 对照各操作类型的文档检查参数格式

### 操作技巧
- **操作间添加wait**：确保UI稳定后再执行下一步
- **使用场景模板**：已沉淀的场景模板可直接转换为batch格式
- **失败处理**：batch失败时会中断，检查results中的失败原因
- **hijack确认**：batch中包含hijack操作时，会依次弹出确认窗口

### 特殊说明

- **非阻塞持续时间**：指令内的 duration_ms 是非阻塞的。如 `press_key` 的 `duration_ms=10000`（按住ctrl 10秒），系统会立即执行下一条指令，但ctrl按键会持续10秒。适用于按住ctrl多选文件等场景
- **阻塞式等待**：需要暂停执行下一条指令时，使用 `wait` 指令
- **截图指令**：batch中可包含screenshot，截图数据在响应results对应位置返回

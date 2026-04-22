---
name: press_key
description: 模拟键盘按键，组合键用空格连接。适用：触发快捷键（Ctrl+C复制、Ctrl+V粘贴）、发送特殊按键（Enter、Escape）、组合键操作等。不适用：鼠标操作即可完成（用click等）。
---

# press_key - 按键

## 请求

**方法**：POST `/api/press_key`

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
| `key` | string | 是 | - | 按键，空格分隔组合键 |
| `x` | float | 否 | - | 先点击此横坐标再按键 |
| `y` | float | 否 | - | 先点击此纵坐标再按键 |
| `duration_ms` | int | 否 | 0 | 按住时长（毫秒），0=立即释放 |
| `action_method` | string | 否 | "background" | 操作方式 |

**参数说明**：
- `key`：按键名称，空格分隔组合键（如 `ctrl c`，不是 `ctrl+c`）
- `x`、`y`：推荐传参，系统会先鼠标点击，再按键。可以不传，不传时，不点击直接按键

### 请求示例

```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "key": "ctrl c",
  "action_method": "hijack"
}
```

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但按键无效** → 按照 skill.md 步骤10 验证，换子窗口、传x/y先点击激活焦点
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **激活后输入**：传x和y参数，先点击位置确保焦点正确
- **组合指令**：按键后如果需要保持选中状态，请用batch连续操作。否则background和hijack会恢复原样，会取消选中状态。例如ctrl+A
- **考虑用户电脑环境**：如果用户是windows，使用windows键盘。如果用户是mac，使用mac键盘
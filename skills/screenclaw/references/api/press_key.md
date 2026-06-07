---
name: press_key
description: 触发快捷键、发送特殊按键
---

# press_key - 按键

## 使用前必读

### 使用目的和效果
模拟键盘按键。可触发快捷键（Ctrl+C复制、Ctrl+V粘贴）、发送特殊按键（Enter确认、Escape取消）、组合键操作（Ctrl+S保存）。


### 适用场景
- 需要触发快捷键
- 需要发送特殊按键
- 鼠标操作无法完成需求

### 不适用场景
- 鼠标操作即可完成 → 使用 `click` 等

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
| `action_method` | string | 否 | "background" | 优先用hijack |

**参数说明**：
- `key`：按键名称，空格分隔组合键（如 `ctrl c`，不是 `ctrl+c`）
- `x`、`y`：强烈推荐传参，先点击确保焦点正确再按键

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

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `USER_DENIED` | 用户拒绝操作 | 用户取消了确认弹窗 |

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但按键无效** → 查阅 SKILL.md「常见问题排查」
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **子窗口**：按键事件需要发送到具体的接收窗口，使用子窗口的window_id
- **点击激活**：传x和y参数，先点击位置确保焦点正确
- **确认弹窗**：每次执行都会弹出确认窗口，需用户确认
- **组合指令**：按键后需要保持选中状态，请用组合指令连续操作。否则background和hijack会恢复原样，取消选中状态。例如ctrl+A

### 常用按键

**单键**：a-z、0-9、enter、escape/esc、space、tab、backspace、delete/del、f1-f12

**组合键**（空格分隔，不用+号）：
- `ctrl c` 复制 | `ctrl v` 粘贴 | `ctrl x` 剪切 | `ctrl a` 全选
- `ctrl s` 保存 | `ctrl z` 撤销 | `ctrl y` 重做
- `alt tab` 切换窗口 | `ctrl shift s` 另存为

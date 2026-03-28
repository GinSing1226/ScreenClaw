---
name: press_key
description: 触发快捷键功能（Ctrl+C复制）、发送特殊按键（Enter确认）
---

# press_key - 按键

## 使用目的
模拟键盘按键操作，用于：
- 触发快捷键功能（如Ctrl+C复制、Ctrl+V粘贴）
- 发送特殊按键（如Enter确认、Escape取消）
- 组合键操作（如Ctrl+S保存）

## 什么时候用
- 需要触发快捷键
- 需要发送特殊按键
- 鼠标操作无法完成需求

## 什么时候不用
- 鼠标操作即可完成（使用click等）

## 重要说明
此操作**只支持 hijack 模式**，会激活窗口并短暂占用鼠标键盘，执行前会弹出确认窗口。

---

## 请求

**方法**：POST
**路径**：`/api/press_key`

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 | 从哪里获取 |
|------|------|------|--------|------|----------|
| `ai_app_type` | string | 是 | - | AI应用类型 | 判断当前AI是什么应用，就用什么值 |
| `session_id` | string | 是 | - | 会话唯一标识 | 获取当前会话唯一标识，获取不到则随机生成 |
| `window_id` | int | 是 | - | 目标窗口句柄 | 从get_window_list获取 |
| `main_window_id` | int | 否 | - | 主窗口ID（用于恢复窗口） | 从get_window_list获取 |
| `key` | string | 是 | - | 按键，空格分隔组合键 | 根据需要设置 |
| `x` | float | 否 | - | 先点击此横坐标再按键 | 从截图分析得出 |
| `y` | float | 否 | - | 先点击此纵坐标再按键 | 从截图分析得出 |
| `duration_ms` | int | 否 | 0 | 按住时长（毫秒），0=立即释放 | 根据需要设置 |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack | **只支持hijack** |

### 参数说明

- `key`：按键名称，空格分隔组合键（如 `ctrl c`，不是 `ctrl+c`）
- `x`、`y`：可选，不传则直接按键（不点击），传则先点击该位置再按键
- `duration_ms`：按住时长，`0` 表示立即释放

### 请求示例

#### 复制（Ctrl+C）
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "key": "ctrl c",
  "action_method": "hijack"
}
```

#### 粘贴（Ctrl+V）
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "key": "ctrl v",
  "action_method": "hijack"
}
```

#### 保存（Ctrl+S）
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "key": "ctrl s",
  "action_method": "hijack"
}
```

#### 确认（Enter）
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "key": "enter",
  "action_method": "hijack"
}
```

#### 点击位置后再按键
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "x": 50.0,
  "y": 50.0,
  "key": "ctrl a",
  "action_method": "hijack"
}
```

---

## 响应

### 成功响应
```json
{
  "success": true,
  "message": "按键成功"
}
```

---

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `USER_DENIED` | 用户拒绝操作 | 用户取消了确认弹窗 |

---

## 常用按键

### 单键
- `a` - `z`：字母键
- `0` - `9`：数字键
- `enter`：回车键
- `escape` 或 `esc`：取消键
- `space`：空格键
- `tab`：制表键
- `backspace`：退格键
- `delete` 或 `del`：删除键
- `f1` - `f12`：功能键

### 组合键
- `ctrl c`：复制
- `ctrl v`：粘贴
- `ctrl x`：剪切
- `ctrl a`：全选
- `ctrl s`：保存
- `ctrl z`：撤销
- `ctrl y`：重做
- `alt tab`：切换窗口
- `ctrl shift s`：另存为

**注意**：组合键用空格分隔，不要用 `+` 号。

---

## 使用技巧

1. **子窗口**：按键事件需要发送到具体的接收窗口，使用子窗口的window_id
2. **点击激活**：传x和y参数，先点击位置确保焦点正确
3. **确认弹窗**：每次执行都会弹出确认窗口，需用户确认

---
name: click
description: 触发按钮功能、进入页面、激活控件
---

# click - 点击

## 使用前必读

### 使用目的和效果
在指定坐标执行点击操作。可触发按钮功能（确认、取消、提交）、进入页面（链接、卡片）、激活控件（输入框、选项）。

### 适用场景
- 需要触发按钮功能
- 需要进入某个页面或打开某个功能
- 需要激活某个控件

### 不适用场景
- 需要输入文本 → 使用 `input_text`（自带点击后输入，不建议分步操作）
- 需要长按触发 → 使用 `long_press`
- 需要滑动/滚动 → 使用 `swipe`/`scroll`

## 请求

**方法**：POST `/api/click`

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
| `main_window_id` | int | 是 | - | 主窗口ID（用于激活最小化窗口） |
| `x` | float | 是 | - | 横坐标 |
| `y` | float | 是 | - | 纵坐标 |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack |

### 操作方式

| 方式 | 特点 | 兼容性 |
|------|------|--------|
| `background` | 无感操作，不干扰用户 | 兼容性稍差 |
| `hijack` | 会短暂接管，需用户确认 | 兼容性好 |

**建议**：优先background，无效时用hijack

### 请求示例

```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "x": 50.0,
  "y": 30.0,
  "action_method": "background"
}
```

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `USER_DENIED` | 用户拒绝操作（hijack模式） | 用户取消了确认弹窗 |
| `OPERATION_FAILED` | 操作失败 | 1.换其他子窗口 2.大调坐标+网格参数重截图 3.Evaluator验证周边元素 4.仍失败才考虑hijack |

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但无效果** → 查阅 SKILL.md「常见问题排查」
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **子窗口**：点击无效时，尝试使用子窗口的window_id
- **输入文本**：输入文本请查阅 `input_text.md`，input_text自带点击后输入

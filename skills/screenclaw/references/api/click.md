---
name: click
description: 单击指定坐标，触发按钮、进入页面、激活控件。适用：触发按钮功能、进入页面/链接、激活控件（输入框、选项）。不适用：需要输入文本（用input_text，自带点击后输入）、需要长按（用long_press）、需要滑动/滚动（用swipe/scroll）。
---

# click - 点击

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

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但无效果** → 按照 skill.md 步骤10 的验证策略，换坐标、换窗口、调参数重试
2. **API调用失败** → 对照请求参数检查参数格式
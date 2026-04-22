---
name: right_click
description: 在指定坐标右键点击，打开上下文菜单。适用：需要打开上下文菜单、通过右键菜单访问功能、左键操作无法完成需求。不适用：左键操作即可完成（用click）。
---

# right_click - 右键点击

## 请求

**方法**：POST `/api/right_click`

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
  "y": 50.0,
  "action_method": "background"
}
```

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但菜单没出来** → 按照 skill.md 步骤10 验证，换坐标、换窗口重试
2. **API调用失败** → 对照请求参数检查参数格式、基于接口返回内容处理

### 操作技巧
- **组合右键+截图**：右键点击后，上下文菜单可能受其它内容影响消失。右键后需立刻截图，了解菜单项的坐标后，再用组合指令点击上下文菜单的具体菜单项
- **子窗口或独立进程**：如果右键后立刻截图，没发现上下文菜单。很可能是菜单新开了子窗口或子进程，需要重新获取窗口列表
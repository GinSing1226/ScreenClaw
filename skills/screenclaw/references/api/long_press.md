---
name: long_press
description: 在指定坐标长按，触发长按菜单、需要长按的特殊功能。适用：显示长按菜单（上下文菜单）、应用需要长按触发的功能。不适用：普通点击即可触发的功能（用click）。
---

# long_press - 长按

## 请求

**方法**：POST `/api/long_press`

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
| `duration_ms` | int | 否 | 500 | 长按时长（毫秒） |
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
  "duration_ms": 1000,
  "action_method": "background"
}
```

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但菜单没出来** → 按照 skill.md 步骤10 验证，换坐标、换窗口重试
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **组合长按+截图**：长按后，上下文菜单可能受其它内容影响消失。需立刻截图，了解菜单项的坐标后，再用组合指令点击上下文菜单的具体菜单项
- **时长调整**：某些应用可能需要更长或更短的长按时长

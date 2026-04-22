---
name: swipe
description: 从起始坐标滑动到终止坐标，触摸式滑动。适用：触摸式滑动（如移动应用模拟器、游戏）、上下左右翻页。不适用：鼠标滚轮滚动（用scroll）、简单点击（用click）、选中物体并移动（用drag）。
---

# swipe - 滑动

## 请求

**方法**：POST `/api/swipe`

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
| `window_id` | int | 是 | - | 目标窗口句柄（建议优先使用子窗口） |
| `main_window_id` | int | 是 | - | 主窗口ID |
| `start_x` | float | 是 | - | 起始横坐标 |
| `start_y` | float | 是 | - | 起始纵坐标 |
| `end_x` | float | 是 | - | 结束横坐标 |
| `end_y` | float | 是 | - | 结束纵坐标 |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack |

### 请求示例

```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "start_x": 50.0,
  "start_y": 80.0,
  "end_x": 50.0,
  "end_y": 20.0,
  "action_method": "background"
}
```

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但效果与预期不同** → 按照 skill.md 步骤10 验证，换坐标、换窗口重试
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **代替滚动**：在部分软件里滚动可能不生效，可尝试用滑动代替。特别是移动端、游戏等软件
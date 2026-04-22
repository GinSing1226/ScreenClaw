---
name: scroll
description: 在指定位置执行鼠标滚轮滚动。适用：浏览长内容或列表、上下滚动页面、内容超出可视范围。不适用：触摸式滑动（用swipe）、简单点击（用click）。
---

# scroll - 滚动

## 请求

**方法**：POST `/api/scroll`

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
| `x` | float | 是 | - | 鼠标位置横坐标 |
| `y` | float | 是 | - | 鼠标位置纵坐标 |
| `delta` | int | 是 | - | 滚动量（正值向上，负值向下） |
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
  "delta": -120,
  "action_method": "background"
}
```

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但滚动效果不对** → 按照 skill.md 步骤10 验证，换坐标、调delta重试
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **delta值**：不同软件的滚动程度差异很大，需截图多次尝试。建议先试用小值（如 -120），根据效果调整
- **滚动方向**：负值向下滚动（如 -120），正值向上滚动（如 120）
- **鼠标位置**：x和y指定滚动时鼠标的位置，通常放在内容区域中央
- **background遮挡**：background模式下滚动坐标不能被其他软件遮挡，若被遮挡，可选hijack
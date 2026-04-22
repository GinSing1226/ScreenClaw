---
name: hover
description: 鼠标悬浮到指定坐标并停留，触发悬停效果。适用：触发tooltip/提示框、显示隐藏的UI元素（如滚动条），hover后立即截图捕获隐藏UI。不适用：需要点击（用click）、需要输入文本（用input_text）。
---

# hover - 鼠标悬浮

## 请求

**方法**：POST `/api/hover`

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
| `duration_ms` | int | 否 | 500 | 停留时长（毫秒） |
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
1. **API成功但tooltip没出来** → 按照 skill.md 步骤10 验证，换坐标重试
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **组合hover+截图**：在batch中使用 hover + wait + screenshot，一次性捕获隐藏UI
- **配合wait**：hover后添加短暂wait，确保UI元素完全显示后再截图。batch里的hover是半阻塞的，hover启动后，会立刻执行后续指令。所以必须用wait指令等待隐藏UI出现。不能依赖hover自身的duration
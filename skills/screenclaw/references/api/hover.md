---
name: hover
description: 鼠标悬浮触发隐藏UI或tooltip
---

# hover - 鼠标悬浮

## 使用前必读

### 使用目的和效果
将鼠标移动到指定坐标并停留。可触发悬停效果（tooltip、提示框）、显示隐藏的UI元素。常配合截图使用：hover后再截图捕获隐藏UI。

### 适用场景
- 需要触发悬停提示或tooltip
- 需要显示隐藏的UI元素
- 常配合截图：hover后再截图捕获隐藏UI

### 不适用场景
- 需要点击 → 使用 `click`
- 需要输入文本 → 使用 `input_text`

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

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `OPERATION_FAILED` | 操作失败 | 1.换其他子窗口 2.大调坐标+网格参数重截图 3.Evaluator验证周边元素 4.仍失败才考虑hijack |

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但tooltip没出来** → 查阅 SKILL.md「常见问题排查」
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **hover后截图**：常用场景是hover后再截图，捕获隐藏的UI元素
- **调整停留时长**：某些UI元素需要更长的hover时间才会显示
- **配合wait**：hover后添加短暂wait，确保UI元素完全显示后再截图
- **批量操作**：在batch中使用 hover + wait + screenshot，一次性捕获隐藏UI

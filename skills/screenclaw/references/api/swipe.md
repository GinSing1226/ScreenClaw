---
name: swipe
description: 触摸式滑动（翻页、切换标签、拖拽）
---

# swipe - 滑动

## 使用前必读

### 使用目的和效果
从起始坐标滑动到终止坐标。可翻页（上下滑动）、切换标签（左右滑动）、拖拽元素。

### 适用场景
- 需要触摸式滑动（如移动应用模拟器）
- 需要翻页或切换标签
- 需要拖拽元素

### 不适用场景
- 鼠标滚轮滚动 → 使用 `scroll`
- 简单点击 → 使用 `click`

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

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `OPERATION_FAILED` | 操作失败 | 1.换其他子窗口 2.大调坐标+网格参数重截图 3.Evaluator验证周边元素 4.仍失败才考虑hijack |

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但效果与预期不同** → 查阅 SKILL.md「常见问题排查」
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **常用滑动方向**：
  - 向上翻页：start_y=80, end_y=20（从下往上滑）
  - 向下翻页：start_y=20, end_y=80（从上往下滑）
  - 向左翻页：start_x=80, end_x=20（从右往左滑）
  - 向右翻页：start_x=20, end_x=80（从左往右滑）
- **子窗口**：滑动通常需要子窗口才能响应

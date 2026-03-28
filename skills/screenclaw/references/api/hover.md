---
name: hover
description: 鼠标悬浮到目标位置并停留，用于触发隐藏的UI交互或悬停提示
---

# hover - 鼠标悬浮

## 使用目的
将鼠标移动到指定坐标并停留，用于：
- 触发悬停效果（tooltip、提示框）
- 显示隐藏的UI交互元素
- 触发鼠标悬浮时的菜单或选项

## 什么时候用
- 需要触发悬停提示或tooltip
- 需要显示隐藏的UI元素
- 需要触发鼠标悬浮时的交互效果
- 常配合截图使用：hover后再截图，捕获隐藏的UI

## 什么时候不用
- 需要点击（使用click）
- 需要输入文本（使用input_text）

---

## 请求

**方法**：POST
**路径**：`/api/hover`
**请求头**：
```
Authorization: Bearer {token}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 | 从哪里获取 |
|------|------|------|--------|------|----------|
| `ai_app_type` | string | 是 | - | AI应用类型 | 判断当前AI是什么应用，就用什么值 |
| `session_id` | string | 是 | - | 会话唯一标识 | 获取当前会话唯一标识，获取不到则随机生成 |
| `window_id` | int | 是 | - | 目标窗口句柄 | 从get_window_list获取 |
| `main_window_id` | int | 否 | - | 主窗口ID（用于恢复窗口） | 从get_window_list获取 |
| `x` | float | 是 | - | 横坐标（0-100，百分比） | 从截图分析得出 |
| `y` | float | 是 | - | 纵坐标（0-100，百分比） | 从截图分析得出 |
| `duration_ms` | int | 否 | 500 | 停留时长（毫秒） | 根据需要调整 |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack | 优先background |

### 请求示例

#### 基础悬浮（默认停留500ms）
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "x": 50.0,
  "y": 30.0,
  "action_method": "background"
}
```

#### 悬停1秒后截图
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "instructions": [
    { "action": "hover", "params": { "x": 50, "y": 30, "duration_ms": 1000, "action_method": "background" } },
    { "action": "wait", "params": { "duration_ms": 100 } },
    { "action": "screenshot", "params": { "coordinate_type": "grid" } }
  ]
}
```

#### 自定义停留时长
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "x": 50.0,
  "y": 30.0,
  "duration_ms": 2000,
  "action_method": "background"
}
```

---

## 响应

### 成功响应
```json
{
  "success": true,
  "message": "悬浮成功"
}
```

---

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `OPERATION_FAILED` | 操作失败 | 检查坐标，尝试hijack模式 |

---

## 使用技巧

1. **hover后截图**：常用场景是hover后再截图，捕获隐藏的UI元素
2. **调整停留时长**：某些UI元素可能需要更长的hover时间才会显示
3. **配合wait**：hover后添加短暂wait，确保UI元素完全显示后再截图
4. **优先background**：hover通常可以用background模式，不干扰用户
5. **批量操作**：在batch中使用hover + screenshot，一次性捕获隐藏UI

---

## 常用场景示例

### 触发tooltip并截图
```json
{
  "instructions": [
    { "action": "hover", "params": { "x": 30, "y": 20, "duration_ms": 800 } },
    { "action": "wait", "params": { "duration_ms": 200 } },
    { "action": "screenshot", "params": { "coordinate_type": "grid" } }
  ]
}
```

### 显示隐藏菜单
```json
{
  "instructions": [
    { "action": "hover", "params": { "x": 50, "y": 10, "duration_ms": 500 } },
    { "action": "wait", "params": { "duration_ms": 300 } },
    { "action": "screenshot", "params": { "coordinate_type": "grid" } },
    { "action": "click", "params": { "x": 50, "y": 15, "action_method": "background" } }
  ]
}
```

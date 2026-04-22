---
name: mouse_move
description: 相对位移移动鼠标（游戏视角控制），使用 mouse_event 硬件级事件。适用：游戏中通过鼠标移动控制视角、需要发送硬件级鼠标移动事件（Raw Input / DirectInput）。不适用：瞬移鼠标到目标位置（用hover）、按住左键拖拽（用drag）、快速触摸式滑动（用swipe）、无感后台操作（不支持background）。约束：仅支持 hijack 和 delegated（托管）模式，不支持 background。
---

# mouse_move - 鼠标移动

## 请求

**方法**：POST `/api/mouse_move`

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
| `main_window_id` | int | 否 | - | 主窗口ID |
| `delta_x` | int | 是 | - | 水平相对位移（像素），正值向右，负值向左 |
| `delta_y` | int | 是 | - | 垂直相对位移（像素），正值向下，负值向上 |
| `duration_ms` | int | 否 | 300 | 移动时长（毫秒），控制移动速度 |
| `action_method` | string | 否 | "hijack" | 操作方式：hijack（托管模式下自动路由为 delegated） |


### 请求示例

```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "delta_x": 200,
  "delta_y": 0,
  "duration_ms": 300,
  "action_method": "hijack"
}
```

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但游戏视角没变** → 增大 delta 值（游戏灵敏度可能较低）
2. **API调用失败** → 确认使用 hijack 模式

### 操作技巧
- **delta 值说明**：实际旋转角度取决于游戏灵敏度设置，需要通过截图-调整-截图循环来确定合适的值。旋转的目的是找到目标元素，不必纠结旋转了多少角度。
- **只顺着一个方向旋转**：不要先右旋，又左旋，这样只会让你保持原角度。要一直右旋，就能360°。
---
name: mouse_move
description: 相对位移移动鼠标（游戏视角控制），使用 mouse_event 硬件级事件，仅 hijack/托管模式
---

# mouse_move - 鼠标移动

## 使用前必读

### 使用目的和效果
通过相对位移移动鼠标，不按下任何键。使用 `mouse_event(MOUSEEVENTF_MOVE)` 发送硬件级相对移动事件，可被游戏 Raw Input 机制识别。适用于游戏视角控制等场景。

### 适用场景
- 游戏中通过鼠标移动控制视角方向
- 需要发送硬件级鼠标移动事件（Raw Input / DirectInput）

### 不适用场景
- 瞬移鼠标到目标位置 → 使用 `hover`
- 按住左键拖拽 → 使用 `drag`
- 快速触摸式滑动 → 使用 `swipe`
- 无感后台操作 → 不支持 background 模式

### 仅支持 hijack / 托管模式
此操作不支持 `background` 模式。因为游戏通过 Raw Input API 读取硬件级鼠标事件，PostMessage 无法伪造此类输入。

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

### 操作方式

| 方式 | 特点 | 支持 |
|------|------|------|
| `background` | 无感操作 | ❌ 不支持 |
| `hijack` | 短暂接管，需用户确认 | ✅ 支持 |
| `delegated` | 托管模式，无需确认 | ✅ 支持 |

**注意**：此操作仅支持 `hijack` 和托管（delegated）模式，不支持 `background` 模式。因为游戏通过 Raw Input API 读取硬件级鼠标事件，PostMessage 无法伪造此类输入。

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

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `OPERATION_FAILED` | 操作失败 | 1.调整 delta 值 2.调整 duration_ms |

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但游戏视角没变** → 增大 delta 值（游戏灵敏度可能较低）
2. **API调用失败** → 确认使用 hijack 模式

### 操作技巧
- **游戏视角控制**：
  - 向右看：`delta_x=200, delta_y=0`
  - 向左看：`delta_x=-200, delta_y=0`
  - 向上看：`delta_x=0, delta_y=-150`
  - 向下看：`delta_x=0, delta_y=150`
  - 斜方向：`delta_x=200, delta_y=-100`（右上方）
- **delta 值说明**：实际旋转角度取决于游戏灵敏度设置，需要通过截图-调整-截图循环来确定合适的值
- **duration_ms 调整**：
  - `100`：快速移动，适合大幅视角调整
  - `300`（默认）：标准速度
  - `500`+：慢速移动，适合精细操作

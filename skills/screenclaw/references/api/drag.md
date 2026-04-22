---
name: drag
description: 从起始坐标拖拽到终止坐标，按住鼠标左键移动后释放。适用：文件拖放、窗口元素拖动（面板位置、滑块）、需要精确控制速度的拖放操作、跨窗口/跨进程拖拽（如从文件管理器拖文件到其他应用，但其实更推荐复制粘贴实现跨窗口/进程玩法）。不适用：快速触摸式滑动（用swipe）、鼠标滚轮滚动（用scroll）、简单点击（用click）。
---

# drag - 拖拽

## 请求

**方法**：POST `/api/drag`

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
| `window_id` | int | 是 | - | 源窗口句柄（拖拽起始窗口） |
| `main_window_id` | int | 是 | - | 源主窗口ID |
| `start_x` | float | 是 | - | 起始横坐标（相对于源窗口） |
| `start_y` | float | 是 | - | 起始纵坐标（相对于源窗口） |
| `end_x` | float | 是 | - | 终止横坐标（跨窗口时相对于目标窗口） |
| `end_y` | float | 是 | - | 终止纵坐标（跨窗口时相对于目标窗口） |
| `duration_ms` | int | 否 | 500 | 拖拽时长（毫秒），控制移动速度 |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack |
| `target_window_id` | int | 否 | - | 目标窗口句柄（跨窗口拖拽时传入，end_x/end_y 相对于此窗口） |
| `target_main_window_id` | int | 否 | - | 目标主窗口ID（可选，用于恢复目标窗口的最小化/隐藏状态） |

### 跨窗口拖拽说明

设置 `target_window_id` 后，拖拽起点和终点分别在两个不同窗口：
- `start_x` / `start_y`：相对于 `window_id`（源窗口）
- `end_x` / `end_y`：相对于 `target_window_id`（目标窗口）
- 跨窗口拖拽自动强制 `action_method = "hijack"`，无需手动指定

### 操作方式

| 方式 | 特点 | 兼容性 |
|------|------|--------|
| `background` | 无感操作，不干扰用户 | 优先使用，不支持跨窗口 |
| `hijack` | 会短暂接管，需用户确认 | 最后之策，支持跨窗口 |

**建议**：优先background，无效时用hijack。操作模式选择详见 skill.md 步骤9

### 请求示例

**同窗口拖拽**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "start_x": 30.0,
  "start_y": 50.0,
  "end_x": 70.0,
  "end_y": 50.0,
  "duration_ms": 500,
  "action_method": "background"
}
```

**跨窗口拖拽**（如从文件管理器拖文件到微信）：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "target_window_id": 2001,
  "target_main_window_id": 2001,
  "start_x": 50.0,
  "start_y": 50.0,
  "end_x": 50.0,
  "end_y": 50.0,
  "duration_ms": 1000
}
```

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但效果与预期不同** → 按照 skill.md 步骤10 验证，换坐标、调duration_ms重试
2. **跨窗口拖拽失败** → 确认 target_window_id 是否正确（可通过 get_window_list 获取）
3. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **duration_ms 调整**：
  - `300`：快速拖拽，接近滑动速度
  - `500`（默认）：标准拖拽，适合大多数同窗口场景
  - `1000`+：慢速拖拽，适合跨窗口或需要精确定位的场景
- **跨窗口拖拽**：两个窗口需要都可见（未被最小化），传入 target_main_window_id 可自动从最小化恢复目标窗口。两个窗口的坐标都要定位准确
- **拖放失败时**：尝试增大 duration_ms，部分应用需要较慢的拖拽才能识别放下操作
- **优先考虑复制粘贴**：跨窗口拖拽是强打断操作，不推荐使用，推荐先在源窗口复制，再到目标窗口粘贴

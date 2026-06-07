---
name: drag
description: 拖拽操作（文件拖放、窗口元素拖动），支持速度控制
---

# drag - 拖拽

## 使用前必读

### 使用目的和效果
从起始坐标拖拽到终止坐标，按住鼠标左键移动到目标位置后释放。适用于文件拖放、窗口元素拖动等需要精确控制速度的场景。

### 适用场景
- 需要拖拽文件到另一个文件夹
- 需要拖动窗口元素（如调整面板位置、拖动滑块）
- 需要精确控制移动速度的拖放操作

### 不适用场景
- 快速触摸式滑动（翻页、切换标签） → 使用 `swipe`
- 鼠标滚轮滚动 → 使用 `scroll`
- 简单点击 → 使用 `click`

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
| `window_id` | int | 是 | - | 目标窗口句柄（建议优先使用子窗口） |
| `main_window_id` | int | 是 | - | 主窗口ID |
| `start_x` | float | 是 | - | 起始横坐标 |
| `start_y` | float | 是 | - | 起始纵坐标 |
| `end_x` | float | 是 | - | 结束横坐标 |
| `end_y` | float | 是 | - | 结束纵坐标 |
| `duration_ms` | int | 否 | 500 | 拖拽时长（毫秒），控制移动速度 |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack |

### 操作方式

| 方式 | 特点 | 兼容性 |
|------|------|--------|
| `background` | 无感操作，不干扰用户 | 兼容性稍差 |
| `hijack` | 会短暂接管，需用户确认 | 兼容性好 |

**建议**：优先background，无效时用hijack

### 请求示例

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

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `OPERATION_FAILED` | 操作失败 | 1.换其他子窗口 2.大调坐标+网格参数重截图 3.调整duration_ms 4.仍失败才考虑hijack |

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但效果与预期不同** → 查阅 SKILL.md「常见问题排查」
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **duration_ms 调整**：
  - `300`：快速拖拽，接近滑动速度
  - `500`（默认）：标准拖拽，适合大多数场景
  - `1000`：慢速拖拽，适合需要精确定位的场景
- **拖放失败时**：尝试增大 duration_ms，部分应用需要较慢的拖拽才能识别放下操作
- **子窗口**：拖拽通常需要子窗口才能响应

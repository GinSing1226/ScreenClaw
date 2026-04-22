---
name: wait
description: batch api里多指令之间的等待时间。结合 `batch.md` 使用。会话过程中的等待，请用你自己的sleep工具。
---

# wait - 等待

## 请求

**方法**：POST `/api/wait`

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
| `duration_ms` | int | 是 | - | 等待时长（毫秒） |
| `random_range` | int | 否 | 0 | 随机波动范围（毫秒），防止被风控，实际等待 `duration_ms ± random_range` |

**注意**：`wait` 不需要 `main_window_id` 参数。

### 请求示例

精确等待（向后兼容）：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "duration_ms": 300
}
```

随机等待（防风控）：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "duration_ms": 1000,
  "random_range": 300
}
```

> 上例实际等待 700~1300ms 之间的随机值。

### 在 batch 中使用

```json
{
  "instructions": [
    {"action": "click", "params": {"x": 50, "y": 50}},
    {"action": "wait", "params": {"duration_ms": 500, "random_range": 200}},
    {"action": "screenshot", "params": {"coordinate_type": "no"}}
  ]
}
```

## 常见问题

### 遇到问题时的排查顺序
1. **等待后界面无变化** → 坐标不正确，导致操作无效。按照 `skill.md` 重新读坐标
2. **API调用失败** → 检查参数格式

## 操作技巧
- **操作后等待**：batch组合指令里，每次点击、输入等操作后建议添加wait等待UI稳定、也可以防止被风控
- **批量操作**：在batch指令中使用wait，减少网络请求
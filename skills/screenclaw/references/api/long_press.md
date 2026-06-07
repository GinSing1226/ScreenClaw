---
name: long_press
description: 触发长按功能（拖拽起点、显示菜单）
---

# long_press - 长按

## 使用前必读

### 使用目的和效果
在指定坐标执行长按操作。可触发拖拽起点、显示长按菜单（上下文菜单、选项菜单）、激活需要长按的特殊功能。

### 适用场景
- 需要开始拖拽操作
- 需要显示长按菜单
- 应用功能需要长按触发

### 不适用场景
- 普通点击即可触发的功能 → 使用 `click`

## 请求

**方法**：POST `/api/long_press`

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
| `duration_ms` | int | 否 | 500 | 长按时长（毫秒） |
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
  "x": 50.0,
  "y": 50.0,
  "duration_ms": 1000,
  "action_method": "background"
}
```

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `USER_DENIED` | 用户拒绝操作（hijack模式） | 用户取消了确认弹窗 |
| `OPERATION_FAILED` | 操作失败 | 1.换其他子窗口 2.大调坐标+网格参数重截图 3.Evaluator验证周边元素 4.仍失败才考虑hijack |

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但菜单没出来** → 查阅 SKILL.md「常见问题排查」
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **拖拽操作**：长按后配合swipe完成拖拽
- **菜单触发**：长按后截图验证菜单是否显示
- **时长调整**：某些应用可能需要更长或更短的长按时长

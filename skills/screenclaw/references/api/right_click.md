---
name: right_click
description: 打开上下文菜单、调用右键快捷方式
---

# right_click - 右键点击

## 使用前必读

### 使用目的和效果
在指定坐标执行右键点击。可打开上下文菜单（快捷菜单）、调用右键功能的快捷方式。

### 适用场景
- 需要打开上下文菜单
- 需要通过右键菜单访问某个功能
- 左键操作无法完成需求

### 不适用场景
- 左键操作即可完成 → 使用 `click`

## 请求

**方法**：POST `/api/right_click`

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
| `action_method` | string | 否 | "background" | 操作方式：background/hijack |

### 请求示例

```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "x": 50.0,
  "y": 50.0,
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
1. **API成功但菜单没出来** → 查阅 SKILL.md「常见问题排查」
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **右键菜单操作**：右键点击后截图查看菜单，然后点击菜单项
- **子窗口**：右键菜单可能在子窗口中，注意选择正确的window_id

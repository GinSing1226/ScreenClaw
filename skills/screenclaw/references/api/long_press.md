---
name: long_press
description: 触发长按才能激活的功能（如拖拽起点、显示菜单）
---

# long_press - 长按

## 使用目的
在指定坐标执行长按操作，用于：
- 触发拖拽操作的起点
- 显示长按菜单（上下文菜单、选项菜单）
- 某些需要长按激活的特殊功能

## 什么时候用
- 需要开始拖拽操作
- 需要显示长按菜单
- 应用功能需要长按触发

## 什么时候不用
- 普通点击即可触发的功能（使用click）

---

## 请求

**方法**：POST
**路径**：`/api/long_press`

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 | 从哪里获取 |
|------|------|------|--------|------|----------|
| `ai_app_type` | string | 是 | - | AI应用类型 | 判断当前AI是什么应用，就用什么值 |
| `session_id` | string | 是 | - | 会话唯一标识 | 获取当前会话唯一标识，获取不到则随机生成 |
| `window_id` | int | 是 | - | 目标窗口句柄 | 从get_window_list获取 |
| `main_window_id` | int | 否 | - | 主窗口ID（用于恢复窗口） | 从get_window_list获取 |
| `x` | float | 是 | - | 横坐标（0-100） | 从截图分析得出 |
| `y` | float | 是 | - | 纵坐标（0-100） | 从截图分析得出 |
| `duration_ms` | int | 否 | 500 | 长按时长（毫秒） | 根据需要调整 |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack | 优先background |

### 请求示例

```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "x": 50.0,
  "y": 50.0,
  "duration_ms": 1000,
  "action_method": "background"
}
```

---

## 响应

### 成功响应
```json
{
  "success": true,
  "message": "长按成功"
}
```

---

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `USER_DENIED` | 用户拒绝操作（hijack模式） | 用户取消了确认弹窗 |
| `OPERATION_FAILED` | 操作失败 | 检查坐标，尝试hijack模式 |

---

## 使用技巧

1. **拖拽操作**：长按后配合swipe完成拖拽
2. **菜单触发**：长按后截图验证菜单是否显示
3. **时长调整**：某些应用可能需要更长或更短的长按时长

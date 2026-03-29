---
name: right_click
description: 打开上下文菜单、调用特定功能的快捷方式
---

# right_click - 右键点击

## 使用目的
在指定坐标执行右键点击，用于：
- 打开上下文菜单（快捷菜单）
- 调用特定功能的快捷方式
- 访问右键菜单中的选项

## 什么时候用
- 需要打开上下文菜单
- 需要通过右键菜单访问某个功能
- 左键操作无法完成需求

## 什么时候不用
- 左键操作即可完成（使用click）

---

## 请求

**方法**：POST
**路径**：`/api/right_click`

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 | 从哪里获取 |
|------|------|------|--------|------|----------|
| `ai_app_type` | string | 是 | - | AI应用类型 | 判断当前AI是什么应用，就用什么值 |
| `session_id` | string | 是 | - | 会话唯一标识 | 获取当前会话唯一标识，获取不到则随机生成 |
| `window_id` | int | 是 | - | 目标窗口句柄 | 从get_window_list获取 |
| `main_window_id` | int | 否 | - | 主窗口ID（用于恢复窗口） | 从get_window_list获取 |
| `x` | float | 是 | - | 横坐标（从截图的网格标记中直接读出的数字） | 从截图分析得出 |
| `y` | float | 是 | - | 纵坐标（从截图的网格标记中直接读出的数字） | 从截图分析得出 |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack | 优先background |

### 请求示例

```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "x": 50.0,
  "y": 50.0,
  "action_method": "background"
}
```

---

## 响应

### 成功响应
```json
{
  "success": true,
  "message": "指令已发送，可截图验证结果"
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

1. **右键菜单操作**：右键点击后，截图查看菜单，然后点击菜单项
2. **快捷操作**：某些功能的快捷方式在右键菜单中
3. **子窗口**：右键菜单可能在子窗口中，注意选择正确的window_id

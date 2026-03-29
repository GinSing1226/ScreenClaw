---
name: click
description: 触发某个功能（如确认、取消）、进入某个页面（如详情页）、激活某个控件
---

# click - 点击

## 使用目的
在指定坐标执行左键点击，用于：
- 触发按钮功能（确认、取消、提交等）
- 进入某个页面（点击链接、卡片等）
- 激活某个控件（输入框、选项等）

## 什么时候用
- 需要触发按钮功能
- 需要进入某个页面或打开某个功能
- 需要激活某个控件

## 什么时候不用
- 需要输入文本（使用input_text）
- 需要长按触发（使用long_press）
- 需要滑动/滚动（使用swipe/scroll）

---

## 请求

**方法**：POST
**路径**：`/api/click`
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
| `action_method` | string | 否 | "background" | 操作方式：background=无感操作，hijack=劫持操作 | 优先background，无效时用hijack |

### 请求示例

#### 后台点击（推荐）
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

#### 劫持点击（background无效时使用）
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "x": 50.0,
  "y": 30.0,
  "action_method": "hijack"
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

### 失败响应
```json
{
  "success": false,
  "error_code": "WINDOW_NOT_FOUND",
  "message": "窗口不存在"
}
```

---

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `USER_DENIED` | 用户拒绝操作（hijack模式） | 用户取消了确认弹窗 |
| `OPERATION_FAILED` | 操作失败 | 检查坐标是否正确，尝试hijack模式 |

---

## 使用技巧

1. **优先使用background**：无感操作，不干扰用户
2. **background无效时**：改用hijack模式
3. **点击后验证**：截图确认点击是否生效
4. **点击后等待**：使用wait等待UI响应
5. **子窗口问题**：点击无效时，尝试使用子窗口的window_id

---

## 操作方式说明

### background（无感操作）
- 不抢夺鼠标键盘
- 用户可以继续使用电脑
- 兼容性稍差，某些应用可能不响应

### hijack（劫持操作）
- 会短暂激活目标窗口
- 需要用户确认（弹窗）
- 兼容性好，几乎所有应用都支持
- 执行时会请求用户暂停操作

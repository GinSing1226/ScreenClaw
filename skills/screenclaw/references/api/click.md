---
name: click
description: 触发某个功能（如确认、取消）、进入某个页面（如详情页）、激活某个控件
---

# click - 点击

## 使用目的
- 触发按钮功能（确认、取消、提交等）
- 进入某个页面（点击链接、卡片等）
- 激活某个控件（输入框、选项等）

## 什么时候用
- 需要触发按钮功能
- 需要进入某个页面或打开某个功能
- 需要激活某个控件

## 什么时候不用
- 需要输入文本（直接使用input_text）
- 需要长按触发（使用long_press）
- 需要滑动/滚动（使用swipe/scroll）

---

## 请求

**方法**：POST `/api/click`

**请求头**：
```
Authorization: Bearer {token}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `ai_app_type` | string | 是 | - | AI应用类型（如claude_code） |
| `session_id` | string | 是 | - | 会话唯一标识，整个会话保持一致 |
| `window_id` | int | 是 | - | 目标窗口句柄，从get_window_list获取 |
| `main_window_id` | int | 否 | - | 主窗口ID（用于恢复窗口） |
| `x` | float | 是 | - | 横坐标（从截图的网格标记中直接读出的数字，如50表示中间位置） |
| `y` | float | 是 | - | 纵坐标（从截图的网格标记中直接读出的数字，如30表示偏上位置） |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack |

### 操作方式

| 方式 | 特点 | 兼容性 |
|------|------|--------|
| `background` | 无感操作，不干扰用户 | 兼容性稍差 |
| `hijack` | 会短暂接管，需用户确认 | 兼容性好 |

**建议**：优先background，无效时用hijack

### 请求示例

**后台点击**（推荐）：
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

**劫持点击**（background无效时）：
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

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `USER_DENIED` | 用户拒绝操作（hijack模式） | 用户取消了确认弹窗 |
| `OPERATION_FAILED` | 操作失败 | 检查坐标，尝试hijack模式 |

---

## 使用技巧

1. **优先使用background**：无感操作，不干扰用户
2. **background无效时**：改用hijack模式
3. **点击后验证**：截图确认点击是否生效
4. **子窗口问题**：点击无效时，尝试使用子窗口的window_id
5. **输入文本**：输入文本请查阅`input_text.md`api文档，Input_text自带点击后输入。不建议分步点击+输入。

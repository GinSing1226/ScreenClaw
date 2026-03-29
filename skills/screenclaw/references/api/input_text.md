---
name: input_text
description: 向输入框输入文本内容、填表、搜索
---

# input_text - 输入文本

## 使用目的
向指定位置输入文本内容，用于：
- 在输入框中输入文本
- 填写表单
- 搜索内容

## 什么时候用
- 需要向输入框输入文本
- 需要填写表单字段
- 需要输入搜索关键词

## 什么时候不用
- 只需点击、无需输入（使用click）
- 需要按键操作（使用press_key）

## 重要说明

- `input_text` **支持两种操作模式**：`background` 和 `hijack`
- **推荐优先使用 `background`**：无感操作，不抢鼠标键盘
- 某些特殊输入框可能不支持 `background`，此时切换到 `hijack` 模式（会激活窗口并短暂占用鼠标键盘）

---

## 请求

**方法**：POST
**路径**：`/api/input_text`

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 | 从哪里获取 |
|------|------|------|--------|------|----------|
| `ai_app_type` | string | 是 | - | AI应用类型 | 判断当前AI是什么应用，就用什么值 |
| `session_id` | string | 是 | - | 会话唯一标识 | 获取当前会话唯一标识，获取不到则随机生成 |
| `window_id` | int | 是 | - | 目标窗口句柄 | 从get_window_list获取 |
| `main_window_id` | int | 否 | - | 主窗口ID（用于恢复窗口） | 从get_window_list获取 |
| `x` | float | 否 | - | 输入位置横坐标（0-100） | 从截图分析得出 |
| `y` | float | 否 | - | 输入位置纵坐标（0-100） | 从截图分析得出 |
| `text` | string | 是 | - | 输入文本，\n表示换行 | 用户提供的文本 |
| `newline_key` | string | 否 | "shift enter" | 换行键（仅background） | ctrl enter/enter |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack | 优先使用background |

### 参数说明

- `x`、`y`：可选，不传则直接输入（不点击），传则先点击该位置再输入
- `text`：输入文本内容，`\n` 表示换行
- `newline_key`：仅在 background 模式下有效，控制 `\n` 用什么键模拟换行

### 请求示例

#### 先点击再输入
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "x": 50.0,
  "y": 50.0,
  "text": "Hello World\n",
  "action_method": "background"
}
```

#### 直接输入（不点击）
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "text": "搜索内容",
  "action_method": "background"
}
```

#### 输入多行文本
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "x": 50.0,
  "y": 50.0,
  "text": "第一行\n第二行\n第三行",
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
| `USER_DENIED` | 用户拒绝操作 | 用户取消了确认弹窗 |

---

## 使用技巧

1. **子窗口**：输入框通常是子窗口，使用子窗口的window_id
2. **点击激活**：传x和y参数，先点击输入框激活焦点
3. **换行**：使用 `\n` 表示换行，background模式下可通过`newline_key`指定换行键
4. **模式选择**：优先尝试`background`，如无效再切`hijack`

---

## 无法粘贴的替代方案

某些输入框可能不支持粘贴（如某些安全输入框、特殊控件），此时可以使用**批处理+按键逐个字符键入**的方式：

### 示例：逐字符输入"hello"

```json
{
  "instructions": [
    { "action": "press_key", "params": { "key": "h", "action_method": "hijack" } },
    { "action": "wait", "params": { "duration_ms": 50 } },
    { "action": "press_key", "params": { "key": "e", "action_method": "hijack" } },
    { "action": "wait", "params": { "duration_ms": 50 } },
    { "action": "press_key", "params": { "key": "l", "action_method": "hijack" } },
    { "action": "wait", "params": { "duration_ms": 50 } },
    { "action": "press_key", "params": { "key": "l", "action_method": "hijack" } },
    { "action": "wait", "params": { "duration_ms": 50 } },
    { "action": "press_key", "params": { "key": "o", "action_method": "hijack" } }
  ]
}
```

**注意**：
- 每个字符之间添加短暂wait（如50ms），避免按键过快丢失
- 大写字母需要配合shift键：先按shift，再按字母，再释放shift
- 特殊字符使用对应的键名（如space、enter等）

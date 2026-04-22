---
name: input_text
description: 向输入框输入文本。传x/y时会先点击坐标位置，再输入文本，无需分步操作。适用：向输入框输入文本、填写表单、输入搜索内容。不适用：只需点击无需输入（用click）、需要按键操作（用press_key）。
---

# input_text - 输入文本

## 请求

**方法**：POST `/api/input_text`

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
| `window_id` | int | 是 | - | 目标窗口句柄，可以是主窗口，也可是子窗口 |
| `main_window_id` | int | 是 | - | 主窗口ID |
| `x` | float | 否 | - | 输入位置横坐标，传则先点击激活再输入。不传就直接输入 |
| `y` | float | 否 | - | 输入位置纵坐标，传则先点击激活再输入。不传就直接输入 |
| `text` | string | 是 | - | 输入文本，\n表示换行 |
| `newline_key` | string | 否 | "shift enter" | 换行键（仅background）：ctrl enter/enter |
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
  "text": "Hello World",
  "action_method": "background"
}
```

```json
// 换行（\n是两个普通字符，服务端自动解析）
{...,"text": "第一行\n第二行"}

// Emoji（直接传）
{...,"text": "hello😊"}
```

**Batch中的使用**：

```json
{"action": "input_text", "params": {"x": 50, "y": 50, "text": "第一行\n第二行😊", "action_method": "hijack"}}
```

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但输入没显示** → 按照 skill.md 步骤10 验证，换坐标（子窗口）、换操作模式重试
2. **API调用失败** → 对照请求参数检查参数格式
3. **换行不成功** → background使用静默输入，不是物理按键的粘贴，所以无法输入换行。换行需要用hijack，hijack的输入方式是粘贴

### 操作技巧
- **激活后输入**：如果传了x和y参数，screenclaw会先点击坐标位置，再输入。
- **换行**：使用 `\n`（两个普通字符 `\` 和 `n`）表示换行
- **Emoji**：直接传 emoji 字符

### 无法粘贴的替代方案

某些输入框不支持粘贴（如安全输入框），可用 batch + press_key 逐个字符键入：

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

字符间添加短暂wait（50ms）避免丢失。中文输入模拟输入法输入，必须进入托管模式，输入法面板才不会被恢复，才能被持续键入。

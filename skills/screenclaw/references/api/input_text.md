---
name: input_text
description: 向输入框输入文本、填表、搜索
---

# input_text - 输入文本

## 使用前必读

### 使用目的和效果
在输入框中输入文本。传x、y参数时，API会先点击该位置激活输入框再输入，无需分步操作。

### 适用场景
- 需要向输入框输入文本
- 需要填写表单
- 需要输入搜索内容

### 不适用场景
- 只需点击无需输入 → 使用 `click`
- 需要按键操作 → 使用 `press_key`

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
| `window_id` | int | 是 | - | 目标窗口句柄 |
| `main_window_id` | int | 是 | - | 主窗口ID |
| `x` | float | 否 | - | 输入位置横坐标，传则先点击激活再输入 |
| `y` | float | 否 | - | 输入位置纵坐标，传则先点击激活再输入 |
| `text` | string | 是 | - | 输入文本，\n表示换行 |
| `newline_key` | string | 否 | "shift enter" | 换行键（仅background）：ctrl enter/enter |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack |

**重要**：建议传x、y参数，先点击激活输入框再输入。输入框通常在子窗口中，优先使用子窗口ID。

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

// 换行+Emoji+中文
{...,"text": "你好\n世界🎉"}
```

**Batch中的换行和Emoji**：

```json
{"action": "input_text", "params": {"x": 50, "y": 50, "text": "第一行\n第二行😊"}}
```

**Batch中指定操作模式**（在参数中加 `action_method=hijack`）：

```json
{"action": "input_text", "params": {"x": 50, "y": 50, "text": "hello", "action_method": "hijack"}}
```

**PowerShell简化格式**（api_call_batch.ps1 专用）：

```powershell
# 基本输入
-Instructions "input_text(x=50,y=35,text=hello)"

# 中文 + 换行 + Emoji
-Instructions "input_text(x=50,y=35,text=第一行\n第二行😊)"

# hijack模式
-Instructions "input_text(x=50,y=35,text=hello,action_method=hijack)"

# 完整调用示例
.\scripts\api_call_batch.ps1 -ApiUrl "http://localhost:12261" -Token "abc123" -AiAppType "claude_code" -SessionId "sess_001" -WindowId 123456 -MainWindowId 123456 -Instructions "input_text(x=50,y=35,text=你好\n世界😊,action_method=hijack);click(x=97,y=96)"
```

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `USER_DENIED` | 用户拒绝操作 | 用户取消了确认弹窗 |

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但输入没显示** → 查阅 SKILL.md「常见问题排查」
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **子窗口**：输入框通常是子窗口，使用子窗口的window_id
- **点击激活**：传x和y参数，先点击输入框激活焦点
- **换行**：使用 `\n` 表示换行
- **模式选择**：优先background，无效再切hijack

### 中文编码

直接传中文即可，脚本和服务端会自动处理编码。

### 换行与Emoji

- **换行**：`text` 参数中用 `\n`（两个普通字符 `\` 和 `n`）表示换行。示例：`text=hello\nworld`
- **Emoji**：直接传 emoji 字符。示例：`text=hello😊`
- **background 模式**下换行和 emoji 均支持，少数软件不支持时切换到 hijack 即可

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

---
name: input_text
description: 向输入框输入文本内容、填表、搜索
---

# input_text - 输入文本

## 使用目的
- 在输入框中输入文本
- 填写表单字段
- 输入搜索关键词

## 什么时候用
- 需要向输入框输入文本
- 需要填写表单
- 需要输入搜索内容

## 什么时候不用
- 只需点击、无需输入（使用click）
- 需要按键操作（使用press_key）

---

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
| `ai_app_type` | string | 是 | - | AI应用类型（如claude_code） |
| `session_id` | string | 是 | - | 会话唯一标识，整个会话保持一致 |
| `window_id` | int | 是 | - | 目标窗口句柄，从get_window_list获取 |
| `x` | float | 否 | - | 输入位置横坐标（从截图的网格标记中直接读出的数字），推荐填写，无感操作时可实现先点击再输入 |
| `y` | float | 否 | - | 输入位置纵坐标（从截图的网格标记中直接读出的数字），推荐填写，无感操作时可实现先点击再输入 |
| `text` | string | 是 | - | 输入文本，\n表示换行 |
| `newline_key` | string | 否 | "shift enter" | 换行键（仅background）：ctrl enter/enter |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack |

**操作方式**：优先background，无效时用hijack

**参数说明**：
- `x`、`y`：可选，**传则先点击该位置激活输入框，再输入**；不传则直接输入
- `text`：`\n` 表示换行
- `newline_key`：仅在background模式有效，控制 `\n` 的换行键

**重要**：输入前通常需要先点击激活输入框，**建议传 x、y 参数**

### 请求示例

**基础示例**（英文）：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "x": 50.0,
  "y": 50.0,
  "text": "Hello World",
  "action_method": "background"
}
```

**中文内容**（注意：命令行传递中文需要特殊处理，详见下方"中文编码问题"）：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "x": 50.0,
  "y": 50.0,
  "text": "你好，这是中文内容",
  "action_method": "background"
}
```

---

## 中文编码问题

**问题**：命令行传递中文时可能报错 `There was an error parsing the body`

**解决方案**：使用Unicode编码

### Unicode编码方案（推荐，所有环境通用）

**原理**：将中文转换为Unicode编码（如`\u4f60\u597d`），服务端自动解码

**示例**：
```json
// 原始中文
"text": "你好，这是中文内容"

// Unicode编码（AI生成时使用）
"text": "\u4f60\u597d\uff0c\u8fd9\u662f\u4e2d\u6587\u5185\u5bb9"
```

**完整请求示例**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "my_session",
  "window_id": 1001,
  "text": "\u4f60\u597d\uff0c\u8fd9\u662f\u4e2d\u6587\u5185\u5bb9",
  "action_method": "background"
}
```

**转换方式**：
- Python: `"你好".encode('unicode_escape').decode('utf-8')` → `\\u4f60\\u597d`
- JavaScript: `JSON.stringify("你好")` → `"\u4f60\u597d"`
- AI自动处理：大多数AI会自动将中文转换为Unicode编码

### PowerShell 环境（直接传递中文也可）

```powershell
# PowerShell支持直接传递中文
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，这是中文内容"}' \
  "http://localhost:12261/api/input_text"
```

### cmd / bash 环境（使用Unicode或batch）

**方案1：Unicode编码**（推荐）
```bash
# 使用Unicode编码，无编码问题
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"\u4f60\u597d\uff0c\u8fd9\u662f\u4e2d\u6587\u5185\u5bb9"}' \
  "http://localhost:12261/api/input_text"
```

**方案2：使用 batch 接口**
```bash
# batch 在服务端处理
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instructions":[{"action":"input_text","params":{"text":"\u4f60\u597d"}}]}' \
  "http://localhost:12261/api/batch"
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
3. **换行**：使用 `\n` 表示换行
4. **模式选择**：优先尝试`background`，如无效再切`hijack`

---

## 无法粘贴的替代方案

某些输入框不支持粘贴（如安全输入框），可用**批处理+按键逐个字符键入**：

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
- 字符间添加短暂wait（如50ms），避免按键过快丢失
- 大写字母需配合shift键

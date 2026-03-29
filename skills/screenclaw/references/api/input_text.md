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
| `x` | float | 否 | - | 输入位置横坐标（0-100），可选 |
| `y` | float | 否 | - | 输入位置纵坐标（0-100），可选 |
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

**解决方案（按环境选择）**：

| 环境 | 中文支持 | 解决方案 |
|------|---------|----------|
| **PowerShell** | ✅ 支持 | 直接传递中文即可 |
| **cmd / bash** | ❌ 有问题 | 使用 batch 接口或文件方式 |

### PowerShell 环境（推荐，支持中文）

```powershell
# 直接传递中文，PowerShell 会正确处理 UTF-8
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ai_app_type":"claude_code","session_id":"session-123","window_id":1001,"text":"你好，这是中文内容"}' \
  "http://localhost:12261/api/input_text"
```

### cmd / bash 环境（中文问题）

**方案1：使用 batch 接口**（推荐）
```bash
# batch 在服务端处理，避免客户端编码问题
curl -X POST \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ai_app_type":"claude_code","session_id":"session-123","window_id":1001,"instructions":[{"action":"click","params":{"x":50,"y":50}},{"action":"input_text","params":{"text":"中文内容"}}]}' \
  "http://localhost:12261/api/batch"
```

**方案2：使用文件**
```bash
# 先保存JSON到文件，再发送
cat > request.json << EOF
{"text":"你好，这是中文内容"}
EOF
curl -d @request.json ...
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

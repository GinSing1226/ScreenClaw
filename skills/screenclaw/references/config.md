---
name: screenclaw-config
description: ScreenClaw连接配置说明
---

# ScreenClaw 连接配置

1. 请求地址

```
http://{host}:{port}
```

2. 请求Token
```
{token}
```
- 默认请求地址：`http://localhost:12261`
- 由用户提供，提供后，你可以保存到此。地址和鉴权信息在screenclaw监控面板上。
- **如果获取不到请求地址、token，直接向用户索取，不要猜测或使用默认值，不要直接调用脚本**

## AI应用类型 (ai_app_type)

**你必须根据当前调用的 AI 应用类型填写正确的值**

### 常见AI应用对应的值

| AI 应用 | ai_app_type 值 |
|---------|---------------|
| Claude Code | `claude_code` |
| openclaw | `openclaw` |
| ChatGPT | `chatgpt` |
| 其他应用 | 应用名称（小写下划线） |

### 如何确定你的值
如果你不确定当前是什么AI应用，检查以下标识：
- 产品名称（Claude Code、openclaw等）
- 运行环境（浏览器、IDE、命令行）
- 使用小写字母和下划线命名

### 示例
```python
# 如果是 Claude Code 在调用
api_call(ai_app_type="claude_code", ...)

# 如果是 ChatGPT 在调用
api_call(ai_app_type="chatgpt", ...)

```

### 命名规则
- 小写字母
- 使用下划线分隔单词
- 简洁明了，能识别应用类型

## 会话ID (session_id) - 强制要求

**你必须在整个会话过程中使用同一个 session_id**

### 如何生成 session_id

格式：`{应用名}_{日期}_{时间戳}`

**重要**：
- 必须使用英文、数字和下划线
- 不要使用中文、连字符（-）或其他特殊符号

示例：
```
claude_code_20260329_143025
kimi_code_20260329_143025
chatgpt_20260329_143025
```

### 为什么必须使用英文

使用中文session_id（如"【第一次尝试】"）会导致：
- PowerShell脚本处理路径时出错
- 目录名编码问题
- 图片保存失败

### 使用规则

1. **会话开始时**：生成一个唯一的 session_id（仅英文数字）
2. **整个会话期间**：所有 API 调用都使用这个 session_id
3. **绝对不要**：每次调用生成新的 session_id

### 正确示例
```
# 会话开始
session_id = "claude_code_20260329_143025"

# 第一次API调用
api_call(session_id=session_id, ...)

# 第N次API调用（使用相同的session_id）
api_call(session_id=session_id, ...)
```

---
name: screenclaw-config
description: ScreenClaw连接配置说明，以及接口重要的公共参数说明：ai_app_type/session_id
---

# ScreenClaw 连接配置

1. 请求地址：
```
http://{host}:{port}
```

2. 请求Token：
```
{token}
```

- 默认请求地址：`http://localhost:12261`。默认token：`8aae49690621b5e57849b3ba8a45085f`
- 由用户提供，提供后，你可以保存到此。地址和鉴权信息在screenclaw监控面板上。
- **如果获取不到请求地址、token，直接向用户索取，不要猜测或使用默认值，不要直接调用脚本**

## AI应用类型 (ai_app_type)
应用类型用于图片/日志保存路径。以便用户追溯。**你必须根据当前调用的 AI 应用类型填写正确的值**

### 如何确定你的值
如果你不确定当前是什么AI应用，检查以下标识：
- 产品名称（Claude Code、openclaw等）
- 运行环境（浏览器、IDE、命令行）
- 命名规则：使用小写字母和下划线命名

### 示例
| AI 应用 | ai_app_type 值 |
|---------|---------------|
| Claude Code | `claude_code` |
| openclaw | `openclaw` |
| codex | `codex` |
| 其他应用 | 应用名称（小写下划线） |

## ScreenClaw 安装目录 (screenclaw_install_dir)

ScreenClaw 软件的解压运行位置。首次下载安装后记录到此文件，后续会话复用。

- 如果未记录或目录下没有 `screenclaw.exe`，需要重新下载安装（见 SKILL.md 初始化步骤）。
- 用户可指定安装目录；未指定时询问用户。

**安装目录**：（下载解压后填写，例如 `C:\Users\admin\ScreenClaw`）

## 会话ID (session_id) 

会话id用于图片/日志保存路径、文件命名，以便用户追溯。**你必须在整个会话过程中使用同一个 session_id**

同一个 `ai_app_type + session_id` 的图片会保存到首次创建的 session 目录。即使日期变化，也不要生成新 `session_id`；服务端和脚本会继续复用最早的 `data/{ai_app_type}__{session_id}__{first-created-date}/` 目录。

### 生成规则

1. 格式：`{应用名}_{日期}_{时间}`

2. 格式规则
- 只能使用英文、数字和下划线。否则路径可能乱码。
- 应用名： `ai_app_type`
- 日期：yyyymmdd格式。
- 时间：hhmmss格式。
- 从上下文里获取日期、时间。若无，可使用 `health.md` 的接口返回的具体时间

示例：claude_code_20260329_143025

### 使用规则

1. **会话开始时**：生成一个唯一的 session_id（仅英文数字）
2. **整个会话期间**：所有 API 调用都使用这个 session_id
3. **跨日期继续使用**：4月26日开始的会话，4月27日、28日仍使用同一个 session_id
4. **绝对不要**：每次调用接口或日期变化时生成新的 session_id
5. **用户优先**：用户明确提出开始全新任务，你才可生成新会话id

### 正确示例
```
# 会话开始
session_id = "claude_code_20260329_143025"

# 第一次API调用
screenclaw(endpoint, session_id=session_id, ...)

# 第N次API调用（使用相同的session_id）
screenclaw(endpoint, session_id=session_id, ...)
```

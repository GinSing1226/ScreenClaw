# ScreenClaw 脚本使用说明

> **前置条件**：先确认 ScreenClaw 服务已启动，并已获取 API 地址和 Token

---

## 通用API调用脚本（推荐）⭐

**优先使用** `api_call.py` / `api_call.ps1` / `api_call.sh`

AI无需手动组装curl命令，只需传递参数即可。脚本会自动：
- ✅ 处理中文编码（自动转Unicode）
- ✅ 组装HTTP请求
- ✅ 返回解析后的结果
### 降级路径

`api_call.py` → `api_call.ps1` → `api_call.sh` → 手动curl（见 `references/api/call_templates.md`）

### 用法

```bash
# Python版本（推荐）
python scripts/api_call.py <api_url> <token> <endpoint> [ai_app_type] [参数...]

# PowerShell版本
powershell -ExecutionPolicy Bypass -File scripts/api_call.ps1 <api_url> <token> <endpoint> [ai_app_type] [参数...]

# Shell版本
bash scripts/api_call.sh <api_url> <token> <endpoint> [ai_app_type] [参数...]
```

### 示例

```bash
# 获取窗口列表（中文关键词，脚本自动转Unicode）
python scripts/api_call.py http://192.168.10.190:12261 TOKEN get_window_list claude_code keyword=飞书

# 点击
python scripts/api_call.py http://192.168.10.190:12261 TOKEN click claude_code window_id=123456 x=50 y=35

# 输入文本
python scripts/api_call.py http://192.168.10.190:12261 TOKEN input_text claude_code window_id=123456 text=你好世界
```

> **注意**：截图API请使用 `fetch_screenshot_cli.py` 专用脚本

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| api_url | ScreenClaw服务地址 | `http://192.168.10.190:12261` |
| token | 认证令牌 | `your_token_here` |
| endpoint | API端点名称 | `get_window_list`, `click` 等 |
| ai_app_type | AI应用类型（可选，默认claude_code） | `claude_code`, `kimi_code` 等 |
| session_id | 会话ID（可选，默认自动生成） | `my_session_20260329` |
| 参数... | API参数（key=value格式） | `keyword=飞书`, `x=50`, `y=35` |

> **session_id**：如果不提供，会自动生成格式为 `screenclaw_YYYYMMDD_HHmmss` 的ID



---

## 截图专用脚本

`fetch_screenshot_cli.py` / `fetch_screenshot_cli.ps1` / `fetch_screenshot_cli.sh` 专门用于截图API。

**用法**：
```bash
# Python版本
python scripts/fetch_screenshot_cli.py <api_url> <token> <window_id> [session_id] [ai_app_type]

# PowerShell版本
powershell -ExecutionPolicy Bypass -File scripts/fetch_screenshot_cli.ps1 <api_url> <token> <window_id> [session_id] [ai_app_type]

# Shell版本
bash scripts/fetch_screenshot_cli.sh <api_url> <token> <window_id> [session_id] [ai_app_type]
```

**参数说明**：
- `session_id`：默认为 `default`
- `ai_app_type`：默认为 `claude_code`

**功能**：
- 自动调用API获取截图
- 本地场景：直接返回 `image_path`
- 远程场景：自动保存到本地并返回路径
- 自动处理中文目录名问题

---

## 环境选择

根据当前 shell 环境选择对应脚本：

| Shell 环境 | 推荐脚本 |
|-----------|---------|
| Python环境 | `.py` 脚本 |
| PowerShell | `.ps1` 脚本 |
| bash / zsh | `.py` 或 `.sh` 脚本 |

---

## 使用建议

1. **优先使用api_call脚本**：无需组装curl，直接传参数
2. **传递中文即可**：脚本会自动转换为Unicode编码
3. **session_id保持一致**：整个会话使用同一个session_id
4. **降级路径**：api_call失败时尝试其他版本或手动curl

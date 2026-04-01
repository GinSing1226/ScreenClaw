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
python scripts/api_call.py <api_url> <token> <endpoint> ai_app_type=<值> session_id=<值> main_window_id=<值> [其他参数...]

# PowerShell版本
powershell -ExecutionPolicy Bypass -File scripts/api_call.ps1 <api_url> <token> <endpoint> ai_app_type=<值> session_id=<值> main_window_id=<值> [其他参数...]

# Shell版本
bash scripts/api_call.sh <api_url> <token> <endpoint> ai_app_type=<值> session_id=<值> main_window_id=<值> [其他参数...]
```

### 示例

```bash
# 获取窗口列表（中文关键词，脚本自动转Unicode）
python scripts/api_call.py http://192.168.10.190:12261 TOKEN get_window_list ai_app_type=claude_code session_id=wechat_20260330_143025 keyword=飞书

# 点击
python scripts/api_call.py http://192.168.10.190:12261 TOKEN click ai_app_type=claude_code session_id=wechat_20260330_143025 main_window_id=123456 window_id=123456 x=50 y=35

# 输入文本
python scripts/api_call.py http://192.168.10.190:12261 TOKEN input_text ai_app_type=claude_code session_id=wechat_20260330_143025 main_window_id=123456 window_id=123456 text=你好世界
```

> **注意**：截图API请使用 `fetch_screenshot_cli.py` 专用脚本

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| api_url | ScreenClaw服务地址 | `http://192.168.10.190:12261` |
| token | 认证令牌 | `your_token_here` |
| endpoint | API端点名称 | `get_window_list`, `click` 等 |
| ai_app_type | **AI应用类型（必需）** | `claude_code`, `kimi_code` 等 |
| session_id | **会话ID（必需）** | `wechat_20260330_143025` |
| main_window_id | **主窗口ID（必需）** | `123456`，从get_window_list获取 |
| 参数... | API参数（key=value格式） | `keyword=飞书`, `x=50`, `y=35` |

> ⚠️ **重要**：`ai_app_type`、`session_id`、`main_window_id` 是**必需参数**，必须由客户端显式传入，脚本不会自动生成。整个会话期间必须使用同一个session_id。



---

## 截图专用脚本

`fetch_screenshot_cli.py` / `fetch_screenshot_cli.ps1` / `fetch_screenshot_cli.sh` 专门用于截图API。

**用法**：
```bash
# Python版本
python scripts/fetch_screenshot_cli.py <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [网格和数字参数...]

# PowerShell版本
powershell -ExecutionPolicy Bypass -File scripts/fetch_screenshot_cli.ps1 <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [网格和数字参数...]

# Shell版本
bash scripts/fetch_screenshot_cli.sh <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [网格和数字参数...]
```

**基础参数**：
- `api_url`：ScreenClaw服务地址
- `token`：认证令牌
- `window_id`：窗口ID
- `session_id`：**必需参数**，会话标识符
- `ai_app_type`：**必需参数**，AI应用类型
- `main_window_id`：**必需参数**，主窗口ID，从get_window_list获取

**网格参数（可选）**：
| 参数 | 说明 | 默认值 |
|------|------|--------|
| grid_density | 每格宽度（像素），值越小网格越密 | 5.0 |
| grid_opacity | 网格透明度(0-100) | 50 |
| grid_color | 网格颜色 | #00FF00 |

**数字参数（可选）**：
| 参数 | 说明 | 默认值 |
|------|------|--------|
| number_density | 数字密度 | 2 |
| number_decimal | 小数位数(0-4) | 0 |
| number_size | 字体大小(4-32) | 8 |
| number_color | 数字颜色 | #00FF00 |
| number_opacity | 数字透明度(0-100) | 100 |

**示例**：
```bash
# 基础用法（使用默认网格和数字参数）
python scripts/fetch_screenshot_cli.py http://192.168.10.190:12261 TOKEN 1380176 my_session claude_code 1380176

# 自定义网格密度和数字大小
python scripts/fetch_screenshot_cli.py http://192.168.10.190:12261 TOKEN 1380176 my_session claude_code 1380176 grid_density=8 number_size=14

# 完整自定义
python scripts/fetch_screenshot_cli.py http://192.168.10.190:12261 TOKEN 1380176 my_session claude_code 1380176 grid_density=8 grid_opacity=30 grid_color="#00FF00" number_size=14 number_color="#FF0000"
```

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
3. **ai_app_type、session_id、main_window_id 必须显式传入**：每次API调用都必须包含这三个参数
4. **session_id保持一致**：整个会话使用同一个session_id
5. **降级路径**：api_call失败时尝试其他版本或手动curl

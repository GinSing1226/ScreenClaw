# ScreenClaw 脚本使用说明

> **前置条件**：先确认 ScreenClaw 服务已启动，并已获取 API 地址和 Token

---

## 脚本选择指南

根据**操作类型**和**当前环境**选择脚本：

| 操作类型 | Python环境 | PowerShell终端 | bash终端 |
|---------|-----------|---------------|---------|
| 截图 | `fetch_screenshot_cli.py` | `fetch_screenshot_cli.ps1` | `fetch_screenshot_cli.sh` |
| 裁剪放大 | `crop_zoom_screenshot_cli.py` | `crop_zoom_screenshot_cli.ps1` | `crop_zoom_screenshot_cli.sh` |
| 滚动长截图 | `scroll_screenshot_cli.py` | `scroll_screenshot_cli.ps1` | `scroll_screenshot_cli.sh` |
| batch | `api_call.py` | `api_call_batch.ps1` | `api_call.py` |
| 其他所有API | `api_call.py` | `api_call.ps1` | `api_call.sh` |

> **关键规则**：
> - **batch 端点**：Python/bash 环境用 `api_call.py`（传 JSON instructions）；**仅 PowerShell 终端**才需要 `api_call_batch.ps1`（简化指令格式，避免 PS 吞双引号）
> - **截图**：必须用专用脚本 `fetch_screenshot_cli`，不能用 `api_call`
> - **裁剪放大**：必须用专用脚本 `crop_zoom_screenshot_cli`，不能用 `api_call`（需处理远程base64）
> - **滚动长截图**：必须用专用脚本 `scroll_screenshot_cli`，不能用 `api_call`
> - Python 环境优先，有 Python 就用 `.py` 脚本

---

## 通用API调用脚本

`api_call.py` / `api_call.ps1` / `api_call.sh` 覆盖除截图外的所有端点。

### 必填参数

| 参数 | 说明 | 示例 |
|------|------|------|
| ai_app_type | AI应用类型（必需） | `claude_code`, `kimi_code` 等 |
| session_id | 会话ID（必需） | `wechat_20260404_143025` |
| main_window_id | 主窗口ID（必需，health/get_window_list/wait/delegated 免传） | `123456` |

> ⚠️ 这三个参数必须由客户端显式传入，脚本不会自动生成。整个会话期间使用同一个 session_id。

### 用法

```bash
# Python版本（推荐）
python scripts/api_call.py <api_url> <token> <endpoint> ai_app_type=<值> session_id=<值> main_window_id=<值> [其他参数...]

# PowerShell版本（不支持batch端点）
powershell -ExecutionPolicy Bypass -File scripts/api_call.ps1 <api_url> <token> <endpoint> ai_app_type=<值> session_id=<值> main_window_id=<值> [其他参数...]

# Shell版本
bash scripts/api_call.sh <api_url> <token> <endpoint> ai_app_type=<值> session_id=<值> main_window_id=<值> [其他参数...]

# health/get_window_list/wait/delegated 不需要 main_window_id
```

### 示例

```bash
# 健康检查（不需要main_window_id）
python scripts/api_call.py http://localhost:12261 TOKEN health ai_app_type=claude_code session_id=sess_001

# 获取窗口列表（中文关键词，不需要main_window_id）
python scripts/api_call.py http://localhost:12261 TOKEN get_window_list ai_app_type=claude_code session_id=sess_001 keyword=飞书 include_children=true

# 点击
python scripts/api_call.py http://localhost:12261 TOKEN click ai_app_type=claude_code session_id=sess_001 window_id=123456 main_window_id=123456 x=50 y=35 action_method=background

# 拖拽（文件拖放、窗口拖动）
python scripts/api_call.py http://localhost:12261 TOKEN drag ai_app_type=claude_code session_id=sess_001 window_id=123456 main_window_id=123456 start_x=30 start_y=50 end_x=70 end_y=50 duration_ms=500 action_method=background

# 鼠标移动（游戏视角控制，仅支持hijack/delegated）
python scripts/api_call.py http://localhost:12261 TOKEN mouse_move ai_app_type=claude_code session_id=sess_001 window_id=123456 delta_x=200 delta_y=0 duration_ms=300 action_method=hijack

# 输入文本（建议带坐标，支持中文、\n换行、Emoji）
python scripts/api_call.py http://localhost:12261 TOKEN input_text ai_app_type=claude_code session_id=sess_001 window_id=123456 main_window_id=123456 x=50 y=35 "text=hello\n你好😊"

# 托管模式（不需要main_window_id）
python scripts/api_call.py http://localhost:12261 TOKEN delegated ai_app_type=claude_code session_id=sess_001 action=enter
```

> **注意**：截图API请使用 `fetch_screenshot_cli.py` 专用脚本

### 降级路径

`api_call.py` → `api_call.ps1` → `api_call.sh` → 手动curl（见各API文档的降级说明）

---

## Batch 调用指南

batch 端点的脚本选择**取决于当前终端环境**：

### Python / bash 终端 → 用 api_call.py

直接传 JSON 格式的 instructions，不存在双引号问题：

```bash
python scripts/api_call.py http://localhost:12261 TOKEN batch ai_app_type=claude_code session_id=sess_001 window_id=123456 main_window_id=123456 instructions='[{"action":"click","params":{"x":50,"y":35}},{"action":"input_text","params":{"x":50,"y":35,"text":"hello"}}]'
```

### PowerShell 终端 → 用 api_call_batch.ps1

PowerShell 终端会吞掉双引号，导致 JSON 损坏。必须用简化指令格式：

**格式**：`action(key=value,key=value);action(key=value,key=value)`

**支持的 action**：

| action | 说明 | 参数示例 |
|--------|------|----------|
| click | 点击 | `click(x=85,y=95)` |
| long_press | 长按 | `long_press(x=50,y=35,duration_ms=1000)` |
| swipe | 滑动 | `swipe(start_x=50,start_y=80,end_x=50,end_y=20)` |
| drag | 拖拽 | `drag(start_x=30,start_y=50,end_x=70,end_y=50,duration_ms=500)` |
| scroll | 滚动 | `scroll(x=50,y=50,delta=3)` |
| right_click | 右键点击 | `right_click(x=50,y=35)` |
| hover | 鼠标悬浮 | `hover(x=50,y=35)` |
| mouse_move | 鼠标移动 | `mouse_move(delta_x=200,delta_y=0,duration_ms=300)` |
| input_text | 输入文本 | `input_text(x=50,y=35,text=hello)` |
| press_key | 按键 | `press_key(key=ctrl c)` |
| wait | 等待 | `wait(duration_ms=1000)` |
| screenshot | 截图 | `screenshot(coordinate_type=grid)` |
| crop_zoom_screenshot | 裁剪放大 | `crop_zoom_screenshot(source_image_path=...,center_x=55,center_y=65,crop_width=20,crop_height=20)` |

**用法**：

```powershell
# 基本用法
.\scripts\api_call_batch.ps1 -ApiUrl "http://localhost:12261" -Token "abc123" -AiAppType "claude_code" -SessionId "sess_20260405_001" -WindowId 123456 -MainWindowId 123456 -Instructions "click(x=85,y=95);wait(duration_ms=500);input_text(x=50,y=35,text=hello)"

# 中文 + \n换行 + Emoji（直接传，脚本自动用UTF-8编码发送）
-Instructions "input_text(x=50,y=35,text=你好\n世界😊)"

# 指定 hijack 模式（在指令参数中加 action_method=hijack）
-Instructions "input_text(x=50,y=35,text=hello,action_method=hijack);click(x=97,y=96)"

# 完整多步流程示例
.\scripts\api_call_batch.ps1 -ApiUrl "http://localhost:12261" -Token "abc123" -AiAppType "kimi_code" -SessionId "kimi_20260405_001" -WindowId 654321 -MainWindowId 654321 -Instructions "click(x=30,y=90);wait(duration_ms=1000);input_text(x=50,y=50,text=第一行\n第二行😊,action_method=hijack);press_key(key=enter)"
```

**参数说明**：

| 参数 | 必填 | 类型 | 说明 |
|------|------|------|------|
| -ApiUrl | 是 | string | ScreenClaw服务地址 |
| -Token | 是 | string | 认证令牌 |
| -AiAppType | 是 | string | AI应用类型（如 claude_code, kimi_code） |
| -SessionId | 是 | string | 会话ID，整个会话保持不变 |
| -WindowId | 是 | int | 目标窗口ID（优先用子窗口） |
| -MainWindowId | 是 | int | 主窗口ID |
| -Instructions | 是 | string | 简化格式的指令序列，分号分隔 |

> **编码说明**：脚本使用 UTF-8 字节数组发送请求，兼容 PS 5.x 和 7.x。中文、Emoji、`\n` 换行均直接传入即可，服务端自动解析。

### Batch 降级路径

- Python/bash：`api_call.py`（batch端点）→ 手动curl
- PowerShell：`api_call_batch.ps1` → `api_call.py`（batch端点）→ 手动curl

---

## 截图专用脚本

`fetch_screenshot_cli.py` / `fetch_screenshot_cli.ps1` / `fetch_screenshot_cli.sh`

**用法**：
```bash
# Python版本
python scripts/fetch_screenshot_cli.py <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [可选参数...]

# 示例：基础截图
python scripts/fetch_screenshot_cli.py http://localhost:12261 TOKEN 1380176 sess_001 claude_code 1380176

# 示例：调整网格密度（x/y分离）+ 标记点预览
python scripts/fetch_screenshot_cli.py http://localhost:12261 TOKEN 1380176 sess_001 claude_code 1380176 grid_density_x=3.3 grid_density_y=5 marker_x=55 marker_y=65
```

**详细参数**：查看 `references/api/screenshot.md`

---

## 裁剪放大专用脚本

`crop_zoom_screenshot_cli.py` / `crop_zoom_screenshot_cli.ps1` / `crop_zoom_screenshot_cli.sh`

**用法**：
```bash
# Python版本
python scripts/crop_zoom_screenshot_cli.py <api_url> <token> <source_image_path> <session_id> <ai_app_type> center_x=<值> center_y=<值> crop_width=<值> crop_height=<值> [zoom_scale=<值>]

# 示例：裁剪放大截图局部
python scripts/crop_zoom_screenshot_cli.py http://localhost:12261 TOKEN "D:/screenClaw/data/.../screenshot_143215.png" sess_001 claude_code center_x=55 center_y=65 crop_width=20 crop_height=20

# 示例：大幅放大看细节
python scripts/crop_zoom_screenshot_cli.py http://localhost:12261 TOKEN "D:/screenClaw/data/.../screenshot_143215.png" sess_001 claude_code center_x=55 center_y=65 crop_width=10 crop_height=10 zoom_scale=4.0
```

**详细参数**：查看 `references/api/crop_zoom_screenshot.md`

**注意**：不需要window_id，仅对已有图片文件进行裁剪放大处理

---

## 滚动长截图专用脚本

`scroll_screenshot_cli.py` / `scroll_screenshot_cli.ps1` / `scroll_screenshot_cli.sh`

**用法**：
```bash
# Python版本
python scripts/scroll_screenshot_cli.py <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [可选参数...]

# 示例
python scripts/scroll_screenshot_cli.py http://localhost:12261 TOKEN 1380176 sess_001 claude_code 1380176 max_scrolls=10 scroll_percent=0.80
```

**详细参数**：查看 `references/api/scroll_screenshot.md`

**注意**：只支持 `hijack` 和 `delegated` 模式，不支持 `background` 模式

---

## 中文、换行与Emoji

所有脚本均支持直接传入中文、换行符（`\n`）、Emoji，无需额外处理。

> **限制**：`api_call.sh`（bash脚本）不支持 Emoji，因为纯 bash 字符串拼接无法正确处理多字节 Unicode。如需输入 Emoji，请使用 Python 或 PowerShell 脚本。

> **注意**：手动curl时中文必须用Unicode编码（如 `\u4f60\u597d`），否则会乱码。

### 单指令示例

```bash
# Python版本（PowerShell/bash终端均可）
python scripts/api_call.py http://localhost:12261 TOKEN input_text ai_app_type=claude_code session_id=sess_001 main_window_id=123456 window_id=123456 x=50 y=35 "text=hello\n你好😊"

# PowerShell版本（兼容5.x和7.x）
powershell -ExecutionPolicy Bypass -File scripts/api_call.ps1 -ApiUrl http://localhost:12261 -Token TOKEN -Endpoint input_text ai_app_type=claude_code session_id=sess_001 main_window_id=123456 window_id=123456 x=50 y=35 "text=hello\n你好😊"

# bash版本（仅Git Bash/WSL，不支持Emoji）
bash scripts/api_call.sh http://localhost:12261 TOKEN input_text ai_app_type=claude_code session_id=sess_001 main_window_id=123456 window_id=123456 x=50 y=35 'text=hello\n你好'
```

### Batch示例

```bash
# Python版本（bash终端）
python scripts/api_call.py http://localhost:12261 TOKEN batch ai_app_type=claude_code session_id=sess_001 main_window_id=123456 window_id=123456 "instructions=[{\"action\":\"input_text\",\"params\":{\"x\":50,\"y\":35,\"text\":\"hello\\n你好😊\"}}]"

# PowerShell版本（兼容5.x和7.x，使用简化指令格式）
# 直接传入中文、Emoji、\n换行，脚本以UTF-8编码发送
powershell -ExecutionPolicy Bypass -File scripts/api_call_batch.ps1 -ApiUrl http://localhost:12261 -Token TOKEN -AiAppType claude_code -SessionId sess_001 -WindowId 123456 -MainWindowId 123456 -Instructions "input_text(x=50,y=35,text=hello\n你好😊)"
```

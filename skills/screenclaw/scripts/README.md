# ScreenClaw 可复用脚本

本目录包含 ScreenClaw 的可复用脚本，AI 可以直接调用这些脚本，无需每次重新生成代码。

## 环境选择规则

**重要**：根据当前 shell 环境选择对应脚本

| Shell 环境 | 使用脚本 |
|-----------|---------|
| bash / zsh | 使用 `.py` 脚本 |
| PowerShell | 使用 `.ps1` 脚本 |
| 不确定 | 优先使用 `.py` 脚本（更通用） |

**禁止混用**：
- ❌ 在 bash 中运行 `.ps1` 脚本
- ❌ 在 PowerShell 中运行 `.py` 脚本（除非用 `python xxx.py`）

---

## 脚本列表

### fetch_screenshot_cli.py / fetch_screenshot_cli.ps1
**用途**：处理截图 API 响应，自动判断本地/局域网场景

**功能**：
- 自动判断 API 地址是本地还是局域网
- 本地场景：直接使用返回的 `image_path`
- 局域网场景：解码 `image_base64` 并保存到本地
- 支持直接调用 API 或处理已保存的 JSON 响应（自动删除临时文件）

**bash/zsh 环境**（使用 .py）：
```bash
# 用法一：直接调用 API
python scripts/fetch_screenshot_cli.py <api_url> <token> <window_id> [session_id]

# 用法二：处理已保存的 JSON 响应
python scripts/fetch_screenshot_cli.py <json_file_path> <api_url>

# 示例
python scripts/fetch_screenshot_cli.py http://192.168.10.190:12261 TOKEN123 1380176 my-session
```

**PowerShell 环境**（使用 .ps1）：
```powershell
# 用法一：直接调用 API
.\scripts\fetch_screenshot_cli.ps1 <api_url> <token> <window_id> [session_id]

# 用法二：处理已保存的 JSON 响应
.\scripts\fetch_screenshot_cli.ps1 <json_file_path> <api_url>

# 示例
.\scripts\fetch_screenshot_cli.ps1 http://192.168.10.190:12261 TOKEN123 1380176 my-session
```

**详细文档**：`scripts/fetch_screenshot_cli.py`、`scripts/fetch_screenshot_cli.ps1`

---

### batch_results_processor.py
**用途**：处理 batch API 响应中的截图数据

**功能**：
- 从 batch 响应的 `results` 数组中提取截图
- 自动判断本地/局域网场景并处理
- 返回处理后的输出列表

**使用方式**：
```python
from scripts.batch_results_processor import process_batch_results

results = response.json()["data"]["results"]
output = process_batch_results(
    results,
    api_url="http://localhost:12261/api/batch"
)
```

**详细文档**：`scripts/batch_results_processor.py`

---

### batch_results_processor.ps1
**用途**：处理 batch API 响应中的截图数据（PowerShell 版本，仅限PowerShell环境）

**功能**：与 Python 版本相同，自动判断本地/局域网场景并处理截图

**使用方式**：
```powershell
# 导入脚本
. .\scripts\batch_results_processor.ps1

# 处理结果
$output = Get-BatchResultsOutput -Results $results -ApiUrl "http://localhost:12261/api/batch"
```

**详细文档**：`scripts/batch_results_processor.ps1`

---

## 使用建议

1. **环境判断**：先确认当前 shell 环境，再选择对应脚本
2. **优先使用方式一**：直接让脚本调用 API，更简洁高效
3. **临时文件规范**：如果需要先保存 JSON，必须保存到系统临时目录
4. **session_id 保持一致**：整个会话使用同一个 session_id，不要每次生成新的

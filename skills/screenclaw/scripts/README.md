# ScreenClaw 可复用脚本

本目录包含 ScreenClaw 的可复用脚本，AI 可以直接调用这些脚本，无需每次重新生成代码。

## 脚本列表

### fetch_screenshot_cli.py / fetch_screenshot_cli.ps1
**用途**：处理截图 API 响应，自动判断本地/局域网场景

**功能**：
- 自动判断 API 地址是本地还是局域网
- 本地场景：直接使用返回的 `image_path`
- 局域网场景：解码 `image_base64` 并保存到本地
- 支持直接调用 API 或处理已保存的 JSON 响应（自动删除临时文件）

**用法一（推荐）**：直接调用 API
```bash
# Python
python scripts/fetch_screenshot_cli.py <api_url> <token> <window_id> [session_id]

# PowerShell
.\scripts\fetch_screenshot_cli.ps1 <api_url> <token> <window_id> [session_id]

# 示例
python scripts/fetch_screenshot_cli.py http://192.168.10.190:12261 TOKEN123 1380176 my-session
```

**用法二（备用）**：处理已保存的 JSON 响应
```bash
# 注意：JSON 必须保存在系统临时目录，脚本会自动删除
# Windows: %TEMP% (C:\Users\xxx\AppData\Local\Temp)
# Linux/macOS: /tmp

# Python
python scripts/fetch_screenshot_cli.py <json_file_path> <api_url>

# PowerShell
.\scripts\fetch_screenshot_cli.ps1 <json_file_path> <api_url>

# 示例
python scripts/fetch_screenshot_cli.py C:\Users\xxx\AppData\Local\Temp\screenshot_response.json http://192.168.10.190:12261
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
**用途**：处理 batch API 响应中的截图数据（PowerShell 版本）

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

1. **优先使用方式一**：直接让脚本调用 API，更简洁高效
2. **临时文件规范**：如果需要先保存 JSON，必须保存到系统临时目录
3. **session_id 保持一致**：整个会话使用同一个 session_id，不要每次生成新的

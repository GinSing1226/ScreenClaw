# ScreenClaw 可复用脚本

本目录包含 ScreenClaw 的可复用脚本，供 Executor 角色调用。

## 环境选择

根据当前 shell 环境选择对应脚本：

| Shell 环境 | 使用脚本 |
|-----------|---------|
| bash / zsh | `.py` 脚本 |
| PowerShell | `.ps1` 脚本 |
| 不确定 | 优先 `.py` 脚本（更通用） |

---

## 脚本列表

### fetch_screenshot_cli.py / fetch_screenshot_cli.ps1

**用途**：处理 screenshot API 响应，自动判断本地/局域网场景

**功能**：
- 自动调用 API 获取截图
- 本地场景：直接使用返回的 `image_path`
- 局域网场景：解码 `image_base64` 并保存到本地
- 支持处理已保存的 JSON 响应（自动删除临时文件）

**调用方式**：

```bash
# Python（优先）
python scripts/fetch_screenshot_cli.py <api_url> <token> <window_id> [session_id]

# PowerShell（Windows）
.\scripts\fetch_screenshot_cli.ps1 <api_url> <token> <window_id> [session_id]
```

---

### batch_results_processor.py / batch_results_processor.ps1

**用途**：处理 batch API 响应中的截图数据

**功能**：
- 从 batch 响应的 `results` 数组中提取截图
- 自动判断本地/局域网场景并处理
- 返回处理后的输出列表

---

## 使用建议

1. **环境判断**：先确认当前 shell 环境，再选择对应脚本
2. **session_id 保持一致**：整个会话使用同一个 session_id
3. **临时文件**：如果需要先保存 JSON，必须保存到系统临时目录

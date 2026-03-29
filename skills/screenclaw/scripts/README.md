# ScreenClaw 可复用脚本

> **前置条件**：先确认 ScreenClaw 服务已启动，并已获取 API 地址和 Token

本目录包含 ScreenClaw 的可复用脚本，供 Executor 角色调用。

## 环境选择

根据当前 shell 环境选择对应脚本：

| Shell 环境 | 使用脚本 |
|-----------|---------|
| bash / zsh | `.py` 或 `.sh` 脚本 |
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
powershell -ExecutionPolicy Bypass -File scripts/fetch_screenshot_cli.ps1 <api_url> <token> <window_id> [session_id]
```

**参数说明**：
- `api_url`：ScreenClaw 服务地址（如 `http://localhost:12261`）
- `token`：认证令牌
- `window_id`：目标窗口 ID（从 get_window_list 获取）
- `session_id`：会话 ID（可选，默认 "default"）

**降级路径**：
```
Python脚本 → PowerShell脚本 → 报告用户无法执行
```

**坑点**：
- ⚠️ 中文目录名：某些环境下中文目录名可能创建失败，脚本会自动 fallback 到时间戳目录名
- ⚠️ 本地 vs 远程：不同场景返回格式不同，脚本会自动处理

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
3. **中文输入**：使用Unicode编码（如`\u4f60\u597d`）而非原始中文
4. **整行复制**：复制整行命令，不要分段复制
5. **只替换参数**：将参数替换为实际值，不要修改命令结构

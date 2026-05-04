---
name: screenclaw 脚本使用说明
description: ScreenClaw 统一脚本入口、降级顺序、点号路径格式和本地/远程图片处理规则
---

# ScreenClaw 统一脚本入口

AI 只调用公开入口：

```text
scripts/screenclaw.py
scripts/screenclaw.ps1
scripts/screenclaw.sh
```

不要调用 `_common.py` 或任何旧脚本。调用某个 API 前，阅读 `references/api/{endpoint}.md`，本文件不提供完整 API 参数示例。

## 降级路径

```text
screenclaw.py -> screenclaw.ps1 -> screenclaw.sh -> curl
```

| 错误类型 | 处理方式 |
|----------|----------|
| 参数错误 | 修正参数，重跑同一脚本，不降级 |
| API 业务错误 | 阅读对应 API 文档和服务端 message，不降级 |
| Python 不存在等环境错误 | 降级到 PowerShell 或 shell |

## 通用格式

Python：

```bash
python scripts/screenclaw.py <endpoint> api_url=<url> token=<token> ai_app_type=<type> session_id=<id> [endpoint参数...]
```

PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/screenclaw.ps1 <endpoint> api_url=<url> token=<token> ai_app_type=<type> session_id=<id> [endpoint参数...]
```

bash：

```bash
bash scripts/screenclaw.sh <endpoint> api_url=<url> token=<token> ai_app_type=<type> session_id=<id> [endpoint参数...]
```

## 点号路径格式

使用点号路径传递嵌套参数。PowerShell 下不要手写 JSON。

```text
grid.density_x=3.3
grid.density_y=5
coordinate.number_size=18
coordinate.number_density=1
marker.0.x=55
marker.0.y=65
step.0.action=click
step.0.params.x=50
step.0.params.y=35
```

点号路径会转换为 API 请求结构。具体参数和完整示例见对应 API 文档。

## 本地/远程图片处理

- 本地调用（`localhost` / `127.0.0.1` / `::1`）：服务端返回 `image_path`，脚本直接输出路径。
- 远程调用：服务端返回 `image_base64`，脚本负责解码并保存到 ScreenClaw 根目录的 `data/{ai_app_type}__{session_id}__{first-created-date}/`；同一 session 跨日期继续复用首次创建的目录。
- 可用 `SCREENCLAW_DATA_DIR` 覆盖 data 目录，或用 `SCREENCLAW_ROOT` 覆盖 ScreenClaw 根目录。
- 远程 `crop_zoom_screenshot`：如果传入 `source_image_path`，脚本会读取本地图片并改为 `source_image_base64` 发送给服务端。
- 远程 `batch`：嵌套截图、滚动截图、裁剪放大结果也会自动落盘；batch 内的 `crop_zoom_screenshot` 本地路径同样会自动转 base64。

## 输出规范

成功时：

- 图片类接口先输出图片路径。
- 然后输出服务端 message。
- 然后输出 `Data:` JSON 摘要，包含完整的 `requested_params`、`effective_params`、`effective_*` 等参数回显；脚本会去掉 `image_base64/source_image_base64`、`null`、空数组和空对象。
- 脚本不自行拼接成功提示。

错误时：

```text
API Error [ERROR_CODE]: service message
```

脚本自身错误：

```text
Script Error: reason
```

脚本会在调用前校验 endpoint 和参数名。未知 endpoint、未知参数名、必填参数缺失都属于脚本自身错误；先阅读 `skill.md` 和 `references/api/{endpoint}.md` 修正参数，不要用不存在的直觉参数。

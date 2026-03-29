---
name: screenshot
description: 截取窗口画面并绘制坐标网格，用于查看界面状态和定位目标元素坐标
---

# screenshot - 截图

## 使用目的
- 查看当前界面状态
- 定位目标元素的坐标
- 验证操作结果

## 什么时候用
- 首次操作某个窗口
- 每次操作后需要验证
- 不确定目标元素的坐标位置

## 什么时候不用
- 执行已知的固定操作序列，且不需要验证

---

## 请求

**方法**：POST `/api/screenshot`

**请求头**：
```
Authorization: Bearer {token}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `ai_app_type` | string | 是 | - | AI应用类型（如claude_code） |
| `session_id` | string | 是 | - | 会话唯一标识，整个会话保持一致 |
| `window_id` | int | 是 | - | 目标窗口句柄，从get_window_list获取 |
| `main_window_id` | int | 否 | - | 主窗口ID（用于恢复窗口） |
| `coordinate_type` | string | 否 | "grid" | 坐标类型：grid/no |

### 网格参数（coordinate_type=grid时）

| 参数 | 类型 | 默认值 | 说明 | 调整时机 |
|------|------|--------|------|----------|
| `density` | float | 5.0 | 网格密度（0-100） | 网格太宽时增大 |
| `opacity` | int | 50 | 网格透明度（0-100） | 遮挡内容时降低 |
| `color` | string | "#00FF00" | 网格颜色（HEX） | 与内容冲突时更换 |
| `number_density` | int | 2 | 每隔几格显示坐标 | 数字太少时减小 |
| `number_decimal` | int | 0 | 小数位数（0-4） | 需要更高精度时增大 |
| `number_size` | int | 8 | 字体大小（4-32） | 数字太小时增大 |
| `number_color` | string | "#00FF00" | 数字颜色（HEX） | 与背景冲突时更换 |
| `number_opacity` | int | 100 | 数字透明度（0-100） | 不够清晰时增大 |

### 请求示例

**基础截图**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "coordinate_type": "grid"
}
```

**调整网格参数**（当默认参数难以判断坐标时）：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "coordinate_type": "grid",
  "grid": {"density": 10, "opacity": 60, "color": "#FF0000"},
  "coordinate": {"number_size": 12, "number_density": 1}
}
```

**不带网格**（用于保存图片）：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "coordinate_type": "no"
}
```

---

## 响应格式

**本地请求**（localhost, 127.0.0.1, ::1）：
```json
{
  "success": true,
  "data": {
    "image_path": "D:\\screenClaw\\data\\session-123\\screenshot_20250329_143025.png"
  }
}
```

**远程请求**（局域网IP）：
```json
{
  "success": true,
  "data": {
    "image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
  }
}
```

**区别**：
- 本地请求：只返回 `image_path`（图片已在服务端保存）
- 远程请求：返回 `image_base64`（客户端需自行解码保存）

---

## 响应处理

### 本地请求（localhost, 127.0.0.1, ::1）

**直接使用返回的 `image_path`，无需脚本**

```python
response = requests.post(url, headers=headers, json=body)
result = response.json()
image_path = result["data"]["image_path"]
# 直接读取图片
with open(image_path, "rb") as f:
    image_data = f.read()
```

### 远程请求（局域网IP）

**必须使用脚本处理 base64**

```bash
# Python（推荐，跨平台）
python scripts/fetch_screenshot_cli.py <api_url> <token> <window_id> [session_id]

# PowerShell（Windows）
.\scripts\fetch_screenshot_cli.ps1 <api_url> <token> <window_id> [session_id]
```

脚本会自动：
1. 解码 `image_base64`
2. 保存到 `%APPDATA%\screenclaw\data`（Windows）或 `~/.local/share/screenclaw/data`（Linux/macOS）
3. 返回保存后的图片路径

### ❌ 禁止以下做法

```python
# ❌ 错误：本地请求也调用脚本（多余）
image_path = fetch_screenshot_cli.py(...)  # 不需要

# ❌ 错误：远程请求自己写保存逻辑（路径会混乱）
if "image_base64" in result["data"]:
    with open("screenshot.png", "wb") as f:
        f.write(base64.b64decode(result["data"]["image_base64"]))
```

---

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `SCREENSHOT_FAILED` | 截图失败 | 窗口可能已最小化或被遮挡 |
| `PROCESS_BLOCKED` | 进程在禁止清单中 | 检查ScreenClaw的禁止列表配置 |

---

## 参数调整指南

### 坐标难以判断时

如果需要长时间分析才能确定坐标，说明参数需要调整：

| 问题 | 解决方案 |
|------|----------|
| 网格太宽 | 增大 `density`（如改为10） |
| 网格遮挡内容 | 降低 `opacity`（如改为30） |
| 颜色混淆 | 更换 `color`（如改为#FF0000） |
| 数字太少 | 减小 `number_density`（如改为1） |
| 数字太小 | 增大 `number_size`（如改为12） |
| 数字颜色看不清 | 更换 `number_color`（如改为#FFFF00） |

### 截图不完整

**原因**：应用跨屏幕、被最小化、在托盘里、部分超出屏幕
**解决**：请求用户协助，将应用显示在桌面上

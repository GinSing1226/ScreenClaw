---
name: screenshot
description: 截取窗口画面并绘制坐标网格，用于查看界面状态和定位目标元素坐标
---

# screenshot - 截图

## 使用目的
截取指定窗口的画面，并在图片上绘制坐标网格，用于：
- 查看当前界面状态
- 定位目标元素的坐标
- 验证操作结果

## 什么时候用
- 首次操作某个窗口，需要了解界面布局
- 每次操作后需要验证结果
- 不确定目标元素的坐标位置

## 什么时候不用
- 执行已知的固定操作序列（如已沉淀的场景模板），且不需要验证

---

## 请求

**方法**：POST
**路径**：`/api/screenshot`
**请求头**：
```
Authorization: Bearer {token}
Content-Type: application/json
```

### 请求参数

#### 通用参数

| 参数 | 类型 | 必填 | 默认值 | 说明 | 从哪里获取 |
|------|------|------|--------|------|----------|
| `ai_app_type` | string | 是 | - | AI应用类型 | 判断当前AI是什么应用，就用什么值 |
| `session_id` | string | 是 | - | 会话唯一标识 | 获取当前会话唯一标识，获取不到则随机生成 |
| `window_id` | int | 是 | - | 目标窗口句柄 | 从get_window_list获取 |
| `main_window_id` | int | 否 | - | 主窗口ID（用于恢复窗口） | 从get_window_list获取 |
| `coordinate_type` | string | 否 | "grid" | 坐标类型：grid/no | 需要网格时用grid |

#### 网格参数（grid）

| 参数 | 类型 | 必填 | 默认值 | 说明 | 适用场景 |
|------|------|------|--------|------|----------|
| `density` | float | 否 | 5.0 | 网格密度（0-100） | 网格太宽时增大 |
| `opacity` | int | 否 | 50 | 网格透明度（0-100） | 网格遮挡内容时降低 |
| `color` | string | 否 | "#00FF00" | 网格颜色（HEX） | 颜色与内容冲突时更换 |

#### 坐标数字参数（coordinate）

| 参数 | 类型 | 必填 | 默认值 | 说明 | 适用场景 |
|------|------|------|--------|------|----------|
| `number_density` | int | 否 | 2 | 数字密度（每隔几格显示坐标） | 数字太少时减小 |
| `number_decimal` | int | 否 | 0 | 小数位数（0-4） | 需要更高精度时增大 |
| `number_size` | int | 否 | 8 | 字体大小（4-32） | 数字太小时增大 |
| `number_color` | string | 否 | "#00FF00" | 数字颜色（HEX） | 颜色与背景冲突时更换 |
| `number_opacity` | int | 否 | 100 | 数字透明度（0-100） | 数字不够清晰时增大 |

### 请求示例

#### 基础截图（使用默认参数）
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "coordinate_type": "grid"
}
```

#### 自定义网格参数
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "coordinate_type": "grid",
  "grid": {
    "density": 5,
    "opacity": 60,
    "color": "#00FF00"
  },
  "coordinate": {
    "number_density": 2,
    "number_decimal": 0,
    "number_size": 12,
    "number_color": "#00FF00",
    "number_opacity": 100
  }
}
```

#### 不带网格（用于保存图片）
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "coordinate_type": "no"
}
```

---

## 响应

### 成功响应
```json
{
  "success": true,
  "message": "截图成功",
  "data": {
    "image_path": "D:/screenClaw/data/.../screenshot.png",
    "image_base64": "iVBORw0KGgo..."
  }
}
```

### 字段说明
- `image_path`：图片在本地的绝对路径（可直接读取）
- `image_base64`：图片的base64编码（用于传输）

---

## 响应处理

**推荐方式**：直接调用脚本，让脚本自己调用 API 并处理

### 方式一（推荐）：直接调用脚本

```
✅ AI: 直接调用脚本，传入 API 参数

python scripts/fetch_screenshot_cli.py http://localhost:12261 TOKEN123 1380176

# 脚本会自己：
# 1. 调用 API
# 2. 获取响应
# 3. 处理图片保存
# 4. 返回结果
```

### 方式二（备用）：先调用 API，再处理

如果因特殊原因需要先调用 API（如需要查看响应内容），请遵守以下规范：

1. **临时 JSON 必须保存到系统临时目录**：
   - Windows: `%TEMP%` （即 `C:\Users\用户名\AppData\Local\Temp`）
   - Linux/macOS: `/tmp`

2. **使用脚本处理时，脚本会自动删除临时 JSON**

```python
# 步骤1：调用 API
response = requests.post("http://localhost:12261/api/screenshot", ...)
data = response.json()

# 步骤2：保存 JSON 到系统临时目录
import tempfile
temp_path = os.path.join(tempfile.gettempdir(), "screenshot_response.json")
with open(temp_path, "w") as f:
    json.dump(data, f)

# 步骤3：调用脚本处理（会自动删除 temp_path）
python scripts/fetch_screenshot_cli.py <temp_path> http://localhost:12261
```

### 为什么推荐方式一
1. **不产生临时文件**（更干净）
2. **减少网络请求**（一次调用完成）
3. **降低复杂度**（无需管理中间文件）

### 脚本工作流程

当你调用 `fetch_screenshot_cli.py` 时，脚本会：
1. **方式一**：自己调用 ScreenClaw API → 获取响应 → 处理图片保存
2. **方式二**：读取 JSON 文件 → 处理图片保存 → **自动删除** JSON 文件

---

## 调用方式

### Python

```python
from scripts.fetch_screenshot import fetch_screenshot_auto

result_path = fetch_screenshot_auto(
    api_base_url="http://localhost:12261",
    token="your-token",
    window_id=12345,
    session_id="claude-code-20260328-001"
)
```

### PowerShell

```python
from scripts.fetch_screenshot import fetch_screenshot_auto

result_path = fetch_screenshot_auto(
    api_base_url="http://localhost:12261",
    token="your-token",
    window_id=12345,
    session_id="claude-code-20260328-001"
)
```

### 调用方式（PowerShell）

```powershell
# 导入脚本
. .\scripts\fetch_screenshot.ps1

# 调用函数
Get-Screenshot -ApiUrl "http://localhost:12261/api/screenshot" -Token "your-token" -WindowId 12345
```

### PowerShell 调用方式

```powershell
# 导入脚本
. .\scripts\fetch_screenshot.ps1

# 调用函数
Get-Screenshot -ApiUrl "http://localhost:12261/api/screenshot" -Token "your-token" -WindowId 12345
```

### ❌ 禁止以下做法

```python
# ❌ 错误：自己写保存逻辑
import base64
with open("screenshot.png", "wb") as f:
    f.write(base64.b64decode(data))

# ❌ 错误：每次生成新的 session_id
session_id = f"session-{time.time()}"  # 这会导致图片分散
```

### 处理逻辑说明

```
调用 screenshot API
       │
       ▼
检查 API 地址
       │
   ┌───┴───┐
   │       │
localhost  其他 IP/域名
   │       │
   ▼       ▼
直接使用   解码 base64
image_path  保存到本地
```

**详细文档**：`scripts/fetch_screenshot.py` 和 `scripts/fetch_screenshot.ps1`

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
如果需要长时间分析思考才能确定坐标，说明参数需要调整：

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 网格太宽，不好判断 | density太小 | 增大density值（如改为10） |
| 网格遮挡内容 | opacity太高 | 降低opacity值（如改为30） |
| 网格颜色与内容冲突 | color不合适 | 更换color（如改为#FF0000红色） |
| 数字太少，定位困难 | number_density太大 | 减小number_density值（如改为1） |
| 数字太小看不清 | number_size太小 | 增大number_size值（如改为12） |
|数字颜色看不见 | number_color冲突 | 更换number_color（如改为#FFFF00黄色） |
| 数字不够清晰 | number_opacity太低 | 增大number_opacity值（如改为100） |

### 截图不完整
- 原因：应用跨屏幕、被最小化、在托盘里、部分超出屏幕
- 解决：请求用户协助，将应用显示在桌面上

---

## 使用技巧

1. **首次截图**：使用默认参数，查看效果
2. **调整参数**：根据需要逐步调整单个参数，验证效果
3. **保存截图**：用于文档或报告时，使用`coordinate_type: "no"`不带网格
4. **定位坐标**：分析截图时，遵循"先定位区域，再放大确认"的两步法

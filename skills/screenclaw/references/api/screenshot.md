---
name: screenshot
description: 截取窗口画面并绘制坐标网格，用于查看界面和定位元素
---

# screenshot - 截图

## 使用前必读

### 使用目的和效果
截取窗口画面并叠加坐标网格。用于查看界面状态、定位目标元素坐标、验证操作结果。坐标是后续点击、输入等操作的关键依据。

### 适用场景
- 首次操作某个窗口
- 每次操作后验证结果
- 不确定目标元素的坐标位置
- 需要调整网格参数以精确定位

### 不适用场景
- 执行已知的固定操作序列且不需要验证

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
| `ai_app_type` | string | 是 | - | AI应用类型 |
| `session_id` | string | 是 | - | 会话唯一标识 |
| `window_id` | int | 是 | - | 目标窗口句柄 |
| `main_window_id` | int | 是 | - | 主窗口ID（用于激活最小化窗口） |
| `coordinate_type` | string | 否 | "grid" | 坐标类型：grid（带网格）/no（无网格） |
| `color_mode` | string | 否 | "grayscale" | 颜色模式：grayscale（灰度）/color（原色） |

### 网格参数（coordinate_type=grid时）

| 参数 | 类型 | 默认值 | 说明 | 调整时机 |
|------|------|--------|------|----------|
| `density` | float | 5.0 | 每格宽度（像素），越小越密 | 网格太宽，读不出坐标时减小 |
| `opacity` | int | 50 | 网格透明度(0-100) | 网格遮挡太多内容时降低 |
| `color` | string | "#ff0000" | 网格颜色(HEX) | 与内容冲突时更换 |
| `number_density` | int | 2 | 每隔几格显示坐标 | 数字太少时减小 |
| `number_decimal` | int | 0 | 小数位数(0-4) | 需要精度时增大 |
| `number_size` | int | 12 | 字体大小(4-64) | 看不清数字时增大 |
| `number_color` | string | "#ff0000" | 数字颜色(HEX) | 与背景冲突时更换 |
| `number_opacity` | int | 100 | 数字透明度(0-100) | 不够清晰时增大 |

### 请求示例

**基础截图**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "coordinate_type": "grid"
}
```

**调整网格参数**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "coordinate_type": "grid",
  "grid": {"density": 10, "opacity": 60, "color": "#FF0000"},
  "coordinate": {"number_size": 12, "number_density": 1}
}
```

**不带网格**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "coordinate_type": "no"
}
```

### 响应处理

**本地请求**（localhost/127.0.0.1/::1）：返回 `image_path`，图片已在服务端保存，直接使用路径。

**远程请求**（局域网IP）：返回 `image_base64`，必须使用脚本处理：
```bash
python scripts/fetch_screenshot_cli.py <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id>
```
脚本会自动解码base64、保存到正确位置、返回图片路径。

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `SCREENSHOT_FAILED` | 截图失败 | 窗口可能已最小化或被遮挡 |
| `PROCESS_BLOCKED` | 进程在禁止清单中 | 检查ScreenClaw的禁止列表配置 |

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但坐标找不到或网格看不清** → 先调整网格参数，无效后查阅 SKILL.md「常见问题排查」
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **坐标难以判断时调整参数**：

| 问题 | 解决方案 |
|------|----------|
| 网格太宽 | 减小 `density`（如改为3） |
| 网格遮挡内容 | 降低 `opacity`（如改为30） |
| 数字太少 | 减小 `number_density`（如改为1） |
| 数字太小 | 增大 `number_size`（如改为16） |
| 数字颜色看不清 | 更换 `number_color`（如改为#FFFF00） |

- **截图不完整**：应用可能跨屏幕、被最小化、在托盘里。用 main_window_id 激活窗口，或请求用户协助将应用显示在桌面上

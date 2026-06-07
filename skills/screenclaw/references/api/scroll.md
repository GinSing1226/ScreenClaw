---
name: scroll
description: 鼠标滚轮滚动（浏览长内容、列表）
---

# scroll - 滚动

## 使用前必读

### 使用目的和效果
在指定位置执行鼠标滚轮滚动。可浏览长内容（文章、网页）、滚动列表查看更多内容。滚动量和方向由delta参数控制。

### 适用场景
- 需要浏览长内容或列表
- 需要上下滚动页面
- 内容超出可视范围

### 不适用场景
- 触摸式滑动 → 使用 `swipe`
- 简单点击 → 使用 `click`

## 请求

**方法**：POST `/api/scroll`

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
| `main_window_id` | int | 是 | - | 主窗口ID |
| `x` | float | 是 | - | 鼠标位置横坐标 |
| `y` | float | 是 | - | 鼠标位置纵坐标 |
| `delta` | int | 是 | - | 滚动量（正值向上，负值向下） |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack |

### 操作方式

| 方式 | 特点 | 注意 |
|------|------|------|
| `background` | 不抢夺鼠标，用户可继续使用电脑 | 滚动坐标位置不能被其他软件遮挡 |
| `hijack` | 会短暂占用鼠标 | 无遮挡限制 |

**建议**：优先background，无效时用hijack

### 请求示例

```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "x": 50.0,
  "y": 50.0,
  "delta": -120,
  "action_method": "background"
}
```

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `USER_DENIED` | 用户拒绝操作 | 用户取消了确认弹窗 |

## 常见问题

### 遇到问题时的排查顺序
1. **API成功但滚动效果不对** → 查阅 SKILL.md「常见问题排查」
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **delta值**：不同软件的滚动程度差异很大，需截图多次尝试。建议先试用小值（如 -120），根据效果调整
- **滚动方向**：负值向下滚动（如 -120），正值向上滚动（如 120）
- **鼠标位置**：x和y指定滚动时鼠标的位置，通常放在内容区域中央
- **background遮挡**：background模式下滚动坐标不能被其他软件遮挡

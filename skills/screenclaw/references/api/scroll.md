---
name: scroll
description: 在指定位置执行鼠标滚轮滚动。适用：浏览列表、页面、长内容。不适用：触摸式滑动用 swipe。
---

# scroll - 滚动

## 快速决策

- 鼠标位置应放在可滚动内容区域。
- 负值向下滚动，正值向上滚动。
- 如果 background 下坐标被遮挡或无效，先换坐标，最后再考虑 hijack。

## 脚本调用

```bash
python scripts/screenclaw.py scroll api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} x=50 y=50 delta=-120 action_method=background
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `x` | float | 是 | 鼠标位置横坐标 |
| `y` | float | 是 | 鼠标位置纵坐标 |
| `delta` | int | 是 | 滚动量，负值向下，正值向上 |
| `action_method` | string | 否 | `background` 或 `hijack` |

## 常见问题

1. **滚动无效**：换到内容区域中央，或确认窗口可滚动。
2. **滚太多/太少**：调整 `delta`，建议从 `-120` 或 `120` 开始。
3. **移动端/游戏不响应滚轮**：改用 `swipe`。

---
name: swipe
description: 从起始坐标滑动到终止坐标，触摸式滑动。适用：移动应用、模拟器、游戏、上下左右翻页。不适用：鼠标滚轮滚动用 scroll，拖动物体用 drag。
---

# swipe - 滑动

## 快速决策

- 移动端、模拟器、游戏优先考虑 swipe。
- 桌面滚轮页面优先用 `scroll`。
- 起点和终点都必须来自截图坐标。

## 脚本调用

```bash
python scripts/screenclaw.py swipe api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} start_x=50 start_y=80 end_x=50 end_y=20 action_method=background
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `start_x` | float | 是 | 起始横坐标 |
| `start_y` | float | 是 | 起始纵坐标 |
| `end_x` | float | 是 | 结束横坐标 |
| `end_y` | float | 是 | 结束纵坐标 |
| `action_method` | string | 否 | `background` 或 `hijack` |

## 常见问题

1. **滑动无效**：确认窗口和坐标，必要时换子窗口。
2. **方向反了**：重新检查起点终点，不要用内部视觉坐标推测。
3. **滚轮不生效的页面**：用 swipe 替代 scroll。

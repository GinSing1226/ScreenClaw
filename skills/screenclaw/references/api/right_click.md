---
name: right_click
description: 在指定坐标右键点击，打开上下文菜单。不适用：左键操作即可完成的场景。
---

# right_click - 右键点击

## 快速决策

- 用于打开上下文菜单。
- 右键菜单可能是新窗口或子窗口；右键后要截图或重新 get_window_list。
- 右键后需要立刻观察时，用 batch 接 screenshot。

## 脚本调用

```bash
python scripts/screenclaw.py right_click api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} x=50 y=50 action_method=background
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `x` | float | 是 | 横坐标百分比 |
| `y` | float | 是 | 纵坐标百分比 |
| `action_method` | string | 否 | `background` 优先；必要时 `hijack` |

## 常见问题

1. **菜单没出来**：重新截图确认坐标和窗口。
2. **截图看不到菜单**：菜单可能是新窗口，重新 `get_window_list`。

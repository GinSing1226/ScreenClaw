---
name: long_press
description: 在指定坐标长按，触发长按菜单或特殊功能。不适用：普通点击用 click。
---

# long_press - 长按

## 快速决策

- 用于长按菜单、移动端长按、游戏或应用特殊长按操作。
- 长按后菜单可能短暂出现，建议用 batch 接 `wait` 和 `screenshot`。
- 操作后必须截图验证。

## 脚本调用

```bash
python scripts/screenclaw.py long_press api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} x=50 y=50 duration_ms=1000 action_method=background
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `x` | float | 是 | 横坐标百分比 |
| `y` | float | 是 | 纵坐标百分比 |
| `duration_ms` | int | 否 | 长按时长，默认 500 |
| `action_method` | string | 否 | `background` 或 `hijack` |

## 常见问题

1. **菜单没出来**：换坐标、增加 `duration_ms`、或用 `hijack`。
2. **菜单很快消失**：用 batch 把长按、等待、截图合并。

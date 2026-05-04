---
name: hover
description: 鼠标悬浮到指定坐标并停留，触发 tooltip、滚动条、隐藏按钮等悬停 UI。不适用：点击用 click，输入用 input_text。
---

# hover - 鼠标悬浮

## 快速决策

- hover 后 UI 可能需要短暂等待才出现。
- hover 的持续时间不等于 batch 阻塞等待；需要观察隐藏 UI 时，在 batch 中加 `wait` 和 `screenshot`。
- hover 后必须截图验证隐藏内容是否出现。

## 脚本调用

单步 hover：

```bash
python scripts/screenclaw.py hover api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} x=50 y=30 duration_ms=500 action_method=background
```

hover 后截图：

```bash
python scripts/screenclaw.py batch api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} step.0.action=hover step.0.params.x=50 step.0.params.y=30 step.1.action=wait step.1.params.duration_ms=300 step.2.action=screenshot step.2.params.coordinate_type=no
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `x` | float | 是 | 横坐标百分比 |
| `y` | float | 是 | 纵坐标百分比 |
| `duration_ms` | int | 否 | 停留时长，默认 500 |
| `action_method` | string | 否 | `background` 或 `hijack` |

## 常见问题

1. **tooltip 没出来**：换坐标，或在 batch 中增加 wait。
2. **截图时隐藏 UI 消失**：把 hover、wait、screenshot 放进同一个 batch。

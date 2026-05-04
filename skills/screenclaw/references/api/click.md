---
name: click
description: 单击指定坐标，触发按钮、进入页面、激活控件。不适用：需要输入文本用 input_text，需要长按用 long_press，需要滑动或滚动用 swipe/scroll。
---

# click - 点击

## 快速决策

- 坐标必须先通过截图读取并尽量 marker 反验。
- 输入框输入文本优先用 `input_text x=... y=... text=...`，不要先 click 再 input_text。
- API 成功后必须截图验证界面是否变化。

## 脚本调用

```bash
python scripts/screenclaw.py click api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} x=50 y=35 action_method=background
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `window_id` | int | 是 | 目标窗口句柄 |
| `main_window_id` | int | 是 | 主窗口 ID |
| `x` | float | 是 | 横坐标百分比 |
| `y` | float | 是 | 纵坐标百分比 |
| `action_method` | string | 否 | `background` 优先；必要时 `hijack` |

## 常见问题

1. **API 成功但无效果**：截图验证坐标、窗口 ID、目标控件状态。
2. **background 无效**：先确认窗口和坐标，最后再切 `hijack`。

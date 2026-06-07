---
name: desktop_double_click
description: 在指定显示器坐标位置执行双击。固定 hijack 模式。
---

# desktop_double_click - 桌面双击

## 快速决策

- 坐标必须先通过 `desktop_screenshot` 截图读取。
- 固定 hijack 模式，delegated 模式激活时自动跳过确认。

## 脚本调用

```bash
python scripts/screenclaw.py desktop_double_click api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} monitor_index=0 x=50 y=35
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `monitor_index` | int | 是 | 目标显示器索引 |
| `x` | float | 是 | 横坐标百分比 |
| `y` | float | 是 | 纵坐标百分比 |

---
name: desktop_hover
description: 在指定显示器坐标位置执行鼠标悬浮。固定 hijack 模式。
---

# desktop_hover - 桌面悬浮

## 快速决策

- 悬浮效果是瞬时 UI，建议在 batch 中接 `wait` + `desktop_screenshot` 捕获。
- 固定 hijack 模式，delegated 模式激活时自动跳过确认。

## 脚本调用

```bash
python scripts/screenclaw.py desktop_hover api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} monitor_index=0 x=50 y=35 duration_ms=1000
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `monitor_index` | int | 是 | 目标显示器索引 |
| `x` | float | 是 | 横坐标百分比 |
| `y` | float | 是 | 纵坐标百分比 |
| `duration_ms` | int | 否 | 悬浮时长（ms），默认 1000 |

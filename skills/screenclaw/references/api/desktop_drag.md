---
name: desktop_drag
description: 桌面拖拽，支持同屏拖拽和跨屏拖拽。固定 hijack 模式。
---

# desktop_drag - 桌面拖拽

## 快速决策

- 支持同屏和跨屏拖拽，起点和终点分别指定各自的显示器索引。
- 固定 hijack 模式，delegated 模式激活时自动跳过确认。
- API 成功后必须 `desktop_screenshot` 验证。

## 脚本调用

同屏拖拽：

```bash
python scripts/screenclaw.py desktop_drag api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} monitor_index=0 start_x=30 start_y=50 end_monitor_index=0 end_x=70 end_y=50
```

跨屏拖拽：

```bash
python scripts/screenclaw.py desktop_drag api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} monitor_index=0 start_x=80 start_y=50 end_monitor_index=1 end_x=20 end_y=50
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `monitor_index` | int | 是 | 起点显示器索引 |
| `start_x` | float | 是 | 起点横坐标百分比 |
| `start_y` | float | 是 | 起点纵坐标百分比 |
| `end_monitor_index` | int | 是 | 终点显示器索引 |
| `end_x` | float | 是 | 终点横坐标百分比 |
| `end_y` | float | 是 | 终点纵坐标百分比 |
| `duration_ms` | int | 否 | 拖拽持续时间，默认 500 |

## 常见问题

1. **拖拽未生效**：确认起终点坐标和显示器索引，`desktop_screenshot` 验证。
2. **跨屏拖拽失败**：确认两个显示器索引均有效。

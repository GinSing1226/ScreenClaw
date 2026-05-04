---
name: drag
description: 从起始坐标拖拽到终止坐标，按住鼠标左键移动后释放。适用：滑块、面板拖动、文件拖放。不适用：快速触摸式滑动用 swipe，滚轮滚动用 scroll。
---

# drag - 拖拽

## 快速决策

- 拖动物体、滑块、窗口内元素用 drag。
- 起点和终点都要截图定位。
- 跨窗口拖拽会自动使用 `hijack`，更推荐优先尝试复制粘贴。

## 脚本调用

同窗口拖拽：

```bash
python scripts/screenclaw.py drag api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} start_x=30 start_y=50 end_x=70 end_y=50 duration_ms=500 action_method=background
```

跨窗口拖拽：

```bash
python scripts/screenclaw.py drag api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={source_window_id} main_window_id={source_main_window_id} target_window_id={target_window_id} target_main_window_id={target_main_window_id} start_x=50 start_y=50 end_x=50 end_y=50 duration_ms=1000
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `start_x` | float | 是 | 源窗口起始横坐标 |
| `start_y` | float | 是 | 源窗口起始纵坐标 |
| `end_x` | float | 是 | 终止横坐标 |
| `end_y` | float | 是 | 终止纵坐标 |
| `duration_ms` | int | 否 | 拖拽时长，默认 500 |
| `action_method` | string | 否 | `background` 或 `hijack` |
| `target_window_id` | int | 否 | 跨窗口目标窗口 |
| `target_main_window_id` | int | 否 | 跨窗口目标主窗口 |

跨窗口时，`start_x/start_y` 相对源窗口，`end_x/end_y` 相对目标窗口。

## 常见问题

1. **拖放失败**：增大 `duration_ms`。
2. **跨窗口失败**：确认两个窗口都可见，坐标分别来自对应窗口截图。
3. **能复制粘贴就不要拖拽**：跨窗口拖拽对焦点和可见性更敏感。

---
name: mouse_move
description: 相对位移移动鼠标，用于游戏视角控制和硬件级鼠标移动。不支持 background。
---

# mouse_move - 鼠标移动

## 快速决策

- 只用于相对移动视角，不用于移动到某个坐标；移动到坐标用 hover。
- 仅支持 `hijack` 和托管模式。
- 游戏视角需要截图 -> 调整 delta -> 截图循环，不必精确计算角度。

## 脚本调用

```bash
python scripts/screenclaw.py mouse_move api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} delta_x=200 delta_y=0 duration_ms=300 action_method=hijack
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `delta_x` | int | 是 | 水平相对位移，正值向右 |
| `delta_y` | int | 是 | 垂直相对位移，正值向下 |
| `duration_ms` | int | 否 | 移动时长，默认 300 |
| `action_method` | string | 否 | `hijack`；托管模式下自动路由 |

## 常见问题

1. **视角没变**：增大 delta，确认使用 `hijack` 或托管。
2. **来回抵消**：不要先右移又左移；找目标时保持同一方向扫描。
3. **需要连续实时控制**：请求用户确认进入托管模式。

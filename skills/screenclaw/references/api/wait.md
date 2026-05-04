---
name: wait
description: batch API 内多指令之间的等待。普通会话等待请用你自己的 sleep 工具。
---

# wait - 等待

## 快速决策

- `wait` 主要用于 batch 中等待 UI 稳定。
- 单独等待不需要调用 ScreenClaw API，直接用本地 sleep 工具即可。
- `wait` 不需要 `main_window_id`。

## 脚本调用

精确等待：

```bash
python scripts/screenclaw.py wait api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} duration_ms=300
```

batch 中等待：

```bash
python scripts/screenclaw.py batch api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} step.0.action=click step.0.params.x=50 step.0.params.y=50 step.1.action=wait step.1.params.duration_ms=500 step.1.params.random_range=200 step.2.action=screenshot step.2.params.coordinate_type=no
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `window_id` | int | 是 | 目标窗口句柄 |
| `duration_ms` | int | 是 | 等待时长 |
| `random_range` | int | 否 | 随机波动范围，实际等待 `duration_ms ± random_range` |

## 常见问题

1. **等待后界面无变化**：通常是前一步操作无效，回去截图验证坐标。
2. **动画未完成**：增加 `duration_ms`。

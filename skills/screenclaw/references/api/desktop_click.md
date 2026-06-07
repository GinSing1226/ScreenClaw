---
name: desktop_click
description: 在指定显示器坐标位置执行单击。固定 hijack 模式。
---

# desktop_click - 桌面单击

## 快速决策

- 坐标必须先通过 `desktop_screenshot` 截图读取并尽量 marker 反验。
- 固定 hijack 模式，无 `action_method` 参数。delegated 模式激活时自动跳过确认。
- API 成功后必须 `desktop_screenshot` 验证。

## 脚本调用

```bash
python scripts/screenclaw.py desktop_click api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} monitor_index=0 x=50 y=35
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `monitor_index` | int | 是 | 目标显示器索引 |
| `x` | float | 是 | 横坐标百分比 |
| `y` | float | 是 | 纵坐标百分比 |

## 常见问题

1. **API 成功但无效果**：`desktop_screenshot` 验证坐标和目标状态。
2. **弹出确认弹窗**：正常行为（hijack 模式），进入 delegated 模式可跳过。

---
name: desktop_scroll
description: 在指定显示器坐标位置执行鼠标滚轮滚动。固定 hijack 模式。
---

# desktop_scroll - 桌面滚动

## 快速决策

- `delta` 正值向上滚动，负值向下滚动。
- 固定 hijack 模式，delegated 模式激活时自动跳过确认。

## 脚本调用

```bash
python scripts/screenclaw.py desktop_scroll api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} monitor_index=0 x=50 y=50 delta=-3
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `monitor_index` | int | 是 | 目标显示器索引 |
| `x` | float | 是 | 横坐标百分比 |
| `y` | float | 是 | 纵坐标百分比 |
| `delta` | int | 是 | 滚动量，正值向上，负值向下 |

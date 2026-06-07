---
name: desktop_press_key
description: 在指定显示器上下文中执行键盘按键/组合键。固定 hijack 模式。适用于 Win 键、Alt+Tab 等系统级快捷键。
---

# desktop_press_key - 桌面按键

## 快速决策

- 按键组合用空格分隔，如 `"ctrl c"`、`"alt tab"`、`"win"`。
- 传了 `x`/`y` 会先点击定位再按键，不传则直接按键。
- 固定 hijack 模式，delegated 模式激活时自动跳过确认。

## 脚本调用

直接按键：

```bash
python scripts/screenclaw.py desktop_press_key api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} monitor_index=0 keys="alt tab"
```

先点击再按键：

```bash
python scripts/screenclaw.py desktop_press_key api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} monitor_index=0 x=50 y=35 keys="ctrl a"
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `monitor_index` | int | 是 | 目标显示器索引 |
| `keys` | string | 是 | 按键组合，空格分隔 |
| `x` | float | 否 | 横坐标百分比（先点击） |
| `y` | float | 否 | 纵坐标百分比（先点击） |
| `duration_ms` | int | 否 | 按住时长（ms），默认 0 |

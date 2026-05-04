---
name: press_key
description: 模拟键盘按键，组合键用空格连接。适用：快捷键、Enter/Escape 等特殊按键。不适用：输入长文本用 input_text。
---

# press_key - 按键

## 快速决策

- 组合键用空格，例如 `key="ctrl c"`，不是 `ctrl+c`。
- 需要先聚焦控件时传 `x/y`。
- 需要保持按键状态或连续组合动作时，用 batch。

## 脚本调用

```bash
python scripts/screenclaw.py press_key api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} key="ctrl c" action_method=background
```

先点击再按键：

```bash
python scripts/screenclaw.py press_key api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} x=50 y=50 key=enter action_method=background
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `key` | string | 是 | 按键名，组合键用空格连接 |
| `x` | float | 否 | 先点击此横坐标 |
| `y` | float | 否 | 先点击此纵坐标 |
| `duration_ms` | int | 否 | 按住时长，0 表示立即释放 |
| `action_method` | string | 否 | `background`、`hijack` 或托管路由 |

## 常见问题

1. **按键无效**：传 `x/y` 先聚焦，或换窗口。
2. **组合键没保持住**：把连续动作放到同一个 batch。
3. **平台键不同**：Windows 用 ctrl/alt/win，mac 场景需按用户环境调整。

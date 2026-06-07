---
name: desktop_input_text
description: 在指定显示器坐标位置输入文本，先点击获取焦点再通过剪贴板粘贴。固定 hijack 模式。
---

# desktop_input_text - 桌面文本输入

## 快速决策

- 会先在指定坐标点击获取焦点，再通过剪贴板粘贴输入文本。
- 固定 hijack 模式，delegated 模式激活时自动跳过确认。
- API 成功后必须 `desktop_screenshot` 验证。

## 脚本调用

```bash
python scripts/screenclaw.py desktop_input_text api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} monitor_index=0 x=50 y=35 text="Hello World"
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `monitor_index` | int | 是 | 目标显示器索引 |
| `x` | float | 是 | 横坐标百分比（点击位置） |
| `y` | float | 是 | 纵坐标百分比（点击位置） |
| `text` | string | 是 | 要输入的文本 |

## 常见问题

1. **文本未输入到正确位置**：确认坐标指向的是可输入区域，`desktop_screenshot` 验证。

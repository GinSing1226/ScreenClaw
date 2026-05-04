---
name: input_text
description: 向输入框输入文本。传 x/y 时会先点击坐标位置再输入，无需分步 click。不适用：只需点击用 click，需要按键用 press_key。
---

# input_text - 输入文本

## 快速决策

- 有输入框坐标时，直接传 `x/y/text`，不要先 click 再 input_text。
- 普通文本优先 `background`。
- 换行、emoji、中文输入法候选面板或粘贴类输入异常时，阅读 `delegated.md` 或改用 `hijack/delegated`。
- 输入后截图验证文本是否真的出现。

## 脚本调用

普通输入：

```bash
python scripts/screenclaw.py input_text api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} x=50 y=50 text="Hello World" action_method=background
```

换行文本：

```bash
python scripts/screenclaw.py input_text api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} x=50 y=50 "text=第一行\n第二行" action_method=hijack
```

batch 中输入：

```bash
python scripts/screenclaw.py batch api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} step.0.action=input_text step.0.params.x=50 step.0.params.y=50 step.0.params.text="hello" step.1.action=wait step.1.params.duration_ms=300 step.2.action=screenshot step.2.params.coordinate_type=no
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `x` | float | 否 | 输入位置横坐标，传则先点击 |
| `y` | float | 否 | 输入位置纵坐标，传则先点击 |
| `text` | string | 是 | 输入文本，`\n` 表示换行 |
| `newline_key` | string | 否 | background 换行键映射 |
| `action_method` | string | 否 | `background` 优先；必要时 `hijack` |

## 常见问题

1. **API 成功但没输入**：换窗口、传 `x/y` 激活输入框、截图验证焦点。
2. **换行不成功**：background 可能无法处理，改 `hijack` 或托管。
3. **emoji/中文候选异常**：优先考虑托管模式。
4. **不支持粘贴的输入框**：用 batch + `press_key` 逐字键入，字符间加短 wait。

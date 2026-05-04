---
name: delegated
description: 进入/退出/查询托管模式，让 AI 获得会话级物理控制权。进入需要用户确认，不能绕过。
---

# delegated - 托管模式

## 快速决策

- 只有用户主动要求、游戏实时操控、中文输入法候选面板、多窗口连续物理控制等场景才进入托管。
- 后台无感操作优先 `background`。
- 偶发物理操作优先 `hijack`。
- 托管模式任务结束后必须退出。
- 进入托管会弹窗，需要用户主动确认。

## 脚本调用

进入托管：

```bash
python scripts/screenclaw.py delegated api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} action=enter
```

退出托管：

```bash
python scripts/screenclaw.py delegated api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} action=exit
```

查询状态：

```bash
python scripts/screenclaw.py delegated api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} action=status
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `action` | string | 是 | `enter` / `exit` / `status` |

`delegated` 不需要 `window_id` 和 `main_window_id`。

## 操作模式对比

| 维度 | background | hijack | delegated |
|------|------------|--------|-----------|
| 输入方式 | 消息注入 | 物理输入 | 物理输入 |
| 确认 | 无 | 每次确认 | 进入时一次确认 |
| 状态恢复 | 不影响用户焦点 | 操作后恢复 | 不恢复 |
| 作用域 | 单次请求 | 单次请求 | 会话级 |

## 退出方式

1. 调用 `action=exit`。
2. 通知用户按设置面板中的退出快捷键。
3. 通知用户使用托盘菜单退出托管。

## 常见问题

1. **进入失败**：用户是否确认弹窗，是否超时。
2. **操作仍需确认**：调用 `action=status` 确认托管是否激活。
3. **任务结束**：必须调用 `action=exit`。

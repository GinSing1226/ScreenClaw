---
name: health
description: 验证 ScreenClaw 服务是否可连接，是所有操作前的第一步检查。也会返回当前时间。
---

# health - 健康检查

## 快速决策

- 每次开始使用 ScreenClaw 前先调用。
- 服务不可达、Token 不确定、需要生成 session_id 时间戳时调用。
- `health` 不需要 `window_id` 和 `main_window_id`。

## 脚本调用

```bash
python scripts/screenclaw.py health api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id}
```

## 响应字段

| 字段 | 说明 |
|------|------|
| `data.server_time` | 服务器当前时间，可用于生成 session_id |

## 常见问题

1. **服务不可达**：检查 ScreenClaw 是否启动、地址端口是否正确、网络是否通。
2. **认证失败**：检查 token 是否来自监控面板。

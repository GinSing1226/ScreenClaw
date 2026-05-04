---
name: get_window_list
description: 获取系统可见窗口列表，找到目标窗口的 window_id。适用：不知道窗口 ID、需要区分主窗口和子窗口、操作失败后怀疑窗口选错。
---

# get_window_list - 获取窗口列表

## 快速决策

- 新任务开始时调用。
- 操作失败且截图不像目标窗口时重新调用。
- 找不到窗口时先换 keyword，再不传 keyword 获取更多候选。
- `get_window_list` 不需要 `window_id` 和 `main_window_id`。

## 脚本调用

按关键词查找：

```bash
python scripts/screenclaw.py get_window_list api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} keyword=notepad include_children=true children_filter=titled
```

获取更多子窗口：

```bash
python scripts/screenclaw.py get_window_list api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} keyword=微信 include_children=true children_filter=all
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ai_app_type` | string | 是 | AI 应用类型 |
| `session_id` | string | 是 | 会话唯一标识 |
| `keyword` | string | 否 | 模糊搜索窗口标题或进程名 |
| `include_children` | bool | 建议 true | 是否返回子窗口 |
| `children_filter` | string | 否 | `titled` 仅有标题子窗口；`all` 全部子窗口 |

## 响应字段

| 字段 | 说明 |
|------|------|
| `window_id` | 窗口句柄，后续操作唯一标识 |
| `process_id` | 进程 ID |
| `process_name` | 进程名称 |
| `window_title` | 窗口标题 |
| `child_windows` | 子窗口列表 |

## 常见问题

1. **找不到目标窗口**：尝试中英文关键词、进程名，或不传 keyword。
2. **窗口太多**：先用 `children_filter=titled`，需要细查时再用 `all`。
3. **操作无效**：对主窗口和候选子窗口截图，建立候选窗口名单后逐个验证。

---
name: get_window_list
description: 获取系统可见窗口列表，找到目标窗口的window_id。适用：需要操作某个窗口但不知道window_id、查找特定应用的窗口、区分主窗口和子窗口。不适用：已知window_id，无需查找。
---

# get_window_list - 获取窗口列表

## 请求

**方法**：POST `/api/get_window_list`

**请求头**：
```
Authorization: Bearer {token}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `ai_app_type` | string | 是 | - | AI应用类型 |
| `session_id` | string | 是 | - | 会话唯一标识 |
| `keyword` | string | 否 | "" | 模糊搜索窗口标题或进程名 |
| `include_children` | bool | 强烈建议true | false | 是否返回子窗口 |
| `children_filter` | string | 否 | "titled" | 子窗口过滤：all/titled（titled=仅返回有标题的子窗口，减少约70%数据量） |

**注意**：`get_window_list` 不需要 `main_window_id` 参数。

### 响应字段

| 字段 | 说明 |
|------|------|
| `window_id` | 窗口句柄，后续操作的唯一标识 |
| `process_id` | 进程ID |
| `process_name` | 进程名称（.exe） |
| `window_title` | 窗口标题 |
| `child_windows` | 子窗口列表（仅 include_children=true 时返回） |

### 请求示例

```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "keyword": "notepad",
  "include_children": true,
  "children_filter": "titled"
}
```

## 常见问题

### 遇到问题时的排查顺序
1. **找不到目标窗口** → 调整keyword、检查窗口是否可见
2. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **keyword**：使用应用名称或进程名模糊搜索，中英文都可以试试。找不到就不要传关键词
- **children_filter="titled"**：只返回有标题的子窗口，减少数据量，推荐使用
- **窗口选择流程**（新进程或更换进程时）：
  1. 对主窗口和所有子窗口截图
  2. 识别哪些窗口可能包含目标元素
  3. 建立候选窗口名单，按可能性排序
  4. 后续操作失败时，按名单依次切换

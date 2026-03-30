---
name: get_window_list
description: 获取系统可见窗口列表，找到目标窗口的window_id（后续操作必需）
---

# get_window_list - 获取窗口列表

## 使用目的
获取系统中所有可见窗口（或指定关键词的窗口），找到目标窗口的window_id，这是后续所有操作（截图、点击、输入等）的必需参数。

## 什么时候用
- 需要操作某个窗口，但不知道它的window_id
- 需要查找特定应用的窗口
- 需要区分主窗口和子窗口

## 什么时候不用
- 已知window_id，无需查找

---

## 请求

**方法**：POST
**路径**：`/api/get_window_list`
**请求头**：
```
Authorization: Bearer {token}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 | 从哪里获取 |
|------|------|------|--------|------|----------|
| `ai_app_type` | string | 是 | - | AI应用类型 | 判断当前AI是什么应用，就用什么值 |
| `session_id` | string | 是 | - | 会话唯一标识 | 获取当前会话唯一标识，获取不到则随机生成 |
| `keyword` | string | 否 | "" | 模糊搜索窗口标题或进程名 | 用户描述的应用名称 |
| `include_children` | bool | **强烈建议true** | false | 是否返回子窗口。**建议始终设为true**， 大部分操作需要子窗口才能响应 |
| `children_filter` | string | 否 | "titled" | 子窗口过滤策略：all/titled | titled=仅返回有标题的子窗口 |

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

---

## 响应

### 成功响应
```json
{
  "success": true,
  "data": {
    "windows": [
      {
        "process_id": 12345,
        "process_name": "notepad.exe",
        "window_id": 1001,
        "window_title": "记事本",
        "child_windows": [
          {
            "window_id": 1002,
            "window_title": "编辑"
          }
        ]
      }
    ]
  }
}
```

### 字段说明
- `window_id`：窗口句柄，后续操作的唯一标识
- `process_id`：进程ID，用于标识进程
- `process_name`：进程名称（.exe）
- `window_title`：窗口标题
- `child_windows`：子窗口列表（仅当include_children=true时返回）

---

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `AUTH_FAILED` | Token不正确 | 检查config.json中的token配置 |

---

## 使用技巧

### 查找特定应用窗口
```json
{
  "keyword": "微信",
  "include_children": false
}
```

### 获取所有窗口（包括子窗口）
```json
{
  "include_children": true,
  "children_filter": "titled"
}
```

**注意**：`children_filter="titled"` 只返回有标题的子窗口，减少约70%的数据量，推荐使用。

---

## 主窗口 vs 子窗口

**主窗口**：应用的主界面窗口
**子窗口**：主窗口内的独立窗口（如输入框、内容区域）

**选择策略**：
- 点击类操作：主窗口通常可工作
- 输入/按键/运动类：优先选择子窗口
- 不确定时：先截图查看主窗口和子窗口的内容分布

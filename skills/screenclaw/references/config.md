---
name: screenclaw-config
description: ScreenClaw连接配置说明
---

# ScreenClaw 连接配置

## 请求地址

```
http://{host}:{port}
```

- 默认：`http://localhost:12261`
- 由用户提供

## 请求Token

```
Bearer {token}
```

- 由用户提供

## 会话ID (session_id) - 重要！

**规则**：**整个会话过程中必须使用同一个 session_id**

### 为什么重要
- 相同 session_id 的截图会保存在同一个文件夹
- 便于追踪和查看历史截图
- 避免图片分散存储

### 如何使用
1. **会话开始时**：生成一个唯一的 session_id（如 "claude-code-20260328-001"）
2. **整个会话期间**：所有 API 调用都使用这个 session_id
3. **会话结束时**：停止使用该 session_id

### 示例
```python
# 会话开始
session_id = "claude-code-20260328-001"

# 所有操作都用这个
api_call(session_id=session_id, ...)  # 第一次
api_call(session_id=session_id, ...)  # 第二次，相同
api_call(session_id=session_id, ...)  # 第N次，仍然相同

# ❌ 错误做法：每次生成新的
api_call(session_id=f"session-{random()}")  # 不要这样
```

### 获取或生成会话id
1. 从你的上下文里找到会话唯一标识。
2. 如果没有，可以按照规则生成唯一：应用名-日期-随机4位数


### 常见错误
| 错误做法 | 后果 |
|---------|------|
| 每次调用生成新的 session_id | 图片分散在多个文件夹 |
| 使用时间戳作为 session_id | 每次都不同，失去追踪意义 |
| 不传 session_id | API 会报错 |

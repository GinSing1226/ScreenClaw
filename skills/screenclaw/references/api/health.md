---
name: health
description: 验证ScreenClaw服务是否可连接，是所有操作前的第一步检查
---

# health - 健康检查

## 使用前必读

### 使用目的和效果
验证ScreenClaw服务是否正常运行。成功返回服务版本和运行时间，失败则后续操作无法执行。

### 适用场景
- 执行任何操作前的第一步检查
- 怀疑服务停止时
- 排查连接问题时

### 不适用场景
- 已确认服务正常运行，连续执行多个操作时

## 请求

**方法**：GET `/api/health`

**请求头**：
```
Authorization: Bearer {token}
```

GET请求不需要请求体。

### 请求示例

```bash
# curl示例
curl -X GET -H "Authorization: Bearer your-token" http://localhost:12261/api/health
```

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `AUTH_FAILED` | Token不正确 | 检查token配置 |

## 常见问题

### 遇到问题时的排查顺序
1. **服务不可达** → 检查ScreenClaw是否启动、网络是否通畅、地址和端口是否正确
2. **认证失败** → 检查Token是否正确

### 操作技巧
- 操作前先调用health确认服务可用，避免后续操作浪费时间

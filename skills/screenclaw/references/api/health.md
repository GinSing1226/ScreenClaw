---
name: health
description: 验证ScreenClaw服务是否可连接，是所有操作前的第一步检查。也会返回当前时间。
---

# health - 健康检查

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

## 响应

### 成功响应

```json
{
  "success": true,
  "message": "Service OK",
  "data": {
    "server_time": "2026-04-22 14:30:05"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `server_time` | string | 服务器当前时间 (yyyy-mm-dd HH:mm:ss) |

## 常见问题

### 遇到问题时的排查顺序
1. **服务不可达** → 检查ScreenClaw是否启动、网络是否通畅、地址和端口是否正确
2. **认证失败** → 检查Token是否正确
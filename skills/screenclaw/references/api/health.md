---
name: health
description: 验证ScreenClaw服务是否可连接，是所有操作前的第一步检查
---

# health - 健康检查

## 使用目的
验证ScreenClaw服务是否正常运行，确保后续操作可以执行。

## 什么时候用
- 执行任何操作前的第一步检查
- 怀疑服务可能停止时
- 排查连接问题时

## 什么时候不用
- 已确认服务正常运行，连续执行多个操作时

---

## 请求

**方法**：GET
**路径**：`/api/health`
**请求头**：
```
Authorization: Bearer {token}
```

**注意**：GET请求不需要请求体

---

## 响应

### 成功响应
```json
{
  "success": true,
  "message": "服务正常",
  "data": {
    "version": "1.0.0",
    "uptime_seconds": 3600
  }
}
```

### 失败响应
```json
{
  "success": false,
  "error_code": "AUTH_FAILED",
  "message": "认证失败"
}
```

---

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `AUTH_FAILED` | Token不正确 | 检查config.json中的token配置 |

---

## 使用示例

```bash
curl -X GET \
  -H "Authorization: Bearer your-token" \
  http://localhost:12261/api/health
```

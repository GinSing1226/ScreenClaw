---
name: delegated
description: 进入/退出/查询托管模式，AI获得电脑物理控制权
---

# delegated - 托管模式

## 使用前必读

### 使用目的和效果
托管模式是会话级控制模式。进入后，AI获得整台电脑的物理操作控制权，所有操作使用物理输入（鼠标/键盘），不恢复窗口焦点和鼠标位置，无需逐次确认。

### 三种操作模式对比

| 维度 | background | hijack | delegated（托管） |
|------|-----------|--------|----------------|
| 输入方式 | PostMessage（消息注入） | 物理输入 | 物理输入（同hijack） |
| 确认弹窗 | 无 | 每次操作需确认 | 进入时一次确认 |
| 状态恢复 | 无需恢复 | 每次操作后恢复焦点和鼠标 | 不恢复 |
| 谁控制焦点 | 不影响焦点 | 操作完还给用户 | AI完全控制 |
| 作用域 | 单次请求 | 单次请求 | 会话级，持续到退出 |

### 适用场景
- **游戏实时操控** — 连续物理输入，不能每次操作后恢复焦点
- **中文输入法（IME）** — 输入拼音→候选面板→选字，hijack恢复焦点会关闭候选面板
- **多窗口连续操控** — 在不同窗口间交替操作，不希望焦点被切走
- **用户主动要求** — 用户明确说"进入托管模式"、"让我电脑完全交给你"等

### 不适用场景
- 后台无感操作 → 使用 background 模式
- 偶尔需要物理操作 → 使用 hijack 模式
- 未获得用户明确同意 → 禁止进入托管

## 请求

**方法**：POST `/api/delegated`

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
| `action` | string | 是 | - | `enter`：进入托管 / `exit`：退出托管 / `status`：查询当前状态 |

**注意**：此接口不需要 `window_id` 和 `main_window_id`。

### action 参数说明

| action | 说明 | 确认机制 |
|--------|------|----------|
| `enter` | 进入托管模式 | 弹窗确认（复用hijack确认机制），用户拒绝则不进入 |
| `exit` | 退出托管模式 | 无需确认 |
| `status` | 查询当前托管状态 | 无需确认 |

### 退出方式

托管模式可通过以下三种方式退出：
1. **API调用** — `action=exit`
2. **快捷键** — 通知用户使用快捷键退出。
3. **托盘菜单** — 通知用户使用右键托盘图标 → 退出托管

### 请求示例

**进入托管**：
```bash
python scripts/api_call.py http://192.168.10.190:12261 TOKEN delegated ai_app_type=claude_code session_id=test_20260404_120000 action=enter
```

**退出托管**：
```bash
python scripts/api_call.py http://192.168.10.190:12261 TOKEN delegated ai_app_type=claude_code session_id=test_20260404_120000 action=exit
```

**查询状态**：
```bash
python scripts/api_call.py http://192.168.10.190:12261 TOKEN delegated ai_app_type=claude_code session_id=test_20260404_120000 action=status
```

### 响应示例

**进入成功**：
```json
{
  "success": true,
  "message": "托管模式已激活",
  "data": {
    "delegated_active": true
  }
}
```

**用户拒绝进入**：
```json
{
  "success": false,
  "message": "用户拒绝进入托管模式"
}
```

**退出成功**：
```json
{
  "success": true,
  "message": "托管模式已退出",
  "data": {
    "delegated_active": false
  }
}
```

**查询状态**：
```json
{
  "success": true,
  "message": "托管模式状态查询",
  "data": {
    "delegated_active": false
  }
}
```

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `USER_DENIED` | 用户拒绝进入托管 | 确认用户意愿后重试 |
| `CONFIRM_TIMEOUT` | 确认弹窗超时（30秒） | 提醒用户点击确认，重新调用 |
| `INTERNAL_ERROR` | 内部错误 | 查看服务日志 |

## 常见问题

### 遇到问题时的排查顺序
1. **进入失败** → 用户是否点击了确认弹窗？是否超时？
2. **操作仍需确认** → 用 `action=status` 确认托管是否已激活


### 安全提示
- 托管模式下AI完全控制电脑（鼠标、键盘、焦点），服务端会自动必与用户确认
- 进入需要用户在弹窗中主动点击确认，不能绕过
- 任务结束后记得退出托管模式

### 边界情况

| 场景 | 处理方式 |
|------|----------|
| 已在托管模式再次调用enter | 返回成功，不做重复确认 |
| 未在托管模式调用exit | 返回成功，状态不变 |
| 确认弹窗超时（30秒） | 视为拒绝，不进入托管 |
| 应用启动 | 自动将托管状态重置为已退出 |

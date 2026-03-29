---
name: swipe
description: 触摸式滑动（翻页、切换标签、拖拽）
---

# swipe - 滑动

## 使用目的
从起始坐标滑动到终止坐标，用于：
- 翻页（向上/向下滑动）
- 切换标签（向左/向右滑动）
- 拖拽操作

## 什么时候用
- 需要触摸式滑动（如移动应用模拟器）
- 需要翻页或切换标签
- 需要拖拽元素

## 什么时候不用
- 鼠标滚轮滚动（使用scroll）
- 简单点击（使用click）

---

## 请求

**方法**：POST
**路径**：`/api/swipe`

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 | 从哪里获取 |
|------|------|------|--------|------|----------|
| `ai_app_type` | string | 是 | - | AI应用类型 | 判断当前AI是什么应用，就用什么值 |
| `session_id` | string | 是 | - | 会话唯一标识 | 获取当前会话唯一标识，获取不到则随机生成 |
| `window_id` | int | 是 | - | 目标窗口句柄 | 从get_window_list获取 |
| `main_window_id` | int | 否 | - | 主窗口ID（用于恢复窗口） | 从get_window_list获取 |
| `start_x` | float | 是 | - | 起始横坐标（从截图的网格标记中直接读出的数字） | 从截图分析得出 |
| `start_y` | float | 是 | - | 起始纵坐标（从截图的网格标记中直接读出的数字） | 从截图分析得出 |
| `end_x` | float | 是 | - | 结束横坐标（从截图的网格标记中直接读出的数字） | 从截图分析得出 |
| `end_y` | float | 是 | - | 结束纵坐标（从截图的网格标记中直接读出的数字） | 从截图分析得出 |
| `action_method` | string | 否 | "background" | 操作方式：background/hijack | 优先background |

### 请求示例

#### 向上翻页
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "start_x": 50.0,
  "start_y": 80.0,
  "end_x": 50.0,
  "end_y": 20.0,
  "action_method": "background"
}
```

#### 向右切换标签
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "start_x": 20.0,
  "start_y": 50.0,
  "end_x": 80.0,
  "end_y": 50.0,
  "action_method": "background"
}
```

---

## 响应

### 成功响应
```json
{
  "success": true,
  "message": "指令已发送，可截图验证结果"
}
```

---

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `OPERATION_FAILED` | 操作失败 | 检查坐标，尝试hijack模式 |

---

## 常用滑动方向

| 方向 | start_y | end_y | 说明 |
|------|---------|-------|------|
| 向上翻页 | 80 | 20 | 从下往上滑 |
| 向下翻页 | 20 | 80 | 从上往下滑 |
| 向左翻页 | 80 | 20 | 从右往左滑 |
| 向右翻页 | 20 | 80 | 从左往右滑 |

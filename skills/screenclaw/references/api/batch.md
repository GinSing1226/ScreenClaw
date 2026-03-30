---
name: batch
description: 执行多步骤的固定流程（如登录、导航）、减少网络请求次数
---

# batch - 批量执行

## 使用目的
批量执行多条指令，按顺序执行，用于：
- 执行多步骤的固定流程（如登录、导航）
- 减少网络请求次数，提高效率
- 执行已沉淀的场景模板

## 什么时候用
- 需要执行多个连续操作
- 操作步骤固定，无需中间决策
- 执行已沉淀的场景模板

## 什么时候不用
- 单步操作
- 需要根据前一步结果动态决策

---

## 请求

**方法**：POST
**路径**：`/api/batch`

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 | 从哪里获取 |
|------|------|------|--------|------|----------|
| `ai_app_type` | string | 是 | - | AI应用类型 | 判断当前AI是什么应用，就用什么值 |
| `session_id` | string | 是 | - | 会话唯一标识 | 获取当前会话唯一标识，获取不到则随机生成 |
| `window_id` | int | 是 | - | 目标窗口句柄 | 从get_window_list获取 |
| `main_window_id` | int | 建议 | - | 主窗口ID（用于激活最小化窗口） | 从get_window_list获取 |
| `instructions` | array | 是 | - | 指令列表 | 根据操作流程设置 |

### instructions 结构

每条指令包含：
- `action`：指令类型（click/input_text/press_key/wait等）
- `params`：指令参数（与单独调用该API时的参数相同）

### 请求示例
#### 包含截图的操作流程
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "instructions": [
    { "action": "screenshot", "params": { "coordinate_type": "grid" } },
    { "action": "click", "params": { "x": 50, "y": 35 } },
    { "action": "wait", "params": { "duration_ms": 300 } },
    { "action": "screenshot", "params": { "coordinate_type": "grid" } }
  ]
}
```

**注意**：batch中包含screenshot时，截图数据（image_path和image_base64）会在响应的results数组中对应位置返回。

---

## 响应

### 成功响应
```json
{
  "success": true,
  "data": {
    "executed_count": 3,
    "results": [
      { "success": true, "message": "指令已发送" },
      { "success": true, "message": "等待完成" },
      { "success": true, "message": "指令已发送，可截图验证结果" }
    ]
  }
}
```

**说明**：只有最后一步成功时才会提示"可截图验证结果"，中间步骤只返回"指令已发送"。

### 失败响应
```json
{
  "success": false,
  "data": {
    "executed_count": 2,
    "results": [
      { "success": true, "message": "指令已发送" },
      { "success": false, "message": "窗口不存在", "error_code": "WINDOW_NOT_FOUND" }
    ]
  }
}
```

**注意**：batch执行失败时会中断，已执行的指令在`results`中可以查看。

---

## 响应格式

### 包含截图的响应

**本地请求**（localhost, 127.0.0.1, ::1）：
```json
{
  "success": true,
  "data": {
    "executed_count": 4,
    "results": [
      { "success": true, "message": "指令已发送" },
      { "success": true, "message": "等待完成" },
      {
        "success": true,
        "message": "截图完成",
        "data": {
          "image_path": "D:\\screenClaw\\data\\session-123\\screenshot_20250329_143025.png"
        }
      },
      { "success": true, "message": "指令已发送，可截图验证结果" }
    ]
  }
}
```

**远程请求**（局域网IP）：
```json
{
  "success": true,
  "data": {
    "executed_count": 4,
    "results": [
      { "success": true, "message": "指令已发送" },
      { "success": true, "message": "等待完成" },
      {
        "success": true,
        "message": "截图完成",
        "data": {
          "image_path": "D:\\screenClaw\\data\\session-123\\screenshot_20250329_143025.png",
          "image_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
        }
      },
      { "success": true, "message": "指令已发送，可截图验证结果" }
    ]
  }
}
```

**区别**：
- 本地请求：截图数据只返回 `image_path`（图片已在服务端保存）
- 远程请求：截图数据返回 `image_path` + `image_base64`（客户端需自行解码保存）

---

## 响应处理

### 本地请求（localhost, 127.0.0.1, ::1）

**直接使用返回的 `image_path`，无需脚本**

```python
results = response.json()["data"]["results"]
for item in results:
    if item.get("data", {}).get("image_path"):
        image_path = item["data"]["image_path"]
        # 直接读取图片
        with open(image_path, "rb") as f:
            image_data = f.read()
```

### 远程请求（局域网IP）

**必须使用脚本处理 base64**

```bash
# Python（推荐，跨平台）
python scripts/batch_results_processor.py <api_url> <token> <json_response_file>

# PowerShell（Windows）
.\scripts\batch_results_processor.ps1 <api_url> <token> <json_response_file>
```

脚本会自动：
1. 遍历 `results` 数组找到截图数据
2. 解码 `image_base64`
3. 保存到正确位置
4. 返回图片路径列表

### ❌ 禁止以下做法

```python
# ❌ 错误：本地请求也调用脚本（多余）
process_batch_results(...)  # 不需要

# ❌ 错误：远程请求自己写保存逻辑（路径会混乱）
if "image_base64" in item["data"]:
    with open("screenshot.png", "wb") as f:
        f.write(base64.b64decode(item["data"]["image_base64"]))
```

### 调用方式（Python）

```python
from scripts.batch_results_processor import process_batch_results

results = response.json()["data"]["results"]
output = process_batch_results(
    results,
    api_url="http://localhost:12261/api/batch"
)
```

### 调用方式（PowerShell）

```powershell
# 导入脚本
. .\scripts\batch_results_processor.ps1

# 处理结果
$output = Get-BatchResultsOutput -Results $results -ApiUrl "http://localhost:12261/api/batch"
```

### ❌ 禁止以下做法

```python
# ❌ 错误：自己写保存逻辑
for item in results:
    if item.get("data", {}).get("image_base64"):
        # 不要这样写
        with open("screenshot.png", "wb") as f:
            f.write(base64.b64decode(item["data"]["image_base64"]))
```

---

## 特殊说明

### 截图指令
batch中可以包含截图指令（screenshot），截图数据（路径和base64）会在响应中返回。

### 非阻塞持续时间
指令内部的持续时间参数是**非阻塞**的：
- 例如：`press_key` 的 `duration_ms=10000`（按住ctrl 10秒）
- 系统会立即执行下一条指令，不会等待10秒
- 但ctrl按键仍然会持续10秒
- 用途：如按住ctrl多选文件时，可以同时执行点击多个文件的操作

### 阻塞式等待
如果需要阻塞式等待（暂停执行下一条指令），使用 `wait` 指令。

---

## 错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| `WINDOW_NOT_FOUND` | 窗口不存在 | 重新获取窗口列表 |
| `USER_DENIED` | 用户拒绝操作（hijack模式） | 用户取消了确认弹窗 |
| `OPERATION_FAILED` | 操作失败 | 检查指令参数 |

---

## 支持的指令类型

| 指令 | 说明 |
|------|------|
| `click` | 点击 |
| `long_press` | 长按 |
| `swipe` | 滑动 |
| `scroll` | 滚动 |
| `right_click` | 右键点击 |
| `hover` | 鼠标悬浮（触发隐藏UI或tooltip） |
| `input_text` | 输入文本 |
| `press_key` | 按键 |
| `wait` | 等待 |
| `screenshot` | 截图（截图数据会在响应的results中返回） |

---

## 使用技巧

1. **操作之间添加wait**：确保UI稳定后再执行下一步
2. **使用场景模板**：已沉淀的场景模板可以直接转换为batch格式
3. **失败处理**：batch失败时会中断，需要检查results中的失败原因
4. **hijack确认**：batch中包含hijack操作时，会依次弹出确认窗口

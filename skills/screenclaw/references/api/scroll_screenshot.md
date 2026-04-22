---
name: scroll_screenshot
description: >-
  对窗口执行自动滚动、连续截图、智能拼接，生成长图。
  适用：长页面截图（文章、论坛帖子、博客）、长文档截图（PDF、Word）、聊天记录截图（微信、QQ）、数据列表截图、日志文件截图。
  不适用：需要定位元素的截图（不支持网格坐标）、动态加载内容（内容无限滚动）、非垂直滚动（横向/斜向）、分页内容（需要点击翻页）。
  约束：固定hijack操作模式（不支持background），不支持绘制网格坐标。
---

# scroll_screenshot - 滚动长截图

## 请求

**方法**：POST `/api/scroll_screenshot`

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
| `window_id` | int | 是 | - | 目标窗口句柄，可以是主窗口、子窗口id |
| `main_window_id` | int | 是 | - | 主窗口ID（用于激活最小化窗口） |
| `x` | float | 否 | 50.0 | 滚动X坐标(0.0-100.0)，在哪里滚动页面，通常不能有遮挡 |
| `y` | float | 否 | 50.0 | 滚动Y坐标(0.0-100.0) |
| `max_scrolls` | int | 否 | 服务端配置 | 单次滚动截图的最大滚动次数。值越大能截取更长的页面，但总耗时更长。建议 5-50 |
| `scroll_percent` | float | 否 | 服务端配置 | 初始滚动幅度（0.1-0.95）。不同应用的滚动幅度不同，100%不一定代表刚好下一屏。系统会根据页面自动动态调整此幅度以获得最佳重叠，接口会返回实际使用的幅度。值越大每次滚得越多，但可能漏内容 |
| `scroll_wait` | float | 否 | 服务端配置 | 每次滚动后的默认等待时间（秒）。值越大等待越充分，适合慢速页面。建议 0.5-2 |
| `max_adjust_retries` | int | 否 | 服务端配置 | 自适应滚动最大调整次数。系统会自动调整滚动幅度以达到目标重叠，此参数控制最多调整几次。值越大越耐心，但耗时更长。建议 3-5 |
| `target_overlap_min` | float | 否 | 服务端配置 | 目标重叠下限（0.1-0.5）。相邻图片重叠量的理想范围下限。值越大确保有足够重叠可拼接，但调整次数可能增多 |
| `target_overlap_max` | float | 否 | 服务端配置 | 目标重叠上限（0.2-0.6）。相邻图片重叠量的理想范围上限。值越小减少截图数量，但重叠太少可能拼接失败 |
| `stop_threshold` | float | 否 | 服务端配置 | 停止阈值（1~0.0001，即 100%~0.01%）。内容变化率低于此值时停止滚动，表示已到底部。值越大越容易判定到底，可能提前停止 |

> **注意**：带"服务端配置"的参数，不传时使用服务端 config.json 中的默认值。大多数场景只传 `window_id`、`main_window_id` 即可。

### 请求示例

**基础用法**（大多数场景足够）：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001
}
```

**自定义参数**：
```json
{
  "ai_app_type": "claude_code",
  "session_id": "session-123",
  "window_id": 1001,
  "main_window_id": 1001,
  "max_scrolls": 50,
  "scroll_percent": 0.80,
  "scroll_wait": 1.5
}
```

### 响应

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.image_path` | string | 拼接后图片本地路径（本地请求） |
| `data.image_base64` | string | 拼接后图片base64（远程请求） |
| `data.scroll_count` | int | 实际截图数量 |
| `data.actual_scroll_percent` | float | 最终使用的滚动幅度 |

## 常见问题

### 遇到问题时的排查顺序
1. **图片拼接有错位** → 增大 `scroll_wait`（如从1.0改为1.5），页面可能还没加载完就截图了
2. **还没到底就停止了** → 减小 `stop_threshold`（如从0.0001改为0.00005）
3. **到底了还继续滚动** → 增大 `stop_threshold`（如从0.0001改为0.0002）
4. **有些内容被截断** → 减小 `scroll_percent`（如从0.85改为0.70）
5. **API调用失败** → 对照请求参数检查参数格式

### 操作技巧
- **x / y**：窗口有分栏布局时，设置x指向目标分栏（如左侧分栏设x=25）
- **默认值机制**：不传的参数由服务端 config.json 填充，大多数场景无需手动指定

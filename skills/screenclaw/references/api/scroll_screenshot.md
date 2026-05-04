---
name: scroll_screenshot
description: 对窗口执行自动滚动、连续截图、智能拼接，生成长图。适用：文章、文档、聊天记录、列表、日志。不适用：需要定位元素坐标的截图。
---

# scroll_screenshot - 滚动长截图

## 快速决策

- 用于整体理解长页面，不用于精确坐标定位。
- 不绘制网格坐标。
- 固定使用 hijack 类物理滚动，不支持 background。
- 大多数场景只传 `window_id/main_window_id`。
- `scroll_screenshot` 不支持 batch。

## 脚本调用

基础长截图：

```bash
python scripts/screenclaw.py scroll_screenshot api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id}
```

指定滚动区域和参数：

```bash
python scripts/screenclaw.py scroll_screenshot api_url={api_url} token={token} ai_app_type={ai_app_type} session_id={session_id} window_id={window_id} main_window_id={main_window_id} x=50 y=50 max_scrolls=20 scroll_percent=0.8 scroll_wait=1.5
```

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `window_id` | int | 是 | 目标窗口句柄 |
| `main_window_id` | int | 是 | 主窗口 ID |
| `x` | float | 否 | 滚动位置横坐标，默认 50 |
| `y` | float | 否 | 滚动位置纵坐标，默认 50 |
| `max_scrolls` | int | 否 | 最大滚动次数 |
| `scroll_percent` | float | 否 | 初始滚动幅度 0.1-0.95 |
| `scroll_wait` | float | 否 | 每次滚动后的等待秒数 |
| `max_adjust_retries` | int | 否 | 自适应滚动最大调整次数 |
| `target_overlap_min` | float | 否 | 目标重叠下限 |
| `target_overlap_max` | float | 否 | 目标重叠上限 |
| `stop_threshold` | float | 否 | 停止阈值 |

不传的参数使用服务端配置。

## 响应字段

| 字段 | 说明 |
|------|------|
| `data.image_path` | 本地长截图路径 |
| `data.image_base64` | 远程调用时的 base64，脚本会自动落盘 |
| `data.requested_params` | 请求参数摘要 |
| `data.effective_params` | 本次实际生效滚动参数 |
| `data.effective_scroll` | 实际生效滚动参数 |
| `data.scroll_count` | 实际截图数量 |
| `data.actual_scroll_percent` | 最终使用的滚动幅度 |

统一脚本输出图片路径和 message 后，会继续输出去掉 base64/null 的 `Data:` 摘要。

## 常见问题

1. **拼接错位**：增大 `scroll_wait`。
2. **没到底就停止**：减小 `stop_threshold`。
3. **到底还继续滚**：增大 `stop_threshold`。
4. **内容被截断**：减小 `scroll_percent`。
5. **多栏页面**：设置 `x/y` 指向目标分栏。

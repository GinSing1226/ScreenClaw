---
name: desktop_get_monitors_list
description: 枚举所有显示器，返回索引、名称、分辨率、是否主屏、坐标偏移。桌面级操作前调用以确定目标显示器。
---

# desktop_get_monitors_list - 显示器枚举

## 快速决策

- 桌面级操作前调用，确认可用的显示器及其索引。
- 单显示器环境可直接使用 `monitor_index=0`。
- 多显示器需根据目标位置选择对应索引。

## 脚本调用

```bash
python scripts/screenclaw.py desktop_get_monitors_list api_url={api_url} token={token}
```

## 响应数据

返回 `monitors` 数组，每个元素包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `index` | int | 显示器索引（从 0 开始） |
| `name` | string | 显示器名称 |
| `resolution` | string | 分辨率，如 "1920x1080" |
| `is_primary` | bool | 是否主显示器 |
| `left` | int | 在虚拟桌面中的 X 偏移 |
| `top` | int | 在虚拟桌面中的 Y 偏移 |
| `width` | int | 像素宽度 |
| `height` | int | 像素高度 |

## 常见问题

1. **显示器列表为空**：系统未检测到显示器，检查显示连接。
2. **多显示器坐标空间**：每个显示器有独立的百分比坐标空间 (0-100)，跨屏操作使用 `desktop_drag` 指定 `end_monitor_index`。

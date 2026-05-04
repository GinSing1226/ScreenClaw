---
name: screenclaw
version: 1.1.7
description:
  通过 screenclaw 获取带坐标网格的截图，读出图上的坐标数字，再调用点击、输入、按键等 API 控制软件，模拟人类视觉交互。

  当符合以下场景时使用此技能：
  - 需要视觉操作软件
  - 用户目标需要通过截图理解界面、读取元素坐标或验证 UI 状态
  - Playwright、CLI、应用专用 API 无法覆盖，例如隐藏按钮、游戏、验证码、任意普通桌面软件
  - 用户要求自动操作一个没有专用技能的软件
---

# screenclaw

## 核心规则

1. 坐标必须来自 ScreenClaw 截图上的 `XxY` 网格交叉点，不能用内部视觉坐标或凭感觉推测。
2. 每个会话固定一个 `session_id`，所有公开调用只使用 `scripts/screenclaw.py|ps1|sh`。
3. 调用 endpoint 前阅读 `references/api/{endpoint}.md`；参数错误或 API 报错时回到文档修正。
4. 首次动态坐标、高风险坐标、看不清目标或数字时，必须先裁剪放大或 marker 反验。
5. API 成功只代表指令已发送，不代表界面达成目标；操作后必须截图验证。
6. 收到 `SELF_CHECK_REQUIRED` 时，阅读并执行 `references/self_check.md` 的自检程序，让关键上下文重新装载，再用 `self_check` 总结执行内容后重试截图。

## 心智模型

1. 外部事实优先：截图、marker、API 返回、窗口列表是事实；你的直觉和预设结论必须服从这些事实。marker 不在目标上，就说明坐标错了。
2. 先证伪，再操作：候选坐标默认可能是错的。先用 crop 或 marker 找反例，确认标记点实际落在哪里，再操作。
3. 失败先回到截图：操作失败、结果不符合预期、连续微调无效时，先重新截图、裁剪、读文档和参数，不要继续猜坐标或重复点击。

## 固定工作循环

```text
理解目标 -> health -> config -> get_window_list -> screenshot -> 读坐标 -> marker 反验 -> 操作 -> screenshot 验证
```

### 1. 初始化

- 根据用户语言回复。
- 阅读 `references/config.md` 获取 `api_url`、`token`、`ai_app_type`、`session_id` 规则。
- 阅读 `scripts/README.md` 了解统一脚本入口和点号路径格式。
- 调用 `health` 确认服务可用。
- 搜索 `references/scenarios/` 是否有匹配模板。
- 复杂、多步、高风险任务先维护 2-5 步简短计划；简单单步任务不强制创建待办。

### 2. 获取目标窗口

- 调用 `get_window_list` 找主窗口和可能的子窗口。
- 新进程或窗口不确定时，对候选窗口截图，记录窗口内容和可用 `window_id/main_window_id`。
- 后续操作失败时，先检查是否选错窗口，再换操作模式。

### 3. 截图与读坐标

- 定位坐标使用 `screenshot coordinate_type=grid`。
- 分析内容或给用户看图可用 `coordinate_type=no`。
- 默认先依赖服务端自适应网格参数。
- 目标没有被交叉点覆盖时，阅读 `references/api/screenshot.md` 调整 `grid.density_x/y`。
- 数字或元素看不清时，使用 `crop_zoom_screenshot` 或调整数字参数。
- 首次动态坐标或高风险坐标，先用 `crop_zoom_screenshot` 看清局部，再用 `marker.0.x/y` 反向验证。
- marker 反验要先找图上的标记点实际落在哪里，描述那里有什么，再判断它是否等于目标；不要先假设候选坐标正确。

### 4. 操作与验证

- 操作模式优先 `background`。
- `background` 无效或必须物理输入时才考虑 `hijack`。
- 用户主动要求、游戏实时操作、中文输入法候选面板等持续物理输入场景，阅读 `references/api/delegated.md` 后进入托管。
- 探索阶段单步调用；流程稳定、需要瞬间观察 hover/菜单/操作结果时才用 `batch`。
- 每次操作后截图验证，验证不通过则回到截图和读坐标。
- 收到 `SELF_CHECK_REQUIRED` 时必须更新当前计划或下一步动作。

## 坐标概念

截图上的坐标格式为 `XxY`，例如 `50x35` 表示距左边界 50%、距上边界 35%。

`x` 是坐标分隔符，不是乘号。目标元素的有效坐标是覆盖到该元素的网格交叉点坐标。

## API 索引

> 执行API前先读对应文档 `references/api/{endpoint}.md`

| API | method | 适用场景 | 参考文档 |
|-----|------|-----------|----------|
| health | GET | 任务开始前检查服务 | `references/api/health.md` |
| get_window_list | POST | 找出需要被控制的目标窗口 | `references/api/get_window_list.md` |
| screenshot | POST | 带网格可定位坐标。不带网格可分析界面、留存记录。带标记点可预览坐标位置 | `references/api/screenshot.md` |
| crop_zoom_screenshot | POST | 裁剪任意截图并放大，看清细节（如坐标数字） | `references/api/crop_zoom_screenshot.md` |
| scroll_screenshot | POST | 滚动长截图，记录长页面、长内容，整体理解目标窗口 | `references/api/scroll_screenshot.md` |
| click | POST | 单击，触发按钮/进入页面 | `references/api/click.md` |
| long_press | POST | 长按，触发某些功能 | `references/api/long_press.md` |
| swipe | POST | 触摸式滑动，上下左右移动页面 | `references/api/swipe.md` |
| drag | POST | 拖拽元素，按住鼠标并移动 | `references/api/drag.md` |
| scroll | POST | 鼠标滚轮滚动，上下移动页面 | `references/api/scroll.md` |
| right_click | POST | 右键，打开上下文菜单 | `references/api/right_click.md` |
| hover | POST | 触发悬停效果，配合截图获取hover效果 | `references/api/hover.md` |
| mouse_move | POST | 鼠标移动，游戏视角控制，仅hijack/托管 | `references/api/mouse_move.md` |
| input_text | POST | 输入文本。带坐标会先单击再输入。不带坐标直接输入 | `references/api/input_text.md` |
| press_key | POST | 按键/组合键。带坐标会先单击再按键。不带坐标直接按键 | `references/api/press_key.md` |
| wait | POST | 等待UI动画/页面加载 | `references/api/wait.md` |
| batch | POST | 组合指令，执行连续步骤。多个单步的操作可组合执行，提高效率 | `references/api/batch.md` |
| delegated | POST | 用户主动要求进入/退出托管模式 | `references/api/delegated.md` |

## 脚本降级

降级路径：

```text
scripts/screenclaw.py -> scripts/screenclaw.ps1 -> scripts/screenclaw.sh -> curl
```

降级前先判断原因：

| 错误类型 | 处理方式 |
|----------|----------|
| 参数错误 | 修正参数，重跑同一脚本，不降级 |
| API 业务错误 | 阅读对应 API 文档和服务端 message，不降级 |
| Python 不存在等环境错误 | 降级到 PowerShell 或 shell |

## 参考文档

- `references/config.md` - 连接配置、`ai_app_type`、`session_id`
- `scripts/README.md` - 统一脚本入口和点号路径格式
- `references/self_check.md` - 长时程自检重载清单
- `references/api/*.md` - 各 API 参数和排错
- `references/scenarios/` - 场景模板和应用知识

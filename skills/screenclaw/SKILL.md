---
name: screenclaw
version: 1.0.0
description:
  通过HTTP API控制ScreenClaw实现桌面软件自动化操作。

  当符合以下场景时使用此技能：
  - 用户需要操作没有API的桌面Windows软件（如点击按钮、输入文字、滚动页面）
  - 需要截图并让AI分析界面元素位置
  - 需要程序化控制桌面应用程序
  - 用户提到"点击某个软件的按钮"、"在XX软件中输入"、"帮我操作XX软件"等操作
  任何涉及桌面软件GUI操作的请求，都应优先考虑使用此技能。
---

# ScreenClaw

## 读前须知
1. **待办清单：** 以待办清单跟进一切行为。任务开始即创建，每一步都记录在案，不跳过不遗漏。
2. **用户语言检查：** 基于用户输入语言（中文/英文），调整你的思考和输出语言，确保用户能理解你的输出。
3. **UTF-8读取文档：** 用UTF-8编码读取所有文档，确保中文内容正确显示。

## 执行顺序

1. **精读skill.md：** - 深入理解skill.md中的规则和方法论，慢下来思考内化，不急于执行，准确远比速度重要
2. **获取请求信息** — 阅读 `references/config.md` 获取API地址和Token；生成 session_id；阅读 `scripts/README.md`
3. **检索场景模板** — 搜索 `references/scenarios/` 下是否有匹配当前任务的模板，有则复用
4. **构建三角色以及任务待办** — 用 TodoWrite 创建待办清单（守则行→全局参数行→准备行→规划行→执行/评估交替→沉淀复盘），启动 Planner→Executor→Evaluator 循环
5. **调用脚本** — 截图用 `scripts/fetch_screenshot_cli.py`，batch用 `scripts/api_call_batch.ps1`，其他用 `scripts/api_call.py`；降级路径：py→ps1→sh→手动curl
6. **遇到问题** — 查阅下方"常见问题排查"或 `references/api/*.md` 对应文档的"常见问题"章节

## 禁止行为

1. **丢失待办** — 每步必须在待办清单中跟踪，不能跳过待办直接执行，不能偷懒
2. **不查文档** — 执行任何API前必须先读对应文档，不能凭直觉调用
3. **不评估就持续执行** — 每个执行步骤必须经过Evaluator验证通过才能进入下一步
4. **死磕坐标** — 同一坐标反复定位失败超过5次，应调整策略（换窗口重截图、调网格参数、换操作模式）或回Planner重新规划

## 核心概念

### 1. 网格坐标

ScreenClaw 通过在截图上叠加坐标网格来定位元素。坐标格式为 `XxY`（如 `50x35`），表示截图中距左边界X%、距上边界Y%的位置。坐标的准确性直接影响操作成功率。你直接读出坐标即可，不需要计算实际像素位置。

| 参数 | 默认值 | 说明 | 调整建议 |
|------|--------|------|----------|
| `color_mode` | grayscale | 颜色模式：grayscale（灰度）/ color（原色） | 灰度下彩色网格更醒目，需看原始色彩时用color |
| `grid_density` | 5.0 | 每格宽度（百分比），越小越密 | 定位困难时减小（如3） |
| `grid_opacity` | 50 | 网格透明度(0-100) | 遮挡内容时降低（如30） |
| `grid_color` | #ff0000 | 网格颜色 | 与截图内容混淆时更换 |
| `number_density` | 2 | 数字密度 | 定位困难时减小（如1） |
| `number_size` | 12 | 字体大小(4-32) | 遮挡内容时降低，看不清数字时增大 |
| `number_decimal` | 0 | 小数位数(0-4) | 精度不够时增大（如1） |
| `number_color` | #ff0000 | 数字颜色 | 与截图内容混淆时更换（如#FFFF00） |
| `number_opacity` | 100 | 数字透明度(0-100) | 遮挡内容时降低（如30） |

### 2. 操作模式

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| `background` | 通过PostMessage/SendMessage注入事件，不激活窗口 | **优先使用**，大多数场景 |
| `hijack` | 短暂激活目标窗口，闪电劫持用户的键鼠操作，执行完后会恢复劫持前原样。持续性操作会被打断，例如恢复后中文输入法候选面板会消失 | 按常见问题说明降级；切换窗口后重新尝试background |
| `delegated` | 接管电脑，物理输入，不恢复焦点和鼠标，无需逐次确认。持续性操作能保持，例如中文输入法候选面板会保持 | **用户主动要求时进入**， 会话级持续到退出 |

### 3. 操作原理
读准坐标，通过API自动化操作该坐标，实现自动化操作电脑软件。

- **窗口层级**：Windows应用有主窗口和子窗口，window_id不同。
- **窗口选择规则**：先尝试主窗口，若操作无效再尝试子窗口。对进程的所有窗口截图，逐个尝试操作，直到成功
- **main_window_id**：必填，用于激活/恢复窗口；`get_window_list` 和 `wait` 不需要
- **session_id**：会话标识符，整个会话使用同一个，绝对禁止更换
- **ai_app_type**：每次API调用必须显式传入

## 核心规则【关键，务必牢记】
### 规则1：切角色
- **三角色架构**：Planner（规划）→ Executor（执行）→ Evaluator（评估验证）
- **交替执行**：每个执行步骤后必须评估验证通过才能进入下一步，禁止连续执行多个步骤
- **待办清单**：所有行为都记录在待办清单中，禁止跳过待办直接执行

### 规则2：读坐标

坐标是90%操作失败的原因。

**五阶段分析流程**：目标描述 → 先验自毁 → 全域扫描 → 排除筛选 → 证据确认

1. **目标描述**：明确要找什么元素
2. **先验自毁**：质疑第一直觉，是否有其他相似元素
3. **全域扫描**：在截图中全面检索目标，定位局部。再放大局部细看坐标数字
4. **排除筛选**：根据形状、颜色、位置、上下文排除干扰
5. **证据确认**：至少找到3个周边元素作为参照验证

**坐标定位三步法**：全局定位元素 → 局部放大图片 → 精细读取坐标网格数字

### 规则3：脚本调用规范

**降级路径**：py → ps1 → sh → 手动curl。

**降级前提**：脚本报错时先看错误原因，再决定处理方式：

| 错误类型 | 识别特征 | 处理方式 |
|----------|----------|----------|
| 参数错误 | 缺少参数、参数类型错误、拼写错误 | **修正参数，重跑同一脚本**，不降级 |
| 环境错误 | Python不存在、模块缺失、权限不足 | 降级到下一个脚本 |
| API错误 | 返回WINDOW_NOT_FOUND等业务错误 | 查文档排查根因，不降级 |

**脚本分工**：
- **截图API** → `scripts/fetch_screenshot_cli.py`（专用脚本，处理base64响应）
- **batch API** → `scripts/api_call_batch.ps1`（PowerShell专用，简化指令格式）
- **其他所有API** → `scripts/api_call.py`（通用脚本）

**通用API调用**：
```bash
python scripts/api_call.py <api_url> <token> <endpoint> ai_app_type=<值> session_id=<值> main_window_id=<值> [其他参数...]
```

**截图API调用**：
```bash
python scripts/fetch_screenshot_cli.py <api_url> <token> <window_id> <session_id> <ai_app_type> <main_window_id> [网格和数字参数...]
```

详细用法 → `scripts/README.md`

### 规则4：查文档

执行任何操作前查阅文档：
1. `scripts/README.md` — 脚本使用说明（调用格式、降级路径）
2. `references/api/{api_name}.md` — 对应API的详细文档（参数、错误码、排查技巧）

不确定时，搜索 `references/` 目录。

## 方法论

### 基础方法论

#### 读坐标方法论

遵循五阶段分析（见核心规则1）。关键原则：

- **证伪优先**：默认认为坐标可能有误，必须找证据推翻
- **参照验证**：至少定位3个周边元素，互相验证
- **不清晰即错误**：无法清晰辨认坐标时，调整网格参数重截图
- **局部放大**：先全局定位元素区域，再局部放大精细读数
- **长思考即错误**：读坐标时如果思考超过20秒，说明坐标不清晰，必须调整参数重截图

### 三角色架构

你需要通过待办清单，以不同角色的思维，执行不同任务，禁止单个角色独立执行。

**流程**：用户需求 → Planner创建待办 → [Executor执行 → Evaluator验证]循环 → 完成
用户打断 → Planner更新待办 | 重试5次失败 → Planner重新规划

---

### 角色定义

#### Planner（规划者）

**职责**：
- 分析用户需求，拆解任务步骤
- 检索场景模板（`references/scenarios/`），有则复用
- 创建和维护待办清单
- **新进程时，自动添加"全窗口识别"待办项**
- 需求不清时向用户提问
- 用户打断时更新待办
- 5次失败后重新规划

**输出内容**：
- 待办清单（标准格式）
- 向用户提问时：明确的问题+选项
- 规划调整时：调整理由

---

#### Executor（执行者）- 只做不验

**职责**：
- 全窗口识别（当待办中有此项时）
- 截图→五阶段分析→读坐标
- 调用API执行操作

**输出内容**（必须显式输出）：

1. **全窗口识别**（当待办中有此项时）：
```
候选窗口列表：
1. window_id=xxx（子窗口，标题"..."）- 理由：...
2. ...
```

2. **操作汇报**：
```
执行动作：click(x=50,y=35,window_id=xxx,action_method=background)
执行理由：点击[按钮名称]触发功能
截图路径：xxx.png
周边元素坐标：左侧[元素A]45x35，右侧[元素B]55x35，上方[元素C]50x30
```

**自检清单**（3条）：
- [ ] 是否显式输出报告（执行动作+执行理由+截图路径+周边元素坐标）？
- [ ] 是否有调整坐标？无则通过，有则检查第3条
- [ ] 调整幅度是否≥2？（横坐标差异≥2 或 纵坐标差异≥2）

**备注**：坐标调整幅度太小，大概率是读错了。如果横坐标、纵坐标都没有超过2的调整，说明基本上还是在原来的位置附近微调，可能是读错了。必须调整幅度≥2才能通过自检。
---

#### Evaluator（评估者）- 只验不做

**职责**：
- 证伪验证：质疑窗口选择、质疑坐标
- 看坐标位置上是否有执行者所说的元素
- 不重新识别坐标，只质疑

**输出内容**（必须显式输出）：
```
通过
```
或
```
不通过：请检查窗口、坐标，或查阅文档
```

**自检清单**（3条）：
- [ ] 是否检查了坐标位置上确实有该元素？
- [ ] 效果不符时是否查阅了文档？
- [ ] 是否没有重新识别坐标（只质疑）？

---

### 待办清单格式

```
- [in_progress] 守则行：执行三角色架构 | 脚本调用(py→ps1→sh→curl) | 遇问题先查文档
- [in_progress] 全局参数（必须先填完才能继续）：session_id=xxx, ai_app_type=xxx, api_url=xxx, token=xxx
- [pending] 准备：阅读关键文档、获取请求地址和token、启动三角色架构
- [pending] Planner：检索已有场景、任务分析与步骤拆解
- [pending] 全窗口识别：[新进程时自动添加]
- [pending] 先切角色，再执行Executor1：[具体操作描述]
- [pending] Executor1自检：[自检清单]
- [pending] 先切角色，再评估Evaluator1：[验证标准描述]
- [pending] Evaluator1自检：[自检清单]
- [pending] 先切角色，再执行Executor2：...
- [pending] Executor2自检：...
- [pending] 先切角色，再评估Evaluator2：...
- [pending] Evaluator2自检：...
- [pending] 沉淀复盘（须主动询问用户是否沉淀，用户确认后才执行）
```

- **守则行**必须在最前面，且**只能在整个待办清单所有其他项都 completed 后才能标记 completed**
- **全局参数行**只放session_id和ai_app_type
- **全窗口识别**：新进程时Planner自动添加，后续切换进程时也需添加
- **显式出输出内容**：每个执行步骤和评估验证都必须有明确的输出内容，且必须满足自检清单要求

### 新任务规则

用户在同一会话中提出与当前待办无关的新需求时，视为新任务：

**判断标准**：操作对象变了（窗口/软件）| 目标意图变了 | 用户明确说"换个任务"
**处理方式**：当前待办全部completed → 生成新session_id → 创建新待办清单 → Planner添加"全窗口识别"待办项 → 重新启动三角色循环

## API索引

> **执行前必做：** 从下表定位到API后，先阅读对应API文档 `references/api/{endpoint}.md`，再调用。

| API | 方法 | 什么时候用 | 参考文档 |
|-----|------|-----------|----------|
| health | GET | 操作前检查服务 | `references/api/health.md` |
| get_window_list | POST | 找目标窗口ID（建议带 include_children=true） | `references/api/get_window_list.md` |
| screenshot | POST | 查看界面/定位坐标 | `references/api/screenshot.md` |
| scroll_screenshot | POST | 滚动长截图，用于记录内容，不适用于定位坐标） | `references/api/scroll_screenshot.md` |
| click | POST | 触发按钮/进入页面 | `references/api/click.md` |
| long_press | POST | 长按触发功能 | `references/api/long_press.md` |
| swipe | POST | 触摸式滑动 | `references/api/swipe.md` |
| drag | POST | 拖拽元素（文件拖放、窗口拖动），支持速度控制 | `references/api/drag.md` |
| scroll | POST | 鼠标滚轮滚动 | `references/api/scroll.md` |
| right_click | POST | 打开上下文菜单 | `references/api/right_click.md` |
| hover | POST | 触发悬停效果 | `references/api/hover.md` |
| mouse_move | POST | 平滑移动鼠标（游戏视角控制），不按下鼠标键 | `references/api/mouse_move.md` |
| input_text | POST | 输入文本，注意，输入文本自带先点击再输入，不需要分两步 | `references/api/input_text.md` |
| press_key | POST | 触发快捷键/特殊按键/持续按键，注意，按键自带先点击再输入，不需要分两步 | `references/api/press_key.md` |
| wait | POST | 等待UI动画/页面加载 | `references/api/wait.md` |
| batch | POST | 执行多步固定流程 | `references/api/batch.md` |
| delegated | POST | 用户主动要求进入/退出托管模式 | `references/api/delegated.md` |

**注意**：
-  `health` 是 get ，其它接口都是 POST
- `scroll_screenshot` 不支持 batch，请单独调用专用脚本
- `input_text` 和 `press_key` 可带坐标参数，API会先点击再执行操作
- 所有POST操作前建议先 `screenshot` 验证界面状态

## 常见问题排查

按优先级递进：**更换窗口ID → 调整坐标参数 → 更换操作方式 → 用户操作干扰**

### 托管模式

- **进入**：用户主动要求时调用 `delegated` API 进入（进入时需确认）
- **效果**：所有操作强制走物理路径，无需逐次确认，AI完全控制焦点
- **退出**：调用 `delegated` API 退出，或按快捷键 Ctrl+Alt+Z
- **安全**：托管模式下AI完全控制电脑，确保用户理解风险

### 操作不成功

#### 1. 窗口是否正确【最先排查】

- **现象**：操作完全无效，截图无变化。截图API报错，如failed to capture screenshot或坐标点击后界面无响应
- **原因**：不同应用需要不同窗口，例如主窗口、子窗口等
- **解决**：`get_window_list` 加 `include_children=true`，对主窗口、所有子窗口重新截图，逐个窗口尝试

#### 2. 坐标是否正确【最常见】

- **现象**：操作结果与预期不符，截图对比无明显变化，坐标位置不清晰等
- **解决**：
  - 调整网格参数，具体调整方法参阅截图api文档。例如减小density、增大number_size、降低opacity
  - 忘记之前的错误坐标，重新基于读坐标方法论，从全局扫描开始，重新定位坐标


#### 3. 操作方式是否正确【最后考虑，满足所有条件才切换】

必须同时满足以下所有条件，才能考虑切换操作方式（background→hijack）：

- **条件1**：已尝试主窗口和所有有内容的子窗口
- **条件2**：在条件1基础上，重新调整过网格参数和坐标，且坐标调整幅度大（如50x35→80x20，不是1-2格的小调整）
- **条件3**：在条件2基础上，坐标周边元素的验证，经Evaluator评估有效

- **解决**：满足所有条件后，background→hijack

#### 4. 用户操作阻塞

- **现象**：hijack模式下操作混乱
- **解决**：请求用户暂停操作

### 连接不成功

1. 调用 `health` 检查服务
2. 检查网络和端口
3. 检查认证参数

## 场景模板机制

规划前检索、沉淀复盘的完整流程 → `references/scenarios/README.md`

## 参考文档

- `references/config.md` — 连接配置（地址、Token、ai_app_type、session_id规则）
- `references/api/*.md` — 各API详细文档（含参数、示例、常见问题）
- `references/scenarios/*/*.md` — 场景模板
- `scripts/README.md` — 脚本使用说明

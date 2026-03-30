---
name: screenclaw
description: |
  通过HTTP API控制ScreenClaw实现桌面软件自动化操作。

  何时使用此技能：
  - 用户需要操作没有API的桌面Windows软件（如点击按钮、输入文字）
  - 需要截图并让AI分析界面元素位置
  - 需要程序化控制桌面应用程序
  - 用户提到"点击某个软件的按钮"、"在XX软件中输入"等操作

  即使是通用任务，只要涉及Windows桌面控制，就必须使用此技能。

  关键词：screenclaw、屏幕控制、桌面自动化、视觉操作、Windows软件控制
---

# ScreenClaw 技能

通过HTTP API控制ScreenClaw实现桌面软件自动化操作。

> **执行前必做**：
> 1. 调用任何API前，必须先阅读对应API的reference文档
> 2. 调用任何API前，必须先完成上方的"调用前清单"
> 3. screenshot API必须使用脚本调用，禁止AI自己生成curl或PowerShell命令

## 快速开始

### 核心概念

**坐标系统**：网格坐标系统，截图时会在图片上显示数字标记（如50表示中间位置）。AI只需要读出目标位置对应的数字即可，无需进行百分比换算。

**操作方式**：background（无感）优先，失败时用hijack（劫持）

---

## 调用前清单（必须按顺序完成）

在使用此技能前，**必须按顺序完成以下步骤**：

### 步骤1：阅读关键文档
- [ ] 阅读 `references/api/call_templates.md`（API调用模板和填写规则）
- [ ] 阅读 `references/config.md`（获取API地址、Token、ai_app_type）
- [ ] 阅读 `scripts/README.md`（了解脚本使用方式和降级路径）

**为什么要先阅读**：避免因不熟悉模板格式导致的命令错误（如JSON引号转义问题）

### 步骤2：创建待办清单并按角色切换执行

- [ ] **生成 session_id**（仅一次）：格式 `app_name_YYYYMMDD_HHMMSS`，使用下划线分隔
- [ ] **进入Planner角色**：分析需求、创建待办清单
- [ ] **进入Executor角色**：执行当前待办、返回结果
- [ ] **进入Evaluator角色**：验证执行结果
- [ ] **循环执行**：直到所有待办完成或需要重新规划

### 步骤3：遇到问题时，重新查阅文档（禁止盲目尝试）

- [ ] **遇到API调用失败**：查阅 `references/api/*.md` 对应的API文档
- [ ] **遇到参数错误**：查阅 `references/config.md` 确认参数格式
- [ ] **遇到脚本执行失败**：查阅 `scripts/README.md` 确认使用方式
- [ ] **遇到坐标/操作问题**：查阅 `SKILL.md` 的"常见问题排查"章节
- [ ] **不确定时**：使用搜索工具在 `references/` 目录中搜索关键词

> ⚠️ **禁止盲目尝试**：遇到问题时，**必须先查阅文档**，而不是自己猜测参数或修改命令格式。文档中已包含所有常见问题的解决方案。
> ⚠️ **截图用script里的脚本**：必须使用 `scripts/fetch_screenshot_cli.py` 或 `scripts/fetch_screenshot_cli.ps1` 来调用截图API，禁止自己生成curl或PowerShell命令。

---

## 方法论概览

ScreenClaw技能采用**三层架构**来组织任务执行：

| 层级 | 名称 | 说明 |
|------|------|------|
| **L1** | 通用角色流 | 任务由三个角色协作完成：Planner规划 → Executor执行 → Evaluator验证，通过待办清单驱动角色切换 |
| **L2** | 角色内部流程 | 每个角色内部有自己的节点流程（如Executor：截图→分析→执行API），每个节点遵循T-IPO-E闭环 |
| **L3** | 具体业务流 | 不同应用有不同的业务步骤（如微信发消息：找联系人→点聊天→输入→发送），沉淀在场景模板中 |

**T-IPO-E**：每个操作节点都按这5个阶段执行
- **Trigger**：什么触发这个节点？
- **Input**：需要什么输入？
- **Process**：执行什么处理？
- **Output**：产生什么输出？
- **Exception**：异常时怎么处理？

三层关系：**L1定义角色切换逻辑 → L2定义角色内部节点 → L3定义具体应用的业务步骤**

---

## 快速上手示例

假设用户说"**帮我在微信发消息给产品组**"，完整流程如下：

**第1步：Planner角色**（规划）
- 用TodoWrite创建待办清单
- 生成session_id（仅一次）：`wechat_20260330_143025`

**第2步：Executor角色**（执行 - 第一个待办）
- 调用 `get_window_list` 找到微信窗口
- 调用 `fetch_screenshot_cli.py` 获取界面截图
- 分析截图，定位"产品组"群聊坐标（如x=15, y=35）
- 调用 `api_call.py` 执行click操作
- 输出：执行动作+理由+周边元素+图片路径

**第3步：Evaluator角色**（验证 - 第一个待办）
- 读取截图，检查是否成功选中"产品组"
- 通过→继续下一个待办；不通过→返回Executor重试

**第4步：循环执行**（Executor→Evaluator交替）
- 点击输入框 → 验证激活
- 输入消息内容 → 验证输入成功
- 点击发送按钮 → 验证发送成功

**关键点**：
- 所有API调用用同一个session_id
- 用脚本调用API，不要手写curl
- Executor每步输出：执行动作+理由+周边元素+图片路径

---

## 阅读指引

> **首次使用**：读完本示例即可开始，遇到问题再查阅下方章节
> **执行时**：重点看"核心规则"的规则1-2和"常见问题排查"
> **深入了解**：需要时再读"三角色架构"的详细说明

---

## 核心规则（必须遵守）

### 规则1：角色切换 + 待办驱动流程（L1: 通用角色流）

**通过待办清单驱动角色切换，执行者和评估者交替工作**

```
用户需求 → Planner创建待办 → [Executor执行 → Evaluator验证]循环 → 完成/重规划
```

**切换时机**：
- 任务开始 → 进入Planner角色
- Planner创建待办后 → 切换到Executor角色
- Executor完成后 → 切换到Evaluator角色
- Evaluator通过 → 继续下一个Executor待办
- Evaluator不通过 → 返回Executor重试
- **重试5次仍失败** → 切换到Planner重新规划
- Evaluator发现根本性问题时 → 也可触发Planner重新规划

**待办清单格式**：
```
- [in_progress] 全局参数：session_id=xxx, ai_app_type=xxx, main_window_id=xxx, api_url=xxx, token=xxx
- [in_progress] 执行：具体操作描述
- [pending] 评估：验证标准描述
```

**关键规则**：
- Planner使用TodoWrite创建待办清单，生成session_id（仅一次）
- 所有角色共享同一个session_id，绝对禁止每次生成新的
- 只有Evaluator认为通过才能进入下一个待办

### 规则2：脚本调用规范
**降级路径**：py-->ps1-->sh-->手动curl
**降级原则**：必须使用脚本调用API，python脚本失败后立刻切换psl脚本
**脚本分工（重要）**：
- **截图API** → 使用 `scripts/fetch_screenshot_cli.py`（专用脚本，处理base64响应）
- **其他所有API** → 使用 `scripts/api_call.py`（通用脚本）

**通用API调用（非截图）**：
```bash
python scripts/api_call.py <api_url> <token> <endpoint> <ai_app_type> [参数...]
```

**示例：**
```bash
# 获取窗口列表（建议始终带include_children=true + children_filter=titled）
python scripts/api_call.py http://192.168.10.190:12261 TOKEN get_window_list claude_code keyword=feishu include_children=true children_filter=titled

# 点击
python scripts/api_call.py http://192.168.10.190:12261 TOKEN click claude_code window_id=123456 x=50 y=35
```

**截图API调用（专用）**：
```bash
python scripts/fetch_screenshot_cli.py <api_url> <token> <window_id> [session_id] [ai_app_type]
```
  - **中文处理**：直接传递中文即可，脚本会自动转换为Unicode编码

详细用法 → `scripts/README.md`

### 规则3：手动curl模板（降级方案）

只有在脚本无法使用时，才参考 `references/api/call_templates.md` 手动组装curl命令

**核心原则**：
- JSON内部引号不转义：`{"key":"value"}` 而不是 `{\"key\":\"value\"}`
- 中文必须使用Unicode编码：`你好` → `\u4f60\u597d`
- 不要使用PowerShell -Command模式

### 规则4：重要参数

已在步骤1中阅读 `references/config.md`，获取：
- API基础地址
- 认证Token
- ai_app_type（当前AI应用类型）
- **session_id：整个会话使用同一个，绝对不要每次生成新的**
- **main_window_id：必填，用于激活最小化窗口**

> ⚠️ **session_id 延续规则**：
> - 首次生成后，后续所有API调用**必须显式传入**同一个session_id
> - **人在回路干涉时**（用户反馈后继续操作），**必须延续使用最初的session_id**，禁止重新生成

> ⚠️ **窗口ID选择规则**：
> - **main_window_id**：必填，用于激活/恢复窗口（如应用最小化时）
> - **window_id（操作窗口）**：优先使用**子窗口ID**操作，大部分应用的输入/按键/运动类操作需要子窗口才能响应
> - 点击类操作（click/long_press/right_click）：主窗口通常可工作
> - 输入/按键/运动类操作（input_text/press_key/swipe/scroll）：通常需要子窗口

### 规则5：问题排查

遇到问题时查阅对应文档：
- **API调用失败** → `references/api/*.md` 对应的API文档
- **参数错误** → `references/config.md`
- **脚本执行失败** → `scripts/README.md`
- **坐标/操作问题** → 本SKILL.md的"常见问题排查"章节
- **不确定时** → 使用搜索工具在 `references/` 目录搜索关键词

---

## 三角色架构

### 角色切换机制

详细的切换时机和流程见上方**规则1**。本章节重点说明各角色的职责、T-IPO-E和节点级流程。

**单AI（你）通过待办清单切换角色**——你不是一个主Agent，而是根据待办清单的需要，在三个角色之间切换：

1. **Planner角色**：规划阶段，创建待办清单
2. **Executor角色**：执行阶段，完成"执行"类待办
3. **Evaluator角色**：评估阶段，完成"评估"类待办

### 成功定义（大前提）

**团队的成功 > 个人的成功**

| ✅ 团队成功 | ❌ 个人失败 |
|------------|------------|
| 任务最终完成，用户满意 | 某个角色在某一步做错了 |

**关键原则**：
- 过程中的错误不是"失误"，而是"必需的探索"
- 承认错误 = 帮助团队更快找到正确答案
- 没有责备，只有"我们现在知道什么路不通了"

---

### 角色1：Planner（规划者）

**本质**：场景构造器 + 需求翻译器 + 待办清单创建者

**方法论**：
- 场景锚定：5W2H参数化建模
- 拓扑解构：MECE分解，穷尽所有可能

**T-IPO-E**：
| 阶段 | 内容 |
|------|------|
| **Trigger** | 收到用户需求 或 Evaluator的重规划请求 |
| **Input** | 用户需求 / Evaluator的反馈 |
| **Process** | 需求澄清 → 场景构造 → 目标分解 → 创建待办清单 |
| **Output** | 待办清单 + session_id |
| **Exception** | 需求不清晰时向用户提问 |

**职责**：
- 理解用户需求，澄清歧义
- 构造结构化场景描述（5W2H）
- 分解任务步骤（MECE原则）
- **使用TodoWrite工具创建待办清单**，格式如下：
  ```
  - [in_progress] 执行：具体操作描述
  - [pending] 评估：验证标准描述
  ```
- **生成 session_id**（首次规划时生成，格式：`app_name_YYYYMMDD_HHMMSS`）
- **重试失败时**：重新分析场景，调整计划步骤
  - 例如：找不到群聊 → 改为搜索群聊
- **不负责**：操作模式选择、参数调整、API调用

**输出**：待办清单（通过TodoWrite）+ session_id

**待办格式示例**：
```
- [in_progress] 全局参数：session_id=wechat_20260330_143025, ai_app_type=claude_code, main_window_id=123456, api_url=http://..., token=xxx
- [pending] 执行：点击群聊"产品组"
- [pending] 评估：验证是否成功选中
- [pending] 执行：点击输入框
- [pending] 评估：验证是否激活
```

> **首行为全局参数行**：所有后续执行/评估待办共享这些参数，避免重复填写。人在回路干涉时**必须延续首行的session_id**，禁止重新生成。

---

### 角色2：Executor（执行者）

**本质**：坐标定位器 + 操作执行器

**方法论**：
- 五阶段分析：目标描述→先验自毁→全域扫描→排除筛选→证据确认
- 定位三步法：全局定位→局部放大→精细确认
- T-IPO-E：每个操作都有完整闭环

**T-IPO-E**：
| 阶段 | 内容 |
|------|------|
| **Trigger** | 待办清单中当前待办状态变为in_progress |
| **Input** | 待办描述、session_id、当前状态 |
| **Process** | 调用screenshot获取图片 → 五阶段分析 → 调用操作API → 返回结果 |
| **Output** | 执行动作 + 执行理由 + 周边元素（≥3个） + 图片路径 |
| **Exception** | 失败时返回错误信息 + 建议重试方案 |

**职责**：
- 读取待办清单，找到当前in_progress的"执行"待办
- 自行决定操作模式（background/hijack）
- 自行调整参数（网格密度、透明度等）
- 分析截图，精确定位坐标
- 调用API执行操作（**使用session_id，绝对不要生成新的**）
- **完成执行后更新待办状态**：将当前待办标记为completed
- **每一步都必须返回完整输出格式**（见下方）
- **失败时**：根据Evaluator的反馈调整参数重试
- **脚本失败时**：按规则2降级路径切换

**输入**：
- 来自待办清单：当前待办描述
- 来自Evaluator：验证反馈、调整建议
- 共享：session_id

**输出协议（每一步必须遵守）**：

```
执行动作：[操作类型](参数)
  例如：click(x=50, y=35, action_method=background)

执行理由：[为什么是这个点位、这个操作]
  例如：点击"保存"按钮，因为图标是软盘形状，位于(50,35)

周边元素（至少3个）：
  1. [元素名称]：(x, y) - [描述/说明]
  2. [元素名称]：(x, y) - [描述/说明]
  3. [元素名称]：(x, y) - [描述/说明]
  ...

图片路径：/path/to/screenshot.png
```

**周边元素示例**：
```
周边元素：
  1. "取消"按钮：(45, 35) - 点击目标左侧
  2. "帮助"链接：(58, 35) - 点击目标右侧
  3. 窗口标题栏：(50, 10) - 顶部居中
```

**重要**：周边元素用于Evaluator验证执行结果是否正确，必须准确描述。

**五阶段分析流程**：目标描述 → 先验自毁 → 全域扫描 → 排除筛选 → 证据确认

**操作模式选择**：优先background，失败时切换hijack

---

### 节点级流程（Executor内部L2）

Executor的Process由3个节点组成，每个节点独立遵循T-IPO-E：

#### 节点1：获取截图

| 阶段 | 内容 |
|------|------|
| **Trigger** | 待办状态变为in_progress |
| **Input** | window_id, session_id, ai_app_type |
| **Process** | 执行 `fetch_screenshot_cli.py <api_url> <token> <window_id> <session_id> <ai_app_type>` |
| **Output** | 图片路径 |
| **Exception** | 脚本失败 → 按降级路径切换（py→ps1→sh→手动curl） |

#### 节点2：五阶段分析定位坐标

| 阶段 | 内容 |
|------|------|
| **Trigger** | 截图成功返回 |
| **Input** | 图片路径、待办描述（目标元素） |
| **Process** | 目标描述 → 先验自毁 → 全域扫描 → 排除筛选 → 证据确认 |
| **Output** | 目标坐标(x,y) + 周边元素（≥3个） |
| **Exception** | 无法定位 → 调整网格参数重新截图（增大density、降低opacity） |

#### 节点3：执行操作API

| 阶段 | 内容 |
|------|------|
| **Trigger** | 坐标定位完成 |
| **Input** | 坐标(x,y)、window_id、操作类型 |
| **Process** | 执行 `api_call.py <api_url> <token> <endpoint> <ai_app_type> [参数...]` |
| **Output** | API响应结果 |
| **Exception** | 操作失败 → 切换操作方式（background→hijack）或切换窗口ID（主窗口→子窗口） |

---

### 角色3：Evaluator（评估者）

**本质**：证伪者 + 反馈循环

**方法论**：
- 证伪思维：默认认为Executor的结果有误
- 强制反驳：必须找至少3个反例
- T-IPO-E：异常时进行根因分析

**T-IPO-E**：
| 阶段 | 内容 |
|------|------|
| **Trigger** | Executor完成执行待办 |
| **Input** | 截图路径、Executor的完整输出（动作+理由+周边元素） |
| **Process** | 读取截图 → 寻找反例 → 逐个测试 → 根因分析 → 生成反馈 |
| **Output** | 验证结果 + 反馈 + 待办状态更新 |
| **Exception** | 验证失败时给出根因 + 调整建议 |

**职责**：
- 默认认为Executor的结论可能有误
- 读取执行结果的截图
- 强制寻找反例（至少3个）：
  - 反例必须与Executor的理由相关联
  - 反例必须在截图中清晰可见
  - 不清晰也是一种反例
- 只有所有反例都被推翻，才承认成功
- **验证通过**：标记当前评估待办为completed，继续下一个待办
- **验证不通过**：
  - 标记对应的执行待办为in_progress
  - 给出根因分析和调整建议，反馈给Executor重试
  - 重试计数+1
- **重试5次后仍失败**：切换到Planner角色重新规划步骤
  - 例如：找不到目标 → 改用搜索策略
- **发现根本性问题时**：可立即触发Planner重新规划
- **负责向用户沟通**：需要澄清问题时向用户提问

**输入**：
- 来自Executor：执行动作、执行理由、周边元素（≥3个）、图片路径

**输出**：验证结果 + 反馈（包含反例测试和根因分析）+ 待办状态更新

**证伪流程**：假设可能有误 → 寻找反例（至少3个）→ 逐个测试 → 推翻或确认

---

### 节点级流程（Evaluator内部L2）

Evaluator的Process由3个节点组成，每个节点独立遵循T-IPO-E：

#### 节点1：读取执行结果

| 阶段 | 内容 |
|------|------|
| **Trigger** | Executor完成执行待办 |
| **Input** | Executor的输出（执行动作+理由+周边元素）、图片路径 |
| **Process** | 读取截图，根据周边元素定位目标区域 |
| **Output** | 目标区域的视觉状态 |
| **Exception** | 图片无法读取 → 要求Executor重新截图 |

#### 节点2：寻找反例验证

| 阶段 | 内容 |
|------|------|
| **Trigger** | 图片读取成功 |
| **Input** | Executor的执行理由、周边元素描述、截图 |
| **Process** | 强制寻找≥3个反例：①周边元素是否正确 ②操作效果是否明显 ③是否有意外变化 |
| **Output** | 反例列表 + 每个反例的验证结果 |
| **Exception** | 反例无法验证 → 要求Executor补充周边元素描述 |

#### 节点3：判定并更新待办

| 阶段 | 内容 |
|------|------|
| **Trigger** | 反例验证完成 |
| **Input** | 反例列表、验证结果 |
| **Process** | 所有的反例都被推翻？ → 通过：有未推翻的反例 → 不通过，给出根因 |
| **Output** | 验证结果 + 反馈 + 待办状态更新 |
| **Exception** | 重试5次仍失败 → 触发Planner重新规划 |

---

## API快速索引

| API | 方法 | 什么时候用 | 参考文档 |
|-----|------|-----------|----------|
| health | **GET** | 操作前检查服务 | api/health.md |
| get_window_list | POST | 找目标窗口ID | api/get_window_list.md |
| screenshot | POST | 查看界面/定位坐标 | api/screenshot.md |
| click | POST | 触发按钮/进入页面 | api/click.md |
| long_press | POST | 长按触发功能 | api/long_press.md |
| swipe | POST | 触摸式滑动 | api/swipe.md |
| scroll | POST | 鼠标滚轮滚动 | api/scroll.md |
| right_click | POST | 打开上下文菜单 | api/right_click.md |
| hover | POST | 触发悬停效果 | api/hover.md |
| input_text | POST | 输入文本 | api/input_text.md |
| press_key | POST | 触发快捷键/特殊按键 | api/press_key.md |
| wait | POST | 等待UI动画/页面加载 | api/wait.md |
| batch | POST | 执行多步固定流程 | api/batch.md |

**重要**：
- 除 `health` 外，所有接口都是 POST 方法。
- 所有post操作前都建议先调用 `screenshot` 验证界面状态和坐标位置。
- **input_text 和 press_key**：可以带坐标参数，API会先点击该位置激活焦点，再执行操作
- **详细参数**：查阅 `references/api/*.md`

---

## API调用指令模板

> **注意**：优先使用脚本调用API（见规则2）。本节仅作为脚本无法使用时的降级方案参考。

**当你需要直接调用API时，必须使用统一模板** → [查看完整模板](references/api/call_templates.md)

**快速参考**：
- 填写参数：`__API_URL__`、`__TOKEN__`、`__WINDOW_ID__`、`__SESSION_ID__`
- 中文使用Unicode：`你好` → `\u4f60\u597d`
- 优先级：curl.exe → PowerShell → batch
- **只替换参数，不要修改命令结构**

---

## 调用示例

**完整的请求地址和Token**：从 `references/config.md` 获取

### GET请求（只有 health）

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  "http://localhost:12261/api/health"
```

### POST请求（其他所有接口）

**获取窗口列表**：
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"ai_app_type": "claude_code", "session_id": "test", "keyword": ""}' \
  "http://localhost:12261/api/get_window_list"
```

**截图**：
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"ai_app_type": "claude_code", "session_id": "test", "window_id": 12345}' \
  "http://localhost:12261/api/screenshot"
```

**说明**：
- 地址：`http://localhost:12261`（默认端口，实际从config.md获取）
- Token：需要替换 `YOUR_TOKEN_HERE`
- 只有 health 是 GET，其他都是 POST
- GET请求没有请求体，POST请求必须有请求体

---

## 常见问题排查（Executor必须熟读）

> **注意**：本章节供Executor参考，Evaluator只需关注验证流程即可。

### 操作不成功

按以下顺序排查，每个问题都要验证：
按以下优先级递进：更换窗口id-->调整坐标参数-->更换操作方式-->用户操作干扰

#### 1. 子窗口是否正确【最先排查】

**判断标准**：
- 操作完全无效，截图验证无任何变化
- 输入、按键、运动类操作无效果

**原因分析**：
- Windows应用有主窗口和子窗口，它们的window_id不同
- **优先使用子窗口ID操作**，大部分应用的输入/按键/运动类操作需要子窗口才能响应
- 操作类型与窗口对应关系：
  - 点击类（click/long_press/right_click）：主窗口通常可工作
  - 输入类（input_text）：通常需要子窗口
  - 按键类（press_key）：通常需要子窗口
  - 运动类（swipe/scroll）：通常需要子窗口

**解决方案**：
1. 调用 `get_window_list` 时使用 `include_children=true` 获取所有窗口
2. 通过截图判断主窗口和子窗口分别包含哪些内容
3. 根据操作类型选择合适的窗口（**优先子窗口**）
4. 验证方法：对比截图，确认操作作用于正确窗口

#### 2. 坐标是否正确

**判断标准**：
- 需要长时间分析思考才能确定坐标
- 截图验证后操作结果与预期完全不符。例如：预期点击"保存"按钮，结果点击了"关闭"按钮

**网格参数调整**（coordinate_type=grid时）：

| 参数 | 当前值 | 问题 | 调整方案 |
|------|--------|------|----------|
| `density` | 5.0 | 网格太宽，不好判断 | 增大（如改为10） |
| `opacity` | 50 | 网格遮挡内容 | 降低（如改为30） |
| `color` | "#00FF00" | 颜色与内容冲突 | 更换（如改为#FF0000） |
| `number_density` | 2 | 数字太少，定位困难 | 减小（如改为1） |
| `number_size` | 8 | 数字太小看不清 | 增大（如改为12） |
| `number_color` | "#00FF00" | 数字颜色看不见 | 更换（如改为#FFFF00） |
| `number_opacity` | 100 | 数字不够清晰 | 增大（保持100） |
| `number_decimal` | 0 | 坐标精度不够 | 增大（如改为1） |

**截图不完整**：
- **原因**：应用跨屏幕、被最小化、在托盘里、部分超出屏幕
- **解决**：使用 `main_window_id` 激活窗口，或请求用户协助

#### 3. 操作方式是否正确（background/hijack）

**判断标准**：
- 子窗口和坐标都正确，但操作仍然无效
- background模式下截图验证无响应

**原因分析**：
- background模式通过PostMessage/SendMessage注入事件
- 某些应用（特别是UWP应用）可能不响应background模式

**解决方案**：
1. 优先尝试background模式
2. 验证时发现无效，改用hijack模式
3. hijack模式会短暂激活目标窗口，需要用户确认

#### 4. 用户操作阻塞

**判断标准**：
- hijack模式下操作混乱
- 用户无意中抢夺了操作

**解决方案**：
- 请求用户暂停操作
- 等待用户确认后重新执行

### 连接不成功

**检查步骤**：
1. 调用 `health` 检查服务是否启动
2. 检查网络是否通畅（地址和端口）
3. 检查认证参数是否正确

---

## 场景模板机制

任务成功后，评估者Evaluator询问用户：
> "是否将这次操作流程沉淀为场景模板？"

存储位置：`references/scenarios/{应用名}/{场景名}.md`

---

## 参考文档

- `references/config.md` - 连接配置（地址、Token、session_id）
- `references/api/*.md` - 各API详细文档
- `references/scenarios/*/*.md` - 场景模板
- `scripts/*` - 可复用脚本

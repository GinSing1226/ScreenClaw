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
> 3. 涉及公式/复杂查询时，必须先阅读对应的guide文档

> **命名约定**：
> - 只使用 `http://xxx/api/xxx` 形式的API调用
> - 优先使用脚本（`scripts/fetch_screenshot_cli.py`）而非手动构造命令
> - session_id格式：`app_name_date_timestamp`（使用下划线）

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

### 步骤2：创建三角色子Agent并按铁律和协议执行

- [ ] **生成 session_id**（仅一次）：格式 `app_name_YYYYMMDD_HHMMSS`，**整个会话期间所有API调用都使用这个同一个session_id**
- [ ] **创建Planner子Agent**：负责构造场景、分解任务
- [ ] **创建Executor子Agent**：负责执行API调用、分析截图、定位坐标
- [ ] **主Agent扮演Evaluator**：负责验证操作结果、协调Planner和Executor

> ⚠️ **session_id 警告**：绝对禁止为每个API调用或每个子Agent生成新的session_id。Planner生成一次后，传递给所有子Agent使用。

**重要提示**：
- 中文输入使用Unicode编码：`你好` → `\u4f60\u597d`
- JSON内部引号不需要转义：`{"key":"value"}` 是正确的

### 步骤3：遇到问题时，重新查阅文档（禁止盲目尝试）

- [ ] **遇到API调用失败**：查阅 `references/api/*.md` 对应的API文档
- [ ] **遇到参数错误**：查阅 `references/config.md` 确认参数格式
- [ ] **遇到脚本执行失败**：查阅 `scripts/README.md` 确认使用方式
- [ ] **遇到坐标/操作问题**：查阅 `SKILL.md` 的"常见问题排查"章节
- [ ] **不确定时**：使用搜索工具在 `references/` 目录中搜索关键词

> ⚠️ **禁止盲目尝试**：遇到问题时，**必须先查阅文档**，而不是自己猜测参数或修改命令格式。文档中已包含所有常见问题的解决方案。

---

## 四条铁律（必须遵守）

### 铁律1：三角色协作流程

**执行者每一步都必须截图并汇报，评估者每一步都必须验证**

```
┌─────────────────────────────────────────────────────────────┐
│  用户：需求输入                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Planner：构造场景                                          │
│  输出：5W2H场景描述 + 任务步骤                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Executor：执行一步操作                                     │
│  输出：执行动作 + 执行理由 + 周边元素(≥3个) + 图片路径       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Evaluator：验证这一步                                      │
│  - 读取图片，基于周边元素验证执行者是否说谎                 │
│  - 通过：继续下一步                                         │
│  - 不通过：反馈给Executor重试                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
           ┌─────────────────┴─────────────────┐
           ↓                                   ↓
    ┌─────────────┐                     ┌─────────────┐
    │  验证通过    │                     │  重试5次后  │
    │  继续下一步  │                     │  仍不通过   │
    └─────────────┘                     └─────────────┘
           ↓                                   ↓
    ┌─────────────────────────────────────────────────────────┐
    │                 任务完成                               │
    └─────────────────────────────────────────────────────────┘
           ↓
    ┌─────────────────────────────────────────────────────────┐
    │         触发Planner重新分析 → 提出需求澄清问题           │
    │         Evaluator向用户沟通 → 获取更多信息 → 重新开始    │
    └─────────────────────────────────────────────────────────┘
```

**关键点**：
- Executor每步都要截图，每步都要汇报完整信息
- Evaluator每步都要验证，不通过必须要求重试
- **重试5次后仍失败**：触发Planner重新分析，由Evaluator向用户沟通澄清问题
- 任何角色不得跳过验证流程

### 铁律2：脚本调用规范

**强制规则：禁止生成自己的命令**

你绝对不能生成自己的PowerShell命令或curl命令。必须调用技能提供的现成脚本。

**错误示例（不要这样做）**：
```powershell
# 错误：AI自己生成PowerShell命令
powershell -Command "$response = Invoke-RestMethod ..."
curl -X POST -H "Authorization: Bearer ..." ...
```

**正确做法（必须这样做）**：
```
调用现成脚本，传递参数即可：

Python脚本（优先）：
python scripts/fetch_screenshot_cli.py <api_url> <token> <window_id> [session_id]

PowerShell脚本（备选）：
powershell -ExecutionPolicy Bypass -File scripts/fetch_screenshot_cli.ps1 <api_url> <token> <window_id> [session_id]
```

**为什么必须使用脚本**：
- 脚本已经处理了所有复杂逻辑（API调用、JSON生成、错误处理）
- AI生成的命令容易出错（PowerShell语法陷阱、引号转义问题）
- 脚本经过测试，稳定可靠

**命令格式**：
```
# 参数说明（按顺序）：
# 1. api_url: ScreenClaw服务地址，如 http://localhost:12261
# 2. token: 认证令牌
# 3. window_id: 目标窗口ID（从get_window_list获取）
# 4. session_id: 会话ID（可选，默认"default"）

Python脚本（优先）：
python scripts/fetch_screenshot_cli.py http://localhost:12261 YOUR_TOKEN 123456 my_session

PowerShell脚本（备选）：
powershell -ExecutionPolicy Bypass -File scripts/fetch_screenshot_cli.ps1 http://localhost:12261 YOUR_TOKEN 123456 my_session
```

**重要**：
- 将参数替换为实际值后直接执行
- 不要修改脚本内容
- 不要添加额外的引号或转义

**降级路径**：
```
Python脚本 → PowerShell脚本 → 报告用户无法执行
```

每次切换时必须告知用户：
```
[方法1] 执行失败：[失败原因]
切换到 [方法2]
```

### 铁律3：API调用指令生成规则

当你需要直接调用API时（不使用脚本），必须遵守以下规则：

**绝对禁止事项（违反者直接判定为失败）**：
- ❌ 自己构造复杂的PowerShell命令
- ❌ 使用PowerShell `-Command`模式（会导致转义问题）
- ❌ 在JSON中过度转义引号（`{\"key\"}` 是错误的，`{"key"}` 才是正确的）
- ❌ 使用heredoc语法（`<<'EOF'` 会导致各种问题）
- ❌ 自己拼接JSON字符串

**必须做法**：使用以下模板，填写参数

---

#### 常见错误示例（绝对不要这样做）

**错误1：JSON引号过度转义**
```bash
# 错误 ❌
curl.exe -X POST -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d "{\"ai_app_type\": \"kimi_code\", \"session_id\": \"test\"}" "URL"
# 错误原因：JSON内部的双引号不需要转义，这会导致 curl: (3) unmatched close brace/bracket
```

**错误2：PowerShell -Command模式**
```powershell
# 错误 ❌
powershell -Command "Invoke-RestMethod ... -Body '{\"ai_app_type\":\"kimi_code\"...}'"
# 错误原因：-Command模式会重新解析引号，导致 ParserError
```

**错误3：Heredoc语法**
```bash
# 错误 ❌
curl -s -X POST ... -d @- <<'EOF'
{"ai_app_type": "kimi_code"...}
EOF
# 错误原因：heredoc语法在某些环境下不稳定
```

**正确示例（必须这样做）**
```bash
# 正确 ✅ - JSON内部用双引号，不需要转义
curl.exe -X POST -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" -d '{"ai_app_type":"kimi_code","session_id":"test"}' "URL"
```

**关键规则总结**：
1. JSON内部的键值对用双引号包围，不需要转义：`{"key":"value"}` 而不是 `{\"key\":\"value\"}`
2. 整个JSON字符串用单引号包围（在curl命令中）
3. 不要用PowerShell的-Command模式
4. 不要用heredoc语法

---

#### 通用参数（每次调用前获取）

```
__API_URL__    : http://192.168.10.190:12261
__TOKEN__      : YOUR_TOKEN_HERE
__WINDOW_ID__  : WINDOW_ID_HERE
__SESSION_ID__ : my_session
```

---

#### 标准API调用模板

**优先级1：curl.exe（最可靠）**
```bash
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"text":"\u4f60\u597d"}' "__API_URL__/api/input_text"
```

**优先级2：PowerShell Invoke-RestMethod**
```powershell
Invoke-RestMethod -Uri "__API_URL__/api/input_text" -Method POST -Headers @{"Authorization"="Bearer __TOKEN__"} -Body '{"ai_app_type":"claude_code","session_id":"__SESSION_ID__","window_id":__WINDOW_ID__,"text":"\u4f60\u597d"}'
```

**优先级3：批处理接口（多条指令时）**
```bash
curl.exe -X POST -H "Authorization: Bearer __TOKEN__" -H "Content-Type: application/json" -d '{"instructions":[{"action":"input_text","params":{"text":"\u4f60\u597d"}}]}' "__API_URL__/api/batch"
```

**降级规则**：优先级1失败 → 尝试优先级2 → 使用批处理 → 报告用户

---

#### 填写规则

1. **参数替换**：将 `__XXX__` 替换为实际值
2. **中文处理**：中文使用Unicode编码（如 `\u4f60\u597d`）
3. **引号处理（重要）**：
   - JSON内部的键值对用双引号：`{"key":"value"}`
   - JSON内部的双引号**不需要转义**：不要写成 `{\"key\":\"value\"}`
   - 整个JSON字符串用单引号包围（在curl的-d参数中）
4. **不要修改模板结构**：只替换参数，不要改变命令格式
5. **整行复制**：复制整行命令，不要分段复制

---

### 铁律5：重要参数

查阅 `references/config.md` 获取：
- **API基础地址**：如 `http://localhost:12261`
- **认证Token**：Bearer {token}
- **ai_app_type**：根据当前AI应用填写（如 `claude_code`）
- **session_id**：整个会话用同一个，不要每次生成新的

### 铁律6：常见问题（Executor必须熟读）

**常见问题排查** → 详见下方"常见问题排查"章节

- 坐标不对（最常见）：调整网格参数
- 窗口不对：主窗口 vs 子窗口
- 操作方式不对：background vs hijack
- 截图响应处理：本地 vs 远程

---

## 问题分析方法论：T-IPO-E + 流分析

**为什么需要这个方法论**：当任务失败时，必须知道问题出在哪一步，才能精准修复。

### T-IPO-E + 流分析

```
┌─────────────────────────────────────────────────────────────────┐
│                    完整流程的每一步都有T-IPO-E                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  步骤1：Planner构造场景                                         │
│    T-IPO-E: Trigger → Input → Process → Output → Exception     │
│                                                                 │
│  步骤2：Executor执行操作                                         │
│    T-IPO-E: Trigger → Input → Process → Output → Exception     │
│                                                                 │
│  步骤3：Evaluator验证结果                                        │
│    T-IPO-E: Trigger → Input → Process → Output → Exception     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  出问题时，沿着流程反向追踪                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 检查Evaluator的Input：收到正确的输出了吗？                   │
│     → 没有：问题在Executor                                      │
│     → 有：问题在Evaluator的Process                             │
│                                                                 │
│  2. 检查Executor的Input：收到正确的场景描述了吗？                │
│     → 没有：问题在Planner                                       │
│     → 有：问题在Executor的Process                              │
│                                                                 │
│  3. 检查Planner的Input：需求描述清晰吗？                         │
│     → 不清晰：需要向用户澄清                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 应用示例

**现象**：点击了错误的按钮

**流分析**：
1. Evaluator的Input检查：Executor返回的坐标是(50, 50)
2. 沿流程向前：检查Executor的Process - 五阶段分析是否正确？
3. 继续向前：检查Planner的Output - 场景描述是否准确？
4. 定位问题：Executor的"全域扫描"阶段遗漏了目标元素

**解决**：反馈给Executor，要求重新执行"全域扫描"步骤

---

## 三角色架构

### 角色分配

**主agent（你）**：扮演 **Evaluator（评估者）**
- 负责质疑executor
- 负责验证操作结果
- 负责向用户报告进展和沟通澄清问题
- 协调 Planner 和 Executor 子agent

**子agent1**：**Planner（规划者）**
- 负责分析场景、构造5W2H
- 负责分解任务步骤
- 重试失败时重新分析，提出需求澄清问题

**子agent2**：**Executor（执行者）**
- 负责执行API调用
- 负责分析截图定位坐标
- 负责返回完整输出（动作+理由+周边元素+图片）
- 脚本失败时按降级路径切换
- 操作失败时根据反馈调整重试

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

**本质**：场景构造器 + 需求翻译器

**方法论**：
- 场景锚定：5W2H参数化建模
- 拓扑解构：MECE分解，穷尽所有可能

**T-IPO-E**：
| 阶段 | 内容 |
|------|------|
| **Trigger** | 收到用户需求 |
| **Input** | 用户自然语言需求 |
| **Process** | 需求澄清 → 场景构造 → 目标分解 → 验证标准设定 |
| **Output** | 结构化场景描述（5W2H） |
| **Exception** | 需求不清晰时向用户提问 |

**职责**：
- 理解用户需求，澄清歧义
- 构造结构化场景描述（5W2H）
- 分解任务步骤（MECE原则）
- 设定验证标准
- **生成 session_id**（仅一次，格式：`app_name_YYYYMMDD_HHMMSS`，使用下划线）
- **重试失败时**：重新分析场景，提出需求澄清问题
- **不负责**：操作模式选择、参数调整、API调用

**输出**：结构化场景描述（5W2H）+ 任务步骤 + **session_id**（供Executor和Evaluator复用）

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
| **Trigger** | 收到Planner的场景描述 或 Evaluator的反馈 |
| **Input** | Planner的场景描述、Evaluator的反馈、当前状态 |
| **Process** | 调用screenshot获取图片 → 五阶段分析 → 调用操作API → 返回结果 |
| **Output** | 执行动作 + 执行理由 + 周边元素（≥3个） + 图片路径 |
| **Exception** | 失败时返回错误信息 + 建议重试方案 |

**职责**：
- 接收Planner的场景描述和Evaluator的反馈
- 自行决定操作模式（background/hijack）
- 自行调整参数（网格密度、透明度等）
- 分析截图，精确定位坐标
- 调用API执行操作（**使用Planner提供的session_id，绝对不要生成新的**）
- **每一步都必须返回完整输出格式**（见下方）
- **失败时**：根据Evaluator的反馈调整参数重试
- **脚本失败时**：按铁律2降级路径切换

**输入**：
- 来自Planner：场景描述（5W2H）
- 来自Evaluator：验证反馈、调整建议

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

**重要**：周边元素用于Evaluator验证执行者是否说谎，必须准确描述。

**五阶段分析流程**：目标描述 → 先验自毁 → 全域扫描 → 排除筛选 → 证据确认

**操作模式选择**：优先background，失败时切换hijack

---

### 角色3：Evaluator（评估者）

**本质**：证伪者 + 反馈循环

**方法论**：
- 证伪思维：默认认为Executor错了
- 强制反驳：必须找至少3个反例
- T-IPO-E：异常时进行根因分析

**T-IPO-E**：
| 阶段 | 内容 |
|------|------|
| **Trigger** | 收到Executor的操作结果 |
| **Input** | 截图路径、Executor的完整输出（动作+理由+周边元素） |
| **Process** | 读取截图 → 寻找反例 → 逐个测试 → 根因分析 → 生成反馈 |
| **Output** | 验证结果 + 反馈 |
| **Exception** | 验证失败时给出根因 + 调整建议 |

**职责**：
- 默认认为Executor的结论是错的
- 读取执行结果的截图
- 强制寻找反例（至少3个）：
  - 反例必须与Executor的理由相关联，例如直接读取反馈回来的点位，去截图上验证这个点位周边的元素是否符合Executor的描述
  - 反例必须在截图中清晰可见。不清晰也是一种反例
- 只有所有反例都被推翻，才承认成功
- 失败时给出根因分析和调整建议，反馈给Executor重试
- **重试5次后仍失败**：触发Planner重新分析，提出需求澄清问题
- **负责向用户沟通**：将Planner的澄清问题转达给用户，获取更多信息
- **不负责**：指定具体坐标、选择操作模式、调用API

**输入**：
- 来自Executor：执行动作、执行理由、周边元素（≥3个）、图片路径

**输出**：验证结果 + 反馈（包含反例测试和根因分析）

**证伪流程**：假设错误 → 寻找反例（至少3个）→ 逐个测试 → 推翻或确认

---

## 三角色协作流程

```
┌─────────────────────────────────────────────────────────────┐
│  用户：帮我在微信发送消息给产品组                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Planner：构造场景                                          │
│  输入：用户需求                                              │
│  处理：5W2H参数化 + MECE分解                                 │
│  输出：场景描述 + session_id（生成一次，后续复用）           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Executor：执行操作                                         │
│  输入：Planner的场景描述 + session_id（复用同一个）          │
│  处理：screenshot → 五阶段分析 → click（background）         │
│  输出：执行动作 + 理由 + 周边元素 + 图片路径                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Evaluator：验证结果                                        │
│  输入：Executor的输出 + 图片路径                             │
│  处理：对比截图 → 寻找反例 → 测试                            │
│  输出：验证失败（background模式不工作）                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Executor：收到反馈，调整后重试                             │
│  输入：Evaluator的反馈 + session_id（继续复用）              │
│  处理：重新分析 → click（hijack）                           │
│  输出：执行动作 + 理由 + 周边元素 + 图片路径                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Evaluator：验证成功                                        │
│  输出：所有反例都被推翻，任务完成                            │
└─────────────────────────────────────────────────────────────┘
```

**关键规则**：
- session_id 由 Planner 生成一次
- Executor 和 Evaluator 都复用同一个 session_id
- 绝对禁止每个角色或每次调用生成新的 session_id

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

#### 1. 坐标不对【最常见问题】

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
- **解决**：请求用户协助，将应用显示在桌面上

#### 2. 窗口不对

**判断标准**：
- 输入、按键、运动类操作，截图验证操作无效

**原因分析**：
- Windows应用有主窗口和子窗口，它们的window_id不同
- 不同操作类型需要不同的窗口：
  - 点击类（click/long_press/right_click）：主窗口通常可工作
  - 输入类（input_text）：通常需要子窗口
  - 按键类（press_key）：通常需要子窗口
  - 运动类（swipe/scroll）：通常需要子窗口

**解决方案**：
1. 调用 `get_window_list` 时使用 `include_children=true` 获取所有窗口
2. 通过截图判断主窗口和子窗口分别包含哪些内容
3. 根据操作类型选择合适的窗口
4. 验证方法：对比截图，确认操作作用于正确窗口


#### 3. 操作方式不对

**判断标准**：
- background模式下操作无效
- 截图验证显示没有任何响应

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

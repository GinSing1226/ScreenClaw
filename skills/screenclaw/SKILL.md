---
name: screenclaw
description: 通过HTTP API控制ScreenClaw实现桌面软件自动化操作。当用户提到以下场景时使用此技能：提到 "screenclaw"、"屏幕控制"、"自动操作"、"视觉操作"；需要自动化操作没有API/CLI的桌面软件；需要截图并带坐标网格供AI分析；需要程序化操作桌面应用程序。

  ScreenClaw让AI应用能够控制任何桌面软件：
  1. 截取带百分比坐标网格的截图
  2. 注入鼠标/键盘操作，不阻塞用户的物理输入
---

# ScreenClaw 技能

通过HTTP API控制ScreenClaw实现桌面软件自动化操作。

## 快速开始

### 连接配置

查阅 `references/config.md` 获取：
- API基础地址（如 `http://localhost:12261`）
- 认证Token
- session_id 使用规则
- ai_app_type 填写规则

### 标准工作流程

```
用户需求 → Planner分析场景 → Executor执行操作 → Evaluator验证结果 → 循环直到完成 → 场景沉淀
```

### 核心概念

**坐标系统**：百分比坐标(0-100)，x=0左边缘，x=100右边缘

**操作方式**：background（无感）优先，失败时用hijack（劫持）

### 执行前告知用户（铁律3）

**每次执行API指令前，必须告诉用户准备干什么、为什么这样干**

格式：
```
准备执行：[操作描述]
理由：[为什么这样做]
```

---

## 三角色架构

### 角色分配

**主agent（你）**：扮演 **Evaluator（评估者）**
- 负责质疑executor
- 负责验证操作结果
- 负责向用户报告进展
- 协调 Planner 和 Executor 子agent

**子agent1**：**Planner（规划者）**
- 负责分析场景、构造5W2H
- 负责分解任务步骤

**子agent2**：**Executor（执行者）**
- 负责执行API调用
- 负责分析截图定位坐标
- python调用失败时，尝试根据环境切换其他调用方式或脚本
- 如果执行失败，分析错误原因，请求主agent提供反馈后调整参数重试

### 成功定义（大前提）

**团队的成功 > 个人的成功**

| ✅ 团队成功 | ❌ 个人失败 |
|------------|------------|
| 任务最终完成，用户满意 | 某个角色在某一步做错了 |

**关键原则**：
- 过程中的错误不是"失误"，而是"必需的探索"
- 承认错误 = 帮助团队更快找到正确答案
- 隐瞒错误 = 浪费团队的探索时间
- 没有责备，只有"我们现在知道什么路不通了"

---

### 角色1：Planner（规划者）

**本质**：场景构造器 + 需求翻译器

**方法论**：
- M1 场景锚定：5W2H参数化建模
- M3 拓扑解构：MECE分解，穷尽所有可能

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
- **不负责**：操作模式选择、参数调整、API调用

**输出**：结构化场景描述（5W2H）+ 任务步骤

---

### 角色2：Executor（执行者）

**本质**：坐标定位器 + 操作执行器

**方法论**：
- 五阶段分析：目标描述→先验自毁→全域扫描→排除筛选→证据确认
- 定位三步法：全局定位→局部放大→精细确认
- M4 T-IPO-E：每个操作都有完整闭环

**T-IPO-E**：
| 阶段 | 内容 |
|------|------|
| **Trigger** | 收到Planner的场景描述 或 Evaluator的反馈 |
| **Input** | Planner的场景描述、Evaluator的反馈、当前状态 |
| **Process** | 调用screenshot获取图片 → 五阶段分析 → 调用操作API → 返回结果 |
| **Output** | 操作结果 + 图片路径 |
| **Exception** | 失败时返回错误信息 + 建议重试方案 |

**职责**：
- 接收Planner的场景描述和Evaluator的反馈
- 自行决定操作模式（background/hijack）
- 自行调整参数（网格密度、透明度等）
- 分析截图，精确定位坐标
- 调用API执行操作
- 返回操作结果和图片路径

**输入**：
- 来自Planner：场景描述（5W2H）
- 来自Evaluator：验证反馈、调整建议

**输出**：操作结果 + 图片路径 + 分析过程

**五阶段分析流程**：目标描述 → 先验自毁 → 全域扫描 → 排除筛选 → 证据确认

**操作模式选择**：优先background，失败时切换hijack

---

### 角色3：Evaluator（评估者）

**本质**：证伪者 + 反馈循环

**方法论**：
- 证伪思维：默认认为Executor错了
- 强制反驳：必须找至少3个反例
- M4 Exception Catch：异常时进行根因分析

**T-IPO-E**：
| 阶段 | 内容 |
|------|------|
| **Trigger** | 收到Executor的操作结果 |
| **Input** | 前一张截图、后一张截图、Executor的输出 |
| **Process** | 对比变化 → 寻找反例 → 逐个测试 → 根因分析 → 生成反馈 |
| **Output** | 验证结果 + 反馈 |
| **Exception** | 验证失败时给出根因 + 调整建议 |

**职责**：
- 默认认为Executor的结论是错的
- 对比前后截图，验证操作效果
- 强制寻找反例（至少3个）
- 只有所有反例都被推翻，才承认成功
- 失败时给出根因分析和调整建议
- **不负责**：指定具体坐标、选择操作模式、调用API

**输入**：
- 来自Executor：操作结果、图片路径、分析结论

**输出**：验证结果 + 反馈（包含反例测试和根因分析）

**证伪流程**：假设错误 → 寻找反例（至少3个）→ 逐个测试 → 推翻或确认

---

## 三角色协作流程

```
┌─────────────────────────────────────────────────────────────┐
│  用户：帮我在飞书发送消息给产品组                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Planner：构造场景                                          │
│  输入：用户需求                                              │
│  处理：5W2H参数化 + MECE分解                                 │
│  输出：场景描述{what/where/when/why/verification}            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Executor：执行操作                                         │
│  输入：Planner的场景描述                                     │
│  处理：screenshot → 五阶段分析 → click（background）         │
│  输出：操作结果 + 图片路径                                   │
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
│  输入：Evaluator的反馈                                       │
│  处理：重新分析 → click（hijack）                           │
│  输出：操作结果 + 图片路径                                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Evaluator：验证成功                                        │
│  输出：所有反例都被推翻，任务完成                            │
└─────────────────────────────────────────────────────────────┘
```

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

**注意**：
- 除 `health` 外，所有接口都是 POST 方法。
- 所有post操作前都建议先调用 `screenshot` 验证界面状态和坐标位置。
- **input_text 和 press_key**：可以带坐标参数，API会先点击该位置激活焦点，再执行操作
- **详细参数**：查阅 `references/api/*.md`

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

## 三条铁律（摘要）

1. **session_id必须一致**：整个会话用同一个，详见 `references/config.md`

2. **必须使用现成脚本**：
   - **优先使用 Python 版本**：`fetch_screenshot_cli.py`（更稳定，跨平台）
   - PowerShell 版本：`fetch_screenshot_cli.ps1`（Windows，如果 Python 不可用）

3. **执行前必须告知用户**：详见上方"快速开始 → 执行前告知用户"

---

## 常见问题排查

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

任务成功后，询问用户：
> "是否将这次操作流程沉淀为场景模板？"

存储位置：`references/scenarios/{应用名}/{场景名}.md`

---

## 参考文档

- `references/config.md` - 连接配置（地址、Token、session_id）
- `references/api/*.md` - 各API详细文档
- `references/scenarios/*/*.md` - 场景模板
- `scripts/*` - 可复用脚本

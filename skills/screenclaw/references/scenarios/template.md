---
name: {应用名}-{场景名}
version: 1.0
description: 什么情况下应该使用该场景模板。什么情况下不适用。
update: {YYYY-MM-DD}
---

> **元数据规则**：
> - `version`：初始创建为 1.0。每次修改场景内容时递增（小改为 x.1，大改为 x+1.0）
> - `update`：每次修改时更新为当天日期
> - `description`：是模板检索的关键字段，需准确描述适用和不适用场景

# {应用名} - {场景名}

## 目标说明

- 进程名：xxx.exe
- 窗口标题关键词：xxx
- 来源：AI 实操沉淀 / 用户录制 `record/record_YYYYMMDD_HHmmss` 归纳
- 窗口清单：

| group_key | 窗口名 | 类型 | 获取方式 | window_info | 录制步骤 | 可用操作 | 说明 |
|-----------|--------|------|----------|-------------|----------|----------|------|
| app_main | 应用主窗口 | 主窗口 | get_window_list 标题关键词 | source_width=1920, source_height=1032, scale_factor=1.0 | 定位/验证 | screenshot, activate | 主窗口锚点；若没有固定坐标落在主窗口，不写 click/input_text |
| app_content_child | 应用内容子窗口 | 子窗口 | include_children=true 后按子窗口标题和截图确认 | source_width=1936, source_height=1048, scale_factor=1.0 | 1,2,3 | click | 实际固定坐标所在窗口；例如 Chrome Legacy Window |
| system_dialog | 系统弹窗 | 主窗口/子窗口 | 用标题关键词通过 get_window_list 查找并截图确认 | source_width=1600, source_height=900, scale_factor=1.0 | 4,5,6 | click, input_text | 如文件选择框，进程名可能不可靠 |

> **尺寸比例**：从截图尺寸计算（宽/高），用于判断沉淀坐标是否仍适用。如果当前截图的比例与沉淀比例不一致，说明窗口尺寸发生了变化，固定坐标可能不准确，需重新截图定位。部分窗口不需要尺寸比例，例如微信的搜索进程，需要截图实时判断坐标。
> **窗口锚点**：模板中不要复用历史 `window_id`。执行时通过进程名、窗口标题关键词、主/子窗口关系和截图内容重新定位。文件选择框、系统弹窗等进程名不可靠时，优先用标题关键词定位。
> **窗口类型**：从录制沉淀时，`window_id != main_window_id` 必须写成子窗口；主窗口可用于定位和验证，实际点击坐标应使用录制对应的子窗口变量。业务名称不能覆盖机械类型，例如 `Chrome Legacy Window` 不能写成主窗口。
> **坐标来源**：固定坐标必须引用窗口清单中的 `window_info`。执行时用当前截图返回的 `window_info` 调用 `scripts/coord_adapt.*`，得到候选坐标和 `direct/verify/relocate` 决策。

## 场景业务流概述

**场景描述**（5W2H）：
- Who：场景的主要对象是谁
- What：做什么
- Where：在哪个窗口、哪个区域操作
- When：什么条件下触发
- Why：场景的目的是什么
- How：大致步骤
- How Much：预期耗时/复杂度

> **补充环境上下文**：描述场景运行时的环境假设。AI需要理解这些前提条件才能正确执行。

**执行状态约定**：
- 执行本模板时，在计划或上下文中维护 `active_template_path/current_node/completed_nodes/next_node`
- 每完成一个节点，更新 `completed_nodes` 和 `next_node`
- 模板较长、上下文变长、收到 `SELF_CHECK_REQUIRED` 或执行高风险节点前，重新打开本模板确认当前节点
- 模板节点多次失败、当前截图与模板明显不符、窗口或坐标复用失效时，将该节点标记为“模板节点降级”，从当前截图重新理解 UI、读取坐标、推理动作并验证结果；降级不等于放弃模板，仍保留模板目标和已完成节点

**全景业务流**：
```
节点1 → 节点2 → 节点3 → 完成
                ↓（分支：条件不满足时）
           节点2b → 节点3
```

## 常用截图参数

场景中需要截图定位时，默认先使用服务端自适应参数，不需要在每个节点重复说明。只有某个节点需要固定覆盖参数时，才填写下表：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| color_mode | grayscale | 灰度模式，彩色网格更醒目 |
| grid.density_x | 不传 | 目标没有被竖线覆盖时才显式传 |
| grid.density_y | 不传 | 目标没有被横线覆盖时才显式传 |
| coordinate.number_density | 不传 | 周围交叉点缺少数字时才显式传 |
| coordinate.number_size | 不传 | 数字看不清时才显式传 |

> 仅当某个节点的截图需求与默认参数不同时，才在该节点的 P（处理）中单独说明。例如：需要看清原始色彩时 `color_mode=color`，目标没有被交叉点覆盖时 `grid.density_x=3.3 grid.density_y=5`。

## 业务流节点详解

### 节点1：{节点名称}

**操作层级**：主窗口 / 子窗口 / 系统弹窗 / 桌面级

**T（触发）**：前置条件

**I（输入）**：需要什么信息。如果输入内容不够，向用户索取。中文、IME 或输入法录制文本可能是拼音/英文中间态，应写成语义变量，例如 `{用户输入}`、`{搜索关键词}`、`{目标文件名}`、`{完整路径}`。

**P（处理）**：操作内容。坐标说明：

> **固定坐标**（可固化，直接使用）：
> | 操作 | 坐标 | 使用窗口组 | 操作层级 | 操作模式 | 等待 | 说明 |
> |------|------|------------|----------|----------|------|------|
> | click | 15.2x35.6 | app_content_child | 子窗口 | background | 200ms | 点击搜索按钮 |
>
> **动态坐标**（不可固化，需截图定位）：
> - 关注区域：左侧聊天列表（约占1/3宽度）
> - 识别特征：深灰色背景表示选中，白色背景未选中
> - 定位要点：根据文字内容匹配目标
> - 动态输入：用 `{用户输入}` 标记，例如 `{联系人}`、`{文件名}`、`{发布文案}`
>
> **状态准备**（菜单/浮层/hover 态）：
> - 截图确认目标菜单或浮层是否已展开
> - 如果未展开，先 hover、mouse_move 或点击父按钮展开
> - 展开后重新截图或直接点击目标项，取决于该状态是否稳定
>
> **跨进程/跨窗口**（执行后再验证）：
> - 执行前：截图确认即将点击的对象正确
> - 执行：点击或拖拽触发新窗口/系统弹窗
> - 执行后：重新 `get_window_list` 定位新窗口，再截图确认结果

**O（输出）**：正常完成无需列出。仅当需要截图验证才能继续下一步时说明验证标准。

> 输出状态必须有截图证据支撑。如果录制或执行截图没有显示最终成功标志，只写“需继续截图确认 xxx 出现”，不要声明已完成。

**E（异常）**：指引到"常见问题"具体条目。

> 如果该节点按模板执行多次失败，或截图事实证明模板已过期/不适配当前窗口，降级为通用视觉流程：重新截图理解当前 UI，必要时裁剪放大和 marker 反验，确定新坐标或新路径后继续执行，并在成功后记录可反哺模板的差异。

---

（每个节点重复上述结构）

## 节点指令

按业务流节点顺序，列出可直接执行的 API 调用指令。不含截图指令。

**坐标复用检查**：
- 遇到某个窗口组的第一个固定坐标时，先截图获取当前 `window_info`。
- 调用 `scripts/coord_adapt.py|ps1|sh`，传入模板 `window_info`、当前 `window_info` 和模板坐标。
- `direct`：使用返回的 `candidate.x/y` 执行。
- `verify`：用返回的 `candidate.x/y` 打 marker 反验，确认后执行。
- `relocate`：不复用固定坐标，按动态坐标说明重新截图定位。
- 同一窗口组缓存一次；窗口尺寸、缩放率、窗口 ID、显示器或页面布局变化后重新计算。

**组合规则**：
- **固定坐标节点**：直接组合成 batch 指令
- **动态坐标节点（需验证）**：截图定位 → 执行 → 截图验证结果 → 再继续
- **动态坐标节点（高可靠）**：截图定位 → 获取坐标后，与后续固定坐标节点一起 batch 执行。仅在历史执行从未出错时标记为"高可靠"
- **高风险动态坐标**：截图定位 → marker 反验 → 执行 → 截图验证
- **桌面级节点**：先 `desktop_get_monitors_list`，按当前目标所在显示器截图定位，不直接假设录制时的 `monitor_index`
- **跨进程节点**：先执行触发动作，再重新定位新窗口并截图确认；不要在旧窗口上验证新窗口结果
- **失败兜底**：同一节点多次失败、窗口/坐标复用失效或截图与模板明显不符时，不继续重复模板指令；将该节点降级为通用截图推理，重新定位坐标或路径，验证后再决定是否回到后续模板节点
- **坐标精度**：保留小数坐标，例如 `15.2`、`35.6`，不要改写成整数

```bash
# 节点1坐标复用检查（窗口组：主窗口）
python scripts/coord_adapt.py \
  source.width={source_width} source.height={source_height} source.scale_factor={source_scale_factor} \
  current.width={current_width} current.height={current_height} current.scale_factor={current_scale_factor} \
  point.x=15.2 point.y=35.6 risk=normal

# 按 coord_adapt 输出的 candidate.x/y 和 decision 决定 direct/marker/relocate

# 节点1+2 组合（全部固定坐标，batch执行）
python scripts/screenclaw.py batch api_url={api_url} token={token} \
  ai_app_type={ai_app_type} session_id={session_id} \
  step.0.action=click \
  step.0.params.window_id={window_id} \
  step.0.params.main_window_id={main_window_id} \
  step.0.params.x={candidate_x} step.0.params.y={candidate_y} \
  step.1.action=wait step.1.params.duration_ms=300

# 截图验证节点2的输出，确认能进入节点3

# 节点3（动态坐标，高可靠：截图定位后，与节点4一起batch）
# 先截图读取坐标 → 然后batch执行节点3+4

# 跨进程节点：点击后打开系统弹窗，再重新定位弹窗
python scripts/screenclaw.py batch api_url={api_url} token={token} \
  ai_app_type={ai_app_type} session_id={session_id} \
  step.0.action=click \
  step.0.params.window_id={window_id} \
  step.0.params.main_window_id={main_window_id} \
  step.0.params.x=51.5 step.0.params.y=52.2 \
  step.1.action=wait step.1.params.duration_ms=500

# 然后调用 get_window_list include_children=true keyword=打开，定位新窗口后截图验证

# 节点5（动态坐标，需验证：执行后必须截图确认结果）
```

> **说明**：
> - 指令中用 `{xxx}` 标记需要运行时填充的参数
> - 每段指令前用注释说明这段指令的目的和上下文
> - 动态坐标节点在指令中以 `{从截图读取}` 标记
> - 固定坐标节点在指令中以 `{candidate_x}`、`{candidate_y}` 标记，表示 `coord_adapt` 返回的候选坐标；`direct` 时也使用候选坐标
> - batch 中 `window_id`、`main_window_id`、`monitor_index` 都写在每个 `step.N.params.*` 下，不写在 batch 顶层
> - 子窗口操作使用明确变量名，例如 `{publish_content_child_window_id}` 和 `{publish_main_window_id}`，不要用泛化 `{window_id}` 导致主/子窗口混填
> - 如果固定坐标表中的“使用窗口组”是子窗口，指令中的 `step.N.params.window_id` 必须填子窗口变量，`step.N.params.main_window_id` 填所属主窗口变量
> - 桌面级 `desktop_press_key` 使用 `keys` 参数；窗口级 `press_key` 使用 `key` 参数
> - 所有示例使用 `scripts/screenclaw.py` 的点号路径；PowerShell/bash 只替换入口，不改变参数格式

## 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| xxx操作无效 | 窗口ID不正确 | 使用子窗口1重试 |

## 参考文档

- 应用公共知识：`app_wiki.md`
- 模板格式：`template.md`
- batch接口：`references/api/batch.md`
- 其它场景模板：同目录下的其它 .md 文件

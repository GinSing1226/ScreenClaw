---
name: scenarios
description: 场景模板的使用说明和沉淀流程
---

# 场景模板使用说明

## 目录结构

```
scenarios/
├── README.md                  ← 本文件
├── template.md                ← 场景沉淀的模板格式
├── app_wiki_template.md       ← 应用知识沉淀的模板格式
├── {应用名}/                  ← 按应用英文/拼音名划分
│   ├── app_wiki.md            ← 应用级公共知识（必有，创建应用目录时必须同步创建）
│   └── {场景名}.md            ← 场景模板（按用户常用语言命名）
```

## 检索流程

执行任务前，按以下顺序检索是否已有场景沉淀：

1. **按应用目录名匹配** — 根据目标应用的英文/拼音名，用 Bash 列出文件（Glob 无法访问工作区外的技能目录）：
   - bash：`find "<技能目录>/references/scenarios/{应用名}" -name "*.md"`
   - PowerShell：`Get-ChildItem -Path "<技能目录>/references/scenarios/{应用名}" -Recurse -Filter "*.md" | Select-Object -ExpandProperty FullName`
   - 匹配方式：目录名与应用进程名或常用英文名匹配（如 WeChat.exe → wechat）
2. **按场景文件名匹配** — 如果找到应用目录，读取该目录下所有场景文件（不含 app_wiki.md）的元数据 description，判断是否匹配当前任务
3. **按 app_wiki 扩展匹配** — 如果步骤1找不到应用目录，读取所有 `scenarios/*/app_wiki.md` 的元数据（含进程名、别名），判断是否有匹配的应用
4. **无匹配** — 说明该应用没有沉淀，按全新任务执行

## 沉淀流程

任务成功后，主动询问用户是否沉淀。用户确认后：

1. **确定沉淀的应用名**：
   - 直接应用（如微信、记事本）→ 用应用名建目录
   - 模拟器/投屏内的应用（如 MuMu 里的原神、scrcpy 投屏操作手机微信）→ **询问用户要沉淀的是哪个应用**，用被操作的应用名建目录，而非模拟器/投屏工具名
   - 不确定时，直接问用户："沉淀的应用名用什么？"

2. **判断沉淀类型**：

| 情况 | 判断方式 | 操作 | 创建路径 |
|------|----------|------|----------|
| 已有应用，已有同类场景 | 找到应用目录且场景元数据匹配 | 修改已有场景文件 | 直接修改已有文件 |
| 已有应用，未有同类场景 | 找到应用目录但无匹配场景 | 新建场景文件到该目录 | `scenarios/{应用名}/{场景名}.md` |
| 未有应用 | 步骤3也无匹配 | 新建应用目录 + 全套文件 | `scenarios/{应用名}/` 目录 + `app_wiki.md`（按 `app_wiki_template.md` 格式） + `{场景名}.md` |

3. **创建/修改文件** — 场景文件按 `template.md` 格式填写；app_wiki 按 `app_wiki_template.md` 格式填写。已有 app_wiki 的公共知识不在场景文件中重复
4. **更新 app_wiki** — 如果沉淀过程中发现了新的应用级公共知识，同步更新 app_wiki.md
5. **文件路径** — 所有文件创建在 `skills/screenclaw/references/scenarios/` 目录下

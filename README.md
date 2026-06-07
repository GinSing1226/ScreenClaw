# ScreenClaw

<div align="center">

**睇虾 — AI 应用的可视化操作必备伴侣**

让任何多模态大模型识别网格坐标，自动化操作任何软件

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tauri 2.0](https://img.shields.io/badge/Tauri-2.0-ffcf131.svg)](https://tauri.app/)

[English](./README_EN.md) | [Agent Guide](./README_AGENT.md) | [Demo Video](https://www.bilibili.com/video/BV1WJD8BUEnh)

</div>

---

## 📖 什么是 ScreenClaw？

ScreenClaw（睇虾）是一款本地运行的"中间件"程序，它充当 AI 应用与桌面软件之间的桥梁。

**核心创新**：通过在截图中叠加百分比坐标网格，让任何多模态大模型都能精确识别界面元素位置，无需专门训练 UI 模型。

AI 应用通过 HTTP API 可以：
- 📸 **截图并绘制坐标网格** — 精确定位界面元素位置
- 🖱️ **注入鼠标键盘操作** — 后台无感控制，不影响用户使用
- 🔄 **自动化任何软件** — 即使软件没有 API 或命令行接口

**关键特性**：全程不抢夺用户的物理鼠标和键盘，你可以在看电影、写文档的同时，让 AI 在后台完成自动化任务。

---

## ✨ 核心特性

### 🖥️ 后台无感操作
采用 `background` 模式，通过 PostMessage/SendMessage 注入事件，不会激活窗口或抢占焦点，用户毫无感知。

### 📐 百分比坐标网格
- 让任何多模态大模型有了精确定位能力，且识别速度更快
- 基于百分比（0-100）的坐标系统，只要窗口比例不变，适用于任何大小的窗口
- 不同分辨率、不同窗口尺寸都能复用相同的坐标

### 💻 操作电脑软件
支持自动化操作大部分电脑软件，特别是不提供 API、CLI 等自动化工具的传统桌面软件。

### 📱 操作手机
支持自动化操作手机模拟器、官方手机助手（各家手机厂商的多屏协同/手机投屏）：
- 无需 ADB
- 无需 root
- 无需虚拟机
- 无需专门 UI 大模型就能操作手机 APP

### 💎 沉淀复用
- 支持将成功的任务流程沉淀为场景模板，下次直接复用
- 接入 OpenClaw 等个人 AI 助手后，个性化数据在本地留存
- AI 会越来越懂你，效率越来越高

### 🔒 安全可控
- Token 认证机制
- 禁止访问进程黑名单，避免 AI 访问敏感应用
- Hijack 操作需用户确认

### 🎮 托管模式
用户主动要求时进入，AI 完全控制电脑，物理输入，无需逐次确认。适合需要持续操作的场景（如中文输入）。通过快捷键 `Ctrl+Alt+Z` 可随时退出。

---

## 🚀 快速开始

### 从源码运行（开发环境）

**一行部署和启动**：
```bash
git clone https://github.com/GinSing1226/ScreenClaw.git && cd ScreenClaw && pip install -r python/requirements.txt && npm install && npm run tauri dev
```

**已有项目**：
```bash
# 安装依赖（首次或依赖更新时）
pip install -r python/requirements.txt && npm install

# 运行开发环境1 建议以管理员身份启动终端
npm run tauri dev

# 或运行开发环境2
npx tauri dev
```

### 下载 Release 运行（生产环境）

1. 前往 [Releases](https://github.com/GinSing1226/ScreenClaw/releases) 页面
2. 下载最新版本的 Windows 压缩包
3. 解压后双击 `ScreenClaw.exe` 启动

### 启动服务

1. 应用启动后，点击"启动服务"按钮
2. 查看连接信息：
   - 本机访问：`http://127.0.0.1:12261`
   - 局域网访问：`http://192.168.x.x:12261`

### 安装 Skill

在 Claude Code、OpenClaw、OpenCode、Codex 等 AI Agent 工具中执行：

```bash
npx skills add GinSing1226/ScreenClaw
```

安装后，AI 即可自动调用 ScreenClaw API 进行桌面软件自动化操作。

---

## 📚 API 清单

| API | 用途 | 说明 |
|-----|------|------|
| `health` | 验证服务是否可连接 | 操作前的第一步检查 |
| `get_window_list` | 查找目标窗口 | 获取 window_id（后续操作必需） |
| `screenshot` | 查看界面状态、定位坐标 | 每次操作后验证结果 |
| `click` | 触发功能、进入页面 | 普通点击操作 |
| `long_press` | 触发长按功能 | 拖拽起点、显示菜单等 |
| `swipe` | 触摸式滑动 | 翻页、切换标签、拖拽 |
| `scroll` | 鼠标滚轮滚动 | 浏览长内容、列表 |
| `right_click` | 打开上下文菜单 | 调用快捷方式 |
| `hover` | 触发悬停效果 | 显示 tooltip、隐藏 UI 元素 |
| `input_text` | 输入文本内容 | 填表、搜索等 |
| `press_key` | 触发快捷键 | Ctrl+C 复制、Enter 确认等 |
| `wait` | 等待 UI 稳定 | 等待动画、加载完成 |
| `batch` | 执行多步骤流程 | 减少网络请求、固定序列 |
| `drag` | 拖拽操作 | 文件拖放、元素拖动，支持速度控制 |
| `mouse_move` | 鼠标相对移动 | 游戏视角控制，仅 hijack/delegated |
| `scroll_screenshot` | 滚动长截图 | 自动滚动拼接，生成长图 |
| `delegated` | 进入/退出托管模式 | 用户主动要求完全控制时 |

---

## 🔧 API 使用示例

### 通用请求头

所有 API 请求都需要携带：

```bash
Authorization: Bearer {token}
Content-Type: application/json
```

### 1. 健康检查

```bash
curl -X GET http://127.0.0.1:12261/api/health
```

### 2. 获取窗口列表

```bash
curl -X POST http://127.0.0.1:12261/api/get_window_list \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "keyword": "notepad",
    "include_children": true,
    "children_filter": "titled"
  }'
```

### 3. 截图（带坐标网格）

```bash
curl -X POST http://127.0.0.1:12261/api/screenshot \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "coordinate_type": "grid",
    "color_mode": "grayscale",
    "density": 5.0,
    "opacity": 50,
    "color": "#ff0000",
    "number_density": 2,
    "number_decimal": 0,
    "number_size": 12,
    "number_color": "#ff0000",
    "number_opacity": 100
  }'
```

### 4. 点击

```bash
curl -X POST http://127.0.0.1:12261/api/click \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "x": 50.0,
    "y": 30.0,
    "action_method": "background"
  }'
```

### 5. 长按

```bash
curl -X POST http://127.0.0.1:12261/api/long_press \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "x": 50.0,
    "y": 50.0,
    "duration_ms": 500,
    "action_method": "background"
  }'
```

### 6. 滑动

```bash
curl -X POST http://127.0.0.1:12261/api/swipe \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "start_x": 50.0,
    "start_y": 80.0,
    "end_x": 50.0,
    "end_y": 20.0,
    "action_method": "background"
  }'
```

### 7. 滚动

```bash
curl -X POST http://127.0.0.1:12261/api/scroll \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "x": 50.0,
    "y": 50.0,
    "delta": -120,
    "action_method": "background"
  }'
```

### 8. 右键点击

```bash
curl -X POST http://127.0.0.1:12261/api/right_click \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "x": 50.0,
    "y": 50.0,
    "action_method": "background"
  }'
```

### 9. 鼠标悬浮

```bash
curl -X POST http://127.0.0.1:12261/api/hover \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "x": 50.0,
    "y": 50.0,
    "duration_ms": 500,
    "action_method": "hijack"
  }'
```

### 10. 输入文本

```bash
curl -X POST http://127.0.0.1:12261/api/input_text \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "x": 50.0,
    "y": 50.0,
    "text": "Hello World\n",
    "action_method": "hijack"
  }'
```

### 11. 按键

```bash
curl -X POST http://127.0.0.1:12261/api/press_key \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "key": "ctrl c",
    "action_method": "background"
  }'
```

### 12. 等待

```bash
curl -X POST http://127.0.0.1:12261/api/wait \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "duration_ms": 1000
  }'
```

### 13. 批量执行

```bash
curl -X POST http://127.0.0.1:12261/api/batch \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "instructions": [
      {"action": "click", "params": {"x": 50, "y": 35, "action_method": "background"}},
      {"action": "wait", "params": {"duration_ms": 200}},
      {"action": "input_text", "params": {"x": 50, "y": 35, "text": "hello", "action_method": "hijack"}},
      {"action": "wait", "params": {"duration_ms": 300}},
      {"action": "screenshot", "params": {"coordinate_type": "no"}}
    ]
  }'
```

### 14. 托管模式

```bash
curl -X POST http://127.0.0.1:12261/api/delegated \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "action": "enter"
  }'
```

退出托管模式：将 `"action": "enter"` 改为 `"action": "exit"`，或按快捷键 `Ctrl+Alt+Z`。

### 15. 拖拽

```bash
curl -X POST http://127.0.0.1:12261/api/drag \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "start_x": 30.0,
    "start_y": 50.0,
    "end_x": 70.0,
    "end_y": 50.0,
    "duration_ms": 500,
    "action_method": "background"
  }'
```

### 16. 鼠标移动

```bash
curl -X POST http://127.0.0.1:12261/api/mouse_move \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "delta_x": 200,
    "delta_y": 0,
    "duration_ms": 300,
    "action_method": "hijack"
  }'
```

### 17. 滚动长截图

```bash
curl -X POST http://127.0.0.1:12261/api/scroll_screenshot \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "main_window_id": 1001,
    "max_scrolls": 20,
    "scroll_percent": 0.85,
    "scroll_wait": 1.0,
    "action_method": "hijack"
  }'
```

---

## 🎯 适用场景

### 自动化可视化测试
模拟人工操作可视化界面，沉淀测试用例，自动打开 F12 管理报错。

### 自动操作无网页版、无 API、无 CLI 的电脑软件
传统 ERP、OA 系统、专业工具软件等，只要能显示在屏幕上就能操作。

### 手机模拟器、手机投屏助手
对于大部分普通人，现阶段的 ADB、虚拟机、docker 等方案的自动化手机太麻烦，门槛太高。专门的 AI 手机又已停产。ScreenClaw 让你直接操作投屏/模拟器界面。

### 复杂任务自动化
专用的 UI 大模型通常参数量较低，难以理解复杂任务，难以尝试长时程执行任务。而 ScreenClaw 能让 SOTA 级别的多模态大模型（如 GPT-4V、Claude 3.5 Sonnet）自动化操作软件。

### 与其他工具对比

| 场景 | 推荐工具 | ScreenClaw 作用 |
|------|----------|----------------|
| 浏览器自动化 | Playwright、CDP、agent-browser | 补充：模拟人工走查操作、获取控制台报错 |
| 传统 RPA | UiPath、Power Automate | 更智能：AI 自动识别坐标，无需人工配置 |

---

## 💡 平台说明

### 执行方（运行 ScreenClaw 的机器）
**推荐：Windows**

- ✅ 支持无感截图（后台截图，不抢占前台）
- ✅ 支持无感鼠标和键盘操作（不影响用户使用）
- ✅ 拥有丰富的手机模拟器（如 MuMu、蓝叠、夜神等）
- ✅ 各大手机厂商的投屏软件（华为多屏协同、小米跨屏协作等）
- ✅ 能自动化大部分手机 APP

### 调用方（运行 AI 应用的机器）
**支持：Windows / macOS / Linux**

通过 HTTP API 调用，跨平台无限制。

### 部署模式
- **本地模式**：执行方和调用方是同一台机器
- **局域网模式**：不同机器，需在同一局域网内

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────┐
│         外部 AI 应用                         │
│  (Claude Code / openclaw / 其他 Agent)         │
└──────────────────┬──────────────────────────┘
                   │ HTTP API
                   ▼
┌─────────────────────────────────────────────┐
│         Python 后端服务                      │
│       FastAPI :12261                         │
│  ┌───────┬────────┬────────┬────────┐      │
│  │ API层 │ Core层 │Platform│Service │      │
│  └───────┴────────┴────────┴────────┘      │
└──────────────────┬──────────────────────────┘
                   │ 子进程
┌──────────────────▼──────────────────────────┐
│         Tauri 桌面应用                       │
│  监控面板 │ 系统设置 │ 托盘图标               │
└─────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Tauri 2.0 + Vue 3 + TypeScript |
| 后端 | Python 3.11 + FastAPI + Uvicorn |
| 截图 | pywin32 / mss |
| 操作注入 | pywin32 (PostMessage) / pyautogui (SendInput) |
| 网格绘制 | Pillow (PIL) |

---

## 📁 项目结构

```
screenClaw/
├── python/                   # Python 后端
│   ├── app/
│   │   ├── api/             # API 路由
│   │   ├── core/            # 核心业务逻辑
│   │   ├── platform/        # 平台适配层
│   │   ├── models/          # 数据模型
│   │   ├── services/        # 服务层
│   │   ├── scripts/         # API 调用脚本
│   │   └── utils/           # 工具函数
│   └── main.py              # 入口文件
│
├── src-tauri/               # Tauri 后端（Rust）
│   └── src/
│       ├── commands.rs      # Tauri 命令
│       └── main.rs          # 入口
│
├── src/                     # Vue 前端
│   ├── components/          # 组件
│   ├── composables/         # 组合式函数
│   └── main.ts              # 入口
│
├── skills/                  # AI Skill
│   └── screenclaw/
│       ├── SKILL.md         # 技能定义（完整使用指南）
│       └── references/      # API 文档和场景模板
│
└── data/                    # 数据目录
    └── config.json          # 配置文件（自动创建）
```

---

## ⚙️ 配置说明

### ScreenClaw 服务配置
位于 `data/config.json`（应用初始化时自动创建）：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 12261,
    "token": "your-token-here",
    "local_ip": "192.168.x.x"
  }
}
```

### AI Skill 连接配置
位于技能目录 `{skill-dir}/references/config.md`，用于 AI 应用连接 ScreenClaw 服务。

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 12261,
    "token": "your-token-here",
    "local_ip": "192.168.x.x"
  }
}
```

| 配置项 | 说明 |
|--------|------|
| `host` | 绑定地址，0.0.0.0 允许局域网访问 |
| `port` | HTTP 服务端口 |
| `token` | API 认证令牌 |
| `local_ip` | 自动检测的局域网 IP |

---

## 🔒 安全说明

- 所有 API 请求需要 Token 认证
- Hijack 模式操作会弹出确认窗口
- 可配置禁止访问的进程黑名单
- 仅允许局域网和本机访问

---

## 📖 更多文档

- [Skill 使用指南](./skills/screenclaw/SKILL.md) — 完整的 API 文档和使用方法论

---

## 🗺️ 未来规划

- 🎯 **提高识别率** — 通过技能优化和场景模板沉淀，提升多模态大模型的初次识别准确率
- 🔄 **更多 RPA 动作** — 扩展支持的自动化操作类型，覆盖更多使用场景
- 🖥️ **桌面级操作** — 直接对桌面截图和操作，不绑定进程，可操作任何可见内容（会抢夺用户鼠标和键盘）
- 📦 **场景模板库** — 封装更多常用软件的场景模板，开箱即用

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star 支持一下！**

**睇虾 — 让任何多模态大模型操作任何屏幕**

Made with ❤️ by GinSing

</div>

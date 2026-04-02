# ScreenClaw

<div align="center">

**Di Xia — The Essential Visual Operation Companion for AI Apps**

Empowering any multimodal LLM to recognize grid coordinates and automate any software

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tauri 2.0](https://img.shields.io/badge/Tauri-2.0-ffcf131.svg)](https://tauri.app/)

[中文](./README.md) | [Agent Guide](./README_AGENT.md)

</div>

---

## 📖 What is ScreenClaw?

ScreenClaw (Di Xia) is a locally running "middleware" program that bridges AI applications and desktop software.

**Core Innovation**: By overlaying percentage-based coordinate grids on screenshots, it enables any multimodal LLM to precisely identify UI element positions without requiring specialized UI model training.

Through HTTP API, AI applications can:
- 📸 **Capture screenshots with coordinate grids** — Precisely locate UI element positions
- 🖱️ **Inject mouse and keyboard operations** — Background control without affecting user activity
- 🔄 **Automate any software** — Even without API or command line interface

**Key Feature**: It never seizes your physical mouse and keyboard. You can watch movies or write documents while AI completes automation tasks in the background.

---

## ✨ Core Features

### 🖥️ Background Operation
Using `background` mode with PostMessage/SendMessage to inject events, it never activates windows or steals focus—users won't feel a thing.

### 📐 Percentage Coordinate Grid
- Gives any multimodal LLM precise positioning capability with faster recognition
- Percentage-based (0-100) coordinate system that works with any window size as long as the aspect ratio remains unchanged
- Same coordinates work across different resolutions and window sizes

### 💻 Control Desktop Software
Automates most desktop software, especially traditional software without API, CLI, or other automation tools.

### 📱 Control Mobile Devices
Automate mobile emulators and official phone assistants (multi-screen collaboration/screen casting from various manufacturers):
- No ADB needed
- No root needed
- No virtual machine needed
- No specialized UI LLM needed to operate mobile apps

### 💎 Knowledge Accumulation & Reuse
- Save successful task workflows as scenario templates for next-time reuse
- When integrated with personal AI assistants like OpenClaw, personalized data stays local
- AI gets smarter about your preferences, boosting efficiency over time

### 🔒 Safe and Controllable
- Token authentication mechanism
- Blocked process blacklist to prevent AI from accessing sensitive applications
- Hijack operations require user confirmation

---

## 🚀 Quick Start

### One-Line Deployment

```bash
git clone https://github.com/GinSing1226/ScreenClaw.git && cd ScreenClaw && pip install -r python/requirements.txt && npm install && npm run tauri dev
```

### Start Service

1. Double-click to launch ScreenClaw application
2. Click "Start Service" button
3. View connection information:
   - Local access: `http://127.0.0.1:12261`
   - LAN access: `http://192.168.x.x:12261`
   - API docs: `http://127.0.0.1:12261/docs`

### Install Skill

In Claude Code, OpenClaw, OpenCode, Codex, and other AI Agent tools, execute:

```bash
npx skills add https://github.com/GinSing1226/ScreenClaw
```

After installation, AI can automatically call ScreenClaw API for desktop software automation.

---

## 📚 API List

| API | Purpose | Description |
|-----|---------|-------------|
| `health` | Verify service connectivity | First step check before operations |
| `get_window_list` | Find target window | Get window_id (required for subsequent operations) |
| `screenshot` | View UI state, locate coordinates | Verify results after each operation |
| `click` | Trigger functions, navigate pages | Normal click operations |
| `long_press` | Trigger long-press functions | Drag start points, show menus, etc. |
| `swipe` | Touch swipe | Page turns, tab switches, dragging |
| `scroll` | Mouse wheel scrolling | Browse long content, lists |
| `right_click` | Open context menus | Call shortcuts |
| `hover` | Trigger hover effects | Show tooltips, hidden UI elements |
| `input_text` | Input text content | Form filling, search, etc. |
| `press_key` | Trigger shortcuts | Ctrl+C copy, Enter confirm, etc. |
| `wait` | Wait for UI stability | Wait for animations, loading completion |
| `batch` | Execute multi-step workflows | Reduce network requests, fixed sequences |

---

## 🔧 API Usage Examples

### Common Request Headers

All API requests require:

```bash
Authorization: Bearer {token}
Content-Type: application/json
```

### 1. Health Check

```bash
curl -X GET http://127.0.0.1:12261/api/health
```

### 2. Get Window List

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

### 3. Screenshot (with Coordinate Grid)

```bash
curl -X POST http://127.0.0.1:12261/api/screenshot \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "coordinate_type": "grid",
    "grid": {
      "density": 5.0,
      "opacity": 50,
      "color": "#00FF00"
    },
    "coordinate": {
      "number_density": 2,
      "number_decimal": 0,
      "number_size": 8,
      "number_color": "#00FF00",
      "number_opacity": 100
    }
  }'
```

### 4. Click

```bash
curl -X POST http://127.0.0.1:12261/api/click \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "x": 50.0,
    "y": 30.0,
    "action_method": "background"
  }'
```

### 5. Long Press

```bash
curl -X POST http://127.0.0.1:12261/api/long_press \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "x": 50.0,
    "y": 50.0,
    "duration_ms": 500,
    "action_method": "background"
  }'
```

### 6. Swipe

```bash
curl -X POST http://127.0.0.1:12261/api/swipe \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "start_x": 50.0,
    "start_y": 80.0,
    "end_x": 50.0,
    "end_y": 20.0,
    "action_method": "background"
  }'
```

### 7. Scroll

```bash
curl -X POST http://127.0.0.1:12261/api/scroll \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "x": 50.0,
    "y": 50.0,
    "delta": -120,
    "action_method": "background"
  }'
```

### 8. Right Click

```bash
curl -X POST http://127.0.0.1:12261/api/right_click \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "x": 50.0,
    "y": 50.0,
    "action_method": "background"
  }'
```

### 9. Hover

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

### 10. Input Text

```bash
curl -X POST http://127.0.0.1:12261/api/input_text \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "x": 50.0,
    "y": 50.0,
    "text": "Hello World\n",
    "newline_key": "shift enter",
    "action_method": "hijack"
  }'
```

### 11. Press Key

```bash
curl -X POST http://127.0.0.1:12261/api/press_key \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "window_id": 1001,
    "key": "ctrl c",
    "x": 55.0,
    "y": 65.0,
    "duration_ms": 0,
    "action_method": "background"
  }'
```

### 12. Wait

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

### 13. Batch Execution

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

---

## 🎯 Use Cases

### Automated Visual Testing
Simulate manual UI operations, save test cases, automatically open F12 to manage errors.

### Automate Software Without Web Version, API, or CLI
Traditional ERP, OA systems, professional tools—anything visible on screen can be controlled.

### Mobile Emulators, Screen Casting Assistants
For most people, current ADB, virtual machine, and docker automation solutions are too complex and have high barriers. Dedicated AI phones are discontinued. ScreenClaw lets you directly operate casted/emulator screens.

### Complex Task Automation
Specialized UI LLMs typically have fewer parameters and struggle to understand complex tasks or execute long-duration tasks. ScreenClaw enables SOTA-level multimodal LLMs (like GPT-4V, Claude 3.5 Sonnet) to automate software operations.

### Comparison with Other Tools

| Scenario | Recommended Tool | ScreenClaw Role |
|----------|-----------------|-----------------|
| Browser automation | Playwright, CDP, agent-browser | Supplement: simulate manual walkthrough, fetch console errors |
| Traditional RPA | UiPath, Power Automate | Smarter: AI auto-recognizes coordinates, no manual config needed |

---

## 💡 Platform Notes

### Execution Side (Machine Running ScreenClaw)
**Recommended: Windows**

- ✅ Supports background screenshot (capture without stealing focus)
- ✅ Supports non-intrusive mouse and keyboard operations (doesn't affect user)
- ✅ Rich mobile emulator ecosystem (MuMu, BlueStacks, Nox, etc.)
- ✅ Official screen casting tools from major phone brands (Huawei Multi-Screen Collaboration, Xiaomi Cross-Screen Collaboration, etc.)
- ✅ Can automate most mobile apps

### Caller Side (Machine Running AI Application)
**Supports: Windows / macOS / Linux**

Calls via HTTP API, cross-platform without restrictions.

### Deployment Modes
- **Local Mode**: Execution and caller on the same machine
- **LAN Mode**: Different machines, must be on the same local network

---

## 🏗️ Technical Architecture

```
┌─────────────────────────────────────────────┐
│         External AI Applications            │
│  (Claude Code / OpenClaw / Other Agents)       │
└──────────────────┬──────────────────────────┘
                   │ HTTP API
                   ▼
┌─────────────────────────────────────────────┐
│         Python Backend Service               │
│       FastAPI :12261                         │
│  ┌───────┬────────┬────────┬────────┐      │
│  │ API层 │ Core层 │Platform│Service │      │
│  └───────┴────────┴────────┴────────┘      │
└──────────────────┬──────────────────────────┘
                   │ Subprocess
┌──────────────────▼──────────────────────────┐
│         Tauri Desktop Application            │
│  Monitor Panel │ Settings │ Tray Icon        │
└─────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Tauri 2.0 + Vue 3 + TypeScript |
| Backend | Python 3.11 + FastAPI + Uvicorn |
| Screenshot | pywin32 / mss |
| Input Injection | pywin32 (PostMessage) / pyautogui (SendInput) |
| Grid Drawing | Pillow (PIL) |

---

## 📁 Project Structure

```
screenClaw/
├── python/                   # Python Backend
│   ├── app/
│   │   ├── api/             # API Routes
│   │   ├── core/            # Core Business Logic
│   │   ├── platform/        # Platform Adaptation Layer
│   │   ├── models/          # Data Models
│   │   ├── services/        # Service Layer
│   │   └── utils/           # Utility Functions
│   └── main.py              # Entry Point
│
├── src-tauri/               # Tauri Backend (Rust)
│   └── src/
│       ├── commands.rs      # Tauri Commands
│       └── main.rs          # Entry Point
│
├── src/                     # Vue Frontend
│   ├── components/          # Components
│   ├── composables/         # Composables
│   └── main.ts              # Entry Point
│
├── skills/                  # AI Skill
│   └── screenclaw/
│       ├── SKILL.md         # Skill Definition (Complete Usage Guide)
│       └── references/      # API Docs and Scenario Templates
│
└── data/                    # Data Directory
    └── config.json          # Configuration File (Auto-created)
```

---

## ⚙️ Configuration

Configuration file located at `data/config.json` (auto-created on initialization):

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

| Config | Description |
|--------|-------------|
| `host` | Bind address, 0.0.0.0 allows LAN access |
| `port` | HTTP service port |
| `token` | API authentication token |
| `local_ip` | Auto-detected LAN IP |

---

## 🔒 Security

- All API requests require Token authentication
- Hijack mode operations pop up confirmation windows
- Configurable blocked process blacklist
- LAN and localhost access only

---

## 📖 More Documentation

- [Skill Usage Guide](./skills/screenclaw/SKILL.md) — Complete API documentation and usage methodology
- [API Online Docs](http://127.0.0.1:12261/docs) — Available after service starts

---

## 🗺️ Roadmap

- 🎯 **Improve Recognition Accuracy** — Enhance first-time recognition through skill optimization and scenario template accumulation
- 🔄 **More RPA Actions** — Expand supported automation types to cover more use cases
- 📦 **Scenario Template Library** — Package more templates for common software, ready to use out-of-the-box

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

---

## 📄 License

MIT License

---

<div align="center">

**If this project helps you, please give it a ⭐ Star!**

**ScreenClaw — Enabling Any Multimodal LLM to Control Any Screen**

Made with ❤️ by GinSing

</div>

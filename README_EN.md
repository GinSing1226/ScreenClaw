# ScreenClaw

<div align="center">

**Di Xia — The Essential Visual Operation Companion for AI Apps**

Empowering any multimodal LLM to recognize grid coordinates and automate any software

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tauri 2.0](https://img.shields.io/badge/Tauri-2.0-ffcf131.svg)](https://tauri.app/)

[中文](./README.md) | [Agent Guide](./README_AGENT.md) | [Demo Video](https://www.bilibili.com/video/BV1WJD8BUEnh)

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
- Adaptive grid density and number size: automatically generates optimal density and font size based on compressed image dimensions, preventing AI from passing bad parameters that affect coordinate reading

### 💻 Control Desktop Software
Automates most desktop software, especially traditional software without API, CLI, or other automation tools.

### 📱 Control Mobile Devices
Automate mobile emulators and official phone assistants (multi-screen collaboration/screen casting from various manufacturers):
- No ADB needed
- No root needed
- No virtual machine needed
- No specialized UI LLM needed to operate mobile apps

### 🖥️ Desktop-Level Capture & Control
- Capture and operate directly on the desktop without binding to any process — control desktop icons, taskbar, Start menu, and any visible content
- Multi-monitor support with independent coordinate spaces per display, including cross-monitor dragging
- Shares the same grid rendering and percentage coordinate system as window-level operations

### 🎬 Record & Distill Scenarios
- Manual walkthrough: Start recording via hotkey or tray menu, perform operations manually, and the backend automatically captures per-step screenshots, coordinates, and action types
- AI distillation: Invoke the screenclaw skill, provide the recording output folder (under the program's `record/` directory), and let AI distill it into a scenario template

### 💎 Knowledge Accumulation & Reuse
- AI operation + AI distillation: After AI completes a task automatically, save the successful workflow as a scenario template for next-time reuse, or refine existing templates
- Coordinate adaptation: When reusing a template, if the application size differs, coordinates can be proportionally adjusted for attempted reuse

### 🔒 Safe and Controllable
- Token authentication mechanism
- Blocked process blacklist to prevent AI from accessing sensitive applications
- Hijack operations require user confirmation

### 🎮 Delegated Mode
Enter when user requests full control. AI completely controls the computer with physical input, no individual confirmations needed. Ideal for continuous operations like Chinese text input. Press `Ctrl+Alt+Z` to exit anytime.

### 🔍 Coordinate Reading Aids
- Marker points on coordinate grids for AI to preview coordinates before executing operations
- Crop & zoom interface to enlarge specific areas of screenshots for easier coordinate reading

### 🎛️ Harness Engineering
- **Round-based self-check**: Every N screenshot operations, forces AI to stop and read self-check documentation via API error, reloading critical context to prevent instruction drift in long sessions
- **Self-check input validation**: AI must input content meeting minimum character count and user-configured keywords to pass; server-side deduplication prevents AI from skipping the process
- **Custom self-check documents**: Self-check content is fully customizable, not limited to ScreenClaw — can enforce AI to reload any critical information

---

## 🚀 Quick Start

### Run from Source (Development Environment)

**One-Line Deployment & Start**:
```bash
git clone https://github.com/GinSing1226/ScreenClaw.git && cd ScreenClaw && pip install -r python/requirements.txt && npm install && npm run tauri dev
```

**Existing Project**:
```bash
# Install dependencies (first time or when dependencies update)
pip install -r python/requirements.txt && npm install

# Run development environment 1 (recommend launching terminal as administrator)
npm run tauri dev

# Or run development environment 2
npx tauri dev
```

### Download Release (Production Environment)

1. Go to [Releases](https://github.com/GinSing1226/ScreenClaw/releases) page
2. Download the latest Windows package
3. Unzip and double-click `ScreenClaw.exe` to launch

### Start Service

1. After application launches, click "Start Service" button
2. View connection information:
   - Local access: `http://127.0.0.1:12261`
   - LAN access: `http://192.168.x.x:12261`

### Install Skill

In Claude Code, OpenClaw, OpenCode, Codex, and other AI Agent tools, execute:

```bash
npx skills add GinSing1226/ScreenClaw
```

---

## 📚 API List

### Window-Level APIs

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
| `drag` | Drag and drop operations | File dragging, element dragging with speed control |
| `mouse_move` | Relative mouse movement | Game camera control, hijack/delegated only |
| `scroll_screenshot` | Scrolling long screenshot | Auto-scroll stitching for long images |
| `crop_zoom_screenshot` | Crop & zoom | Enlarge specific area of existing screenshot |
| `delegated` | Enter/Exit delegated mode | User requests full computer control |

### Desktop-Level APIs

Desktop-level operations target **monitors** rather than windows. They can control desktop icons, taskbar, Start menu, and other elements not bound to any process. Always use hijack mode.

| API | Purpose | Description |
|-----|---------|-------------|
| `desktop_get_monitors_list` | Enumerate monitors | Get index, name, resolution, primary flag |
| `desktop_screenshot` | Desktop screenshot | Capture specified monitor with grid and markers |
| `desktop_click` | Desktop click | Click desktop elements |
| `desktop_double_click` | Desktop double-click | Double-click desktop elements |
| `desktop_right_click` | Desktop right-click | Right-click desktop elements |
| `desktop_drag` | Desktop drag | Same-monitor and cross-monitor dragging |
| `desktop_scroll` | Desktop scroll | Mouse wheel operation |
| `desktop_input_text` | Desktop text input | Clipboard paste input |
| `desktop_press_key` | Desktop key press | Keyboard shortcuts |
| `desktop_hover` | Desktop hover | Trigger hover tooltips |

### Recording APIs

| API | Purpose | Description |
|-----|---------|-------------|
| `recording/start` | Start recording | Trigger via hotkey or API |
| `recording/stop` | Stop recording | Stop and save output to record/ directory |
| `recording/status` | Query recording status | Whether recording, step count, etc. |

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
    "main_window_id": 1001,
    "coordinate_type": "grid",
    "color_mode": "grayscale",
    "grid": {
      "density_x": 5.0,
      "density_y": 5.0,
      "opacity": 50,
      "color": "#ff0000"
    },
    "coordinate": {
      "number_density": 2,
      "number_decimal": 1,
      "number_size": 14,
      "number_color": "#ff0000",
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
    "main_window_id": 1001,
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
    "main_window_id": 1001,
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
    "main_window_id": 1001,
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
    "main_window_id": 1001,
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
    "main_window_id": 1001,
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
    "main_window_id": 1001,
    "x": 50.0,
    "y": 50.0,
    "text": "Hello World\n",
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
    "main_window_id": 1001,
    "key": "ctrl c",
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
    "duration_ms": 1000,
    "random_range": 300
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

### 14. Delegated Mode

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

To exit delegated mode: Change `"action": "enter"` to `"action": "exit"`, or press `Ctrl+Alt+Z`.

### 15. Drag

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

Cross-window drag (optional `target_window_id`, `target_main_window_id`; `end_x`/`end_y` relative to target window).

### 16. Mouse Move

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

### 17. Crop & Zoom

```bash
curl -X POST http://127.0.0.1:12261/api/crop_zoom_screenshot \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_app_type": "claude_code",
    "session_id": "session-123",
    "source_image_path": "D:/screenClaw/data/claude_code__session-123/screenshot_143215.png",
    "center_x": 55.0,
    "center_y": 65.0,
    "crop_width": 20,
    "crop_height": 20,
    "zoom_scale": 2.0
  }'
```

### 18. Scroll Screenshot

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

## 🎯 Use Cases

### Automated Visual Testing
Simulate manual UI operations, save test cases, automatically open F12 to manage errors.

### Automate Software Without Web Version, API, or CLI
Traditional ERP, OA systems, professional tools—anything visible on screen can be controlled.

### Mobile Emulators, Screen Casting Assistants
For most people, current ADB, virtual machine, and docker automation solutions are too complex and have high barriers. Dedicated AI phones are discontinued. ScreenClaw lets you directly operate casted/emulator screens.

### Complex Task Automation
Specialized UI LLMs typically have fewer parameters and struggle to understand complex tasks or execute long-duration tasks. ScreenClaw enables SOTA-level multimodal LLMs (like GPT-4V, Claude 3.5 Sonnet) to automate software operations.

### Record → Distill Template → Auto Reuse
Manually operate once while recording captures per-step screenshots and actions. AI then distills the recording into a scenario template. Next time, AI executes the same task automatically, with coordinate adaptation and template refinement support.

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
| Window Screenshot | pywin32 (PrintWindow) |
| Desktop Screenshot | mss |
| Input Injection | pywin32 (PostMessage) / pyautogui (SendInput) |
| Operation Recording | Windows Hook (WH_MOUSE_LL / WH_KEYBOARD_LL) |
| Grid Drawing | Pillow (PIL) |

---

## 📁 Project Structure

```
screenClaw/
├── python/                   # Python Backend
│   ├── app/
│   │   ├── api/             # API Routes (window-level, desktop-level, recording)
│   │   ├── core/            # Core Business Logic (recorder, etc.)
│   │   ├── platform/        # Platform Adaptation (capture, Hook, input injection)
│   │   ├── models/          # Data Models
│   │   ├── services/        # Service Layer
│   │   ├── scripts/         # API Call Scripts
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
│       ├── scripts/         # Helper scripts (coord_adapt, recording_windows, etc.)
│       └── references/      # API Docs and Scenario Templates
│
├── record/                  # Recording outputs (auto-created, gitignored)
│   └── record_YYYYMMDD_HHmmss/
│       ├── step.json        # Recording metadata + steps
│       └── step_XXXX.png    # Step screenshots
│
└── data/                    # Data Directory
    └── config.json          # Configuration File (Auto-created)
```

---

## ⚙️ Configuration

### ScreenClaw Service Configuration
Located at `data/config.json` (auto-created on initialization):

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 12261,
    "token": "your-token-here",
    "local_ip": "192.168.x.x"
  },
  "recording": {
    "hotkey": "ctrl+alt+\\",
    "scroll_merge_interval_ms": 1000
  }
}
```

| Config | Description |
|--------|-------------|
| `host` | Bind address, 0.0.0.0 allows LAN access |
| `port` | HTTP service port |
| `token` | API authentication token |
| `local_ip` | Auto-detected LAN IP |
| `recording.hotkey` | Recording hotkey, default `Ctrl+Alt+\` |
| `recording.scroll_merge_interval_ms` | Continuous scroll merge interval (ms) |

### AI Skill Connection Configuration
Located at `{skill-dir}/references/config.md`, for AI applications to connect to ScreenClaw service.

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
- 🧠 **Coordinate Accuracy Improvement** — Leverage lightweight OCR or accessibility tree technology to further improve coordinate accuracy
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

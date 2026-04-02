# ScreenClaw Agent Integration Guide

> **For AI Agents**: This guide explains how to deploy ScreenClaw and integrate the skill.

---

## Quick Start

### 1. Deploy ScreenClaw

```bash
# Clone and run
git clone https://github.com/GinSing1226/ScreenClaw.git && cd ScreenClaw && pip install -r python/requirements.txt && npm install && npm run tauri dev
```

Or download release and double-click to run.

### 2. Get Connection Info

Ask user to provide from ScreenClaw app:
- **Service Address**: e.g., `http://192.168.x.x:12261`
- **Access Token**: Displayed in app

### 3. Install Skill

```bash
npx skills add https://github.com/GinSing1226/ScreenClaw
```

### 4. Configure

Create/update config file at skill location:
```
{skill-dir}/reference/config.md
```

Config format:
```json
{
  "server": {
    "host": "192.168.x.x",
    "port": 12261,
    "token": "your-token-here"
  }
}
```

---

## Platform-Specific Notes

### OpenClaw

After Step 4, also update `openclaw.json`:
```json
{
  "skills": {
    "load": {
      "extraDirs": ["{absolute-path-to-skill}"]
    }
  }
}
```

Then restart gateway:
```bash
# Linux/macOS
sleep 20 && openclaw gateway restart

# Windows
Start-Sleep -Seconds 20; openclaw gateway restart
```

### Claude Code / Other AI Apps

Just Steps 1-4 above. No additional config needed.

---

## Documentation Index

| Topic | Document |
|-------|----------|
| **Product Features** | [README.md](./README.md) — What ScreenClaw can do |
| **Skill Usage** | [skills/screenclaw/SKILL.md](./skills/screenclaw/SKILL.md) — Complete API reference and methodology |
| **API Details** | [skills/screenclaw/reference/api/](./skills/screenclaw/reference/api/) — Individual API documentation |
| **Scenario Templates** | [skills/screenclaw/reference/scenarios/](./skills/screenclaw/reference/scenarios/) — Pre-built workflows |

---

## Essential Workflow Summary

When using ScreenClaw, follow the standard workflow from SKILL.md:

```
1. Read skill directory references:
   - /references/config.md (connection info)
   - /references/api/health.md (verify service)
   - /references/api/get_window_list.md (find target window)
   - /references/api/screenshot.md (capture with grid)

2. Screenshot → Analyze → Execute → Verify loop:
   - Call /api/screenshot
   - Analyze image to determine coordinates
   - Call action API (click/input_text/press_key, etc.)
   - Loop until task complete
```

**Important**: Always read from skill reference files, not hardcode values.

---

## Coordinate System

- **Type**: Percentage (0-100)
- **Origin**: Top-left corner
- **Example**: `x=50, y=50` = center of screen

---

<div align="center">

**Di Xia — Enabling Any Multimodal LLM to Control Any Screen**

Made with ❤️ by GinSing

</div>

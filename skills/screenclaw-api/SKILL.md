---
name: screenclaw-api
description: |
  Control ScreenClaw to automate GUI operations through HTTP API. Use this skill whenever:
  - User mentions "screenclaw", "screen claw", or controlling desktop applications
  - Automating clicks, swipes, or keyboard input on windows/apps without API
  - Taking screenshots with coordinate grids for AI visual analysis
  - User wants to interact with desktop software programmatically

  ScreenClaw enables AI applications to control any desktop software by:
  1. Capturing screenshots with percentage-based coordinate grids
  2. Injecting mouse/keyboard operations without blocking user's physical input
---

# ScreenClaw API Control Skill

Enable AI applications to control desktop software through ScreenClaw's HTTP API.

## Quick Start

1. **Check service status**: Call `/api/health` to verify ScreenClaw is running
2. **Find target process**: Call `/api/get_process_list` with keyword
3. **Capture screenshot**: Call `/api/screenshot` to get image with coordinate grid
4. **Identify coordinates**: Analyze the screenshot to find target coordinates
5. **Execute operation**: Call appropriate API (click, swipe, input_text, etc.)

## Coordinate System

ScreenClaw uses **percentage coordinates (0-100)**:
- `x=0` is left edge, `x=100` is right edge
- `y=0` is top edge, `y=100` is bottom edge
- Example: `x=50, y=30` means center horizontally, 30% from top

## Visual Coordinate Recognition Methodology

**CRITICAL**: When analyzing screenshots to determine coordinates, follow this two-step process:

### Step 1: Element Localization
First, identify the approximate region where the target element is located. Look at the full screenshot and determine which grid cell contains the element.

### Step 2: Magnified Coordinate Verification
**The coordinate numbers on grid images are small.** To accurately read them:
- Zoom in on the identified region
- Examine the coordinate labels at grid intersections carefully
- Interpolate between grid lines if the element is not exactly on an intersection

```
Example workflow:
1. See button is roughly in center-right area
2. Zoom into that region of the screenshot
3. Read the exact coordinate numbers (e.g., "72,45")
4. If element is between grid lines, interpolate: grid shows "70,45" and "75,45",
   element appears halfway → use "72.5,45"
```

## API Overview

| API | Method | Purpose |
|-----|--------|---------|
| `/api/health` | GET | Check service status |
| `/api/get_process_list` | POST | List available processes |
| `/api/screenshot` | POST | Capture screenshot with grid |
| `/api/click` | POST | Left-click at coordinates |
| `/api/long_press` | POST | Long-press at coordinates |
| `/api/swipe` | POST | Swipe from start to end |
| `/api/right_click` | POST | Right-click at coordinates |
| `/api/input_text` | POST | Click and type text |
| `/api/press_key` | POST | Press key(s), supports combos |
| `/api/wait` | POST | Wait for duration |
| `/api/batch` | POST | Execute multiple operations |

## Common Request Structure

All POST APIs require these common fields:

```json
{
  "ai_app_type": "claude_code",
  "session_id": "unique-session-id",
  "process_id": 12345,
  // ... API-specific fields
}
```

Read `references/config.md` for:
- Base URL and port configuration
- Authentication token
- Session ID generation

Read `references/api-reference.md` for:
- Complete API specifications
- Request/response examples
- Error codes

## Typical Workflow Example

```
1. GET /api/health → Verify service running

2. POST /api/get_process_list {"keyword": "notepad"}
   → Returns process_id

3. POST /api/screenshot {"process_id": 12345, "coordinate_type": "grid"}
   → Returns image_path and image_base64

4. [Analyze screenshot, identify target coordinates]
   → Determine x=45, y=32 for the button

5. POST /api/click {"process_id": 12345, "x": 45, "y": 32}
   → Operation executed

6. POST /api/wait {"process_id": 12345, "duration_ms": 500}
   → Wait for UI response

7. Repeat as needed...
```

## Error Handling

Common errors and solutions:
- `PROCESS_NOT_FOUND`: Process closed, get new process list
- `SCREENSHOT_FAILED`: Window may be minimized
- `AUTH_FAILED`: Check token in config.md
- `TIMEOUT`: Increase wait duration

## Tips

- Use `/api/batch` for multi-step operations to reduce network overhead
- Always `wait` after actions that trigger UI changes
- For precise coordinate identification, request higher grid density
- Screenshot images are saved locally and returned as base64

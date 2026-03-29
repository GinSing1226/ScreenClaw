"""
Code templates for subprocess execution.
Templates are cached using @lru_cache to avoid regenerating f-strings
for each subprocess call with the same parameters.
"""
from functools import lru_cache


# ============ Cached Template Functions ============
# Each function uses @lru_cache to cache the generated code string
# based on input parameters. Same parameters = same cached string.
# lru_cache is thread-safe by design.


@lru_cache(maxsize=512)
def _get_background_click_template(hwnd: int, x: int, y: int) -> str:
    """Generate background click code template (cached)."""
    return f'''
import win32gui, win32api, win32con

hwnd = {hwnd}
x = {x}
y = {y}

# API 层已经处理了最小化恢复，直接 PostMessage
lParam = win32api.MAKELONG(x, y)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
'''


@lru_cache(maxsize=256)
def _get_background_right_click_template(hwnd: int, x: int, y: int) -> str:
    """Generate background right click code template (cached)."""
    return f'''
import win32gui, win32api, win32con, time
hwnd, x, y = {hwnd}, {x}, {y}
lParam = win32api.MAKELONG(x, y)
win32gui.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, 0x0002, lParam)
time.sleep(0.05)
win32gui.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lParam)
'''


@lru_cache(maxsize=256)
def _get_background_long_press_template(hwnd: int, x: int, y: int, duration_ms: int) -> str:
    """Generate background long press code template (cached)."""
    return f'''
import win32gui, win32api, win32con, time
hwnd, x, y, duration_ms = {hwnd}, {x}, {y}, {duration_ms}
lParam = win32api.MAKELONG(x, y)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam)
time.sleep(duration_ms / 1000)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
'''


@lru_cache(maxsize=512)
def _get_background_swipe_template(hwnd: int, sx: int, sy: int, ex: int, ey: int) -> str:
    """Generate background swipe code template (cached)."""
    return f'''
import win32gui, win32api, win32con, time

hwnd = {hwnd}
sx = {sx}
sy = {sy}
ex = {ex}
ey = {ey}

lParam_start = win32api.MAKELONG(sx, sy)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam_start)
time.sleep(0.05)

# 分步移动
steps = 10
duration = 0.3
step_delay = duration / steps

for i in range(1, steps + 1):
    progress = i / steps
    current_x = int(sx + (ex - sx) * progress)
    current_y = int(sy + (ey - sy) * progress)
    lParam = win32api.MAKELONG(current_x, current_y)
    win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0x0001, lParam)
    time.sleep(step_delay)

lParam_end = win32api.MAKELONG(ex, ey)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam_end)
'''


@lru_cache(maxsize=512)
def _get_background_scroll_template(hwnd: int, virtual_x: int, virtual_y: int, delta: int) -> str:
    """Generate background scroll code template (cached)."""
    return f'''
import win32gui, win32api, win32con

hwnd = {hwnd}
delta = {delta}

# 客户区虚拟坐标 → 屏幕坐标
screen_x, screen_y = win32gui.ClientToScreen(hwnd, ({virtual_x}, {virtual_y}))
lParam = win32api.MAKELONG(screen_x, screen_y)
wParam = (delta << 16) & 0xFFFF0000
win32gui.PostMessage(hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)
'''


@lru_cache(maxsize=256)
def _get_background_hover_template(hwnd: int, x: int, y: int, duration_ms: int) -> str:
    """Generate background hover code template (cached)."""
    return f'''
import win32gui, win32api, win32con, time

hwnd = {hwnd}
x = {x}
y = {y}
duration_ms = {duration_ms}

# 只发送 WM_MOUSEMOVE，不按下鼠标
lParam = win32api.MAKELONG(x, y)
win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lParam)

# 多发送几次增强效果
for _ in range(3):
    time.sleep(0.01)
    win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lParam)

# 停留指定时长
if duration_ms > 0:
    time.sleep(duration_ms / 1000.0)
'''


def clear_template_cache():
    """Clear all template caches."""
    _get_background_click_template.cache_clear()
    _get_background_right_click_template.cache_clear()
    _get_background_long_press_template.cache_clear()
    _get_background_swipe_template.cache_clear()
    _get_background_scroll_template.cache_clear()
    _get_background_hover_template.cache_clear()

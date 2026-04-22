"""
Windows操作注入实现
支持 background(无感) / hijack(劫持) / delegated(托管) 三种模式
所有操作通过子进程隔离执行

坐标说明：
- virtual_x/y: 窗口客户端区域的原始虚拟坐标（未经 DPI 缩放）
- physical_x/y: DPI 缩放后的物理坐标（已弃用于 background 模式）

Background 模式必须使用 virtual 坐标：
- PostMessage/SendMessage 的 lParam 需要的是客户端区域的原始坐标
- 在 DPI 缩放环境（如 4K 150%）中，physical 坐标会超出客户区实际范围
- 例如：4K 150% 时，virtual=(100, 100) 会变成 physical=(150, 150)，导致点击位置错误

Hijack 模式使用 virtual 坐标转屏幕坐标：
- SetCursorPos 需要屏幕绝对坐标
- 通过 ClientToScreen(virtual_x, virtual_y) 转换

Delegated（托管）模式：
- 与 hijack 相同的物理操作方式
- 不恢复窗口焦点和鼠标位置（restore_state=False）
- 跳过确认弹窗（由API层处理）
"""
from typing import Optional, Tuple, List
from dataclasses import dataclass
import time
import subprocess
import sys
import base64
import ctypes

import win32gui
import win32api
import win32con


@dataclass
class InjectResult:
    """操作注入结果"""
    success: bool
    error: Optional[str]
    method: str  # "background" | "hijack" | "delegated"


# 修饰键 VK 集合
MODIFIER_VKS = {0x11, 0x12, 0x10, 0x5B}  # Ctrl, Alt, Shift, Win


class WindowsInputInjector:
    """Windows操作注入 - background/hijack/delegated 模式 + 子进程隔离"""

    def __init__(self):
        self._last_error: Optional[str] = None

    # 按键名 → VK码
    _key_map = {
        "enter": 0x0D, "return": 0x0D,
        "tab": 0x09,
        "escape": 0x1B, "esc": 0x1B,
        "space": 0x20,
        "backspace": 0x08, "bs": 0x08,
        "delete": 0x2E, "del": 0x2E,
        "insert": 0x2D, "ins": 0x2D,
        "home": 0x24,
        "end": 0x23,
        "pageup": 0x21, "pgup": 0x21,
        "pagedown": 0x22, "pgdn": 0x22,
        "up": 0x26,
        "down": 0x28,
        "left": 0x25,
        "right": 0x27,
        "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
        "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
        "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
        "ctrl": 0x11, "control": 0x11,
        "alt": 0x12,
        "shift": 0x10,
        "win": 0x5B, "windows": 0x5B,
        "plus": 0xBB, "equal": 0xBB,
        "minus": 0xBD,
        "lbracket": 0xDB, "[": 0xDB,
        "rbracket": 0xDD, "]": 0xDD,
        "semicolon": 0xBA,
        "quote": 0xDE,
        "backslash": 0xDC, "\\": 0xDC,
        "comma": 0xBC,
        "period": 0xBE,
        "slash": 0xBF,
    }

    # ============ 托管模式 ============

    @staticmethod
    def _is_delegated_active() -> bool:
        """检查托管模式是否激活"""
        try:
            from app.services.config_service import config_service
            return config_service.is_delegated_active()
        except Exception:
            return False

    def _fail_result(self, operation: str, method: str) -> InjectResult:
        error = f"{operation} failed"
        if self._last_error:
            error += f": {self._last_error}"
        return InjectResult(False, error, method)

    def _effective_method(self, action_method: str) -> str:
        """获取有效的操作方法：托管模式时强制转为 delegated

        如果 action_method 已经是 "delegated"（由装饰器解析），直接返回，避免重复检查。
        仅当 action_method 非 delegated 时才检查文件，用于 batch 等不经装饰器的路径。
        """
        if action_method == "delegated":
            return "delegated"
        if self._is_delegated_active():
            return "delegated"
        return action_method

    @staticmethod
    def _build_restore_code(restore_state: bool) -> str:
        """构建状态恢复代码块"""
        if restore_state:
            return '''
# 恢复状态
try:
    time.sleep(0.01)
    win32api.SetCursorPos(old_pos)
    win32gui.SetForegroundWindow(old_fg)
except:
    pass
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        return ''

    # ============ 公共方法 ============

    # ============ delegated 直接操作（无窗口操控） ============

    def _delegated_click(self, hwnd: int, virtual_x: int, virtual_y: int) -> bool:
        """Delegated 点击 - 激活窗口 + mouse_event 硬件级点击，不恢复状态"""
        code = f'''
import win32gui, win32api, win32con, ctypes, time

hwnd = {hwnd}
virtual_x = {virtual_x}
virtual_y = {virtual_y}

# 计算屏幕坐标
screen_x, screen_y = win32gui.ClientToScreen(hwnd, (virtual_x, virtual_y))

# 激活目标窗口（先检查窗口状态）
main_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
    time.sleep(0.1)

# 先强制释放可能的鼠标捕获（防止游戏处于拖拽/捕获状态导致死锁）
try:
    ctypes.windll.user32.ReleaseCapture()
except:
    pass

target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)

# 激活窗口，带异常处理
try:
    win32gui.SetForegroundWindow(main_hwnd)
except Exception:
    try:
        win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
        ctypes.windll.user32.BringWindowToTop(main_hwnd)
    except Exception:
        pass

time.sleep(0.3)

win32api.SetCursorPos((screen_x, screen_y))
time.sleep(0.3)

# 使用 mouse_event 硬件级点击（与 hijack 一致）
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

# 断开线程绑定
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        return self._run_subprocess(code, timeout=15)

    def _delegated_right_click(self, hwnd: int, virtual_x: int, virtual_y: int) -> bool:
        """Delegated 右键 - 激活窗口 + mouse_event 硬件级右键，不恢复状态"""
        code = f'''
import win32gui, win32api, win32con, ctypes, time

hwnd = {hwnd}
virtual_x = {virtual_x}
virtual_y = {virtual_y}

# 计算屏幕坐标
screen_x, screen_y = win32gui.ClientToScreen(hwnd, (virtual_x, virtual_y))

# 激活目标窗口
main_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd
target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)

# 激活窗口，带异常处理
try:
    win32gui.SetForegroundWindow(main_hwnd)
except Exception:
    try:
        win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
        ctypes.windll.user32.BringWindowToTop(main_hwnd)
    except Exception:
        pass

time.sleep(0.3)

win32api.SetCursorPos((screen_x, screen_y))
time.sleep(0.3)

# 使用 mouse_event 硬件级右键（与 hijack 一致）
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

# 断开线程绑定
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        return self._run_subprocess(code, timeout=15)

    def _delegated_long_press(self, hwnd: int, virtual_x: int, virtual_y: int, duration_ms: int) -> bool:
        """Delegated 长按 - 激活窗口 + mouse_event 硬件级长按，不恢复状态"""
        code = f'''
import win32gui, win32api, win32con, ctypes, time

hwnd = {hwnd}
virtual_x = {virtual_x}
virtual_y = {virtual_y}
duration_ms = {duration_ms}

# 计算屏幕坐标
screen_x, screen_y = win32gui.ClientToScreen(hwnd, (virtual_x, virtual_y))

# 激活目标窗口
main_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd
target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)

# 激活窗口，带异常处理
try:
    win32gui.SetForegroundWindow(main_hwnd)
except Exception:
    try:
        win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
        ctypes.windll.user32.BringWindowToTop(main_hwnd)
    except Exception:
        pass

time.sleep(0.3)

win32api.SetCursorPos((screen_x, screen_y))
time.sleep(0.3)

# 使用 mouse_event 硬件级长按（与 hijack 一致）
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

# 长按保持
time.sleep(duration_ms / 1000)

ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

# 断开线程绑定
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        return self._run_subprocess(code, timeout=max(15, duration_ms / 1000 + 15))

    def _delegated_swipe(self, hwnd: int, virtual_sx: int, virtual_sy: int,
                       virtual_ex: int, virtual_ey: int) -> bool:
        """Delegated 滑动 - 激活窗口 + mouse_event 硬件级拖拽，不恢复状态"""
        code = f'''
import win32gui, win32api, win32con, ctypes, time

hwnd = {hwnd}
virtual_sx = {virtual_sx}
virtual_sy = {virtual_sy}
virtual_ex = {virtual_ex}
virtual_ey = {virtual_ey}

# 计算屏幕坐标
screen_sx, screen_sy = win32gui.ClientToScreen(hwnd, (virtual_sx, virtual_sy))
screen_ex, screen_ey = win32gui.ClientToScreen(hwnd, (virtual_ex, virtual_ey))

# 激活目标窗口
main_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd
target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)

# 激活窗口，带异常处理
try:
    win32gui.SetForegroundWindow(main_hwnd)
except Exception:
    try:
        win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
        ctypes.windll.user32.BringWindowToTop(main_hwnd)
    except Exception:
        pass

time.sleep(0.3)

win32api.SetCursorPos((screen_sx, screen_sy))
time.sleep(0.1)

# 使用 mouse_event 硬件级拖拽（与 hijack 一致）
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)

# 分步移动
steps = 10
duration = 0.3
step_delay = duration / steps
for i in range(1, steps + 1):
    progress = i / steps
    screen_cx = int(screen_sx + (screen_ex - screen_sx) * progress)
    screen_cy = int(screen_sy + (screen_ey - screen_sy) * progress)
    win32api.SetCursorPos((screen_cx, screen_cy))
    time.sleep(step_delay)

ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

# 断开线程绑定
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        return self._run_subprocess(code, timeout=15)

    def _delegated_drag(self, hwnd: int, virtual_sx: int, virtual_sy: int,
                        virtual_ex: int, virtual_ey: int, duration_ms: int = 500) -> bool:
        """Delegated 拖拽 - 激活窗口 + mouse_event 硬件级拖拽，不恢复状态"""
        duration = duration_ms / 1000.0
        code = f'''
import win32gui, win32api, win32con, ctypes, time

hwnd = {hwnd}
virtual_sx = {virtual_sx}
virtual_sy = {virtual_sy}
virtual_ex = {virtual_ex}
virtual_ey = {virtual_ey}
duration = {duration}

# 计算屏幕坐标
screen_sx, screen_sy = win32gui.ClientToScreen(hwnd, (virtual_sx, virtual_sy))
screen_ex, screen_ey = win32gui.ClientToScreen(hwnd, (virtual_ex, virtual_ey))

# 激活目标窗口
main_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd
target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)

# 激活窗口，带异常处理
try:
    win32gui.SetForegroundWindow(main_hwnd)
except Exception:
    try:
        win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
        ctypes.windll.user32.BringWindowToTop(main_hwnd)
    except Exception:
        pass

time.sleep(0.3)

win32api.SetCursorPos((screen_sx, screen_sy))
time.sleep(0.1)

# 使用 mouse_event 硬件级拖拽（与 hijack 一致）
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)

# 分步移动
steps = 10
step_delay = duration / steps
for i in range(1, steps + 1):
    progress = i / steps
    screen_cx = int(screen_sx + (screen_ex - screen_sx) * progress)
    screen_cy = int(screen_sy + (screen_ey - screen_sy) * progress)
    win32api.SetCursorPos((screen_cx, screen_cy))
    time.sleep(step_delay)

ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

# 断开线程绑定
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        timeout = max(20, int(duration_ms / 1000) + 15)
        return self._run_subprocess(code, timeout=timeout)

    def _delegated_drag_cross_process(self, source_hwnd: int, target_hwnd: int,
                                      screen_sx: int, screen_sy: int,
                                      screen_ex: int, screen_ey: int,
                                      duration_ms: int = 500) -> bool:
        """Delegated 跨窗口拖拽 - 激活源窗口 + midpoint激活目标窗口 + mouse_event"""
        duration = duration_ms / 1000.0
        code = f'''
import win32gui, win32api, win32con, ctypes, time

source_hwnd = {source_hwnd}
target_hwnd = {target_hwnd}
screen_sx = {screen_sx}
screen_sy = {screen_sy}
screen_ex = {screen_ex}
screen_ey = {screen_ey}
duration = {duration}

source_main_hwnd = ctypes.windll.user32.GetAncestor(source_hwnd, 2) or source_hwnd
target_main_hwnd = ctypes.windll.user32.GetAncestor(target_hwnd, 2) or target_hwnd
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()

# 确保目标窗口可见（不激活，仅恢复）
if win32gui.IsIconic(target_main_hwnd):
    win32gui.ShowWindow(target_main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(target_main_hwnd):
    win32gui.ShowWindow(target_main_hwnd, win32con.SW_SHOW)
    time.sleep(0.1)

# 激活源窗口
if win32gui.IsIconic(source_main_hwnd):
    win32gui.ShowWindow(source_main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
source_tid = ctypes.windll.user32.GetWindowThreadProcessId(source_main_hwnd, None)
ctypes.windll.user32.AttachThreadInput(current_tid, source_tid, True)
try:
    win32gui.SetForegroundWindow(source_main_hwnd)
except Exception:
    try:
        win32gui.ShowWindow(source_main_hwnd, win32con.SW_SHOW)
        ctypes.windll.user32.BringWindowToTop(source_main_hwnd)
    except Exception:
        pass
time.sleep(0.3)

win32api.SetCursorPos((screen_sx, screen_sy))
time.sleep(0.1)

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)

# 分步移动到终点
steps = 10
step_delay = duration / steps
mid = steps // 2
for i in range(1, steps + 1):
    progress = i / steps
    cx = int(screen_sx + (screen_ex - screen_sx) * progress)
    cy = int(screen_sy + (screen_ey - screen_sy) * progress)
    win32api.SetCursorPos((cx, cy))
    # 在 midpoint 激活目标窗口，使其浮到源窗口之上
    if i == mid:
        target_tid = ctypes.windll.user32.GetWindowThreadProcessId(target_main_hwnd, None)
        ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
        try:
            win32gui.SetForegroundWindow(target_main_hwnd)
        except Exception:
            pass
        time.sleep(0.15)
    time.sleep(step_delay)

ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

ctypes.windll.user32.AttachThreadInput(current_tid, source_tid, False)
'''
        timeout = max(20, int(duration_ms / 1000) + 15)
        return self._run_subprocess(code, timeout=timeout)

    def _delegated_mouse_move(self, hwnd: int, delta_x: int, delta_y: int,
                              duration_ms: int = 300) -> bool:
        """Delegated 鼠标移动 - mouse_event 分步相对移动 + 不恢复状态"""
        duration = duration_ms / 1000.0
        code = f'''
import win32gui, win32api, win32con, ctypes, time

hwnd = {hwnd}
delta_x = {delta_x}
delta_y = {delta_y}
duration = {duration}

# 激活目标窗口
main_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd
target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.3)

# 分步发送相对移动事件
MOUSEEVENTF_MOVE = 0x0001
steps = 10
step_dx = delta_x / steps
step_dy = delta_y / steps
step_delay = duration / steps

for i in range(steps):
    dx = int(round(step_dx))
    dy = int(round(step_dy))
    if i == steps - 1:
        dx = delta_x - int(round(step_dx)) * (steps - 1)
        dy = delta_y - int(round(step_dy)) * (steps - 1)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)
    time.sleep(step_delay)

# 不恢复状态，仅断开线程绑定
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        timeout = max(15, int(duration_ms / 1000) + 10)
        return self._run_subprocess(code, timeout=timeout)

    def _delegated_scroll(self, hwnd: int, virtual_x: int, virtual_y: int, delta: int) -> bool:
        """Delegated 滚动 - 激活窗口 + mouse_event 硬件级滚轮，不恢复状态"""
        code = f'''
import win32gui, win32api, win32con, ctypes, time

hwnd = {hwnd}
virtual_x = {virtual_x}
virtual_y = {virtual_y}
delta = {delta}

# 计算屏幕坐标
screen_x, screen_y = win32gui.ClientToScreen(hwnd, (virtual_x, virtual_y))

# 激活目标窗口
main_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd
target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)

# 激活窗口，带异常处理
try:
    win32gui.SetForegroundWindow(main_hwnd)
except Exception:
    try:
        win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
        ctypes.windll.user32.BringWindowToTop(main_hwnd)
    except Exception:
        pass

time.sleep(0.3)

win32api.SetCursorPos((screen_x, screen_y))
time.sleep(0.1)

# 使用 mouse_event 硬件级滚轮（与 hijack 一致，兼容所有应用）
MOUSEEVENTF_WHEEL = 0x0800
ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, delta, 0)

# 断开线程绑定
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        return self._run_subprocess(code, timeout=15)

    def _delegated_hover(self, hwnd: int, virtual_x: int, virtual_y: int,
                       duration_ms: int, semi_blocking: bool = False) -> bool:
        """Delegated 悬浮 - 激活窗口 + 移动鼠标停留，不恢复状态"""
        code = f'''
import win32gui, win32api, win32con, ctypes, time

hwnd = {hwnd}
virtual_x = {virtual_x}
virtual_y = {virtual_y}
duration_ms = {duration_ms}

# 计算屏幕坐标
screen_x, screen_y = win32gui.ClientToScreen(hwnd, (virtual_x, virtual_y))

# 激活目标窗口
main_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd
target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.3)

win32api.SetCursorPos((screen_x, screen_y))

# 停留指定时长
if duration_ms > 0:
    time.sleep(duration_ms / 1000.0)

# 不恢复状态，仅断开线程绑定
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        timeout = max(5, duration_ms / 1000 + 5) if duration_ms > 0 else 5
        return self._run_subprocess(code, timeout=int(timeout), semi_blocking=semi_blocking)

    def _delegated_input_text(self, hwnd: int, virtual_x: int, virtual_y: int,
                            text: str, has_coord: bool) -> bool:
        """Delegated 输入文本 - 激活窗口 + 剪贴板粘贴，不恢复状态"""
        text_b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')

        click_code = ''
        if has_coord:
            click_code = f'''
# 点击目标位置
screen_x, screen_y = win32gui.ClientToScreen(hwnd, ({virtual_x}, {virtual_y}))
win32api.SetCursorPos((screen_x, screen_y))
time.sleep(0.3)
lParam = win32api.MAKELONG({virtual_x}, {virtual_y})
win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam)
time.sleep(0.05)
win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
time.sleep(0.2)
'''

        code = f'''
import win32gui, win32api, win32con, ctypes, time, base64
import pyperclip

hwnd = {hwnd}
text = base64.b64decode("{text_b64}").decode("utf-8")

# 激活目标窗口
main_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd
target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.3)

{click_code}

pyperclip.copy(text)
time.sleep(0.1)

VK_CONTROL = 0x11
VK_V = 0x56
scan_ctrl = ctypes.windll.user32.MapVirtualKeyW(VK_CONTROL, 0)
scan_v = ctypes.windll.user32.MapVirtualKeyW(VK_V, 0)

ctypes.windll.user32.keybd_event(VK_CONTROL, scan_ctrl, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(VK_V, scan_v, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(VK_V, scan_v, 2, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(VK_CONTROL, scan_ctrl, 2, 0)
time.sleep(0.1)

# 不恢复状态，仅断开线程绑定
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        return self._run_subprocess(code, timeout=30)

    def _delegated_key_press(self, hwnd: int, key: str,
                           virtual_x: int = None, virtual_y: int = None,
                           duration_ms: int = 0, non_blocking: bool = False) -> bool:
        """Delegated 按键 - 激活窗口 + keybd_event 硬件级按键，不恢复状态"""
        parsed = self._parse_keys(key)
        if parsed is None:
            return False

        modifiers, main_vk = parsed
        all_vks = modifiers + [main_vk]

        # 构建 keybd_event 硬件级按键代码（与 hijack 一致）
        press_lines = []
        release_lines = []
        for vk in all_vks:
            scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
            press_lines.append(f'ctypes.windll.user32.keybd_event({vk}, {scan}, 0, 0)')
        for vk in reversed(all_vks):
            scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
            release_lines.append(f'ctypes.windll.user32.keybd_event({vk}, {scan}, 2, 0)')

        all_press = '\n'.join(press_lines)
        all_release = '\n'.join(release_lines)

        hold_sleep = f'time.sleep({duration_ms} / 1000.0)' if duration_ms > 0 else ''

        click_code = ''
        if virtual_x is not None and virtual_y is not None:
            click_code = f'''
# 点击目标位置
screen_x, screen_y = win32gui.ClientToScreen(hwnd, ({virtual_x}, {virtual_y}))
win32api.SetCursorPos((screen_x, screen_y))
time.sleep(0.3)
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(0.1)
'''

        code = f'''
import win32gui, win32api, win32con, ctypes, time

hwnd = {hwnd}

# 激活目标窗口
main_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd
target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)

# 激活窗口，带异常处理
try:
    win32gui.SetForegroundWindow(main_hwnd)
except Exception:
    try:
        win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
        ctypes.windll.user32.BringWindowToTop(main_hwnd)
    except Exception:
        pass

time.sleep(0.3)

{click_code}

# 按下所有键
{all_press}
time.sleep(0.05)
{hold_sleep}
# 释放所有键
{all_release}
time.sleep(0.05)

# 断开线程绑定
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        timeout = max(15, duration_ms / 1000 + 15) if duration_ms > 0 else 15
        return self._run_subprocess(code, timeout=int(timeout), non_blocking=non_blocking)

    # ============ 原有公共方法（修改路由） ============

    def click(self, hwnd: int, physical_x: int, physical_y: int,
              virtual_x: int, virtual_y: int,
              action_method: str = "background") -> InjectResult:
        effective = self._effective_method(action_method)

        if effective == "delegated":
            if self._delegated_click(hwnd, virtual_x, virtual_y):
                return InjectResult(True, None, "delegated")
            return self._fail_result("Click", "delegated")
        if effective == "hijack":
            if self._hijack_click(hwnd, virtual_x, virtual_y, restore_state=True):
                return InjectResult(True, None, "hijack")
            return self._fail_result("Click", "hijack")
        if self._background_click(hwnd, virtual_x, virtual_y):
            return InjectResult(True, None, "background")
        return self._fail_result("Click", "background")

    def right_click(self, hwnd: int, physical_x: int, physical_y: int,
                    virtual_x: int, virtual_y: int,
                    action_method: str = "background") -> InjectResult:
        effective = self._effective_method(action_method)
        if effective == "delegated":
            if self._delegated_right_click(hwnd, virtual_x, virtual_y):
                return InjectResult(True, None, "delegated")
            return self._fail_result("Right-click", "delegated")
        if effective == "hijack":
            screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
            if self._hijack_right_click(hwnd, screen_x, screen_y, restore_state=True):
                return InjectResult(True, None, "hijack")
            return self._fail_result("Right-click", "hijack")
        if self._background_right_click(hwnd, virtual_x, virtual_y):
            return InjectResult(True, None, "background")
        return self._fail_result("Right-click", "background")

    def long_press(self, hwnd: int, physical_x: int, physical_y: int,
                   virtual_x: int, virtual_y: int, duration_ms: int,
                   action_method: str = "background") -> InjectResult:
        effective = self._effective_method(action_method)
        if effective == "delegated":
            if self._delegated_long_press(hwnd, virtual_x, virtual_y, duration_ms):
                return InjectResult(True, None, "delegated")
            return self._fail_result("Long press", "delegated")
        if effective == "hijack":
            screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
            if self._hijack_long_press(hwnd, screen_x, screen_y, duration_ms, restore_state=True):
                return InjectResult(True, None, "hijack")
            return self._fail_result("Long press", "hijack")
        # background 使用 virtual 坐标
        if self._background_long_press(hwnd, virtual_x, virtual_y, duration_ms):
            return InjectResult(True, None, "background")
        return self._fail_result("Long press", "background")

    def swipe(self, hwnd: int,
              physical_sx: int, physical_sy: int, physical_ex: int, physical_ey: int,
              virtual_sx: int, virtual_sy: int, virtual_ex: int, virtual_ey: int,
              action_method: str = "background") -> InjectResult:
        effective = self._effective_method(action_method)
        if effective == "delegated":
            if self._delegated_swipe(hwnd, virtual_sx, virtual_sy, virtual_ex, virtual_ey):
                return InjectResult(True, None, "delegated")
            return self._fail_result("Swipe", "delegated")
        if effective == "hijack":
            ss = self._client_to_screen(hwnd, virtual_sx, virtual_sy)
            se = self._client_to_screen(hwnd, virtual_ex, virtual_ey)
            if self._hijack_swipe(hwnd, ss[0], ss[1], se[0], se[1], restore_state=True):
                return InjectResult(True, None, "hijack")
            return self._fail_result("Swipe", "hijack")
        # background 使用 virtual 坐标（与 click 一致，修复 DPI 缩放问题）
        if self._background_swipe(hwnd, virtual_sx, virtual_sy, virtual_ex, virtual_ey):
            return InjectResult(True, None, "background")
        return self._fail_result("Swipe", "background")

    def drag(self, hwnd: int,
             physical_sx: int, physical_sy: int, physical_ex: int, physical_ey: int,
             virtual_sx: int, virtual_sy: int, virtual_ex: int, virtual_ey: int,
             duration_ms: int = 500,
             action_method: str = "background",
             target_hwnd: int = None) -> InjectResult:
        effective = self._effective_method(action_method)
        if effective == "delegated":
            if target_hwnd:
                ss = self._client_to_screen(hwnd, virtual_sx, virtual_sy)
                se = self._client_to_screen(target_hwnd, virtual_ex, virtual_ey)
                if self._delegated_drag_cross_process(hwnd, target_hwnd, ss[0], ss[1], se[0], se[1], duration_ms):
                    return InjectResult(True, None, "delegated")
                return self._fail_result("Drag", "delegated")
            if self._delegated_drag(hwnd, virtual_sx, virtual_sy, virtual_ex, virtual_ey, duration_ms):
                return InjectResult(True, None, "delegated")
            return self._fail_result("Drag", "delegated")
        if effective == "hijack":
            end_hwnd = target_hwnd if target_hwnd else hwnd
            ss = self._client_to_screen(hwnd, virtual_sx, virtual_sy)
            se = self._client_to_screen(end_hwnd, virtual_ex, virtual_ey)
            if self._hijack_drag(hwnd, ss[0], ss[1], se[0], se[1], duration_ms, restore_state=True, target_hwnd=target_hwnd):
                return InjectResult(True, None, "hijack")
            return self._fail_result("Drag", "hijack")
        # background 使用 virtual 坐标（不支持跨进程，由 model validator 强制 hijack）
        if self._background_drag(hwnd, virtual_sx, virtual_sy, virtual_ex, virtual_ey, duration_ms):
            return InjectResult(True, None, "background")
        return self._fail_result("Drag", "background")

    def mouse_move(self, hwnd: int,
                   delta_x: int, delta_y: int,
                   duration_ms: int = 300,
                   action_method: str = "hijack") -> InjectResult:
        effective = self._effective_method(action_method)
        if effective == "delegated":
            if self._delegated_mouse_move(hwnd, delta_x, delta_y, duration_ms):
                return InjectResult(True, None, "delegated")
            return self._fail_result("Mouse move", "delegated")
        if effective == "hijack":
            if self._hijack_mouse_move(hwnd, delta_x, delta_y, duration_ms, restore_state=True):
                return InjectResult(True, None, "hijack")
            return self._fail_result("Mouse move", "hijack")
        return InjectResult(False, "Mouse move does not support background mode", "background")

    def scroll(self, hwnd: int, physical_x: int, physical_y: int,
               virtual_x: int, virtual_y: int, delta: int,
               action_method: str = "background") -> InjectResult:
        effective = self._effective_method(action_method)
        if effective == "delegated":
            if self._delegated_scroll(hwnd, virtual_x, virtual_y, delta):
                return InjectResult(True, None, "delegated")
            return self._fail_result("Scroll", "delegated")
        if effective == "hijack":
            screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
            if self._hijack_scroll(hwnd, screen_x, screen_y, delta, restore_state=True):
                return InjectResult(True, None, "hijack")
            return self._fail_result("Scroll", "hijack")
        if self._background_scroll(hwnd, virtual_x, virtual_y, delta):
            return InjectResult(True, None, "background")
        return self._fail_result("Scroll", "background")

    def hover(self, hwnd: int, physical_x: int, physical_y: int,
              virtual_x: int, virtual_y: int, duration_ms: int,
              action_method: str = "background") -> InjectResult:
        """鼠标悬浮 - 移动到目标位置并停留 duration_ms

        半阻塞模式：等待鼠标到位（200ms）后返回，hover 持续时间在后台继续执行

        Args:
            hwnd: 窗口句柄
            physical_x/y: 物理坐标（已弃用，保留兼容）
            virtual_x/y: 虚拟坐标
            duration_ms: 停留时长（毫秒）
            action_method: background / hijack / delegated
        """
        effective = self._effective_method(action_method)
        if effective == "delegated":
            if self._delegated_hover(hwnd, virtual_x, virtual_y, duration_ms, semi_blocking=True):
                return InjectResult(True, None, "delegated")
            return self._fail_result("Hover", "delegated")
        if effective == "hijack":
            screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
            success = self._hijack_hover(hwnd, screen_x, screen_y, duration_ms,
                                         semi_blocking=True, restore_state=True)
            if success:
                return InjectResult(True, None, "hijack")
            return self._fail_result("Hover", "hijack")
        # background 也是半阻塞
        success = self._background_hover(hwnd, virtual_x, virtual_y, duration_ms, semi_blocking=True)
        if success:
            return InjectResult(True, None, "background")
        return self._fail_result("Hover", "background")

    def input_text(self, hwnd: int, physical_x: int = None, physical_y: int = None,
                   virtual_x: int = None, virtual_y: int = None, text: str = None, newline_key: str = None,
                   action_method: str = "background") -> InjectResult:
        """输入文本 - 支持可选坐标

        Args:
            hwnd: 窗口句柄
            physical_x/y: 可选，物理坐标（已弃用，保留兼容）
            virtual_x/y: 可选，虚拟坐标（background/hijack 都使用）
            text: 输入文本
            newline_key: 换行键
            action_method: background / hijack / delegated
        """
        effective = self._effective_method(action_method)
        has_coord = virtual_x is not None and virtual_y is not None
        if effective == "delegated":
            if self._delegated_input_text(hwnd, virtual_x, virtual_y, text, has_coord):
                return InjectResult(True, None, "delegated")
            return self._fail_result("Input text", "delegated")
        if effective == "hijack":
            # hijack 需要屏幕坐标
            if has_coord:
                screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
                if self._hijack_input_text(hwnd, screen_x, screen_y, text, restore_state=True):
                    return InjectResult(True, None, "hijack")
            else:
                # 无坐标 hijack，直接执行
                if self._hijack_input_text(hwnd, None, None, text, restore_state=True):
                    return InjectResult(True, None, "hijack")
            return self._fail_result("Input text", "hijack")
        # background 使用 virtual 坐标
        import logging
        logger = logging.getLogger(__name__)
        if has_coord:
            if self._background_input_text(hwnd, virtual_x, virtual_y, text, newline_key):
                return InjectResult(True, None, "background")
        else:
            # 无坐标 background，直接输入
            if self._background_input_text(hwnd, None, None, text, newline_key):
                return InjectResult(True, None, "background")
        return self._fail_result("Input text", "background")

    def key_press(self, hwnd: int, key: str,
                  physical_x: int = None, physical_y: int = None,
                  virtual_x: int = None, virtual_y: int = None,
                  duration_ms: int = 0, action_method: str = "background",
                  non_blocking: bool = False) -> InjectResult:
        """按键操作

        Args:
            hwnd: 窗口句柄
            key: 按键，空格分隔如 "ctrl c"
            physical_x/y: 可选，先点击的物理坐标（已弃用，保留兼容）
            virtual_x/y: 可选，先点击的虚拟坐标（background/hijack 都使用）
            duration_ms: 按住时长，0=立即释放
            action_method: background / hijack
            non_blocking: True 时用 Popen（不等待完成），用于 batch 并发
        """
        effective = self._effective_method(action_method)
        if effective == "delegated":
            if self._delegated_key_press(hwnd, key, virtual_x, virtual_y,
                                       duration_ms, non_blocking):
                return InjectResult(True, None, "delegated")
            return self._fail_result("Key press", "delegated")
        if effective == "hijack":
            if self._hijack_key_press(hwnd, key, virtual_x, virtual_y,
                                      duration_ms, non_blocking, restore_state=True):
                return InjectResult(True, None, "hijack")
            return self._fail_result("Key press", "hijack")
        # background 使用 virtual 坐标
        if self._background_key_press(hwnd, key, virtual_x, virtual_y,
                                      duration_ms, non_blocking):
            return InjectResult(True, None, "background")
        return self._fail_result("Key press", "background")

    # ============ background 实现（无感操作）============

    def _background_click(self, hwnd: int, x: int, y: int) -> bool:
        """Background 点击 - 使用 virtual 坐标（API层已处理最小化恢复）"""
        code = f'''
import win32gui, win32api, win32con

hwnd = {hwnd}
x = {x}
y = {y}

# API 层已经处理了最小化恢复，直接 PostMessage
lParam = win32api.MAKELONG(x, y)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
'''
        return self._run_subprocess(code, timeout=5)

    def _background_right_click(self, hwnd: int, x: int, y: int) -> bool:
        """Background 右键点击"""
        code = f'''
import win32gui, win32api, win32con, time
hwnd, x, y = {hwnd}, {x}, {y}
lParam = win32api.MAKELONG(x, y)
win32gui.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, 0x0002, lParam)
time.sleep(0.05)
win32gui.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lParam)
'''
        return self._run_subprocess(code, timeout=5)

    def _background_long_press(self, hwnd: int, x: int, y: int, duration_ms: int) -> bool:
        """Background 长按"""
        code = f'''
import win32gui, win32api, win32con, time
hwnd, x, y, duration_ms = {hwnd}, {x}, {y}, {duration_ms}
lParam = win32api.MAKELONG(x, y)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam)
time.sleep(duration_ms / 1000)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
'''
        return self._run_subprocess(code, timeout=max(10, duration_ms / 1000 + 5))

    def _background_swipe(self, hwnd: int, sx: int, sy: int, ex: int, ey: int) -> bool:
        """Background 滑动 - 10步插值，使用 virtual 坐标"""
        code = f'''
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
        return self._run_subprocess(code, timeout=10)

    def _background_drag(self, hwnd: int, sx: int, sy: int, ex: int, ey: int,
                         duration_ms: int = 500) -> bool:
        """Background 拖拽 - 10步插值，duration_ms 参数化，使用 virtual 坐标"""
        duration = duration_ms / 1000.0
        code = f'''
import win32gui, win32api, win32con, time

hwnd = {hwnd}
sx = {sx}
sy = {sy}
ex = {ex}
ey = {ey}
duration = {duration}

lParam_start = win32api.MAKELONG(sx, sy)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam_start)
time.sleep(0.05)

# 分步移动
steps = 10
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
        timeout = max(10, int(duration_ms / 1000) + 5)
        return self._run_subprocess(code, timeout=timeout)

    def _background_mouse_move_not_supported(self):
        """Background 模式不支持 mouse_move - 游戏读 Raw Input，PostMessage 无效"""
        return False

    def _background_scroll(self, hwnd: int, virtual_x: int, virtual_y: int, delta: int) -> bool:
        """PostMessage WM_MOUSEWHEEL，lParam 使用屏幕坐标"""
        code = f'''
import win32gui, win32api, win32con

hwnd = {hwnd}
delta = {delta}

# 客户区虚拟坐标 → 屏幕坐标
screen_x, screen_y = win32gui.ClientToScreen(hwnd, ({virtual_x}, {virtual_y}))
lParam = win32api.MAKELONG(screen_x, screen_y)
wParam = (delta << 16) & 0xFFFF0000
win32gui.PostMessage(hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)
'''
        return self._run_subprocess(code, timeout=5)

    def _background_hover(self, hwnd: int, x: int, y: int, duration_ms: int,
                         semi_blocking: bool = False) -> bool:
        """Background 鼠标悬浮 - 只发送 WM_MOUSEMOVE（不按下鼠标）"""
        code = f'''
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
        timeout = max(5, duration_ms / 1000 + 5) if duration_ms > 0 else 5
        return self._run_subprocess(code, timeout=int(timeout), semi_blocking=semi_blocking)

    def _background_input_text(self, hwnd: int, x: int, y: int, text: str, newline_key: str) -> bool:
        """PostMessage点击 → SendMessage WM_CHAR逐字符 + 换行键

        支持 None 坐标：无坐标时不点击，直接输入文本
        换行处理：根据 newline_key 参数模拟换行按键（默认 shift enter）
        """
        import logging
        logger = logging.getLogger(__name__)

        # 确保 newline_key 有默认值
        if newline_key is None:
            newline_key = "shift enter"

        # 解析换行键（如 "shift enter" → [{0x10}, {0x0D}]）
        newline_parts = newline_key.strip().split()
        newline_vks = []
        for part in newline_parts:
            part_lower = part.lower()
            if part_lower in self._key_map:
                newline_vks.append(self._key_map[part_lower])
            elif len(part) == 1:
                newline_vks.append(ord(part.upper()))

        newline_vks_b64 = base64.b64encode(str(newline_vks).encode('utf-8')).decode('ascii')
        text_b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')

        # 判断是否有坐标
        has_coord = x is not None and y is not None

        code = f'''
import win32gui, win32api, win32con, time, base64, ctypes

hwnd = {hwnd}
has_coord = {has_coord}
text = base64.b64decode("{text_b64}").decode("utf-8")
newline_vks = eval(base64.b64decode("{newline_vks_b64}").decode("utf-8"))

# 如果有坐标，PostMessage 点击获取焦点
if has_coord:
    x, y = {x}, {y}
    lParam = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
    time.sleep(0.1)

# 逐字符发送
for char in text:
    if char == '\\n':
        # 换行：keybd_event 模拟按键（短暂，影响范围可控）
        for vk in newline_vks:
            scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
            ctypes.windll.user32.keybd_event(vk, scan, 0, 0)
            time.sleep(0.02)
        for vk in reversed(newline_vks):
            scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
            ctypes.windll.user32.keybd_event(vk, scan, 2, 0)
            time.sleep(0.02)
    else:
        char_code = ord(char)
        vk = ord(char.upper()) if char.isalpha() else char_code
        scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
        lParam_char = (scan << 16) | 1
        win32gui.SendMessage(hwnd, win32con.WM_CHAR, char_code, lParam_char)
    time.sleep(0.03)
'''
        timeout = max(30, len(text) * 0.05 + 5)
        return self._run_subprocess(code, timeout=int(timeout))

    def _background_key_press(self, hwnd: int, key: str,
                              physical_x: int = None, physical_y: int = None,
                              virtual_x: int = None, virtual_y: int = None,
                              duration_ms: int = 0, non_blocking: bool = False) -> bool:
        """混合方案: keybd_event修饰键 + SendMessage主键"""
        parsed = self._parse_keys(key)
        if parsed is None:
            return False

        modifiers, main_vk = parsed
        main_scan = ctypes.windll.user32.MapVirtualKeyW(main_vk, 0)

        # 构建修饰键的 keybd_event 代码
        mod_press_lines = []
        mod_release_lines = []
        for mod_vk in modifiers:
            mod_scan = ctypes.windll.user32.MapVirtualKeyW(mod_vk, 0)
            mod_press_lines.append(f'ctypes.windll.user32.keybd_event({mod_vk}, {mod_scan}, 0, 0)')
            mod_release_lines.append(f'ctypes.windll.user32.keybd_event({mod_vk}, {mod_scan}, 2, 0)')

        mod_press = '\n    '.join(mod_press_lines)
        mod_release = '\n    '.join(reversed(mod_release_lines))

        # 可选的先点击代码 - 使用 virtual 坐标
        click_code = ''
        if virtual_x is not None and virtual_y is not None:
            click_code = f'''
# 先点击目标位置
lParam = win32api.MAKELONG({virtual_x}, {virtual_y})
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam)
time.sleep(0.05)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
time.sleep(0.1)
'''

        # lParam 构造
        lparam_down = (main_scan << 16) | 1
        lparam_up = (main_scan << 16) | 0xC0000001

        # duration_ms 的 sleep
        hold_sleep = f'time.sleep({duration_ms} / 1000.0)' if duration_ms > 0 else ''

        code = f'''
import win32gui, win32con, win32api, ctypes, time

hwnd = {hwnd}

{click_code}
# 按下修饰键
{mod_press}
time.sleep(0.05)

# SendMessage 主键
win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, {main_vk}, {lparam_down})
{hold_sleep}
win32gui.SendMessage(hwnd, win32con.WM_KEYUP, {main_vk}, {lparam_up})
time.sleep(0.05)

# 释放修饰键
{mod_release}
'''
        timeout = max(5, duration_ms / 1000 + 5) if duration_ms > 0 else 5
        return self._run_subprocess(code, timeout=int(timeout), non_blocking=non_blocking)

    # ============ hijack 实现（劫持操作）============

    def _hijack_click(self, hwnd: int, virtual_x: int, virtual_y: int,
                      restore_state: bool = True) -> bool:
        """Hijack 点击 - 接收 virtual 坐标（API层已处理最小化恢复）"""
        restore_code = self._build_restore_code(restore_state)
        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

hwnd = {hwnd}
virtual_x = {virtual_x}
virtual_y = {virtual_y}

# API 层已经处理了最小化恢复，直接计算屏幕坐标
screen_x, screen_y = win32gui.ClientToScreen(hwnd, (virtual_x, virtual_y))

# Hijack 模式：设置焦点并点击
main_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd
target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.3)

win32api.SetCursorPos((screen_x, screen_y))
time.sleep(0.3)

# 用 SendMessage 点击（virtual_x, virtual_y 是客户区坐标）
lParam = win32api.MAKELONG(virtual_x, virtual_y)
win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam)
time.sleep(0.05)
win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)

{restore_code}
'''
        return self._run_subprocess(code, timeout=10)

    def _hijack_right_click(self, hwnd: int, screen_x: int, screen_y: int,
                            restore_state: bool = True) -> bool:
        """Hijack 右键 - 用 win32api 绕过 pyautogui 多屏限制"""
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        restore_code = self._build_restore_code(restore_state)
        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

hwnd = {hwnd}
main_hwnd = {main_hwnd}
screen_x = {screen_x}
screen_y = {screen_y}

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
    time.sleep(0.1)

target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.1)

win32api.SetCursorPos((screen_x, screen_y))
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

{restore_code}
'''
        return self._run_subprocess(code, timeout=10)

    def _hijack_long_press(self, hwnd: int, screen_x: int, screen_y: int, duration_ms: int,
                           restore_state: bool = True) -> bool:
        """Hijack 长按 - 用 win32api 绕过 pyautogui 多屏限制"""
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        restore_code = self._build_restore_code(restore_state)
        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

hwnd = {hwnd}
main_hwnd = {main_hwnd}
screen_x = {screen_x}
screen_y = {screen_y}
duration_ms = {duration_ms}

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
    time.sleep(0.1)

target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.1)

win32api.SetCursorPos((screen_x, screen_y))
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(duration_ms / 1000)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

{restore_code}
'''
        return self._run_subprocess(code, timeout=max(10, duration_ms / 1000 + 5))

    def _hijack_swipe(self, hwnd: int, sx: int, sy: int, ex: int, ey: int,
                      restore_state: bool = True) -> bool:
        """Hijack 滑动 - 10步插值 + win32api（支持多屏）"""
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        restore_code = self._build_restore_code(restore_state)
        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

main_hwnd = {main_hwnd}
sx = {sx}
sy = {sy}
ex = {ex}
ey = {ey}

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
    time.sleep(0.1)

target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.1)

# 用 win32api 模拟拖拽
win32api.SetCursorPos((sx, sy))
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

# 按下左键
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)

# 分步移动到终点
steps = 10
duration = 0.3
step_delay = duration / steps

for i in range(1, steps + 1):
    progress = i / steps
    cx = int(sx + (ex - sx) * progress)
    cy = int(sy + (ey - sy) * progress)
    win32api.SetCursorPos((cx, cy))
    time.sleep(step_delay)

# 释放左键
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

{restore_code}
'''
        return self._run_subprocess(code, timeout=15)

    def _hijack_drag(self, hwnd: int, sx: int, sy: int, ex: int, ey: int,
                     duration_ms: int = 500, restore_state: bool = True,
                     target_hwnd: int = None) -> bool:
        """Hijack 拖拽 - 10步插值 + duration_ms 参数化 + win32api（支持多屏）"""
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        duration = duration_ms / 1000.0
        restore_code = self._build_restore_code(restore_state)

        # 跨窗口拖拽：预计算目标主窗口
        target_main_hwnd = "None"
        if target_hwnd:
            target_main_hwnd = f"ctypes.windll.user32.GetAncestor({target_hwnd}, 2) or {target_hwnd}"

        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

main_hwnd = {main_hwnd}
sx = {sx}
sy = {sy}
ex = {ex}
ey = {ey}
duration = {duration}
target_main_hwnd = {target_main_hwnd}

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
    time.sleep(0.1)

# 跨窗口拖拽：提前确保目标窗口可见（不激活，仅恢复）
if target_main_hwnd:
    if win32gui.IsIconic(target_main_hwnd):
        win32gui.ShowWindow(target_main_hwnd, win32con.SW_RESTORE)
        time.sleep(0.2)
    elif not win32gui.IsWindowVisible(target_main_hwnd):
        win32gui.ShowWindow(target_main_hwnd, win32con.SW_SHOW)
        time.sleep(0.1)

target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.1)

# 用 win32api 模拟拖拽
win32api.SetCursorPos((sx, sy))
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

# 按下左键
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)

# 分步移动到终点
steps = 10
step_delay = duration / steps
mid = steps // 2

for i in range(1, steps + 1):
    progress = i / steps
    cx = int(sx + (ex - sx) * progress)
    cy = int(sy + (ey - sy) * progress)
    win32api.SetCursorPos((cx, cy))
    # 跨窗口拖拽：在 midpoint 激活目标窗口，使其浮到源窗口之上
    if target_main_hwnd and i == mid:
        target_tid2 = ctypes.windll.user32.GetWindowThreadProcessId(target_main_hwnd, None)
        ctypes.windll.user32.AttachThreadInput(current_tid, target_tid2, True)
        win32gui.SetForegroundWindow(target_main_hwnd)
        time.sleep(0.15)
    time.sleep(step_delay)

# 释放左键
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

{restore_code}
'''
        timeout = max(15, int(duration_ms / 1000) + 10)
        return self._run_subprocess(code, timeout=timeout)

    def _hijack_mouse_move(self, hwnd: int, delta_x: int, delta_y: int,
                           duration_ms: int = 300, restore_state: bool = True) -> bool:
        """Hijack 鼠标移动 - mouse_event(MOUSEEVENTF_MOVE) 分步相对移动，可被游戏 Raw Input 识别"""
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        duration = duration_ms / 1000.0
        restore_code = self._build_restore_code(restore_state)
        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

main_hwnd = {main_hwnd}
delta_x = {delta_x}
delta_y = {delta_y}
duration = {duration}

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
    time.sleep(0.1)

target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.1)

# 分步发送相对移动事件
MOUSEEVENTF_MOVE = 0x0001
steps = 10
step_dx = delta_x / steps
step_dy = delta_y / steps
step_delay = duration / steps

for i in range(steps):
    dx = int(round(step_dx))
    dy = int(round(step_dy))
    # 处理余数：最后一步补偿
    if i == steps - 1:
        dx = delta_x - int(round(step_dx)) * (steps - 1)
        dy = delta_y - int(round(step_dy)) * (steps - 1)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)
    time.sleep(step_delay)

{restore_code}
'''
        timeout = max(15, int(duration_ms / 1000) + 10)
        return self._run_subprocess(code, timeout=timeout)

    def _hijack_scroll(self, hwnd: int, screen_x: int, screen_y: int, delta: int,
                       restore_state: bool = True) -> bool:
        """Hijack 滚动 - 用 win32api 绕过 pyautogui 多屏限制"""
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        wheel_delta = delta
        restore_code = self._build_restore_code(restore_state)
        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

hwnd = {hwnd}
main_hwnd = {main_hwnd}
screen_x = {screen_x}
screen_y = {screen_y}
wheel_delta = {wheel_delta}

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
    time.sleep(0.1)

target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.1)

win32api.SetCursorPos((screen_x, screen_y))
MOUSEEVENTF_WHEEL = 0x0800
ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, wheel_delta, 0)

{restore_code}
'''
        return self._run_subprocess(code, timeout=10)

    def _hijack_hover(self, hwnd: int, screen_x: int, screen_y: int, duration_ms: int,
                     semi_blocking: bool = False, restore_state: bool = True) -> bool:
        """Hijack 鼠标悬浮 - SetCursorPos + sleep(duration_ms) + 恢复"""
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        restore_code = self._build_restore_code(restore_state)
        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

main_hwnd = {main_hwnd}
hwnd = {hwnd}
screen_x = {screen_x}
screen_y = {screen_y}
duration_ms = {duration_ms}

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
    time.sleep(0.1)

target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.1)

# 用 win32api 移动鼠标到目标位置
win32api.SetCursorPos((screen_x, screen_y))

# 停留指定时长
if duration_ms > 0:
    time.sleep(duration_ms / 1000.0)

{restore_code}
'''
        timeout = max(5, duration_ms / 1000 + 5) if duration_ms > 0 else 5
        return self._run_subprocess(code, timeout=int(timeout), semi_blocking=semi_blocking)

    def _hijack_input_text(self, hwnd: int, screen_x: int, screen_y: int, text: str,
                           restore_state: bool = True) -> bool:
        """Hijack 输入文本 - 用 win32api 绕过 pyautogui 多屏限制

        支持 None 坐标：无坐标时不点击，直接粘贴
        """
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        text_b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')
        restore_code = self._build_restore_code(restore_state)

        # 判断是否有坐标
        has_coord = screen_x is not None and screen_y is not None

        code = f'''
import win32gui, win32api, win32con, ctypes, time, base64
import pyperclip

text = base64.b64decode("{text_b64}").decode("utf-8")

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

main_hwnd = {main_hwnd}
screen_x = {screen_x}
screen_y = {screen_y}
has_coord = {has_coord}

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
    time.sleep(0.1)

target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.1)

if has_coord:
    win32api.SetCursorPos((screen_x, screen_y))
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.2)

pyperclip.copy(text)
time.sleep(0.1)

VK_CONTROL = 0x11
VK_V = 0x56
scan_ctrl = ctypes.windll.user32.MapVirtualKeyW(VK_CONTROL, 0)
scan_v = ctypes.windll.user32.MapVirtualKeyW(VK_V, 0)

ctypes.windll.user32.keybd_event(VK_CONTROL, scan_ctrl, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(VK_V, scan_v, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(VK_V, scan_v, 2, 0)
time.sleep(0.05)
ctypes.windll.user32.keybd_event(VK_CONTROL, scan_ctrl, 2, 0)
time.sleep(0.1)

{restore_code}
'''
        return self._run_subprocess(code, timeout=30)

    def _hijack_key_press(self, hwnd: int, key: str,
                          virtual_x: int = None, virtual_y: int = None,
                          duration_ms: int = 0, non_blocking: bool = False,
                          restore_state: bool = True) -> bool:
        """Hijack 按键 - 用 win32api 绕过 pyautogui 多屏限制

        关键点：激活窗口后需要足够延迟确保焦点稳定（150ms）
        """
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        restore_code = self._build_restore_code(restore_state)
        parsed = self._parse_keys(key)
        if parsed is None:
            return False

        modifiers, main_vk = parsed
        all_vks = modifiers + [main_vk]

        # 构建按键代码
        press_lines = []
        release_lines = []
        for vk in all_vks:
            scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
            press_lines.append(f'ctypes.windll.user32.keybd_event({vk}, {scan}, 0, 0)')
        for vk in reversed(all_vks):
            scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
            release_lines.append(f'ctypes.windll.user32.keybd_event({vk}, {scan}, 2, 0)')

        all_press = '\n'.join(press_lines)
        all_release = '\n'.join(release_lines)

        # 可选的先点击代码
        click_code = ''
        if virtual_x is not None and virtual_y is not None:
            screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
            click_code = f'''
# 用 win32api 点击目标位置
win32api.SetCursorPos(({screen_x}, {screen_y}))
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(0.1)
'''

        hold_sleep = f'time.sleep({duration_ms} / 1000.0)' if duration_ms > 0 else ''

        code = f'''
import win32gui, win32api, win32con, ctypes, time

hwnd = {hwnd}
main_hwnd = {main_hwnd}

# 保存状态
old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
    time.sleep(0.1)

target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.1)

{click_code}

# 按下所有键
{all_press}
time.sleep(0.05)
{hold_sleep}
# 释放所有键
{all_release}
time.sleep(0.05)

{restore_code}
'''
        timeout = max(5, duration_ms / 1000 + 5) if duration_ms > 0 else 5
        return self._run_subprocess(code, timeout=int(timeout), non_blocking=non_blocking)

    # ============ 辅助方法 ============

    def _run_subprocess(self, code: str, timeout: int = 5,
                        non_blocking: bool = False, semi_blocking: bool = False) -> bool:
        """在子进程中执行代码

        Args:
            code: Python 代码字符串
            timeout: 超时秒数
            non_blocking: True 时用 Popen 不等待完成（用于 duration_ms 的并发按键）
            semi_blocking: True 时启动子进程后等待 100ms（用于 hover 等待鼠标到位）

        Note:
            打包环境(frozen)使用嵌入的 Python 解释器创建子进程。
            开发环境使用 sys.executable。

            非阻塞模式下返回 True 仅表示"消息已投递"，不代表目标窗口已完成操作。
            _last_error 捕获的是子进程自身的启动/执行错误，不是目标窗口的响应。
        """
        self._last_error = None
        is_frozen = getattr(sys, 'frozen', False)

        if is_frozen:
            import os
            python_exe = os.path.join(sys._MEIPASS, 'embed_python', 'python.exe')
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.join(sys._MEIPASS, 'embed_python')
        else:
            python_exe = sys.executable
            env = None

        try:
            if non_blocking or semi_blocking:
                proc = subprocess.Popen(
                    [python_exe, '-c', code],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    env=env
                )
                if semi_blocking:
                    time.sleep(0.2)
                    if proc.poll() is not None:
                        self._last_error = (proc.stderr.read() or b"").decode("utf-8", errors="replace").strip()
                        return False
                else:
                    time.sleep(0.01)
                    if proc.poll() is not None:
                        self._last_error = (proc.stderr.read() or b"").decode("utf-8", errors="replace").strip()
                        return False
                return True
            else:
                result = subprocess.run(
                    [python_exe, '-c', code],
                    capture_output=True, text=True, timeout=timeout,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    env=env
                )
                if result.returncode != 0:
                    self._last_error = result.stderr.strip() if result.stderr else None
                return result.returncode == 0
        except Exception as e:
            self._last_error = str(e)
            return False

    def _client_to_screen(self, hwnd: int, x: int, y: int) -> Tuple[int, int]:
        """客户区坐标转屏幕坐标"""
        return win32gui.ClientToScreen(hwnd, (x, y))

    def _parse_keys(self, key: str) -> Optional[Tuple[List[int], int]]:
        """解析按键字符串，返回 (修饰键列表, 主键VK)

        按键用空格分隔，如 "ctrl shift s"
        最后一个非修饰键作为主键
        """
        parts = key.strip().split()
        if not parts:
            return None

        vks = []
        for part in parts:
            part_lower = part.lower()
            if part_lower in self._key_map:
                vks.append(self._key_map[part_lower])
            elif len(part) == 1:
                vks.append(ord(part.upper()))
            else:
                return None

        # 分离修饰键和主键：最后一个非修饰键是主键
        main_idx = len(vks) - 1
        for i in range(len(vks) - 1, -1, -1):
            if vks[i] not in MODIFIER_VKS:
                main_idx = i
                break

        modifiers = vks[:main_idx]
        main_vk = vks[main_idx]

        return modifiers, main_vk


# 全局操作注入实例
windows_input = WindowsInputInjector()

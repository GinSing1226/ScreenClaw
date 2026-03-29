"""
Windows操作注入实现
支持 background(无感) / hijack(劫持) 两种模式
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

# Cached code templates for background operations
from app.platform.windows._code_templates import (
    _get_background_click_template,
    _get_background_right_click_template,
    _get_background_long_press_template,
    _get_background_swipe_template,
    _get_background_scroll_template,
    _get_background_hover_template,
)


@dataclass
class InjectResult:
    """操作注入结果"""
    success: bool
    error: Optional[str]
    method: str  # "background" | "hijack"


# 修饰键 VK 集合
MODIFIER_VKS = {0x11, 0x12, 0x10, 0x5B}  # Ctrl, Alt, Shift, Win


class WindowsInputInjector:
    """Windows操作注入 - background/hijack 双模式 + 子进程隔离"""

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

    # ============ 公共方法 ============

    def click(self, hwnd: int, physical_x: int, physical_y: int,
              virtual_x: int, virtual_y: int,
              action_method: str = "background") -> InjectResult:
        # 传递 virtual 坐标，子进程内处理最小化恢复和坐标计算
        if action_method == "hijack":
            if self._hijack_click(hwnd, virtual_x, virtual_y):
                return InjectResult(True, None, "hijack")
            return InjectResult(False, "点击操作失败", "hijack")
        if self._background_click(hwnd, virtual_x, virtual_y):
            return InjectResult(True, None, "background")
        return InjectResult(False, "点击操作失败", "background")

    def right_click(self, hwnd: int, physical_x: int, physical_y: int,
                    virtual_x: int, virtual_y: int,
                    action_method: str = "background") -> InjectResult:
        if action_method == "hijack":
            screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
            if self._hijack_right_click(hwnd, screen_x, screen_y):
                return InjectResult(True, None, "hijack")
            return InjectResult(False, "右键操作失败", "hijack")
        # background 使用 virtual 坐标
        if self._background_right_click(hwnd, virtual_x, virtual_y):
            return InjectResult(True, None, "background")
        return InjectResult(False, "右键操作失败", "background")

    def long_press(self, hwnd: int, physical_x: int, physical_y: int,
                   virtual_x: int, virtual_y: int, duration_ms: int,
                   action_method: str = "background") -> InjectResult:
        if action_method == "hijack":
            screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
            if self._hijack_long_press(hwnd, screen_x, screen_y, duration_ms):
                return InjectResult(True, None, "hijack")
            return InjectResult(False, "长按操作失败", "hijack")
        # background 使用 virtual 坐标
        if self._background_long_press(hwnd, virtual_x, virtual_y, duration_ms):
            return InjectResult(True, None, "background")
        return InjectResult(False, "长按操作失败", "background")

    def swipe(self, hwnd: int,
              physical_sx: int, physical_sy: int, physical_ex: int, physical_ey: int,
              virtual_sx: int, virtual_sy: int, virtual_ex: int, virtual_ey: int,
              action_method: str = "background") -> InjectResult:
        if action_method == "hijack":
            ss = self._client_to_screen(hwnd, virtual_sx, virtual_sy)
            se = self._client_to_screen(hwnd, virtual_ex, virtual_ey)
            if self._hijack_swipe(hwnd, ss[0], ss[1], se[0], se[1]):
                return InjectResult(True, None, "hijack")
            return InjectResult(False, "滑动操作失败", "hijack")
        # background 使用 virtual 坐标（与 click 一致，修复 DPI 缩放问题）
        if self._background_swipe(hwnd, virtual_sx, virtual_sy, virtual_ex, virtual_ey):
            return InjectResult(True, None, "background")
        return InjectResult(False, "滑动操作失败", "background")

    def scroll(self, hwnd: int, physical_x: int, physical_y: int,
               virtual_x: int, virtual_y: int, delta: int,
               action_method: str = "background") -> InjectResult:
        if action_method == "hijack":
            screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
            if self._hijack_scroll(hwnd, screen_x, screen_y, delta):
                return InjectResult(True, None, "hijack")
            return InjectResult(False, "滚动操作失败", "hijack")
        if self._background_scroll(hwnd, virtual_x, virtual_y, delta):
            return InjectResult(True, None, "background")
        return InjectResult(False, "滚动操作失败", "background")

    def hover(self, hwnd: int, physical_x: int, physical_y: int,
              virtual_x: int, virtual_y: int, duration_ms: int,
              action_method: str = "background") -> InjectResult:
        """鼠标悬浮 - 移动到目标位置并停留 duration_ms

        半阻塞模式：等待鼠标到位（100ms）后返回，hover 持续时间在后台继续执行

        Args:
            hwnd: 窗口句柄
            physical_x/y: 物理坐标（已弃用，保留兼容）
            virtual_x/y: 虚拟坐标
            duration_ms: 停留时长（毫秒）
            action_method: background / hijack
        """
        if action_method == "hijack":
            screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
            # 半阻塞：等待鼠标到位后再返回
            success = self._hijack_hover(hwnd, screen_x, screen_y, duration_ms, semi_blocking=True)
            if success:
                return InjectResult(True, None, "hijack")
            return InjectResult(False, "悬浮操作失败", "hijack")
        # background 也是半阻塞
        success = self._background_hover(hwnd, virtual_x, virtual_y, duration_ms, semi_blocking=True)
        if success:
            return InjectResult(True, None, "background")
        return InjectResult(False, "悬浮操作失败", "background")

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
            action_method: background / hijack
        """
        if action_method == "hijack":
            # hijack 需要屏幕坐标
            if virtual_x is not None and virtual_y is not None:
                screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
                if self._hijack_input_text(hwnd, screen_x, screen_y, text):
                    return InjectResult(True, None, "hijack")
            else:
                # 无坐标 hijack，直接执行
                if self._hijack_input_text(hwnd, None, None, text):
                    return InjectResult(True, None, "hijack")
            return InjectResult(False, "输入文本失败", "hijack")
        # background 使用 virtual 坐标
        if virtual_x is not None and virtual_y is not None:
            if self._background_input_text(hwnd, virtual_x, virtual_y, text, newline_key):
                return InjectResult(True, None, "background")
        else:
            # 无坐标 background，直接输入
            if self._background_input_text(hwnd, None, None, text, newline_key):
                return InjectResult(True, None, "background")
        return InjectResult(False, "输入文本失败", "background")

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
        if action_method == "hijack":
            if self._hijack_key_press(hwnd, key, virtual_x, virtual_y,
                                      duration_ms, non_blocking):
                return InjectResult(True, None, "hijack")
            return InjectResult(False, "按键操作失败", "hijack")
        # background 使用 virtual 坐标
        if self._background_key_press(hwnd, key, virtual_x, virtual_y,
                                      duration_ms, non_blocking):
            return InjectResult(True, None, "background")
        return InjectResult(False, "按键操作失败", "background")

    # ============ background 实现（无感操作）============

    def _background_click(self, hwnd: int, x: int, y: int) -> bool:
        """Background 点击 - 使用 virtual 坐标（API层已处理最小化恢复）"""
        code = _get_background_click_template(hwnd, x, y)
        return self._run_subprocess(code, timeout=5)

    def _background_right_click(self, hwnd: int, x: int, y: int) -> bool:
        """Background 右键点击"""
        code = _get_background_right_click_template(hwnd, x, y)
        return self._run_subprocess(code, timeout=5)

    def _background_long_press(self, hwnd: int, x: int, y: int, duration_ms: int) -> bool:
        """Background 长按"""
        code = _get_background_long_press_template(hwnd, x, y, duration_ms)
        return self._run_subprocess(code, timeout=max(10, duration_ms / 1000 + 5))

    def _background_swipe(self, hwnd: int, sx: int, sy: int, ex: int, ey: int) -> bool:
        """Background 滑动 - 10步插值，使用 virtual 坐标"""
        code = _get_background_swipe_template(hwnd, sx, sy, ex, ey)
        return self._run_subprocess(code, timeout=10)

    def _background_scroll(self, hwnd: int, virtual_x: int, virtual_y: int, delta: int) -> bool:
        """PostMessage WM_MOUSEWHEEL，lParam 使用屏幕坐标"""
        code = _get_background_scroll_template(hwnd, virtual_x, virtual_y, delta)
        return self._run_subprocess(code, timeout=5)

    def _background_hover(self, hwnd: int, x: int, y: int, duration_ms: int,
                         semi_blocking: bool = False) -> bool:
        """Background 鼠标悬浮 - 只发送 WM_MOUSEMOVE（不按下鼠标）"""
        code = _get_background_hover_template(hwnd, x, y, duration_ms)
        timeout = max(5, duration_ms / 1000 + 5) if duration_ms > 0 else 5
        return self._run_subprocess(code, timeout=int(timeout), semi_blocking=semi_blocking)

    def _background_input_text(self, hwnd: int, x: int, y: int, text: str, newline_key: str) -> bool:
        """PostMessage点击 → SendMessage WM_CHAR逐字符 + 换行键

        支持 None 坐标：无坐标时不点击，直接输入文本
        换行处理：根据 newline_key 参数模拟换行按键（默认 shift enter）
        """
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
    print("[BgInputText] Clicking at client coords=(%d, %d), hwnd=%d" % (x, y, hwnd))
    lParam = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
    time.sleep(0.1)
    print("[BgInputText] Click done")

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

    def _hijack_click(self, hwnd: int, virtual_x: int, virtual_y: int) -> bool:
        """Hijack 点击 - 接收 virtual 坐标（API层已处理最小化恢复）"""
        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

hwnd = {hwnd}
virtual_x = {virtual_x}
virtual_y = {virtual_y}

# API 层已经处理了最小化恢复，直接计算屏幕坐标
screen_x, screen_y = win32gui.ClientToScreen(hwnd, (virtual_x, virtual_y))
print("[HijackClick] virtual=(%d, %d), screen=(%d, %d)" % (virtual_x, virtual_y, screen_x, screen_y))

# Hijack 模式：设置焦点并点击
main_hwnd = ctypes.windll.user32.GetAncestor(hwnd, 2) or hwnd
print("[HijackClick] Setting foreground window...")
target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.3)

print("[HijackClick] Setting cursor to (%d, %d)..." % (screen_x, screen_y))
win32api.SetCursorPos((screen_x, screen_y))
actual_pos = win32api.GetCursorPos()
print("[HijackClick] Actual cursor pos: (%d, %d)" % (actual_pos[0], actual_pos[1]))
time.sleep(0.3)

# 用 SendMessage 点击（virtual_x, virtual_y 是客户区坐标）
lParam = win32api.MAKELONG(virtual_x, virtual_y)
print("[HijackClick] SendMessage click to hwnd=%d, client=(%d, %d)" % (hwnd, virtual_x, virtual_y))
win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam)
time.sleep(0.05)
win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)

# 恢复状态
print("[HijackClick] Restoring state...")
try:
    time.sleep(0.01)
    win32api.SetCursorPos(old_pos)
    win32gui.SetForegroundWindow(old_fg)
except:
    pass
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
print("[HijackClick] Done")
'''
        return self._run_subprocess(code, timeout=10)

    def _hijack_right_click(self, hwnd: int, screen_x: int, screen_y: int) -> bool:
        """Hijack 右键 - 用 win32api 绕过 pyautogui 多屏限制"""
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

hwnd = {hwnd}
main_hwnd = {main_hwnd}
screen_x = {screen_x}
screen_y = {screen_y}

print("[HijackRightClick] hwnd=%d, main=%d, target_screen=(%d, %d)" % (hwnd, main_hwnd, screen_x, screen_y))

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    print("[HijackRightClick] Main window is minimized, restoring...")
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    print("[HijackRightClick] Main window not visible, showing...")
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

time.sleep(0.01)
win32api.SetCursorPos(old_pos)
win32gui.SetForegroundWindow(old_fg)
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        return self._run_subprocess(code, timeout=10)

    def _hijack_long_press(self, hwnd: int, screen_x: int, screen_y: int, duration_ms: int) -> bool:
        """Hijack 长按 - 用 win32api 绕过 pyautogui 多屏限制"""
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

hwnd = {hwnd}
main_hwnd = {main_hwnd}
screen_x = {screen_x}
screen_y = {screen_y}
duration_ms = {duration_ms}

print("[HijackLongPress] hwnd=%d, main=%d, target_screen=(%d, %d), duration=%dms" % (hwnd, main_hwnd, screen_x, screen_y, duration_ms))

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    print("[HijackLongPress] Main window is minimized, restoring...")
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    print("[HijackLongPress] Main window not visible, showing...")
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

time.sleep(0.01)
win32api.SetCursorPos(old_pos)
win32gui.SetForegroundWindow(old_fg)
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        return self._run_subprocess(code, timeout=max(10, duration_ms / 1000 + 5))

    def _hijack_swipe(self, hwnd: int, sx: int, sy: int, ex: int, ey: int) -> bool:
        """Hijack 滑动 - 10步插值 + win32api（支持多屏）"""
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
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
    print("[HijackSwipe] Main window is minimized, restoring...")
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    print("[HijackSwipe] Main window not visible, showing...")
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

time.sleep(0.01)
win32api.SetCursorPos(old_pos)
win32gui.SetForegroundWindow(old_fg)
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        return self._run_subprocess(code, timeout=15)

    def _hijack_scroll(self, hwnd: int, screen_x: int, screen_y: int, delta: int) -> bool:
        """Hijack 滚动 - 用 win32api 绕过 pyautogui 多屏限制"""
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        wheel_delta = delta
        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

hwnd = {hwnd}
main_hwnd = {main_hwnd}
screen_x = {screen_x}
screen_y = {screen_y}
wheel_delta = {wheel_delta}

print("[HijackScroll] hwnd=%d, main=%d, scroll_screen=(%d, %d), delta=%d" % (hwnd, main_hwnd, screen_x, screen_y, wheel_delta))

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    print("[HijackScroll] Main window is minimized, restoring...")
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    print("[HijackScroll] Main window not visible, showing...")
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

time.sleep(0.01)
win32api.SetCursorPos(old_pos)
win32gui.SetForegroundWindow(old_fg)
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        return self._run_subprocess(code, timeout=10)

    def _hijack_hover(self, hwnd: int, screen_x: int, screen_y: int, duration_ms: int,
                     semi_blocking: bool = False) -> bool:
        """Hijack 鼠标悬浮 - SetCursorPos + sleep(duration_ms) + 恢复"""
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        code = f'''
import win32gui, win32api, win32con, ctypes, time

old_fg = win32gui.GetForegroundWindow()
old_pos = win32api.GetCursorPos()

# 获取窗口信息用于调试
window_rect = win32gui.GetWindowRect({hwnd})
client_rect = win32gui.GetClientRect({hwnd})

main_hwnd = {main_hwnd}
hwnd = {hwnd}
screen_x = {screen_x}
screen_y = {screen_y}
duration_ms = {duration_ms}

print("[HijackHover] hwnd=%d, main=%d" % (hwnd, main_hwnd))
print("[HijackHover] window_rect=(%d, %d, %d, %d)" % (window_rect[0], window_rect[1], window_rect[2], window_rect[3]))
print("[HijackHover] client_rect=(%d, %d, %d, %d)" % (client_rect[0], client_rect[1], client_rect[2], client_rect[3]))
print("[HijackHover] target_screen_coords=(%d, %d), duration=%dms" % (screen_x, screen_y, duration_ms))

# 仅在窗口最小化或隐藏时才恢复
if win32gui.IsIconic(main_hwnd):
    print("[HijackHover] Main window is minimized, restoring...")
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    print("[HijackHover] Main window not visible, showing...")
    win32gui.ShowWindow(main_hwnd, win32con.SW_SHOW)
    time.sleep(0.1)

target_tid = ctypes.windll.user32.GetWindowThreadProcessId(main_hwnd, None)
current_tid = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, True)
win32gui.SetForegroundWindow(main_hwnd)
time.sleep(0.1)

# 用 win32api 移动鼠标到目标位置
print("[HijackHover] Moving to (%d, %d) with SetCursorPos..." % (screen_x, screen_y))
win32api.SetCursorPos((screen_x, screen_y))
actual_pos = win32api.GetCursorPos()
print("[HijackHover] After SetCursorPos, actual pos=(%d, %d)" % (actual_pos[0], actual_pos[1]))

# 停留指定时长
if duration_ms > 0:
    time.sleep(duration_ms / 1000.0)

# 恢复状态
win32api.SetCursorPos(old_pos)
win32gui.SetForegroundWindow(old_fg)
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        timeout = max(5, duration_ms / 1000 + 5) if duration_ms > 0 else 5
        return self._run_subprocess(code, timeout=int(timeout), semi_blocking=semi_blocking)

    def _hijack_input_text(self, hwnd: int, screen_x: int, screen_y: int, text: str) -> bool:
        """Hijack 输入文本 - 用 win32api 绕过 pyautogui 多屏限制

        支持 None 坐标：无坐标时不点击，直接粘贴
        """
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
        text_b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')

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
    print("[HijackInputText] Main window is minimized, restoring...")
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    print("[HijackInputText] Main window not visible, showing...")
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

win32api.SetCursorPos(old_pos)
win32gui.SetForegroundWindow(old_fg)
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
'''
        return self._run_subprocess(code, timeout=30)

    def _hijack_key_press(self, hwnd: int, key: str,
                          virtual_x: int = None, virtual_y: int = None,
                          duration_ms: int = 0, non_blocking: bool = False) -> bool:
        """Hijack 按键 - 用 win32api 绕过 pyautogui 多屏限制

        关键点：激活窗口后需要足够延迟确保焦点稳定（150ms）
        """
        main_hwnd = win32gui.GetParent(hwnd) or hwnd
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
    print("[HijackKeyPress] Main window is minimized, restoring...")
    win32gui.ShowWindow(main_hwnd, win32con.SW_RESTORE)
    time.sleep(0.2)
elif not win32gui.IsWindowVisible(main_hwnd):
    print("[HijackKeyPress] Main window not visible, showing...")
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

# 恢复状态
win32api.SetCursorPos(old_pos)
win32gui.SetForegroundWindow(old_fg)
ctypes.windll.user32.AttachThreadInput(current_tid, target_tid, False)
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
        """
        try:
            if non_blocking or semi_blocking:
                proc = subprocess.Popen(
                    [sys.executable, '-c', code],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                # 验证子进程是否成功启动
                if semi_blocking:
                    # 半阻塞：等待 200ms 让鼠标到位
                    time.sleep(0.2)
                    if proc.poll() is not None:
                        # 子进程已经退出了，说明启动失败
                        print(f"[SubprocessError] semi_blocking subprocess exited immediately with code={proc.returncode}")
                        return False
                    print(f"[Subprocess] semi_blocking subprocess started and mouse positioned, pid={proc.pid}")
                else:
                    # 非阻塞：检查子进程是否启动
                    time.sleep(0.01)
                    if proc.poll() is not None:
                        print(f"[SubprocessError] non_blocking subprocess exited immediately with code={proc.returncode}")
                        return False
                    print(f"[Subprocess] non_blocking subprocess started with pid={proc.pid}")
                return True
            else:
                result = subprocess.run(
                    [sys.executable, '-c', code],
                    capture_output=True, text=True, timeout=timeout
                )
                if result.returncode != 0:
                    print(f"[SubprocessError] returncode={result.returncode}")
                    if result.stderr:
                        print(f"[SubprocessError] stderr={result.stderr[:500]}")
                if result.stdout and result.stdout.strip():
                    print(f"[SubprocessLog] {result.stdout.strip()[:500]}")
                return result.returncode == 0
        except Exception as e:
            print(f"[SubprocessError] exception={e}")
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

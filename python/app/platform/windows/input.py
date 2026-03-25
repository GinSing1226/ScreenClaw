"""
Windows操作注入实现
使用 PostMessage + SendInput (pyautogui) 双重方案
"""
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple, Callable
from dataclasses import dataclass
import time

# 延迟导入 pyautogui
PYAUTOGUI_AVAILABLE = True
try:
    import pyautogui
except ImportError:
    PYAUTOGUI_AVAILABLE = False


@dataclass
class InjectResult:
    """操作注入结果"""
    success: bool
    error: Optional[str]
    method: str  # "postmessage" | "sendinput"
    need_confirm: bool  # 是否需要用户确认


class WindowsInputInjector:
    """Windows操作注入"""

    # Windows消息常量
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202
    WM_RBUTTONDOWN = 0x0204
    WM_RBUTTONUP = 0x0205
    WM_MOUSEMOVE = 0x0200
    WM_KEYDOWN = 0x0100
    WM_KEYUP = 0x0101
    WM_CHAR = 0x0102

    MK_LBUTTON = 0x0001
    MK_RBUTTON = 0x0002

    def __init__(self, confirm_callback: Optional[Callable[[], bool]] = None):
        self.user32 = ctypes.windll.user32
        self.confirm_callback = confirm_callback

        # 按键映射
        self._key_map = {
            "enter": 0x0D,
            "tab": 0x09,
            "escape": 0x1B,
            "esc": 0x1B,
            "space": 0x20,
            "backspace": 0x08,
            "delete": 0x2E,
            "arrowup": 0x26,
            "arrowdown": 0x28,
            "arrowleft": 0x25,
            "arrowright": 0x27,
            "f1": 0x70,
            "f2": 0x71,
            "f3": 0x72,
            "f4": 0x73,
            "f5": 0x74,
            "f6": 0x75,
            "f7": 0x76,
            "f8": 0x77,
            "f9": 0x78,
            "f10": 0x79,
            "f11": 0x7A,
            "f12": 0x7B,
            "ctrl": 0x11,
            "alt": 0x12,
            "shift": 0x10,
            "win": 0x5B,
        }

    def click(self, hwnd: int, x: int, y: int) -> InjectResult:
        """点击操作"""
        # 方案1: PostMessage
        if self._postmessage_click(hwnd, x, y):
            return InjectResult(
                success=True,
                error=None,
                method="postmessage",
                need_confirm=False
            )

        # 方案2: SendInput (需要确认)
        if not self._request_confirm():
            return InjectResult(
                success=False,
                error="用户拒绝操作",
                method="",
                need_confirm=True
            )

        if self._sendinput_click(x, y):
            return InjectResult(
                success=True,
                error=None,
                method="sendinput",
                need_confirm=True
            )

        return InjectResult(
            success=False,
            error="点击操作失败",
            method="",
            need_confirm=True
        )

    def right_click(self, hwnd: int, x: int, y: int) -> InjectResult:
        """右键点击"""
        if self._postmessage_right_click(hwnd, x, y):
            return InjectResult(
                success=True,
                error=None,
                method="postmessage",
                need_confirm=False
            )

        if not self._request_confirm():
            return InjectResult(
                success=False,
                error="用户拒绝操作",
                method="",
                need_confirm=True
            )

        if self._sendinput_right_click(x, y):
            return InjectResult(
                success=True,
                error=None,
                method="sendinput",
                need_confirm=True
            )

        return InjectResult(
            success=False,
            error="右键操作失败",
            method="",
            need_confirm=True
        )

    def long_press(self, hwnd: int, x: int, y: int, duration_ms: int) -> InjectResult:
        """长按操作"""
        if self._postmessage_long_press(hwnd, x, y, duration_ms):
            return InjectResult(
                success=True,
                error=None,
                method="postmessage",
                need_confirm=False
            )

        if not self._request_confirm():
            return InjectResult(
                success=False,
                error="用户拒绝操作",
                method="",
                need_confirm=True
            )

        if self._sendinput_long_press(x, y, duration_ms):
            return InjectResult(
                success=True,
                error=None,
                method="sendinput",
                need_confirm=True
            )

        return InjectResult(
            success=False,
            error="长按操作失败",
            method="",
            need_confirm=True
        )

    def swipe(
        self,
        hwnd: int,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int
    ) -> InjectResult:
        """滑动操作"""
        if self._postmessage_swipe(hwnd, start_x, start_y, end_x, end_y):
            return InjectResult(
                success=True,
                error=None,
                method="postmessage",
                need_confirm=False
            )

        if not self._request_confirm():
            return InjectResult(
                success=False,
                error="用户拒绝操作",
                method="",
                need_confirm=True
            )

        if self._sendinput_swipe(start_x, start_y, end_x, end_y):
            return InjectResult(
                success=True,
                error=None,
                method="sendinput",
                need_confirm=True
            )

        return InjectResult(
            success=False,
            error="滑动操作失败",
            method="",
            need_confirm=True
        )

    def key_press(self, hwnd: int, key: str) -> InjectResult:
        """按键操作"""
        if self._postmessage_key_press(hwnd, key):
            return InjectResult(
                success=True,
                error=None,
                method="postmessage",
                need_confirm=False
            )

        if not self._request_confirm():
            return InjectResult(
                success=False,
                error="用户拒绝操作",
                method="",
                need_confirm=True
            )

        if self._sendinput_key_press(key):
            return InjectResult(
                success=True,
                error=None,
                method="sendinput",
                need_confirm=True
            )

        return InjectResult(
            success=False,
            error="按键操作失败",
            method="",
            need_confirm=True
        )

    def input_text(self, hwnd: int, x: int, y: int, text: str) -> InjectResult:
        """输入文本"""
        # 先点击
        click_result = self.click(hwnd, x, y)
        if not click_result.success:
            return click_result

        time.sleep(0.1)

        # 输入文本
        for char in text:
            if char == '\n':
                # 换行处理
                if self._postmessage_key_press(hwnd, "enter"):
                    continue
                if not self._request_confirm():
                    return InjectResult(
                        success=False,
                        error="用户拒绝操作",
                        method="",
                        need_confirm=True
                    )
                self._sendinput_key_press("enter")
            else:
                # 普通字符
                self._postmessage_char(hwnd, char)

        return InjectResult(
            success=True,
            error=None,
            method="postmessage",
            need_confirm=False
        )

    # ============ PostMessage 实现 ============

    def _make_lparam(self, x: int, y: int) -> int:
        """生成LPARAM"""
        return (y << 16) | (x & 0xFFFF)

    def _postmessage_click(self, hwnd: int, x: int, y: int) -> bool:
        """PostMessage点击"""
        try:
            lParam = self._make_lparam(x, y)
            self.user32.PostMessageW(hwnd, self.WM_LBUTTONDOWN, self.MK_LBUTTON, lParam)
            self.user32.PostMessageW(hwnd, self.WM_LBUTTONUP, 0, lParam)
            return True
        except Exception:
            return False

    def _postmessage_right_click(self, hwnd: int, x: int, y: int) -> bool:
        """PostMessage右键"""
        try:
            lParam = self._make_lparam(x, y)
            self.user32.PostMessageW(hwnd, self.WM_RBUTTONDOWN, self.MK_RBUTTON, lParam)
            self.user32.PostMessageW(hwnd, self.WM_RBUTTONUP, 0, lParam)
            return True
        except Exception:
            return False

    def _postmessage_long_press(self, hwnd: int, x: int, y: int, duration_ms: int) -> bool:
        """PostMessage长按"""
        try:
            lParam = self._make_lparam(x, y)
            self.user32.PostMessageW(hwnd, self.WM_LBUTTONDOWN, self.MK_LBUTTON, lParam)
            time.sleep(duration_ms / 1000)
            self.user32.PostMessageW(hwnd, self.WM_LBUTTONUP, 0, lParam)
            return True
        except Exception:
            return False

    def _postmessage_swipe(
        self,
        hwnd: int,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int
    ) -> bool:
        """PostMessage滑动"""
        try:
            lParam_start = self._make_lparam(start_x, start_y)
            lParam_end = self._make_lparam(end_x, end_y)

            self.user32.PostMessageW(hwnd, self.WM_LBUTTONDOWN, self.MK_LBUTTON, lParam_start)
            time.sleep(0.05)
            self.user32.PostMessageW(hwnd, self.WM_MOUSEMOVE, self.MK_LBUTTON, lParam_end)
            time.sleep(0.05)
            self.user32.PostMessageW(hwnd, self.WM_LBUTTONUP, 0, lParam_end)
            return True
        except Exception:
            return False

    def _postmessage_key_press(self, hwnd: int, key: str) -> bool:
        """PostMessage按键"""
        try:
            vk_code = self._get_vk_code(key)
            if vk_code is None:
                return False

            self.user32.PostMessageW(hwnd, self.WM_KEYDOWN, vk_code, 0)
            time.sleep(0.05)
            self.user32.PostMessageW(hwnd, self.WM_KEYUP, vk_code, 0)
            return True
        except Exception:
            return False

    def _postmessage_char(self, hwnd: int, char: str) -> bool:
        """PostMessage字符"""
        try:
            self.user32.PostMessageW(hwnd, self.WM_CHAR, ord(char), 0)
            return True
        except Exception:
            return False

    # ============ SendInput 实现 ============

    def _sendinput_click(self, x: int, y: int) -> bool:
        """SendInput点击"""
        if not PYAUTOGUI_AVAILABLE:
            return False
        try:
            pyautogui.click(x, y)
            return True
        except Exception:
            return False

    def _sendinput_right_click(self, x: int, y: int) -> bool:
        """SendInput右键"""
        if not PYAUTOGUI_AVAILABLE:
            return False
        try:
            pyautogui.rightClick(x, y)
            return True
        except Exception:
            return False

    def _sendinput_long_press(self, x: int, y: int, duration_ms: int) -> bool:
        """SendInput长按"""
        if not PYAUTOGUI_AVAILABLE:
            return False
        try:
            pyautogui.moveTo(x, y)
            pyautogui.mouseDown()
            time.sleep(duration_ms / 1000)
            pyautogui.mouseUp()
            return True
        except Exception:
            return False

    def _sendinput_swipe(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        """SendInput滑动"""
        if not PYAUTOGUI_AVAILABLE:
            return False
        try:
            duration = 0.3
            pyautogui.moveTo(start_x, start_y)
            pyautogui.drag(end_x - start_x, end_y - start_y, duration=duration)
            return True
        except Exception:
            return False

    def _sendinput_key_press(self, key: str) -> bool:
        """SendInput按键"""
        if not PYAUTOGUI_AVAILABLE:
            return False
        try:
            keys = self._parse_key_combination(key)
            pyautogui.hotkey(*keys)
            return True
        except Exception:
            return False

    # ============ 辅助方法 ============

    def _get_vk_code(self, key: str) -> Optional[int]:
        """获取虚拟键码"""
        key_lower = key.lower()

        # 特殊键
        if key_lower in self._key_map:
            return self._key_map[key_lower]

        # 单个字符
        if len(key) == 1:
            return ord(key.upper())

        return None

    def _parse_key_combination(self, key: str) -> list:
        """解析组合键"""
        parts = key.split('+')
        result = []
        for part in parts:
            part = part.strip().lower()
            if part in self._key_map:
                result.append(part)
            elif len(part) == 1:
                result.append(part)
        return result

    def _request_confirm(self) -> bool:
        """请求用户确认"""
        if self.confirm_callback:
            return self.confirm_callback()
        # 默认返回False，需要Tauri设置确认回调
        return False


# 全局操作注入实例
windows_input = WindowsInputInjector()

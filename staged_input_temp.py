"""
Windows操作注入实现
使用 PostMessage (pywin32) + SendInput (pyautogui) 双重方案
"""
from typing import Optional, Tuple
from dataclasses import dataclass
import time

import win32gui
import win32api
import win32con

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

    def __init__(self):
        # 按键映射
        self._key_map = {
            "enter": win32con.VK_RETURN,
            "tab": win32con.VK_TAB,
            "escape": win32con.VK_ESCAPE,
            "esc": win32con.VK_ESCAPE,
            "space": win32con.VK_SPACE,
            "backspace": win32con.VK_BACK,
            "delete": win32con.VK_DELETE,
            "arrowup": win32con.VK_UP,
            "arrowdown": win32con.VK_DOWN,
            "arrowleft": win32con.VK_LEFT,
            "arrowright": win32con.VK_RIGHT,
            "f1": win32con.VK_F1,
            "f2": win32con.VK_F2,
            "f3": win32con.VK_F3,
            "f4": win32con.VK_F4,
            "f5": win32con.VK_F5,
            "f6": win32con.VK_F6,
            "f7": win32con.VK_F7,
            "f8": win32con.VK_F8,
            "f9": win32con.VK_F9,
            "f10": win32con.VK_F10,
            "f11": win32con.VK_F11,
            "f12": win32con.VK_F12,
            "ctrl": win32con.VK_CONTROL,
            "alt": win32con.VK_MENU,
            "shift": win32con.VK_SHIFT,
            "win": win32con.VK_LWIN,
        }

    def click(self, hwnd: int, physical_x: int, physical_y: int,
              virtual_x: int, virtual_y: int, action_method: str = "postmessage") -> InjectResult:
        """点击操作

        Args:
            hwnd: 窗口句柄
            physical_x, physical_y: 物理坐标（PostMessage 用）
            virtual_x, virtual_y: 虚拟坐标（SendInput 用）
            action_method: 操作方式 "postmessage" 或 "sendinput"
        """
        if action_method == "sendinput":
            # SendInput 需要虚拟坐标转屏幕坐标
            screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
            if self._sendinput_click(screen_x, screen_y):
                return InjectResult(
                    success=True,
                    error=None,
                    method="sendinput",
                    need_confirm=False
                )
            return InjectResult(
                success=False,
                error="点击操作失败",
                method="sendinput",
                need_confirm=False
            )

        # PostMessage 使用物理坐标
        if self._postmessage_click(hwnd, physical_x, physical_y):
            return InjectResult(
                success=True,
                error=None,
                method="postmessage",
                need_confirm=False
            )

        return InjectResult(
            success=False,
            error="点击操作失败",
            method="postmessage",
            need_confirm=False
        )

    def right_click(self, hwnd: int, physical_x: int, physical_y: int,
                   virtual_x: int, virtual_y: int, action_method: str = "postmessage") -> InjectResult:
        """右键点击

        Args:
            hwnd: 窗口句柄
            physical_x, physical_y: 物理坐标（PostMessage 用）
            virtual_x, virtual_y: 虚拟坐标（SendInput 用）
            action_method: 操作方式 "postmessage" 或 "sendinput"
        """
        if action_method == "sendinput":
            screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
            if self._sendinput_right_click(screen_x, screen_y):
                return InjectResult(
                    success=True,
                    error=None,
                    method="sendinput",
                    need_confirm=False
                )
            return InjectResult(
                success=False,
                error="右键操作失败",
                method="sendinput",
                need_confirm=False
            )

        if self._postmessage_right_click(hwnd, physical_x, physical_y):
            return InjectResult(
                success=True,
                error=None,
                method="postmessage",
                need_confirm=False
            )

        return InjectResult(
            success=False,
            error="右键操作失败",
            method="postmessage",
            need_confirm=False
        )

    def long_press(self, hwnd: int, physical_x: int, physical_y: int,
                   virtual_x: int, virtual_y: int, duration_ms: int,
                   action_method: str = "postmessage") -> InjectResult:
        """长按操作

        Args:
            hwnd: 窗口句柄
            physical_x, physical_y: 物理坐标（PostMessage 用）
            virtual_x, virtual_y: 虚拟坐标（SendInput 用）
            duration_ms: 长按时长（毫秒）
            action_method: 操作方式 "postmessage" 或 "sendinput"
        """
        if action_method == "sendinput":
            # SendInput 需要虚拟坐标转屏幕坐标
            screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)
            if self._sendinput_long_press(screen_x, screen_y, duration_ms):
                return InjectResult(
                    success=True,
                    error=None,
                    method="sendinput",
                    need_confirm=False
                )
            return InjectResult(
                success=False,
                error="长按操作失败",
                method="sendinput",
                need_confirm=False
            )

        # PostMessage 使用物理坐标
        if self._postmessage_long_press(hwnd, physical_x, physical_y, duration_ms):
            return InjectResult(
                success=True,
                error=None,
                method="postmessage",
                need_confirm=False
            )

        return InjectResult(
            success=False,
            error="长按操作失败",
            method="postmessage",
            need_confirm=False
        )

    def swipe(
        self,
        hwnd: int,
        physical_start_x: int, physical_start_y: int,
        physical_end_x: int, physical_end_y: int,
        virtual_start_x: int, virtual_start_y: int,
        virtual_end_x: int, virtual_end_y: int,
        action_method: str = "postmessage"
    ) -> InjectResult:
        """滑动操作

        Args:
            hwnd: 窗口句柄
            physical_*: 物理坐标（PostMessage 用）
            virtual_*: 虚拟坐标（SendInput 用）
            action_method: 操作方式
        """
        if action_method == "sendinput":
            screen_start_x, screen_start_y = self._client_to_screen(hwnd, virtual_start_x, virtual_start_y)
            screen_end_x, screen_end_y = self._client_to_screen(hwnd, virtual_end_x, virtual_end_y)
            if self._sendinput_swipe(screen_start_x, screen_start_y, screen_end_x, screen_end_y):
                return InjectResult(
                    success=True,
                    error=None,
                    method="sendinput",
                    need_confirm=False
                )
            return InjectResult(
                success=False,
                error="滑动操作失败",
                method="sendinput",
                need_confirm=False
            )

        if self._postmessage_swipe(hwnd, physical_start_x, physical_start_y, physical_end_x, physical_end_y):
            return InjectResult(
                success=True,
                error=None,
                method="postmessage",
                need_confirm=False
            )

        return InjectResult(
            success=False,
            error="滑动操作失败",
            method="postmessage",
            need_confirm=False
        )

    def scroll(self, hwnd: int, virtual_x: int, virtual_y: int, delta: int) -> InjectResult:
        """滚动操作 - 强制使用 SendInput，需要激活窗口

        Args:
            hwnd: 窗口句柄
            virtual_x, virtual_y: 虚拟坐标（相对于客户区）
            delta: 滚动量（正值向上，负值向下）
        """
        # 激活目标窗口
        self._activate_window(hwnd)

        # 转换为屏幕坐标
        screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)

        if self._sendinput_scroll(screen_x, screen_y, delta):
            return InjectResult(
                success=True,
                error=None,
                method="sendinput",
                need_confirm=False
            )
        return InjectResult(
            success=False,
            error="滚动操作失败",
            method="sendinput",
            need_confirm=False
        )

    def key_press(self, hwnd: int, key: str) -> InjectResult:
        """按键操作 - 强制使用 SendInput，需要激活窗口

        Args:
            hwnd: 窗口句柄
            key: 按键，支持组合键如 Ctrl+C
        """
        # 激活目标窗口
        self._activate_window(hwnd)

        if self._sendinput_key_press(key):
            return InjectResult(
                success=True,
                error=None,
                method="sendinput",
                need_confirm=False
            )
        return InjectResult(
            success=False,
            error="按键操作失败",
            method="sendinput",
            need_confirm=False
        )

    def input_text(self, hwnd: int, virtual_x: int, virtual_y: int, text: str, input_method: str = "paste") -> InjectResult:
        """输入文本

        Args:
            hwnd: 窗口句柄
            virtual_x, virtual_y: 虚拟坐标（相对于客户区）
            text: 要输入的文本
            input_method: 输入方式
                - paste: 剪贴板粘贴（PC 推荐）
                - type: PostMessage WM_CHAR 逐字输入（模拟器推荐）
        """
        # 激活目标窗口
        self._activate_window(hwnd)

        # 转换为屏幕坐标
        screen_x, screen_y = self._client_to_screen(hwnd, virtual_x, virtual_y)

        if self._sendinput_input_text(screen_x, screen_y, text, input_method, hwnd):
            return InjectResult(
                success=True,
                error=None,
                method="sendinput",
                need_confirm=False
            )
        return InjectResult(
            success=False,
            error="输入文本失败",
            method="sendinput",
            need_confirm=False
        )

    # ============ PostMessage 实现 ============

    def _postmessage_click(self, hwnd: int, x: int, y: int) -> bool:
        """PostMessage点击 - 使用子进程隔离环境"""
        try:
            import subprocess
            import sys

            code = f'''
import win32gui
import win32api
import win32con
import time

hwnd = {hwnd}
x = {x}
y = {y}
lParam = win32api.MAKELONG(x, y)
wParam = 0x0001

win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, wParam, lParam)
time.sleep(0.05)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _postmessage_right_click(self, hwnd: int, x: int, y: int) -> bool:
        """PostMessage右键 - 使用子进程隔离环境"""
        try:
            import subprocess
            import sys

            code = f'''
import win32gui
import win32api
import win32con
import time

hwnd = {hwnd}
x = {x}
y = {y}
lParam = win32api.MAKELONG(x, y)
wParam = 0x0002  # MK_RBUTTON

win32gui.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, wParam, lParam)
time.sleep(0.05)
win32gui.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, lParam)
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _postmessage_long_press(self, hwnd: int, x: int, y: int, duration_ms: int) -> bool:
        """PostMessage长按 - 使用子进程隔离环境"""
        try:
            import subprocess
            import sys

            code = f'''
import win32gui
import win32api
import win32con
import time

hwnd = {hwnd}
x = {x}
y = {y}
duration_ms = {duration_ms}
lParam = win32api.MAKELONG(x, y)
wParam = 0x0001  # MK_LBUTTON

win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, wParam, lParam)
time.sleep(duration_ms / 1000)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=10  # 长按可能需要更长时间
            )
            return result.returncode == 0
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
        """PostMessage滑动 - 使用子进程隔离环境"""
        try:
            import subprocess
            import sys

            code = f'''
import win32gui
import win32api
import win32con
import time

hwnd = {hwnd}
start_x = {start_x}
start_y = {start_y}
end_x = {end_x}
end_y = {end_y}

lParam_start = win32api.MAKELONG(start_x, start_y)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, 0x0001, lParam_start)
time.sleep(0.05)

# 分步移动
steps = 10
duration = 0.3
step_delay = duration / steps

for i in range(1, steps + 1):
    progress = i / steps
    current_x = int(start_x + (end_x - start_x) * progress)
    current_y = int(start_y + (end_y - start_y) * progress)
    lParam = win32api.MAKELONG(current_x, current_y)
    win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0x0001, lParam)
    time.sleep(step_delay)

lParam_end = win32api.MAKELONG(end_x, end_y)
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam_end)
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _postmessage_key_press(self, hwnd: int, key: str) -> bool:
        """PostMessage按键 - 使用子进程隔离环境"""
        try:
            vk_code = self._get_vk_code(key)
            if vk_code is None:
                return False

            import subprocess
            import sys

            code = f'''
import win32gui
import win32con
import time

hwnd = {hwnd}
vk_code = {vk_code}

win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, 0)
time.sleep(0.05)
win32gui.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, 0)
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _postmessage_char(self, hwnd: int, char: str) -> bool:
        """PostMessage字符 - 使用子进程隔离环境"""
        try:
            import subprocess
            import sys

            # 处理特殊字符转义
            char_code = ord(char)

            code = f'''
import win32gui
import win32con

hwnd = {hwnd}
char_code = {char_code}

win32gui.PostMessage(hwnd, win32con.WM_CHAR, char_code, 0)
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _postmessage_scroll(self, hwnd: int, x: int, y: int, delta: int) -> bool:
        """PostMessage滚动 - 使用子进程隔离环境"""
        try:
            import subprocess
            import sys

            code = f'''
import win32gui
import win32api
import win32con

hwnd = {hwnd}
x = {x}
y = {y}
delta = {delta}

lParam = win32api.MAKELONG(x, y)
wParam = delta << 16  # HIWORD = delta, LOWORD = 0

win32gui.PostMessage(hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    # ============ SendInput 实现 ============

    def _sendinput_click(self, x: int, y: int) -> bool:
        """SendInput点击 - 使用子进程隔离环境"""
        try:
            import subprocess
            import sys

            code = f'''
import pyautogui
pyautogui.click({x}, {y})
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _sendinput_right_click(self, x: int, y: int) -> bool:
        """SendInput右键 - 使用子进程隔离环境"""
        try:
            import subprocess
            import sys

            code = f'''
import pyautogui
pyautogui.rightClick({x}, {y})
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _sendinput_long_press(self, x: int, y: int, duration_ms: int) -> bool:
        """SendInput长按 - 使用子进程隔离环境"""
        try:
            import subprocess
            import sys

            code = f'''
import pyautogui
import time
pyautogui.moveTo({x}, {y})
pyautogui.mouseDown()
time.sleep({duration_ms} / 1000)
pyautogui.mouseUp()
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _sendinput_swipe(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        """SendInput滑动 - 使用子进程隔离环境"""
        try:
            import subprocess
            import sys

            code = f'''
import pyautogui
pyautogui.moveTo({start_x}, {start_y})
pyautogui.dragTo({end_x}, {end_y}, duration=0.5, button='left')
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _sendinput_scroll(self, x: int, y: int, delta: int) -> bool:
        """SendInput滚动 - 使用子进程隔离环境"""
        try:
            import subprocess
            import sys

            clicks = delta // 120
            code = f'''
import pyautogui
pyautogui.moveTo({x}, {y})
pyautogui.scroll({clicks}, {x}, {y})
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _sendinput_key_press(self, key: str) -> bool:
        """SendInput按键 - 使用子进程隔离环境"""
        try:
            import subprocess
            import sys

            keys = self._parse_key_combination(key)
            keys_str = str(keys)
            code = f'''
import pyautogui
pyautogui.hotkey(*{keys_str})
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _sendinput_input_text(self, x: int, y: int, text: str, input_method: str = "paste", hwnd: int = 0) -> bool:
        """SendInput输入文本

        Args:
            x, y: 屏幕坐标
            text: 要输入的文本
            input_method: 输入方式
                - paste: 剪贴板粘贴（PC 推荐）
                - type: PostMessage WM_CHAR 逐字输入（模拟器推荐）
            hwnd: 窗口句柄（type 模式需要）
        """
        try:
            import subprocess
            import sys
            import base64
            text_bytes = text.encode('utf-8')
            text_b64 = base64.b64encode(text_bytes).decode('ascii')

            if input_method == "type":
                # type 模式 - PostMessage WM_CHAR 逐字输入
                code = f'''
import win32gui
import win32con
import time
import base64
import pyautogui

hwnd = {hwnd}
text = base64.b64decode("{text_b64}").decode("utf-8")

# 先点击输入框获得焦点
pyautogui.click({x}, {y})
time.sleep(0.2)

# 逐字符发送 WM_CHAR
for char in text:
    char_code = ord(char)
    win32gui.PostMessage(hwnd, win32con.WM_CHAR, char_code, 0)
    time.sleep(0.05)
'''
            else:
                # paste 模式 - 剪贴板 + keybd_event Ctrl+V
                code = f'''
import ctypes
import time
import pyperclip
import base64
import pyautogui

VK_CONTROL = 0x11
VK_V = 0x56
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002

def key_down(vk):
    ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYDOWN, 0)

def key_up(vk):
    ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

def press_ctrl_v():
    key_down(VK_CONTROL)
    time.sleep(0.05)
    key_down(VK_V)
    time.sleep(0.05)
    key_up(VK_V)
    time.sleep(0.05)
    key_up(VK_CONTROL)
    time.sleep(0.1)

text = base64.b64decode("{text_b64}").decode("utf-8")

pyautogui.click({x}, {y})
time.sleep(0.3)

pyperclip.copy(text)
time.sleep(0.3)
press_ctrl_v()
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception:
            return False

    # ============ 辅助方法 ============

    def _activate_window(self, hwnd: int) -> bool:
        """激活窗口到前台

        Args:
            hwnd: 窗口句柄

        Returns:
            bool: 是否成功激活
        """
        try:
            import subprocess
            import sys

            code = f'''
import win32gui
import win32con
import pyautogui
import time

hwnd = {hwnd}

# 如果最小化，先恢复
win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
time.sleep(0.05)

# Alt 键技巧：绕过 Windows 焦点限制
pyautogui.press('alt')
time.sleep(0.02)

# 设置为前台窗口
win32gui.SetForegroundWindow(hwnd)
time.sleep(0.1)
'''

            result = subprocess.run(
                [sys.executable, '-c', code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _client_to_screen(self, hwnd: int, x: int, y: int) -> Tuple[int, int]:
        """客户区坐标转屏幕坐标"""
        return win32gui.ClientToScreen(hwnd, (x, y))

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


# 全局操作注入实例
windows_input = WindowsInputInjector()

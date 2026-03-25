"""
控制模块 - 后台点击/滑动/长按
"""
import win32gui
import win32api
import win32con
import time
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum


class MouseButton(Enum):
    """鼠标按钮"""
    LEFT = 0
    RIGHT = 1
    MIDDLE = 2


@dataclass
class Point:
    """坐标点"""
    x: int
    y: int

    @classmethod
    def from_percent(cls, x_pct: float, y_pct: float, width: int, height: int) -> 'Point':
        """从百分比坐标创建"""
        return cls(
            x=int(x_pct * width),
            y=int(y_pct * height)
        )


class WindowController:
    """窗口控制器"""

    # 鼠标按钮映射
    BUTTON_MAP = {
        MouseButton.LEFT: (win32con.WM_LBUTTONDOWN, win32con.WM_LBUTTONUP),
        MouseButton.RIGHT: (win32con.WM_RBUTTONDOWN, win32con.WM_RBUTTONUP),
        MouseButton.MIDDLE: (win32con.WM_MBUTTONDOWN, win32con.WM_MBUTTONUP),
    }

    def __init__(self, hwnd: int):
        """
        初始化控制器

        Args:
            hwnd: 目标窗口句柄
        """
        self.hwnd = hwnd
        self._width = 0
        self._height = 0
        self._update_size()
        self._delay = 0.05  # 默认操作间隔

    def _update_size(self):
        """更新窗口尺寸"""
        rect = win32gui.GetWindowRect(self.hwnd)
        self._width = rect[2] - rect[0]
        self._height = rect[3] - rect[1]

    @property
    def size(self) -> Tuple[int, int]:
        """返回窗口尺寸 (width, height)"""
        self._update_size()
        return self._width, self._height

    def set_delay(self, delay: float):
        """设置操作间隔（秒）"""
        self._delay = delay

    def _make_lparam(self, x: int, y: int) -> int:
        """
        创建 lParam（坐标打包）

        Args:
            x: X 坐标
            y: Y 坐标

        Returns:
            打包后的 lParam
        """
        return win32api.MAKELONG(x, y)

    def _send_message(self, msg: int, wparam: int, lparam: int):
        """
        发送窗口消息

        Args:
            msg: 消息类型
            wparam: wParam
            lparam: lParam
        """
        win32gui.PostMessage(self.hwnd, msg, wparam, lparam)

    def _send_click_messages(self, x: int, y: int, button: MouseButton = MouseButton.LEFT):
        """
        发送点击消息序列

        Args:
            x: X 坐标
            y: Y 坐标
            button: 鼠标按钮
        """
        down_msg, up_msg = self.BUTTON_MAP[button]
        lparam = self._make_lparam(x, y)

        # wParam: MK_LBUTTON = 0x0001
        wparam = 0x0001 if button == MouseButton.LEFT else 0

        # 发送按下消息
        self._send_message(down_msg, wparam, lparam)
        time.sleep(self._delay)

        # 发送释放消息
        self._send_message(up_msg, 0, lparam)

    def click(self, x: float, y: float, button: MouseButton = MouseButton.LEFT,
              use_percent: bool = True) -> bool:
        """
        点击指定位置

        Args:
            x: X 坐标（百分比或像素）
            y: Y 坐标（百分比或像素）
            button: 鼠标按钮
            use_percent: 是否使用百分比坐标

        Returns:
            是否成功
        """
        try:
            self._update_size()

            if use_percent:
                point = Point.from_percent(x, y, self._width, self._height)
                px, py = point.x, point.y
            else:
                px, py = int(x), int(y)

            print(f"点击位置: ({px}, {py}) 窗口尺寸: {self._width}x{self._height}")
            self._send_click_messages(px, py, button)
            return True

        except Exception as e:
            print(f"点击失败: {e}")
            return False

    def double_click(self, x: float, y: float, use_percent: bool = True) -> bool:
        """
        双击指定位置

        Args:
            x: X 坐标
            y: Y 坐标
            use_percent: 是否使用百分比坐标

        Returns:
            是否成功
        """
        if self.click(x, y, use_percent=use_percent):
            time.sleep(0.1)
            return self.click(x, y, use_percent=use_percent)
        return False

    def long_press(self, x: float, y: float, duration: float = 1.0,
                   use_percent: bool = True) -> bool:
        """
        长按指定位置

        Args:
            x: X 坐标
            y: Y 坐标
            duration: 持续时间（秒）
            use_percent: 是否使用百分比坐标

        Returns:
            是否成功
        """
        try:
            self._update_size()

            if use_percent:
                point = Point.from_percent(x, y, self._width, self._height)
                px, py = point.x, point.y
            else:
                px, py = int(x), int(y)

            print(f"长按位置: ({px}, {py}) 持续 {duration} 秒")

            down_msg, up_msg = self.BUTTON_MAP[MouseButton.LEFT]
            lparam = self._make_lparam(px, py)

            # 按下
            self._send_message(down_msg, 0x0001, lparam)
            # 等待
            time.sleep(duration)
            # 释放
            self._send_message(up_msg, 0, lparam)

            return True

        except Exception as e:
            print(f"长按失败: {e}")
            return False

    def swipe(self, start_x: float, start_y: float, end_x: float, end_y: float,
              duration: float = 0.3, steps: int = 10, use_percent: bool = True) -> bool:
        """
        滑动操作

        Args:
            start_x: 起始 X 坐标
            start_y: 起始 Y 坐标
            end_x: 结束 X 坐标
            end_y: 结束 Y 坐标
            duration: 持续时间（秒）
            steps: 滑动步数
            use_percent: 是否使用百分比坐标

        Returns:
            是否成功
        """
        try:
            self._update_size()

            if use_percent:
                start = Point.from_percent(start_x, start_y, self._width, self._height)
                end = Point.from_percent(end_x, end_y, self._width, self._height)
            else:
                start = Point(int(start_x), int(start_y))
                end = Point(int(end_x), int(end_y))

            print(f"滑动: ({start.x}, {start.y}) -> ({end.x}, {end.y})")

            down_msg, up_msg = self.BUTTON_MAP[MouseButton.LEFT]
            step_delay = duration / steps

            # 按下起始点
            lparam = self._make_lparam(start.x, start.y)
            self._send_message(down_msg, 0x0001, lparam)
            time.sleep(step_delay)

            # 滑动过程
            for i in range(1, steps + 1):
                progress = i / steps
                current_x = int(start.x + (end.x - start.x) * progress)
                current_y = int(start.y + (end.y - start.y) * progress)

                # 发送移动消息 (WM_MOUSEMOVE)
                lparam = self._make_lparam(current_x, current_y)
                self._send_message(win32con.WM_MOUSEMOVE, 0x0001, lparam)
                time.sleep(step_delay)

            # 释放
            lparam = self._make_lparam(end.x, end.y)
            self._send_message(up_msg, 0, lparam)

            return True

        except Exception as e:
            print(f"滑动失败: {e}")
            return False

    def drag(self, start_x: float, start_y: float, end_x: float, end_y: float,
             duration: float = 0.5, use_percent: bool = True) -> bool:
        """
        拖拽操作（与滑动类似，但更强调"拖拽"语义）

        Args:
            start_x: 起始 X 坐标
            start_y: 起始 Y 坐标
            end_x: 结束 X 坐标
            end_y: 结束 Y 坐标
            duration: 持续时间（秒）
            use_percent: 是否使用百分比坐标

        Returns:
            是否成功
        """
        return self.swipe(start_x, start_y, end_x, end_y, duration, steps=20, use_percent=use_percent)

    def scroll(self, x: float, y: float, delta: int = -120, use_percent: bool = True) -> bool:
        """
        滚轮滚动

        Args:
            x: X 坐标
            y: Y 坐标
            delta: 滚动量（负值向下，正值向上）
            use_percent: 是否使用百分比坐标

        Returns:
            是否成功
        """
        try:
            self._update_size()

            if use_percent:
                point = Point.from_percent(x, y, self._width, self._height)
                px, py = point.x, point.y
            else:
                px, py = int(x), int(y)

            lparam = self._make_lparam(px, py)
            wparam = delta << 16  # HIWORD 是 delta

            # WM_MOUSEWHEEL 的 wParam 格式: HIWORD = delta, LOWORD = key state
            self._send_message(win32con.WM_MOUSEWHEEL, wparam, lparam)
            return True

        except Exception as e:
            print(f"滚动失败: {e}")
            return False

    def is_window_valid(self) -> bool:
        """检查窗口是否仍然有效"""
        try:
            return win32gui.IsWindow(self.hwnd) and win32gui.IsWindowVisible(self.hwnd)
        except:
            return False


def test_controller(hwnd: int):
    """测试控制器功能"""
    ctrl = WindowController(hwnd)
    print(f"窗口尺寸: {ctrl.size}")

    print("\n测试点击屏幕中心...")
    ctrl.click(0.5, 0.5)

    time.sleep(1)

    print("\n测试长按...")
    ctrl.long_press(0.3, 0.3, duration=2.0)

    time.sleep(1)

    print("\n测试滑动...")
    ctrl.swipe(0.2, 0.5, 0.8, 0.5, duration=0.5)


if __name__ == '__main__':
    from window_manager import WindowManager

    mgr = WindowManager()
    windows = mgr.enum_all_windows()

    print("可见窗口列表:")
    for i, win in enumerate(windows[:10]):
        print(f"[{i}] {win.title[:40]:40s} | {win.class_name}")

    idx = int(input("\n选择窗口序号: "))
    if 0 <= idx < len(windows):
        test_controller(windows[idx].hwnd)

"""
窗体管理模块 - 枚举和管理模拟器窗口
"""
import win32gui
import win32process
import win32con
from dataclasses import dataclass
from typing import Optional, List, Callable


@dataclass
class WindowInfo:
    """窗口信息"""
    hwnd: int           # 窗口句柄
    title: str          # 窗口标题
    class_name: str     # 窗口类名
    pid: int            # 进程ID
    width: int          # 宽度
    height: int         # 高度
    is_visible: bool    # 是否可见
    parent_hwnd: int    # 父窗口句柄


class WindowManager:
    """窗口管理器"""

    # 已知的模拟器进程名/窗口类名
    EMULATOR_SIGNATURES = {
        'mumu': {
            'process_names': ['MuMuPlayer.exe', 'MuMuPlayerGlobal.exe', 'MuMu.exe'],
            'window_classes': ['MuMuPlayer', 'MuMuWnd', 'NemuWindow', 'Qt5QWindowIcon'],
            'title_keywords': ['MuMu', 'mumu']
        },
        '雷电': {
            'process_names': ['dnplayer.exe', 'LDPlayer.exe'],
            'window_classes': ['LDPlayer', 'Qt5QWindowIcon'],
            'title_keywords': ['雷电', 'LDPlayer']
        },
        '夜神': {
            'process_names': ['Nox.exe', 'NoxVMHandle.exe'],
            'window_classes': ['Nox', 'Qt5QWindowIcon'],
            'title_keywords': ['夜神', 'Nox']
        }
    }

    def __init__(self):
        self._windows: List[WindowInfo] = []
        self._child_windows: List[WindowInfo] = []

    def enum_all_windows(self) -> List[WindowInfo]:
        """枚举所有顶级窗口"""
        self._windows = []

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True

            try:
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)

                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]

                info = WindowInfo(
                    hwnd=hwnd,
                    title=title,
                    class_name=class_name,
                    pid=pid,
                    width=width,
                    height=height,
                    is_visible=True,
                    parent_hwnd=win32gui.GetParent(hwnd)
                )
                self._windows.append(info)
            except Exception:
                pass

            return True

        win32gui.EnumWindows(callback, None)
        return self._windows

    def find_emulator_windows(self, emulator_type: str = 'mumu') -> List[WindowInfo]:
        """
        查找指定类型的模拟器窗口

        Args:
            emulator_type: 模拟器类型 ('mumu', '雷电', '夜神')

        Returns:
            匹配的窗口列表
        """
        self.enum_all_windows()
        sig = self.EMULATOR_SIGNATURES.get(emulator_type.lower(), {})

        if not sig:
            return []

        matched = []
        for win in self._windows:
            # 检查进程名
            try:
                import psutil
                proc = psutil.Process(win.pid)
                proc_name = proc.name()
                if proc_name in sig.get('process_names', []):
                    matched.append(win)
                    continue
            except:
                pass

            # 检查窗口类名
            for cls_pattern in sig.get('window_classes', []):
                if cls_pattern.lower() in win.class_name.lower():
                    matched.append(win)
                    break
            else:
                # 检查标题关键词
                for keyword in sig.get('title_keywords', []):
                    if keyword.lower() in win.title.lower():
                        matched.append(win)
                        break

        return matched

    def enum_child_windows(self, parent_hwnd: int) -> List[WindowInfo]:
        """
        枚举指定窗口的所有子窗口

        Args:
            parent_hwnd: 父窗口句柄

        Returns:
            子窗口信息列表
        """
        self._child_windows = []

        def callback(hwnd, _):
            try:
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)

                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]

                info = WindowInfo(
                    hwnd=hwnd,
                    title=title,
                    class_name=class_name,
                    pid=pid,
                    width=width,
                    height=height,
                    is_visible=win32gui.IsWindowVisible(hwnd),
                    parent_hwnd=parent_hwnd
                )
                self._child_windows.append(info)
            except Exception:
                pass
            return True

        win32gui.EnumChildWindows(parent_hwnd, callback, None)
        return self._child_windows

    def find_render_window(self, parent_hwnd: int, min_size: tuple = (200, 200)) -> Optional[WindowInfo]:
        """
        在子窗口中查找渲染窗口（通常是最大且有特定类名的子窗口）

        Args:
            parent_hwnd: 父窗口句柄
            min_size: 最小尺寸 (width, height)

        Returns:
            渲染窗口信息，未找到返回 None
        """
        children = self.enum_child_windows(parent_hwnd)
        if not children:
            return None

        # 常见的渲染窗口类名
        render_classes = [
            'Qt5QWindowIcon',  # Qt 渲染窗口
            'MuMuPlayer',
            'NemuWindow',
            'Chrome_WidgetWin',  # 某些基于 Chrome 的渲染
            'RenderWindow',
            'GameWindow',
            'SDL_app',  # SDL 应用
            'GLFW',     # GLFW 窗口
        ]

        min_w, min_h = min_size
        candidates = []

        for child in children:
            if child.width < min_w or child.height < min_h:
                continue

            # 检查是否是渲染类窗口
            for render_cls in render_classes:
                if render_cls.lower() in child.class_name.lower():
                    candidates.append(child)
                    break

        if candidates:
            # 返回面积最大的
            return max(candidates, key=lambda w: w.width * w.height)

        # 如果没有匹配类名，返回最大的子窗口
        valid_children = [c for c in children if c.width >= min_w and c.height >= min_h]
        if valid_children:
            return max(valid_children, key=lambda w: w.width * w.height)

        return None

    def get_window_rect(self, hwnd: int) -> tuple:
        """
        获取窗口矩形区域

        Args:
            hwnd: 窗口句柄

        Returns:
            (left, top, right, bottom)
        """
        return win32gui.GetWindowRect(hwnd)

    def get_client_rect(self, hwnd: int) -> tuple:
        """
        获取窗口客户区矩形（不含边框）

        Args:
            hwnd: 窗口句柄

        Returns:
            (left, top, right, bottom) 相对于窗口左上角
        """
        return win32gui.GetClientRect(hwnd)

    def is_window_valid(self, hwnd: int) -> bool:
        """检查窗口句柄是否有效"""
        try:
            return win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd)
        except:
            return False

    def get_window_info(self, hwnd: int) -> Optional[WindowInfo]:
        """获取单个窗口的详细信息"""
        try:
            if not win32gui.IsWindow(hwnd):
                return None

            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]

            return WindowInfo(
                hwnd=hwnd,
                title=title,
                class_name=class_name,
                pid=pid,
                width=width,
                height=height,
                is_visible=win32gui.IsWindowVisible(hwnd),
                parent_hwnd=win32gui.GetParent(hwnd)
            )
        except Exception:
            return None


def list_all_windows():
    """调试函数：列出所有可见窗口"""
    mgr = WindowManager()
    windows = mgr.enum_all_windows()

    print(f"\n找到 {len(windows)} 个可见窗口:")
    print("-" * 80)
    for i, win in enumerate(windows):
        print(f"[{i}] HWND: {win.hwnd:8d} | PID: {win.pid:6d} | "
              f"Size: {win.width:4d}x{win.height:4d} | "
              f"Class: {win.class_name[:30]:30s} | Title: {win.title[:30]}")
    return windows


if __name__ == '__main__':
    list_all_windows()

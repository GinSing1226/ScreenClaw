"""
进程管理服务
使用 pywin32 (win32gui, win32process, win32api)
"""
import os
from typing import List, Optional, Tuple
from functools import lru_cache

import win32gui
import win32process
import win32api
import win32con

from app.models.response import ProcessInfo, ChildWindow


class ProcessService:
    """进程管理服务"""

    # 进程名缓存大小
    _PROCESS_NAME_CACHE_SIZE = 256

    # 常见的渲染窗口类名
    RENDER_WINDOW_CLASSES = [
        'Qt5QWindowIcon',      # Qt 渲染窗口
        'MuMuPlayer',          # MuMu 模拟器
        'NemuWindow',          # MuMu 模拟器（新版）
        'Chrome_WidgetWin',    # 基于 Chrome 的渲染
        'RenderWindow',
        'GameWindow',
        'SDL_app',             # SDL 应用
        'GLFW',                # GLFW 窗口
    ]

    def __init__(self):
        """初始化进程服务"""
        pass

    def get_process_list(self, keyword: str = "", include_children: bool = False, children_filter: str = "titled") -> List[ProcessInfo]:
        """获取进程列表（包含子窗口信息）

        Args:
            keyword: 搜索关键词
            include_children: 是否返回子窗口列表
            children_filter: 子窗口过滤策略，"all"返回全部，"titled"仅返回有标题的
        """
        processes = []

        def enum_windows_callback(hwnd, _):
            """枚举窗口回调"""
            # 只处理可见窗口
            if not win32gui.IsWindowVisible(hwnd):
                return True

            # 获取窗口标题
            window_title = win32gui.GetWindowText(hwnd)
            if not window_title:
                return True

            # 获取进程ID
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)

            # 获取进程名
            process_name = self._get_process_name_impl(process_id)
            if not process_name:
                return True

            # 关键词过滤
            if keyword:
                keyword_lower = keyword.lower()
                if (keyword_lower not in window_title.lower() and
                    keyword_lower not in process_name.lower()):
                    return True

            # 获取子窗口列表（根据参数决定是否获取）
            child_windows = []
            if include_children:
                child_windows = self._get_child_windows_info(hwnd, children_filter)

            processes.append(ProcessInfo(
                process_id=process_id,
                process_name=process_name,
                window_id=hwnd,
                window_title=window_title,
                child_windows=child_windows
            ))

            return True

        # 枚举所有窗口
        win32gui.EnumWindows(enum_windows_callback, None)

        return processes

    def _get_child_windows_info(self, parent_hwnd: int, filter_mode: str = "titled") -> List[ChildWindow]:
        """获取子窗口信息列表

        Args:
            parent_hwnd: 父窗口句柄
            filter_mode: 过滤模式，"all"返回全部，"titled"仅返回有标题的
        """
        children = []

        def callback(hwnd, _):
            try:
                window_title = win32gui.GetWindowText(hwnd) or ""
                class_name = win32gui.GetClassName(hwnd) or ""

                # 根据过滤模式决定是否添加
                if filter_mode == "titled" and not window_title:
                    return True  # 跳过无标题窗口

                children.append(ChildWindow(
                    window_id=hwnd,
                    window_title=window_title,
                    class_name=class_name
                ))
            except Exception:
                pass
            return True

        try:
            win32gui.EnumChildWindows(parent_hwnd, callback, None)
        except Exception:
            pass

        return children

    @lru_cache(maxsize=_PROCESS_NAME_CACHE_SIZE)
    def _get_process_name_impl(self, process_id: int) -> Optional[str]:
        """获取进程名（实际实现，带LRU缓存）"""
        try:
            # 打开进程
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_READ = 0x0010

            handle = win32api.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
                False,
                process_id
            )

            if not handle:
                return None

            try:
                # 获取进程路径
                full_path = win32process.GetModuleFileNameEx(handle, 0)
                # 提取文件名
                return os.path.basename(full_path)
            finally:
                win32api.CloseHandle(handle)

        except Exception:
            return None

    def clear_cache(self):
        """清除进程名缓存"""
        self._get_process_name_impl.cache_clear()

    def get_window_rect(self, hwnd: int) -> Optional[Tuple[int, int, int, int]]:
        """获取窗口矩形"""
        try:
            rect = win32gui.GetWindowRect(hwnd)
            return rect  # (left, top, right, bottom)
        except Exception:
            return None

    def get_client_rect(self, hwnd: int) -> Optional[Tuple[int, int, int, int]]:
        """获取客户区矩形（相对于窗口本身）"""
        try:
            rect = win32gui.GetClientRect(hwnd)
            return rect  # (left, top, right, bottom)
        except Exception:
            return None

    def get_process_by_window_id(self, window_id: int) -> Optional[ProcessInfo]:
        """根据窗口句柄获取进程信息"""
        try:
            if not win32gui.IsWindow(window_id):
                return None

            # 获取进程ID
            _, process_id = win32process.GetWindowThreadProcessId(window_id)

            # 获取窗口标题
            window_title = win32gui.GetWindowText(window_id) or ""

            # 获取进程名
            process_name = self._get_process_name_impl(process_id)

            # 获取子窗口
            child_windows = self._get_child_windows_info(window_id)

            return ProcessInfo(
                process_id=process_id,
                process_name=process_name or "",
                window_id=window_id,
                window_title=window_title,
                child_windows=child_windows
            )
        except Exception:
            return None

    # ============ 兼容旧方法（后续可删除） ============

    def get_hwnd_by_process_id(self, process_id: int) -> Optional[int]:
        """根据进程ID获取主窗口句柄（兼容旧代码）"""
        result = None

        def enum_callback(hwnd, _):
            nonlocal result
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == process_id and win32gui.IsWindowVisible(hwnd):
                result = hwnd
                return False
            return True

        win32gui.EnumWindows(enum_callback, None)

        return result

    def get_process_by_id(self, process_id: int) -> Optional[ProcessInfo]:
        """根据进程ID获取进程信息（兼容旧代码）"""
        hwnd = self.get_hwnd_by_process_id(process_id)
        if not hwnd:
            return None

        return self.get_process_by_window_id(hwnd)

    def find_render_window(self, parent_hwnd: int, min_size: Tuple[int, int] = (200, 200)) -> Optional[int]:
        """
        在子窗口中查找渲染窗口
        用于解决 MuMu 等模拟器的操作兼容性问题

        Args:
            parent_hwnd: 父窗口句柄
            min_size: 最小尺寸 (width, height)

        Returns:
            渲染子窗口句柄，未找到返回 None
        """
        children = self._enum_child_windows(parent_hwnd)
        if not children:
            return None

        min_w, min_h = min_size
        candidates = []

        for child_hwnd in children:
            try:
                rect = win32gui.GetWindowRect(child_hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]

                # 尺寸过滤
                if width < min_w or height < min_h:
                    continue

                class_name = win32gui.GetClassName(child_hwnd)

                # 检查是否是已知的渲染窗口类名
                is_render_class = any(
                    render_class.lower() in class_name.lower()
                    for render_class in self.RENDER_WINDOW_CLASSES
                )

                candidates.append({
                    'hwnd': child_hwnd,
                    'width': width,
                    'height': height,
                    'class_name': class_name,
                    'is_render_class': is_render_class
                })
            except Exception:
                continue

        if not candidates:
            return None

        # 优先选择已知渲染类名的窗口
        render_candidates = [c for c in candidates if c['is_render_class']]
        if render_candidates:
            # 选择面积最大的
            render_candidates.sort(key=lambda x: x['width'] * x['height'], reverse=True)
            return render_candidates[0]['hwnd']

        # 否则选择最大的子窗口
        candidates.sort(key=lambda x: x['width'] * x['height'], reverse=True)
        return candidates[0]['hwnd']

    def _enum_child_windows(self, parent_hwnd: int) -> List[int]:
        """枚举子窗口"""
        children = []

        def callback(hwnd, _):
            children.append(hwnd)
            return True

        try:
            win32gui.EnumChildWindows(parent_hwnd, callback, None)
        except Exception:
            pass

        return children


# 全局进程服务实例
process_service = ProcessService()

"""
进程管理服务
"""
import ctypes
from ctypes import wintypes
from typing import List, Optional, Tuple

from app.models.response import ProcessInfo


class ProcessService:
    """进程管理服务"""

    def __init__(self):
        # Windows API 常量
        self.GW_OWNER = 4
        self.GA_ROOT = 2

        # 加载 Windows API
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32

    def get_process_list(self, keyword: str = "") -> List[ProcessInfo]:
        """获取进程列表"""
        processes = []

        def enum_windows_callback(hwnd, lparam):
            """枚举窗口回调"""
            # 只处理可见窗口
            if not self.user32.IsWindowVisible(hwnd):
                return True

            # 获取窗口标题
            title_length = self.user32.GetWindowTextLengthW(hwnd)
            if title_length == 0:
                return True

            title = ctypes.create_unicode_buffer(title_length + 1)
            self.user32.GetWindowTextW(hwnd, title, title_length + 1)
            window_title = title.value

            # 获取进程ID
            process_id = wintypes.DWORD()
            self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))

            # 获取进程名
            process_name = self._get_process_name(process_id.value)
            if not process_name:
                return True

            # 关键词过滤
            if keyword:
                keyword_lower = keyword.lower()
                if (keyword_lower not in window_title.lower() and
                    keyword_lower not in process_name.lower()):
                    return True

            processes.append(ProcessInfo(
                process_id=process_id.value,
                process_name=process_name,
                window_title=window_title
            ))

            return True

        # 枚举所有窗口
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)

        return processes

    def _get_process_name(self, process_id: int) -> Optional[str]:
        """获取进程名"""
        try:
            # 打开进程
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_VM_READ = 0x0010

            handle = self.kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ,
                False,
                process_id
            )

            if not handle:
                return None

            try:
                # 获取进程路径
                max_path = 260
                path = ctypes.create_unicode_buffer(max_path)
                size = wintypes.DWORD(max_path)

                if self.kernel32.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
                    full_path = path.value
                    # 提取文件名
                    import os
                    return os.path.basename(full_path)

                return None
            finally:
                self.kernel32.CloseHandle(handle)

        except Exception:
            return None

    def get_window_rect(self, hwnd: int) -> Optional[Tuple[int, int, int, int]]:
        """获取窗口矩形"""
        rect = wintypes.RECT()
        if self.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return (rect.left, rect.top, rect.right, rect.bottom)
        return None

    def get_hwnd_by_process_id(self, process_id: int) -> Optional[int]:
        """根据进程ID获取窗口句柄"""
        result = None

        def enum_callback(hwnd, lparam):
            nonlocal result
            pid = wintypes.DWORD()
            self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == process_id and self.user32.IsWindowVisible(hwnd):
                result = hwnd
                return False
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumWindows(WNDENUMPROC(enum_callback), 0)

        return result

    def get_process_by_id(self, process_id: int) -> Optional[ProcessInfo]:
        """根据ID获取进程信息"""
        hwnd = self.get_hwnd_by_process_id(process_id)
        if not hwnd:
            return None

        # 获取窗口标题
        title_length = self.user32.GetWindowTextLengthW(hwnd)
        if title_length == 0:
            window_title = ""
        else:
            title = ctypes.create_unicode_buffer(title_length + 1)
            self.user32.GetWindowTextW(hwnd, title, title_length + 1)
            window_title = title.value

        # 获取进程名
        process_name = self._get_process_name(process_id)

        return ProcessInfo(
            process_id=process_id,
            process_name=process_name or "",
            window_title=window_title
        )


# 全局进程服务实例
process_service = ProcessService()

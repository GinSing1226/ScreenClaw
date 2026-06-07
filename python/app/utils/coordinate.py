"""
坐标转换工具
"""
from typing import Tuple

import win32gui


def percent_to_absolute(
    x_percent: float,
    y_percent: float,
    client_rect: Tuple[int, int, int, int]
) -> Tuple[int, int]:
    """
    百分比坐标转相对于窗口客户区的坐标

    Args:
        x_percent: 横坐标百分比 (0-100)
        y_percent: 纵坐标百分比 (0-100)
        client_rect: 客户区矩形 (left, top, right, bottom)，由 GetClientRect 返回

    Returns:
        (x, y) 相对于窗口客户区左上角的坐标
        注意：PostMessage 的 lParam 期望的是相对于客户区的坐标
    """
    left, top, right, bottom = client_rect
    width = right - left
    height = bottom - top

    # 返回相对于客户区左上角的坐标（PostMessage lParam 格式）
    x = int(width * x_percent / 100)
    y = int(height * y_percent / 100)

    return x, y


def absolute_to_percent(
    x: int,
    y: int,
    client_rect: Tuple[int, int, int, int]
) -> Tuple[float, float]:
    """
    客户区坐标转百分比坐标

    Args:
        x: 相对于客户区的横坐标
        y: 相对于客户区的纵坐标
        client_rect: 客户区矩形 (left, top, right, bottom)

    Returns:
        (x_percent, y_percent) 百分比坐标 (0-100)
    """
    left, top, right, bottom = client_rect
    width = right - left
    height = bottom - top

    if width == 0 or height == 0:
        return 0.0, 0.0

    x_percent = (x - left) * 100 / width
    y_percent = (y - top) * 100 / height

    return x_percent, y_percent


def client_to_screen(
    hwnd: int,
    client_x: int,
    client_y: int
) -> Tuple[int, int]:
    """
    客户区坐标转屏幕坐标

    Args:
        hwnd: 窗口句柄
        client_x: 客户区横坐标
        client_y: 客户区纵坐标

    Returns:
        (screen_x, screen_y) 屏幕坐标
    """
    return win32gui.ClientToScreen(hwnd, (client_x, client_y))


def restore_window_and_calc_coords(hwnd: int, x_pct: float, y_pct: float, main_window_id: int = None):
    """恢复窗口（如果需要）并计算坐标

    Args:
        hwnd: 窗口句柄（操作目标）
        x_pct, y_pct: 百分比坐标
        main_window_id: 主窗口ID（可选，用于恢复主窗口）

    Returns:
        (physical_x, physical_y, virtual_x, virtual_y) 或 None
    """
    import ctypes
    import win32con
    import time
    from app.services.process_service import process_service

    # 如果提供了主窗口ID，检查并恢复主窗口
    if main_window_id:
        is_minimized = win32gui.IsIconic(main_window_id)
        is_visible = win32gui.IsWindowVisible(main_window_id)

        # 恢复最小化的主窗口
        if is_minimized:
            win32gui.ShowWindow(main_window_id, win32con.SW_RESTORE)
            # 等待恢复完成
            start = time.time()
            restored = False
            while time.time() - start < 2.0:
                if win32gui.IsWindowVisible(main_window_id) and not win32gui.IsIconic(main_window_id):
                    restored = True
                    break
                time.sleep(0.01)

            time.sleep(0.3)  # 等待子窗口可用

        # 处理隐藏的主窗口
        elif not is_visible:
            win32gui.ShowWindow(main_window_id, win32con.SW_SHOW)
            time.sleep(0.3)

    # 获取窗口矩形（DPI-aware 进程中 GetWindowRect 返回物理坐标，无需 DPI 转换）
    window_rect = process_service.get_window_rect(hwnd)

    if not window_rect:
        return None

    win_w = window_rect[2] - window_rect[0]
    win_h = window_rect[3] - window_rect[1]

    # 窗口相对像素位置（百分比 → 像素，参考系为整个窗口含标题栏）
    win_rel_x = int(win_w * x_pct / 100)
    win_rel_y = int(win_h * y_pct / 100)

    # physical_x/y 保持为窗口相对偏移（已弃用但保持接口兼容）
    physical_x = win_rel_x
    physical_y = win_rel_y

    # 客户区偏移（标题栏 + 窗口边框）
    # 录制时百分比是相对整个窗口（GetWindowRect），但 ClientToScreen / PostMessage
    # 期望客户区相对坐标，需要减去标题栏和边框的高度
    client_origin = win32gui.ClientToScreen(hwnd, (0, 0))
    client_offset_x = client_origin[0] - window_rect[0]
    client_offset_y = client_origin[1] - window_rect[1]

    # virtual_x/y: 客户区相对坐标（用于 ClientToScreen / PostMessage lParam）
    virtual_x = win_rel_x - client_offset_x
    virtual_y = win_rel_y - client_offset_y

    return physical_x, physical_y, virtual_x, virtual_y

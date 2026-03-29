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

    # 获取窗口矩形
    window_rect = process_service.get_window_rect(hwnd)

    if not window_rect:
        return None

    virtual_width = window_rect[2] - window_rect[0]
    virtual_height = window_rect[3] - window_rect[1]

    system_dpi = ctypes.windll.user32.GetDpiForSystem()
    window_dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
    scale_factor = window_dpi / system_dpi if system_dpi > 0 else 1.0

    physical_width = int(virtual_width * scale_factor)
    physical_height = int(virtual_height * scale_factor)

    physical_x = int(physical_width * x_pct / 100)
    physical_y = int(physical_height * y_pct / 100)
    virtual_x = int(virtual_width * x_pct / 100)
    virtual_y = int(virtual_height * y_pct / 100)

    return physical_x, physical_y, virtual_x, virtual_y

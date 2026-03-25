"""
坐标转换工具
"""
from typing import Tuple


def percent_to_absolute(
    x_percent: float,
    y_percent: float,
    window_rect: Tuple[int, int, int, int]
) -> Tuple[int, int]:
    """
    百分比坐标转绝对坐标

    Args:
        x_percent: 横坐标百分比 (0-100)
        y_percent: 纵坐标百分比 (0-100)
        window_rect: 窗口矩形 (left, top, right, bottom)

    Returns:
        (x, y) 绝对坐标
    """
    left, top, right, bottom = window_rect
    width = right - left
    height = bottom - top

    x = left + int(width * x_percent / 100)
    y = top + int(height * y_percent / 100)

    return x, y


def absolute_to_percent(
    x: int,
    y: int,
    window_rect: Tuple[int, int, int, int]
) -> Tuple[float, float]:
    """
    绝对坐标转百分比坐标

    Args:
        x: 绝对横坐标
        y: 绝对纵坐标
        window_rect: 窗口矩形 (left, top, right, bottom)

    Returns:
        (x_percent, y_percent) 百分比坐标 (0-100)
    """
    left, top, right, bottom = window_rect
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
    import ctypes

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    point = POINT(client_x, client_y)
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(point))

    return point.x, point.y

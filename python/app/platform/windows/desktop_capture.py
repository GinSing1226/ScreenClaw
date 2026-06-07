"""
桌面级截图与坐标模块

基于 mss 实现桌面截图，提供显示器枚举和百分比坐标到屏幕绝对坐标的转换。

坐标系统说明：
- mss 截图使用物理像素(高 DPI 下分辨率更大，如 4K 3840x2160)
- SetCursorPos / mouse_event 使用的坐标系取决于进程 DPI 感知：
  - DPI-aware 进程：物理坐标(mss 初始化后本进程为 DPI-aware)
  - DPI-unaware 进程：虚拟坐标
- 关键：mss 初始化时会调用 SetProcessDpiAwareness，将进程从 DPI-unaware
  变为 DPI-aware。因此必须在模块加载时立即初始化 mss，确保后续所有
  GetMonitorInfo / SetCursorPos 调用都在同一坐标系下。
"""
import mss
import ctypes
import time
import subprocess
import sys
import math
import random
import win32api
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
from PIL import Image

# 【关键】模块加载时立即初始化 mss。
# mss 在首次创建实例时会调用 SetProcessDpiAwareness 将进程设为 DPI-aware。
# 如果不在这里预先触发，后续的 GetMonitorInfo 和 SetCursorPos 会
# 使用不同的坐标系，导致坐标偏移。
_mss_instance = mss.mss()
_mss_monitors_cache = _mss_instance.monitors  # 同时缓存 monitors 数据


def _get_screen_monitor_rects() -> List[Dict[str, int]]:
    """通过 Win32 API 获取显示器的屏幕坐标矩形

    EnumDisplayMonitors + GetMonitorInfo 返回的坐标与 SetCursorPos / mouse_event 一致：
    - DPI-aware 进程：返回物理坐标
    - DPI-unaware 进程：返回虚拟(缩放后)坐标
    两种情况下都与 SetCursorPos 坐标系匹配，确保坐标转换正确。

    Returns:
        每个显示器的屏幕矩形列表，按枚举顺序索引：
        [{"left": int, "top": int, "right": int, "bottom": int, "width": int, "height": int}, ...]
    """
    result = []
    monitors = win32api.EnumDisplayMonitors()
    for hmon, hdc, rect in monitors:
        info = win32api.GetMonitorInfo(hmon)
        mon_rect = info["Monitor"]  # (left, top, right, bottom)
        result.append({
            "left": mon_rect[0],
            "top": mon_rect[1],
            "right": mon_rect[2],
            "bottom": mon_rect[3],
            "width": mon_rect[2] - mon_rect[0],
            "height": mon_rect[3] - mon_rect[1],
        })
    return result


def _get_physical_monitor_rects() -> List[Dict[str, int]]:
    """通过 mss 获取显示器的物理像素矩形

    mss 返回物理像素坐标。在有 DPI 缩放的显示器上，
    物理尺寸 > 虚拟尺寸(如 3840 vs 2560)。
    仅用于截图捕获。

    Returns:
        每个显示器的物理矩形列表
    """
    return _mss_monitors_cache[1:]  # 跳过 [0](全虚拟桌面合计)


def get_monitors() -> List[Dict[str, Any]]:
    """枚举所有显示器

    使用虚拟坐标报告分辨率和位置(与 Windows 显示设置一致)。
    同时保留物理分辨率供截图参考。

    Returns:
        显示器信息列表，每项包含 index, name, resolution, is_primary, left, top, width, height
    """
    virtual_rects = _get_screen_monitor_rects()
    physical_rects = _get_physical_monitor_rects()

    result = []
    for i, vrect in enumerate(virtual_rects):
        # 物理分辨率(来自 mss，用于截图参考)
        prect = physical_rects[i] if i < len(physical_rects) else vrect
        result.append({
            "index": i,
            "name": f"显示器 {i + 1}",
            "resolution": f"{prect['width']}x{prect['height']}",
            "is_primary": vrect["left"] == 0 and vrect["top"] == 0,
            "left": vrect["left"],
            "top": vrect["top"],
            "width": vrect["width"],
            "height": vrect["height"],
        })
    return result


def get_monitor_dpi_scale(monitor_index: int) -> float:
    """获取指定显示器的 DPI 缩放率

    Args:
        monitor_index: 显示器索引(从 0 开始)

    Returns:
        DPI 缩放率(1.0 = 100%, 1.5 = 150%)
    """
    monitors = win32api.EnumDisplayMonitors()
    if monitor_index < 0 or monitor_index >= len(monitors):
        return 1.0
    hmon = int(monitors[monitor_index][0])
    dpi_x = ctypes.c_uint()
    dpi_y = ctypes.c_uint()
    ctypes.windll.shcore.GetDpiForMonitor(ctypes.c_void_p(hmon), 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y))
    return round(dpi_x.value / 96.0, 2)


def capture_monitor(monitor_index: int) -> Image.Image:
    """截取指定显示器的画面

    Args:
        monitor_index: 显示器索引(从 0 开始)

    Returns:
        PIL.Image RGB 模式

    Raises:
        IndexError: monitor_index 越界
    """
    with mss.mss() as sct:
        raw_monitors = sct.monitors
        if monitor_index < 0 or monitor_index + 1 >= len(raw_monitors):
            raise IndexError(f"Monitor index {monitor_index} out of range. Available: 0-{len(raw_monitors) - 2}")
        target = raw_monitors[monitor_index + 1]
        screenshot = sct.grab(target)
        # mss 返回 BGRA，转为 RGB
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")


def desktop_percent_to_screen(monitor_index: int, x_pct: float, y_pct: float) -> Tuple[int, int]:
    """桌面百分比坐标 → 屏幕绝对像素坐标(虚拟坐标)

    使用 Win32 API 获取显示器的虚拟坐标矩形，与 SetCursorPos 坐标系一致。
    这样在有 DPI 缩放的显示器上(如 4K 150%)，坐标转换才是准确的。

    Args:
        monitor_index: 显示器索引
        x_pct: 百分比横坐标 (0-100)
        y_pct: 百分比纵坐标 (0-100)

    Returns:
        (screen_x, screen_y) 屏幕虚拟绝对坐标，可直接用于 SetCursorPos
    """
    virtual_rects = _get_screen_monitor_rects()
    if monitor_index < 0 or monitor_index >= len(virtual_rects):
        raise IndexError(f"Monitor index {monitor_index} out of range. Available: 0-{len(virtual_rects) - 1}")
    mon = virtual_rects[monitor_index]
    screen_x = mon["left"] + int(mon["width"] * x_pct / 100)
    screen_y = mon["top"] + int(mon["height"] * y_pct / 100)
    return screen_x, screen_y


# ============ 桌面操作注入 ============

@dataclass
class DesktopInjectResult:
    """桌面操作注入结果"""
    success: bool
    error: Optional[str] = None


def _run_subprocess(code: str, timeout: int = 5, non_blocking: bool = False, semi_blocking: bool = False) -> bool:
    """在子进程中执行代码(与窗口级 input.py 相同模式)

    打包环境(frozen)使用 sys._MEIPASS 下的嵌入 Python 解释器。
    开发环境使用 sys.executable。

    注意：子进程是全新 Python 进程，不会继承父进程的 DPI awareness。
    本模块在加载时通过 mss 初始化将父进程设为 DPI-aware(物理坐标)，
    因此子进程代码头部会注入 SetProcessDpiAwareness(2) 确保坐标系一致。
    """
    # 注入 DPI awareness 设置，确保子进程与父进程使用同一套屏幕坐标
    dpi_awareness_prefix = (
        "import ctypes; "
        "ctypes.windll.shcore.SetProcessDpiAwareness(2); "
    )
    code = dpi_awareness_prefix + code

    is_frozen = getattr(sys, 'frozen', False)
    debug_lines = [f"[DesktopInput] _run_subprocess: is_frozen={is_frozen}, sys.executable={sys.executable}"]

    if is_frozen:
        import os
        embed_python_dir = os.path.join(sys._MEIPASS, 'embed_python')
        python_exe = os.path.join(embed_python_dir, 'python.exe')

        env = os.environ.copy()
        env['PATH'] = embed_python_dir + os.pathsep + env.get('PATH', '')
        env['PYTHONIOENCODING'] = 'utf-8'
        debug_lines.append(f"  frozen mode: python_exe={python_exe}, embed_dir={embed_python_dir}")
    else:
        python_exe = sys.executable
        env = None
        debug_lines.append(f"  dev mode: python_exe={python_exe}")

    # 打印调试信息(flush=True 解决 Python stdout 缓冲导致日志不输出的问题)
    for line in debug_lines:
        print(line, flush=True)

    # 打印要执行的代码(前200字符)
    code_preview = code.strip()[:200]
    print(f"[DesktopInput] code preview: {code_preview}", flush=True)

    try:
        if non_blocking:
            subprocess.Popen(
                [python_exe, '-c', code],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
                env=env
            )
            return True
        elif semi_blocking:
            proc = subprocess.Popen(
                [python_exe, '-c', code],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
                env=env
            )
            try:
                proc.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                pass
            return True
        else:
            result = subprocess.run(
                [python_exe, '-c', code],
                capture_output=True, text=True, timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW,
                env=env
            )
            if result.returncode != 0:
                print(f"[DesktopInput] FAILED returncode={result.returncode}", flush=True)
                if result.stderr:
                    print(f"[DesktopInput] stderr: {result.stderr[:500]}", flush=True)
                if result.stdout:
                    print(f"[DesktopInput] stdout: {result.stdout[:500]}", flush=True)
            else:
                print(f"[DesktopInput] OK", flush=True)
            return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"[DesktopInput] Subprocess timeout ({timeout}s)", flush=True)
        return False
    except Exception as e:
        print(f"[DesktopInput] Subprocess exception: {e}", flush=True)
        return False


def _generate_humanized_path(start_x, start_y, end_x, end_y, steps=10):
    """生成人类化鼠标路径(简化版, 复用贝塞尔曲线逻辑)"""
    dist = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
    if dist < 3:
        return [(end_x, end_y)]

    # 贝塞尔控制点偏移
    mid_x = (start_x + end_x) / 2
    mid_y = (start_y + end_y) / 2
    perp_x = -(end_y - start_y) / dist
    perp_y = (end_x - start_x) / dist
    offset = random.uniform(-0.15, 0.15) * dist
    ctrl_x = mid_x + perp_x * offset
    ctrl_y = mid_y + perp_y * offset

    path = []
    for i in range(1, steps + 1):
        t = i / steps
        # Cubic ease-in-out
        if t < 0.5:
            eased = 4 * t * t * t
        else:
            eased = 1 - (-2 * t + 2) ** 3 / 2
        # 二次贝塞尔
        bx = (1 - eased) ** 2 * start_x + 2 * (1 - eased) * eased * ctrl_x + eased ** 2 * end_x
        by = (1 - eased) ** 2 * start_y + 2 * (1 - eased) * eased * ctrl_y + eased ** 2 * end_y
        # 微抖动
        jitter = min(2, dist * 0.01)
        bx += random.uniform(-jitter, jitter)
        by += random.uniform(-jitter, jitter)
        path.append((int(bx), int(by)))
    return path


def desktop_click(screen_x: int, screen_y: int, restore: bool = True) -> DesktopInjectResult:
    """桌面点击(hijack 模式)"""
    restore_code = "win32api.SetCursorPos(old_pos)" if restore else ""

    code = f"""
import ctypes, time, win32api
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
old_pos = win32api.GetCursorPos()
win32api.SetCursorPos(({screen_x}, {screen_y}))
time.sleep(0.02)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(0.02)
{restore_code}
"""
    success = _run_subprocess(code)
    return DesktopInjectResult(success=success, error=None if success else "Click failed")


def desktop_double_click(screen_x: int, screen_y: int, restore: bool = True) -> DesktopInjectResult:
    """桌面双击"""
    restore_code = "win32api.SetCursorPos(old_pos)" if restore else ""

    code = f"""
import ctypes, time, win32api
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
old_pos = win32api.GetCursorPos()
win32api.SetCursorPos(({screen_x}, {screen_y}))
time.sleep(0.02)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(0.08)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(0.02)
{restore_code}
"""
    success = _run_subprocess(code)
    return DesktopInjectResult(success=success, error=None if success else "Double click failed")


def desktop_right_click(screen_x: int, screen_y: int, restore: bool = True) -> DesktopInjectResult:
    """桌面右键"""
    restore_code = "win32api.SetCursorPos(old_pos)" if restore else ""

    code = f"""
import ctypes, time, win32api
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
old_pos = win32api.GetCursorPos()
win32api.SetCursorPos(({screen_x}, {screen_y}))
time.sleep(0.02)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
time.sleep(0.02)
{restore_code}
"""
    success = _run_subprocess(code)
    return DesktopInjectResult(success=success, error=None if success else "Right click failed")


def desktop_drag(start_x: int, start_y: int, end_x: int, end_y: int,
                 duration_ms: int = 500, restore: bool = True) -> DesktopInjectResult:
    """桌面拖拽(支持跨屏)"""
    steps = max(5, min(20, duration_ms // 50))
    step_delay = duration_ms / steps / 1000
    restore_code = "win32api.SetCursorPos(old_pos)" if restore else ""

    code = f"""
import ctypes, time, win32api, math, random
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
old_pos = win32api.GetCursorPos()
sx, sy = {start_x}, {start_y}
ex, ey = {end_x}, {end_y}
win32api.SetCursorPos((sx, sy))
time.sleep(0.05)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
steps = {steps}
for i in range(1, steps + 1):
    t = i / steps
    if t < 0.5:
        eased = 4 * t * t * t
    else:
        eased = 1 - (-2 * t + 2) ** 3 / 2
    px = int(sx + (ex - sx) * eased)
    py = int(sy + (ey - sy) * eased)
    win32api.SetCursorPos((px, py))
    time.sleep({step_delay:.4f})
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(0.02)
{restore_code}
"""
    success = _run_subprocess(code, timeout=max(5, duration_ms // 1000 + 3))
    return DesktopInjectResult(success=success, error=None if success else "Drag failed")


def desktop_scroll(screen_x: int, screen_y: int, delta: int, restore: bool = True) -> DesktopInjectResult:
    """桌面滚动"""
    restore_code = "win32api.SetCursorPos(old_pos)" if restore else ""

    code = f"""
import ctypes, time, win32api
MOUSEEVENTF_WHEEL = 0x0800
old_pos = win32api.GetCursorPos()
win32api.SetCursorPos(({screen_x}, {screen_y}))
time.sleep(0.02)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, {delta}, 0)
time.sleep(0.02)
{restore_code}
"""
    success = _run_subprocess(code)
    return DesktopInjectResult(success=success, error=None if success else "Scroll failed")


def desktop_input_text(screen_x: int, screen_y: int, text: str, restore: bool = True) -> DesktopInjectResult:
    """桌面文本输入(点击获取焦点 + 剪贴板粘贴)"""
    # 转义文本中的特殊字符
    escaped_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
    restore_code = "win32api.SetCursorPos(old_pos)" if restore else ""

    code = f"""
import ctypes, time, win32api, win32clipboard
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
old_pos = win32api.GetCursorPos()
win32api.SetCursorPos(({screen_x}, {screen_y}))
time.sleep(0.02)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(0.1)
win32clipboard.OpenClipboard()
win32clipboard.EmptyClipboard()
win32clipboard.SetClipboardText('{escaped_text}')
win32clipboard.CloseClipboard()
VK_CONTROL = 0x11
scan_ctrl = ctypes.windll.user32.MapVirtualKeyW(VK_CONTROL, 0)
scan_v = ctypes.windll.user32.MapVirtualKeyW(ord('V'), 0)
ctypes.windll.user32.keybd_event(VK_CONTROL, scan_ctrl, 0, 0)
time.sleep(0.02)
ctypes.windll.user32.keybd_event(ord('V'), scan_v, 0, 0)
time.sleep(0.02)
ctypes.windll.user32.keybd_event(ord('V'), scan_v, 2, 0)
ctypes.windll.user32.keybd_event(VK_CONTROL, scan_ctrl, 2, 0)
time.sleep(0.05)
{restore_code}
"""
    success = _run_subprocess(code)
    return DesktopInjectResult(success=success, error=None if success else "Input text failed")


def desktop_press_key(keys: str, duration_ms: int = 0,
                      screen_x: Optional[int] = None, screen_y: Optional[int] = None) -> DesktopInjectResult:
    """桌面按键

    Args:
        keys: 按键组合，空格分隔
        duration_ms: 按住时长
        screen_x: 可选，屏幕绝对坐标 X。传值则先点击定位再按键
        screen_y: 可选，屏幕绝对坐标 Y。传值则先点击定位再按键
    """
    key_map = {
        'ctrl': 0x11, 'shift': 0x10, 'alt': 0x12, 'win': 0x5B,
        'enter': 0x0D, 'tab': 0x09, 'escape': 0x1B, 'space': 0x20,
        'backspace': 0x08, 'delete': 0x2E, 'insert': 0x2D,
        'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
        'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
        'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
        'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
        'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22,
        'capslock': 0x14, 'numlock': 0x90,
    }
    modifier_vks = {0x11, 0x12, 0x10, 0x5B}

    parts = keys.strip().split()
    vks = []
    for part in parts:
        part_lower = part.lower()
        if part_lower in key_map:
            vks.append(key_map[part_lower])
        elif len(part) == 1:
            vks.append(ord(part.upper()))

    if not vks:
        return DesktopInjectResult(success=False, error=f"No valid keys in: {keys}")

    modifiers = [vk for vk in vks if vk in modifier_vks]
    main_keys = [vk for vk in vks if vk not in modifier_vks]
    if not main_keys:
        main_keys = modifiers
        modifiers = []

    # 构建 keybd_event 调用
    key_events = ""
    for vk in modifiers:
        scan = f"ctypes.windll.user32.MapVirtualKeyW({vk}, 0)"
        key_events += f"ctypes.windll.user32.keybd_event({vk}, {scan}, 0, 0)\ntime.sleep(0.02)\n"
    for vk in main_keys:
        scan = f"ctypes.windll.user32.MapVirtualKeyW({vk}, 0)"
        key_events += f"ctypes.windll.user32.keybd_event({vk}, {scan}, 0, 0)\n"
    if duration_ms > 0:
        key_events += f"time.sleep({duration_ms / 1000})\n"
    else:
        key_events += "time.sleep(0.02)\n"
    for vk in reversed(main_keys):
        scan = f"ctypes.windll.user32.MapVirtualKeyW({vk}, 0)"
        key_events += f"ctypes.windll.user32.keybd_event({vk}, {scan}, 2, 0)\ntime.sleep(0.02)\n"
    for vk in reversed(modifiers):
        scan = f"ctypes.windll.user32.MapVirtualKeyW({vk}, 0)"
        key_events += f"ctypes.windll.user32.keybd_event({vk}, {scan}, 2, 0)\ntime.sleep(0.02)\n"

    # 可选的点击定位代码
    click_code = ""
    if screen_x is not None and screen_y is not None:
        click_code = f"""
import win32api
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
win32api.SetCursorPos(({screen_x}, {screen_y}))
time.sleep(0.02)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.05)
ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(0.1)
"""

    imports = "import ctypes, time"
    if click_code:
        imports += ", win32api"

    code = f"""
{imports}
{click_code}{key_events}
"""
    non_block = duration_ms > 0
    success = _run_subprocess(code, non_blocking=non_block)
    return DesktopInjectResult(success=success, error=None if success else "Key press failed")


def desktop_hover(screen_x: int, screen_y: int, duration_ms: int = 1000, restore: bool = True) -> DesktopInjectResult:
    """桌面悬浮"""
    restore_code = "win32api.SetCursorPos(old_pos)" if restore else ""

    code = f"""
import ctypes, time, win32api
old_pos = win32api.GetCursorPos()
win32api.SetCursorPos(({screen_x}, {screen_y}))
time.sleep({duration_ms / 1000})
{restore_code}
"""
    success = _run_subprocess(code, timeout=max(5, duration_ms // 1000 + 3), semi_blocking=True)
    return DesktopInjectResult(success=success, error=None if success else "Hover failed")

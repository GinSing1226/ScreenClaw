"""
Windows 全局 Hook 管理器
WH_MOUSE_LL + WH_KEYBOARD_LL + WH_GETMESSAGE(IME)
在独立守护线程中运行，回调只入队（< 1ms）
"""
import ctypes
import ctypes.wintypes
import queue
import threading
import time
from typing import Optional, Callable

from app.models.recording import RawHookEvent, HookEventType

# ============================================================
# Win32 常量
# ============================================================
WH_MOUSE_LL = 14
WH_KEYBOARD_LL = 13

WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MOUSEWHEEL = 0x020A

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0106
WM_SYSKEYUP = 0x0107

WM_QUIT = 0x0012
WM_USER = 0x0400
WM_STOP_HOOK = WM_USER + 100  # 自定义消息：停止 Hook

# ============================================================
# ctypes 结构体（模块级定义，防止 GC）
# ============================================================


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", POINT),
        ("mouseData", ctypes.c_ulong),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.wintypes.DWORD),
        ("scanCode", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class MSGSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.wintypes.HWND),
        ("message", ctypes.wintypes.UINT),
        ("wParam", ctypes.wintypes.WPARAM),
        ("lParam", ctypes.wintypes.LPARAM),
        ("time", ctypes.wintypes.DWORD),
        ("pt", POINT),
    ]


# Win32 函数原型（64 位兼容：必须设置 argtypes，否则默认 c_int 截断指针）
# LRESULT = LONG_PTR，与 LPARAM 同宽度，用 LPARAM 代替
_user32 = ctypes.windll.user32
_user32.CallNextHookEx.argtypes = [
    ctypes.c_void_p,          # hhk (HHOOK)
    ctypes.c_int,             # nCode
    ctypes.wintypes.WPARAM,   # wParam
    ctypes.wintypes.LPARAM,   # lParam
]
_user32.CallNextHookEx.restype = ctypes.wintypes.LPARAM  # LRESULT

# 回调函数类型（模块级，防止 GC）
HOOKPROC = ctypes.CFUNCTYPE(
    ctypes.wintypes.LPARAM,   # return LRESULT（指针宽度）
    ctypes.c_int,             # nCode
    ctypes.wintypes.WPARAM,   # wParam
    ctypes.wintypes.LPARAM,   # lParam
)


class WindowsHookManager:
    """管理 WH_MOUSE_LL / WH_KEYBOARD_LL / WH_GETMESSAGE 钩子"""

    # 连续回调异常超过此阈值 → 自动停止 Hook，避免卡死系统
    _MAX_CONSECUTIVE_ERRORS = 10

    def __init__(self):
        self._event_queue: queue.Queue = queue.Queue()
        self._running = False
        self._start_time_us: int = 0
        self._hook_thread_id: int = 0
        self._screenclaw_pid: int = 0
        self._filter_fn: Optional[Callable] = None
        self._thread: Optional[threading.Thread] = None
        self._consecutive_errors: int = 0

        # 保持回调引用防止 GC（关键！）
        self._mouse_cb: Optional[HOOKPROC] = None
        self._keyboard_cb: Optional[HOOKPROC] = None

    def start(self, filter_fn: Optional[Callable] = None) -> None:
        """启动 Hook（守护线程）

        Args:
            filter_fn: 可选的过滤回调 filter_fn(screen_x, screen_y) -> bool
                       返回 True 表示过滤掉该事件
        """
        if self._running:
            return
        self._filter_fn = filter_fn
        self._screenclaw_pid = ctypes.windll.kernel32.GetCurrentProcessId()
        self._start_time_us = int(time.time() * 1_000_000)
        self._consecutive_errors = 0
        self._running = True
        self._thread = threading.Thread(
            target=self._hook_loop,
            daemon=True,
            name="RecordingHook",
        )
        self._thread.start()

    def stop(self) -> None:
        """停止 Hook"""
        if not self._running:
            return
        self._running = False
        # 向 Hook 线程发 WM_QUIT
        if self._hook_thread_id:
            ctypes.windll.user32.PostThreadMessageW(
                self._hook_thread_id, WM_QUIT, 0, 0
            )
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._thread = None

    def get_event(self, timeout: float = 0.01) -> Optional[RawHookEvent]:
        """从队列取事件（非阻塞）"""
        try:
            return self._event_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    # ============================================================
    # Hook 线程主循环
    # ============================================================

    def _hook_loop(self):
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        self._hook_thread_id = kernel32.GetCurrentThreadId()

        # ---- 创建回调并保持引用 ----
        self._mouse_cb = HOOKPROC(self._mouse_proc)
        self._keyboard_cb = HOOKPROC(self._keyboard_proc)

        # ---- 注册钩子（仅低级钩子，可跨进程） ----
        mouse_hook = user32.SetWindowsHookExW(
            WH_MOUSE_LL, self._mouse_cb, None, 0
        )
        kb_hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._keyboard_cb, None, 0
        )

        if not mouse_hook or not kb_hook:
            self._running = False
            return

        # ---- 消息循环（低级钩子必须有） ----
        msg = MSGSTRUCT()
        while self._running:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0 or ret == -1:
                break

        # ---- 注销钩子 ----
        if mouse_hook:
            user32.UnhookWindowsHookEx(mouse_hook)
        if kb_hook:
            user32.UnhookWindowsHookEx(kb_hook)

    # ============================================================
    # 安全回调包装：异常不阻断事件，连续失败自动停止 Hook
    # ============================================================

    def _safe_call_next(self, nCode, wParam, lParam):
        """调用 CallNextHookEx，如果 Hook 已被自动停止则返回 1（放行）"""
        if not self._running:
            return 1  # 已停止，放行所有事件
        return _user32.CallNextHookEx(None, nCode, wParam, lParam)

    def _on_callback_error(self):
        """回调异常计数，超阈值自动停止 Hook"""
        self._consecutive_errors += 1
        if self._consecutive_errors >= self._MAX_CONSECUTIVE_ERRORS:
            import logging
            logging.getLogger(__name__).error(
                f"[HOOK] 连续 {self._consecutive_errors} 次回调异常，自动停止 Hook"
            )
            self._running = False  # 触发 Hook 线程退出

    def _on_callback_success(self):
        """回调成功，重置计数"""
        self._consecutive_errors = 0

    # ============================================================
    # 鼠标钩子回调
    # ============================================================

    def _mouse_proc(self, nCode, wParam, lParam):
        try:
            if nCode >= 0 and self._running:
                mhs = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                sx, sy = mhs.pt.x, mhs.pt.y

                # 过滤 screenclaw 自身窗口
                if self._should_filter_mouse(sx, sy):
                    return _user32.CallNextHookEx(None, nCode, wParam, lParam)

                event_type = None
                delta = 0

                if wParam == WM_LBUTTONDOWN:
                    event_type = HookEventType.LBUTTONDOWN
                elif wParam == WM_LBUTTONUP:
                    event_type = HookEventType.LBUTTONUP
                elif wParam == WM_LBUTTONDBLCLK:
                    event_type = HookEventType.LBUTTONDOWN  # 双击作为第二次按下处理
                elif wParam == WM_RBUTTONDOWN:
                    event_type = HookEventType.RBUTTONDOWN
                elif wParam == WM_RBUTTONUP:
                    event_type = HookEventType.RBUTTONUP
                elif wParam == WM_MOUSEWHEEL:
                    event_type = HookEventType.MOUSEWHEEL
                    delta = ctypes.c_short(mhs.mouseData >> 16).value

                if event_type:
                    now_us = int(time.time() * 1_000_000) - self._start_time_us
                    self._event_queue.put(RawHookEvent(
                        event_type=event_type,
                        screen_x=sx, screen_y=sy,
                        delta=delta,
                        timestamp_us=now_us,
                        flags=mhs.flags,
                    ), block=False)
            self._on_callback_success()
        except Exception:
            self._on_callback_error()
        return self._safe_call_next(nCode, wParam, lParam)

    # ============================================================
    # 键盘钩子回调
    # ============================================================

    def _keyboard_proc(self, nCode, wParam, lParam):
        try:
            if nCode >= 0 and self._running:
                khs = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents

                event_type = None
                if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    event_type = HookEventType.KEYDOWN
                elif wParam in (WM_KEYUP, WM_SYSKEYUP):
                    event_type = HookEventType.KEYUP

                if event_type:
                    now_us = int(time.time() * 1_000_000) - self._start_time_us
                    self._event_queue.put(RawHookEvent(
                        event_type=event_type,
                        vk_code=khs.vkCode,
                        scan_code=khs.scanCode,
                        timestamp_us=now_us,
                        flags=khs.flags,
                    ), block=False)
            self._on_callback_success()
        except Exception:
            self._on_callback_error()
        return self._safe_call_next(nCode, wParam, lParam)

    # ============================================================
    # 过滤
    # ============================================================

    def _should_filter_mouse(self, screen_x: int, screen_y: int) -> bool:
        """过滤 screenclaw 自身窗口上的鼠标事件"""
        if self._filter_fn and self._filter_fn(screen_x, screen_y):
            return True
        # 通过 WindowFromPoint + 进程ID 判断
        try:
            pt = POINT(screen_x, screen_y)
            hwnd = ctypes.windll.user32.WindowFromPoint(pt)
            if hwnd:
                pid = ctypes.wintypes.DWORD()
                ctypes.windll.user32.GetWindowThreadProcessId(
                    hwnd, ctypes.byref(pid)
                )
                if pid.value == self._screenclaw_pid:
                    return True
        except Exception:
            pass
        return False


# 全局单例
hook_manager = WindowsHookManager()

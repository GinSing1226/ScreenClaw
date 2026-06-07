"""
录制服务 — 生命周期管理、事件处理、截图管线、悬浮面板、产物存储

线程模型：
  Hook 线程 (hook_manager)         → 原始事件入队 <1ms
  事件处理线程 (_processing_loop)  → DOWN预截图→分类→识别进程→使用预截图→入标记队列
  标记绘制线程 (_marker_loop)      → 取截图+坐标→绘制标记→保存PNG
  悬浮面板线程 (_overlay_loop)     → Win32原生面板，GDI绘制
"""
import json
import os
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from app.models.recording import RecordStep, StepProcessInfo, RecordingMeta
from app.core.recorder import EventClassifier, MODIFIER_VKS, FUNCTION_KEY_VKS
from app.platform.windows.hook import hook_manager
from app.services.log_service import get_project_root


class RecordingService:
    """录制服务 — 全局单例"""

    def __init__(self):
        self._is_recording = False
        self._start_time: float = 0
        self._start_time_iso: str = ""
        self._steps: List[Dict] = []
        self._step_counter = 0
        self._record_dir: Optional[str] = None
        self._classifier: Optional[EventClassifier] = None

        # 线程控制
        self._stop_event = threading.Event()
        self._processing_thread: Optional[threading.Thread] = None
        self._marker_thread: Optional[threading.Thread] = None
        self._screenshot_queue: queue.Queue = queue.Queue()

        # 悬浮面板
        self._overlay_hwnd = None
        self._overlay_thread: Optional[threading.Thread] = None

        # 线程安全锁
        self._lock = threading.Lock()

        # 预截图缓存（DOWN 时捕获，step 产出时消费）
        self._pending_capture = None

    # ================================================================
    # 公开 API
    # ================================================================

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def get_status(self) -> dict:
        """当前录制状态"""
        if not self._is_recording:
            return {"is_recording": False, "duration_ms": 0, "step_count": 0}
        duration = int((time.time() - self._start_time) * 1000)
        return {"is_recording": True, "duration_ms": duration, "step_count": self._step_counter}

    def start(self) -> dict:
        """开始录制"""
        if self._is_recording:
            return {"success": False, "message": "Already recording"}

        # 延迟导入避免循环依赖
        from app.services.config_service import config_service
        config = config_service.get()
        rec_config = config.recording

        # 创建输出目录
        now = datetime.now()
        dir_name = f"record_{now.strftime('%Y%m%d_%H%M%S')}"
        project_root = get_project_root()
        self._record_dir = str(project_root / "record" / dir_name)
        os.makedirs(self._record_dir, exist_ok=True)

        # 初始化状态
        self._start_time = time.time()
        self._start_time_iso = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        self._steps = []
        self._step_counter = 0
        self._pending_capture = None
        self._stop_event.clear()
        self._classifier = EventClassifier(
            scroll_merge_interval_ms=rec_config.scroll_merge_interval_ms
        )

        # 启动 Hook
        hook_manager.start(filter_fn=self._should_filter_event)

        # 启动事件处理线程
        self._processing_thread = threading.Thread(
            target=self._processing_loop, daemon=True, name="RecordProcessor"
        )
        self._processing_thread.start()

        # 启动标记绘制线程
        self._marker_thread = threading.Thread(
            target=self._marker_loop, daemon=True, name="MarkerDrawer"
        )
        self._marker_thread.start()

        # 启动悬浮面板
        self._overlay_thread = threading.Thread(
            target=self._overlay_loop, daemon=True, name="RecordOverlay"
        )
        self._overlay_thread.start()

        self._is_recording = True
        return {"success": True, "message": "Recording started"}

    def stop(self) -> dict:
        """停止录制，冲刷状态，保存 step.json"""
        if not self._is_recording:
            return {"success": False, "message": "Not recording"}

        self._is_recording = False
        self._stop_event.set()

        # 停止 Hook
        hook_manager.stop()

        # 冲刷分类器
        if self._classifier:
            pending_steps = self._classifier.flush()
            for step in pending_steps:
                self._finalize_step(step)

        # 等待线程结束
        if self._processing_thread:
            self._processing_thread.join(timeout=3.0)
        if self._marker_thread:
            self._marker_thread.join(timeout=5.0)

        # 关闭悬浮面板
        self._close_overlay()

        # 保存 step.json
        end_time_iso = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        duration_ms = int((time.time() - self._start_time) * 1000)

        from app.services.config_service import config_service
        hotkey = config_service.get().recording.hotkey

        meta = RecordingMeta(
            start_time=self._start_time_iso,
            end_time=end_time_iso,
            duration_ms=duration_ms,
            total_steps=self._step_counter,
            hotkey=hotkey,
            steps=self._steps,
        )
        meta_path = os.path.join(self._record_dir, "step.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta.model_dump(), f, indent=2, ensure_ascii=False)

        # 通知 Rust 侧更新托盘图标和菜单（浮窗停止、API 停止统一走这里）
        self._notify_recording_stopped()

        return {
            "success": True,
            "record_dir": self._record_dir,
            "total_steps": self._step_counter,
            "duration_ms": duration_ms,
        }

    # ================================================================
    # 事件处理线程
    # ================================================================

    def _processing_loop(self):
        """事件处理主循环"""
        import logging
        logger = logging.getLogger(__name__)

        while not self._stop_event.is_set():
            try:
                event = hook_manager.get_event(timeout=0.01)
                if event is None:
                    # 检查超时（时间基准必须与 Hook 一致：相对录制启动时间的微秒数）
                    now_us = int((time.time() - self._start_time) * 1_000_000)
                    if self._classifier:
                        timed_out = self._classifier.check_timeouts(now_us)
                        for step in timed_out:
                            self._finalize_step(step)
                    continue

                # DOWN 时预截图（窗口一定还在，在分类之前执行）
                self._maybe_pre_capture(event)

                if self._classifier:
                    step = self._classifier.feed(event)
                    if step:
                        self._finalize_step(step)
            except Exception:
                logger.exception("[RecordProcessor] 处理事件异常")

    # ================================================================
    # DOWN 预截图
    # ================================================================

    def _maybe_pre_capture(self, event):
        """DOWN 事件时预截图（窗口一定还在，分类器尚未产出 step）

        鼠标 DOWN：截取点击位置的窗口
        键盘 DOWN：仅功能键和组合键时截取前台窗口
        可打印字符和修饰键不触发预截图
        """
        from app.models.recording import HookEventType

        if event.event_type == HookEventType.LBUTTONDOWN:
            self._pending_capture = self._pre_capture_screenshot(
                screen_x=event.screen_x, screen_y=event.screen_y
            )
            return

        if event.event_type == HookEventType.RBUTTONDOWN:
            self._pending_capture = self._pre_capture_screenshot(
                screen_x=event.screen_x, screen_y=event.screen_y
            )
            return

        if event.event_type == HookEventType.KEYDOWN:
            vk = event.vk_code

            # 修饰键单独按下 → 不截图
            if vk in MODIFIER_VKS:
                return

            # 功能键（Enter/Escape/F1-F12 等）→ 预截图
            if vk in FUNCTION_KEY_VKS:
                self._pending_capture = self._pre_capture_screenshot()
                return

            # 有修饰键按住 → 组合键（如 Ctrl+S），预截图
            if self._classifier and self._classifier._held_modifiers:
                self._pending_capture = self._pre_capture_screenshot()
                return

            # 可打印字符（无修饰键）→ 不截图，input_text 窗口稳定

    def _pre_capture_screenshot(self, screen_x=None, screen_y=None):
        """预截图：在屏幕坐标处或前台窗口截图

        策略与 _do_capture 一致：先截子窗口，失败则截主窗口。
        自身进程和桌面进程 → 桌面截图。
        """
        try:
            import win32gui
            import win32process

            # 确定目标窗口
            if screen_x is not None and screen_y is not None:
                hwnd = win32gui.WindowFromPoint((screen_x, screen_y))
            else:
                hwnd = win32gui.GetForegroundWindow()

            if not hwnd:
                return None

            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            # 自身进程 → 桌面截图
            if pid == os.getpid():
                if screen_x is not None:
                    return self._capture_desktop_at(screen_x, screen_y)
                return None

            # 桌面级进程 → 桌面截图
            from app.services.process_service import process_service
            proc_name = process_service._get_process_name_impl(pid) or ""
            if proc_name.lower() in self.DESKTOP_PROCESSES:
                if screen_x is not None:
                    return self._capture_desktop_at(screen_x, screen_y)
                return None

            # 窗口截图：两层模型（先子窗口，后主窗口）
            main_hwnd = self._get_toplevel_owner(hwnd)
            child_hwnd = self._find_direct_child(hwnd, main_hwnd)

            from app.platform.windows.capture import windows_capture
            if child_hwnd:
                result = windows_capture.capture(child_hwnd)
                if result.success and result.image:
                    return result.image
            if main_hwnd and main_hwnd != child_hwnd:
                result = windows_capture.capture(main_hwnd)
                if result.success and result.image:
                    return result.image
        except Exception:
            pass
        return None

    def _capture_desktop_at(self, screen_x: int, screen_y: int):
        """桌面级预截图"""
        try:
            mon_idx = self._get_monitor_at_point(screen_x, screen_y)
            from app.platform.windows.desktop_capture import capture_monitor
            return capture_monitor(mon_idx)
        except Exception:
            return None

    def _finalize_step(self, step: RecordStep):
        """完成一步：识别进程→转换坐标→截图→入标记队列→记录"""
        # 1. 识别进程
        process_info = self._identify_process(step)
        has_process = process_info is not None

        # 1.5 window_title 为空时统一用主窗口（子窗口是无标题控件区域）
        #     这样坐标计算和截图都基于主窗口，避免子窗口不包含标题栏等区域
        if process_info and not process_info.get("window_title", "").strip():
            main_hwnd = process_info.get("main_window_id")
            if main_hwnd and main_hwnd != process_info["window_id"]:
                process_info["window_id"] = main_hwnd
                process_info["window_title"] = process_info.get("main_window_title", "")

        # 2. 解析动作名
        resolved_action = EventClassifier.resolve_action(step.action, has_process)
        step.action = resolved_action

        # 3. 构建批量兼容的参数
        batch_params = self._build_batch_params(step, process_info)

        # 4. 转换坐标（屏幕像素→百分比）
        self._convert_coordinates(step, batch_params, process_info)

        # 4.5 采集窗口/桌面分辨率和 DPI 缩放率（在清理 _raw_* 之前，需要原始屏幕坐标）
        step.window_info = self._collect_window_info(step, process_info)

        # 5. 清理内部字段（_raw_* 不写入产物）
        step.params = {k: v for k, v in batch_params.items() if not k.startswith('_raw_')}

        # 6. 设置进程信息
        if process_info:
            step.process = process_info
        step.timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        # 7. 截图
        self._capture_screenshot(step, process_info)

        # 8. 记录步骤
        with self._lock:
            self._step_counter += 1
            step.step_index = self._step_counter
            self._steps.append(step.to_dict())

        # 9. 入标记绘制队列（role: "main" / "start" / "end"）
        if step._image is not None:
            self._screenshot_queue.put((step, step._image, "main"), block=False)
        if step._start_image is not None:
            self._screenshot_queue.put((step, step._start_image, "start"), block=False)
        if step._end_image is not None:
            self._screenshot_queue.put((step, step._end_image, "end"), block=False)

        # 10. 更新悬浮面板
        self._update_overlay()

    # ================================================================
    # 进程识别
    # ================================================================

    # 桌面级系统进程 → 走桌面操作路径（desktop_click 等），不返回窗口信息
    DESKTOP_PROCESSES = {"explorer.exe"}

    def _identify_process(self, step: RecordStep) -> Optional[Dict]:
        """识别操作目标进程"""
        try:
            import win32gui
            import win32process
        except ImportError:
            return None

        # 获取原始屏幕坐标
        sx = step.params.get('_raw_screen_x', 0)
        sy = step.params.get('_raw_screen_y', 0)

        try:
            # 鼠标操作用 WindowFromPoint
            if '_raw_screen_x' in step.params:
                hwnd = win32gui.WindowFromPoint((sx, sy))
            else:
                # 键盘操作用 GetForegroundWindow
                hwnd = win32gui.GetForegroundWindow()

            if not hwnd:
                return None

            _, pid = win32process.GetWindowThreadProcessId(hwnd)

            # 过滤自身进程
            own_pid = os.getpid()
            if pid == own_pid:
                return None

            # 获取进程名（统一使用 process_service，与 get_windows_list API 一致）
            # 获取不到时置空，方便 AI 通过窗口标题判断，不使用 pid_xxx 避免误导
            from app.services.process_service import process_service
            proc_name = process_service._get_process_name_impl(pid) or ""

            # 桌面级系统进程（explorer.exe 等）走桌面操作路径
            if proc_name.lower() in self.DESKTOP_PROCESSES:
                return None

            # 获取主窗口（顶层窗口，走完整 parent 链）
            main_hwnd = self._get_toplevel_owner(hwnd)

            # 获取直接子窗口（顶层窗口的直接子级，跳过组件级窗口）
            child_hwnd = self._find_direct_child(hwnd, main_hwnd)

            # 窗口标题
            child_title = win32gui.GetWindowText(child_hwnd) or ""
            main_title = win32gui.GetWindowText(main_hwnd) or "" if main_hwnd != child_hwnd else child_title

            return {
                "process_id": pid,
                "process_name": proc_name,
                "window_id": child_hwnd if isinstance(child_hwnd, int) else int(child_hwnd),
                "window_title": child_title,
                "main_window_id": main_hwnd if isinstance(main_hwnd, int) else int(main_hwnd),
                "main_window_title": main_title,
            }
        except Exception:
            return None

    @staticmethod
    def _get_toplevel_owner(hwnd) -> int:
        """向上查找顶层窗口（使用 GetAncestor GA_ROOT 走完整个 parent 链）"""
        import ctypes
        try:
            user32 = ctypes.windll.user32
            root = user32.GetAncestor(hwnd, 2)  # GA_ROOT = 2
            if root:
                return root
        except Exception:
            pass
        # fallback: 手动走 parent 链
        import win32gui
        current = hwnd
        while True:
            parent = win32gui.GetParent(current)
            if not parent:
                break
            current = parent
        return current

    @staticmethod
    def _find_direct_child(deep_hwnd, root_hwnd) -> int:
        """从深层子窗口向上找到 root 的直接子窗口（两层模型）

        WindowFromPoint 返回最深层子控件（如按钮、文本框），
        本方法沿 parent 链向上走，返回 root 的直接子窗口。
        例如：root → 内容面板 → 列表 → 按钮控件，返回「内容面板」。
        """
        if deep_hwnd == root_hwnd:
            return root_hwnd

        import win32gui
        current = deep_hwnd
        while current:
            parent = win32gui.GetParent(current)
            if not parent or parent == root_hwnd:
                return current
            current = parent
        return deep_hwnd  # fallback: 无法找到中间层

    # ================================================================
    # 坐标转换
    # ================================================================

    def _build_batch_params(self, step: RecordStep, process_info: Optional[Dict]) -> Dict:
        """构建 batch 兼容的 params"""
        params = dict(step.params)

        if process_info:
            params["window_id"] = process_info["window_id"]
            if process_info.get("main_window_id"):
                params["main_window_id"] = process_info["main_window_id"]
        else:
            # 桌面操作：需要确定 monitor_index
            sx = params.get('_raw_screen_x', 0)
            sy = params.get('_raw_screen_y', 0)
            monitor_index = self._get_monitor_at_point(sx, sy)
            params["monitor_index"] = monitor_index

            # drag 的终点也需要 monitor_index
            if '_raw_end_x' in params:
                ex = params['_raw_end_x']
                ey = params['_raw_end_y']
                end_monitor = self._get_monitor_at_point(ex, ey)
                if end_monitor != monitor_index:
                    params["end_monitor_index"] = end_monitor

        return params

    def _convert_coordinates(self, step: RecordStep, params: Dict,
                             process_info: Optional[Dict]):
        """将原始屏幕像素坐标转换为百分比坐标

        统一使用 GetWindowRect 计算百分比，与截图（capture 用 WindowRect）
        和 Skill API（restore_window_and_calc_coords 用 WindowRect）保持一致。
        公式：pct = (screen_coord - window_left_top) / window_size * 100
        """
        try:
            import win32gui
        except ImportError:
            return

        # 单坐标操作（click/right_click/long_press/scroll）
        if '_raw_screen_x' in params:
            sx, sy = params['_raw_screen_x'], params['_raw_screen_y']
            if process_info:
                hwnd = process_info["window_id"]
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    w = rect[2] - rect[0]
                    h = rect[3] - rect[1]
                    if w > 0 and h > 0:
                        params["x"] = round((sx - rect[0]) / w * 100, 1)
                        params["y"] = round((sy - rect[1]) / h * 100, 1)
                except Exception:
                    pass
            else:
                # 桌面操作
                mon_idx = params.get("monitor_index", 0)
                monitors = self._get_monitor_list()
                if mon_idx < len(monitors):
                    mon = monitors[mon_idx]
                    params["x"] = round((sx - mon["left"]) / mon["width"] * 100, 1)
                    params["y"] = round((sy - mon["top"]) / mon["height"] * 100, 1)

        # 双坐标操作（drag/swipe）
        if '_raw_start_x' in params:
            ssx, ssy = params['_raw_start_x'], params['_raw_start_y']
            esx, esy = params['_raw_end_x'], params['_raw_end_y']

            if process_info:
                hwnd = process_info["window_id"]
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    w = rect[2] - rect[0]
                    h = rect[3] - rect[1]
                    if w > 0 and h > 0:
                        params["start_x"] = round((ssx - rect[0]) / w * 100, 1)
                        params["start_y"] = round((ssy - rect[1]) / h * 100, 1)
                except Exception:
                    pass

                # 终点可能在不同窗口（跨窗口拖拽）
                target_process = self._identify_target_process(esx, esy, process_info)
                if target_process and target_process["window_id"] != process_info["window_id"]:
                    step.target_process = target_process
                    params["target_window_id"] = target_process["window_id"]
                    if target_process.get("main_window_id"):
                        params["target_main_window_id"] = target_process["main_window_id"]
                    # 终点坐标相对于目标窗口的 WindowRect
                    thwnd = target_process["window_id"]
                    try:
                        trect = win32gui.GetWindowRect(thwnd)
                        tw = trect[2] - trect[0]
                        th = trect[3] - trect[1]
                        if tw > 0 and th > 0:
                            params["end_x"] = round((esx - trect[0]) / tw * 100, 1)
                            params["end_y"] = round((esy - trect[1]) / th * 100, 1)
                    except Exception:
                        pass
                else:
                    # 同窗口终点
                    try:
                        params["end_x"] = round((esx - rect[0]) / w * 100, 1)
                        params["end_y"] = round((esy - rect[1]) / h * 100, 1)
                    except Exception:
                        pass
            else:
                # 桌面操作
                mon_idx = params.get("monitor_index", 0)
                monitors = self._get_monitor_list()
                if mon_idx < len(monitors):
                    mon = monitors[mon_idx]
                    params["start_x"] = round((ssx - mon["left"]) / mon["width"] * 100, 1)
                    params["start_y"] = round((ssy - mon["top"]) / mon["height"] * 100, 1)
                end_mon_idx = params.get("end_monitor_index", mon_idx)
                if end_mon_idx < len(monitors):
                    emon = monitors[end_mon_idx]
                    params["end_x"] = round((esx - emon["left"]) / emon["width"] * 100, 1)
                    params["end_y"] = round((esy - emon["top"]) / emon["height"] * 100, 1)

    def _identify_target_process(self, screen_x: int, screen_y: int,
                                 source_process: Dict) -> Optional[Dict]:
        """识别终点坐标的进程（跨窗口拖拽）"""
        try:
            import win32gui
            import win32process
            hwnd = win32gui.WindowFromPoint((screen_x, screen_y))
            if not hwnd:
                return None
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == os.getpid():
                return None

            # 获取进程名（获取不到时置空）
            from app.services.process_service import process_service
            proc_name = process_service._get_process_name_impl(pid) or ""

            # 桌面级系统进程走桌面路径，不返回窗口信息
            if proc_name.lower() in self.DESKTOP_PROCESSES:
                return None

            # 获取主窗口和直接子窗口（两层模型）
            main_hwnd = self._get_toplevel_owner(hwnd)
            child_hwnd = self._find_direct_child(hwnd, main_hwnd)
            child_title = win32gui.GetWindowText(child_hwnd) or ""
            main_title = win32gui.GetWindowText(main_hwnd) or "" if main_hwnd != child_hwnd else child_title

            return {
                "process_id": pid,
                "process_name": proc_name,
                "window_id": child_hwnd if isinstance(child_hwnd, int) else int(child_hwnd),
                "window_title": child_title,
                "main_window_id": main_hwnd if isinstance(main_hwnd, int) else int(main_hwnd),
                "main_window_title": main_title,
            }
        except Exception:
            return None

    # ================================================================
    # 截图管线
    # ================================================================

    def _capture_screenshot(self, step: RecordStep, process_info: Optional[Dict] = None):
        """截图：先正常截图（基于 _identify_process 识别的正确窗口），
        失败时 fallback 到 DOWN 时预截图（窗口可能已关闭的兜底）"""
        action = step.action
        params = step.params

        # scroll 不截图
        if action in ("scroll", "desktop_scroll"):
            step.screenshot = None
            self._pending_capture = None  # 清理
            return

        # 消费预截图（如果有的话）
        pre_capture = self._pending_capture
        self._pending_capture = None

        # drag/swipe 有两张截图
        is_drag = action in ("drag", "swipe", "desktop_drag", "desktop_swipe")

        if is_drag:
            # 起点截图：先正常截图，失败则用预截图
            step._start_image = self._do_capture(params, "_raw_start_x", "_raw_start_y")
            if not step._start_image and pre_capture:
                step._start_image = pre_capture
            # 终点截图：用当前逻辑（终点窗口通常是稳定的）
            step._end_image = self._do_capture(params, "_raw_end_x", "_raw_end_y")
        else:
            # 单截图操作：先正常截图，失败则用预截图
            step._image = self._do_capture(params, "_raw_screen_x", "_raw_screen_y")
            if not step._image and pre_capture:
                step._image = pre_capture

    def _do_capture(self, params: Dict, x_key: str, y_key: str):
        """执行截图 — 截取 window_id，失败时 fallback 到 main_window_id"""
        try:
            if params.get("window_id") or params.get("main_window_id"):
                from app.platform.windows.capture import windows_capture
                child_hwnd = params.get("window_id")
                main_hwnd = params.get("main_window_id")

                # 优先截取 window_id（_finalize_step 已归一化：空标题时 window_id=main_window_id）
                if child_hwnd:
                    result = windows_capture.capture(child_hwnd)
                    if result.success and result.image:
                        return result.image

                # 截取失败时 fallback 到 main_window_id
                if main_hwnd and main_hwnd != child_hwnd:
                    result = windows_capture.capture(main_hwnd)
                    if result.success and result.image:
                        return result.image
            elif params.get("monitor_index") is not None:
                # 桌面截图
                from app.platform.windows.desktop_capture import capture_monitor
                return capture_monitor(params["monitor_index"])
        except Exception:
            pass
        return None

    # ================================================================
    # 标记绘制线程
    # ================================================================

    def _marker_loop(self):
        """后台标记绘制：原图 → 缩放 → 绘制标记 → 保存"""
        import logging
        logger = logging.getLogger(__name__)

        while not self._stop_event.is_set() or not self._screenshot_queue.empty():
            try:
                step, image, role = self._screenshot_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if image is None:
                continue

            try:
                # 获取缩放和标记配置（复用 screenshot 配置）
                max_width = self._get_compress_config()["max_image_width"]
                marker_cfg = self._get_marker_config()

                # 先缩放（控制像素分辨率，降低 AI token 消耗）
                from app.utils.image import compress_image
                image = compress_image(image, max_width=max_width)

                # 绘制标记（在缩放后的图上，标记比例正确）
                is_start = role == "start"
                coords = self._get_marker_coords(step, is_start)
                if coords:
                    image = self._draw_markers(image, coords, marker_cfg)

                # 生成文件名
                step_idx = step.step_index
                if role == "start":
                    filename = f"step_{step_idx:04d}_start.png"
                elif role == "end":
                    filename = f"step_{step_idx:04d}_end.png"
                else:
                    filename = f"step_{step_idx:04d}.png"

                filepath = os.path.join(self._record_dir, filename)
                image.save(filepath, "PNG")

                # 更新步骤的 screenshot 字段
                if role == "start":
                    step.screenshot = {"start": filename}
                elif role == "end":
                    if isinstance(step.screenshot, dict) and "start" in step.screenshot:
                        step.screenshot["end"] = filename
                    else:
                        step.screenshot = {"end": filename}
                else:
                    step.screenshot = filename

                # 同步到 self._steps
                with self._lock:
                    if step.step_index <= len(self._steps):
                        self._steps[step.step_index - 1] = step.to_dict()
            except Exception:
                logger.exception("[MarkerDrawer] 处理截图异常")

    def _get_marker_config(self) -> Dict:
        """获取标记配置（复用 screenshot 的 default_marker_* 参数）"""
        try:
            from app.services.config_service import config_service
            ss = config_service.get().screenshot
            return {
                "ring_radius": ss.default_marker_ring_radius,
                "ring_line_width": ss.default_marker_ring_line_width,
                "ring_color": ss.default_marker_ring_color,
                "dot_radius": ss.default_marker_dot_radius,
                "dot_color": ss.default_marker_dot_color,
            }
        except Exception:
            return {"ring_radius": 12, "ring_line_width": 2, "ring_color": "#FF0000",
                    "dot_radius": 3, "dot_color": "#FF0000"}

    def _get_compress_config(self) -> Dict:
        """获取缩放配置（复用 screenshot 的 max_image_width）"""
        try:
            from app.services.config_service import config_service
            ss = config_service.get().screenshot
            return {"max_image_width": ss.max_image_width}
        except Exception:
            return {"max_image_width": 1600}

    def _get_marker_coords(self, step: RecordStep, is_start: bool) -> List[Dict]:
        """获取需要在截图上标记的坐标"""
        params = step.params
        action = step.action

        if action in ("press_key", "desktop_press_key"):
            return []  # 无坐标
        if action in ("scroll", "desktop_scroll"):
            return []  # 不截图

        if action in ("drag", "swipe", "desktop_drag", "desktop_swipe"):
            if is_start:
                x = params.get("start_x")
                y = params.get("start_y")
            else:
                x = params.get("end_x")
                y = params.get("end_y")
        else:
            x = params.get("x")
            y = params.get("y")

        if x is not None and y is not None:
            return [{"x": x, "y": y}]
        return []

    @staticmethod
    def _draw_markers(image, coords: List[Dict], cfg: Dict):
        """在截图上绘制标记点"""
        from PIL import Image, ImageDraw

        img = image.convert("RGBA")
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        w, h = img.size

        r = cfg.get("ring_radius", 12)
        lw = cfg.get("ring_line_width", 2)
        color = cfg.get("ring_color", "#FF0000")
        dr = cfg.get("dot_radius", 3)
        dot_color = cfg.get("dot_color", "#FF0000")

        for coord in coords:
            px = int(coord["x"] / 100 * w)
            py = int(coord["y"] / 100 * h)
            # 外圈空心圆
            draw.ellipse(
                [px - r, py - r, px + r, py + r],
                outline=color, width=lw,
            )
            # 中心实心圆
            draw.ellipse(
                [px - dr, py - dr, px + dr, py + dr],
                fill=dot_color,
            )

        return Image.alpha_composite(img, overlay).convert("RGB")

    # ================================================================
    # 悬浮面板（Win32 原生）
    # ================================================================

    def _overlay_loop(self):
        """悬浮录制面板线程"""
        import ctypes
        import ctypes.wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # ---- 64 位兼容：设置所有用到的 Win32 函数原型 ----
        LRESULT = ctypes.wintypes.LPARAM  # LRESULT = LONG_PTR，与 LPARAM 同宽度
        HWND = ctypes.wintypes.HWND
        UINT = ctypes.wintypes.UINT
        WPARAM = ctypes.wintypes.WPARAM
        LPARAM = ctypes.wintypes.LPARAM

        user32.DefWindowProcW.argtypes = [HWND, UINT, WPARAM, LPARAM]
        user32.DefWindowProcW.restype = LRESULT

        user32.InvalidateRect.argtypes = [HWND, ctypes.c_void_p, ctypes.wintypes.BOOL]
        user32.InvalidateRect.restype = ctypes.wintypes.BOOL

        user32.PostQuitMessage.argtypes = [ctypes.c_int]
        user32.PostQuitMessage.restype = None

        user32.BeginPaint.argtypes = [HWND, ctypes.c_void_p]
        user32.BeginPaint.restype = ctypes.c_void_p  # HDC

        user32.EndPaint.argtypes = [HWND, ctypes.c_void_p]
        user32.EndPaint.restype = ctypes.c_int

        user32.GetClientRect.argtypes = [HWND, ctypes.c_void_p]
        user32.GetClientRect.restype = ctypes.wintypes.BOOL

        user32.SetLayeredWindowAttributes.argtypes = [HWND, ctypes.wintypes.COLORREF, ctypes.c_ubyte, ctypes.wintypes.DWORD]
        user32.SetLayeredWindowAttributes.restype = ctypes.wintypes.BOOL

        user32.DestroyWindow.argtypes = [HWND]
        user32.DestroyWindow.restype = ctypes.wintypes.BOOL

        user32.UnregisterClassW.argtypes = [ctypes.c_wchar_p, ctypes.wintypes.HINSTANCE]
        user32.UnregisterClassW.restype = ctypes.wintypes.BOOL

        gdi32 = ctypes.windll.gdi32
        gdi32.CreateSolidBrush.argtypes = [ctypes.wintypes.COLORREF]
        gdi32.CreateSolidBrush.restype = ctypes.c_void_p  # HBRUSH

        # FillRect 在 user32.dll，不在 gdi32.dll
        user32.FillRect.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        user32.FillRect.restype = ctypes.c_int

        gdi32.SelectObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        gdi32.SelectObject.restype = ctypes.c_void_p

        gdi32.Ellipse.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        gdi32.Ellipse.restype = ctypes.wintypes.BOOL

        gdi32.Rectangle.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        gdi32.Rectangle.restype = ctypes.wintypes.BOOL

        gdi32.CreateFontW.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                       ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                                       ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_wchar_p]
        gdi32.CreateFontW.restype = ctypes.c_void_p  # HFONT

        gdi32.SetTextColor.argtypes = [ctypes.c_void_p, ctypes.wintypes.COLORREF]
        gdi32.SetTextColor.restype = ctypes.wintypes.COLORREF

        gdi32.SetBkMode.argtypes = [ctypes.c_void_p, ctypes.c_int]
        gdi32.SetBkMode.restype = ctypes.c_int

        gdi32.TextOutW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int]
        gdi32.TextOutW.restype = ctypes.wintypes.BOOL

        gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
        gdi32.DeleteObject.restype = ctypes.wintypes.BOOL

        WNDCLASS_NAME = "ScreenClawRecordPanel"
        WIDTH, HEIGHT = 240, 40

        # WNDPROC 类型（返回 LRESULT，指针宽度）
        WNDPROC = ctypes.CFUNCTYPE(
            ctypes.wintypes.LPARAM, ctypes.wintypes.HWND, ctypes.wintypes.UINT,
            ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
        )

        # WNDCLASSW 结构体（Python 3.13 移除了 ctypes.wintypes.WNDCLASSW）
        class WNDCLASSW(ctypes.Structure):
            _fields_ = [
                ("style", ctypes.c_uint),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", ctypes.wintypes.HINSTANCE),
                ("hIcon", ctypes.wintypes.HICON),
                ("hCursor", ctypes.wintypes.HANDLE),
                ("hbrBackground", ctypes.wintypes.HBRUSH),
                ("lpszMenuName", ctypes.c_wchar_p),
                ("lpszClassName", ctypes.c_wchar_p),
            ]

        # 保持引用
        self._overlay_wndproc = WNDPROC(self._overlay_wnd_proc)

        wnd_class = WNDCLASSW()
        wnd_class.lpszClassName = WNDCLASS_NAME
        wnd_class.lpfnWndProc = self._overlay_wndproc
        wnd_class.hInstance = kernel32.GetModuleHandleW(None)
        wnd_class.hCursor = user32.LoadCursorW(None, ctypes.c_void_p(32512))  # IDC_ARROW
        user32.RegisterClassW(ctypes.byref(wnd_class))

        # 计算位置（中间底部，任务栏上方）
        work_area = ctypes.wintypes.RECT()
        user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(work_area), 0)  # SPI_GETWORKAREA
        wa_w = work_area.right - work_area.left
        x = (wa_w - WIDTH) // 2 + work_area.left
        y = work_area.bottom - HEIGHT - 10  # 距任务栏 10px

        # 创建窗口
        WS_EX_TOPMOST = 0x00000008
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_LAYERED = 0x00080000
        WS_POPUP = 0x80000000
        WS_VISIBLE = 0x10000000
        LWA_ALPHA = 0x02

        self._overlay_hwnd = user32.CreateWindowExW(
            WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_LAYERED,
            WNDCLASS_NAME, "ScreenClaw Recording",
            WS_POPUP | WS_VISIBLE,
            x, y, WIDTH, HEIGHT,
            None, None, wnd_class.hInstance, None,
        )

        # 设置半透明
        user32.SetLayeredWindowAttributes(self._overlay_hwnd, 0, 200, LWA_ALPHA)

        # 设置定时器（每秒重绘）
        user32.SetTimer(self._overlay_hwnd, 1, 1000, None)

        # 消息循环
        msg = ctypes.wintypes.MSG()
        while not self._stop_event.is_set():
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == 0 or ret == -1:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        # 清理
        if self._overlay_hwnd:
            user32.DestroyWindow(self._overlay_hwnd)
            self._overlay_hwnd = None
        user32.UnregisterClassW(WNDCLASS_NAME, wnd_class.hInstance)

    def _overlay_wnd_proc(self, hwnd, msg, wparam, lparam):
        """悬浮面板窗口过程"""
        import ctypes
        import ctypes.wintypes

        user32 = ctypes.windll.user32

        WM_PAINT = 0x000F
        WM_TIMER = 0x0113
        WM_LBUTTONUP = 0x0202
        WM_NCHITTEST = 0x0084
        WM_DESTROY = 0x0002
        HTCAPTION = 2

        if msg == WM_PAINT or msg == WM_TIMER:
            self._overlay_paint(hwnd)
            if msg == WM_TIMER:
                user32.InvalidateRect(hwnd, None, True)
            return 0

        elif msg == WM_LBUTTONUP:
            # 检查是否点击了停止按钮区域（右侧 40px）
            import ctypes.wintypes
            x = ctypes.c_short(lparam & 0xFFFF).value
            if x >= 200:  # 停止按钮区域
                # 异步停止录制
                threading.Thread(target=self.stop, daemon=True).start()
            return 0

        elif msg == WM_NCHITTEST:
            # lParam = MAKELONG(screen_x, screen_y)，需转为窗口客户区坐标
            screen_x = ctypes.c_short(lparam & 0xFFFF).value
            screen_y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
            win_rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(win_rect))
            client_x = screen_x - win_rect.left
            # 停止按钮区域（右侧 40px）→ 返回 HTCLIENT 以接收 WM_LBUTTONUP
            if client_x >= 200:
                return 1  # HTCLIENT
            return HTCAPTION  # 其余区域可拖动

        elif msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _overlay_paint(self, hwnd):
        """GDI 绘制悬浮面板"""
        import ctypes
        import ctypes.wintypes

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        # PAINTSTRUCT 不是 ctypes.wintypes 内置类型，手动定义
        class PAINTSTRUCT(ctypes.Structure):
            _fields_ = [
                ('hdc', ctypes.c_void_p),
                ('fErase', ctypes.wintypes.BOOL),
                ('rcPaint', ctypes.wintypes.RECT),
                ('fRestore', ctypes.wintypes.BOOL),
                ('fIncUpdate', ctypes.wintypes.BOOL),
                ('rgbReserved', ctypes.c_byte * 32),
            ]

        WM_PAINT = 0x000F
        PS = PAINTSTRUCT()

        hdc = user32.BeginPaint(hwnd, ctypes.byref(PS))

        # 背景
        rect = ctypes.wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        bg_brush = gdi32.CreateSolidBrush(0x001A1A1A)  # #1A1A1A (BGR)
        user32.FillRect(hdc, ctypes.byref(rect), bg_brush)

        # REC 指示器
        rec_brush = gdi32.CreateSolidBrush(0x000000FF)  # Red
        gdi32.SelectObject(hdc, rec_brush)
        gdi32.Ellipse(hdc, 10, 13, 20, 23)

        # 文字
        font = gdi32.CreateFontW(
            -14, 0, 0, 0, 400, 0, 0, 0,
            0x01, 0, 0, 0, 0x31,  # DEFAULT_CHARSET, FIXED_PITCH
            "Consolas",
        )
        gdi32.SelectObject(hdc, font)
        gdi32.SetTextColor(hdc, 0x00FFFFFF)  # White
        gdi32.SetBkMode(hdc, 1)  # TRANSPARENT

        # 绘制时间
        if self._is_recording and self._start_time:
            elapsed = int(time.time() - self._start_time)
            m, s = divmod(elapsed, 60)
            h, m = divmod(m, 60)
            time_text = f"{h:02d}:{m:02d}:{s:02d}"
        else:
            time_text = "00:00:00"

        gdi32.TextOutW(hdc, 26, 12, time_text, len(time_text))

        # 步骤计数
        step_text = f"{self._step_counter} 步"
        gdi32.TextOutW(hdc, 120, 12, step_text, len(step_text))

        # 停止按钮
        stop_brush = gdi32.CreateSolidBrush(0x000000FF)  # Red
        gdi32.SelectObject(hdc, stop_brush)
        gdi32.Rectangle(hdc, 210, 10, 228, 28)

        # 清理
        gdi32.DeleteObject(bg_brush)
        gdi32.DeleteObject(rec_brush)
        gdi32.DeleteObject(font)
        gdi32.DeleteObject(stop_brush)

        user32.EndPaint(hwnd, ctypes.byref(PS))

    def _close_overlay(self):
        """关闭悬浮面板"""
        if self._overlay_hwnd:
            try:
                ctypes.windll.user32.PostMessageW(self._overlay_hwnd, 0x0010, 0, 0)  # WM_CLOSE
            except Exception:
                pass

    def _update_overlay(self):
        """触发悬浮面板重绘"""
        if self._overlay_hwnd:
            try:
                import ctypes
                ctypes.windll.user32.InvalidateRect(self._overlay_hwnd, None, True)
            except Exception:
                pass

    # ================================================================
    # 工具方法
    # ================================================================

    def _should_filter_event(self, screen_x: int, screen_y: int) -> bool:
        """过滤 screenclaw 自身窗口"""
        return False  # hook_manager 内部已处理

    def _collect_window_info(self, step: RecordStep,
                             process_info: Optional[Dict]) -> Optional[Dict]:
        """采集步骤的窗口/桌面分辨率和 DPI 缩放率

        窗口操作：GetWindowRect 物理尺寸 + GetDpiForMonitor 缩放率
        桌面操作：GetMonitorInfoW 物理尺寸 + GetDpiForMonitor 缩放率

        统一使用 GetDpiForMonitor(hmon, MDT_EFFECTIVE_DPI) 获取 per-monitor DPI：
          100% → 96 → scale 1.0
          150% → 144 → scale 1.5
          200% → 192 → scale 2.0
        """
        import ctypes
        import ctypes.wintypes

        try:
            user32 = ctypes.windll.user32
            shcore = ctypes.windll.shcore

            if process_info:
                # ---- 窗口操作 ----
                hwnd = process_info["window_id"]

                # 窗口物理尺寸（进程 DPI-aware，GetWindowRect 返回物理坐标）
                import win32gui
                rect = win32gui.GetWindowRect(hwnd)
                source_width = rect[2] - rect[0]
                source_height = rect[3] - rect[1]

                # 窗口所在显示器
                hmon = user32.MonitorFromWindow(hwnd, 1)  # MONITOR_DEFAULTTOPRIMARY
            else:
                # ---- 桌面操作 ----
                # 用起始坐标定位显示器（drag 用 start，其他用 screen）
                sx = step.params.get('_raw_start_x',
                                     step.params.get('_raw_screen_x', 0))
                sy = step.params.get('_raw_start_y',
                                     step.params.get('_raw_screen_y', 0))

                # MonitorFromPoint → HMONITOR
                class POINT(ctypes.Structure):
                    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

                user32.MonitorFromPoint.argtypes = [POINT, ctypes.c_uint]
                user32.MonitorFromPoint.restype = ctypes.c_void_p
                hmon = user32.MonitorFromPoint(POINT(sx, sy), 1)

                if hmon:
                    # GetMonitorInfoW → 显示器物理矩形（DPI-aware 进程直接返回物理坐标）
                    class MONITORINFOEXW(ctypes.Structure):
                        _fields_ = [
                            ("cbSize", ctypes.c_uint),
                            ("rcMonitor", ctypes.wintypes.RECT),
                            ("rcWork", ctypes.wintypes.RECT),
                            ("dwFlags", ctypes.c_uint),
                            ("szDevice", ctypes.c_wchar * 32),
                        ]

                    mi = MONITORINFOEXW()
                    mi.cbSize = ctypes.sizeof(MONITORINFOEXW)
                    user32.GetMonitorInfoW(ctypes.c_void_p(hmon), ctypes.byref(mi))
                    source_width = mi.rcMonitor.right - mi.rcMonitor.left
                    source_height = mi.rcMonitor.bottom - mi.rcMonitor.top

            if not hmon:
                return None

            # GetDpiForMonitor(hmon, MDT_EFFECTIVE_DPI=0, &dpiX, &dpiY)
            dpi_x = ctypes.c_uint()
            dpi_y = ctypes.c_uint()
            shcore.GetDpiForMonitor(
                ctypes.c_void_p(hmon), 0,
                ctypes.byref(dpi_x), ctypes.byref(dpi_y)
            )
            scale_factor = round(dpi_x.value / 96, 2)

            return {
                "source_width": source_width,
                "source_height": source_height,
                "scale_factor": scale_factor,
            }
        except Exception:
            return None

    def _get_monitor_at_point(self, screen_x: int, screen_y: int) -> int:
        """获取坐标所在显示器索引"""
        monitors = self._get_monitor_list()
        for i, mon in enumerate(monitors):
            if (mon["left"] <= screen_x < mon["left"] + mon["width"] and
                    mon["top"] <= screen_y < mon["top"] + mon["height"]):
                return i
        return 0

    @staticmethod
    def _get_monitor_list() -> List[Dict]:
        """获取显示器列表"""
        try:
            from app.platform.windows.desktop_capture import get_monitors
            return get_monitors()
        except Exception:
            return [{"left": 0, "top": 0,
                     "width": ctypes.windll.user32.GetSystemMetrics(0),
                     "height": ctypes.windll.user32.GetSystemMetrics(1)}]

    def _get_record_dir(self) -> str:
        return self._record_dir or "."

    def _notify_recording_stopped(self):
        """通知 Rust 侧录制已停止（更新托盘图标和菜单）

        Rust 热键线程将线程 ID 写入 data/.hotkey_tid，
        Python 侧通过 PostThreadMessageW(WM_RECORDING_SYNC=0x0403) 通知。
        """
        try:
            import ctypes
            tid_path = get_project_root() / "data" / ".hotkey_tid"
            if tid_path.exists():
                tid = int(tid_path.read_text().strip())
                ctypes.windll.user32.PostThreadMessageW(tid, 0x0403, 0, 0)
        except Exception:
            pass


# 全局单例
recording_service = RecordingService()

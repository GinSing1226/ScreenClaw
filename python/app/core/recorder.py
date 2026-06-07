"""
事件分类器 — 将原始 Hook 事件归纳为有意义的操作步骤

状态机：
  IDLE → LBUTTONDOWN → LEFT_DOWN
  LEFT_DOWN + LBUTTONUP(位移<5px, 时长<300ms) → click
  LEFT_DOWN + LBUTTONUP(位移<5px, 时长≥500ms) → long_press
  LEFT_DOWN + LBUTTONUP(位移≥5px, 时长<300ms) → swipe
  LEFT_DOWN + LBUTTONUP(位移≥5px, 时长≥300ms) → drag
  IDLE → RBUTTONDOWN → RIGHT_DOWN → RBUTTONUP → right_click
  连续 MOUSEWHEEL(同位置, 间隔<500ms) → scroll(合并)
  连续 CHAR/IME_CHAR(间隔<1s) → input_text
  修饰键 + 其他键 KEYUP → press_key

动作名通过 DESKTOP_ACTION_MAP 在输出时转换（有进程信息=窗口级，无=desktop_前缀）
"""
import time
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from app.models.recording import RawHookEvent, HookEventType, RecordStep


# ============================================================
# 动作名映射（窗口级 → 桌面级）
# ============================================================

DESKTOP_ACTION_MAP = {
    "click": "desktop_click",
    "double_click": "desktop_double_click",
    "right_click": "desktop_right_click",
    "long_press": "desktop_long_press",
    "drag": "desktop_drag",
    "swipe": "desktop_swipe",
    "scroll": "desktop_scroll",
    "input_text": "desktop_input_text",
    "press_key": "desktop_press_key",
}

# 修饰键虚拟键码（WH_KEYBOARD_LL 返回左/右具体键码，如 0xA2=VK_LCONTROL）
MODIFIER_VKS = {
    0x10, 0x11, 0x12, 0x5B, 0x5C,    # 通用: Shift, Ctrl, Alt, LWin, RWin
    0xA0, 0xA1,                        # LShift, RShift
    0xA2, 0xA3,                        # LControl, RControl
    0xA4, 0xA5,                        # LMenu, RMenu
}

# 功能键虚拟键码（单独按下应输出 press_key）
FUNCTION_KEY_VKS = set(range(0x70, 0x88))  # F1-F24
FUNCTION_KEY_VKS.update({
    0x08,  # Backspace
    0x09,  # Tab
    0x0D,  # Enter
    0x1B,  # Escape
    0x2E,  # Delete
    0x23,  # End
    0x24,  # Home
    0x21,  # Page Up
    0x22,  # Page Down
    0x25,  # Left
    0x26,  # Up
    0x27,  # Right
    0x28,  # Down
    0x14,  # Caps Lock
    0x90,  # Num Lock
    0x91,  # Scroll Lock
    0x5D,  # Apps (ContextMenu)
})

# 阈值
CLICK_DISTANCE_THRESHOLD = 5      # 像素
CLICK_TIME_THRESHOLD_US = 300_000  # 微秒 (300ms)
LONG_PRESS_TIME_US = 500_000      # 微秒 (500ms)
SWIPE_TIME_THRESHOLD_US = 300_000 # 微秒 (300ms)
SCROLL_MERGE_INTERVAL_US = 500_000  # 微秒 (500ms)
TEXT_INPUT_TIMEOUT_US = 1_000_000   # 微秒 (1s)


# ============================================================
# 内部数据类
# ============================================================

@dataclass
class PendingClick:
    """鼠标按下状态跟踪"""
    button: str = "left"  # "left" or "right"
    start_time_us: int = 0
    start_x: int = 0
    start_y: int = 0


@dataclass
class PendingScroll:
    """累积滚动数据"""
    start_time_us: int = 0
    screen_x: int = 0
    screen_y: int = 0
    total_delta: int = 0
    last_event_us: int = 0


@dataclass
class PendingText:
    """累积文本输入"""
    chars: str = ""
    last_char_time_us: int = 0


# ============================================================
# 分类器
# ============================================================

class EventClassifier:
    """状态机分类器：将原始 Hook 事件流归纳为操作步骤

    feed() 返回分类完成的步骤（RecordStep），包含原始屏幕像素坐标。
    调用方负责：进程识别、坐标转换、截图。

    使用方式：
        step = classifier.feed(event)
        if step:
            # step.action 是窗口级动作名
            # 调用 resolve_action(step.action, has_process) 获取最终动作名
            ...
    """

    def __init__(self, scroll_merge_interval_ms: int = 500):
        self._scroll_merge_interval_us = scroll_merge_interval_ms * 1000

        # 鼠标按下状态
        self._pending_click: Optional[PendingClick] = None

        # 滚动累积
        self._pending_scroll: Optional[PendingScroll] = None

        # 文本累积
        self._pending_text: Optional[PendingText] = None

        # 修饰键追踪
        self._held_modifiers: set = set()

        # 等待非修饰键释放（组合键模式）
        self._modifier_combo_pending: Optional[int] = None  # 等待释放的 vk_code

    def feed(self, event: RawHookEvent) -> Optional[RecordStep]:
        """输入原始事件，返回完成的步骤或 None"""
        et = event.event_type

        # 更新修饰键状态
        if et == HookEventType.KEYDOWN:
            if event.vk_code in MODIFIER_VKS:
                self._held_modifiers.add(event.vk_code)
        elif et == HookEventType.KEYUP:
            self._held_modifiers.discard(event.vk_code)

        # 分发
        if et == HookEventType.LBUTTONDOWN:
            return self._on_button_down(event, "left")
        elif et == HookEventType.LBUTTONUP:
            return self._on_left_up(event)
        elif et == HookEventType.RBUTTONDOWN:
            return self._on_button_down(event, "right")
        elif et == HookEventType.RBUTTONUP:
            return self._on_right_up(event)
        elif et == HookEventType.MOUSEWHEEL:
            return self._on_scroll(event)
        elif et == HookEventType.KEYDOWN:
            return self._on_key_down(event)
        elif et == HookEventType.KEYUP:
            return self._on_key_up(event)
        elif et in (HookEventType.CHAR, HookEventType.IME_CHAR):
            return self._on_char(event)

        return None

    def flush(self) -> List[RecordStep]:
        """冲刷所有未完成状态，返回剩余步骤列表（录制停止时调用）"""
        results = []
        if self._pending_scroll:
            results.append(self._build_scroll_step(self._pending_scroll))
            self._pending_scroll = None
        if self._pending_text and self._pending_text.chars:
            results.append(self._build_text_step(self._pending_text))
            self._pending_text = None
        return results

    def check_timeouts(self, current_time_us: int) -> List[RecordStep]:
        """检查超时（滚动合并窗口、文本输入间隔），由事件处理循环周期调用"""
        results = []
        # 滚动合并超时
        if self._pending_scroll:
            elapsed = current_time_us - self._pending_scroll.last_event_us
            if elapsed > self._scroll_merge_interval_us:
                results.append(self._build_scroll_step(self._pending_scroll))
                self._pending_scroll = None
        # 文本输入间隔超时
        if self._pending_text and self._pending_text.chars:
            elapsed = current_time_us - self._pending_text.last_char_time_us
            if elapsed > TEXT_INPUT_TIMEOUT_US:
                results.append(self._build_text_step(self._pending_text))
                self._pending_text = None
        return results

    @staticmethod
    def resolve_action(window_action: str, has_process: bool) -> str:
        """根据是否有进程信息决定最终动作名"""
        if not has_process:
            return DESKTOP_ACTION_MAP.get(window_action, window_action)
        return window_action

    # ============================================================
    # 鼠标事件处理
    # ============================================================

    def _on_button_down(self, event: RawHookEvent, button: str) -> Optional[RecordStep]:
        """鼠标按下：先冲刷待定文本，保存按下状态"""
        results = []
        # 按下鼠标时如果有待定文本，立即输出
        if self._pending_text and self._pending_text.chars:
            results.append(self._build_text_step(self._pending_text))
            self._pending_text = None
        # 冲刷待定滚动
        if self._pending_scroll:
            results.append(self._build_scroll_step(self._pending_scroll))
            self._pending_scroll = None

        self._pending_click = PendingClick(
            button=button,
            start_time_us=event.timestamp_us,
            start_x=event.screen_x,
            start_y=event.screen_y,
        )
        # 返回第一个结果（如果有多个，调用方需处理）
        # 实际上每次按下最多产生 flush 的步骤，先返回第一个
        return results[0] if results else None

    def _on_left_up(self, event: RawHookEvent) -> Optional[RecordStep]:
        """左键释放：判断 click / long_press / drag / swipe"""
        if not self._pending_click or self._pending_click.button != "left":
            return None
        pc = self._pending_click
        self._pending_click = None

        dx = event.screen_x - pc.start_x
        dy = event.screen_y - pc.start_y
        displacement = (dx * dx + dy * dy) ** 0.5
        duration_us = event.timestamp_us - pc.start_time_us

        if displacement < CLICK_DISTANCE_THRESHOLD:
            if duration_us < CLICK_TIME_THRESHOLD_US:
                return self._build_click_step("click", pc.start_x, pc.start_y)
            elif duration_us >= LONG_PRESS_TIME_US:
                return self._build_click_step("long_press", pc.start_x, pc.start_y, duration_us)
            else:
                # 300-500ms 之间，视为 click
                return self._build_click_step("click", pc.start_x, pc.start_y)
        else:
            duration_ms = duration_us // 1000
            if duration_us < SWIPE_TIME_THRESHOLD_US:
                return self._build_drag_step("swipe", pc.start_x, pc.start_y,
                                             event.screen_x, event.screen_y, duration_ms)
            else:
                return self._build_drag_step("drag", pc.start_x, pc.start_y,
                                             event.screen_x, event.screen_y, duration_ms)

    def _on_right_up(self, event: RawHookEvent) -> Optional[RecordStep]:
        """右键释放"""
        if not self._pending_click or self._pending_click.button != "right":
            return None
        pc = self._pending_click
        self._pending_click = None
        return self._build_click_step("right_click", pc.start_x, pc.start_y)

    # ============================================================
    # 键盘按下事件处理（文本输入路径）
    # ============================================================

    # Shift + 数字/符号 映射（US 键盘布局）
    _SHIFT_SYMBOL_MAP = {
        0x30: ')', 0x31: '!', 0x32: '@', 0x33: '#', 0x34: '$',
        0x35: '%', 0x36: '^', 0x37: '&', 0x38: '*', 0x39: '(',
        0xBA: ':', 0xBB: '+', 0xBC: '<', 0xBD: '_',
        0xBE: '>', 0xBF: '?', 0xC0: '~',
        0xDB: '{', 0xDC: '|', 0xDD: '}', 0xDE: '"',
    }
    # 无 Shift 的符号键
    _PLAIN_SYMBOL_MAP = {
        0xBA: ';', 0xBB: '=', 0xBC: ',', 0xBD: '-',
        0xBE: '.', 0xBF: '/', 0xC0: '`',
        0xDB: '[', 0xDC: '\\', 0xDD: ']', 0xDE: "'",
    }

    def _on_key_down(self, event: RawHookEvent) -> Optional[RecordStep]:
        """KEYDOWN：可打印字符 → 累积文本；功能键 → 冲刷待定文本"""
        vk = event.vk_code

        # 修饰键仅跟踪状态
        if vk in MODIFIER_VKS:
            return None

        # 如果有非 Shift 修饰键按住（Ctrl/Alt/Win），不作为文本输入
        # 这种组合会在 KEYUP 的 _on_key_up 中生成 press_key
        non_shift_mods = self._held_modifiers - {0x10}  # 排除 Shift
        if non_shift_mods:
            return None

        shift = 0x10 in self._held_modifiers
        char = self._vk_to_printable(vk, shift)

        if char:
            # 可打印字符 → 累积到待定文本
            if self._pending_text is None:
                self._pending_text = PendingText(
                    chars=char,
                    last_char_time_us=event.timestamp_us,
                )
            else:
                self._pending_text.chars += char
                self._pending_text.last_char_time_us = event.timestamp_us
            return None
        else:
            # 功能键（Enter/Tab/Escape 等）→ 先冲刷待定文本
            results = []
            if self._pending_text and self._pending_text.chars:
                results.append(self._build_text_step(self._pending_text))
                self._pending_text = None
            return results[0] if results else None

    @classmethod
    def _vk_to_printable(cls, vk: int, shift: bool) -> str:
        """VK 码 → 可打印字符（不依赖 ToUnicodeEx，直接映射）"""
        # A-Z
        if 0x41 <= vk <= 0x5A:
            return chr(vk).upper() if shift else chr(vk).lower()
        # 0-9
        if 0x30 <= vk <= 0x39:
            if shift:
                return cls._SHIFT_SYMBOL_MAP.get(vk, '')
            return chr(vk)
        # Space
        if vk == 0x20:
            return ' '
        # 符号键
        if shift:
            return cls._SHIFT_SYMBOL_MAP.get(vk, '')
        return cls._PLAIN_SYMBOL_MAP.get(vk, '')

    # ============================================================
    # 滚动事件处理
    # ============================================================

    def _on_scroll(self, event: RawHookEvent) -> Optional[RecordStep]:
        """滚动事件：累积合并"""
        if self._pending_scroll:
            elapsed = event.timestamp_us - self._pending_scroll.last_event_us
            if elapsed <= self._scroll_merge_interval_us:
                # 同一合并窗口内，累加
                self._pending_scroll.total_delta += event.delta
                self._pending_scroll.last_event_us = event.timestamp_us
                return None
            else:
                # 超出合并窗口，输出旧的，开始新的
                step = self._build_scroll_step(self._pending_scroll)

        else:
            step = None

        self._pending_scroll = PendingScroll(
            start_time_us=event.timestamp_us,
            screen_x=event.screen_x,
            screen_y=event.screen_y,
            total_delta=event.delta,
            last_event_us=event.timestamp_us,
        )
        return step

    # ============================================================
    # 键盘事件处理
    # ============================================================

    def _on_key_up(self, event: RawHookEvent) -> Optional[RecordStep]:
        """键盘释放：判断 press_key"""
        vk = event.vk_code

        # 如果正在等待组合键释放
        if self._modifier_combo_pending is not None:
            if vk == self._modifier_combo_pending:
                key_name = self._vk_to_key_name(self._modifier_combo_pending)
                self._modifier_combo_pending = None
                return self._build_key_step(key_name)
            else:
                # 修饰键仍在，但释放的是其他键 → 组合键已完成
                # 这种情况说明修饰键 + 其他键的 KEYDOWN 被跳过了
                pass

        # 如果有修饰键被按住，且释放的是非修饰键 → 组合键
        if self._held_modifiers and vk not in MODIFIER_VKS:
            mod_names = [self._vk_to_key_name(m) for m in sorted(self._held_modifiers)]
            key_name = self._vk_to_key_name(vk)
            all_keys = " ".join(mod_names + [key_name])
            return self._build_key_step(all_keys)

        # 单独的功能键释放
        if vk in FUNCTION_KEY_VKS:
            return self._build_key_step(self._vk_to_key_name(vk))

        # 单独的修饰键释放（无其他键）→ 忽略
        if vk in MODIFIER_VKS:
            return None

        return None

    def _on_char(self, event: RawHookEvent) -> Optional[RecordStep]:
        """字符输入（WM_CHAR / WM_IME_CHAR）"""
        char = chr(event.char_code) if event.char_code < 0x10000 else ""
        if not char:
            return None

        # 如果有修饰键按住，不应作为文本输入（但 CHAR 通常在无修饰键时产生）
        if self._held_modifiers:
            return None

        if self._pending_text is None:
            self._pending_text = PendingText(
                chars=char,
                last_char_time_us=event.timestamp_us,
            )
        else:
            self._pending_text.chars += char
            self._pending_text.last_char_time_us = event.timestamp_us

        return None  # 文本持续累积，由超时或鼠标事件触发输出

    # ============================================================
    # 步骤构建
    # ============================================================

    def _build_click_step(self, action: str, sx: int, sy: int,
                          duration_us: int = 0) -> RecordStep:
        params = {"_raw_screen_x": sx, "_raw_screen_y": sy}
        if action == "long_press":
            params["duration_ms"] = duration_us // 1000
        return RecordStep(action=action, params=params)

    def _build_drag_step(self, action: str, sx: int, sy: int,
                         ex: int, ey: int, duration_ms: int = 0) -> RecordStep:
        params = {
            "_raw_start_x": sx, "_raw_start_y": sy,
            "_raw_end_x": ex, "_raw_end_y": ey,
        }
        if duration_ms:
            params["duration_ms"] = duration_ms
        return RecordStep(action=action, params=params)

    def _build_scroll_step(self, pending: PendingScroll) -> RecordStep:
        return RecordStep(
            action="scroll",
            params={
                "_raw_screen_x": pending.screen_x,
                "_raw_screen_y": pending.screen_y,
                "delta": pending.total_delta,
            },
        )

    def _build_text_step(self, pending: PendingText) -> RecordStep:
        return RecordStep(
            action="input_text",
            params={"text": pending.chars},
        )

    def _build_key_step(self, key: str) -> RecordStep:
        return RecordStep(
            action="press_key",
            params={"key": key},
        )

    # ============================================================
    # 工具方法
    # ============================================================

    @staticmethod
    def _vk_to_key_name(vk: int) -> str:
        """将虚拟键码转换为按键名称"""
        # 常用映射
        VK_NAMES = {
            0x08: "backspace", 0x09: "tab", 0x0D: "enter",
            0x1B: "escape", 0x20: "space",
            0x21: "pageup", 0x22: "pagedown",
            0x23: "end", 0x24: "home",
            0x25: "left", 0x26: "up", 0x27: "right", 0x28: "down",
            0x2D: "insert", 0x2E: "delete",
            0x5B: "win", 0x5C: "win",
            0x5D: "apps",
            0x10: "shift", 0x11: "ctrl", 0x12: "alt",
            0xA0: "shift", 0xA1: "shift",   # LShift, RShift → 统一为 shift
            0xA2: "ctrl",  0xA3: "ctrl",     # LControl, RControl → 统一为 ctrl
            0xA4: "alt",   0xA5: "alt",      # LMenu, RMenu → 统一为 alt
            0x14: "capslock", 0x90: "numlock", 0x91: "scrolllock",
        }
        # F1-F24
        if 0x70 <= vk <= 0x87:
            return f"f{vk - 0x6F}"
        # 数字 0-9
        if 0x30 <= vk <= 0x39:
            return chr(vk)
        # A-Z
        if 0x41 <= vk <= 0x5A:
            return chr(vk).lower()
        return VK_NAMES.get(vk, f"vk_{vk}")

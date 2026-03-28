"""
用户确认服务 - 用于 SendInput 操作前的弹窗确认
"""
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Optional
from dataclasses import dataclass
import json
import os


@dataclass
class ConfirmResult:
    """确认结果"""
    confirmed: bool
    remember: bool  # 是否记住选择（下次自动同意）


class ConfirmDialog:
    """确认弹窗 - 使用 tkinter"""

    # 颜色配置 - 米黄色主题
    BG_PRIMARY = "#FAF8F0"      # 米黄底色
    BG_ELEVATED = "#FFFFFF"     # 白色卡片
    BG_SECONDARY = "#F0EBE0"    # 次要背景
    BORDER = "#D4CDBE"          # 边框色
    TEXT_PRIMARY = "#333333"    # 主文字
    TEXT_SECONDARY = "#666666"  # 次要文字
    ACCENT = "#1A1A1A"          # 炭黑主按钮
    ACCENT_HOVER = "#2A2A2A"    # 炭黑悬停
    DANGER = "#C94E4E"          # 红色
    SUCCESS = "#4EC9B0"         # 成功色

    # 多语言文本
    I18N = {
        "zh_CN": {
            "title": "操作确认",
            "checkbox": "该进程下次自动同意（可在设置里取消）",
            "checkbox_short": "该进程下次自动同意",
            "confirm": "确定",
            "cancel": "取消",
            "timeout_prefix": "超时自动关闭：",
            "preparing": " 准备操作 ",
            "operation": "操作：",
            "detail": "详情：",
            "warning": "这会占用你的鼠标和键盘。",
            # 操作类型翻译
            "op_click": "点击",
            "op_long_press": "长按",
            "op_swipe": "滑动",
            "op_right_click": "右键点击",
            "op_input_text": "输入文本",
            "op_press_key": "按键",
            "op_scroll": "滚动",
            "op_hover": "鼠标悬浮"
        },
        "en_US": {
            "title": "Operation Confirmation",
            "checkbox": "Auto-approve this process next time",
            "checkbox_suffix": "(can be cancelled in settings)",
            "confirm": "Confirm",
            "cancel": "Cancel",
            "timeout_prefix": "Auto-close in: ",
            "preparing": " is preparing to operate ",
            "operation": "Operation: ",
            "detail": "Detail: ",
            "warning": "This will occupy your mouse and keyboard.",
            # 操作类型翻译
            "op_click": "Click",
            "op_long_press": "Long Press",
            "op_swipe": "Swipe",
            "op_right_click": "Right Click",
            "op_input_text": "Input Text",
            "op_press_key": "Press Key",
            "op_scroll": "Scroll",
            "op_hover": "Hover"
        }
    }

    # 操作类型映射
    OPERATION_MAP = {
        "点击": "op_click",
        "长按": "op_long_press",
        "滑动": "op_swipe",
        "右键点击": "op_right_click",
        "输入文本": "op_input_text",
        "按键": "op_press_key",
        "滚动": "op_scroll",
        "鼠标悬浮": "op_hover"
    }

    TIMEOUT_SECONDS = 30  # 超时时间（秒）

    def __init__(self, ai_app_type: str, window_title: str, operation: str, operation_detail: str, language: str = "zh_CN"):
        self.ai_app_type = ai_app_type
        self.window_title = window_title
        self.operation = operation
        self.operation_detail = operation_detail
        self.language = language
        self.result: Optional[ConfirmResult] = None
        self.time_left = self.TIMEOUT_SECONDS
        self.timer_id = None

    def get_text(self, key: str) -> str:
        """获取当前语言的文本"""
        return self.I18N.get(self.language, self.I18N["zh_CN"]).get(key, key)

    def translate_operation(self, operation: str) -> str:
        """翻译操作类型"""
        # 如果是中文操作类型，进行翻译
        if operation in self.OPERATION_MAP:
            return self.get_text(self.OPERATION_MAP[operation])
        # 如果已经是英文或其他语言，直接返回
        return operation

    def translate_detail(self, detail: str) -> str:
        """翻译详情内容"""
        if self.language == "en_US":
            # 英文翻译映射
            replacements = {
                "输入：": "Input: ",
                "按键：": "Key: ",
                "滚动量：": "Scroll: ",
                "滚动": "scroll"
            }
            for cn, en in replacements.items():
                detail = detail.replace(cn, en)
        return detail

    def update_countdown(self, root, label):
        """更新倒计时显示"""
        self.time_left -= 1
        label.config(text=f"{self.get_text('timeout_prefix')}{self.time_left}s")

        if self.time_left <= 0:
            # 超时，视为拒绝
            self.result = ConfirmResult(confirmed=False, remember=False)
            root.destroy()
        else:
            # 继续倒计时
            self.timer_id = root.after(1000, lambda: self.update_countdown(root, label))

    def show(self) -> ConfirmResult:
        """显示弹窗并返回结果"""
        print(f"[ConfirmDialog] Starting show() for operation={self.operation}")

        root = tk.Tk()
        root.title("ScreenClaw " + self.get_text('title'))
        root.geometry("520x420")
        root.resizable(False, False)

        # 设置系统默认字体
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=10)

        # 获取屏幕尺寸并居中
        root.update_idletasks()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = 520
        window_height = 420
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # 设置为最顶层窗口并强制显示
        root.attributes('-topmost', True)
        root.lift()
        root.focus_force()

        # 确保窗口立即显示
        root.update()

        print(f"[ConfirmDialog] Window created at ({x}, {y}), screen=({screen_width}, {screen_height})")

        # 配置根窗口背景
        root.configure(bg=self.BG_PRIMARY)

        # 主容器
        main_frame = tk.Frame(root, bg=self.BG_PRIMARY, padx=24, pady=24)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题和倒计时
        header_frame = tk.Frame(main_frame, bg=self.BG_PRIMARY)
        header_frame.pack(fill=tk.X, pady=(0, 16))

        title_label = tk.Label(
            header_frame,
            text=self.get_text('title'),
            bg=self.BG_PRIMARY,
            fg=self.TEXT_PRIMARY,
            font=('TkDefaultFont', 14, 'bold'),
            anchor=tk.W
        )
        title_label.pack(side=tk.LEFT)

        countdown_label = tk.Label(
            header_frame,
            text=f"{self.get_text('timeout_prefix')}{self.TIMEOUT_SECONDS}s",
            bg=self.BG_PRIMARY,
            fg=self.DANGER,
            font=('TkDefaultFont', 10),
            anchor=tk.E
        )
        countdown_label.pack(side=tk.RIGHT)

        # 翻译操作类型和详情
        translated_operation = self.translate_operation(self.operation)
        translated_detail = self.translate_detail(self.operation_detail)

        # 内容区域容器（固定高度）
        content_frame = tk.Frame(main_frame, bg=self.BG_PRIMARY)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 16))

        # 提示信息（可滚动）
        info_text = (f"{self.ai_app_type}{self.get_text('preparing')}{self.window_title}\n"
                    f"{self.get_text('operation')}{translated_operation}\n"
                    f"{self.get_text('detail')}{translated_detail}\n"
                    f"{self.get_text('warning')}")

        # 创建滚动文本框
        info_text_widget = tk.Text(
            content_frame,
            bg=self.BG_ELEVATED,
            fg=self.TEXT_PRIMARY,
            font=('TkDefaultFont', 10),
            relief=tk.SOLID,
            bd=1,
            padx=16,
            pady=14,
            wrap=tk.WORD,
            height=6,  # 固定显示6行
            state=tk.NORMAL
        )
        info_text_widget.insert(tk.END, info_text)
        info_text_widget.config(state=tk.DISABLED)  # 设为只读

        # 滚动条
        scrollbar = tk.Scrollbar(
            content_frame,
            command=info_text_widget.yview,
            bg=self.BG_SECONDARY,
            troughcolor=self.BG_PRIMARY
        )
        info_text_widget.config(yscrollcommand=scrollbar.set)

        # 布局：文本框和滚动条
        info_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 记住选择复选框
        remember_var = tk.BooleanVar(value=False)

        # 复选框文本（根据语言决定是否分行）
        if self.language == "en_US":
            # 英文时分两行显示
            checkbox_frame = tk.Frame(main_frame, bg=self.BG_PRIMARY)
            checkbox_frame.pack(fill=tk.X, pady=(0, 20))

            check_btn = tk.Checkbutton(
                checkbox_frame,
                text="",
                variable=remember_var,
                bg=self.BG_PRIMARY,
                fg=self.TEXT_PRIMARY,
                selectcolor=self.BG_ELEVATED,
                activebackground=self.BG_PRIMARY,
                activeforeground=self.TEXT_PRIMARY,
                font=('TkDefaultFont', 10),
                relief=tk.FLAT,
                bd=0,
                padx=0,
                pady=0,
                anchor=tk.W
            )
            check_btn.pack(side=tk.LEFT)

            # 复选框旁边的文本
            checkbox_text_label = tk.Label(
                checkbox_frame,
                text=f"{self.get_text('checkbox')}\n{self.get_text('checkbox_suffix')}",
                bg=self.BG_PRIMARY,
                fg=self.TEXT_PRIMARY,
                font=('TkDefaultFont', 9),
                anchor=tk.W,
                justify=tk.LEFT
            )
            checkbox_text_label.pack(side=tk.LEFT, padx=(4, 0))

            # 绑定点击事件
            def toggle_checkbox(event):
                remember_var.set(not remember_var.get())
                checkbox_text_label.config(
                    fg=self.TEXT_PRIMARY if remember_var.get() else self.TEXT_SECONDARY
                )

            checkbox_text_label.bind("<Button-1>", toggle_checkbox)
            check_btn.bind("<Button-1>", lambda e: checkbox_text_label.config(
                fg=self.TEXT_PRIMARY if remember_var.get() else self.TEXT_SECONDARY
            ))
        else:
            # 中文时正常显示
            check_btn = tk.Checkbutton(
                main_frame,
                text=self.get_text('checkbox'),
                variable=remember_var,
                bg=self.BG_PRIMARY,
                fg=self.TEXT_PRIMARY,
                selectcolor=self.BG_ELEVATED,
                activebackground=self.BG_PRIMARY,
                activeforeground=self.TEXT_PRIMARY,
                font=('TkDefaultFont', 10),
                relief=tk.FLAT,
                bd=0,
                padx=0,
                pady=4,
                anchor=tk.W,
                justify=tk.LEFT
            )
            check_btn.pack(fill=tk.X, pady=(0, 20))

        # 按钮框架
        btn_frame = tk.Frame(main_frame, bg=self.BG_PRIMARY)
        btn_frame.pack(fill=tk.X)

        def on_cancel():
            print(f"[ConfirmDialog] on_cancel called")
            if self.timer_id:
                root.after_cancel(self.timer_id)
            self.result = ConfirmResult(confirmed=False, remember=remember_var.get())
            print(f"[ConfirmDialog] on_cancel: result.confirmed={self.result.confirmed}, remember={self.result.remember}")
            root.destroy()

        def on_confirm():
            print(f"[ConfirmDialog] on_confirm called")
            if self.timer_id:
                root.after_cancel(self.timer_id)
            self.result = ConfirmResult(confirmed=True, remember=remember_var.get())
            print(f"[ConfirmDialog] on_confirm: result.confirmed={self.result.confirmed}, remember={self.result.remember}")
            root.destroy()

        # 右侧按钮容器
        btn_right_frame = tk.Frame(btn_frame, bg=self.BG_PRIMARY)
        btn_right_frame.pack(side=tk.RIGHT)

        # 确定按钮
        confirm_btn = tk.Button(
            btn_right_frame,
            text=self.get_text('confirm'),
            command=on_confirm,
            width=10,
            bg=self.ACCENT,
            fg="white",
            font=('TkDefaultFont', 10),
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=12,
            cursor="hand2"
        )
        confirm_btn.pack(side=tk.LEFT, padx=(0, 8))

        # 取消按钮
        cancel_btn = tk.Button(
            btn_right_frame,
            text=self.get_text('cancel'),
            command=on_cancel,
            width=10,
            bg=self.BG_SECONDARY,
            fg=self.TEXT_PRIMARY,
            font=('TkDefaultFont', 10),
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=12,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT)

        # 设置默认按钮
        confirm_btn.focus_set()
        root.bind('<Return>', lambda e: on_confirm())
        root.bind('<Escape>', lambda e: on_cancel())

        # 关闭窗口等同于取消
        root.protocol("WM_DELETE_WINDOW", on_cancel)

        # 启动倒计时
        self.timer_id = root.after(1000, lambda: self.update_countdown(root, countdown_label))

        root.mainloop()

        return self.result or ConfirmResult(confirmed=False, remember=False)


class ConfirmService:
    """确认服务"""

    # 自动同意的进程列表（进程名）
    _auto_confirm_processes: set = set()
    # 当前语言设置
    _language: str = "zh_CN"

    @classmethod
    def _get_config_path(cls) -> str:
        """获取配置文件路径"""
        # confirm_service.py 在 python/app/services/ 下，需要向上四级到项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        return os.path.join(project_root, "data", "config.json")

    @classmethod
    def _load_language(cls):
        """从配置加载语言设置"""
        config_path = cls._get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    cls._language = config.get("ui", {}).get("language", "zh_CN")
                    print(f"[ConfirmService] 加载语言设置: {cls._language}")
            except Exception as e:
                print(f"[ConfirmService] 加载语言失败: {e}")
                cls._language = "zh_CN"
        else:
            print(f"[ConfirmService] 配置文件不存在，使用默认语言")
            cls._language = "zh_CN"

    @classmethod
    def load_config(cls):
        """从配置加载自动同意设置"""
        config_path = cls._get_config_path()

        # 同时加载语言设置
        cls._load_language()

        print(f"[ConfirmService] 加载配置，路径: {config_path}")
        print(f"[ConfirmService] 当前语言: {cls._language}")

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    security = config.get("security", {})
                    cls._auto_confirm_processes = set(security.get("auto_confirm_processes", []))
                print(f"[ConfirmService] 加载成功，自动同意列表: {cls._auto_confirm_processes}")
            except Exception as e:
                print(f"[ConfirmService] 加载失败: {e}")
                cls._auto_confirm_processes = set()
        else:
            print(f"[ConfirmService] 配置文件不存在")
            cls._auto_confirm_processes = set()

    @classmethod
    def save_auto_confirm_process(cls, process_name: str):
        """保存自动同意的进程"""
        cls._auto_confirm_processes.add(process_name)
        config_path = cls._get_config_path()

        print(f"[ConfirmService] 保存自动同意进程: {process_name}")
        print(f"[ConfirmService] 配置路径: {config_path}")
        print(f"[ConfirmService] 当前自动同意列表: {cls._auto_confirm_processes}")

        try:
            # 读取现有配置
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"[ConfirmService] 读取现有配置成功")
            else:
                config = {}
                print(f"[ConfirmService] 配置文件不存在，创建新配置")

            if "security" not in config:
                config["security"] = {}

            config["security"]["auto_confirm_processes"] = list(cls._auto_confirm_processes)

            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            # 写入配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"[ConfirmService] 保存配置成功")
        except Exception as e:
            print(f"[ConfirmService] 保存配置失败: {e}")
            import traceback
            traceback.print_exc()

    @classmethod
    def request_confirm(cls, ai_app_type: str, window_title: str, process_name: str,
                        operation: str, operation_detail: str) -> ConfirmResult:
        """请求用户确认

        Args:
            ai_app_type: AI 应用类型（如 "claude_code"）
            window_title: 目标窗口标题
            process_name: 目标进程名（如 "notepad.exe"）
            operation: 操作类型（如 "输入文本" / "按键" / "滚动"）
            operation_detail: 操作详情（如 "输入：hello" / "按键：Ctrl+C"）

        Returns:
            ConfirmResult: 确认结果
        """
        # 每次请求前重新加载语言设置
        cls._load_language()

        print(f"[ConfirmService] request_confirm 被调用: ai_app_type={ai_app_type}, process_name={process_name}, operation={operation}, detail={operation_detail}")
        print(f"[ConfirmService] 当前语言: {cls._language}")
        print(f"[ConfirmService] 当前自动同意列表: {cls._auto_confirm_processes}")

        # 检查目标进程是否在自动同意列表中
        if process_name in cls._auto_confirm_processes:
            print(f"[ConfirmService] 进程在自动同意列表中，跳过弹窗")
            return ConfirmResult(confirmed=True, remember=True)

        # 在主线程中显示弹窗
        print(f"[ConfirmService] 创建确认弹窗...")
        dialog = ConfirmDialog(ai_app_type, window_title, operation, operation_detail, cls._language)
        result = dialog.show()

        print(f"[ConfirmService] 弹窗返回: confirmed={result.confirmed}, remember={result.remember}")

        # 如果用户选择记住，保存进程名
        if result.remember and result.confirmed:
            cls.save_auto_confirm_process(process_name)
        else:
            print(f"[ConfirmService] 未保存：remember={result.remember}, confirmed={result.confirmed}")

        print(f"[ConfirmService] request_confirm 返回: confirmed={result.confirmed}")
        return result


# 初始化时加载配置
ConfirmService.load_config()

"""
托管模式API - 进入/退出/查询托管状态
"""
import time
import tkinter as tk
import tkinter.font as tkfont
from typing import Optional
from dataclasses import dataclass
from fastapi import APIRouter, Request as FastAPIRequest

from app.models.request import DelegatedRequest
from app.models.response import BaseResponse, create_error_response
from app.services.config_service import config_service
from app.services.log_service import log_service
from app.api.decorators import get_client_ip

router = APIRouter()


# ============ 托管确认弹窗 ============

@dataclass
class DelegatedConfirmResult:
    """托管确认结果"""
    confirmed: bool


class DelegatedConfirmDialog:
    """托管模式确认弹窗 - 无"记住"复选框，专属UI"""

    # 颜色配置
    BG_PRIMARY = "#FAF8F0"
    BG_ELEVATED = "#FFFFFF"
    BG_SECONDARY = "#F0EBE0"
    BORDER = "#D4CDBE"
    TEXT_PRIMARY = "#333333"
    TEXT_SECONDARY = "#666666"
    ACCENT = "#C94E4E"          # 红色警告风格
    ACCENT_HOVER = "#A33A3A"
    DANGER = "#C94E4E"
    BTN_PRIMARY = "#1A1A1A"
    BTN_PRIMARY_HOVER = "#2A2A2A"

    I18N = {
        "zh_CN": {
            "title": "⚠ 进入托管模式",
            "message": "ScreenClaw 将获得电脑的鼠标和键盘控制权",
            "detail": "所有操作将直接执行，不恢复窗口状态和鼠标位置。",
            "hotkey_info": "按 {hotkey} 可随时退出托管模式",
            "request_from": "请求来源：{ip}",
            "confirm": "进入托管",
            "cancel": "取消",
            "timeout_prefix": "超时自动关闭：",
        },
        "en_US": {
            "title": "⚠ Enter Delegated Mode",
            "message": "ScreenClaw will gain control of your mouse and keyboard",
            "detail": "All operations will be executed directly without restoring window state or cursor position.",
            "hotkey_info": "Press {hotkey} to exit delegated mode at any time",
            "request_from": "Request from: {ip}",
            "confirm": "Enter Delegated",
            "cancel": "Cancel",
            "timeout_prefix": "Auto-close in: ",
        }
    }

    TIMEOUT_SECONDS = 30

    def __init__(self, language: str = "zh_CN", hotkey: str = "ctrl+alt+z", client_ip: str = "unknown"):
        self.language = language
        self.hotkey = hotkey
        self.client_ip = client_ip
        self.result: Optional[DelegatedConfirmResult] = None
        self.time_left = self.TIMEOUT_SECONDS
        self.timer_id = None

    def get_text(self, key: str) -> str:
        texts = self.I18N.get(self.language, self.I18N["zh_CN"])
        text = texts.get(key, key)
        if "{hotkey}" in text:
            text = text.replace("{hotkey}", self.hotkey.upper())
        return text

    def show(self) -> DelegatedConfirmResult:
        root = tk.Tk()
        root.title("ScreenClaw - " + self.get_text('title'))
        root.geometry("480x340")
        root.resizable(False, False)

        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=10)

        root.update_idletasks()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - 480) // 2
        y = (screen_height - 340) // 2
        root.geometry(f"480x340+{x}+{y}")

        root.attributes('-topmost', True)
        root.lift()
        root.focus_force()
        root.update()

        root.configure(bg=self.BG_PRIMARY)

        main_frame = tk.Frame(root, bg=self.BG_PRIMARY, padx=24, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题和倒计时
        header_frame = tk.Frame(main_frame, bg=self.BG_PRIMARY)
        header_frame.pack(fill=tk.X, pady=(0, 12))

        title_label = tk.Label(
            header_frame, text=self.get_text('title'),
            bg=self.BG_PRIMARY, fg=self.ACCENT,
            font=('TkDefaultFont', 14, 'bold'), anchor=tk.W
        )
        title_label.pack(side=tk.LEFT)

        countdown_label = tk.Label(
            header_frame,
            text=f"{self.get_text('timeout_prefix')}{self.TIMEOUT_SECONDS}s",
            bg=self.BG_PRIMARY, fg=self.DANGER,
            font=('TkDefaultFont', 10), anchor=tk.E
        )
        countdown_label.pack(side=tk.RIGHT)

        # 内容区域
        content_frame = tk.Frame(main_frame, bg=self.BG_ELEVATED, padx=16, pady=14)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 16))

        msg_label = tk.Label(
            content_frame, text=self.get_text('message'),
            bg=self.BG_ELEVATED, fg=self.TEXT_PRIMARY,
            font=('TkDefaultFont', 10), anchor=tk.W, wraplength=420, justify=tk.LEFT
        )
        msg_label.pack(fill=tk.X, pady=(0, 8))

        detail_label = tk.Label(
            content_frame, text=self.get_text('detail'),
            bg=self.BG_ELEVATED, fg=self.TEXT_SECONDARY,
            font=('TkDefaultFont', 9), anchor=tk.W, wraplength=420, justify=tk.LEFT
        )
        detail_label.pack(fill=tk.X, pady=(0, 8))

        hotkey_label = tk.Label(
            content_frame, text=self.get_text('hotkey_info'),
            bg=self.BG_ELEVATED, fg=self.ACCENT,
            font=('TkDefaultFont', 10, 'bold'), anchor=tk.W, wraplength=420, justify=tk.LEFT
        )
        hotkey_label.pack(fill=tk.X)

        # 请求来源 IP
        if self.client_ip and self.client_ip != "unknown":
            ip_text = self.get_text('request_from').replace("{ip}", self.client_ip)
            ip_label = tk.Label(
                content_frame, text=ip_text,
                bg=self.BG_ELEVATED, fg=self.TEXT_SECONDARY,
                font=('TkDefaultFont', 9), anchor=tk.W, wraplength=420, justify=tk.LEFT
            )
            ip_label.pack(fill=tk.X, pady=(6, 0))

        # 按钮框架
        btn_frame = tk.Frame(main_frame, bg=self.BG_PRIMARY)
        btn_frame.pack(fill=tk.X)

        def on_cancel():
            if self.timer_id:
                root.after_cancel(self.timer_id)
            self.result = DelegatedConfirmResult(confirmed=False)
            root.destroy()

        def on_confirm():
            if self.timer_id:
                root.after_cancel(self.timer_id)
            self.result = DelegatedConfirmResult(confirmed=True)
            root.destroy()

        btn_right = tk.Frame(btn_frame, bg=self.BG_PRIMARY)
        btn_right.pack(side=tk.RIGHT)

        confirm_btn = tk.Button(
            btn_right, text=self.get_text('confirm'), command=on_confirm,
            width=12, bg=self.BTN_PRIMARY, fg="white",
            font=('TkDefaultFont', 10), relief=tk.FLAT, padx=20, pady=10, cursor="hand2"
        )
        confirm_btn.pack(side=tk.LEFT, padx=(0, 8))

        cancel_btn = tk.Button(
            btn_right, text=self.get_text('cancel'), command=on_cancel,
            width=8, bg=self.BG_SECONDARY, fg=self.TEXT_PRIMARY,
            font=('TkDefaultFont', 10), relief=tk.FLAT, padx=20, pady=10, cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT)

        def update_countdown():
            self.time_left -= 1
            countdown_label.config(text=f"{self.get_text('timeout_prefix')}{self.time_left}s")
            if self.time_left <= 0:
                self.result = DelegatedConfirmResult(confirmed=False)
                root.destroy()
            else:
                self.timer_id = root.after(1000, update_countdown)

        cancel_btn.focus_set()
        root.bind('<Return>', lambda e: on_confirm())
        root.bind('<Escape>', lambda e: on_cancel())
        root.protocol("WM_DELETE_WINDOW", on_cancel)

        self.timer_id = root.after(1000, update_countdown)
        root.mainloop()

        return self.result or DelegatedConfirmResult(confirmed=False)


# ============ API端点 ============

@router.post("/delegated")
async def delegated_control(request: DelegatedRequest, req: FastAPIRequest = None):
    """托管模式控制 - 进入/退出/查询"""
    client_ip = get_client_ip(req) if req else "unknown"

    if request.action == "status":
        active = config_service.is_delegated_active()
        return BaseResponse(
            success=True,
            message="Delegated mode status",
            data={"delegated_active": active}
        )

    if request.action == "enter":
        start_time = time.time()

        # 已在托管模式，直接返回
        if config_service.is_delegated_active():
            return BaseResponse(
                success=True,
                message="Delegated mode activated.",
                data={"delegated_active": True}
            )

        # 获取退出快捷键
        config = config_service.get()
        language = config.ui.language
        exit_hotkey = config.delegated.exit_hotkey

        # 弹窗确认（专属托管确认弹窗，无"记住"复选框）
        dialog = DelegatedConfirmDialog(language=language, hotkey=exit_hotkey, client_ip=client_ip)
        confirm_result = dialog.show()

        duration_ms = int((time.time() - start_time) * 1000)

        if not confirm_result.confirmed:
            # 记录日志
            log_service.log(
                ai_app_type="", session_id="", window_id=0,
                process_name="", instruction="delegated_enter",
                params={"action": "enter"},
                result={"success": False, "message": "User rejected"},
                duration_ms=duration_ms,
                client_ip=client_ip
            )
            return BaseResponse(
                success=False,
                message="User rejected delegated mode",
                data={"delegated_active": False}
            )

        # 写入托管状态
        config_service.update_delegated(active=True)
        print("[Delegated] Delegated mode ACTIVATED")

        # 记录日志
        log_service.log(
            ai_app_type="", session_id="", window_id=0,
            process_name="", instruction="delegated_enter",
            params={"action": "enter"},
            result={"success": True, "message": "Delegated mode activated."},
            duration_ms=duration_ms,
            client_ip=client_ip
        )

        return BaseResponse(
            success=True,
            message="Delegated mode activated.",
            data={"delegated_active": True}
        )

    if request.action == "exit":
        start_time = time.time()
        config_service.update_delegated(active=False)
        duration_ms = int((time.time() - start_time) * 1000)
        print("[Delegated] Delegated mode DEACTIVATED")

        # 记录日志
        log_service.log(
            ai_app_type="", session_id="", window_id=0,
            process_name="", instruction="delegated_exit",
            params={"action": "exit"},
            result={"success": True, "message": "Delegated mode exited."},
            duration_ms=duration_ms,
            client_ip=client_ip
        )

        return BaseResponse(
            success=True,
            message="Delegated mode exited.",
            data={"delegated_active": False}
        )

    return create_error_response("INVALID_ACTION", f"Unknown action: {request.action}. Use enter/exit/status.")

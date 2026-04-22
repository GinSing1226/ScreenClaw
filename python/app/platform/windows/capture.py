"""
Windows截图实现
使用 PrintWindow (ctypes) + Pillow，并通过 WGC 服务作为 DirectX 窗口的 fallback。
"""
import logging
from typing import Optional
from dataclasses import dataclass
import ctypes
from ctypes import windll, c_void_p, byref

import win32gui

from PIL import Image

logger = logging.getLogger(__name__)

# PrintWindow 标志
PW_CLIENTONLY = 0x1
PW_RENDERFULLCONTENT = 0x2


@dataclass
class CaptureResult:
    """截图结果"""
    success: bool
    image: Optional[Image.Image]
    error: Optional[str]
    method: str  # "printwindow" | "wgc" | ""


class WindowsCapture:
    """Windows截图 — 支持 PrintWindow 与 WGC 两种方式"""

    def __init__(self):
        self._capture_method: str = "auto"  # "auto" | "printwindow" | "wgc"

    def set_capture_method(self, method: str):
        """设置截图方式: auto / printwindow / wgc"""
        if method in ("auto", "printwindow", "wgc"):
            self._capture_method = method
        else:
            logger.warning("[capture] 未知的截图方式: %s，使用 auto", method)

    def capture(self, hwnd: int) -> CaptureResult:
        """截图主入口"""
        if self._capture_method == "wgc":
            return self._capture_by_wgc(hwnd)

        # printwindow 或 auto: 先尝试 PrintWindow
        result = self._capture_by_printwindow(hwnd)
        if result.success:
            return result

        # auto: PrintWindow 失败时 fallback 到 WGC
        if self._capture_method == "auto":
            logger.info("[capture] PrintWindow 失败，尝试 WGC fallback")
            wgc_result = self._capture_by_wgc(hwnd)
            if wgc_result.success:
                return wgc_result

        return result

    def _capture_by_wgc(self, hwnd: int) -> CaptureResult:
        """通过 WGC 服务截图（适用于 DX/UE 游戏）"""
        try:
            from app.platform.windows.wgc_client import wgc_client
            success, image, error = wgc_client.capture(hwnd)
            if success:
                return CaptureResult(
                    success=True,
                    image=image,
                    error=None,
                    method="wgc",
                )
            else:
                return CaptureResult(
                    success=False,
                    image=None,
                    error=error,
                    method="",
                )
        except Exception as e:
            logger.error("[capture] WGC 异常: %s", e)
            return CaptureResult(
                success=False,
                image=None,
                error=f"WGC 异常: {e}",
                method="",
            )

    def _capture_by_printwindow(self, hwnd: int) -> CaptureResult:
        """使用 PrintWindow 截图（支持后台）"""
        try:
            # 获取窗口尺寸（PrintWindow 渲染整个窗口，包含边框）
            rect = win32gui.GetWindowRect(hwnd)
            virtual_width = rect[2] - rect[0]
            virtual_height = rect[3] - rect[1]

            # 多显示器混合DPI环境下，GetWindowRect 返回的是虚拟屏幕坐标
            # PrintWindow 渲染的尺寸取决于窗口所在显示器的 DPI
            # - 当 WindowDPI = SystemDPI 时，渲染 Virtual 尺寸
            # - 当 WindowDPI < SystemDPI 时，渲染 Virtual × (WindowDPI/SystemDPI)
            system_dpi = windll.user32.GetDpiForSystem()
            window_dpi = windll.user32.GetDpiForWindow(hwnd)
            scale_factor = window_dpi / system_dpi

            # 虚拟坐标转 PrintWindow 渲染尺寸
            width = int(virtual_width * scale_factor)
            height = int(virtual_height * scale_factor)

            if width <= 0 or height <= 0:
                return CaptureResult(
                    success=False,
                    image=None,
                    error="窗口尺寸无效",
                    method=""
                )

            # 获取窗口 DC
            hwnd_dc = win32gui.GetWindowDC(hwnd)

            # 创建兼容的内存 DC
            mem_dc = windll.gdi32.CreateCompatibleDC(hwnd_dc)

            # 创建 DIB 位图（PrintWindow 需要 DIB 位图）
            bmi = ctypes.create_string_buffer(40)
            ctypes.memset(bmi, 0, 40)
            ctypes.memmove(bmi, ctypes.byref(ctypes.c_int32(40)), 4)  # biSize
            ctypes.memmove(ctypes.addressof(bmi) + 4, ctypes.byref(ctypes.c_int32(width)), 4)  # biWidth
            ctypes.memmove(ctypes.addressof(bmi) + 8, ctypes.byref(ctypes.c_int32(-height)), 4)  # biHeight (负数表示自上而下)
            ctypes.memmove(ctypes.addressof(bmi) + 12, ctypes.byref(ctypes.c_ushort(1)), 2)  # biPlanes
            ctypes.memmove(ctypes.addressof(bmi) + 14, ctypes.byref(ctypes.c_ushort(32)), 2)  # biBitCount (32位)
            ctypes.memmove(ctypes.addressof(bmi) + 16, ctypes.byref(ctypes.c_int32(0)), 4)  # biCompression

            # 创建 DIB 位图
            pbits = c_void_p()
            hbitmap = windll.gdi32.CreateDIBSection(hwnd_dc, bmi, 0, byref(pbits), None, 0)

            if not hbitmap or not pbits:
                windll.gdi32.DeleteDC(mem_dc)
                win32gui.ReleaseDC(hwnd, hwnd_dc)
                return CaptureResult(
                    success=False,
                    image=None,
                    error="创建 DIB 位图失败",
                    method=""
                )

            # 选入位图
            old_bitmap = windll.gdi32.SelectObject(mem_dc, hbitmap)

            # 调用 PrintWindow
            result = windll.user32.PrintWindow(hwnd, mem_dc, PW_RENDERFULLCONTENT)

            if result:
                # 从 DIB 位图读取像素数据
                pixel_count = width * height
                buffer_size = pixel_count * 4  # BGRA 4 bytes per pixel
                pixel_buffer = ctypes.create_string_buffer(buffer_size)
                ctypes.memmove(pixel_buffer, pbits, buffer_size)

                # 使用 Pillow 直接处理 BGRA 数据
                image = Image.frombuffer(
                    'RGBA',
                    (width, height),
                    pixel_buffer.raw,
                    'raw',
                    'BGRA',
                    0,
                    1
                )
                # 转换为 RGB
                image = image.convert('RGB')
            else:
                image = None

            # 清理资源
            windll.gdi32.SelectObject(mem_dc, old_bitmap)
            windll.gdi32.DeleteObject(hbitmap)
            windll.gdi32.DeleteDC(mem_dc)
            win32gui.ReleaseDC(hwnd, hwnd_dc)

            if image:
                # 黑屏检测：PrintWindow 恢复后可能拿到全黑图像
                if self._is_black_image(image):
                    logger.info("[capture] PrintWindow 返回黑屏图像，触发 fallback")
                    return CaptureResult(
                        success=False,
                        image=None,
                        error="PrintWindow captured black screen",
                        method=""
                    )
                return CaptureResult(
                    success=True,
                    image=image,
                    error=None,
                    method="printwindow"
                )
            else:
                return CaptureResult(
                    success=False,
                    image=None,
                    error="PrintWindow failed. The target window may be invalid or unresponsive. Use get_window_list to get a valid window_id and retry.",
                    method=""
                )

        except Exception as e:
            return CaptureResult(
                success=False,
                image=None,
                error=f"截图异常: {str(e)}",
                method=""
            )

    def _is_black_image(self, image: Image.Image) -> bool:
        """检测 PrintWindow 返回的图像是否全黑

        PrintWindow 恢复最小化窗口后可能返回纯黑图像（像素全为 0）。
        使用 numpy 计算均值和标准差：纯黑 mean≈0, std≈0。
        暗色主题 UI 仍有文字/图标/边框，std 不会接近 0，不会误判。
        """
        try:
            import numpy as np
            arr = np.array(image)
            return arr.mean() < 5 and arr.std() < 2
        except Exception:
            return False


# 全局截图实例
windows_capture = WindowsCapture()

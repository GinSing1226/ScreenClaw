"""
Windows截图实现
使用 PrintWindow (ctypes) + Pillow
"""
from typing import Optional
from dataclasses import dataclass
import ctypes
from ctypes import windll, c_void_p, byref

import win32gui

from PIL import Image


# PrintWindow 标志
PW_CLIENTONLY = 0x1
PW_RENDERFULLCONTENT = 0x2


@dataclass
class CaptureResult:
    """截图结果"""
    success: bool
    image: Optional[Image.Image]
    error: Optional[str]
    method: str  # "printwindow" | ""


class WindowsCapture:
    """Windows截图"""

    def capture(self, hwnd: int) -> CaptureResult:
        """截图主入口"""
        return self._capture_by_printwindow(hwnd)

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

            # 调试日志
            print(f"[DEBUG] Virtual: ({virtual_width}, {virtual_height}), SystemDPI={system_dpi}, WindowDPI={window_dpi}, Scale={scale_factor:.2f}, RenderSize: ({width}, {height})")

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
                    error="PrintWindow 调用失败",
                    method=""
                )

        except Exception as e:
            return CaptureResult(
                success=False,
                image=None,
                error=f"截图异常: {str(e)}",
                method=""
            )


# 全局截图实例
windows_capture = WindowsCapture()

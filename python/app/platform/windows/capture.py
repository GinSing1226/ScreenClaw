"""
Windows截图实现
使用 PrintWindow + WinRT Graphics Capture 双重方案
"""
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple
from dataclasses import dataclass

# 延迟导入 Pillow，避免启动时加载
PIL_AVAILABLE = True
try:
    from PIL import Image
except ImportError:
    PIL_AVAILABLE = False


@dataclass
class CaptureResult:
    """截图结果"""
    success: bool
    image: Optional['Image.Image']
    error: Optional[str]
    method: str  # "printwindow" | "winrt" | ""


class WindowsCapture:
    """Windows截图"""

    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.gdi32 = ctypes.windll.gdi32

    def capture(self, hwnd: int) -> CaptureResult:
        """截图主入口"""
        # 方案1: PrintWindow
        result = self._capture_by_printwindow(hwnd)
        if result.success and result.image is not None:
            if not self._is_black_image(result.image):
                result.method = "printwindow"
                return result

        # 方案2: WinRT Graphics Capture (TODO: 需要安装winsdk)
        # result = self._capture_by_winrt(hwnd)
        # if result.success:
        #     result.method = "winrt"
        #     return result

        # 暂时只支持PrintWindow
        if result.success:
            result.method = "printwindow"
            return result

        return CaptureResult(
            success=False,
            image=None,
            error=result.error or "截图失败：所有方案均不可用",
            method=""
        )

    def _capture_by_printwindow(self, hwnd: int) -> CaptureResult:
        """使用PrintWindow截图"""
        if not PIL_AVAILABLE:
            return CaptureResult(
                success=False,
                image=None,
                error="Pillow库未安装",
                method=""
            )

        try:
            # 获取窗口尺寸
            rect = wintypes.RECT()
            if not self.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return CaptureResult(
                    success=False,
                    image=None,
                    error="获取窗口尺寸失败",
                    method=""
                )

            width = rect.right - rect.left
            height = rect.bottom - rect.top

            if width <= 0 or height <= 0:
                return CaptureResult(
                    success=False,
                    image=None,
                    error="窗口尺寸无效",
                    method=""
                )

            # 获取窗口DC
            hwnd_dc = self.user32.GetWindowDC(hwnd)
            if not hwnd_dc:
                return CaptureResult(
                    success=False,
                    image=None,
                    error="获取窗口DC失败",
                    method=""
                )

            try:
                # 创建兼容DC
                mem_dc = self.gdi32.CreateCompatibleDC(hwnd_dc)
                if not mem_dc:
                    self.user32.ReleaseDC(hwnd, hwnd_dc)
                    return CaptureResult(
                        success=False,
                        image=None,
                        error="创建内存DC失败",
                        method=""
                    )

                try:
                    # 创建位图
                    bitmap = self.gdi32.CreateCompatibleBitmap(hwnd_dc, width, height)
                    if not bitmap:
                        # 释放已创建的资源
                        self.gdi32.DeleteDC(mem_dc)
                        self.user32.ReleaseDC(hwnd, hwnd_dc)
                        return CaptureResult(
                            success=False,
                            image=None,
                            error="创建位图失败",
                            method=""
                        )

                    try:
                        # 选入位图
                        old_bitmap = self.gdi32.SelectObject(mem_dc, bitmap)

                        # PrintWindow
                        # PW_CLIENTONLY = 1, PW_RENDERFULLCONTENT = 2
                        result = self.user32.PrintWindow(hwnd, mem_dc, 2)

                        if not result:
                            # 释放资源
                            self.gdi32.SelectObject(mem_dc, old_bitmap)
                            self.gdi32.DeleteObject(bitmap)
                            self.gdi32.DeleteDC(mem_dc)
                            self.user32.ReleaseDC(hwnd, hwnd_dc)
                            return CaptureResult(
                                success=False,
                                image=None,
                                error="PrintWindow调用失败",
                                method=""
                            )

                        # 获取位图数据
                        image = self._bitmap_to_image(bitmap, width, height)

                        # 恢复旧位图
                        self.gdi32.SelectObject(mem_dc, old_bitmap)

                        # 释放资源
                        self.gdi32.DeleteObject(bitmap)
                        self.gdi32.DeleteDC(mem_dc)
                        self.user32.ReleaseDC(hwnd, hwnd_dc)

                        return CaptureResult(
                            success=True,
                            image=image,
                            error=None,
                            method="printwindow"
                        )

                    except Exception as e:
                        # 异常时确保资源释放
                        self.gdi32.DeleteObject(bitmap)
                        raise

                finally:
                    # 确保mem_dc被释放
                    pass  # 已在上方处理

            finally:
                self.user32.ReleaseDC(hwnd, hwnd_dc)

        except Exception as e:
            return CaptureResult(
                success=False,
                image=None,
                error=f"截图异常: {str(e)}",
                method=""
            )

    def _bitmap_to_image(self, bitmap: int, width: int, height: int) -> Optional['Image.Image']:
        """将位图转换为Pillow Image"""
        from PIL import Image

        # 定义BITMAPINFO结构
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize", wintypes.DWORD),
                ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD),
                ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG),
                ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD),
            ]

        class BITMAPINFO(ctypes.Structure):
            _fields_ = [
                ("bmiHeader", BITMAPINFOHEADER),
                ("bmiColors", wintypes.DWORD * 3),
            ]

        # 设置BITMAPINFO
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  # 负值表示从上到下
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0  # BI_RGB

        # 分配缓冲区
        buffer_size = width * height * 4
        buffer = ctypes.create_string_buffer(buffer_size)

        # 获取位图数据
        hdc = self.gdi32.GetDC(None)
        try:
            result = self.gdi32.GetDIBits(
                hdc,
                bitmap,
                0,
                height,
                buffer,
                ctypes.byref(bmi),
                0  # DIB_RGB_COLORS
            )

            if not result:
                return None

            # 转换为Pillow Image
            # BGRA -> RGBA
            import numpy as np
            arr = np.frombuffer(buffer.raw, dtype=np.uint8)
            arr = arr.reshape((height, width, 4))
            # BGRA to RGBA
            arr = arr[:, :, [2, 1, 0, 3]]

            return Image.fromarray(arr, 'RGBA')

        finally:
            self.gdi32.ReleaseDC(None, hdc)

    def _is_black_image(self, image: 'Image.Image') -> bool:
        """检测图片是否为黑屏"""
        try:
            import numpy as np
            # 转换为灰度
            gray = image.convert('L')
            arr = np.array(gray)
            # 如果平均像素值过低，认为是黑屏
            return arr.mean() < 5
        except Exception:
            return False

    def _capture_by_winrt(self, hwnd: int) -> CaptureResult:
        """使用WinRT Graphics Capture截图"""
        # TODO: 实现WinRT截图
        # 需要安装 winsdk 库
        return CaptureResult(
            success=False,
            image=None,
            error="WinRT截图尚未实现",
            method=""
        )


# 全局截图实例
windows_capture = WindowsCapture()

"""
截图模块 - 支持 Windows.Graphics.Capture 和传统方式
"""
import win32gui
import win32ui
import win32con
import win32api
import ctypes
from ctypes import windll, c_void_p, c_int, byref
from dataclasses import dataclass
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
from datetime import datetime

# PrintWindow 标志
PW_CLIENTONLY = 0x1
PW_RENDERFULLCONTENT = 0x2


@dataclass
class GridConfig:
    """网格配置"""
    interval: float = 0.1          # 网格间隔（百分比，0.1 = 10%）
    line_color: tuple = (255, 0, 0, 128)    # 网格线颜色 RGBA
    text_color: tuple = (255, 255, 0, 200)  # 文字颜色 RGBA
    text_size: int = 12            # 文字大小
    line_width: int = 1            # 线宽
    show_grid: bool = True         # 是否显示网格线
    show_labels: bool = True       # 是否显示标签


class ScreenCapture:
    """屏幕截图器"""

    def __init__(self, hwnd: int, output_dir: str = "data"):
        """
        初始化截图器

        Args:
            hwnd: 目标窗口句柄
            output_dir: 输出目录
        """
        self.hwnd = hwnd
        self.output_dir = output_dir
        self._width = 0
        self._height = 0
        self._update_size()

        # Windows.Graphics.Capture 相关
        self._capture_session = None
        self._frame_pool = None
        self._d3d_device = None

        os.makedirs(output_dir, exist_ok=True)

    def _update_size(self):
        """更新窗口尺寸"""
        rect = win32gui.GetWindowRect(self.hwnd)
        self._width = rect[2] - rect[0]
        self._height = rect[3] - rect[1]

    @property
    def size(self) -> Tuple[int, int]:
        """返回窗口尺寸 (width, height)"""
        self._update_size()
        return self._width, self._height

    def capture_bitblt(self) -> Optional[Image.Image]:
        """
        使用 BitBlt 方式截图（传统方式，兼容性最好）

        Returns:
            PIL Image 对象，失败返回 None
        """
        try:
            self._update_size()
            width, height = self._width, self._height

            # 获取窗口 DC
            hwnd_dc = win32gui.GetWindowDC(self.hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            # 创建位图
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)

            # BitBlt 拷贝
            result = save_dc.BitBlt(
                (0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY
            )

            if result:
                # 转换为 PIL Image
                bmpinfo = save_bitmap.GetInfo()
                bmpstr = save_bitmap.GetBitmapBits(True)
                img = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1
                )

                # 清理资源
                win32gui.DeleteObject(save_bitmap.GetHandle())
                save_dc.DeleteDC()
                mfc_dc.DeleteDC()
                win32gui.ReleaseDC(self.hwnd, hwnd_dc)

                return img

        except Exception as e:
            print(f"BitBlt 截图失败: {e}")

        return None

    def capture_printwindow(self, flags: int = 2) -> Optional[Image.Image]:
        """
        使用 PrintWindow 方式截图（支持后台截图）

        Args:
            flags: PrintWindow 标志
                   0 = PW_CLIENTONLY
                   2 = PW_RENDERFULLCONTENT (Windows 8.1+)

        Returns:
            PIL Image 对象，失败返回 None
        """
        try:
            self._update_size()
            width, height = self._width, self._height

            # 获取窗口 DC
            hwnd_dc = win32gui.GetWindowDC(self.hwnd)

            # 创建兼容的内存 DC
            mem_dc = windll.gdi32.CreateCompatibleDC(hwnd_dc)

            # 创建 DIB 位图（重要：PrintWindow 需要 DIB 位图）
            # BITMAPINFOHEADER
            bmi = ctypes.create_string_buffer(40)
            ctypes.memset(bmi, 0, 40)
            header_size = ctypes.sizeof(ctypes.c_int32) * 10
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
                print("创建 DIB 位图失败")
                windll.gdi32.DeleteDC(mem_dc)
                win32gui.ReleaseDC(self.hwnd, hwnd_dc)
                return None

            # 选入位图
            old_bitmap = windll.gdi32.SelectObject(mem_dc, hbitmap)

            # 调用 PrintWindow (使用 ctypes)
            # BOOL PrintWindow(HWND hwnd, HDC hdcBlt, int nFlags)
            result = windll.user32.PrintWindow(self.hwnd, mem_dc, flags)

            if result:
                # 从 DIB 位图读取像素数据
                pixel_count = width * height
                buffer_size = pixel_count * 4  # BGRA 4 bytes per pixel
                pixel_buffer = ctypes.create_string_buffer(buffer_size)
                ctypes.memmove(pixel_buffer, pbits, buffer_size)

                # 转换为 numpy 数组 (BGRA -> RGBA)
                arr = np.frombuffer(pixel_buffer.raw, dtype=np.uint8)
                arr = arr.reshape((height, width, 4))
                # BGRA -> RGBA
                arr = arr[:, :, [2, 1, 0, 3]]
                # 转为 RGB
                arr = arr[:, :, :3]

                img = Image.fromarray(arr, 'RGB')
            else:
                print(f"PrintWindow 返回失败 (错误码: {ctypes.get_last_error()})")
                img = None

            # 清理资源
            windll.gdi32.SelectObject(mem_dc, old_bitmap)
            windll.gdi32.DeleteObject(hbitmap)
            windll.gdi32.DeleteDC(mem_dc)
            win32gui.ReleaseDC(self.hwnd, hwnd_dc)

            return img

        except Exception as e:
            print(f"PrintWindow 截图失败: {e}")
            import traceback
            traceback.print_exc()

        return None

    def capture_wgc(self) -> Optional[Image.Image]:
        """
        使用 Windows.Graphics.Capture 方式截图（最现代的方式）

        注意：需要 winsdk 库支持，且需要 Windows 10 1903+

        Returns:
            PIL Image 对象，失败返回 None
        """
        if not WSDK_AVAILABLE:
            print("winsdk 库不可用，无法使用 Windows.Graphics.Capture")
            return None

        try:
            # TODO: 实现 WGC 截图
            # 这需要创建 D3D11 设备、CaptureSession 等
            # 实现较复杂，作为高级功能
            raise NotImplementedError("Windows.Graphics.Capture 尚未实现")

        except Exception as e:
            print(f"Windows.Graphics.Capture 截图失败: {e}")

        return None

    def capture(self, method: str = 'auto') -> Optional[Image.Image]:
        """
        截图（自动选择最佳方法）

        Args:
            method: 截图方法 'auto', 'bitblt', 'printwindow', 'wgc'

        Returns:
            PIL Image 对象，失败返回 None
        """
        if method == 'auto':
            # 优先尝试 PrintWindow（支持后台）
            img = self.capture_printwindow()
            if img:
                return img

            # 回退到 BitBlt
            return self.capture_bitblt()

        elif method == 'printwindow':
            return self.capture_printwindow()

        elif method == 'bitblt':
            return self.capture_bitblt()

        elif method == 'wgc':
            return self.capture_wgc()

        return None

    def save_capture(self, img: Image.Image, filename: Optional[str] = None) -> str:
        """
        保存截图到文件

        Args:
            img: PIL Image 对象
            filename: 文件名，不指定则自动生成

        Returns:
            保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"screenshot_{timestamp}.png"

        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath)
        return filepath


class GridOverlay:
    """网格叠加器"""

    def __init__(self, config: Optional[GridConfig] = None):
        self.config = config or GridConfig()

    def apply_grid(self, img: Image.Image) -> Image.Image:
        """
        在图片上叠加网格

        Args:
            img: 原始图片

        Returns:
            叠加网格后的图片
        """
        if not self.config.show_grid and not self.config.show_labels:
            return img

        # 转换为 RGBA 模式以支持透明度
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # 创建透明层
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        width, height = img.size
        interval = self.config.interval

        # 尝试加载字体
        try:
            font = ImageFont.truetype("arial.ttf", self.config.text_size)
        except:
            font = ImageFont.load_default()

        # 绘制网格线
        if self.config.show_grid:
            # 垂直线
            x = interval
            while x < 1.0:
                px = int(x * width)
                draw.line([(px, 0), (px, height)], fill=self.config.line_color, width=self.config.line_width)
                x += interval

            # 水平线
            y = interval
            while y < 1.0:
                py = int(y * height)
                draw.line([(0, py), (width, py)], fill=self.config.line_color, width=self.config.line_width)
                y += interval

        # 绘制标签
        if self.config.show_labels:
            y_pct = interval
            while y_pct < 1.0:
                x_pct = interval
                while x_pct < 1.0:
                    px = int(x_pct * width)
                    py = int(y_pct * height)

                    # 标签格式: (0.5, 0.5)
                    label = f"({x_pct:.1f},{y_pct:.1f})"
                    draw.text((px + 3, py + 3), label, fill=self.config.text_color, font=font)

                    x_pct += interval
                y_pct += interval

        # 合并图层
        result = Image.alpha_composite(img, overlay)
        return result

    def set_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)


def test_capture(hwnd: int):
    """测试截图功能"""
    capture = ScreenCapture(hwnd)
    print(f"窗口尺寸: {capture.size}")

    print("\n测试 BitBlt 截图...")
    img = capture.capture_bitblt()
    if img:
        path = capture.save_capture(img, "test_bitblt.png")
        print(f"  成功! 保存到: {path}")
    else:
        print("  失败!")

    print("\n测试 PrintWindow 截图...")
    img = capture.capture_printwindow()
    if img:
        path = capture.save_capture(img, "test_printwindow.png")
        print(f"  成功! 保存到: {path}")
    else:
        print("  失败!")

    print("\n测试网格叠加...")
    if img:
        overlay = GridOverlay()
        grid_img = overlay.apply_grid(img)
        path = capture.save_capture(grid_img, "test_grid.png")
        print(f"  成功! 保存到: {path}")


if __name__ == '__main__':
    # 测试：列出窗口并截取
    from window_manager import WindowManager

    mgr = WindowManager()
    windows = mgr.enum_all_windows()

    print("可见窗口列表:")
    for i, win in enumerate(windows[:10]):
        print(f"[{i}] {win.title[:40]:40s} | {win.class_name}")

    idx = int(input("\n选择窗口序号: "))
    if 0 <= idx < len(windows):
        test_capture(windows[idx].hwnd)

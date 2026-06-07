"""
桌面级截图捕获测试

契约定义（TDD Red Phase）：
- capture_monitor(monitor_index) → PIL.Image
  截取指定显示器的可见画面
- 截图后复用现有网格绘制管线（grid.py）

关键约束：
- mss.grab(monitors[index+1]) 截取指定显示器
- 返回 PIL.Image RGB 格式
- monitor_index 越界时抛出异常或返回错误
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock


# ============ 模拟显示器数据 ============

MOCK_MONITORS = [
    {"left": 0, "top": 0, "width": 4480, "height": 1440},     # 全屏拼合
    {"left": 0, "top": 0, "width": 1920, "height": 1080},     # 主显示器
    {"left": 1920, "top": 0, "width": 2560, "height": 1440},  # 副显示器
]


def _make_mock_grab_result(width, height):
    """创建模拟的 mss grab 返回结果"""
    mock_img = MagicMock()
    mock_img.size = (width, height)
    mock_img.bgra = b'\x00' * (width * height * 4)
    return mock_img


def _mock_mss_context():
    """创建模拟 mss 上下文管理器"""
    mock_sct = MagicMock()
    mock_sct.monitors = MOCK_MONITORS
    mock_sct.grab.return_value = _make_mock_grab_result(1920, 1080)

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_sct)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx


# ============ capture_monitor ============

class TestCaptureMonitor:
    """测试桌面截图捕获"""

    @patch('app.platform.windows.desktop_capture.mss')
    def test_returns_pil_image(self, mock_mss_module):
        """截图返回 PIL.Image 对象"""
        mock_mss_module.mss.return_value = _mock_mss_context()

        from app.platform.windows.desktop_capture import capture_monitor
        from PIL import Image

        result = capture_monitor(0)
        assert isinstance(result, Image.Image)

    @patch('app.platform.windows.desktop_capture.mss')
    def test_primary_monitor_capture(self, mock_mss_module):
        """截取主显示器（index=0）"""
        mock_mss_module.mss.return_value = _mock_mss_context()

        from app.platform.windows.desktop_capture import capture_monitor
        result = capture_monitor(0)

        # 应使用 monitors[1]（mss 中 index 0 对应 monitors[1]）
        mock_sct = mock_mss_module.mss.return_value.__enter__.return_value
        mock_sct.grab.assert_called_once_with(MOCK_MONITORS[1])

    @patch('app.platform.windows.desktop_capture.mss')
    def test_secondary_monitor_capture(self, mock_mss_module):
        """截取副显示器（index=1）"""
        mock_mss_module.mss.return_value = _mock_mss_context()

        from app.platform.windows.desktop_capture import capture_monitor
        result = capture_monitor(1)

        # 应使用 monitors[2]（mss 中 index 1 对应 monitors[2]）
        mock_sct = mock_mss_module.mss.return_value.__enter__.return_value
        mock_sct.grab.assert_called_once_with(MOCK_MONITORS[2])

    @patch('app.platform.windows.desktop_capture.mss')
    def test_invalid_monitor_index(self, mock_mss_module):
        """monitor_index 越界时抛出异常"""
        mock_mss_module.mss.return_value = _mock_mss_context()

        from app.platform.windows.desktop_capture import capture_monitor

        with pytest.raises((IndexError, ValueError)):
            capture_monitor(99)

    @patch('app.platform.windows.desktop_capture.mss')
    def test_image_rgb_mode(self, mock_mss_module):
        """返回的图片是 RGB 模式"""
        mock_mss_module.mss.return_value = _mock_mss_context()

        from app.platform.windows.desktop_capture import capture_monitor
        result = capture_monitor(0)

        assert result.mode == "RGB"

    @patch('app.platform.windows.desktop_capture.mss')
    def test_image_dimensions(self, mock_mss_module):
        """返回的图片尺寸与显示器分辨率一致"""
        mock_mss_module.mss.return_value = _mock_mss_context()

        from app.platform.windows.desktop_capture import capture_monitor
        result = capture_monitor(0)

        assert result.size == (1920, 1080)

    @patch('app.platform.windows.desktop_capture.mss')
    def test_bgrx_to_rgb_conversion(self, mock_mss_module):
        """mss 返回 BGRX 格式，需转为 RGB"""
        # 构造一个 4x4 的简单图片验证颜色转换
        mock_sct = MagicMock()
        mock_sct.monitors = MOCK_MONITORS

        # BGRX 数据：蓝色(255,0,0,X) 像素 × 4×4
        pixel = bytes([0, 0, 255, 0])  # BGRX: Blue=0, Green=0, Red=255 → RGB: (255, 0, 0)
        mock_img = MagicMock()
        mock_img.size = (4, 4)
        mock_img.bgra = pixel * 16  # 16 pixels
        mock_sct.grab.return_value = mock_img

        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_sct)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_mss_module.mss.return_value = mock_ctx

        from app.platform.windows.desktop_capture import capture_monitor
        result = capture_monitor(0)

        # 验证第一个像素是 (255, 0, 0) in RGB
        pixel_rgb = result.getpixel((0, 0))
        assert pixel_rgb[0] == 255  # R
        assert pixel_rgb[1] == 0    # G
        assert pixel_rgb[2] == 0    # B

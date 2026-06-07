"""
桌面级坐标转换测试

契约定义（TDD Red Phase）：
- desktop_percent_to_screen(monitor_index, x_pct, y_pct) → (screen_x, screen_y)
  将桌面百分比坐标转换为屏幕绝对像素坐标
- get_monitors() → list[DesktopMonitorInfo]
  枚举所有显示器

关键约束：
- 坐标系：每个显示器独立，(0,0) 为显示器左上角，(100,100) 为右下角
- 多显示器：屏幕绝对坐标 = 显示器偏移 + 百分比 × 显示器分辨率
- 主显示器：left=0, top=0
- mss.monitors[0] 是全屏拼合，[1:] 是各显示器
"""
import pytest
from unittest.mock import patch, MagicMock


# ============ 模拟显示器数据 ============

MOCK_MONITORS = [
    # [0]: 全屏拼合（mss 内部格式，不直接暴露）
    {"left": 0, "top": 0, "width": 4480, "height": 1440},
    # [1]: 主显示器 1920x1080
    {"left": 0, "top": 0, "width": 1920, "height": 1080},
    # [2]: 副显示器 2560x1440
    {"left": 1920, "top": 0, "width": 2560, "height": 1440},
]


def _mock_mss():
    """创建模拟的 mss 上下文管理器"""
    mock_sct = MagicMock()
    mock_sct.monitors = MOCK_MONITORS

    # 模拟 grab 返回值
    mock_img = MagicMock()
    mock_img.size = (1920, 1080)
    # BGRX 格式的原始数据
    mock_img.bgra = b'\x00' * (1920 * 1080 * 4)
    mock_sct.grab.return_value = mock_img

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_sct)
    mock_ctx.__exit__ = MagicMock(return_value=False)
    return mock_ctx


# ============ desktop_percent_to_screen ============

class TestDesktopPercentToScreen:
    """测试桌面百分比坐标 → 屏幕绝对像素坐标转换"""

    @patch('app.platform.windows.desktop_capture.mss')
    def test_primary_monitor_center(self, mock_mss_module):
        """主显示器中心点 (50, 50) → 屏幕坐标 (960, 540)"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import desktop_percent_to_screen
        screen_x, screen_y = desktop_percent_to_screen(0, 50, 50)

        assert screen_x == 960    # 0 + 1920 * 50/100
        assert screen_y == 540    # 0 + 1080 * 50/100

    @patch('app.platform.windows.desktop_capture.mss')
    def test_primary_monitor_top_left(self, mock_mss_module):
        """主显示器左上角 (0, 0) → 屏幕坐标 (0, 0)"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import desktop_percent_to_screen
        screen_x, screen_y = desktop_percent_to_screen(0, 0, 0)

        assert screen_x == 0
        assert screen_y == 0

    @patch('app.platform.windows.desktop_capture.mss')
    def test_primary_monitor_bottom_right(self, mock_mss_module):
        """主显示器右下角 (100, 100) → 屏幕坐标 (1920, 1080)"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import desktop_percent_to_screen
        screen_x, screen_y = desktop_percent_to_screen(0, 100, 100)

        assert screen_x == 1920
        assert screen_y == 1080

    @patch('app.platform.windows.desktop_capture.mss')
    def test_secondary_monitor_center(self, mock_mss_module):
        """副显示器中心点 (50, 50) → 屏幕坐标 (3200, 720)
        副屏偏移 left=1920, 宽2560, 高1440"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import desktop_percent_to_screen
        screen_x, screen_y = desktop_percent_to_screen(1, 50, 50)

        assert screen_x == 3200   # 1920 + 2560 * 50/100
        assert screen_y == 720    # 0 + 1440 * 50/100

    @patch('app.platform.windows.desktop_capture.mss')
    def test_secondary_monitor_top_left(self, mock_mss_module):
        """副显示器左上角 (0, 0) → 屏幕坐标 (1920, 0)"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import desktop_percent_to_screen
        screen_x, screen_y = desktop_percent_to_screen(1, 0, 0)

        assert screen_x == 1920
        assert screen_y == 0

    @patch('app.platform.windows.desktop_capture.mss')
    def test_secondary_monitor_bottom_right(self, mock_mss_module):
        """副显示器右下角 (100, 100) → 屏幕坐标 (4480, 1440)"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import desktop_percent_to_screen
        screen_x, screen_y = desktop_percent_to_screen(1, 100, 100)

        assert screen_x == 4480   # 1920 + 2560
        assert screen_y == 1440   # 0 + 1440

    @patch('app.platform.windows.desktop_capture.mss')
    def test_fractional_coordinates(self, mock_mss_module):
        """小数坐标精确换算"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import desktop_percent_to_screen
        screen_x, screen_y = desktop_percent_to_screen(0, 25.5, 33.3)

        # 0 + 1920 * 25.5 / 100 = 489.6 → int(489.6) = 489
        assert screen_x == int(1920 * 25.5 / 100)
        assert screen_y == int(1080 * 33.3 / 100)


# ============ get_monitors ============

class TestGetMonitors:
    """测试显示器枚举"""

    @patch('app.platform.windows.desktop_capture.mss')
    def test_returns_list(self, mock_mss_module):
        """返回显示器列表"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import get_monitors
        monitors = get_monitors()

        assert isinstance(monitors, list)

    @patch('app.platform.windows.desktop_capture.mss')
    def test_correct_count(self, mock_mss_module):
        """返回正确的显示器数量（不含全屏拼合项）"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import get_monitors
        monitors = get_monitors()

        # MOCK_MONITORS 有 3 项（1 拼合 + 2 显示器），应返回 2 个
        assert len(monitors) == 2

    @patch('app.platform.windows.desktop_capture.mss')
    def test_primary_monitor_flag(self, mock_mss_module):
        """主显示器 is_primary=True，副显示器 is_primary=False"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import get_monitors
        monitors = get_monitors()

        assert monitors[0]["is_primary"] is True
        assert monitors[1]["is_primary"] is False

    @patch('app.platform.windows.desktop_capture.mss')
    def test_monitor_index_starts_from_zero(self, mock_mss_module):
        """显示器索引从 0 开始"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import get_monitors
        monitors = get_monitors()

        assert monitors[0]["index"] == 0
        assert monitors[1]["index"] == 1

    @patch('app.platform.windows.desktop_capture.mss')
    def test_monitor_info_fields(self, mock_mss_module):
        """每个显示器包含必要字段"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import get_monitors
        monitors = get_monitors()
        mon = monitors[0]

        required_fields = ["index", "name", "resolution", "is_primary", "left", "top", "width", "height"]
        for field in required_fields:
            assert field in mon, f"缺少字段: {field}"

    @patch('app.platform.windows.desktop_capture.mss')
    def test_resolution_format(self, mock_mss_module):
        """resolution 格式为 WxH"""
        mock_mss_module.mss.return_value = _mock_mss()

        from app.platform.windows.desktop_capture import get_monitors
        monitors = get_monitors()

        assert monitors[0]["resolution"] == "1920x1080"
        assert monitors[1]["resolution"] == "2560x1440"

    @patch('app.platform.windows.desktop_capture.mss')
    def test_empty_monitors(self, mock_mss_module):
        """无显示器时返回空列表"""
        mock_sct = MagicMock()
        mock_sct.monitors = [{"left": 0, "top": 0, "width": 0, "height": 0}]  # 仅有拼合项
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_sct)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_mss_module.mss.return_value = mock_ctx

        from app.platform.windows.desktop_capture import get_monitors
        monitors = get_monitors()

        assert monitors == []

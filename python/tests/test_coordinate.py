"""
坐标转换单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from app.utils.coordinate import (
    percent_to_absolute,
    absolute_to_percent,
    client_to_screen,
    restore_window_and_calc_coords
)


class TestCoordinateConversion:
    """坐标转换测试"""

    def test_percent_to_absolute_center(self):
        """测试百分比转相对坐标 - 中心点"""
        client_rect = (0, 0, 1000, 800)

        x, y = percent_to_absolute(50, 50, client_rect)
        assert x == 500
        assert y == 400

    def test_percent_to_absolute_origin(self):
        """测试百分比转相对坐标 - 原点"""
        client_rect = (0, 0, 1000, 800)

        x, y = percent_to_absolute(0, 0, client_rect)
        assert x == 0
        assert y == 0

    def test_percent_to_absolute_max(self):
        """测试百分比转相对坐标 - 最大值"""
        client_rect = (0, 0, 1000, 800)

        x, y = percent_to_absolute(100, 100, client_rect)
        assert x == 1000
        assert y == 800

    def test_percent_to_absolute_with_offset(self):
        """测试百分比转相对坐标 - 带偏移的客户区"""
        # GetClientRect 返回的 always 是 (0, 0, width, height)
        client_rect = (0, 0, 1000, 800)

        x, y = percent_to_absolute(50, 50, client_rect)
        # 返回相对于客户区左上角的坐标
        assert x == 500  # width * 50% = 500
        assert y == 400  # height * 50% = 400

    def test_absolute_to_percent_center(self):
        """测试相对坐标转百分比 - 中心点"""
        client_rect = (0, 0, 1000, 800)

        x_pct, y_pct = absolute_to_percent(500, 400, client_rect)
        assert x_pct == 50.0
        assert y_pct == 50.0

    def test_absolute_to_percent_relative_coords(self):
        """测试相对坐标转百分比"""
        client_rect = (0, 0, 1000, 800)

        # 输入的是相对坐标（不需要加偏移）
        x_pct, y_pct = absolute_to_percent(500, 400, client_rect)
        assert x_pct == 50.0
        assert y_pct == 50.0

    def test_round_trip_conversion(self):
        """测试往返转换"""
        client_rect = (0, 0, 1000, 800)

        # 百分比 -> 相对坐标 -> 百分比
        original_pct = (33.3, 66.6)
        rel_x, rel_y = percent_to_absolute(*original_pct, client_rect)

        # 相对坐标转回百分比
        back_pct = absolute_to_percent(rel_x, rel_y, client_rect)

        # 允许小误差（因为浮点转换）
        assert abs(back_pct[0] - original_pct[0]) < 0.1
        assert abs(back_pct[1] - original_pct[1]) < 0.1

    def test_zero_size_window(self):
        """测试零尺寸窗口"""
        client_rect = (0, 0, 0, 0)  # 宽0，高0

        x_pct, y_pct = absolute_to_percent(100, 100, client_rect)
        assert x_pct == 0.0
        assert y_pct == 0.0

    @patch('app.utils.coordinate.win32gui.ClientToScreen')
    def test_client_to_screen(self, mock_client_to_screen):
        """测试客户区坐标转屏幕坐标"""
        mock_hwnd = 12345
        mock_client_to_screen.return_value = (1100, 1050)

        screen_x, screen_y = client_to_screen(mock_hwnd, 100, 50)

        mock_client_to_screen.assert_called_once_with(mock_hwnd, (100, 50))
        assert screen_x == 1100
        assert screen_y == 1050

    @pytest.mark.skip(reason="依赖 Windows API，适合集成测试环境")
    def test_restore_window_and_calc_coords_basic(self):
        """测试恢复窗口并计算坐标 - 基本情况

        此测试依赖 Windows API (ctypes, win32gui, process_service)，
        需要在真实的 Windows 环境中运行或使用复杂的 mock。
        建议在集成测试中验证此功能。
        """
        pass

    @pytest.mark.skip(reason="依赖 Windows API，适合集成测试环境")
    def test_restore_window_and_calc_coords_no_rect(self):
        """测试恢复窗口并计算坐标 - 窗口矩形获取失败

        此测试依赖 Windows API (ctypes, win32gui, process_service)，
        需要在真实的 Windows 环境中运行或使用复杂的 mock。
        建议在集成测试中验证此功能。
        """
        pass

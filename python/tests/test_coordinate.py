"""
坐标转换单元测试
"""
import pytest
from app.utils.coordinate import percent_to_absolute, absolute_to_percent


class TestCoordinateConversion:
    """坐标转换测试"""

    def test_percent_to_absolute_center(self):
        """测试百分比转绝对坐标 - 中心点"""
        window_rect = (0, 0, 1000, 800)

        x, y = percent_to_absolute(50, 50, window_rect)
        assert x == 500
        assert y == 400

    def test_percent_to_absolute_origin(self):
        """测试百分比转绝对坐标 - 原点"""
        window_rect = (0, 0, 1000, 800)

        x, y = percent_to_absolute(0, 0, window_rect)
        assert x == 0
        assert y == 0

    def test_percent_to_absolute_max(self):
        """测试百分比转绝对坐标 - 最大值"""
        window_rect = (0, 0, 1000, 800)

        x, y = percent_to_absolute(100, 100, window_rect)
        assert x == 1000
        assert y == 800

    def test_percent_to_absolute_with_offset(self):
        """测试百分比转绝对坐标 - 带偏移"""
        window_rect = (100, 50, 1100, 850)  # 宽1000，高800

        x, y = percent_to_absolute(50, 50, window_rect)
        assert x == 600  # 100 + 500
        assert y == 450  # 50 + 400

    def test_absolute_to_percent_center(self):
        """测试绝对坐标转百分比 - 中心点"""
        window_rect = (0, 0, 1000, 800)

        x_pct, y_pct = absolute_to_percent(500, 400, window_rect)
        assert x_pct == 50.0
        assert y_pct == 50.0

    def test_absolute_to_percent_with_offset(self):
        """测试绝对坐标转百分比 - 带偏移"""
        window_rect = (100, 50, 1100, 850)

        x_pct, y_pct = absolute_to_percent(600, 450, window_rect)
        assert x_pct == 50.0
        assert y_pct == 50.0

    def test_round_trip_conversion(self):
        """测试往返转换"""
        window_rect = (100, 200, 1100, 1000)  # 宽1000，高800

        # 百分比 -> 绝对 -> 百分比
        original_pct = (33.3, 66.6)
        abs_x, abs_y = percent_to_absolute(*original_pct, window_rect)
        back_pct = absolute_to_percent(abs_x, abs_y, window_rect)

        # 允许小误差（因为整数转换）
        assert abs(back_pct[0] - original_pct[0]) < 0.1
        assert abs(back_pct[1] - original_pct[1]) < 0.1

    def test_zero_size_window(self):
        """测试零尺寸窗口"""
        window_rect = (100, 100, 100, 100)  # 宽0，高0

        x_pct, y_pct = absolute_to_percent(100, 100, window_rect)
        assert x_pct == 0.0
        assert y_pct == 0.0

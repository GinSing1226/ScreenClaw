"""
桌面级操作请求模型测试

契约定义（TDD Red Phase）：
- DesktopBaseRequest：公共字段（monitor_index 必填）
- DesktopScreenshotRequest：截图请求，复用网格/标记参数
- DesktopClickRequest：单击请求
- DesktopDoubleClickRequest：双击请求
- DesktopRightClickRequest：右键请求
- DesktopDragRequest：拖拽请求，支持跨屏（start/end 各自指定 monitor_index）
- DesktopScrollRequest：滚动请求
- DesktopInputTextRequest：文本输入请求
- DesktopPressKeyRequest：按键请求
- DesktopHoverRequest：悬浮请求
- DesktopMonitorsRequest：显示器枚举请求

约束验证：
- monitor_index: int, 必填, >= 0
- x / y: float, 0-100
- 桌面操作无 action_method 参数
"""
import pytest
from pydantic import ValidationError


# ============ Helper ============

def _base_kwargs(**overrides):
    """桌面操作请求的公共参数"""
    kwargs = {
        "ai_app_type": "claude_code",
        "session_id": "test_session_001",
        "monitor_index": 0,
    }
    kwargs.update(overrides)
    return kwargs


# ============ DesktopBaseRequest ============

class TestDesktopBaseRequest:
    """测试桌面操作请求基类"""

    def test_monitor_index_required(self):
        """monitor_index 是必填字段"""
        from app.models.desktop_request import DesktopBaseRequest
        with pytest.raises(ValidationError, match="monitor_index"):
            DesktopBaseRequest(ai_app_type="claude_code", session_id="test")

    def test_monitor_index_negative_rejected(self):
        """monitor_index 不能为负数"""
        from app.models.desktop_request import DesktopBaseRequest
        with pytest.raises(ValidationError):
            DesktopBaseRequest(**_base_kwargs(monitor_index=-1))

    def test_monitor_index_zero_accepted(self):
        """monitor_index=0 表示主显示器，应该接受"""
        from app.models.desktop_request import DesktopBaseRequest
        req = DesktopBaseRequest(**_base_kwargs(monitor_index=0))
        assert req.monitor_index == 0

    def test_no_action_method_field(self):
        """桌面操作请求不应有 action_method 字段"""
        from app.models.desktop_request import DesktopBaseRequest
        req = DesktopBaseRequest(**_base_kwargs())
        assert not hasattr(req, "action_method")


# ============ DesktopScreenshotRequest ============

class TestDesktopScreenshotRequest:
    """测试桌面截图请求模型"""

    def test_minimal_valid_request(self):
        """最小合法请求：只有公共参数"""
        from app.models.desktop_request import DesktopScreenshotRequest
        req = DesktopScreenshotRequest(**_base_kwargs())
        assert req.monitor_index == 0
        assert req.coordinate_type == "grid"

    def test_coordinate_type_default_grid(self):
        """coordinate_type 默认为 grid"""
        from app.models.desktop_request import DesktopScreenshotRequest
        req = DesktopScreenshotRequest(**_base_kwargs())
        assert req.coordinate_type == "grid"

    def test_coordinate_type_no(self):
        """coordinate_type 可设为 no（不绘制网格）"""
        from app.models.desktop_request import DesktopScreenshotRequest
        req = DesktopScreenshotRequest(**_base_kwargs(coordinate_type="no"))
        assert req.coordinate_type == "no"

    def test_grid_params_optional(self):
        """grid 参数可选"""
        from app.models.desktop_request import DesktopScreenshotRequest
        req = DesktopScreenshotRequest(**_base_kwargs())
        assert req.grid is None

    def test_marker_params_optional(self):
        """marker 参数可选"""
        from app.models.desktop_request import DesktopScreenshotRequest
        req = DesktopScreenshotRequest(**_base_kwargs())
        assert req.marker is None

    def test_marker_single_object_normalized_to_list(self):
        """marker 传入单个对象时，自动转为列表"""
        from app.models.desktop_request import DesktopScreenshotRequest
        req = DesktopScreenshotRequest(**_base_kwargs(
            marker={"x": 50, "y": 30}
        ))
        assert isinstance(req.marker, list)
        assert len(req.marker) == 1

    def test_marker_list_accepted(self):
        """marker 传入列表时保持不变"""
        from app.models.desktop_request import DesktopScreenshotRequest
        req = DesktopScreenshotRequest(**_base_kwargs(
            marker=[{"x": 50, "y": 30}, {"x": 80, "y": 60}]
        ))
        assert isinstance(req.marker, list)
        assert len(req.marker) == 2

    def test_self_check_optional(self):
        """self_check 参数可选"""
        from app.models.desktop_request import DesktopScreenshotRequest
        req = DesktopScreenshotRequest(**_base_kwargs())
        assert req.self_check is None

    def test_color_mode_optional(self):
        """color_mode 参数可选"""
        from app.models.desktop_request import DesktopScreenshotRequest
        req = DesktopScreenshotRequest(**_base_kwargs())
        assert req.color_mode is None


# ============ DesktopClickRequest ============

class TestDesktopClickRequest:
    """测试桌面点击请求模型"""

    def test_valid_click(self):
        """合法点击请求"""
        from app.models.desktop_request import DesktopClickRequest
        req = DesktopClickRequest(**_base_kwargs(x=50, y=30))
        assert req.x == 50
        assert req.y == 30

    def test_x_y_required(self):
        """x 和 y 是必填字段"""
        from app.models.desktop_request import DesktopClickRequest
        with pytest.raises(ValidationError, match="x"):
            DesktopClickRequest(**_base_kwargs())

    def test_x_range_0_to_100(self):
        """x 坐标范围 0-100"""
        from app.models.desktop_request import DesktopClickRequest
        # 边界值合法
        DesktopClickRequest(**_base_kwargs(x=0, y=50))
        DesktopClickRequest(**_base_kwargs(x=100, y=50))
        # 超出范围非法
        with pytest.raises(ValidationError):
            DesktopClickRequest(**_base_kwargs(x=-1, y=50))
        with pytest.raises(ValidationError):
            DesktopClickRequest(**_base_kwargs(x=101, y=50))

    def test_y_range_0_to_100(self):
        """y 坐标范围 0-100"""
        from app.models.desktop_request import DesktopClickRequest
        DesktopClickRequest(**_base_kwargs(x=50, y=0))
        DesktopClickRequest(**_base_kwargs(x=50, y=100))
        with pytest.raises(ValidationError):
            DesktopClickRequest(**_base_kwargs(x=50, y=-1))
        with pytest.raises(ValidationError):
            DesktopClickRequest(**_base_kwargs(x=50, y=101))

    def test_no_action_method(self):
        """点击请求不应有 action_method 字段"""
        from app.models.desktop_request import DesktopClickRequest
        req = DesktopClickRequest(**_base_kwargs(x=50, y=50))
        assert not hasattr(req, "action_method")


# ============ DesktopDoubleClickRequest ============

class TestDesktopDoubleClickRequest:
    """测试桌面双击请求模型"""

    def test_valid_double_click(self):
        """合法双击请求"""
        from app.models.desktop_request import DesktopDoubleClickRequest
        req = DesktopDoubleClickRequest(**_base_kwargs(x=50, y=50))
        assert req.x == 50

    def test_inherits_click_fields(self):
        """双击请求与点击请求字段一致"""
        from app.models.desktop_request import DesktopDoubleClickRequest
        req = DesktopDoubleClickRequest(**_base_kwargs(x=25.5, y=75.3))
        assert req.x == 25.5
        assert req.y == 75.3


# ============ DesktopRightClickRequest ============

class TestDesktopRightClickRequest:
    """测试桌面右键请求模型"""

    def test_valid_right_click(self):
        """合法右键请求"""
        from app.models.desktop_request import DesktopRightClickRequest
        req = DesktopRightClickRequest(**_base_kwargs(x=50, y=50))
        assert req.x == 50


# ============ DesktopDragRequest ============

class TestDesktopDragRequest:
    """测试桌面拖拽请求模型"""

    def test_same_monitor_drag(self):
        """同屏拖拽：起终点在同一显示器"""
        from app.models.desktop_request import DesktopDragRequest
        req = DesktopDragRequest(
            **_base_kwargs(
                start_x=20, start_y=50,
                end_x=80, end_y=50,
                end_monitor_index=0,
            )
        )
        assert req.start_x == 20
        assert req.end_x == 80
        assert req.monitor_index == 0
        assert req.end_monitor_index == 0

    def test_cross_monitor_drag(self):
        """跨屏拖拽：起终点在不同显示器"""
        from app.models.desktop_request import DesktopDragRequest
        req = DesktopDragRequest(
            **_base_kwargs(
                start_x=80, start_y=50,
                end_x=20, end_y=50,
                end_monitor_index=1,
            )
        )
        assert req.monitor_index == 0
        assert req.end_monitor_index == 1

    def test_end_monitor_index_required(self):
        """end_monitor_index 是必填字段"""
        from app.models.desktop_request import DesktopDragRequest
        with pytest.raises(ValidationError, match="end_monitor_index"):
            DesktopDragRequest(
                **_base_kwargs(start_x=20, start_y=50, end_x=80, end_y=50)
            )

    def test_start_coordinates_range(self):
        """起点坐标范围 0-100"""
        from app.models.desktop_request import DesktopDragRequest
        with pytest.raises(ValidationError):
            DesktopDragRequest(**_base_kwargs(
                start_x=-1, start_y=50, end_x=80, end_y=50, end_monitor_index=0
            ))

    def test_end_coordinates_range(self):
        """终点坐标范围 0-100"""
        from app.models.desktop_request import DesktopDragRequest
        with pytest.raises(ValidationError):
            DesktopDragRequest(**_base_kwargs(
                start_x=50, start_y=50, end_x=101, end_y=50, end_monitor_index=0
            ))

    def test_duration_ms_default(self):
        """拖拽时长默认 500ms"""
        from app.models.desktop_request import DesktopDragRequest
        req = DesktopDragRequest(**_base_kwargs(
            start_x=20, start_y=50, end_x=80, end_y=50, end_monitor_index=0
        ))
        assert req.duration_ms == 500

    def test_duration_ms_minimum(self):
        """拖拽时长最小 50ms"""
        from app.models.desktop_request import DesktopDragRequest
        with pytest.raises(ValidationError):
            DesktopDragRequest(**_base_kwargs(
                start_x=20, start_y=50, end_x=80, end_y=50,
                end_monitor_index=0, duration_ms=10
            ))


# ============ DesktopScrollRequest ============

class TestDesktopScrollRequest:
    """测试桌面滚动请求模型"""

    def test_valid_scroll(self):
        """合法滚动请求"""
        from app.models.desktop_request import DesktopScrollRequest
        req = DesktopScrollRequest(**_base_kwargs(x=50, y=50, delta=-3))
        assert req.delta == -3

    def test_positive_delta(self):
        """正值 delta 向上滚动"""
        from app.models.desktop_request import DesktopScrollRequest
        req = DesktopScrollRequest(**_base_kwargs(x=50, y=50, delta=3))
        assert req.delta == 3

    def test_negative_delta(self):
        """负值 delta 向下滚动"""
        from app.models.desktop_request import DesktopScrollRequest
        req = DesktopScrollRequest(**_base_kwargs(x=50, y=50, delta=-5))
        assert req.delta == -5


# ============ DesktopInputTextRequest ============

class TestDesktopInputTextRequest:
    """测试桌面文本输入请求模型"""

    def test_valid_input_text(self):
        """合法文本输入请求"""
        from app.models.desktop_request import DesktopInputTextRequest
        req = DesktopInputTextRequest(**_base_kwargs(x=50, y=50, text="hello"))
        assert req.text == "hello"

    def test_text_required(self):
        """text 是必填字段"""
        from app.models.desktop_request import DesktopInputTextRequest
        with pytest.raises(ValidationError, match="text"):
            DesktopInputTextRequest(**_base_kwargs(x=50, y=50))

    def test_text_with_newline(self):
        """text 支持换行符"""
        from app.models.desktop_request import DesktopInputTextRequest
        req = DesktopInputTextRequest(**_base_kwargs(x=50, y=50, text="line1\nline2"))
        assert "\n" in req.text


# ============ DesktopPressKeyRequest ============

class TestDesktopPressKeyRequest:
    """测试桌面按键请求模型"""

    def test_valid_press_key(self):
        """合法按键请求"""
        from app.models.desktop_request import DesktopPressKeyRequest
        req = DesktopPressKeyRequest(**_base_kwargs(keys="ctrl c"))
        assert req.keys == "ctrl c"

    def test_keys_required(self):
        """keys 是必填字段"""
        from app.models.desktop_request import DesktopPressKeyRequest
        with pytest.raises(ValidationError, match="keys"):
            DesktopPressKeyRequest(**_base_kwargs())

    def test_combination_keys(self):
        """组合键支持空格分隔"""
        from app.models.desktop_request import DesktopPressKeyRequest
        req = DesktopPressKeyRequest(**_base_kwargs(keys="ctrl shift s"))
        assert req.keys == "ctrl shift s"

    def test_duration_ms_default_zero(self):
        """按住时长默认为 0（立即释放）"""
        from app.models.desktop_request import DesktopPressKeyRequest
        req = DesktopPressKeyRequest(**_base_kwargs(keys="enter"))
        assert req.duration_ms == 0

    def test_single_key(self):
        """单键请求"""
        from app.models.desktop_request import DesktopPressKeyRequest
        req = DesktopPressKeyRequest(**_base_kwargs(keys="win"))
        assert req.keys == "win"


# ============ DesktopHoverRequest ============

class TestDesktopHoverRequest:
    """测试桌面悬浮请求模型"""

    def test_valid_hover(self):
        """合法悬浮请求"""
        from app.models.desktop_request import DesktopHoverRequest
        req = DesktopHoverRequest(**_base_kwargs(x=50, y=50))
        assert req.x == 50

    def test_duration_ms_default(self):
        """悬浮时长默认 1000ms"""
        from app.models.desktop_request import DesktopHoverRequest
        req = DesktopHoverRequest(**_base_kwargs(x=50, y=50))
        assert req.duration_ms == 1000

    def test_duration_ms_custom(self):
        """可自定义悬浮时长"""
        from app.models.desktop_request import DesktopHoverRequest
        req = DesktopHoverRequest(**_base_kwargs(x=50, y=50, duration_ms=3000))
        assert req.duration_ms == 3000

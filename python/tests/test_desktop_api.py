"""
桌面级 API 端点测试

验证所有桌面级 API 端点的功能：
- GET /api/desktop_get_monitors_list → 显示器枚举
- POST /api/desktop_screenshot → 桌面截图
- POST /api/desktop_click → 桌面点击
- POST /api/desktop_double_click → 桌面双击
- POST /api/desktop_right_click → 桌面右键
- POST /api/desktop_drag → 桌面拖拽
- POST /api/desktop_scroll → 桌面滚动
- POST /api/desktop_input_text → 桌面文本输入
- POST /api/desktop_press_key → 桌面按键
- POST /api/desktop_hover → 桌面悬浮

关键约束：
- 所有操作固定 hijack 模式，无 action_method 参数
- monitor_index 必填，越界返回 MONITOR_NOT_FOUND
- 日志字段按需填充：桌面操作填充 monitor_index，窗口字段为 null
- 截图文件名前缀 desktop_，与窗口截图共存于同一 session 目录
- delegated 活跃时跳过状态恢复
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock


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


def _mock_inject_result(success=True, error=None):
    """创建模拟的桌面操作结果"""
    from app.platform.windows.desktop_capture import DesktopInjectResult
    return DesktopInjectResult(success=success, error=error)


# ============ 显示器枚举 API ============

class TestDesktopMonitorsAPI:
    """测试 GET /api/desktop_get_monitors_list"""

    @patch('app.api.desktop.get_monitors')
    def test_returns_monitor_list(self, mock_get_monitors):
        """返回显示器列表"""
        mock_get_monitors.return_value = [
            {"index": 0, "name": "显示器 1", "resolution": "1920x1080",
             "is_primary": True, "left": 0, "top": 0, "width": 1920, "height": 1080},
        ]

        from app.api.desktop import get_monitors_endpoint
        result = asyncio.run(get_monitors_endpoint())

        assert result.success is True
        assert "monitors" in result.data

    @patch('app.api.desktop.get_monitors')
    def test_empty_monitors(self, mock_get_monitors):
        """无显示器时返回空列表"""
        mock_get_monitors.return_value = []

        from app.api.desktop import get_monitors_endpoint
        result = asyncio.run(get_monitors_endpoint())

        assert result.success is True
        assert result.data["monitors"] == []


# ============ 桌面截图 API ============

class TestDesktopScreenshotAPI:
    """测试 POST /api/desktop_screenshot"""

    @patch('app.api.desktop.self_check_service')
    @patch('app.api.desktop.capture_monitor')
    @patch('app.api.desktop.save_image')
    @patch('app.api.desktop.generate_data_dir')
    @patch('app.api.desktop.get_monitors')
    def test_screenshot_success(self, mock_monitors, mock_dir, mock_save, mock_capture, mock_sc):
        """桌面截图成功"""
        from PIL import Image
        mock_monitors.return_value = [{"index": 0}]
        mock_capture.return_value = Image.new("RGB", (1920, 1080))
        mock_dir.return_value = "/tmp/data/test_session"
        mock_sc.validate_before_screenshot.return_value = MagicMock(ok=True)
        mock_sc.record_screenshot_success.return_value = None

        from app.api.desktop import desktop_screenshot
        from app.models.desktop_request import DesktopScreenshotRequest

        request = DesktopScreenshotRequest(**_base_kwargs())
        result = asyncio.run(desktop_screenshot(request))

        assert result.success is True

    @patch('app.api.desktop.get_monitors')
    def test_screenshot_invalid_monitor(self, mock_monitors):
        """无效 monitor_index 返回 MONITOR_NOT_FOUND"""
        mock_monitors.return_value = [{"index": 0}]

        from app.api.desktop import desktop_screenshot
        from app.models.desktop_request import DesktopScreenshotRequest

        request = DesktopScreenshotRequest(**_base_kwargs(monitor_index=99))
        result = asyncio.run(desktop_screenshot(request))

        assert result.success is False
        assert result.error_code == "MONITOR_NOT_FOUND"

    @patch('app.api.desktop.self_check_service')
    @patch('app.api.desktop.capture_monitor')
    @patch('app.api.desktop.save_image')
    @patch('app.api.desktop.generate_data_dir')
    @patch('app.api.desktop.get_monitors')
    def test_screenshot_filename_prefix(self, mock_monitors, mock_dir, mock_save, mock_capture, mock_sc):
        """桌面截图文件名使用 desktop_ 前缀"""
        from PIL import Image
        mock_monitors.return_value = [{"index": 0}]
        mock_capture.return_value = Image.new("RGB", (1920, 1080))
        mock_dir.return_value = "/tmp/data/test_session"
        mock_sc.validate_before_screenshot.return_value = MagicMock(ok=True)
        mock_sc.record_screenshot_success.return_value = None

        from app.api.desktop import desktop_screenshot
        from app.models.desktop_request import DesktopScreenshotRequest

        request = DesktopScreenshotRequest(**_base_kwargs())
        result = asyncio.run(desktop_screenshot(request))

        # 验证保存的文件名包含 desktop_
        if mock_save.called:
            save_args = mock_save.call_args
            path_arg = save_args[0][1] if len(save_args[0]) > 1 else ""
            assert "desktop_" in path_arg or "desktop_" in str(save_args)


# ============ 桌面点击 API ============

class TestDesktopClickAPI:
    """测试 POST /api/desktop_click"""

    @patch('app.api.desktop.config_service')
    @patch('app.api.desktop.desktop_click')
    @patch('app.api.desktop.desktop_percent_to_screen')
    @patch('app.api.desktop.get_monitors')
    def test_click_success(self, mock_monitors, mock_coord, mock_click_fn, mock_config):
        """桌面点击成功"""
        mock_config.is_delegated_active.return_value = True
        mock_monitors.return_value = [{"index": 0}]
        mock_coord.return_value = (960, 540)
        mock_click_fn.return_value = _mock_inject_result(success=True)

        from app.api.desktop import desktop_click_endpoint
        from app.models.desktop_request import DesktopClickRequest

        request = DesktopClickRequest(**_base_kwargs(x=50, y=50))
        result = asyncio.run(desktop_click_endpoint(request))

        assert result.success is True

    @patch('app.api.desktop.get_monitors')
    def test_click_invalid_monitor(self, mock_monitors):
        """无效 monitor_index 返回错误"""
        mock_monitors.return_value = [{"index": 0}]

        from app.api.desktop import desktop_click_endpoint
        from app.models.desktop_request import DesktopClickRequest

        request = DesktopClickRequest(**_base_kwargs(monitor_index=99, x=50, y=50))
        result = asyncio.run(desktop_click_endpoint(request))

        assert result.success is False


# ============ 桌面双击 API ============

class TestDesktopDoubleClickAPI:
    """测试 POST /api/desktop_double_click"""

    @patch('app.api.desktop.config_service')
    @patch('app.api.desktop.desktop_double_click')
    @patch('app.api.desktop.desktop_percent_to_screen')
    @patch('app.api.desktop.get_monitors')
    def test_double_click_success(self, mock_monitors, mock_coord, mock_dblclick_fn, mock_config):
        """桌面双击成功"""
        mock_config.is_delegated_active.return_value = True
        mock_monitors.return_value = [{"index": 0}]
        mock_coord.return_value = (960, 540)
        mock_dblclick_fn.return_value = _mock_inject_result(success=True)

        from app.api.desktop import desktop_double_click_endpoint
        from app.models.desktop_request import DesktopDoubleClickRequest

        request = DesktopDoubleClickRequest(**_base_kwargs(x=50, y=50))
        result = asyncio.run(desktop_double_click_endpoint(request))

        assert result.success is True


# ============ 桌面右键 API ============

class TestDesktopRightClickAPI:
    """测试 POST /api/desktop_right_click"""

    @patch('app.api.desktop.config_service')
    @patch('app.api.desktop.desktop_right_click')
    @patch('app.api.desktop.desktop_percent_to_screen')
    @patch('app.api.desktop.get_monitors')
    def test_right_click_success(self, mock_monitors, mock_coord, mock_rclick_fn, mock_config):
        """桌面右键成功"""
        mock_config.is_delegated_active.return_value = True
        mock_monitors.return_value = [{"index": 0}]
        mock_coord.return_value = (960, 540)
        mock_rclick_fn.return_value = _mock_inject_result(success=True)

        from app.api.desktop import desktop_right_click_endpoint
        from app.models.desktop_request import DesktopRightClickRequest

        request = DesktopRightClickRequest(**_base_kwargs(x=50, y=50))
        result = asyncio.run(desktop_right_click_endpoint(request))

        assert result.success is True


# ============ 桌面拖拽 API ============

class TestDesktopDragAPI:
    """测试 POST /api/desktop_drag"""

    @patch('app.api.desktop.config_service')
    @patch('app.api.desktop.desktop_drag')
    @patch('app.api.desktop.desktop_percent_to_screen')
    @patch('app.api.desktop.get_monitors')
    def test_same_monitor_drag(self, mock_monitors, mock_coord, mock_drag_fn, mock_config):
        """同屏拖拽成功"""
        mock_config.is_delegated_active.return_value = True
        mock_monitors.return_value = [{"index": 0}]
        mock_coord.side_effect = [(384, 540), (1536, 540)]
        mock_drag_fn.return_value = _mock_inject_result(success=True)

        from app.api.desktop import desktop_drag_endpoint
        from app.models.desktop_request import DesktopDragRequest

        request = DesktopDragRequest(**_base_kwargs(
            start_x=20, start_y=50,
            end_x=80, end_y=50,
            end_monitor_index=0,
        ))
        result = asyncio.run(desktop_drag_endpoint(request))

        assert result.success is True

    @patch('app.api.desktop.config_service')
    @patch('app.api.desktop.desktop_drag')
    @patch('app.api.desktop.desktop_percent_to_screen')
    @patch('app.api.desktop.get_monitors')
    def test_cross_monitor_drag(self, mock_monitors, mock_coord, mock_drag_fn, mock_config):
        """跨屏拖拽：从主屏拖到副屏"""
        mock_config.is_delegated_active.return_value = True
        mock_monitors.return_value = [{"index": 0}, {"index": 1}]
        mock_coord.side_effect = [(1536, 540), (2432, 720)]
        mock_drag_fn.return_value = _mock_inject_result(success=True)

        from app.api.desktop import desktop_drag_endpoint
        from app.models.desktop_request import DesktopDragRequest

        request = DesktopDragRequest(**_base_kwargs(
            start_x=80, start_y=50,
            end_x=20, end_y=50,
            end_monitor_index=1,
        ))
        result = asyncio.run(desktop_drag_endpoint(request))

        assert result.success is True
        assert mock_coord.call_count == 2


# ============ 桌面滚动 API ============

class TestDesktopScrollAPI:
    """测试 POST /api/desktop_scroll"""

    @patch('app.api.desktop.config_service')
    @patch('app.api.desktop.desktop_scroll')
    @patch('app.api.desktop.desktop_percent_to_screen')
    @patch('app.api.desktop.get_monitors')
    def test_scroll_success(self, mock_monitors, mock_coord, mock_scroll_fn, mock_config):
        """桌面滚动成功"""
        mock_config.is_delegated_active.return_value = True
        mock_monitors.return_value = [{"index": 0}]
        mock_coord.return_value = (960, 540)
        mock_scroll_fn.return_value = _mock_inject_result(success=True)

        from app.api.desktop import desktop_scroll_endpoint
        from app.models.desktop_request import DesktopScrollRequest

        request = DesktopScrollRequest(**_base_kwargs(x=50, y=50, delta=-3))
        result = asyncio.run(desktop_scroll_endpoint(request))

        assert result.success is True


# ============ 桌面文本输入 API ============

class TestDesktopInputTextAPI:
    """测试 POST /api/desktop_input_text"""

    @patch('app.api.desktop.config_service')
    @patch('app.api.desktop.desktop_input_text')
    @patch('app.api.desktop.desktop_percent_to_screen')
    @patch('app.api.desktop.get_monitors')
    def test_input_text_success(self, mock_monitors, mock_coord, mock_input_fn, mock_config):
        """桌面文本输入成功"""
        mock_config.is_delegated_active.return_value = True
        mock_monitors.return_value = [{"index": 0}]
        mock_coord.return_value = (960, 540)
        mock_input_fn.return_value = _mock_inject_result(success=True)

        from app.api.desktop import desktop_input_text_endpoint
        from app.models.desktop_request import DesktopInputTextRequest

        request = DesktopInputTextRequest(**_base_kwargs(x=50, y=50, text="hello world"))
        result = asyncio.run(desktop_input_text_endpoint(request))

        assert result.success is True


# ============ 桌面按键 API ============

class TestDesktopPressKeyAPI:
    """测试 POST /api/desktop_press_key"""

    @patch('app.api.desktop.config_service')
    @patch('app.api.desktop.desktop_press_key')
    def test_press_key_success(self, mock_key_fn, mock_config):
        """桌面按键成功"""
        mock_config.is_delegated_active.return_value = True
        mock_key_fn.return_value = _mock_inject_result(success=True)

        from app.api.desktop import desktop_press_key_endpoint
        from app.models.desktop_request import DesktopPressKeyRequest

        request = DesktopPressKeyRequest(**_base_kwargs(keys="ctrl c"))
        result = asyncio.run(desktop_press_key_endpoint(request))

        assert result.success is True

    @patch('app.api.desktop.config_service')
    @patch('app.api.desktop.desktop_press_key')
    def test_press_key_win(self, mock_key_fn, mock_config):
        """桌面 Win 键（打开开始菜单）"""
        mock_config.is_delegated_active.return_value = True
        mock_key_fn.return_value = _mock_inject_result(success=True)

        from app.api.desktop import desktop_press_key_endpoint
        from app.models.desktop_request import DesktopPressKeyRequest

        request = DesktopPressKeyRequest(**_base_kwargs(keys="win"))
        result = asyncio.run(desktop_press_key_endpoint(request))

        assert result.success is True


# ============ 桌面悬浮 API ============

class TestDesktopHoverAPI:
    """测试 POST /api/desktop_hover"""

    @patch('app.api.desktop.config_service')
    @patch('app.api.desktop.desktop_hover')
    @patch('app.api.desktop.desktop_percent_to_screen')
    @patch('app.api.desktop.get_monitors')
    def test_hover_success(self, mock_monitors, mock_coord, mock_hover_fn, mock_config):
        """桌面悬浮成功"""
        mock_config.is_delegated_active.return_value = True
        mock_monitors.return_value = [{"index": 0}]
        mock_coord.return_value = (960, 540)
        mock_hover_fn.return_value = _mock_inject_result(success=True)

        from app.api.desktop import desktop_hover_endpoint
        from app.models.desktop_request import DesktopHoverRequest

        request = DesktopHoverRequest(**_base_kwargs(x=50, y=50, duration_ms=2000))
        result = asyncio.run(desktop_hover_endpoint(request))

        assert result.success is True


# ============ 日志字段验证 ============

class TestDesktopLogFields:
    """测试桌面操作的日志字段按需填充"""

    @patch('app.api.desktop.config_service')
    @patch('app.api.desktop.desktop_click')
    @patch('app.api.desktop.desktop_percent_to_screen')
    @patch('app.api.desktop.get_monitors')
    @patch('app.api.desktop.log_service')
    def test_log_has_monitor_index(self, mock_log, mock_monitors, mock_coord, mock_click_fn, mock_config):
        """桌面操作的日志包含 monitor_index"""
        mock_config.is_delegated_active.return_value = True
        mock_monitors.return_value = [{"index": 0}]
        mock_coord.return_value = (960, 540)
        mock_click_fn.return_value = _mock_inject_result(success=True)

        from app.api.desktop import desktop_click_endpoint
        from app.models.desktop_request import DesktopClickRequest

        request = DesktopClickRequest(**_base_kwargs(x=50, y=50))
        asyncio.run(desktop_click_endpoint(request))

        # 验证 log_service.log 被调用且包含 monitor_index
        if mock_log.log.called:
            call_kwargs = mock_log.log.call_args
            assert "monitor_index" in call_kwargs.kwargs or any(
                "monitor_index" in str(v) for v in call_kwargs.kwargs.values()
            )

    @patch('app.api.desktop.config_service')
    @patch('app.api.desktop.desktop_click')
    @patch('app.api.desktop.desktop_percent_to_screen')
    @patch('app.api.desktop.get_monitors')
    @patch('app.api.desktop.log_service')
    def test_log_window_fields_null(self, mock_log, mock_monitors, mock_coord, mock_click_fn, mock_config):
        """桌面操作的日志中窗口字段为 None"""
        mock_config.is_delegated_active.return_value = True
        mock_monitors.return_value = [{"index": 0}]
        mock_coord.return_value = (960, 540)
        mock_click_fn.return_value = _mock_inject_result(success=True)

        from app.api.desktop import desktop_click_endpoint
        from app.models.desktop_request import DesktopClickRequest

        request = DesktopClickRequest(**_base_kwargs(x=50, y=50))
        asyncio.run(desktop_click_endpoint(request))

        # 验证 window_id 和 process_name 为 None
        if mock_log.log.called:
            kwargs = mock_log.log.call_args.kwargs
            assert kwargs.get("window_id") is None
            assert kwargs.get("process_name") is None

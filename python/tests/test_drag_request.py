"""
DragRequest 数据模型单元测试

测试新增的跨窗口拖拽字段和 model_validator
"""
import pytest
from pydantic import ValidationError
from app.models.request import DragRequest


class TestDragRequestFields:
    """测试 DragRequest 基础字段"""

    def test_basic_drag_request(self):
        """基本拖拽请求 - 无 target_window_id"""
        req = DragRequest(
            ai_app_type="claude_code",
            session_id="s1",
            window_id=11111,
            start_x=10.0,
            start_y=20.0,
            end_x=80.0,
            end_y=90.0,
            duration_ms=500,
            action_method="background"
        )
        assert req.target_window_id is None
        assert req.target_main_window_id is None
        assert req.action_method == "background"

    def test_cross_process_drag_request(self):
        """跨窗口拖拽请求 - 有 target_window_id"""
        req = DragRequest(
            ai_app_type="claude_code",
            session_id="s1",
            window_id=11111,
            start_x=10.0,
            start_y=20.0,
            end_x=80.0,
            end_y=90.0,
            target_window_id=22222,
            target_main_window_id=33333
        )
        assert req.target_window_id == 22222
        assert req.target_main_window_id == 33333


class TestDragRequestValidator:
    """测试跨进程强制 hijack 的 model_validator"""

    def test_cross_process_forces_hijack(self):
        """跨窗口拖拽自动强制 action_method 为 hijack"""
        req = DragRequest(
            ai_app_type="claude_code",
            session_id="s1",
            window_id=11111,
            start_x=10.0,
            start_y=20.0,
            end_x=80.0,
            end_y=90.0,
            action_method="background",
            target_window_id=22222
        )
        assert req.action_method == "hijack"

    def test_cross_process_hijack_stays_hijack(self):
        """跨窗口拖拽，已经是 hijack 则不变"""
        req = DragRequest(
            ai_app_type="claude_code",
            session_id="s1",
            window_id=11111,
            start_x=10.0,
            start_y=20.0,
            end_x=80.0,
            end_y=90.0,
            action_method="hijack",
            target_window_id=22222
        )
        assert req.action_method == "hijack"

    def test_same_window_background_stays(self):
        """同窗口拖拽，background 模式不变"""
        req = DragRequest(
            ai_app_type="claude_code",
            session_id="s1",
            window_id=11111,
            start_x=10.0,
            start_y=20.0,
            end_x=80.0,
            end_y=90.0,
            action_method="background"
        )
        assert req.action_method == "background"

    def test_target_same_as_window_no_force(self):
        """target_window_id 等于 window_id 时视为同窗口，不强制 hijack"""
        req = DragRequest(
            ai_app_type="claude_code",
            session_id="s1",
            window_id=11111,
            start_x=10.0,
            start_y=20.0,
            end_x=80.0,
            end_y=90.0,
            action_method="background",
            target_window_id=11111
        )
        assert req.action_method == "background"

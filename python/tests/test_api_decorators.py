# tests/test_api_decorators.py
"""
API装饰器单元测试
"""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.api.decorators import verify_request_common
from app.models.response import BaseResponse, create_error_response
from app.models.request import ClickRequest


def test_verify_request_common_success():
    """测试验证函数在验证通过时返回进程信息"""
    request_data = ClickRequest(
        ai_app_type="claude_code",
        session_id="test123",
        window_id=12345,
        x=50.0,
        y=50.0
    )

    with patch('app.api.decorators.process_service') as mock_process_svc, \
         patch('app.api.decorators.config_service') as mock_config_svc:

        mock_process = Mock()
        mock_process.process_name = "test.exe"
        mock_process_svc.get_process_by_window_id.return_value = mock_process
        mock_config_svc.is_process_blocked.return_value = False

        result = verify_request_common(request_data, "unknown")

    assert result is not None
    assert "error" not in result
    assert result["process_info"] == mock_process
    assert result["start_time"] > 0
    assert result["client_ip"] == "unknown"


def test_verify_request_common_window_not_found():
    """测试验证函数在窗口不存在时返回错误信息并记录日志"""
    request_data = ClickRequest(
        ai_app_type="claude_code",
        session_id="test123",
        window_id=12345,
        x=50.0,
        y=50.0
    )

    with patch('app.api.decorators.process_service') as mock_process_svc, \
         patch('app.api.decorators.log_service') as mock_log_svc:

        mock_process_svc.get_process_by_window_id.return_value = None

        result = verify_request_common(request_data, "unknown")

    assert result is not None
    assert result["error"] == "WINDOW_NOT_FOUND"
    mock_log_svc.log.assert_called_once()
    call_args = mock_log_svc.log.call_args
    assert call_args[1]["window_id"] == 12345
    assert call_args[1]["result"]["success"] == False
    assert "窗口不存在" in call_args[1]["result"]["message"]


def test_verify_request_common_process_blocked():
    """测试验证函数在进程被禁止时返回错误信息"""
    request_data = ClickRequest(
        ai_app_type="claude",
        session_id="test123",
        window_id=12345,
        x=50.0,
        y=50.0
    )

    with patch('app.api.decorators.process_service') as mock_process_svc, \
         patch('app.api.decorators.config_service') as mock_config_svc:

        mock_process = Mock()
        mock_process.process_name = "notepad.exe"
        mock_process_svc.get_process_by_window_id.return_value = mock_process
        mock_config_svc.is_process_blocked.return_value = True

        result = verify_request_common(request_data, "unknown")

    assert result is not None
    assert result["error"] == "PROCESS_BLOCKED"

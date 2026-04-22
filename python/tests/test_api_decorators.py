# tests/test_api_decorators.py
"""
API装饰器单元测试

测试 @with_verification 和 @log_and_format 装饰器的功能
"""
import pytest
import time
from fastapi import FastAPI, Request
from unittest.mock import Mock, patch
from app.api.decorators import with_verification, log_and_format, get_client_ip
from app.models.response import BaseResponse, create_error_response
from app.models.request import ClickRequest


def test_with_verification_success():
    """测试 @with_verification 装饰器在验证通过时注入上下文变量"""
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

        # 创建测试函数
        @with_verification
        async def test_func(request: ClickRequest):
            # 验证注入的属性
            assert hasattr(request, 'process_info')
            assert hasattr(request, 'start_time')
            assert hasattr(request, 'client_ip')
            assert request.process_info.process_name == "test.exe"
            assert request.client_ip == "unknown"
            return {"success": True}

        # 运行测试
        import asyncio
        result = asyncio.run(test_func(request_data))

        # 验证结果
        assert result["success"] is True


def test_with_verification_window_not_found():
    """测试 @with_verification 装饰器在窗口不存在时返回错误并记录日志"""
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

        # 创建测试函数
        @with_verification
        async def test_func(request: ClickRequest):
            return {"success": True}

        # 运行测试
        import asyncio
        result = asyncio.run(test_func(request_data))

        # 验证返回错误响应
        assert result.success is False
        assert "WINDOW_NOT_FOUND" in str(result.error_code)

        # 验证日志被记录
        mock_log_svc.log.assert_called_once()
        call_args = mock_log_svc.log.call_args
        assert call_args[1]["window_id"] == 12345
        assert call_args[1]["result"]["success"] is False
        assert "Window not found" in call_args[1]["result"]["message"]


def test_with_verification_process_blocked():
    """测试 @with_verification 装饰器在进程被禁止时返回错误"""
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

        # 创建测试函数
        @with_verification
        async def test_func(request: ClickRequest):
            return {"success": True}

        # 运行测试
        import asyncio
        result = asyncio.run(test_func(request_data))

        # 验证返回错误响应
        assert result.success is False
        assert "PROCESS_BLOCKED" in str(result.error_code)


def test_log_and_format():
    """测试 @log_and_format 装饰器记录日志并格式化响应"""
    request_data = ClickRequest(
        ai_app_type="claude_code",
        session_id="test123",
        window_id=12345,
        x=50.0,
        y=50.0
    )

    # 手动注入装饰器需要的上下文变量
    mock_process = Mock()
    mock_process.process_name = "test.exe"
    object.__setattr__(request_data, 'process_info', mock_process)
    object.__setattr__(request_data, 'start_time', time.time())
    object.__setattr__(request_data, 'client_ip', "127.0.0.1")

    with patch('app.api.decorators.log_service') as mock_log_svc:
        # 创建测试函数
        @log_and_format
        async def test_func(request: ClickRequest):
            return BaseResponse(success=True, message="操作成功")

        # 运行测试
        import asyncio
        result = asyncio.run(test_func(request_data))

        # 验证返回值
        assert result.success is True
        assert result.message == "操作成功"

        # 验证日志被记录
        mock_log_svc.log.assert_called_once()
        call_args = mock_log_svc.log.call_args
        assert call_args[1]["ai_app_type"] == "claude_code"
        assert call_args[1]["session_id"] == "test123"
        assert call_args[1]["window_id"] == 12345
        assert call_args[1]["process_name"] == "test.exe"
        assert call_args[1]["instruction"] == "test_func"
        assert call_args[1]["result"]["success"] is True
        assert "duration_ms" in call_args[1]


def test_both_decorators():
    """测试 @with_verification 和 @log_and_format 装饰器组合使用"""
    request_data = ClickRequest(
        ai_app_type="claude_code",
        session_id="test123",
        window_id=12345,
        x=50.0,
        y=50.0
    )

    with patch('app.api.decorators.process_service') as mock_process_svc, \
         patch('app.api.decorators.config_service') as mock_config_svc, \
         patch('app.api.decorators.log_service') as mock_log_svc:

        mock_process = Mock()
        mock_process.process_name = "test.exe"
        mock_process_svc.get_process_by_window_id.return_value = mock_process
        mock_config_svc.is_process_blocked.return_value = False

        # 创建测试函数（注意装饰器顺序）
        @with_verification
        @log_and_format
        async def test_func(request: ClickRequest):
            return BaseResponse(success=True, message="操作成功")

        # 运行测试
        import asyncio
        result = asyncio.run(test_func(request_data))

        # 验证返回值
        assert result.success is True
        assert result.message == "操作成功"

        # 验证日志被记录
        mock_log_svc.log.assert_called_once()
        call_args = mock_log_svc.log.call_args
        assert call_args[1]["process_name"] == "test.exe"
        assert call_args[1]["result"]["success"] is True


def test_get_client_ip():
    """测试 get_client_ip 函数正确提取IP地址"""
    # 测试 X-Forwarded-For
    request = Mock(spec=Request)
    request.headers = {"X-Forwarded-For": "192.168.1.100, 10.0.0.1"}
    request.client = None
    assert get_client_ip(request) == "192.168.1.100"

    # 测试 X-Real-IP
    request.headers = {"X-Real-IP": "192.168.1.101"}
    assert get_client_ip(request) == "192.168.1.101"

    # 测试直接连接
    request.headers = {}
    mock_client = Mock()
    mock_client.host = "192.168.1.102"
    request.client = mock_client
    assert get_client_ip(request) == "192.168.1.102"

    # 测试未知IP
    request.headers = {}
    request.client = None
    assert get_client_ip(request) == "unknown"


def test_decorator_injection_attributes():
    """测试装饰器正确注入属性到请求对象"""
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

        @with_verification
        async def test_func(request: ClickRequest):
            # 验证注入的属性可以通过 object.__getattribute__ 访问
            process_info = object.__getattribute__(request, 'process_info')
            start_time = object.__getattribute__(request, 'start_time')
            client_ip = object.__getattribute__(request, 'client_ip')

            assert process_info.process_name == "test.exe"
            assert start_time > 0
            assert client_ip == "unknown"
            return {"success": True}

        import asyncio
        result = asyncio.run(test_func(request_data))
        assert result["success"] is True

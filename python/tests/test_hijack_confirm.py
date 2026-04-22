"""
@with_hijack_confirm 装饰器单元测试

测试三条路径:
1. delegated 激活 → 跳过确认，强制设为 delegated
2. background → 直接放行
3. hijack → 弹确认弹窗
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.models.request import ClickRequest
from app.models.response import BaseResponse, create_error_response


def _make_click_request(action_method="background", **kwargs):
    """创建测试用 ClickRequest"""
    return ClickRequest(
        ai_app_type="claude_code",
        session_id="test123",
        window_id=12345,
        x=50.0,
        y=50.0,
        action_method=action_method,
        **kwargs
    )


@patch('app.api.decorators.config_service')
def test_hijack_confirm_background_passes(mock_config_svc):
    """background 模式直接放行，不弹确认框"""
    mock_config_svc.is_delegated_active.return_value = False

    request = _make_click_request(action_method="background")
    # 注入 process_info（模拟 @with_verification 已执行）
    mock_process = Mock()
    mock_process.process_name = "test.exe"
    object.__setattr__(request, 'process_info', mock_process)

    from app.api.decorators import with_hijack_confirm

    @with_hijack_confirm("Click")
    async def handler(request: ClickRequest):
        return BaseResponse(success=True, message="ok")

    import asyncio
    result = asyncio.run(handler(request))

    assert result.success is True
    assert request.action_method == "background"


@patch('app.api.decorators.config_service')
def test_hijack_confirm_delegated_forces_mode(mock_config_svc):
    """delegated 激活时跳过确认，强制设为 delegated"""
    mock_config_svc.is_delegated_active.return_value = True

    request = _make_click_request(action_method="hijack")
    mock_process = Mock()
    mock_process.process_name = "test.exe"
    object.__setattr__(request, 'process_info', mock_process)

    from app.api.decorators import with_hijack_confirm

    @with_hijack_confirm("Click")
    async def handler(request: ClickRequest):
        return BaseResponse(success=True, message="ok")

    import asyncio
    result = asyncio.run(handler(request))

    assert result.success is True
    assert request.action_method == "delegated"


@patch('app.api.decorators.config_service')
@patch('app.api.decorators.win32gui')
def test_hijack_confirm_user_denied(mock_win32gui, mock_config_svc):
    """hijack 模式用户拒绝 → 返回 USER_DENIED"""
    mock_config_svc.is_delegated_active.return_value = False
    mock_win32gui.GetWindowText.return_value = "Test Window"

    request = _make_click_request(action_method="hijack")
    mock_process = Mock()
    mock_process.process_name = "notepad.exe"
    object.__setattr__(request, 'process_info', mock_process)

    from app.api.decorators import with_hijack_confirm

    with patch('app.services.confirm_service.ConfirmService.request_confirm') as mock_confirm:
        mock_confirm.return_value = MagicMock(confirmed=False)

        @with_hijack_confirm("Click")
        async def handler(request: ClickRequest):
            return BaseResponse(success=True, message="ok")

        import asyncio
        result = asyncio.run(handler(request))

        assert result.success is False
        assert result.error_code == "USER_DENIED"


@patch('app.api.decorators.config_service')
@patch('app.api.decorators.win32gui')
def test_hijack_confirm_user_approved(mock_win32gui, mock_config_svc):
    """hijack 模式用户确认 → 正常执行"""
    mock_config_svc.is_delegated_active.return_value = False
    mock_win32gui.GetWindowText.return_value = "Test Window"

    request = _make_click_request(action_method="hijack")
    mock_process = Mock()
    mock_process.process_name = "notepad.exe"
    object.__setattr__(request, 'process_info', mock_process)

    from app.api.decorators import with_hijack_confirm

    with patch('app.services.confirm_service.ConfirmService.request_confirm') as mock_confirm:
        mock_confirm.return_value = MagicMock(confirmed=True)

        @with_hijack_confirm("Click", detail_fn=lambda r: f"({r.x}, {r.y})")
        async def handler(request: ClickRequest):
            return BaseResponse(success=True, message="ok")

        import asyncio
        result = asyncio.run(handler(request))

        assert result.success is True
        # 验证 detail_fn 被调用
        mock_confirm.assert_called_once()
        call_kwargs = mock_confirm.call_args[1]
        assert "operation_detail" in call_kwargs

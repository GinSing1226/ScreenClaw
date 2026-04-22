"""
托管模式API单元测试

测试 delegated 接口的三个分支: status / enter / exit
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.models.request import DelegatedRequest
from app.models.response import BaseResponse


class TestDelegatedStatus:
    """测试托管模式状态查询"""

    @pytest.mark.asyncio
    @patch('app.api.delegated.config_service')
    async def test_delegated_status_inactive(self, mock_config_svc):
        """查询托管状态 - 未激活"""
        mock_config_svc.is_delegated_active.return_value = False

        from app.api.delegated import delegated_control

        request = DelegatedRequest(action="status")
        result = await delegated_control(request, req=None)

        assert result.success is True
        assert result.data["delegated_active"] is False
        mock_config_svc.is_delegated_active.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.api.delegated.config_service')
    async def test_delegated_status_active(self, mock_config_svc):
        """查询托管状态 - 已激活"""
        mock_config_svc.is_delegated_active.return_value = True

        from app.api.delegated import delegated_control

        request = DelegatedRequest(action="status")
        result = await delegated_control(request, req=None)

        assert result.success is True
        assert result.data["delegated_active"] is True


class TestDelegatedEnter:
    """测试进入托管模式"""

    @pytest.mark.asyncio
    @patch('app.api.delegated.config_service')
    @patch('app.api.delegated.log_service')
    @patch('app.api.delegated.DelegatedConfirmDialog')
    async def test_delegated_enter_confirmed(self, mock_dialog_cls, mock_log_svc, mock_config_svc):
        """进入托管 - 用户确认"""
        mock_config_svc.is_delegated_active.return_value = False
        mock_config_svc.get.return_value = MagicMock(
            ui=MagicMock(language="zh_CN"),
            delegated=MagicMock(exit_hotkey="ctrl+alt+z")
        )
        mock_dialog_cls.return_value.show.return_value = MagicMock(confirmed=True)

        from app.api.delegated import delegated_control

        request = DelegatedRequest(action="enter")
        result = await delegated_control(request, req=None)

        assert result.success is True
        assert result.data["delegated_active"] is True
        mock_config_svc.update_delegated.assert_called_once_with(active=True)
        mock_log_svc.log.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.api.delegated.config_service')
    @patch('app.api.delegated.log_service')
    @patch('app.api.delegated.DelegatedConfirmDialog')
    async def test_delegated_enter_rejected(self, mock_dialog_cls, mock_log_svc, mock_config_svc):
        """进入托管 - 用户拒绝"""
        mock_config_svc.is_delegated_active.return_value = False
        mock_config_svc.get.return_value = MagicMock(
            ui=MagicMock(language="zh_CN"),
            delegated=MagicMock(exit_hotkey="ctrl+alt+z")
        )
        mock_dialog_cls.return_value.show.return_value = MagicMock(confirmed=False)

        from app.api.delegated import delegated_control

        request = DelegatedRequest(action="enter")
        result = await delegated_control(request, req=None)

        assert result.success is False
        assert result.data["delegated_active"] is False
        mock_config_svc.update_delegated.assert_not_called()
        mock_log_svc.log.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.api.delegated.config_service')
    @patch('app.api.delegated.log_service')
    @patch('app.api.delegated.DelegatedConfirmDialog')
    async def test_delegated_enter_already_active(self, mock_dialog_cls, mock_log_svc, mock_config_svc):
        """进入托管 - 已在托管模式中"""
        mock_config_svc.is_delegated_active.return_value = True

        from app.api.delegated import delegated_control

        request = DelegatedRequest(action="enter")
        result = await delegated_control(request, req=None)

        assert result.success is True
        assert result.data["delegated_active"] is True
        # 不应弹出确认框
        mock_dialog_cls.assert_not_called()
        mock_config_svc.update_delegated.assert_not_called()


class TestDelegatedExit:
    """测试退出托管模式"""

    @pytest.mark.asyncio
    @patch('app.api.delegated.config_service')
    @patch('app.api.delegated.log_service')
    async def test_delegated_exit(self, mock_log_svc, mock_config_svc):
        """退出托管模式"""
        from app.api.delegated import delegated_control

        request = DelegatedRequest(action="exit")
        result = await delegated_control(request, req=None)

        assert result.success is True
        assert result.data["delegated_active"] is False
        mock_config_svc.update_delegated.assert_called_once_with(active=False)
        mock_log_svc.log.assert_called_once()


class TestDelegatedInvalidAction:
    """测试未知action"""

    @pytest.mark.asyncio
    async def test_delegated_invalid_action(self):
        """未知action返回错误"""
        from app.api.delegated import delegated_control

        request = DelegatedRequest(action="invalid_action")
        result = await delegated_control(request, req=None)

        assert result.success is False
        assert result.error_code == "INVALID_ACTION"

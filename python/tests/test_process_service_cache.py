# tests/test_process_service_cache.py
"""
ProcessService缓存功能单元测试
"""
import pytest
from app.services.process_service import ProcessService
from unittest.mock import patch, Mock, MagicMock, call


@pytest.mark.parametrize("process_id,expected_name", [
    (1234, "test.exe"),
    (5678, "explorer.exe"),
])
def test_get_process_name_cached(process_id, expected_name):
    """Test that process name lookup is cached"""
    process_service = ProcessService()

    # Mock win32api module functions
    with patch('app.services.process_service.win32api.OpenProcess') as mock_open, \
         patch('app.services.process_service.win32process.GetModuleFileNameEx') as mock_get_module, \
         patch('app.services.process_service.win32api.CloseHandle'):

        mock_handle = Mock()
        mock_open.return_value = mock_handle
        mock_get_module.return_value = f"C:\\Windows\\{expected_name}"

        # First call
        result1 = process_service._get_process_name_impl(process_id)
        assert result1 == expected_name

        # Verify OpenProcess was called
        assert mock_open.call_count == 1

        # Second call should use cache (OpenProcess not called again)
        result2 = process_service._get_process_name_impl(process_id)
        assert result2 == expected_name

        # Verify OpenProcess was still only called once due to caching
        assert mock_open.call_count == 1


def test_get_process_by_window_id_uses_cache():
    """Test that get_process_by_window_id benefits from cached process names"""
    process_service = ProcessService()

    # Mock win32gui and win32process
    with patch('app.services.process_service.win32gui') as mock_win32gui, \
         patch('app.services.process_service.win32process') as mock_win32process, \
         patch('app.services.process_service.win32api.OpenProcess') as mock_open, \
         patch('app.services.process_service.win32process.GetModuleFileNameEx') as mock_get_module, \
         patch('app.services.process_service.win32api.CloseHandle'):

        # Setup mocks
        mock_win32gui.IsWindow.return_value = True
        mock_win32process.GetWindowThreadProcessId.return_value = (1234, 5678)
        mock_win32gui.GetWindowText.return_value = "Test Window"

        mock_handle = Mock()
        mock_open.return_value = mock_handle
        mock_get_module.return_value = "C:\\Windows\\test.exe"

        # First call
        result1 = process_service.get_process_by_window_id(12345)
        assert result1.process_name == "test.exe"

        # Verify OpenProcess was called once
        assert mock_open.call_count == 1

        # Second call should use cache
        result2 = process_service.get_process_by_window_id(12345)
        assert result2.process_name == "test.exe"

        # Verify OpenProcess was still only called once (cached)
        assert mock_open.call_count == 1


def test_clear_cache_method():
    """Test that clear_cache method exists and works"""
    process_service = ProcessService()

    # Verify clear_cache method exists
    assert hasattr(process_service, 'clear_cache')
    assert callable(process_service.clear_cache)

    # Mock win32api functions
    with patch('app.services.process_service.win32api.OpenProcess') as mock_open, \
         patch('app.services.process_service.win32process.GetModuleFileNameEx') as mock_get_module, \
         patch('app.services.process_service.win32api.CloseHandle'):

        mock_handle = Mock()
        mock_open.return_value = mock_handle
        mock_get_module.return_value = "C:\\Windows\\test.exe"

        # First call
        result1 = process_service._get_process_name_impl(1234)
        assert result1 == "test.exe"

        # Verify cache has been used
        assert mock_open.call_count == 1

        # Clear cache
        process_service.clear_cache()

        # Second call should hit win32api again after cache clear
        result2 = process_service._get_process_name_impl(1234)
        assert result2 == "test.exe"

        # Verify OpenProcess was called again after cache clear
        assert mock_open.call_count == 2


def test_cache_size_constant():
    """Test that cache size constant is defined"""
    process_service = ProcessService()

    # Verify cache size constant exists
    assert hasattr(ProcessService, '_PROCESS_NAME_CACHE_SIZE')
    assert isinstance(ProcessService._PROCESS_NAME_CACHE_SIZE, int)
    assert ProcessService._PROCESS_NAME_CACHE_SIZE == 256


def test_cache_stores_multiple_processes():
    """Test that cache can store multiple different process names"""
    process_service = ProcessService()

    # Mock win32api functions
    with patch('app.services.process_service.win32api.OpenProcess') as mock_open, \
         patch('app.services.process_service.win32process.GetModuleFileNameEx') as mock_get_module, \
         patch('app.services.process_service.win32api.CloseHandle'):

        mock_handle = Mock()

        def mock_get_module_filename(handle, module_id):
            # Return different names based on call count
            call_count = mock_get_module.call_count
            if call_count == 1:
                return "C:\\Windows\\test1.exe"
            elif call_count == 2:
                return "C:\\Windows\\test2.exe"
            elif call_count == 3:
                return "C:\\Windows\\test3.exe"
            return "C:\\Windows\\unknown.exe"

        mock_open.return_value = mock_handle
        mock_get_module.side_effect = mock_get_module_filename

        # Call with different process IDs
        result1 = process_service._get_process_name_impl(1001)
        result2 = process_service._get_process_name_impl(1002)
        result3 = process_service._get_process_name_impl(1003)

        assert result1 == "test1.exe"
        assert result2 == "test2.exe"
        assert result3 == "test3.exe"

        # All three should have been cached
        assert mock_open.call_count == 3

        # Second round should use cache
        result1_again = process_service._get_process_name_impl(1001)
        result2_again = process_service._get_process_name_impl(1002)
        result3_again = process_service._get_process_name_impl(1003)

        assert result1_again == "test1.exe"
        assert result2_again == "test2.exe"
        assert result3_again == "test3.exe"

        # No additional calls to OpenProcess (still 3)
        assert mock_open.call_count == 3

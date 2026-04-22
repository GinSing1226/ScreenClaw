# tests/test_process_service_cache.py
"""
ProcessService缓存功能单元测试
"""
import pytest
from app.services.process_service import ProcessService
from unittest.mock import patch, Mock


@pytest.mark.parametrize("process_id,expected_name", [
    (1234, "test.exe"),
    (5678, "explorer.exe"),
])
def test_get_process_name_cached(process_id, expected_name):
    """Test that process name lookup is cached"""
    process_service = ProcessService()

    def mock_query(handle, flags, buf, size):
        buf.value = f"C:\\Windows\\{expected_name}"

    with patch('app.services.process_service.win32api.OpenProcess') as mock_open, \
         patch('ctypes.windll.kernel32.QueryFullProcessImageNameW', side_effect=mock_query), \
         patch('app.services.process_service.win32api.CloseHandle'):

        mock_handle = Mock()
        mock_open.return_value = mock_handle

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

    def mock_query(handle, flags, buf, size):
        buf.value = "C:\\Windows\\test.exe"

    with patch('app.services.process_service.win32gui') as mock_win32gui, \
         patch('app.services.process_service.win32process') as mock_win32process, \
         patch('app.services.process_service.win32api.OpenProcess') as mock_open, \
         patch('ctypes.windll.kernel32.QueryFullProcessImageNameW', side_effect=mock_query), \
         patch('app.services.process_service.win32api.CloseHandle'):

        # Setup mocks
        mock_win32gui.IsWindow.return_value = True
        mock_win32process.GetWindowThreadProcessId.return_value = (1234, 5678)
        mock_win32gui.GetWindowText.return_value = "Test Window"

        mock_handle = Mock()
        mock_open.return_value = mock_handle

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

    def mock_query(handle, flags, buf, size):
        buf.value = "C:\\Windows\\test.exe"

    with patch('app.services.process_service.win32api.OpenProcess') as mock_open, \
         patch('ctypes.windll.kernel32.QueryFullProcessImageNameW', side_effect=mock_query), \
         patch('app.services.process_service.win32api.CloseHandle'):

        mock_handle = Mock()
        mock_open.return_value = mock_handle

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

    call_count = [0]
    names = ["test1.exe", "test2.exe", "test3.exe"]

    def mock_query(handle, flags, buf, size):
        idx = call_count[0]
        call_count[0] += 1
        buf.value = f"C:\\Windows\\{names[idx]}"

    with patch('app.services.process_service.win32api.OpenProcess') as mock_open, \
         patch('ctypes.windll.kernel32.QueryFullProcessImageNameW', side_effect=mock_query), \
         patch('app.services.process_service.win32api.CloseHandle'):

        mock_handle = Mock()
        mock_open.return_value = mock_handle

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

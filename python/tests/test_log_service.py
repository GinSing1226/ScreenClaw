"""
日志服务单元测试
"""
import pytest
import os
import tempfile
from datetime import datetime
from app.services.log_service import LogService


class TestLogService:
    """日志服务测试"""

    def test_log_write(self, tmp_path):
        """测试日志写入"""
        import time
        log_dir = os.path.join(tmp_path, "logs")
        service = LogService(log_dir)

        # 写入日志
        service.log(
            ai_app_type="test_app",
            session_id="session_001",
            window_id=1234,
            process_name="test.exe",
            instruction="click",
            params={"x": 50, "y": 50},
            result={"success": True, "message": "成功"},
            duration_ms=100
        )

        # 等待批量写入完成（最多2秒）
        time.sleep(2)

        # 验证文件被创建
        date_str = datetime.now().strftime("%Y-%m-%d")
        expected_file = os.path.join(log_dir, f"test_app-session_001-{date_str}.jsonl")
        assert os.path.exists(expected_file)

        # 清理
        service.shutdown()

    def test_read_logs(self, tmp_path):
        """测试读取日志"""
        import time
        log_dir = os.path.join(tmp_path, "logs")
        service = LogService(log_dir)

        # 写入多条日志
        for i in range(3):
            service.log(
                ai_app_type="test_app",
                session_id="session_001",
                window_id=1234,
                process_name="test.exe",
                instruction=f"action_{i}",
                params={},
                result={"success": True},
                duration_ms=10 * i
            )

        # 等待批量写入完成
        time.sleep(2)

        # 读取日志
        logs = service.read_logs(ai_app_type="test_app", session_id="session_001")
        assert len(logs) == 3

        # 清理
        service.shutdown()

    def test_log_content(self, tmp_path):
        """测试日志内容"""
        import time
        log_dir = os.path.join(tmp_path, "logs")
        service = LogService(log_dir)

        service.log(
            ai_app_type="test_app",
            session_id="session_001",
            window_id=1234,
            process_name="test.exe",
            instruction="click",
            params={"x": 50, "y": 50},
            result={"success": True},
            duration_ms=100
        )

        # 等待批量写入完成
        time.sleep(2)

        logs = service.read_logs(ai_app_type="test_app", session_id="session_001")
        assert len(logs) == 1

        log = logs[0]
        assert log["window_id"] == 1234
        assert log["process_name"] == "test.exe"
        assert log["instruction"] == "click"
        assert log["params"]["x"] == 50
        assert log["result"]["success"] == True
        assert log["duration_ms"] == 100

        # 清理
        service.shutdown()

    def test_keyword_filter(self, tmp_path):
        """测试关键词过滤"""
        import time
        log_dir = os.path.join(tmp_path, "logs")
        service = LogService(log_dir)

        # 写入不同内容的日志
        service.log(
            ai_app_type="test_app",
            session_id="session_001",
            window_id=1234,
            process_name="notepad.exe",
            instruction="click",
            params={},
            result={"success": True},
            duration_ms=10
        )

        service.log(
            ai_app_type="test_app",
            session_id="session_001",
            window_id=5678,
            process_name="calc.exe",
            instruction="click",
            params={},
            result={"success": True},
            duration_ms=10
        )

        # 等待批量写入完成
        time.sleep(2)

        # 搜索
        logs = service.read_logs(keyword="notepad")
        assert len(logs) == 1
        assert logs[0]["process_name"] == "notepad.exe"

        # 清理
        service.shutdown()

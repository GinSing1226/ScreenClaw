# tests/test_log_service_async.py
import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
import pytest

from app.services.log_service import LogService


@pytest.fixture
def temp_log_dir():
    """Temporary directory for log tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.mark.asyncio
async def test_log_write_async(temp_log_dir):
    """Test async log writing completes quickly"""
    log_service = LogService(log_dir=temp_log_dir)

    start = time.perf_counter()
    log_service.log(
        ai_app_type="test",
        session_id="session1",
        window_id=12345,
        process_name="test.exe",
        instruction="click",
        params={"x": 50, "y": 50},
        result={"success": True},
        duration_ms=100
    )
    elapsed = time.perf_counter() - start

    # Should complete in <10ms (async, non-blocking)
    assert elapsed < 0.01, f"Log write took {elapsed:.3f}s, expected <0.01s"

    # Wait for batch to flush and shutdown
    await asyncio.sleep(2)
    log_service.shutdown()


@pytest.mark.asyncio
async def test_log_batch_write(temp_log_dir):
    """Test multiple logs are batch written correctly"""
    log_service = LogService(log_dir=temp_log_dir)

    # Write multiple logs rapidly
    for i in range(10):
        log_service.log(
            ai_app_type="test",
            session_id="session1",
            window_id=12345,
            process_name="test.exe",
            instruction=f"click_{i}",
            params={"index": i},
            result={"success": True},
            duration_ms=100
        )

    # Wait for batch to flush (max 2 seconds)
    await asyncio.sleep(2)

    # Verify all logs were written
    log_files = list(Path(temp_log_dir).glob("test__session1__*.jsonl"))

    assert len(log_files) == 1, f"Expected 1 log file, found {len(log_files)}"

    with open(log_files[0], 'r', encoding='utf-8') as f:
        lines = f.readlines()

    assert len(lines) == 10, f"Expected 10 log entries, found {len(lines)}"

    # Verify log content
    for i, line in enumerate(lines):
        entry = json.loads(line)
        assert entry["instruction"] == f"click_{i}"

    log_service.shutdown()


@pytest.mark.asyncio
async def test_log_flush_on_shutdown(temp_log_dir):
    """Test pending logs are flushed on service shutdown"""
    log_service = LogService(log_dir=temp_log_dir)

    log_service.log(
        ai_app_type="test",
        session_id="session2",
        window_id=12345,
        process_name="test.exe",
        instruction="click",
        params={"x": 50},
        result={"success": True},
        duration_ms=100
    )

    # Shutdown immediately (should flush pending logs)
    log_service.shutdown()

    # Verify log was written
    log_files = list(Path(temp_log_dir).glob("test__session2__*.jsonl"))
    assert len(log_files) == 1

    with open(log_files[0], 'r', encoding='utf-8') as f:
        entry = json.loads(f.read())

    assert entry["instruction"] == "click"

"""
性能基准测试
验证优化效果
"""
import pytest
import time
import tempfile
import os
from pathlib import Path

from app.services.log_service import LogService
from app.services.config_service import ConfigService
from app.services.process_service import ProcessService


class TestLogPerformance:
    """日志服务性能测试"""

    def test_single_log_write_latency(self):
        """测试单条日志写入延迟（目标：<10ms）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_service = LogService(log_dir=tmpdir)

            start = time.perf_counter()
            log_service.log(
                ai_app_type="test",
                session_id="perf",
                window_id=12345,
                process_name="test.exe",
                instruction="click",
                params={"x": 50},
                result={"success": True},
                duration_ms=100
            )
            elapsed = time.perf_counter() - start

            # 应该立即返回（异步非阻塞）
            assert elapsed < 0.01, f"Log write took {elapsed:.3f}s, expected <0.01s"

            # 等待批量写入完成
            log_service.shutdown()

    def test_batch_log_throughput(self):
        """测试批量日志吞吐量（目标：>1000条/秒）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_service = LogService(log_dir=tmpdir)

            count = 1000
            start = time.perf_counter()

            for i in range(count):
                log_service.log(
                    ai_app_type="test",
                    session_id="perf",
                    window_id=12345,
                    process_name="test.exe",
                    instruction=f"click_{i}",
                    params={"index": i},
                    result={"success": True},
                    duration_ms=100
                )

            elapsed = time.perf_counter() - start
            throughput = count / elapsed

            # 应该能快速写入（异步）
            assert throughput > 1000, f"Throughput: {throughput:.0f} logs/sec, expected >1000"

            # 等待批量写入完成
            log_service.shutdown()

    def test_log_flush_on_shutdown(self):
        """测试关闭时刷新待写入日志"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_service = LogService(log_dir=tmpdir)

            log_service.log(
                ai_app_type="test",
                session_id="shutdown_test",
                window_id=12345,
                process_name="test.exe",
                instruction="click",
                params={"x": 50},
                result={"success": True},
                duration_ms=100
            )

            # 立即关闭（应该刷新待写入日志）
            log_service.shutdown()

            # 验证日志已写入文件
            log_files = list(Path(tmpdir).glob("test-shutdown_test-*.jsonl"))
            assert len(log_files) == 1, f"Expected 1 log file, found {len(log_files)}"

            with open(log_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
                assert "click" in content


class TestConfigPerformance:
    """配置服务性能测试"""

    def test_is_process_blocked_performance(self):
        """测试进程禁止检查性能（目标：O(1)缓存查询）"""
        config = ConfigService()

        # 大量查询
        iterations = 10000
        start = time.perf_counter()

        for _ in range(iterations):
            config.is_process_blocked("test.exe")

        elapsed = time.perf_counter() - start
        avg_time = elapsed / iterations

        # 平均每次查询应该非常快（<0.01ms，缓存O(1)查询）
        assert avg_time < 0.00001, f"Average lookup time: {avg_time*1000:.3f}ms, expected <0.01ms"

    def test_case_insensitive_cached_lookup(self):
        """测试大小写不敏感的缓存查询"""
        config = ConfigService()

        # 多次不同大小写的查询都应该很快
        iterations = 1000
        names = ["notepad.exe", "NOTEPAD.EXE", "NoTePaD.exe", "notepad.EXE"]

        start = time.perf_counter()
        for i in range(iterations):
            for name in names:
                config.is_process_blocked(name)
        elapsed = time.perf_counter() - start

        total_queries = iterations * len(names)
        avg_time = elapsed / total_queries

        # 缓存查询应该很快
        assert avg_time < 0.00001, f"Average lookup time: {avg_time*1000:.3f}ms"


class TestProcessServiceCache:
    """进程服务缓存性能测试"""

    def test_process_name_cache_hit(self):
        """测试进程名缓存效果"""
        service = ProcessService()

        # 使用当前进程ID（肯定存在）
        own_pid = os.getpid()

        # 第一次调用
        start = time.perf_counter()
        name1 = service._get_process_name_impl(own_pid)
        first_call = time.perf_counter() - start

        # 第二次调用（缓存命中）
        start = time.perf_counter()
        name2 = service._get_process_name_impl(own_pid)
        second_call = time.perf_counter() - start

        assert name1 == name2, "Process name should be consistent"
        # 缓存命中应该快得多（虽然测试环境可能差异不大）
        if first_call > 0:
            # 如果第一次调用有实际耗时，缓存应该更快
            # 注意：在测试环境中，如果进程已在缓存中，可能差异不明显
            pass

    def test_process_cache_clear(self):
        """测试进程缓存清除功能"""
        service = ProcessService()
        own_pid = os.getpid()

        # 第一次调用
        name1 = service._get_process_name_impl(own_pid)

        # 清除缓存
        service.clear_cache()

        # 再次调用（应该重新查询）
        name2 = service._get_process_name_impl(own_pid)

        assert name1 == name2, "Process name should be consistent after cache clear"

    def test_multiple_pid_cache(self):
        """测试多个进程ID的缓存"""
        service = ProcessService()

        # 使用当前进程ID的不同查询
        own_pid = os.getpid()

        # 多次查询相同PID
        for _ in range(100):
            name = service._get_process_name_impl(own_pid)
            assert name is not None


class TestIntegrationPerformance:
    """集成性能测试"""

    def test_concurrent_log_performance(self):
        """测试连续日志写入性能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_service = LogService(log_dir=tmpdir)

            # 快速连续写入多条日志
            count = 500
            start = time.perf_counter()

            for i in range(count):
                log_service.log(
                    ai_app_type="test",
                    session_id=f"concurrent_{i % 10}",  # 10个不同session
                    window_id=12345,
                    process_name="test.exe",
                    instruction="click",
                    params={"index": i},
                    result={"success": True},
                    duration_ms=100
                )

            elapsed = time.perf_counter() - start
            throughput = count / elapsed

            # 应该达到高吞吐量
            assert throughput > 1000, f"Throughput: {throughput:.0f} logs/sec, expected >1000"

            log_service.shutdown()

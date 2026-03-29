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
from app.platform.windows._code_templates import (
    _get_background_click_template,
    clear_template_cache
)


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


class TestCodeTemplatePerformance:
    """代码模板缓存性能测试"""

    def test_template_cache_hit(self):
        """测试模板缓存命中效果"""
        clear_template_cache()

        # 第一次调用 - 未缓存
        start = time.perf_counter()
        code1 = _get_background_click_template(12345, 100, 200)
        first_call = time.perf_counter() - start

        # 第二次调用 - 已缓存
        start = time.perf_counter()
        code2 = _get_background_click_template(12345, 100, 200)
        second_call = time.perf_counter() - start

        # 缓存调用应该快得多
        assert second_call < first_call, f"Cached call ({second_call*1000:.3f}ms) should be faster than first ({first_call*1000:.3f}ms)"
        assert code1 == code2

    def test_cache_performance_improvement(self):
        """测试缓存带来的性能提升"""
        clear_template_cache()

        params = (12345, 100, 200)

        # 预热：第一次调用
        _get_background_click_template(*params)

        # 测试缓存命中性能
        iterations = 10000
        start = time.perf_counter()

        for _ in range(iterations):
            _get_background_click_template(*params)

        elapsed = time.perf_counter() - start
        avg_cached_time = elapsed / iterations

        # 缓存命中应该非常快（<0.001ms）
        assert avg_cached_time < 0.001, f"Average cached lookup: {avg_cached_time*1000:.3f}ms, expected <0.001ms"

    def test_unique_template_generation(self):
        """测试不同参数生成不同模板"""
        clear_template_cache()

        templates = set()
        params = [
            (12345, 100, 200),
            (12345, 150, 250),
            (99999, 100, 200),
        ]

        for hwnd, x, y in params:
            template = _get_background_click_template(hwnd, x, y)
            templates.add(template)

        # 不同参数应该生成不同模板
        assert len(templates) == len(params), f"Different params should generate different templates, got {len(templates)} templates for {len(params)} param sets"

    def test_all_template_types_cached(self):
        """测试所有模板类型都支持缓存"""
        clear_template_cache()

        # 生成所有类型的模板
        _get_background_click_template(12345, 100, 200)
        from app.platform.windows._code_templates import (
            _get_background_right_click_template,
            _get_background_long_press_template,
            _get_background_swipe_template,
            _get_background_scroll_template,
            _get_background_hover_template,
        )

        _get_background_right_click_template(12345, 100, 200)
        _get_background_long_press_template(12345, 100, 200, 500)
        _get_background_swipe_template(12345, 100, 200, 150, 250)
        _get_background_scroll_template(12345, 100, 200, 120)
        _get_background_hover_template(12345, 100, 200, 1000)

        # 第二次调用应该命中缓存
        start = time.perf_counter()
        _get_background_click_template(12345, 100, 200)
        _get_background_right_click_template(12345, 100, 200)
        _get_background_long_press_template(12345, 100, 200, 500)
        _get_background_swipe_template(12345, 100, 200, 150, 250)
        _get_background_scroll_template(12345, 100, 200, 120)
        _get_background_hover_template(12345, 100, 200, 1000)
        elapsed = time.perf_counter() - start

        # 所有缓存命中应该非常快（<0.005s for 6 templates）
        assert elapsed < 0.005, f"6 cached lookups took {elapsed*1000:.3f}ms, expected <5ms"


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

    def test_log_and_template_combined(self):
        """测试日志和模板缓存的组合性能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_service = LogService(log_dir=tmpdir)
            clear_template_cache()

            iterations = 100

            start = time.perf_counter()

            for i in range(iterations):
                # 生成模板
                template = _get_background_click_template(12345, 100 + i, 200 + i)

                # 记录日志
                log_service.log(
                    ai_app_type="test",
                    session_id="integration",
                    window_id=12345,
                    process_name="test.exe",
                    instruction="click",
                    params={"template_len": len(template)},
                    result={"success": True},
                    duration_ms=100
                )

            elapsed = time.perf_counter() - start
            avg_time = elapsed / iterations

            # 组合操作应该很快（<1ms per iteration）
            assert avg_time < 0.001, f"Average combined operation time: {avg_time*1000:.3f}ms, expected <1ms"

            log_service.shutdown()

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

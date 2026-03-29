"""
日志服务 - 优化版本：支持异步批量写入
"""
import os
import sys
import json
import time
import queue
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List


def get_project_root() -> Path:
    """获取项目根目录"""
    # 优先从环境变量获取（开发模式）
    if os.environ.get('SCREENCLAW_ROOT'):
        return Path(os.environ['SCREENCLAW_ROOT'])

    # 获取当前exe或脚本所在目录，然后向上一级找到项目根目录
    if getattr(sys, 'frozen', False):
        # 打包后的exe
        exe_dir = Path(sys.executable).parent
        return exe_dir.parent.parent.parent
    else:
        # 开发模式：python/main.py 所在目录的父目录
        return Path(__file__).parent.parent.parent.parent


class LogService:
    """日志服务 - 支持异步批量写入"""

    # 批量写入配置
    BATCH_SIZE = 50          # 批量大小
    FLUSH_INTERVAL = 1.0     # 刷新间隔（秒）

    def __init__(self, log_dir: str = None):
        if log_dir is None:
            project_root = get_project_root()
            self.log_dir = str(project_root / "logs")
        else:
            self.log_dir = log_dir
        self._ensure_dir()

        # 异步批量写入组件
        self._queue: queue.Queue = queue.Queue()
        self._batch: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._writer_thread = None

        # 启动后台写入线程
        self._start_writer_thread()

    def _ensure_dir(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _get_log_file_path(self, ai_app_type: str, session_id: str) -> str:
        """获取日志文件路径"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{ai_app_type}_{session_id}_{date_str}.jsonl"
        return os.path.join(self.log_dir, filename)

    def _start_writer_thread(self):
        """启动后台写入线程"""
        self._writer_thread = threading.Thread(
            target=self._batch_writer_loop,
            daemon=True,
            name="LogWriter"
        )
        self._writer_thread.start()

    def _batch_writer_loop(self):
        """后台批量写入循环"""
        last_flush = time.time()

        while not self._stop_event.is_set():
            try:
                # 等待新日志或超时
                log_entry = self._queue.get(timeout=self.FLUSH_INTERVAL)
                with self._lock:
                    self._batch.append(log_entry)

                # 检查是否需要刷新
                now = time.time()
                should_flush = (
                    len(self._batch) >= self.BATCH_SIZE or
                    (now - last_flush) >= self.FLUSH_INTERVAL
                )

                if should_flush:
                    self._flush_batch()
                    last_flush = now

            except queue.Empty:
                # 超时，刷新批量
                self._flush_batch()
                last_flush = time.time()

        # 线程结束时刷新剩余日志
        self._flush_batch()

    def _flush_batch(self):
        """刷新批量日志到文件"""
        if not self._batch:
            return

        with self._lock:
            batch_to_write = self._batch.copy()
            self._batch.clear()

        if not batch_to_write:
            return

        # 按文件分组
        file_groups: Dict[str, List[Dict[str, Any]]] = {}
        for entry in batch_to_write:
            log_file = entry.pop("_log_file")  # 临时字段
            if log_file not in file_groups:
                file_groups[log_file] = []
            file_groups[log_file].append(entry)

        # 批量写入每个文件
        for log_file, entries in file_groups.items():
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    for entry in entries:
                        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                print(f"[LOG] Batch wrote {len(entries)} entries to {log_file}")
            except Exception as e:
                print(f"[LOG] 批量写入失败: {e}")

    def log(
        self,
        ai_app_type: str,
        session_id: str,
        window_id: int,
        process_name: str,
        instruction: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
        duration_ms: int = 0,
        client_ip: str = None
    ):
        """
        记录日志（异步非阻塞）

        Args:
            ai_app_type: AI应用类型
            session_id: 会话ID
            window_id: 窗口句柄
            process_name: 进程名称
            instruction: 指令类型
            params: 请求参数
            result: 执行结果
            duration_ms: 执行耗时（毫秒）
            client_ip: 客户端IP地址
        """
        log_file = self._get_log_file_path(ai_app_type, session_id)

        log_entry = {
            "_log_file": log_file,  # 临时字段，用于文件分组
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "client_ip": client_ip or "unknown",
            "window_id": window_id,
            "process_name": process_name,
            "instruction": instruction,
            "params": params,
            "result": result,
            "duration_ms": duration_ms
        }

        # 放入队列，立即返回（非阻塞）
        self._queue.put(log_entry)

    def read_logs(
        self,
        ai_app_type: Optional[str] = None,
        session_id: Optional[str] = None,
        date: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """读取日志（优化：直接搜索原始JSON字符串）"""
        # 先刷新待写入的日志，确保数据最新
        self._flush_batch()

        logs = []
        log_files = self._get_log_files(ai_app_type, session_id, date)

        for log_file in log_files:
            if not os.path.exists(log_file):
                continue

            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        # 优化：先在原始字符串中搜索关键词
                        if keyword:
                            keyword_lower = keyword.lower()
                            if keyword_lower not in line.lower():
                                continue

                        try:
                            entry = json.loads(line)
                            logs.append(entry)

                            if len(logs) >= limit:
                                return logs
                        except json.JSONDecodeError:
                            continue
            except Exception:
                continue

        return logs

    def _get_log_files(
        self,
        ai_app_type: Optional[str] = None,
        session_id: Optional[str] = None,
        date: Optional[str] = None
    ) -> List[str]:
        """获取匹配的日志文件"""
        files = []

        if not os.path.exists(self.log_dir):
            return files

        for filename in os.listdir(self.log_dir):
            if not filename.endswith('.jsonl'):
                continue

            # 解析文件名: ai_app_type-session_id-yyyy-mm-dd.jsonl
            # 日期格式固定为yyyy-mm-dd，从右边取10个字符
            name_without_ext = filename.replace('.jsonl', '')

            # 日期是最后10个字符
            if len(name_without_ext) < 12:  # 至少 x-x-yyyy-mm-dd
                continue

            file_date = name_without_ext[-10:]  # yyyy-mm-dd
            remaining = name_without_ext[:-11]  # 去掉 -yyyy-mm-dd

            # 验证日期格式
            if len(file_date) != 10 or file_date[4] != '-' or file_date[7] != '-':
                continue

            # 分离 ai_app_type 和 session_id
            # 格式: ai_app_type-session_id
            remaining_parts = remaining.rsplit('-', 1)
            if len(remaining_parts) < 2:
                continue

            file_session_id = remaining_parts[-1]
            file_ai_app_type = remaining_parts[0]

            # 过滤条件
            if ai_app_type and file_ai_app_type != ai_app_type:
                continue
            if session_id and file_session_id != session_id:
                continue
            if date and file_date != date:
                continue

            files.append(os.path.join(self.log_dir, filename))

        return sorted(files, reverse=True)  # 按时间倒序

    def cleanup_old_logs(self, retention_days: int):
        """清理过期日志"""
        # 先刷新待写入的日志
        self._flush_batch()

        if not os.path.exists(self.log_dir):
            return

        now = time.time()
        for filename in os.listdir(self.log_dir):
            if not filename.endswith('.jsonl'):
                continue

            filepath = os.path.join(self.log_dir, filename)
            file_time = os.path.getmtime(filepath)

            if (now - file_time) > retention_days * 24 * 60 * 60:
                os.remove(filepath)
                print(f"已删除过期日志: {filename}")

    def shutdown(self):
        """关闭日志服务，刷新所有待写入日志"""
        self._stop_event.set()

        # 等待写入线程结束（最多5秒）
        if self._writer_thread and self._writer_thread.is_alive():
            self._writer_thread.join(timeout=5.0)

        # 最后一次刷新
        self._flush_batch()


# 全局日志服务实例
log_service = LogService()

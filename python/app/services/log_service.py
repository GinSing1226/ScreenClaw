"""
日志服务
"""
import os
import sys
import json
import time
from datetime import datetime
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
    """日志服务"""

    def __init__(self, log_dir: str = None):
        if log_dir is None:
            project_root = get_project_root()
            self.log_dir = str(project_root / "logs")
        else:
            self.log_dir = log_dir
        self._ensure_dir()

    def _ensure_dir(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _get_log_file_path(self, ai_app_type: str, session_id: str) -> str:
        """获取日志文件路径"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{ai_app_type}-{session_id}-{date_str}.jsonl"
        return os.path.join(self.log_dir, filename)

    def log(
        self,
        ai_app_type: str,
        session_id: str,
        window_id: int,
        process_name: str,
        instruction: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
        duration_ms: int = 0
    ):
        """
        记录日志

        Args:
            ai_app_type: AI应用类型
            session_id: 会话ID
            window_id: 窗口句柄
            process_name: 进程名称
            instruction: 指令类型
            params: 请求参数
            result: 执行结果
            duration_ms: 执行耗时（毫秒）
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "window_id": window_id,
            "process_name": process_name,
            "instruction": instruction,
            "params": params,
            "result": result,
            "duration_ms": duration_ms
        }

        log_file = self._get_log_file_path(ai_app_type, session_id)

        # 调试信息
        print(f"[LOG] Writing log to: {log_file}")
        print(f"[LOG] ai_app_type='{ai_app_type}', session_id='{session_id}'")

        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            print(f"[LOG] Log written successfully")
        except Exception as e:
            print(f"[LOG] 写入日志失败: {e}")

    def read_logs(
        self,
        ai_app_type: Optional[str] = None,
        session_id: Optional[str] = None,
        date: Optional[str] = None,
        keyword: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """读取日志"""
        logs = []

        # 获取匹配的日志文件
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

                        try:
                            entry = json.loads(line)

                            # 关键词过滤
                            if keyword:
                                keyword_lower = keyword.lower()
                                entry_str = json.dumps(entry, ensure_ascii=False).lower()
                                if keyword_lower not in entry_str:
                                    continue

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


# 全局日志服务实例
log_service = LogService()

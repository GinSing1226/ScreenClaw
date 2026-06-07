"""
Windows Graphics Capture (WGC) 服务客户端

通过与 C# 常驻进程 screenclaw-wincapture-service 通信，
实现 DirectX / UE 引擎游戏的窗口截图。
"""
import atexit
import json
import logging
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)

WGC_DEFAULT_PORT = 12262
WGC_STARTUP_TIMEOUT = 10

# C# 服务可执行文件相对于项目根目录的路径模式 (开发环境)
_WGC_SERVICE_BASE = os.path.join(
    "src-wincapture", "bin",
    "{config}",  # "Release" or "Debug"
    "net9.0-windows10.0.22621.0",
    "screenclaw-wincapture-service.exe",
)
# 发布版本路径 (自包含 .NET 运行时)
_WGC_SERVICE_PUBLISH = os.path.join(
    "src-wincapture", "bin",
    "Release",
    "net9.0-windows10.0.22621.0",
    "win-x64", "publish",
    "screenclaw-wincapture-service.exe",
)


def _find_service_exe() -> Optional[str]:
    """查找 C# WGC 服务可执行文件。

    查找顺序：
    1. 环境变量 SCREENCLAW_WGC_SERVICE
    2. 打包环境：_MEIPASS 临时目录（单文件模式）/ exe 所在目录
    3. 开发环境：基于当前文件的相对路径
    """
    service_name = "screenclaw-wincapture-service.exe"

    # 1) 环境变量优先
    env_path = os.environ.get("SCREENCLAW_WGC_SERVICE")
    if env_path and Path(env_path).exists():
        return env_path

    # 2) 打包环境
    if getattr(sys, 'frozen', False):
        # 2a) 单文件模式：数据解压到 _MEIPASS 临时目录
        if hasattr(sys, '_MEIPASS'):
            meipass_dir = Path(sys._MEIPASS)  # type: ignore
            candidate = meipass_dir / "wgc-service" / service_name
            if candidate.exists():
                return str(candidate)
            logger.warning("[wgc] 打包环境 _MEIPASS 未找到: %s", candidate)

        # 2b) exe 所在目录（便携安装）
        exe_dir = Path(sys.executable).parent
        candidate = exe_dir / "wgc-service" / service_name
        if candidate.exists():
            return str(candidate)
        logger.warning("[wgc] 打包环境 exe_dir 未找到: %s", candidate)

    # 3) 开发环境：基于当前文件的相对路径
    try:
        root = Path(__file__).resolve().parents[4]
        candidates = [
            root / "wgc-service" / service_name,
            root / "src-wincapture" / "bin" / "Release" / "net9.0-windows10.0.22621.0" / "win-x64" / "publish" / service_name,
            root / "src-wincapture" / "bin" / "Release" / "net9.0-windows10.0.22621.0" / service_name,
            root / "src-wincapture" / "bin" / "Debug" / "net9.0-windows10.0.22621.0" / service_name,
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
    except Exception as e:
        logger.debug("[wgc] 开发环境查找失败: %s", e)

    logger.error("[wgc] 未找到服务")
    return None


class WGCClient:
    """WGC 截图服务客户端 — 管理与 C# 常驻进程的生命周期和通信。"""

    def __init__(self, port: int = WGC_DEFAULT_PORT):
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self._process: Optional[subprocess.Popen] = None
        self._service_path: Optional[str] = _find_service_exe()
        if not self._service_path:
            logger.warning("[wgc] C# 服务可执行文件未找到，WGC 截图不可用")

    # ---- 生命周期 ----

    def ensure_running(self) -> bool:
        """确保 WGC 服务正在运行，如未运行则尝试启动。"""
        if self._is_healthy():
            logger.debug("[wgc] 服务已在运行")
            return True
        logger.info("[wgc] 服务未运行，尝试启动...")
        return self._start()

    def _is_healthy(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/health", timeout=2):
                return True
        except Exception:
            return False

    def _start(self) -> bool:
        if not self._service_path:
            logger.error("[wgc] 启动失败: 服务路径未找到")
            return False

        logger.info("[wgc] 正在启动服务: %s (port=%d)", self._service_path, self.port)

        try:
            flags = 0
            if sys.platform == "win32":
                flags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]

            self._process = subprocess.Popen(
                [self._service_path, "--port", str(self.port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
            )

            logger.debug("[wgc] 进程已启动, pid=%s", self._process.pid)

            deadline = time.time() + WGC_STARTUP_TIMEOUT
            while time.time() < deadline:
                if self._is_healthy():
                    logger.info("[wgc] 服务已启动 (port=%d)", self.port)
                    return True
                time.sleep(0.3)

            # 超时后检查进程是否还在运行
            if self._process.poll() is not None:
                logger.error("[wgc] 服务进程已退出, exit code=%s", self._process.returncode)
            else:
                logger.error("[wgc] 服务启动超时 (进程仍在运行但健康检查失败)")
            return False

        except Exception as e:
            logger.error("[wgc] 启动失败: %s", e, exc_info=True)
            return False

    def stop(self):
        """停止 WGC 服务。"""
        try:
            with urllib.request.urlopen(f"{self.base_url}/shutdown", timeout=2):
                pass
        except Exception:
            pass

        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
            self._process = None

    # ---- 截图 ----

    def capture(self, hwnd: int) -> Tuple[bool, Optional[Image.Image], Optional[str]]:
        """
        通过 WGC 服务截取指定窗口。

        Returns:
            (success, image, error)
        """
        if not self.ensure_running():
            return False, None, "WGC 服务不可用"

        try:
            body = json.dumps({"hwnd": hwnd}).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/capture",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            if not data.get("success"):
                return False, None, data.get("error", "WGC capture failed")

            image_path = data.get("image_path")
            if not image_path or not os.path.exists(image_path):
                return False, None, f"WGC: 图片文件不存在 {image_path}"

            image = Image.open(image_path).convert("RGB")
            return True, image, None

        except urllib.error.URLError as e:
            return False, None, f"WGC request error: {e}"
        except Exception as e:
            return False, None, f"WGC error: {e}"


# 全局单例
wgc_client = WGCClient()

# 退出时自动停止服务
atexit.register(wgc_client.stop)

"""
AutoEmu-Bridge MVP - 终端交互主程序
验证技术可行性：获取进程、后台截图、后台控制
"""
import sys
import os
import time
import threading
from typing import Optional

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from colorama import init, Fore, Style

# 初始化 colorama
init(autoreset=True)

from core.window_manager import WindowManager, WindowInfo
from core.capture import ScreenCapture, GridOverlay, GridConfig
from core.controller import WindowController


class AutoEmuBridge:
    """AutoEmu-Bridge 主类"""

    def __init__(self):
        self.window_manager = WindowManager()
        self.current_window: Optional[WindowInfo] = None
        self.render_window: Optional[WindowInfo] = None
        self.capture: Optional[ScreenCapture] = None
        self.controller: Optional[WindowController] = None
        self.grid_overlay = GridOverlay()

        self.running = False
        self._auto_capture_thread: Optional[threading.Thread] = None

    def list_windows(self, emulator_type: str = None):
        """列出窗口"""
        print(f"\n{Fore.CYAN}═══════════════════════════════════════════════════════════════")
        print(f"  窗口列表")
        print(f"═══════════════════════════════════════════════════════════════{Style.RESET_ALL}")

        if emulator_type:
            windows = self.window_manager.find_emulator_windows(emulator_type)
            print(f"  搜索模拟器类型: {emulator_type}")
        else:
            windows = self.window_manager.enum_all_windows()

        if not windows:
            print(f"{Fore.YELLOW}  未找到窗口{Style.RESET_ALL}")
            return []

        for i, win in enumerate(windows[:30]):  # 限制显示前30个
            marker = ""
            if self.current_window and win.hwnd == self.current_window.hwnd:
                marker = f"{Fore.GREEN} ◄ 当前{Style.RESET_ALL}"

            print(f"  [{i:2d}] {Fore.YELLOW}HWND:{win.hwnd:8d}{Style.RESET_ALL} | "
                  f"Size: {win.width:4d}x{win.height:4d} | "
                  f"{Fore.CYAN}{win.class_name[:25]:25s}{Style.RESET_ALL} | "
                  f"{win.title[:35]}{marker}")

        print()
        return windows

    def attach_window(self, index: int, windows: list) -> bool:
        """挂载窗口"""
        if index < 0 or index >= len(windows):
            print(f"{Fore.RED}无效的窗口索引{Style.RESET_ALL}")
            return False

        self.current_window = windows[index]

        # 查找渲染子窗口
        self.render_window = self.window_manager.find_render_window(
            self.current_window.hwnd,
            min_size=(200, 200)
        )

        if self.render_window:
            print(f"{Fore.GREEN}✓ 挂载成功!{Style.RESET_ALL}")
            print(f"  主窗口: {self.current_window.title}")
            print(f"  主句柄: {self.current_window.hwnd} ({self.current_window.width}x{self.current_window.height})")
            print(f"  渲染窗口句柄: {self.render_window.hwnd} ({self.render_window.width}x{self.render_window.height})")

            # 初始化截图器和控制器
            target_hwnd = self.render_window.hwnd
            self.capture = ScreenCapture(target_hwnd)
            self.controller = WindowController(target_hwnd)
            return True
        else:
            # 没有找到子窗口，使用主窗口
            print(f"{Fore.YELLOW}⚠ 未找到渲染子窗口，使用主窗口{Style.RESET_ALL}")
            print(f"  主窗口: {self.current_window.title}")
            print(f"  句柄: {self.current_window.hwnd} ({self.current_window.width}x{self.current_window.height})")

            self.render_window = self.current_window
            self.capture = ScreenCapture(self.current_window.hwnd)
            self.controller = WindowController(self.current_window.hwnd)
            return True

    def screenshot(self, with_grid: bool = True, method: str = 'auto') -> Optional[str]:
        """截图"""
        if not self.capture:
            print(f"{Fore.RED}请先挂载窗口 (attach 命令){Style.RESET_ALL}")
            return None

        if not self.window_manager.is_window_valid(self.capture.hwnd):
            print(f"{Fore.RED}窗口已失效，请重新挂载{Style.RESET_ALL}")
            self.capture = None
            self.controller = None
            return None

        print(f"{Fore.CYAN}正在截图... (方法: {method}){Style.RESET_ALL}")
        img = self.capture.capture(method=method)

        if img is None:
            print(f"{Fore.RED}截图失败{Style.RESET_ALL}")
            return None

        if with_grid:
            img = self.grid_overlay.apply_grid(img)

        path = self.capture.save_capture(img)
        print(f"{Fore.GREEN}✓ 截图已保存: {path}{Style.RESET_ALL}")
        return path

    def click(self, x: float, y: float):
        """点击"""
        if not self.controller:
            print(f"{Fore.RED}请先挂载窗口 (attach 命令){Style.RESET_ALL}")
            return False

        if not self.controller.is_window_valid():
            print(f"{Fore.RED}窗口已失效，请重新挂载{Style.RESET_ALL}")
            self.capture = None
            self.controller = None
            return False

        return self.controller.click(x, y)

    def long_press(self, x: float, y: float, duration: float = 2.0):
        """长按"""
        if not self.controller:
            print(f"{Fore.RED}请先挂载窗口 (attach 命令){Style.RESET_ALL}")
            return False

        if not self.controller.is_window_valid():
            print(f"{Fore.RED}窗口已失效，请重新挂载{Style.RESET_ALL}")
            return False

        return self.controller.long_press(x, y, duration=duration)

    def swipe(self, x1: float, y1: float, x2: float, y2: float, duration: float = 0.3):
        """滑动"""
        if not self.controller:
            print(f"{Fore.RED}请先挂载窗口 (attach 命令){Style.RESET_ALL}")
            return False

        if not self.controller.is_window_valid():
            print(f"{Fore.RED}窗口已失效，请重新挂载{Style.RESET_ALL}")
            return False

        return self.controller.swipe(x1, y1, x2, y2, duration=duration)

    def show_status(self):
        """显示状态"""
        print(f"\n{Fore.CYAN}═══════════════════════════════════════════════════════════════")
        print(f"  当前状态")
        print(f"═══════════════════════════════════════════════════════════════{Style.RESET_ALL}")

        if self.current_window:
            print(f"  挂载窗口: {self.current_window.title}")
            print(f"  主句柄:   {self.current_window.hwnd}")
            if self.render_window:
                print(f"  渲染句柄: {self.render_window.hwnd}")
                print(f"  窗口尺寸: {self.render_window.width}x{self.render_window.height}")
        else:
            print(f"  {Fore.YELLOW}未挂载任何窗口{Style.RESET_ALL}")

        print()


def print_help():
    """打印帮助"""
    print(f"""
{Fore.CYAN}═════════════════════════════════════════════════════════════════════
  AutoEmu-Bridge MVP - 命令帮助
═════════════════════════════════════════════════════════════════════{Style.RESET_ALL}

{Fore.YELLOW}窗口管理{Style.RESET_ALL}
  list              列出所有可见窗口
  list mumu         列出 MuMu 模拟器窗口
  attach <index>    挂载指定索引的窗口
  status            显示当前状态

{Fore.YELLOW}截图操作{Style.RESET_ALL}
  screenshot        截图（带网格）
  screenshot raw    截图（不带网格）
  screenshot bitblt 使用 BitBlt 方式截图
  screenshot print  使用 PrintWindow 方式截图

{Fore.YELLOW}控制操作 (坐标为百分比，0-1){Style.RESET_ALL}
  click <x> <y>              点击 (例: click 0.5 0.5)
  longpress <x> <y> [秒]     长按 (例: longpress 0.5 0.5 2)
  swipe <x1> <y1> <x2> <y2> [秒]  滑动 (例: swipe 0.2 0.5 0.8 0.5)

{Fore.YELLOW}网格设置{Style.RESET_ALL}
  grid interval <0.1-0.5>    设置网格间隔 (默认 0.1 = 10%)

{Fore.YELLOW}其他{Style.RESET_ALL}
  help              显示此帮助
  exit / quit       退出程序
  Ctrl+C            强制退出

""")


def main():
    """主函数"""
    bridge = AutoEmuBridge()
    windows = []

    print(f"""
{Fore.CYAN}╔═════════════════════════════════════════════════════════════════════╗
║                                                                     ║
║   {Fore.YELLOW}AutoEmu-Bridge MVP{Fore.CYAN} - 安卓模拟器后台 RPA 代理网关           ║
║                                                                     ║
║   验证模式: 获取进程 → 后台截图 → 后台控制                          ║
║                                                                     ║
╚═════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

输入 {Fore.YELLOW}help{Style.RESET_ALL} 查看命令列表
""")

    while True:
        try:
            cmd = input(f"{Fore.GREEN}AutoEmu>{Style.RESET_ALL} ").strip()

            if not cmd:
                continue

            parts = cmd.split()
            action = parts[0].lower()

            # ----- 窗口管理 -----
            if action == 'list':
                emulator_type = parts[1] if len(parts) > 1 else None
                windows = bridge.list_windows(emulator_type)

            elif action == 'attach':
                if len(parts) < 2:
                    print(f"{Fore.RED}用法: attach <窗口索引>{Style.RESET_ALL}")
                    continue
                try:
                    index = int(parts[1])
                    bridge.attach_window(index, windows)
                except ValueError:
                    print(f"{Fore.RED}索引必须是数字{Style.RESET_ALL}")

            elif action == 'status':
                bridge.show_status()

            # ----- 截图 -----
            elif action == 'screenshot':
                with_grid = 'raw' not in parts
                method = 'auto'
                if 'bitblt' in parts:
                    method = 'bitblt'
                elif 'print' in parts:
                    method = 'printwindow'
                bridge.screenshot(with_grid=with_grid, method=method)

            # ----- 控制 -----
            elif action == 'click':
                if len(parts) < 3:
                    print(f"{Fore.RED}用法: click <x> <y>{Style.RESET_ALL}")
                    continue
                try:
                    x, y = float(parts[1]), float(parts[2])
                    bridge.click(x, y)
                except ValueError:
                    print(f"{Fore.RED}坐标必须是数字{Style.RESET_ALL}")

            elif action == 'longpress':
                if len(parts) < 3:
                    print(f"{Fore.RED}用法: longpress <x> <y> [秒]{Style.RESET_ALL}")
                    continue
                try:
                    x, y = float(parts[1]), float(parts[2])
                    duration = float(parts[3]) if len(parts) > 3 else 2.0
                    bridge.long_press(x, y, duration)
                except ValueError:
                    print(f"{Fore.RED}参数必须是数字{Style.RESET_ALL}")

            elif action == 'swipe':
                if len(parts) < 5:
                    print(f"{Fore.RED}用法: swipe <x1> <y1> <x2> <y2> [秒]{Style.RESET_ALL}")
                    continue
                try:
                    x1, y1 = float(parts[1]), float(parts[2])
                    x2, y2 = float(parts[3]), float(parts[4])
                    duration = float(parts[5]) if len(parts) > 5 else 0.3
                    bridge.swipe(x1, y1, x2, y2, duration)
                except ValueError:
                    print(f"{Fore.RED}参数必须是数字{Style.RESET_ALL}")

            # ----- 网格设置 -----
            elif action == 'grid':
                if len(parts) >= 3 and parts[1] == 'interval':
                    try:
                        interval = float(parts[2])
                        if 0.05 <= interval <= 0.5:
                            bridge.grid_overlay.set_config(interval=interval)
                            print(f"{Fore.GREEN}网格间隔已设置为 {interval}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}间隔范围: 0.05 - 0.5{Style.RESET_ALL}")
                    except ValueError:
                        print(f"{Fore.RED}间隔必须是数字{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}用法: grid interval <0.05-0.5>{Style.RESET_ALL}")

            # ----- 其他 -----
            elif action in ('help', '?'):
                print_help()

            elif action in ('exit', 'quit', 'q'):
                print(f"\n{Fore.CYAN}再见!{Style.RESET_ALL}")
                break

            else:
                print(f"{Fore.RED}未知命令: {action}。输入 help 查看帮助。{Style.RESET_ALL}")

        except KeyboardInterrupt:
            print(f"\n\n{Fore.CYAN}强制退出{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"{Fore.RED}错误: {e}{Style.RESET_ALL}")


if __name__ == '__main__':
    main()

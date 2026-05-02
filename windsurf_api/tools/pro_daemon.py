"""Pro 注入守护进程 — 持续监控并自动注入 Pro 实验

Windsurf 重启后实验会重置。本守护进程:
  - 持续监控 LS 进程状态
  - 检测到 LS 启动后自动注入 Pro 实验
  - 支持后台运行
  - 断线自动重连

用法::

    daemon = ProDaemon()
    daemon.start()          # 阻塞运行
    daemon.start_background()  # 后台守护

    # 或命令行:
    python -m windsurf_api.tools.pro_daemon
"""
import time
import threading
import sys
from typing import Optional

from ..services.language_server import LanguageServerService


class ProDaemon:
    """Pro 实验注入守护进程

    Args:
        check_interval: 检查间隔秒数
        retry_interval: 重试间隔秒数
        api_key: API Key (用于 LS 元数据)
        verbose: 是否打印日志
    """

    def __init__(self, *, check_interval: int = 30, retry_interval: int = 10,
                 api_key: str = "", verbose: bool = True):
        self.check_interval = check_interval
        self.retry_interval = retry_interval
        self.api_key = api_key
        self.verbose = verbose
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._ls: Optional[LanguageServerService] = None
        self._injected = False
        self._last_port = 0

    def _log(self, msg: str):
        if self.verbose:
            t = time.strftime("%H:%M:%S")
            print(f"[{t}] ProDaemon: {msg}")

    def _try_connect(self) -> bool:
        """尝试连接 LS"""
        try:
            ls = LanguageServerService(api_key=self.api_key)
            ls.auto_connect()
            if ls.port:
                self._ls = ls
                self._last_port = ls.port
                return True
        except Exception as e:
            self._log(f"连接失败: {e}")
        return False

    def _try_inject(self) -> bool:
        """尝试注入 Pro 实验"""
        if not self._ls or not self._ls.port:
            return False
        try:
            r = self._ls.inject_pro_experiments()
            if r and r.ok:
                self._log(f"✅ Pro 实验注入成功 (port={self._ls.port})")
                self._injected = True
                return True
            else:
                self._log(f"⚠️ 注入返回异常: {r}")
        except Exception as e:
            self._log(f"❌ 注入失败: {e}")
            self._ls = None
            self._injected = False
        return False

    def _check_alive(self) -> bool:
        """检查 LS 是否还活着"""
        if not self._ls or not self._ls.port:
            return False
        try:
            r = self._ls.heartbeat()
            return r and r.ok
        except Exception:
            return False

    def _loop(self):
        """主循环"""
        self._log("🚀 守护进程启动")
        self._log(f"   检查间隔: {self.check_interval}s")

        while self._running:
            try:
                if self._ls and self._injected:
                    # 已注入 — 定期检查 LS 是否还活着
                    if self._check_alive():
                        time.sleep(self.check_interval)
                        continue
                    else:
                        # LS 挂了 — 等待重启
                        self._log("⚠️ LS 断开，等待重启...")
                        self._ls = None
                        self._injected = False
                        time.sleep(self.retry_interval)
                        continue

                # 未连接 — 尝试连接
                if self._try_connect():
                    self._log(f"🔗 连接到 LS (port={self._ls.port})")
                    # 连上了 — 立即注入
                    self._try_inject()
                else:
                    # 连不上 — 等等再试
                    time.sleep(self.retry_interval)
                    continue

            except Exception as e:
                self._log(f"❌ 循环异常: {e}")
                self._ls = None
                self._injected = False
                time.sleep(self.retry_interval)

            time.sleep(2)

    def start(self):
        """启动守护 (阻塞)"""
        self._running = True
        try:
            self._loop()
        except KeyboardInterrupt:
            self._log("⏹ 守护进程已停止")
            self._running = False

    def start_background(self) -> threading.Thread:
        """后台启动守护 (非阻塞)"""
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._log("🚀 后台守护进程已启动")
        return self._thread

    def stop(self):
        """停止守护"""
        self._running = False
        self._log("⏹ 正在停止...")

    @property
    def status(self) -> dict:
        """当前状态"""
        return {
            "running": self._running,
            "connected": self._ls is not None and self._ls.port > 0,
            "injected": self._injected,
            "port": self._last_port,
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Windsurf Pro 注入守护进程")
    parser.add_argument("--interval", type=int, default=30, help="检查间隔秒数")
    parser.add_argument("--key", type=str, default="", help="API Key")
    args = parser.parse_args()

    daemon = ProDaemon(check_interval=args.interval, api_key=args.key)
    daemon.start()

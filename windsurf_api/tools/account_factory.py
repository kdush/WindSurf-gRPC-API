"""批量账号工厂 — 自动化注册 Windsurf 账号并收集 API Key

支持:
  - 批量邮箱注册
  - GitHub Token 批量注册
  - 自动收集 API Key
  - 结果导出 (JSON / 文本)
  - 并发注册

用法::

    factory = AccountFactory()

    # 单个注册
    result = factory.register_email("test@example.com", "password123")
    print(result)  # {"ok": True, "api_key": "sk-ws-...", "email": "..."}

    # 批量注册
    accounts = [
        ("user1@test.com", "pass1"),
        ("user2@test.com", "pass2"),
    ]
    results = factory.batch_register_email(accounts)

    # 导出 Keys
    factory.export_keys("keys.txt")
"""
import json
import time
import threading
from typing import Optional
from dataclasses import dataclass, field

from ..auth import email_signup, email_login, oauth_login, refresh_token
from ..transport import ConnectTransport
from ..services.seat_management import SeatManagementService


REGISTER_SERVER = "https://register.windsurf.com"


@dataclass
class AccountResult:
    """注册结果"""
    ok: bool = False
    email: str = ""
    api_key: str = ""
    id_token: str = ""
    refresh_token: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "email": self.email,
            "api_key": self.api_key,
            "error": self.error,
        }


class AccountFactory:
    """批量账号工厂

    Args:
        delay: 每次注册间隔秒数 (避免限速)
        max_workers: 最大并发数
    """

    def __init__(self, delay: float = 2.0, max_workers: int = 3):
        self.delay = delay
        self.max_workers = max_workers
        self.results: list[AccountResult] = []
        self._lock = threading.Lock()

    def register_email(self, email: str, password: str) -> AccountResult:
        """邮箱注册单个账号

        Args:
            email: 邮箱
            password: 密码 (至少6位)

        Returns:
            AccountResult
        """
        result = AccountResult(email=email)

        try:
            # Step 1: Firebase 注册
            user = email_signup(email, password)
            if not user.ok:
                result.error = f"Firebase signup failed: {user.error}"
                self._save(result)
                return result

            result.id_token = user.id_token
            result.refresh_token = user.refresh_token

            # Step 2: Windsurf 注册
            transport = ConnectTransport(REGISTER_SERVER)
            seat = SeatManagementService(transport, "")
            reg_result = seat.register_user(user.id_token)

            if reg_result.ok:
                result.ok = True
                result.api_key = reg_result.api_key
            else:
                result.error = f"Windsurf register failed"

        except Exception as e:
            result.error = str(e)

        self._save(result)
        return result

    def register_github(self, github_token: str) -> AccountResult:
        """GitHub Token 注册

        Args:
            github_token: GitHub access token

        Returns:
            AccountResult
        """
        result = AccountResult()

        try:
            # Step 1: Firebase OAuth
            user = oauth_login("github", github_token)
            if not user.ok:
                result.error = f"Firebase GitHub auth failed: {user.error}"
                self._save(result)
                return result

            result.email = user.email or ""
            result.id_token = user.id_token
            result.refresh_token = user.refresh_token

            # Step 2: Windsurf 注册
            transport = ConnectTransport(REGISTER_SERVER)
            seat = SeatManagementService(transport, "")
            reg_result = seat.register_user(user.id_token)

            if reg_result.ok:
                result.ok = True
                result.api_key = reg_result.api_key
            else:
                result.error = "Windsurf register failed"

        except Exception as e:
            result.error = str(e)

        self._save(result)
        return result

    def batch_register_email(self, accounts: list) -> list:
        """批量邮箱注册

        Args:
            accounts: [(email, password), ...] 列表

        Returns:
            list of AccountResult
        """
        results = []
        semaphore = threading.Semaphore(self.max_workers)

        def _worker(email, password):
            with semaphore:
                r = self.register_email(email, password)
                results.append(r)
                time.sleep(self.delay)

        threads = []
        for email, password in accounts:
            t = threading.Thread(target=_worker, args=(email, password))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return results

    def batch_register_github(self, tokens: list) -> list:
        """批量 GitHub 注册

        Args:
            tokens: GitHub access token 列表

        Returns:
            list of AccountResult
        """
        results = []
        for token in tokens:
            r = self.register_github(token)
            results.append(r)
            time.sleep(self.delay)
        return results

    def _save(self, result: AccountResult):
        with self._lock:
            self.results.append(result)

    def get_keys(self) -> list:
        """获取所有成功注册的 API Key"""
        return [r.api_key for r in self.results if r.ok and r.api_key]

    def export_keys(self, filepath: str, format: str = "txt"):
        """导出 Key 到文件

        Args:
            filepath: 输出文件路径
            format: "txt" (每行一个key) 或 "json"
        """
        if format == "json":
            data = [r.to_dict() for r in self.results]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            keys = self.get_keys()
            with open(filepath, "w") as f:
                for k in keys:
                    f.write(k + "\n")

    def summary(self) -> dict:
        """获取注册统计摘要"""
        total = len(self.results)
        ok = sum(1 for r in self.results if r.ok)
        return {
            "total": total,
            "success": ok,
            "failed": total - ok,
            "keys": self.get_keys(),
        }

"""Key Pool — 多 API Key 轮换 + 健康检查 + 自动禁用

支持:
  - Round-Robin 轮换
  - 失败自动冷却 (cooldown)
  - 定期健康检查
  - Key 动态添加/移除
"""
import time
import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KeyState:
    """单个 Key 的运行状态"""
    key: str
    healthy: bool = True
    total_calls: int = 0
    total_errors: int = 0
    last_used: float = 0.0
    last_error: float = 0.0
    cooldown_until: float = 0.0
    error_message: str = ""

    @property
    def available(self) -> bool:
        return self.healthy and time.time() >= self.cooldown_until


class KeyPool:
    """多 Key 轮换池

    用法::

        pool = KeyPool(["sk-ws-key1", "sk-ws-key2", "sk-ws-key3"])
        key = pool.next()            # 拿一个可用的 key
        pool.report_success(key)     # 报告成功
        pool.report_error(key, "rate limited")  # 报告失败 → 自动冷却

    配置::

        pool = KeyPool(keys, cooldown=60, max_errors=5)
    """

    def __init__(self, keys: list, *, cooldown: int = 60, max_errors: int = 10):
        """
        Args:
            keys: API Key 列表
            cooldown: 错误后冷却秒数
            max_errors: 连续错误次数阈值后标记不健康
        """
        self.cooldown = cooldown
        self.max_errors = max_errors
        self._lock = threading.Lock()
        self._index = 0
        self._states: dict[str, KeyState] = {}

        for k in keys:
            k = k.strip()
            if k:
                self._states[k] = KeyState(key=k)

    @property
    def size(self) -> int:
        return len(self._states)

    @property
    def available_count(self) -> int:
        return sum(1 for s in self._states.values() if s.available)

    def add_key(self, key: str):
        """动态添加 Key"""
        key = key.strip()
        if key and key not in self._states:
            with self._lock:
                self._states[key] = KeyState(key=key)

    def remove_key(self, key: str):
        """动态移除 Key"""
        with self._lock:
            self._states.pop(key, None)

    def next(self) -> Optional[str]:
        """获取下一个可用 Key (Round-Robin)

        Returns:
            可用的 API Key，全部不可用时返回 None
        """
        with self._lock:
            keys = list(self._states.keys())
            if not keys:
                return None

            n = len(keys)
            for _ in range(n):
                idx = self._index % n
                self._index += 1
                state = self._states[keys[idx]]
                if state.available:
                    state.last_used = time.time()
                    state.total_calls += 1
                    return state.key

            # 全部冷却中 — 返回冷却时间最短的
            soonest = min(self._states.values(), key=lambda s: s.cooldown_until)
            soonest.last_used = time.time()
            soonest.total_calls += 1
            return soonest.key

    def report_success(self, key: str):
        """报告调用成功"""
        with self._lock:
            if key in self._states:
                state = self._states[key]
                state.healthy = True
                state.total_errors = 0
                state.error_message = ""

    def report_error(self, key: str, message: str = "", permanent: bool = False):
        """报告调用错误

        Args:
            key: 出错的 Key
            message: 错误信息
            permanent: 是否永久禁用 (如 Key 无效)
        """
        with self._lock:
            if key not in self._states:
                return
            state = self._states[key]
            state.total_errors += 1
            state.last_error = time.time()
            state.error_message = message

            if permanent:
                state.healthy = False
                state.cooldown_until = float("inf")
            elif state.total_errors >= self.max_errors:
                state.healthy = False
                state.cooldown_until = time.time() + self.cooldown * 5
            else:
                state.cooldown_until = time.time() + self.cooldown

    def reset(self, key: str):
        """重置 Key 状态"""
        with self._lock:
            if key in self._states:
                state = self._states[key]
                state.healthy = True
                state.total_errors = 0
                state.cooldown_until = 0.0
                state.error_message = ""

    def reset_all(self):
        """重置所有 Key"""
        with self._lock:
            for state in self._states.values():
                state.healthy = True
                state.total_errors = 0
                state.cooldown_until = 0.0
                state.error_message = ""

    def status(self) -> list:
        """获取所有 Key 状态

        Returns:
            list of dict — 每个 Key 的状态快照
        """
        result = []
        for state in self._states.values():
            result.append({
                "key": state.key[:12] + "..." + state.key[-4:],
                "healthy": state.healthy,
                "available": state.available,
                "total_calls": state.total_calls,
                "total_errors": state.total_errors,
                "error": state.error_message,
            })
        return result

    def __len__(self):
        return len(self._states)

    def __bool__(self):
        return len(self._states) > 0

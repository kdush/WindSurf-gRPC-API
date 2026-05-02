"""Cascade 对话自动化 — 程序化控制 Windsurf AI 聊天

支持:
  - 发起新对话
  - 发送消息并获取回复
  - 管理对话历史
  - 批量执行任务

用法::

    bot = CascadeBot()
    bot.connect()  # 自动连接本地 LS

    # 新对话
    reply = bot.ask("帮我写一个 TODO app")
    print(reply)

    # 继续对话
    reply = bot.ask("再加个删除功能")
    print(reply)

    # 查看对话历史
    trajectories = bot.list_conversations()

注意: 需要 Windsurf IDE 正在运行。
"""
import time
from typing import Optional

from ..services.language_server import LanguageServerService


class CascadeBot:
    """Cascade 对话机器人

    Args:
        api_key: API Key (用于 LS 元数据)
        auto_connect: 是否自动连接 LS
    """

    def __init__(self, api_key: str = "", auto_connect: bool = True):
        self.api_key = api_key
        self._ls = LanguageServerService(api_key=api_key)
        self._trajectory_id: str = ""
        self._connected = False

        if auto_connect:
            self.connect()

    def connect(self) -> bool:
        """连接本地 LS

        Returns:
            是否连接成功
        """
        try:
            self._ls.auto_connect()
            if self._ls.port:
                self._connected = True
                return True
        except Exception:
            pass
        return False

    @property
    def connected(self) -> bool:
        return self._connected and self._ls.port > 0

    def ask(self, message: str, *, trajectory_id: str = "",
            wait: float = 0.5) -> Optional[str]:
        """发送消息并获取回复

        Args:
            message: 用户消息
            trajectory_id: 对话轨迹 ID (空则开新对话)
            wait: 发送后等待秒数 (让 LS 处理)

        Returns:
            AI 回复内容 (str)，失败返回 None
        """
        if not self.connected:
            return None

        tid = trajectory_id or self._trajectory_id

        try:
            if not tid:
                # 新对话
                r = self._ls.start_cascade(message=message)
                if r and r.ok:
                    data = r.data if isinstance(r.data, dict) else {}
                    self._trajectory_id = data.get("trajectoryId", "")
                    time.sleep(wait)
                    return self._get_latest_reply()
            else:
                # 继续对话
                r = self._ls.send_user_cascade_message(
                    message=message, trajectoryId=tid)
                if r and r.ok:
                    time.sleep(wait)
                    return self._get_latest_reply()

        except Exception as e:
            return f"[Error: {e}]"

        return None

    def new_conversation(self, message: str = "") -> str:
        """开始新对话

        Args:
            message: 首条消息 (可空)

        Returns:
            新的 trajectory ID
        """
        self._trajectory_id = ""
        if message:
            self.ask(message)
        return self._trajectory_id

    def _get_latest_reply(self) -> Optional[str]:
        """获取最新的 AI 回复"""
        if not self._trajectory_id:
            return None
        try:
            r = self._ls.get_cascade_trajectory_steps(
                trajectoryId=self._trajectory_id)
            if r and r.ok:
                data = r.data if isinstance(r.data, dict) else {}
                steps = data.get("steps", [])
                # 找最后一个 assistant 步骤
                for step in reversed(steps):
                    if isinstance(step, dict) and step.get("role") == "assistant":
                        return step.get("content", "")
        except Exception:
            pass
        return None

    def list_conversations(self) -> list:
        """列出所有对话轨迹

        Returns:
            list of dict — 对话轨迹列表
        """
        try:
            r = self._ls.get_all_cascade_trajectories()
            if r and r.ok:
                data = r.data if isinstance(r.data, dict) else {}
                return data.get("trajectories", [])
        except Exception:
            pass
        return []

    def get_conversation(self, trajectory_id: str) -> dict:
        """获取对话详情

        Args:
            trajectory_id: 轨迹 ID

        Returns:
            dict — 对话详情
        """
        try:
            r = self._ls.get_cascade_trajectory(trajectoryId=trajectory_id)
            if r and r.ok:
                return r.data if isinstance(r.data, dict) else {}
        except Exception:
            pass
        return {}

    def delete_conversation(self, trajectory_id: str) -> bool:
        """删除对话

        Args:
            trajectory_id: 轨迹 ID
        """
        try:
            r = self._ls.delete_cascade_trajectory(trajectoryId=trajectory_id)
            return r and r.ok
        except Exception:
            return False

    def archive_conversation(self, trajectory_id: str) -> bool:
        """归档对话"""
        try:
            r = self._ls.archive_cascade_trajectory(trajectoryId=trajectory_id)
            return r and r.ok
        except Exception:
            return False

    def get_memories(self) -> list:
        """获取 Cascade 记忆"""
        try:
            r = self._ls.get_cascade_memories()
            if r and r.ok:
                data = r.data if isinstance(r.data, dict) else {}
                return data.get("memories", [])
        except Exception:
            pass
        return []

    def batch_ask(self, questions: list, *, delay: float = 2.0) -> list:
        """批量发送问题 (每个问题开新对话)

        Args:
            questions: 问题列表
            delay: 每个问题间隔秒数

        Returns:
            list of (question, reply) tuples
        """
        results = []
        for q in questions:
            self._trajectory_id = ""
            reply = self.ask(q)
            results.append((q, reply))
            time.sleep(delay)
        return results

    def status(self) -> dict:
        """当前状态"""
        return {
            "connected": self.connected,
            "port": self._ls.port if self._ls else 0,
            "trajectory_id": self._trajectory_id,
        }

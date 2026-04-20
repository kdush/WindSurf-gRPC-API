"""windsurf-api — Windsurf IDE 逆向协议 Python 库

非官方 Python SDK，通过逆向工程实现 Windsurf IDE 的完整 gRPC 协议。
覆盖 13 个服务、560+ 方法，零依赖 (仅用 Python 标准库)。

快速上手::

    from windsurf_api import WindsurfClient

    ws = WindsurfClient(api_key="sk-ws-...")
    print(ws.get_user_status())     # 用户状态 + 额度
    print(ws.get_models())          # 可用 AI 模型列表

GitHub:  https://github.com/YOUR_USERNAME/windsurf-api
License: MIT
"""

__version__ = "3.0.0"
__author__ = "lixin"

from .client import WindsurfClient
from .transport import RpcResponse, RpcError
from .models import (
    UserStatus, ModelProvider, RegisterResult,
    TeamsTier, BillingStrategy, ExperimentKey,
)
from .auth import FirebaseUser

__all__ = [
    # 主入口
    "WindsurfClient",
    # 响应类型
    "RpcResponse",
    "RpcError",
    # 数据模型
    "UserStatus",
    "ModelProvider",
    "RegisterResult",
    "FirebaseUser",
    # 枚举
    "TeamsTier",
    "BillingStrategy",
    "ExperimentKey",
]

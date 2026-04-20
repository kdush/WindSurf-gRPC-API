"""gRPC 服务封装 — 逆向自 LS binary 的 13 个服务

服务清单 (567+ RPC methods):
    SeatManagement     142 methods  用户/团队/计费/订阅
    ApiServer          164 methods  模型/聊天/补全/部署
    LanguageServer     171 methods  本地 LS (补全/诊断/实验)
    ExtensionServer     50 methods  扩展功能
    CascadePlugins       5 methods  MCP 插件
    Analytics            8 methods  分析
    UserAnalytics        7 methods  用户分析
    ProductAnalytics     2 methods  产品分析
    BrowserPreview       3 methods  浏览器预览
    FileSystemProvider   3 methods  文件系统
    Auth                 1 methods  认证
    ChatClientServer     1 methods  聊天客户端
    Dev                  3 methods  开发调试

远程服务器:
    API:      https://server.self-serve.windsurf.com
    Register: https://register.windsurf.com
    EU:       https://eu.windsurf.com/_route/api_server

本地 LS:
    http://127.0.0.1:{port}  (端口随机, 需探测)
"""
from .seat_management import SeatManagementService
from .api_server import ApiServerService
from .language_server import LanguageServerService
from .extension_server import ExtensionServerService
from .plugins import CascadePluginsService
from .analytics import AnalyticsService, UserAnalyticsService, ProductAnalyticsService
from .misc import (
    BrowserPreviewService,
    FileSystemProviderService,
    DevService,
    AuthService,
    ChatClientServerService,
)

__all__ = [
    "SeatManagementService",
    "ApiServerService",
    "LanguageServerService",
    "ExtensionServerService",
    "CascadePluginsService",
    "AnalyticsService",
    "UserAnalyticsService",
    "ProductAnalyticsService",
    "BrowserPreviewService",
    "FileSystemProviderService",
    "DevService",
    "AuthService",
    "ChatClientServerService",
]

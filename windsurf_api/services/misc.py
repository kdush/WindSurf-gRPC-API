"""杂项小服务集合 — 9 RPC methods

BrowserPreviewService (3)         — 浏览器预览
FileSystemProviderService (3)     — 文件系统
DevService (1)                    — 开发调试
AuthService (1)                   — 认证
ChatClientServerService (1)       — 聊天客户端
"""
from ..transport import ConnectTransport, RpcResponse
from ..models import metadata


class BrowserPreviewService:
    """浏览器预览服务 — 向 IDE 内置浏览器发送截图、DOM 和控制台日志"""
    SERVICE = "exa.browser_preview_pb.BrowserPreviewService"

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(self.SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def send_console_output(self, *, url: str = "", logs: list = None, **kw) -> RpcResponse:
        """发送浏览器控制台输出

        Args:
            url: 预览页面 URL
            logs: 控制台日志条目列表
        """
        return self._call("SendConsoleOutput", {**self._meta(), "url": url, "logs": logs or [], **kw})

    def send_dom_element(self, *, url: str = "", selector: str = "", html: str = "", **kw) -> RpcResponse:
        """发送 DOM 元素内容

        Args:
            url: 预览页面 URL
            selector: CSS 选择器
            html: 元素 HTML 内容
        """
        return self._call("SendDOMElement", {**self._meta(), "url": url, "selector": selector, "html": html, **kw})

    def send_screenshot(self, *, url: str = "", data: str = "", **kw) -> RpcResponse:
        """发送页面截图

        Args:
            url: 预览页面 URL
            data: 截图数据 (base64 编码)
        """
        return self._call("SendScreenshot", {**self._meta(), "url": url, "data": data, **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)


class FileSystemProviderService:
    """文件系统提供者服务 — 远程读取文件和目录"""
    SERVICE = "exa.file_system_provider_pb.FileSystemProviderService"

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(self.SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def read_directory(self, *, uri: str = "", **kw) -> RpcResponse:
        """读取目录内容列表

        Args:
            uri: 目录 URI (如 file:///path/to/dir)
        """
        return self._call("ReadDirectory", {**self._meta(), "uri": uri, **kw})

    def read_file(self, *, uri: str = "", **kw) -> RpcResponse:
        """读取文件内容

        Args:
            uri: 文件 URI (如 file:///path/to/file)
        """
        return self._call("ReadFile", {**self._meta(), "uri": uri, **kw})

    def stat(self, *, uri: str = "", **kw) -> RpcResponse:
        """获取文件/目录元信息 (大小、修改时间等)

        Args:
            uri: 文件或目录 URI
        """
        return self._call("Stat", {**self._meta(), "uri": uri, **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)


class DevService:
    """开发调试服务 — 内部调试入口"""
    SERVICE = "exa.dev_pb.DevService"

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(self.SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def dev(self, *, command: str = "", args: dict = None, **kw) -> RpcResponse:
        """开发调试入口

        Args:
            command: 调试命令名
            args: 命令参数
        """
        return self._call("Dev", {**self._meta(), "command": command, "args": args or {}, **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)


class AuthService:
    """认证服务 — JWT Token 管理"""
    SERVICE = "exa.auth_pb.AuthService"

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(self.SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def get_user_jwt(self, **kw) -> RpcResponse:
        """获取当前用户的 JWT Token (用于跨服务认证)"""
        return self._call("GetUserJwt", {**self._meta(), **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)


class ChatClientServerService:
    """聊天客户端服务 — Cascade 聊天流"""
    SERVICE = "exa.chat_client_server_pb.ChatClientServerService"

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(self.SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def start_chat_client_request_stream(self, *, conversationId: str = "", message: str = "", **kw) -> RpcResponse:
        """启动聊天请求流 (服务端流式响应)

        Args:
            conversationId: 对话 ID
            message: 用户消息内容
        """
        return self._call("StartChatClientRequestStream", {
            **self._meta(), "conversationId": conversationId, "message": message, **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)

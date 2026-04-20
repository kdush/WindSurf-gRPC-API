"""杂项小服务集合 — 11 RPC methods

BrowserPreviewService (3)         — 浏览器预览
FileSystemProviderService (3)     — 文件系统
DevService (3)                    — 开发调试
AuthService (1)                   — 认证
ChatClientServerService (1)       — 聊天客户端
"""
from ..transport import ConnectTransport, RpcResponse
from ..models import metadata


class BrowserPreviewService:
    """BrowserPreviewService (3 methods)"""
    SERVICE = "exa.browser_preview_pb.BrowserPreviewService"

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(self.SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def send(self, **kw) -> RpcResponse:
        return self._call("Send", {**self._meta(), **kw})

    def send_console_output(self, **kw) -> RpcResponse:
        return self._call("SendConsoleOutput", {**self._meta(), **kw})

    def send_screenshot(self, **kw) -> RpcResponse:
        return self._call("SendScreenshot", {**self._meta(), **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)


class FileSystemProviderService:
    """FileSystemProviderService (3 methods)"""
    SERVICE = "exa.file_system_provider_pb.FileSystemProviderService"

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(self.SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def read_directory(self, **kw) -> RpcResponse:
        return self._call("ReadDirectory", {**self._meta(), **kw})

    def read_file(self, **kw) -> RpcResponse:
        return self._call("ReadFile", {**self._meta(), **kw})

    def stat(self, **kw) -> RpcResponse:
        return self._call("Stat", {**self._meta(), **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)


class DevService:
    """DevService (3 methods) — 开发调试"""
    SERVICE = "exa.dev_pb.DevService"

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(self.SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def cascade(self, **kw) -> RpcResponse:
        return self._call("CASCADE", {**self._meta(), **kw})

    def dev(self, **kw) -> RpcResponse:
        return self._call("Dev", {**self._meta(), **kw})

    def get(self, **kw) -> RpcResponse:
        return self._call("Get", {**self._meta(), **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)


class AuthService:
    """AuthService (1 method)"""
    SERVICE = "exa.auth_pb.AuthService"

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(self.SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def get_user_jwt(self, **kw) -> RpcResponse:
        return self._call("GetUserJwt", {**self._meta(), **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)


class ChatClientServerService:
    """ChatClientServerService (1 method)"""
    SERVICE = "exa.chat_client_server_pb.ChatClientServerService"

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(self.SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def start_chat_client_request_stream(self, **kw) -> RpcResponse:
        return self._call("StartChatClientRequestStream", {**self._meta(), **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)

"""CascadePluginsService — 5 RPC methods

MCP 插件管理，含泄露的 GitHub Copilot OAuth 凭据。
逆向自 exa.cascade_plugins_pb.CascadePluginsService
"""
from ..transport import ConnectTransport, RpcResponse
from ..models import metadata


SERVICE = "exa.cascade_plugins_pb.CascadePluginsService"


class CascadePluginsService:
    """CascadePlugins 服务封装"""

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def get_mcp_client_infos(self) -> RpcResponse:
        """获取 MCP 客户端信息 (含 GitHub Copilot OAuth secret)"""
        r = self._call("GetMcpClientInfos", {})
        if not r.ok or not r.get("clientInfos"):
            r = self._call("GetMcpClientInfos", self._meta())
        return r

    def get_available_cascade_plugins(self) -> RpcResponse:
        """获取可用插件列表"""
        return self._call("GetAvailableCascadePlugins", self._meta())

    def get_cascade_plugin_config(self, **kw) -> RpcResponse:
        return self._call("GetCascadePluginConfig", {**self._meta(), **kw})

    def update_cascade_plugin_config(self, **kw) -> RpcResponse:
        return self._call("UpdateCascadePluginConfig", {**self._meta(), **kw})

    def get_all_acp_registries(self) -> RpcResponse:
        return self._call("GetAllAcpRegistries", self._meta())

    def get_cascade_plugin_by_id(self, **kw) -> RpcResponse:
        return self._call("GetCascadePluginById", {**self._meta(), **kw})

    def install_cascade_plugin(self, **kw) -> RpcResponse:
        return self._call("InstallCascadePlugin", {**self._meta(), **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)

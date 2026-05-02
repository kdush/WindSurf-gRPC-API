"""CascadePluginsService — 5 RPC methods

MCP 插件管理: 获取 OAuth 凭据、插件列表、安装插件。
逆向自 exa.cascade_plugins_pb.CascadePluginsService
"""
from ..transport import ConnectTransport, RpcResponse
from ..models import metadata


SERVICE = "exa.cascade_plugins_pb.CascadePluginsService"


class CascadePluginsService:
    """MCP/ACP 插件管理服务 — 管理 Cascade 的外部工具插件"""

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def get_mcp_client_infos(self) -> RpcResponse:
        """获取 MCP 客户端信息 (含 OAuth client_id/secret)

        先尝试无 key 调用，失败后带 api_key 重试。
        返回 data.clientInfos 列表。
        """
        r = self._call("GetMcpClientInfos", {})
        if not r.ok or not r.get("clientInfos"):
            r = self._call("GetMcpClientInfos", self._meta())
        return r

    def get_all_acp_registries(self, **kw) -> RpcResponse:
        """获取所有 ACP (Agent Communication Protocol) 注册表"""
        return self._call("GetAllAcpRegistries", {**self._meta(), **kw})

    def get_available_cascade_plugins(self, **kw) -> RpcResponse:
        """获取所有可用 Cascade 插件列表

        返回 data.plugins — 每个插件含 name, description, pluginId 等。
        """
        return self._call("GetAvailableCascadePlugins", {**self._meta(), **kw})

    def get_cascade_plugin_by_id(self, *, pluginId: str = "", **kw) -> RpcResponse:
        """按 ID 获取单个插件详情

        Args:
            pluginId: 插件唯一标识符
        """
        return self._call("GetCascadePluginById", {**self._meta(), "pluginId": pluginId, **kw})

    def install_cascade_plugin(self, *, pluginId: str = "", **kw) -> RpcResponse:
        """安装 Cascade 插件

        Args:
            pluginId: 要安装的插件 ID
        """
        return self._call("InstallCascadePlugin", {**self._meta(), "pluginId": pluginId, **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)

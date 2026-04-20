"""Analytics 服务集合 — 17 RPC methods

包含 3 个分析服务:
  AnalyticsService (8)        — 补全/遥测
  UserAnalyticsService (7)    — 用户分析
  ProductAnalyticsService (2) — 产品分析

逆向自 exa.analytics_pb / exa.user_analytics_pb / exa.product_analytics_pb
"""
from ..transport import ConnectTransport, RpcResponse
from ..models import metadata


ANALYTICS_SVC = "exa.analytics_pb.AnalyticsService"
USER_ANALYTICS_SVC = "exa.user_analytics_pb.UserAnalyticsService"
PRODUCT_ANALYTICS_SVC = "exa.product_analytics_pb.ProductAnalyticsService"


class AnalyticsService:
    """AnalyticsService (8 methods) — 补全/遥测"""

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(ANALYTICS_SVC, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def batch_record_completions_hermes(self, **kw) -> RpcResponse:
        return self._call("BatchRecordCompletionsHermes", {**self._meta(), **kw})

    def batch_record_prompts(self, **kw) -> RpcResponse:
        return self._call("BatchRecordPrompts", {**self._meta(), **kw})

    def record_command_usage(self, **kw) -> RpcResponse:
        return self._call("RecordCommandUsage", {**self._meta(), **kw})

    def record_completions_internal(self, **kw) -> RpcResponse:
        return self._call("RecordCompletionsinternal", {**self._meta(), **kw})

    def record_context_to_prompt(self, **kw) -> RpcResponse:
        return self._call("RecordContextToPrompt", {**self._meta(), **kw})

    def record_cortex_trajectory(self, **kw) -> RpcResponse:
        return self._call("RecordCortexTrajectory", {**self._meta(), **kw})

    def record_cortex_trajectory_step_internal(self, **kw) -> RpcResponse:
        return self._call("RecordCortexTrajectoryStepinternal", {**self._meta(), **kw})

    def record_tab_trajectory_step(self, **kw) -> RpcResponse:
        return self._call("RecordTabTrajectoryStep", {**self._meta(), **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)


class UserAnalyticsService:
    """UserAnalyticsService (7 methods) — 用户分析"""

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(USER_ANALYTICS_SVC, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def analytics(self, **kw) -> RpcResponse:
        return self._call("Analytics", {**self._meta(), **kw})

    def cascade_analytics(self, **kw) -> RpcResponse:
        return self._call("CascadeAnalytics", {**self._meta(), **kw})

    def get_analytics(self, **kw) -> RpcResponse:
        return self._call("GetAnalytics", {**self._meta(), **kw})

    def get_big_query_analytics(self, **kw) -> RpcResponse:
        return self._call("GetBigQueryAnalytics", {**self._meta(), **kw})

    def get_devin_user_analytics(self, **kw) -> RpcResponse:
        return self._call("GetDevinUserAnalytics", {**self._meta(), **kw})

    def get_global_leaderboard(self, **kw) -> RpcResponse:
        return self._call("GetGlobalLeaderboard", {**self._meta(), **kw})

    def user_page_analytics(self, **kw) -> RpcResponse:
        return self._call("UserPageAnalytics", {**self._meta(), **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)


class ProductAnalyticsService:
    """ProductAnalyticsService (2 methods) — 产品分析"""

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(PRODUCT_ANALYTICS_SVC, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def batch_record_analytics_events(self, **kw) -> RpcResponse:
        return self._call("BatchRecordAnalyticsEvents", {**self._meta(), **kw})

    def record_analytics_event(self, **kw) -> RpcResponse:
        return self._call("RecordAnalyticsEvent", {**self._meta(), **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)

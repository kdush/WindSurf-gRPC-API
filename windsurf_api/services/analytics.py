"""Analytics 服务集合 — 17 RPC methods

包含 3 个分析服务:
  AnalyticsService (8)        — 补全记录 / 遥测上报
  UserAnalyticsService (7)    — 用户行为分析 / 排行榜
  ProductAnalyticsService (2) — 产品事件追踪

逆向自 exa.analytics_pb / exa.user_analytics_pb / exa.product_analytics_pb
"""
from ..transport import ConnectTransport, RpcResponse
from ..models import metadata


ANALYTICS_SVC = "exa.analytics_pb.AnalyticsService"
USER_ANALYTICS_SVC = "exa.user_analytics_pb.UserAnalyticsService"
PRODUCT_ANALYTICS_SVC = "exa.product_analytics_pb.ProductAnalyticsService"


class AnalyticsService:
    """补全记录 / 遥测上报服务"""

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(ANALYTICS_SVC, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def batch_record_completions(self, *, completions: list = None, **kw) -> RpcResponse:
        """批量上报代码补全记录

        Args:
            completions: 补全事件列表, 每项含 completionId / accepted / language 等
        """
        return self._call("BatchRecordCompletions", {**self._meta(), "completions": completions or [], **kw})

    def batch_record_prompts(self, *, prompts: list = None, **kw) -> RpcResponse:
        """批量上报 Prompt 记录

        Args:
            prompts: Prompt 事件列表
        """
        return self._call("BatchRecordPrompts", {**self._meta(), "prompts": prompts or [], **kw})

    def record_command_usage(self, *, command: str = "", source: str = "", **kw) -> RpcResponse:
        """上报命令使用记录

        Args:
            command: 命令名称 (如 "cascade.chat")
            source: 触发来源 (如 "palette", "keybinding")
        """
        return self._call("RecordCommandUsage", {**self._meta(), "command": command, "source": source, **kw})

    def record_completions(self, *, completionId: str = "", language: str = "",
                           accepted: bool = False, **kw) -> RpcResponse:
        """上报单次代码补全记录

        Args:
            completionId: 补全事件 ID
            language: 编程语言
            accepted: 用户是否接受了补全
        """
        return self._call("RecordCompletions", {
            **self._meta(), "completionId": completionId,
            "language": language, "accepted": accepted, **kw})

    def record_context_to_prompt(self, *, promptId: str = "", context: dict = None, **kw) -> RpcResponse:
        """上报上下文到 Prompt 的映射

        Args:
            promptId: Prompt ID
            context: 上下文数据 (文件、选区等)
        """
        return self._call("RecordContextToPrompt", {
            **self._meta(), "promptId": promptId, "context": context or {}, **kw})

    def record_cortex_trajectory(self, *, trajectoryId: str = "", steps: list = None, **kw) -> RpcResponse:
        """上报 Cortex (Cascade) 完整对话轨迹

        Args:
            trajectoryId: 轨迹 ID
            steps: 轨迹步骤列表
        """
        return self._call("RecordCortexTrajectory", {
            **self._meta(), "trajectoryId": trajectoryId, "steps": steps or [], **kw})

    def record_cortex_trajectory_step(self, *, trajectoryId: str = "", step: dict = None, **kw) -> RpcResponse:
        """上报 Cortex 单个轨迹步骤

        Args:
            trajectoryId: 轨迹 ID
            step: 步骤数据 (含 action, result 等)
        """
        return self._call("RecordCortexTrajectoryStep", {
            **self._meta(), "trajectoryId": trajectoryId, "step": step or {}, **kw})

    def record_tab_trajectory_step(self, *, trajectoryId: str = "", step: dict = None, **kw) -> RpcResponse:
        """上报 Tab 补全轨迹步骤

        Args:
            trajectoryId: 轨迹 ID
            step: Tab 补全步骤数据
        """
        return self._call("RecordTabTrajectoryStep", {
            **self._meta(), "trajectoryId": trajectoryId, "step": step or {}, **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)


class UserAnalyticsService:
    """用户行为分析 / 排行榜服务"""

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(USER_ANALYTICS_SVC, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def analytics(self, *, timeRange: str = "", **kw) -> RpcResponse:
        """获取通用分析数据

        Args:
            timeRange: 时间范围 (如 "7d", "30d")
        """
        return self._call("Analytics", {**self._meta(), "timeRange": timeRange, **kw})

    def cascade_analytics(self, *, timeRange: str = "", **kw) -> RpcResponse:
        """获取 Cascade AI 使用分析

        Args:
            timeRange: 时间范围
        """
        return self._call("CascadeAnalytics", {**self._meta(), "timeRange": timeRange, **kw})

    def get_analytics(self, *, timeRange: str = "", **kw) -> RpcResponse:
        """获取综合分析报告

        Args:
            timeRange: 时间范围
        """
        return self._call("GetAnalytics", {**self._meta(), "timeRange": timeRange, **kw})

    def get_big_query_analytics(self, *, query: str = "", **kw) -> RpcResponse:
        """获取 BigQuery 分析数据 (内部)

        Args:
            query: 查询条件
        """
        return self._call("GetBigQueryAnalytics", {**self._meta(), "query": query, **kw})

    def get_devin_user_analytics(self, *, timeRange: str = "", **kw) -> RpcResponse:
        """获取 Devin (远程开发) 用户分析

        Args:
            timeRange: 时间范围
        """
        return self._call("GetDevinUserAnalytics", {**self._meta(), "timeRange": timeRange, **kw})

    def get_global_leaderboard_api_key(self, *, timeRange: str = "", limit: int = 0, **kw) -> RpcResponse:
        """使用 API Key 获取全球排行榜

        Args:
            timeRange: 时间范围
            limit: 返回条目数量上限
        """
        return self._call("GetGlobalLeaderboardApiKey", {
            **self._meta(), "timeRange": timeRange, "limit": limit, **kw})

    def user_page_analytics(self, *, page: str = "", timeRange: str = "", **kw) -> RpcResponse:
        """获取用户页面级分析

        Args:
            page: 页面标识
            timeRange: 时间范围
        """
        return self._call("UserPageAnalytics", {**self._meta(), "page": page, "timeRange": timeRange, **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)


class ProductAnalyticsService:
    """产品事件追踪服务"""

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(PRODUCT_ANALYTICS_SVC, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    def batch_record_analytics_events(self, *, events: list = None, **kw) -> RpcResponse:
        """批量上报产品分析事件

        Args:
            events: 事件列表, 每项含 eventName / properties / timestamp 等
        """
        return self._call("BatchRecordAnalyticsEvents", {**self._meta(), "events": events or [], **kw})

    def record_analytics_event(self, *, eventName: str = "", properties: dict = None, **kw) -> RpcResponse:
        """上报单个产品分析事件

        Args:
            eventName: 事件名称 (如 "cascade_chat_started")
            properties: 事件属性键值对
        """
        return self._call("RecordAnalyticsEvent", {
            **self._meta(), "eventName": eventName, "properties": properties or {}, **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)

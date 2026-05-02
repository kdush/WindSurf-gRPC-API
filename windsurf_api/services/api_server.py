"""ApiServerService — 170 RPC methods

模型配置、聊天补全、容量检查、部署、限速、代码分析等。
逆向自 exa.api_server_pb.ApiServerService
"""
from ..transport import ConnectTransport, RpcResponse
from ..models import metadata, ModelProvider


SERVICE = "exa.api_server_pb.ApiServerService"


class ApiServerService:
    """ApiServerService 完整封装"""

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(SERVICE, method, payload or {}, **kw)

    def _meta(self, key: str = None) -> dict:
        return {"metadata": metadata(key or self.api_key)}

    def get_model_providers(self) -> list:
        """获取模型提供商列表"""
        try:
            r = self._call("GetModelProviders", self._meta())
            if r.ok and isinstance(getattr(r, 'data', None), dict):
                return [ModelProvider.from_response(p)
                        for p in r.data.get('modelProviders', [])]
        except Exception:
            pass
        return []

    def get_model_providers_raw(self) -> RpcResponse:
        return self._call("GetModelProviders", self._meta())

    def check_chat_capacity(self, model_uid: str = "") -> RpcResponse:
        payload = self._meta()
        if model_uid:
            payload["modelUid"] = model_uid
        return self._call("CheckChatCapacity", payload)

    def check_user_message_rate_limit(self, model_uid: str = "") -> RpcResponse:
        payload = self._meta()
        if model_uid:
            payload["modelUid"] = model_uid
        return self._call("CheckUserMessageRateLimit", payload)

    # ── Bug / 反馈 ──

    def accept_bug(self, *, bugId: str = "", **kw) -> RpcResponse:
        """接受 Bug 报告

        Args:
            bugId: Bug ID
        """
        return self._call("AcceptBug", {**self._meta(), "bugId": bugId, **kw})

    def check_bugs(self, **kw) -> RpcResponse:
        """检查待处理的 Bug"""
        return self._call("CheckBugs", {**self._meta(), **kw})

    def reject_bug(self, *, bugId: str = "", reason: str = "", **kw) -> RpcResponse:
        """拒绝 Bug 报告

        Args:
            bugId: Bug ID
            reason: 拒绝原因
        """
        return self._call("RejectBug", {**self._meta(), "bugId": bugId, "reason": reason, **kw})

    def submit_bug_report(self, *, title: str = "", description: str = "",
                          steps: str = "", **kw) -> RpcResponse:
        """提交 Bug 报告

        Args:
            title: Bug 标题
            description: 描述
            steps: 复现步骤
        """
        return self._call("SubmitBugReport", {
            **self._meta(), "title": title, "description": description, "steps": steps, **kw})

    def provide_feedback(self, *, feedback: str = "", type: str = "", **kw) -> RpcResponse:
        """提供反馈

        Args:
            feedback: 反馈内容
            type: 反馈类型
        """
        return self._call("ProvideFeedback", {**self._meta(), "feedback": feedback, "type": type, **kw})

    # ── 账号验证 ──

    def account_ownership_notification_dismiss(self, **kw) -> RpcResponse:
        """关闭账户所有权验证通知"""
        return self._call("AccountOwnershipNotificationDismiss", {**self._meta(), **kw})

    def account_ownership_notification_verification(self, **kw) -> RpcResponse:
        """触发账户所有权验证通知"""
        return self._call("AccountOwnershipNotificationVerification", {**self._meta(), **kw})

    def ping_account_ownership_notification_verification(self, **kw) -> RpcResponse:
        """Ping 账户所有权验证状态"""
        return self._call("PingAccountOwnershipNotificationVerification", {**self._meta(), **kw})

    def enroll_cyber_verification(self, **kw) -> RpcResponse:
        """注册 Anthropic Cyber 验证"""
        return self._call("EnrollCyberVerification", {**self._meta(), **kw})

    def get_cyber_verification_enrollment_url(self, **kw) -> RpcResponse:
        """获取 Cyber 验证注册 URL"""
        return self._call("GetCyberVerificationEnrollmentUrl", {**self._meta(), **kw})

    def update_anthropic_cyber_verification_enabled(self, *, enabled: bool = False, **kw) -> RpcResponse:
        """更新 Anthropic Cyber 验证启用状态

        Args:
            enabled: 是否启用
        """
        return self._call("UpdateAnthropicCyberVerificationEnabled", {**self._meta(), "enabled": enabled, **kw})

    # ── AI / 模型 / 补全 ──

    def apply_trajectory_heuristics(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """对对话轨迹应用启发式规则

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("ApplyTrajectoryHeuristics", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def assign_arena_model(self, **kw) -> RpcResponse:
        """分配 Arena 模式对比模型"""
        return self._call("AssignArenaModel", {**self._meta(), **kw})

    def assign_model(self, *, modelUid: str = "", **kw) -> RpcResponse:
        """分配模型

        Args:
            modelUid: 模型 UID
        """
        return self._call("AssignModel", {**self._meta(), "modelUid": modelUid, **kw})

    def cancel_completions(self, *, requestId: str = "", **kw) -> RpcResponse:
        """取消进行中的补全请求

        Args:
            requestId: 请求 ID
        """
        return self._call("CancelCompletions", {**self._meta(), "requestId": requestId, **kw})

    def generate_syn(self, **kw) -> RpcResponse:
        """生成合成数据"""
        return self._call("GenerateSyn", {**self._meta(), **kw})

    def get_cascade_model_configs(self, **kw) -> RpcResponse:
        """获取 Cascade 模型配置列表"""
        return self._call("GetCascadeModelConfigs", {**self._meta(), **kw})

    def get_cascade_model_configs_for_site(self, **kw) -> RpcResponse:
        """获取站点级 Cascade 模型配置"""
        return self._call("GetCascadeModelConfigsForSite", {**self._meta(), **kw})

    def get_chat_completions(self, *, messages: list = None, modelUid: str = "",
                             temperature: float = 0.0, **kw) -> RpcResponse:
        """获取聊天补全 (非流式)

        Args:
            messages: 消息列表 [{role, content}, ...]
            modelUid: 模型 UID
            temperature: 温度参数
        """
        return self._call("GetChatCompletions", {
            **self._meta(), "messages": messages or [], "modelUid": modelUid,
            "temperature": temperature, **kw})

    def get_chat_message(self, *, messageId: str = "", **kw) -> RpcResponse:
        """获取聊天消息

        Args:
            messageId: 消息 ID
        """
        return self._call("GetChatMessage", {**self._meta(), "messageId": messageId, **kw})

    def get_cli_model_configs(self, **kw) -> RpcResponse:
        """获取 CLI 模型配置"""
        return self._call("GetCliModelConfigs", {**self._meta(), **kw})

    def get_cli_model_configs_for_site(self, **kw) -> RpcResponse:
        """获取站点级 CLI 模型配置"""
        return self._call("GetCliModelConfigsForSite", {**self._meta(), **kw})

    def get_command_model_configs(self, **kw) -> RpcResponse:
        """获取命令模型配置"""
        return self._call("GetCommandModelConfigs", {**self._meta(), **kw})

    def get_command_model_configs_for_site(self, **kw) -> RpcResponse:
        """获取站点级命令模型配置"""
        return self._call("GetCommandModelConfigsForSite", {**self._meta(), **kw})

    def get_completions(self, *, document: dict = None, **kw) -> RpcResponse:
        """获取代码补全

        Args:
            document: 文档信息 {uri, languageId, content, cursorOffset, ...}
        """
        return self._call("GetCompletions", {**self._meta(), "document": document or {}, **kw})

    def get_completion_examples(self, **kw) -> RpcResponse:
        """获取补全示例"""
        return self._call("GetCompletionExamples", {**self._meta(), **kw})

    def get_config(self, **kw) -> RpcResponse:
        """获取服务端配置"""
        return self._call("GetConfig", {**self._meta(), **kw})

    def get_devstral_stream(self, **kw) -> RpcResponse:
        """获取 Devstral 模型流式响应"""
        return self._call("GetDevstralStream", {**self._meta(), **kw})

    def get_embeddings(self, *, texts: list = None, **kw) -> RpcResponse:
        """获取文本向量嵌入

        Args:
            texts: 文本列表
        """
        return self._call("GetEmbeddings", {**self._meta(), "texts": texts or [], **kw})

    def get_lifeguard_config(self, **kw) -> RpcResponse:
        """获取 Lifeguard 安全配置"""
        return self._call("GetLifeguardConfig", {**self._meta(), **kw})

    def get_model_statuses(self, **kw) -> RpcResponse:
        """获取所有模型的状态 (可用性)"""
        return self._call("GetModelStatuses", {**self._meta(), **kw})

    def get_streaming_completions(self, *, document: dict = None, **kw) -> RpcResponse:
        """获取流式代码补全

        Args:
            document: 文档信息
        """
        return self._call("GetStreamingCompletions", {**self._meta(), "document": document or {}, **kw})

    def get_streaming_external_chat_completions(self, *, messages: list = None,
                                                modelUid: str = "", **kw) -> RpcResponse:
        """获取外部模型流式聊天补全

        Args:
            messages: 消息列表
            modelUid: 模型 UID
        """
        return self._call("GetStreamingExternalChatCompletions", {
            **self._meta(), "messages": messages or [], "modelUid": modelUid, **kw})

    def get_streaming_model_api_text_completion(self, *, prompt: str = "",
                                                modelUid: str = "", **kw) -> RpcResponse:
        """获取模型 API 流式文本补全

        Args:
            prompt: 提示文本
            modelUid: 模型 UID
        """
        return self._call("GetStreamingModelAPITextCompletion", {
            **self._meta(), "prompt": prompt, "modelUid": modelUid, **kw})

    def get_tab(self, **kw) -> RpcResponse:
        """获取 Tab 补全"""
        return self._call("GetTab", {**self._meta(), **kw})

    def get_transcription(self, *, audioData: str = "", **kw) -> RpcResponse:
        """获取音频转录

        Args:
            audioData: 音频数据 (base64)
        """
        return self._call("GetTranscription", {**self._meta(), "audioData": audioData, **kw})

    def run_code_alignment(self, **kw) -> RpcResponse:
        """运行代码对齐"""
        return self._call("RunCodeAlignment", {**self._meta(), **kw})

    # ── 外部模型管理 ──

    def create_external_models(self, *, models: list = None, **kw) -> RpcResponse:
        """创建外部模型配置

        Args:
            models: 模型配置列表
        """
        return self._call("CreateExternalModels", {**self._meta(), "models": models or [], **kw})

    def delete_external_models(self, *, modelIds: list = None, **kw) -> RpcResponse:
        """删除外部模型

        Args:
            modelIds: 模型 ID 列表
        """
        return self._call("DeleteExternalModels", {**self._meta(), "modelIds": modelIds or [], **kw})

    def get_external_model(self, *, modelId: str = "", **kw) -> RpcResponse:
        """获取单个外部模型

        Args:
            modelId: 模型 ID
        """
        return self._call("GetExternalModel", {**self._meta(), "modelId": modelId, **kw})

    def get_external_models_group(self, **kw) -> RpcResponse:
        """获取外部模型组"""
        return self._call("GetExternalModelsGroup", {**self._meta(), **kw})

    def update_external_models(self, *, models: list = None, **kw) -> RpcResponse:
        """更新外部模型配置

        Args:
            models: 模型配置列表
        """
        return self._call("UpdateExternalModels", {**self._meta(), "models": models or [], **kw})

    def update_external_models_group(self, *, group: dict = None, **kw) -> RpcResponse:
        """更新外部模型组

        Args:
            group: 组配置
        """
        return self._call("UpdateExternalModelsGroup", {**self._meta(), "group": group or {}, **kw})

    # ── 混合部署 ──

    def check_hybrid_deployment_status(self, **kw) -> RpcResponse:
        """检查混合部署状态"""
        return self._call("CheckHybridDeploymentStatus", {**self._meta(), **kw})

    def create_hybrid_deployment_internal(self, *, secret: str = "", **kw) -> RpcResponse:
        """[Internal] 创建混合部署

        Args:
            secret: Internal 密钥
        """
        return self._call("CreateHybridDeploymentInternal", {**self._meta(), "secret": secret, **kw})

    def get_hybrid_deployments_internal(self, *, secret: str = "", **kw) -> RpcResponse:
        """[Internal] 获取混合部署列表

        Args:
            secret: Internal 密钥
        """
        return self._call("GetHybridDeploymentsInternal", {**self._meta(), "secret": secret, **kw})

    def register_hybrid_deployment(self, **kw) -> RpcResponse:
        """注册混合部署"""
        return self._call("RegisterHybridDeployment", {**self._meta(), **kw})

    def remove_hybrid_deployment_internal(self, *, secret: str = "", deploymentId: str = "", **kw) -> RpcResponse:
        """[Internal] 移除混合部署

        Args:
            secret: Internal 密钥
            deploymentId: 部署 ID
        """
        return self._call("RemoveHybridDeploymentInternal", {
            **self._meta(), "secret": secret, "deploymentId": deploymentId, **kw})

    # ── Windsurf JS App 部署 ──

    def create_windsurf_js_app(self, *, name: str = "", framework: str = "", **kw) -> RpcResponse:
        """创建 Windsurf JS 应用

        Args:
            name: 应用名称
            framework: 前端框架 (如 "react", "vue")
        """
        return self._call("CreateWindsurfJSApp", {**self._meta(), "name": name, "framework": framework, **kw})

    def delete_windsurf_js_app(self, *, projectId: str = "", **kw) -> RpcResponse:
        """删除 Windsurf JS 应用

        Args:
            projectId: 项目 ID
        """
        return self._call("DeleteWindsurfJSApp", {**self._meta(), "projectId": projectId, **kw})

    def deploy_windsurf_js_app(self, *, projectId: str = "", **kw) -> RpcResponse:
        """部署 Windsurf JS 应用

        Args:
            projectId: 项目 ID
        """
        return self._call("DeployWindsurfJSApp", {**self._meta(), "projectId": projectId, **kw})

    def get_windsurf_js_app_deployment(self, *, deploymentId: str = "", **kw) -> RpcResponse:
        """获取 JS 应用部署详情

        Args:
            deploymentId: 部署 ID
        """
        return self._call("GetWindsurfJSAppDeployment", {**self._meta(), "deploymentId": deploymentId, **kw})

    def get_windsurf_js_app_deployment_claim_status(self, *, deploymentId: str = "", **kw) -> RpcResponse:
        """获取 JS 应用部署认领状态

        Args:
            deploymentId: 部署 ID
        """
        return self._call("GetWindsurfJSAppDeploymentClaimStatus", {
            **self._meta(), "deploymentId": deploymentId, **kw})

    def get_windsurf_js_app_deployment_statuses_by_project_id(self, *, projectId: str = "", **kw) -> RpcResponse:
        """按项目获取 JS 应用部署状态列表

        Args:
            projectId: 项目 ID
        """
        return self._call("GetWindsurfJSAppDeploymentStatusesByProjectId", {
            **self._meta(), "projectId": projectId, **kw})

    def get_windsurf_js_app_deployments_by_project_id(self, *, projectId: str = "", **kw) -> RpcResponse:
        """按项目获取 JS 应用部署列表

        Args:
            projectId: 项目 ID
        """
        return self._call("GetWindsurfJSAppDeploymentsByProjectId", {
            **self._meta(), "projectId": projectId, **kw})

    def get_windsurf_js_apps(self, **kw) -> RpcResponse:
        """获取所有 Windsurf JS 应用"""
        return self._call("GetWindsurfJSApps", {**self._meta(), **kw})

    def get_windsurf_js_available_deploy_targets(self, **kw) -> RpcResponse:
        """获取可用部署目标"""
        return self._call("GetWindsurfJSAvailableDeployTargets", {**self._meta(), **kw})

    def get_windsurf_js_deploy_target_by_project_id(self, *, projectId: str = "", **kw) -> RpcResponse:
        """按项目获取部署目标

        Args:
            projectId: 项目 ID
        """
        return self._call("GetWindsurfJSDeployTargetByProjectId", {
            **self._meta(), "projectId": projectId, **kw})

    def validate_windsurf_js_app_project_name(self, *, name: str = "", **kw) -> RpcResponse:
        """验证 JS 应用项目名称是否可用

        Args:
            name: 项目名称
        """
        return self._call("ValidateWindsurfJSAppProjectName", {**self._meta(), "name": name, **kw})

    # ── 部署配置 ──

    def get_deployment_config(self, *, projectId: str = "", **kw) -> RpcResponse:
        """获取部署配置

        Args:
            projectId: 项目 ID
        """
        return self._call("GetDeploymentConfig", {**self._meta(), "projectId": projectId, **kw})

    def get_deployment_provider_project_name_by_project_id(self, *, projectId: str = "", **kw) -> RpcResponse:
        """按项目 ID 获取部署提供商项目名

        Args:
            projectId: 项目 ID
        """
        return self._call("GetDeploymentProviderProjectNameByProjectId", {
            **self._meta(), "projectId": projectId, **kw})

    def upsert_deployment_config(self, *, projectId: str = "", config: dict = None, **kw) -> RpcResponse:
        """创建/更新部署配置

        Args:
            projectId: 项目 ID
            config: 部署配置
        """
        return self._call("UpsertDeploymentConfig", {
            **self._meta(), "projectId": projectId, "config": config or {}, **kw})

    # ── 对话分享 ──

    def create_trajectory_share_stream(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """创建对话轨迹分享 (流式)

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("CreateTrajectoryShareStream", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def delete_trajectory_share(self, *, shareId: str = "", **kw) -> RpcResponse:
        """删除对话分享

        Args:
            shareId: 分享 ID
        """
        return self._call("DeleteTrajectoryShare", {**self._meta(), "shareId": shareId, **kw})

    def fetch_trajectory_share(self, *, shareId: str = "", **kw) -> RpcResponse:
        """获取对话分享内容

        Args:
            shareId: 分享 ID
        """
        return self._call("FetchTrajectoryShare", {**self._meta(), "shareId": shareId, **kw})

    def fetch_trajectory_share_by_user(self, **kw) -> RpcResponse:
        """获取当前用户的所有对话分享"""
        return self._call("FetchTrajectoryShareByUser", {**self._meta(), **kw})

    def is_conversation_sharing_blocked(self, **kw) -> RpcResponse:
        """检查对话分享是否被阻止"""
        return self._call("IsConversationSharingBlocked", {**self._meta(), **kw})

    # ── Code Map ──

    def get_code_map_encountered(self, **kw) -> RpcResponse:
        """获取已遇到的 Code Map"""
        return self._call("GetCodeMapEncountered", {**self._meta(), **kw})

    def get_code_map_metadata(self, *, codeMapId: str = "", **kw) -> RpcResponse:
        """获取 Code Map 元数据

        Args:
            codeMapId: Code Map ID
        """
        return self._call("GetCodeMapMetadata", {**self._meta(), "codeMapId": codeMapId, **kw})

    def get_shared_code_map(self, *, shareId: str = "", **kw) -> RpcResponse:
        """获取共享的 Code Map

        Args:
            shareId: 分享 ID
        """
        return self._call("GetSharedCodeMap", {**self._meta(), "shareId": shareId, **kw})

    def delete_shared_code_map(self, *, shareId: str = "", **kw) -> RpcResponse:
        """删除共享的 Code Map

        Args:
            shareId: 分享 ID
        """
        return self._call("DeleteSharedCodeMap", {**self._meta(), "shareId": shareId, **kw})

    def list_user_shared_code_maps(self, **kw) -> RpcResponse:
        """列出用户所有共享的 Code Map"""
        return self._call("ListUserSharedCodeMaps", {**self._meta(), **kw})

    def share_code_map(self, *, codeMapId: str = "", **kw) -> RpcResponse:
        """分享 Code Map

        Args:
            codeMapId: Code Map ID
        """
        return self._call("ShareCodeMap", {**self._meta(), "codeMapId": codeMapId, **kw})

    def update_code_map_sharing_mode(self, *, codeMapId: str = "", mode: str = "", **kw) -> RpcResponse:
        """更新 Code Map 分享模式

        Args:
            codeMapId: Code Map ID
            mode: 分享模式
        """
        return self._call("UpdateCodeMapSharingMode", {
            **self._meta(), "codeMapId": codeMapId, "mode": mode, **kw})

    def supports_remote_indexing(self, **kw) -> RpcResponse:
        """检查是否支持远程索引"""
        return self._call("SupportsRemoteIndexing", {**self._meta(), **kw})

    # ── OIDC / SSO ──

    def delete_oidc_provider(self, *, providerId: str = "", **kw) -> RpcResponse:
        """删除 OIDC 提供商

        Args:
            providerId: 提供商 ID
        """
        return self._call("DeleteOidcProvider", {**self._meta(), "providerId": providerId, **kw})

    def exchange_oidc_code(self, *, code: str = "", redirectUri: str = "", **kw) -> RpcResponse:
        """兑换 OIDC 授权码

        Args:
            code: 授权码
            redirectUri: 重定向 URI
        """
        return self._call("ExchangeOidcCode", {**self._meta(), "code": code, "redirectUri": redirectUri, **kw})

    def get_all_oidc_providers(self, **kw) -> RpcResponse:
        """获取所有 OIDC 提供商"""
        return self._call("GetAllOidcProviders", {**self._meta(), **kw})

    def get_oidc_authorization_url(self, *, providerId: str = "", **kw) -> RpcResponse:
        """获取 OIDC 授权 URL

        Args:
            providerId: 提供商 ID
        """
        return self._call("GetOidcAuthorizationUrl", {**self._meta(), "providerId": providerId, **kw})

    def get_sso_providers(self, **kw) -> RpcResponse:
        """获取 SSO 提供商列表"""
        return self._call("GetSSOProviders", {**self._meta(), **kw})

    def get_team_oidc_providers(self, **kw) -> RpcResponse:
        """获取团队 OIDC 提供商"""
        return self._call("GetTeamOidcProviders", {**self._meta(), **kw})

    def refresh_oidc_token(self, *, refreshToken: str = "", **kw) -> RpcResponse:
        """刷新 OIDC Token

        Args:
            refreshToken: Refresh Token
        """
        return self._call("RefreshOidcToken", {**self._meta(), "refreshToken": refreshToken, **kw})

    def register_oidc_provider(self, *, config: dict = None, **kw) -> RpcResponse:
        """注册 OIDC 提供商

        Args:
            config: 提供商配置
        """
        return self._call("RegisterOidcProvider", {**self._meta(), "config": config or {}, **kw})

    def update_oidc_provider(self, *, providerId: str = "", config: dict = None, **kw) -> RpcResponse:
        """更新 OIDC 提供商配置

        Args:
            providerId: 提供商 ID
            config: 新配置
        """
        return self._call("UpdateOidcProvider", {**self._meta(), "providerId": providerId, "config": config or {}, **kw})

    # ── 允许列表 / 组织管控 ──

    def delete_allowlist(self, *, listId: str = "", **kw) -> RpcResponse:
        """删除允许列表

        Args:
            listId: 列表 ID
        """
        return self._call("DeleteAllowlist", {**self._meta(), "listId": listId, **kw})

    def get_allowlist(self, **kw) -> RpcResponse:
        """获取允许列表"""
        return self._call("GetAllowlist", {**self._meta(), **kw})

    def get_user_allowlist(self, **kw) -> RpcResponse:
        """获取用户允许列表"""
        return self._call("GetUserAllowlist", {**self._meta(), **kw})

    def insert_allowlist(self, *, entries: list = None, **kw) -> RpcResponse:
        """插入允许列表条目

        Args:
            entries: 条目列表
        """
        return self._call("InsertAllowlist", {**self._meta(), "entries": entries or [], **kw})

    def delete_team_organizational_controls(self, **kw) -> RpcResponse:
        """删除团队组织管控配置"""
        return self._call("DeleteTeamOrganizationalControls", {**self._meta(), **kw})

    def get_team_organizational_controls(self, **kw) -> RpcResponse:
        """获取团队组织管控配置"""
        return self._call("GetTeamOrganizationalControls", {**self._meta(), **kw})

    def get_team_organizational_controls_for_site(self, **kw) -> RpcResponse:
        """获取站点级团队组织管控"""
        return self._call("GetTeamOrganizationalControlsForSite", {**self._meta(), **kw})

    def upsert_team_organizational_controls(self, *, controls: dict = None, **kw) -> RpcResponse:
        """创建/更新团队组织管控

        Args:
            controls: 管控配置
        """
        return self._call("UpsertTeamOrganizationalControls", {**self._meta(), "controls": controls or {}, **kw})

    def upsert_team_organizational_controls_for_site(self, *, controls: dict = None, **kw) -> RpcResponse:
        """创建/更新站点级团队组织管控

        Args:
            controls: 管控配置
        """
        return self._call("UpsertTeamOrganizationalControlsForSite", {
            **self._meta(), "controls": controls or {}, **kw})

    # ── 杂项查询 ──

    def capture_code(self, *, code: str = "", language: str = "", **kw) -> RpcResponse:
        """捕获代码片段

        Args:
            code: 代码内容
            language: 语言
        """
        return self._call("CaptureCode", {**self._meta(), "code": code, "language": language, **kw})

    def capture_file(self, *, uri: str = "", content: str = "", **kw) -> RpcResponse:
        """捕获文件内容

        Args:
            uri: 文件 URI
            content: 文件内容
        """
        return self._call("CaptureFile", {**self._meta(), "uri": uri, "content": content, **kw})

    def delete_external_user(self, *, userId: str = "", **kw) -> RpcResponse:
        """删除外部用户

        Args:
            userId: 用户 ID
        """
        return self._call("DeleteExternalUser", {**self._meta(), "userId": userId, **kw})

    def find_team_by_email(self, *, email: str = "", **kw) -> RpcResponse:
        """按邮箱查找团队

        Args:
            email: 用户邮箱
        """
        return self._call("FindTeamByEmail", {**self._meta(), "email": email, **kw})

    def get_deep_wiki(self, *, repoUrl: str = "", **kw) -> RpcResponse:
        """获取 DeepWiki 内容

        Args:
            repoUrl: 仓库 URL
        """
        return self._call("GetDeepWiki", {**self._meta(), "repoUrl": repoUrl, **kw})

    def get_default_workflow_templates(self, **kw) -> RpcResponse:
        """获取默认 Workflow 模板"""
        return self._call("GetDefaultWorkflowTemplates", {**self._meta(), **kw})

    def get_extension_stats(self, **kw) -> RpcResponse:
        """获取扩展使用统计"""
        return self._call("GetExtensionStats", {**self._meta(), **kw})

    def get_m_query(self, **kw) -> RpcResponse:
        """获取 M-Query"""
        return self._call("GetMQuery", {**self._meta(), **kw})

    def get_status(self, **kw) -> RpcResponse:
        """获取服务状态"""
        return self._call("GetStatus", {**self._meta(), **kw})

    def get_supabase_secret(self, **kw) -> RpcResponse:
        """获取 Supabase Secret"""
        return self._call("GetSupabaseSecret", {**self._meta(), **kw})

    def get_web_docs_options(self, **kw) -> RpcResponse:
        """获取 Web 文档选项"""
        return self._call("GetWebDocsOptions", {**self._meta(), **kw})

    def get_web_search_redirect(self, *, query: str = "", **kw) -> RpcResponse:
        """获取 Web 搜索重定向 URL

        Args:
            query: 搜索关键词
        """
        return self._call("GetWebSearchRedirect", {**self._meta(), "query": query, **kw})

    def get_web_search_results(self, *, query: str = "", **kw) -> RpcResponse:
        """获取 Web 搜索结果

        Args:
            query: 搜索关键词
        """
        return self._call("GetWebSearchResults", {**self._meta(), "query": query, **kw})

    def join_waitlist(self, *, email: str = "", feature: str = "", **kw) -> RpcResponse:
        """加入功能等待列表

        Args:
            email: 邮箱
            feature: 功能名称
        """
        return self._call("JoinWaitlist", {**self._meta(), "email": email, "feature": feature, **kw})

    def query_image_for_pixel(self, *, imageData: str = "", x: int = 0, y: int = 0, **kw) -> RpcResponse:
        """查询图片像素信息

        Args:
            imageData: 图片数据
            x: X 坐标
            y: Y 坐标
        """
        return self._call("QueryImageForPixel", {
            **self._meta(), "imageData": imageData, "x": x, "y": y, **kw})

    def register_external_user(self, *, email: str = "", **kw) -> RpcResponse:
        """注册外部用户

        Args:
            email: 用户邮箱
        """
        return self._call("RegisterExternalUser", {**self._meta(), "email": email, **kw})

    def send_referral_email(self, *, email: str = "", **kw) -> RpcResponse:
        """发送推荐邮件

        Args:
            email: 收件人邮箱
        """
        return self._call("SendReferralEmail", {**self._meta(), "email": email, **kw})

    def subscribe_to_blog(self, *, email: str = "", **kw) -> RpcResponse:
        """订阅博客

        Args:
            email: 邮箱
        """
        return self._call("SubscribeToBlog", {**self._meta(), "email": email, **kw})

    def unsubscribe_from_emails(self, *, token: str = "", **kw) -> RpcResponse:
        """退订邮件

        Args:
            token: 退订 Token
        """
        return self._call("UnsubscribeFromEmails", {**self._meta(), "token": token, **kw})

    # ── 混合日志 (Hybrid Logging) ──

    def log_cascade_prompt_hybrid(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cascade Prompt 混合日志

        Args:
            data: 日志数据
        """
        return self._call("LogCascadePromptHybrid", {**self._meta(), "data": data or {}, **kw})

    def log_cascade_session_hybrid(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cascade Session 混合日志

        Args:
            data: 会话日志数据
        """
        return self._call("LogCascadeSessionHybrid", {**self._meta(), "data": data or {}, **kw})

    def log_chat_hybrid_error(self, *, error: dict = None, **kw) -> RpcResponse:
        """记录 Chat 混合模式错误

        Args:
            error: 错误数据
        """
        return self._call("LogChatHybridError", {**self._meta(), "error": error or {}, **kw})

    def log_completions_hybrid(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录补全混合日志

        Args:
            data: 补全日志数据
        """
        return self._call("LogCompletionsHybrid", {**self._meta(), "data": data or {}, **kw})

    def log_feedback_hybrid(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录反馈混合日志

        Args:
            data: 反馈数据
        """
        return self._call("LogFeedbackHybrid", {**self._meta(), "data": data or {}, **kw})

    # ── 批量记录 ──

    def batch_record_chat_request_records(self, *, records: list = None, **kw) -> RpcResponse:
        """批量记录聊天请求

        Args:
            records: 聊天请求记录列表
        """
        return self._call("BatchRecordChatRequestRecords", {**self._meta(), "records": records or [], **kw})

    def batch_record_completions(self, *, completions: list = None, **kw) -> RpcResponse:
        """批量记录补全

        Args:
            completions: 补全记录列表
        """
        return self._call("BatchRecordCompletions", {**self._meta(), "completions": completions or [], **kw})

    def batch_record_prompts(self, *, prompts: list = None, **kw) -> RpcResponse:
        """批量记录 Prompt

        Args:
            prompts: Prompt 记录列表
        """
        return self._call("BatchRecordPrompts", {**self._meta(), "prompts": prompts or [], **kw})

    def batch_record_raw_completions(self, *, completions: list = None, **kw) -> RpcResponse:
        """批量记录原始补全

        Args:
            completions: 原始补全列表
        """
        return self._call("BatchRecordRawCompletions", {**self._meta(), "completions": completions or [], **kw})

    def batch_record_user_last_update_times(self, *, updates: list = None, **kw) -> RpcResponse:
        """批量记录用户最后更新时间

        Args:
            updates: 更新时间列表
        """
        return self._call("BatchRecordUserLastUpdateTimes", {**self._meta(), "updates": updates or [], **kw})

    # ── 遥测记录 (Record) ──

    def record_arena_mode_trajectory_details(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Arena 模式轨迹详情

        Args:
            data: 轨迹数据
        """
        return self._call("RecordArenaModeTrajectoryDetails", {**self._meta(), "data": data or {}, **kw})

    def record_async(self, *, data: dict = None, **kw) -> RpcResponse:
        """异步记录事件

        Args:
            data: 事件数据
        """
        return self._call("RecordAsync", {**self._meta(), "data": data or {}, **kw})

    def record_auto_cascade_telemetry(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Auto-Cascade 遥测

        Args:
            data: 遥测数据
        """
        return self._call("RecordAutoCascadeTelemetry", {**self._meta(), "data": data or {}, **kw})

    def record_cascade_usage(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cascade 使用量

        Args:
            data: 使用量数据
        """
        return self._call("RecordCascadeUsage", {**self._meta(), "data": data or {}, **kw})

    def record_chat(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录聊天

        Args:
            data: 聊天数据
        """
        return self._call("RecordChat", {**self._meta(), "data": data or {}, **kw})

    def record_chat_feedback(self, *, messageId: str = "", feedback: str = "", **kw) -> RpcResponse:
        """记录聊天反馈

        Args:
            messageId: 消息 ID
            feedback: 反馈 (thumbsUp/thumbsDown)
        """
        return self._call("RecordChatFeedback", {
            **self._meta(), "messageId": messageId, "feedback": feedback, **kw})

    def record_chat_model_node_run(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Chat 模型节点运行

        Args:
            data: 节点运行数据
        """
        return self._call("RecordChatModelNodeRun", {**self._meta(), "data": data or {}, **kw})

    def record_chat_panel_session(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Chat Panel 会话

        Args:
            data: 会话数据
        """
        return self._call("RecordChatPanelSession", {**self._meta(), "data": data or {}, **kw})

    def record_code_tracker_updates(self, *, updates: list = None, **kw) -> RpcResponse:
        """记录代码追踪器更新

        Args:
            updates: 更新列表
        """
        return self._call("RecordCodeTrackerUpdates", {**self._meta(), "updates": updates or [], **kw})

    def record_command_usage(self, *, command: str = "", **kw) -> RpcResponse:
        """记录命令使用

        Args:
            command: 命令名称
        """
        return self._call("RecordCommandUsage", {**self._meta(), "command": command, **kw})

    def record_commit_message_generation(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Commit 消息生成

        Args:
            data: 生成数据
        """
        return self._call("RecordCommitMessageGeneration", {**self._meta(), "data": data or {}, **kw})

    def record_commit_message_save(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Commit 消息保存

        Args:
            data: 保存数据
        """
        return self._call("RecordCommitMessageSave", {**self._meta(), "data": data or {}, **kw})

    def record_completion_example(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录补全示例

        Args:
            data: 示例数据
        """
        return self._call("RecordCompletionExample", {**self._meta(), "data": data or {}, **kw})

    def record_completions(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录补全结果

        Args:
            data: 补全数据
        """
        return self._call("RecordCompletions", {**self._meta(), "data": data or {}, **kw})

    def record_context_refresh(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录上下文刷新

        Args:
            data: 刷新数据
        """
        return self._call("RecordContextRefresh", {**self._meta(), "data": data or {}, **kw})

    def record_context_to_prompt(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录上下文到 Prompt 的转换

        Args:
            data: 转换数据
        """
        return self._call("RecordContextToPrompt", {**self._meta(), "data": data or {}, **kw})

    def record_cortex_coding_plan(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cortex 编码计划

        Args:
            data: 计划数据
        """
        return self._call("RecordCortexCodingPlan", {**self._meta(), "data": data or {}, **kw})

    def record_cortex_coding_step(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cortex 编码步骤

        Args:
            data: 步骤数据
        """
        return self._call("RecordCortexCodingStep", {**self._meta(), "data": data or {}, **kw})

    def record_cortex_coding_step_feedback(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cortex 编码步骤反馈

        Args:
            data: 反馈数据
        """
        return self._call("RecordCortexCodingStepFeedback", {**self._meta(), "data": data or {}, **kw})

    def record_cortex_error(self, *, error: dict = None, **kw) -> RpcResponse:
        """记录 Cortex 错误

        Args:
            error: 错误数据
        """
        return self._call("RecordCortexError", {**self._meta(), "error": error or {}, **kw})

    def record_cortex_execution_metadata(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cortex 执行元数据

        Args:
            data: 执行元数据
        """
        return self._call("RecordCortexExecutionMetadata", {**self._meta(), "data": data or {}, **kw})

    def record_cortex_feedback(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cortex 反馈

        Args:
            data: 反馈数据
        """
        return self._call("RecordCortexFeedback", {**self._meta(), "data": data or {}, **kw})

    def record_cortex_generator_metadata(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cortex 生成器元数据

        Args:
            data: 生成器元数据
        """
        return self._call("RecordCortexGeneratorMetadata", {**self._meta(), "data": data or {}, **kw})

    def record_cortex_step(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cortex 步骤

        Args:
            data: 步骤数据
        """
        return self._call("RecordCortexStep", {**self._meta(), "data": data or {}, **kw})

    def record_cortex_trajectory(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cortex 轨迹

        Args:
            data: 轨迹数据
        """
        return self._call("RecordCortexTrajectory", {**self._meta(), "data": data or {}, **kw})

    def record_cortex_trajectory_step(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cortex 轨迹步骤

        Args:
            data: 步骤数据
        """
        return self._call("RecordCortexTrajectoryStep", {**self._meta(), "data": data or {}, **kw})

    def record_debounce(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Debounce 事件

        Args:
            data: 事件数据
        """
        return self._call("RecordDebounce", {**self._meta(), "data": data or {}, **kw})

    def record_event(self, *, eventType: str = "", data: dict = None, **kw) -> RpcResponse:
        """记录通用事件

        Args:
            eventType: 事件类型
            data: 事件数据
        """
        return self._call("RecordEvent", {**self._meta(), "eventType": eventType, "data": data or {}, **kw})

    def record_git_telemetry(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Git 遥测

        Args:
            data: Git 遥测数据
        """
        return self._call("RecordGitTelemetry", {**self._meta(), "data": data or {}, **kw})

    def record_m_query(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 M-Query

        Args:
            data: 查询数据
        """
        return self._call("RecordMQuery", {**self._meta(), "data": data or {}, **kw})

    def record_new_cortex_plan(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录新 Cortex 计划

        Args:
            data: 计划数据
        """
        return self._call("RecordNewCortexPlan", {**self._meta(), "data": data or {}, **kw})

    def record_opportunities(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录补全机会

        Args:
            data: 机会数据
        """
        return self._call("RecordOpportunities", {**self._meta(), "data": data or {}, **kw})

    def record_pinned_context(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录固定上下文

        Args:
            data: 上下文数据
        """
        return self._call("RecordPinnedContext", {**self._meta(), "data": data or {}, **kw})

    def record_profiling_data(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录性能分析数据

        Args:
            data: 分析数据
        """
        return self._call("RecordProfilingData", {**self._meta(), "data": data or {}, **kw})

    def record_read_url_content(self, *, url: str = "", **kw) -> RpcResponse:
        """记录 URL 内容读取

        Args:
            url: 读取的 URL
        """
        return self._call("RecordReadUrlContent", {**self._meta(), "url": url, **kw})

    def record_search(self, *, query: str = "", **kw) -> RpcResponse:
        """记录搜索事件

        Args:
            query: 搜索关键词
        """
        return self._call("RecordSearch", {**self._meta(), "query": query, **kw})

    def record_search_doc_open(self, *, docId: str = "", **kw) -> RpcResponse:
        """记录搜索文档打开

        Args:
            docId: 文档 ID
        """
        return self._call("RecordSearchDocOpen", {**self._meta(), "docId": docId, **kw})

    def record_search_results(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录搜索结果

        Args:
            data: 搜索结果数据
        """
        return self._call("RecordSearchResults", {**self._meta(), "data": data or {}, **kw})

    def record_search_results_view(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录搜索结果查看

        Args:
            data: 查看数据
        """
        return self._call("RecordSearchResultsView", {**self._meta(), "data": data or {}, **kw})

    def record_state_initialization_data(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录状态初始化数据

        Args:
            data: 初始化数据
        """
        return self._call("RecordStateInitializationData", {**self._meta(), "data": data or {}, **kw})

    def record_trajectory_segment_analytics(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录轨迹段分析

        Args:
            data: 分析数据
        """
        return self._call("RecordTrajectorySegmentAnalytics", {**self._meta(), "data": data or {}, **kw})

    def record_trajectory_segment_events(self, *, events: list = None, **kw) -> RpcResponse:
        """记录轨迹段事件

        Args:
            events: 事件列表
        """
        return self._call("RecordTrajectorySegmentEvents", {**self._meta(), "events": events or [], **kw})

    def record_windsurf_review_event(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Windsurf Review 事件

        Args:
            data: 事件数据
        """
        return self._call("RecordWindsurfReviewEvent", {**self._meta(), "data": data or {}, **kw})

    def record_windsurf_reviews_telemetry(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Windsurf Reviews 遥测

        Args:
            data: 遥测数据
        """
        return self._call("RecordWindsurfReviewsTelemetry", {**self._meta(), "data": data or {}, **kw})

    # ── 错误上传 ──

    def upload_error_traces(self, *, traces: list = None, **kw) -> RpcResponse:
        """上传错误跟踪

        Args:
            traces: 错误跟踪列表
        """
        return self._call("UploadErrorTraces", {**self._meta(), "traces": traces or [], **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        """调用任意 ApiServer 方法"""
        return self._call(method, payload, **kw)

"""ApiServerService — 164 RPC methods

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

    # ═══════════════════════════════════════════════════
    #  模型
    # ═══════════════════════════════════════════════════

    def get_model_providers(self) -> list:
        """获取模型提供商列表"""
        try:
            r = self._call("GetModelProviders", self._meta())
            if r.ok and isinstance(getattr(r, 'data', None), dict):
                return [ModelProvider.from_response(p)
                        for p in r.data.get("modelProviders", [])]
        except Exception:
            pass
        return []

    def get_model_providers_raw(self) -> RpcResponse:
        return self._call("GetModelProviders", self._meta())

    def get_cascade_model_configs(self) -> RpcResponse:
        """获取 Cascade 模型配置"""
        return self._call("GetCascadeModelConfigs", self._meta())

    def get_cascade_model_configs_for_site(self) -> RpcResponse:
        return self._call("GetCascadeModelConfigsForSite", self._meta())

    def get_cli_model_configs(self) -> RpcResponse:
        return self._call("GetCliModelConfigs", self._meta())

    def get_cli_model_configs_for_site(self) -> RpcResponse:
        return self._call("GetCliModelConfigsForSite", self._meta())

    def get_command_model_configs(self) -> RpcResponse:
        return self._call("GetCommandModelConfigs", self._meta())

    def get_command_model_configs_for_site(self) -> RpcResponse:
        return self._call("GetCommandModelConfigsForSite", self._meta())

    def get_model_statuses(self) -> RpcResponse:
        return self._call("GetModelStatuses", self._meta())

    def assign_model(self, **kw) -> RpcResponse:
        return self._call("AssignModel", {**self._meta(), **kw})

    def assign_arena_model(self, **kw) -> RpcResponse:
        return self._call("AssignArenaModel", {**self._meta(), **kw})

    def create_external_models(self, **kw) -> RpcResponse:
        return self._call("CreateExternalModels", {**self._meta(), **kw})

    def delete_external_models(self, **kw) -> RpcResponse:
        return self._call("DeleteExternalModels", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  聊天 & 补全
    # ═══════════════════════════════════════════════════

    def get_chat_completions(self, **kw) -> RpcResponse:
        return self._call("GetChatCompletions", {**self._meta(), **kw})

    def get_chat_message(self, **kw) -> RpcResponse:
        return self._call("GetChatMessage", {**self._meta(), **kw})

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

    def cancel_completions(self) -> RpcResponse:
        return self._call("CancelCompletions", self._meta())

    # ═══════════════════════════════════════════════════
    #  使用记录
    # ═══════════════════════════════════════════════════

    def record_cascade_usage(self, **kw) -> RpcResponse:
        return self._call("RecordCascadeUsage", {**self._meta(), **kw})

    def batch_record_chat_request_records(self, **kw) -> RpcResponse:
        return self._call("BatchRecordChatRequestRecords", {**self._meta(), **kw})

    def batch_record_completions(self, **kw) -> RpcResponse:
        return self._call("BatchRecordCompletions", {**self._meta(), **kw})

    def batch_record_prompts(self, **kw) -> RpcResponse:
        return self._call("BatchRecordPrompts", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  配置 & 状态
    # ═══════════════════════════════════════════════════

    def get_lifeguard_config(self) -> RpcResponse:
        return self._call("GetLifeguardConfig", self._meta())

    def get_extension_stats(self) -> RpcResponse:
        return self._call("GetExtensionStats", self._meta())

    def get_completion_examples(self) -> RpcResponse:
        return self._call("GetCompletionExamples", self._meta())

    # ═══════════════════════════════════════════════════
    #  推荐 & 分享
    # ═══════════════════════════════════════════════════

    def send_referral_email(self, email: str = "") -> RpcResponse:
        return self._call("SendReferralEmail", {**self._meta(), "email": email})

    def create_trajectory_share(self, **kw) -> RpcResponse:
        return self._call("CreateTrajectoryShareStream", {**self._meta(), **kw})

    def fetch_trajectory_share(self, share_id: str = "") -> RpcResponse:
        return self._call("FetchTrajectoryShare", {"shareId": share_id})

    def delete_trajectory_share(self, share_id: str = "") -> RpcResponse:
        return self._call("DeleteTrajectoryShare", {**self._meta(), "shareId": share_id})

    # ═══════════════════════════════════════════════════
    #  Windsurf JS App (Web 部署)
    # ═══════════════════════════════════════════════════

    def create_windsurf_js_app(self, **kw) -> RpcResponse:
        return self._call("CreateWindsurfJSApp", {**self._meta(), **kw})

    def deploy_windsurf_js_app(self, **kw) -> RpcResponse:
        return self._call("DeployWindsurfJSApp", {**self._meta(), **kw})

    def delete_windsurf_js_app(self, app_id: str = "") -> RpcResponse:
        return self._call("DeleteWindsurfJSApp", {**self._meta(), "appId": app_id})

    # ═══════════════════════════════════════════════════
    #  Hybrid Deployment
    # ═══════════════════════════════════════════════════

    def check_hybrid_deployment_status(self) -> RpcResponse:
        return self._call("CheckHybridDeploymentStatus", self._meta())

    def create_hybrid_deployment_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("CreateHybridDeploymentInternal", {"secret": secret, **kw})

    # ═══════════════════════════════════════════════════
    #  代码
    # ═══════════════════════════════════════════════════

    def capture_code(self, **kw) -> RpcResponse:
        return self._call("CaptureCode", {**self._meta(), **kw})

    def get_code_map_metadata(self) -> RpcResponse:
        return self._call("GetCodeMapMetadata", self._meta())

    def delete_shared_code_map(self, **kw) -> RpcResponse:
        return self._call("DeleteSharedCodeMap", {**self._meta(), **kw})

    def generate_synthetic_rule(self, **kw) -> RpcResponse:
        return self._call("GenerateSyntheticRule", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  OIDC
    # ═══════════════════════════════════════════════════

    def get_all_oidc_providers(self) -> RpcResponse:
        return self._call("GetAllOidcProviders", self._meta())

    def exchange_oidc_code(self, code: str = "") -> RpcResponse:
        return self._call("ExchangeOidcCode", {**self._meta(), "code": code})

    def delete_oidc_provider(self, provider_id: str = "") -> RpcResponse:
        return self._call("DeleteOidcProvider", {**self._meta(), "providerId": provider_id})

    # ═══════════════════════════════════════════════════
    #  Allowlist / Org Controls
    # ═══════════════════════════════════════════════════

    def get_allowlist(self) -> RpcResponse:
        return self._call("GetAllowlist", self._meta())

    def delete_allowlist(self) -> RpcResponse:
        return self._call("DeleteAllowlist", self._meta())

    def get_team_organizational_controls(self) -> RpcResponse:
        return self._call("GetTeamOrganizationalControls", self._meta())

    def delete_team_organizational_controls(self) -> RpcResponse:
        return self._call("DeleteTeamOrganizationalControls", self._meta())

    # ═══════════════════════════════════════════════════
    #  Trajectory & Heuristics
    # ═══════════════════════════════════════════════════

    def apply_trajectory_heuristics(self, **kw) -> RpcResponse:
        return self._call("ApplyTrajectoryHeuristics", {**self._meta(), **kw})

    def find_team_by_email(self, email: str = "") -> RpcResponse:
        return self._call("FindTeamByEmail", {**self._meta(), "email": email})

    # ═══════════════════════════════════════════════════
    #  Bug Report
    # ═══════════════════════════════════════════════════

    def accept_bug(self, **kw) -> RpcResponse:
        return self._call("AcceptBug", {**self._meta(), **kw})

    def check_bugs(self, **kw) -> RpcResponse:
        return self._call("CheckBugs", {**self._meta(), **kw})

    def reject_bug(self, **kw) -> RpcResponse:
        return self._call("RejectBug", {**self._meta(), **kw})

    def submit_bug_report(self, **kw) -> RpcResponse:
        return self._call("SubmitBugReport", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Streaming
    # ═══════════════════════════════════════════════════

    def get_streaming_completions(self, **kw) -> RpcResponse:
        return self._call("GetStreamingCompletions", {**self._meta(), **kw})

    def get_streaming_external_chat_completions(self, **kw) -> RpcResponse:
        return self._call("GetStreamingExternalChatCompletions", {**self._meta(), **kw})

    def get_streaming_model(self, **kw) -> RpcResponse:
        return self._call("GetStreamingModel", {**self._meta(), **kw})

    def get_devstral_stream(self, **kw) -> RpcResponse:
        return self._call("GetDevstralStream", {**self._meta(), **kw})

    def get_completions(self, **kw) -> RpcResponse:
        return self._call("GetCompletions", {**self._meta(), **kw})

    def get_embeddings(self, **kw) -> RpcResponse:
        return self._call("GetEmbeddings", {**self._meta(), **kw})

    def get_transcription(self, **kw) -> RpcResponse:
        return self._call("GetTranscription", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  状态 & 配置 (补充)
    # ═══════════════════════════════════════════════════

    def get_status(self, **kw) -> RpcResponse:
        return self._call("GetStatus", {**self._meta(), **kw})

    def get_deep_wiki(self, **kw) -> RpcResponse:
        return self._call("GetDeepWiki", {**self._meta(), **kw})

    def get_default_workflow_templates(self) -> RpcResponse:
        return self._call("GetDefaultWorkflowTemplates", self._meta())

    def get_deployment_config(self, **kw) -> RpcResponse:
        return self._call("GetDeploymentConfig", {**self._meta(), **kw})

    def get_external_model(self, **kw) -> RpcResponse:
        return self._call("GetExternalModel", {**self._meta(), **kw})

    def get_web_docs_options(self) -> RpcResponse:
        return self._call("GetWebDocsOptions", self._meta())

    def get_web_search_results(self, query: str = "", **kw) -> RpcResponse:
        return self._call("GetWebSearchResults", {**self._meta(), "query": query, **kw})

    def get_web_search_redirect(self, **kw) -> RpcResponse:
        return self._call("GetWebSearchRedirect", {**self._meta(), **kw})

    def get_user_allowlist(self) -> RpcResponse:
        return self._call("GetUserAllowlist", self._meta())

    def insert_allowlist(self, **kw) -> RpcResponse:
        return self._call("InsertAllowlist", {**self._meta(), **kw})

    def get_team_oidc_providers(self) -> RpcResponse:
        return self._call("GetTeamOidcProviders", self._meta())

    def get_team_organizational_controls(self) -> RpcResponse:
        return self._call("GetTeamOrganizationalControls", self._meta())

    def upsert_team_organizational_controls(self, **kw) -> RpcResponse:
        return self._call("UpsertTeamOrganizationalControls", {**self._meta(), **kw})

    def upsert_team_organizational_controls_for_site(self, **kw) -> RpcResponse:
        return self._call("UpsertTeamOrganizationalControlsForSite", {**self._meta(), **kw})

    def delete_team_organizational_controls(self) -> RpcResponse:
        return self._call("DeleteTeamOrganizationalControls", self._meta())

    def upsert_deployment_config(self, **kw) -> RpcResponse:
        return self._call("UpsertDeploymentConfig", {**self._meta(), **kw})

    def get_cascade_model_configs_for_site(self) -> RpcResponse:
        return self._call("GetCascadeModelConfigsForSite", self._meta())

    # ═══════════════════════════════════════════════════
    #  Hybrid Deployment (补充)
    # ═══════════════════════════════════════════════════

    def get_hybrid_deployments_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("GetHybridDeploymentsInternal", {"secret": secret, **kw})

    def register_hybrid_deployment(self, **kw) -> RpcResponse:
        return self._call("RegisterHybridDeployment", {**self._meta(), **kw})

    def remove_hybrid_deployment_internal(self, secret: str = "", **kw) -> RpcResponse:
        return self._call("RemoveHybridDeploymentInternal", {"secret": secret, **kw})

    def log_cascade_prompt_hybrid(self, **kw) -> RpcResponse:
        return self._call("LogCascadePromptHybrid", {**self._meta(), **kw})

    def log_cascade_session(self, **kw) -> RpcResponse:
        return self._call("LogCascadeSession", {**self._meta(), **kw})

    def log_chat_hybrid_error(self, **kw) -> RpcResponse:
        return self._call("LogChatHybridError", {**self._meta(), **kw})

    def log_completions_hybrid(self, **kw) -> RpcResponse:
        return self._call("LogCompletionsHybrid", {**self._meta(), **kw})

    def log_feedback_hybrid(self, **kw) -> RpcResponse:
        return self._call("LogFeedbackHybrid", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Record / Telemetry (全部)
    # ═══════════════════════════════════════════════════

    def record(self, **kw) -> RpcResponse:
        return self._call("Record", {**self._meta(), **kw})

    def record_arena_mode_trajectory_details(self, **kw) -> RpcResponse:
        return self._call("RecordArenaModeTrajectoryDetails", {**self._meta(), **kw})

    def record_async_telemetry(self, **kw) -> RpcResponse:
        return self._call("RecordAsyncTelemetry", {**self._meta(), **kw})

    def record_auto_cascade_telemetry(self, **kw) -> RpcResponse:
        return self._call("RecordAutoCascadeTelemetry", {**self._meta(), **kw})

    def record_chat(self, **kw) -> RpcResponse:
        return self._call("RecordChat", {**self._meta(), **kw})

    def record_chat_feedback(self, **kw) -> RpcResponse:
        return self._call("RecordChatFeedback", {**self._meta(), **kw})

    def record_chat_model_node_run(self, **kw) -> RpcResponse:
        return self._call("RecordChatModelNodeRun", {**self._meta(), **kw})

    def record_chat_panel_session(self, **kw) -> RpcResponse:
        return self._call("RecordChatPanelSession", {**self._meta(), **kw})

    def record_code_tracker_updates(self, **kw) -> RpcResponse:
        return self._call("RecordCodeTrackerUpdates", {**self._meta(), **kw})

    def record_command_usage(self, **kw) -> RpcResponse:
        return self._call("RecordCommandUsage", {**self._meta(), **kw})

    def record_commit_message_generation(self, **kw) -> RpcResponse:
        return self._call("RecordCommitMessageGeneration", {**self._meta(), **kw})

    def record_commit_message_save(self, **kw) -> RpcResponse:
        return self._call("RecordCommitMessageSave", {**self._meta(), **kw})

    def record_completion_example(self, **kw) -> RpcResponse:
        return self._call("RecordCompletionExample", {**self._meta(), **kw})

    def record_completions(self, **kw) -> RpcResponse:
        return self._call("RecordCompletions", {**self._meta(), **kw})

    def record_context_refresh(self, **kw) -> RpcResponse:
        return self._call("RecordContextRefresh", {**self._meta(), **kw})

    def record_context_to_prompt(self, **kw) -> RpcResponse:
        return self._call("RecordContextToPrompt", {**self._meta(), **kw})

    def record_cortex_coding_plan(self, **kw) -> RpcResponse:
        return self._call("RecordCortexCodingPlan", {**self._meta(), **kw})

    def record_cortex_coding_step(self, **kw) -> RpcResponse:
        return self._call("RecordCortexCodingStep", {**self._meta(), **kw})

    def record_cortex_coding_step_feedback(self, **kw) -> RpcResponse:
        return self._call("RecordCortexCodingStepFeedback", {**self._meta(), **kw})

    def record_cortex_error(self, **kw) -> RpcResponse:
        return self._call("RecordCortexError", {**self._meta(), **kw})

    def record_cortex_execution_metadata(self, **kw) -> RpcResponse:
        return self._call("RecordCortexExecutionMetadata", {**self._meta(), **kw})

    def record_cortex_feedback(self, **kw) -> RpcResponse:
        return self._call("RecordCortexFeedback", {**self._meta(), **kw})

    def record_cortex_generator_metadata(self, **kw) -> RpcResponse:
        return self._call("RecordCortexGeneratorMetadata", {**self._meta(), **kw})

    def record_cortex_step(self, **kw) -> RpcResponse:
        return self._call("RecordCortexStep", {**self._meta(), **kw})

    def record_cortex_trajectory(self, **kw) -> RpcResponse:
        return self._call("RecordCortexTrajectory", {**self._meta(), **kw})

    def record_cortex_trajectory_step(self, **kw) -> RpcResponse:
        return self._call("RecordCortexTrajectoryStep", {**self._meta(), **kw})

    def record_debounce_failed(self, **kw) -> RpcResponse:
        return self._call("RecordDebounceFailed", {**self._meta(), **kw})

    def record_event(self, **kw) -> RpcResponse:
        return self._call("RecordEvent", {**self._meta(), **kw})

    def record_git_telemetry(self, **kw) -> RpcResponse:
        return self._call("RecordGitTelemetry", {**self._meta(), **kw})

    def record_new_cortex_plan(self, **kw) -> RpcResponse:
        return self._call("RecordNewCortexPlan", {**self._meta(), **kw})

    def record_opportunities(self, **kw) -> RpcResponse:
        return self._call("RecordOpportunities", {**self._meta(), **kw})

    def record_pinned_context(self, **kw) -> RpcResponse:
        return self._call("RecordPinnedContext", {**self._meta(), **kw})

    def record_profiling_data(self, **kw) -> RpcResponse:
        return self._call("RecordProfilingData", {**self._meta(), **kw})

    def record_read_url_content(self, **kw) -> RpcResponse:
        return self._call("RecordReadUrlContent", {**self._meta(), **kw})

    def record_search(self, **kw) -> RpcResponse:
        return self._call("RecordSearch", {**self._meta(), **kw})

    def record_search_doc_open(self, **kw) -> RpcResponse:
        return self._call("RecordSearchDocOpen", {**self._meta(), **kw})

    def record_search_results(self, **kw) -> RpcResponse:
        return self._call("RecordSearchResults", {**self._meta(), **kw})

    def record_search_results_view(self, **kw) -> RpcResponse:
        return self._call("RecordSearchResultsView", {**self._meta(), **kw})

    def record_state_initialization_data(self, **kw) -> RpcResponse:
        return self._call("RecordStateInitializationData", {**self._meta(), **kw})

    def record_trajectory_segment_analytics(self, **kw) -> RpcResponse:
        return self._call("RecordTrajectorySegmentAnalytics", {**self._meta(), **kw})

    def record_trajectory_segment_events(self, **kw) -> RpcResponse:
        return self._call("RecordTrajectorySegmentEvents", {**self._meta(), **kw})

    def record_windsurf_review_event(self, **kw) -> RpcResponse:
        return self._call("RecordWindsurfReviewEvent", {**self._meta(), **kw})

    def record_windsurf_reviews_telemetry(self, **kw) -> RpcResponse:
        return self._call("RecordWindsurfReviewsTelemetry", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  OIDC (补充)
    # ═══════════════════════════════════════════════════

    def refresh_oidc_token(self, **kw) -> RpcResponse:
        return self._call("RefreshOidcToken", {**self._meta(), **kw})

    def register_oidc_provider(self, **kw) -> RpcResponse:
        return self._call("RegisterOidcProvider", {**self._meta(), **kw})

    def update_oidc_provider(self, **kw) -> RpcResponse:
        return self._call("UpdateOidcProvider", {**self._meta(), **kw})

    def get_oidc_authorization_url(self, **kw) -> RpcResponse:
        return self._call("GetOidcAuthorizationUrl", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  External User / Model
    # ═══════════════════════════════════════════════════

    def register_external_user(self, **kw) -> RpcResponse:
        return self._call("RegisterExternalUser", {**self._meta(), **kw})

    def delete_external_user(self, **kw) -> RpcResponse:
        return self._call("DeleteExternalUser", {**self._meta(), **kw})

    def update_external_models(self, **kw) -> RpcResponse:
        return self._call("UpdateExternalModels", {**self._meta(), **kw})

    def update_external_models_group(self, **kw) -> RpcResponse:
        return self._call("UpdateExternalModelsGroup", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  CodeMap & Sharing
    # ═══════════════════════════════════════════════════

    def share_code_map(self, **kw) -> RpcResponse:
        return self._call("ShareCodeMap", {**self._meta(), **kw})

    def get_shared_code_map(self, **kw) -> RpcResponse:
        return self._call("GetSharedCodeMap", {**self._meta(), **kw})

    def list_user_shared_code_maps(self) -> RpcResponse:
        return self._call("ListUserSharedCodeMaps", self._meta())

    def update_code_map_sharing_mode(self, **kw) -> RpcResponse:
        return self._call("UpdateCodeMapSharingMode", {**self._meta(), **kw})

    def get_code_map_metadata(self) -> RpcResponse:
        return self._call("GetCodeMapMetadata", self._meta())

    def is_conversation_sharing_blocked(self, **kw) -> RpcResponse:
        return self._call("IsConversationSharingBlocked", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  杂项
    # ═══════════════════════════════════════════════════

    def provide_feedback(self, **kw) -> RpcResponse:
        return self._call("ProvideFeedback", {**self._meta(), **kw})

    def query_image_for_pixel(self, **kw) -> RpcResponse:
        return self._call("QueryImageForPixel", {**self._meta(), **kw})

    def run_code_alignment(self, **kw) -> RpcResponse:
        return self._call("RunCodeAlignment", {**self._meta(), **kw})

    def supports_remote_indexing(self, **kw) -> RpcResponse:
        return self._call("SupportsRemoteIndexing", {**self._meta(), **kw})

    def upload_error_traces(self, **kw) -> RpcResponse:
        return self._call("UploadErrorTraces", {**self._meta(), **kw})

    def validate_windsurf(self, **kw) -> RpcResponse:
        return self._call("ValidateWindsurf", {**self._meta(), **kw})

    def get_windsurf(self, **kw) -> RpcResponse:
        return self._call("GetWindsurf", {**self._meta(), **kw})

    def create_windsurf(self, **kw) -> RpcResponse:
        return self._call("CreateWindsurf", {**self._meta(), **kw})

    def delete_windsurf(self, **kw) -> RpcResponse:
        return self._call("DeleteWindsurf", {**self._meta(), **kw})

    def deploy_windsurf(self, **kw) -> RpcResponse:
        return self._call("DeployWindsurf", {**self._meta(), **kw})

    def join_waitlist(self, **kw) -> RpcResponse:
        return self._call("JoinWaitlist", {**self._meta(), **kw})

    def subscribe_to_blog(self, email: str = "", **kw) -> RpcResponse:
        return self._call("SubscribeToBlog", {**self._meta(), "email": email, **kw})

    def unsubscribe_from_emails(self, **kw) -> RpcResponse:
        return self._call("UnsubscribeFromEmails", {**self._meta(), **kw})

    def account_ownership_notification_dismiss(self, **kw) -> RpcResponse:
        return self._call("AccountOwnershipNotificationDismiss", {**self._meta(), **kw})

    def account_ownership_notification_verification(self, **kw) -> RpcResponse:
        return self._call("AccountOwnershipNotificationVerification", {**self._meta(), **kw})

    def ping_account_ownership_notification(self, **kw) -> RpcResponse:
        return self._call("PingAccountOwnershipNotificationVerification", {**self._meta(), **kw})

    def get_supabase_secret(self, **kw) -> RpcResponse:
        return self._call("GetSupabaseSecret", {**self._meta(), **kw})

    def capture_file(self, **kw) -> RpcResponse:
        return self._call("CaptureFile", {**self._meta(), **kw})

    def fetch_trajectory_share_by_user(self, **kw) -> RpcResponse:
        return self._call("FetchTrajectoryShareByUser", {**self._meta(), **kw})

    def get_config(self, **kw) -> RpcResponse:
        return self._call("GetConfig", {**self._meta(), **kw})

    def batch_record_raw_completions(self, **kw) -> RpcResponse:
        return self._call("BatchRecordRawCompletions", {**self._meta(), **kw})

    def batch_record_user_last_update_times(self, **kw) -> RpcResponse:
        return self._call("BatchRecordUserLastUpdateTimes", {**self._meta(), **kw})

    def delete_team(self, **kw) -> RpcResponse:
        return self._call("DeleteTeam", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  通用
    # ═══════════════════════════════════════════════════

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        """调用任意 ApiServer 方法"""
        return self._call(method, payload, **kw)

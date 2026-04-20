"""LanguageServerService — 171 RPC methods (本地)

本地 LS 进程的 gRPC 服务，用于补全、诊断、实验注入等。
逆向自 exa.language_server_pb.LanguageServerService

注意: LS 运行在 127.0.0.1 随机端口，需要探测。
部分方法需要 CSRF token (从 LS 进程环境变量读取)。
"""
import os
import re
import json
import subprocess
from ..transport import ConnectTransport, RpcResponse
from ..models import metadata, ExperimentKey


SERVICE = "exa.language_server_pb.LanguageServerService"


class LanguageServerService:
    """本地 LanguageServer 封装

    Args:
        port: LS gRPC 端口 (不传则自动探测)
        csrf_token: CSRF token (不传则尝试自动获取)
        api_key: API key
    """

    # 实验注入默认值
    FORCE_DISABLE = [ExperimentKey.CASCADE_ENFORCE_QUOTA]
    FORCE_ENABLE = [
        ExperimentKey.CASCADE_PLAN_BASED_CONFIG_OVERRIDE,
        ExperimentKey.CASCADE_ENABLE_MCP_TOOLS,
        ExperimentKey.CASCADE_WEB_APP_DEPLOYMENTS_ENABLED,
        ExperimentKey.CASCADE_ENABLE_PROXY_WEB_SERVER,
        ExperimentKey.CASCADE_ENABLE_AUTOMATED_MEMORIES,
        ExperimentKey.CASCADE_WINDSURF_BROWSER_TOOLS_ENABLED,
    ]

    def __init__(self, port: int = None, csrf_token: str = None, api_key: str = ""):
        self.port = port
        self.csrf_token = csrf_token
        self.api_key = api_key
        self._transport = None

    @property
    def transport(self) -> ConnectTransport:
        if self._transport is None:
            if not self.port:
                self.port = self.find_port()
            if self.port:
                headers = {}
                if self.csrf_token:
                    headers["x-csrf-token"] = self.csrf_token
                self._transport = ConnectTransport(
                    f"http://127.0.0.1:{self.port}", timeout=10, extra_headers=headers
                )
        return self._transport

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        t = self.transport
        if not t:
            return RpcResponse(ok=False, status=0, data={"error": "LS 未连接"})
        return t.call(SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    # ═══════════════════════════════════════════════════
    #  进程发现
    # ═══════════════════════════════════════════════════

    @staticmethod
    def find_process() -> dict:
        """查找 LS 进程 (Windows)

        Returns: {"pid": int, "port": int, "cmdline": str} 或 None
        """
        try:
            r = subprocess.run(
                ['powershell', '-Command',
                 'Get-Process language_server_windows_x64 -EA SilentlyContinue '
                 '| Select Id,@{N="Cmd";E={(Get-CimInstance Win32_Process -Filter '
                 '"ProcessId=$($_.Id)").CommandLine}} | ConvertTo-Json'],
                capture_output=True, text=True, timeout=10,
            )
            if not r.stdout.strip():
                return None
            data = json.loads(r.stdout)
            if isinstance(data, dict):
                data = [data]
            for proc in data:
                pid = proc.get("Id")
                cmd = proc.get("Cmd", "")
                port_m = re.search(r'--port[=\s]+(\d+)', cmd)
                port = int(port_m.group(1)) if port_m else None
                if pid:
                    return {"pid": pid, "port": port, "cmdline": cmd}
        except Exception:
            pass
        return None

    @staticmethod
    def find_port() -> int:
        """通过 Heartbeat 探测 LS 端口"""
        proc = LanguageServerService.find_process()
        if proc and proc.get("port"):
            return proc["port"]

        t = ConnectTransport("http://127.0.0.1:0", timeout=2)
        for port in range(49152, 49250):
            t.base_url = f"http://127.0.0.1:{port}"
            r = t.call(SERVICE, "Heartbeat", {"metadata": {}})
            if r.status != 0:
                return port
        return 0

    @staticmethod
    def read_csrf_from_process(pid: int) -> str:
        """从 LS 命令行读 CSRF token"""
        try:
            r = subprocess.run(
                ['powershell', '-Command',
                 f'(Get-CimInstance Win32_Process -Filter "ProcessId={pid}").CommandLine'],
                capture_output=True, text=True, timeout=5,
            )
            m = re.search(r'WINDSURF_CSRF_TOKEN[=]([^\s"]+)', r.stdout)
            return m.group(1) if m else ""
        except Exception:
            return ""

    def auto_connect(self) -> bool:
        """自动发现 LS 并连接"""
        proc = self.find_process()
        if not proc:
            return False
        self.port = proc.get("port") or self.find_port()
        if proc.get("pid"):
            self.csrf_token = self.read_csrf_from_process(proc["pid"])
        self._transport = None  # 重建
        return bool(self.port)

    # ═══════════════════════════════════════════════════
    #  核心方法
    # ═══════════════════════════════════════════════════

    def heartbeat(self) -> RpcResponse:
        return self._call("Heartbeat", {"metadata": {}})

    def get_completions(self, **kw) -> RpcResponse:
        return self._call("GetCompletions", {**self._meta(), **kw})

    def accept_completion(self, completion_id: str) -> RpcResponse:
        return self._call("AcceptCompletion",
                          {**self._meta(), "completionId": completion_id})

    # ═══════════════════════════════════════════════════
    #  实验注入
    # ═══════════════════════════════════════════════════

    def set_base_experiments(self, disable: list = None, enable: list = None) -> RpcResponse:
        """注入实验 flags

        Args:
            disable: 要禁用的实验 ID 列表 (默认禁用 CASCADE_ENFORCE_QUOTA)
            enable: 要启用的实验 ID 列表 (默认启用 Pro 功能)
        """
        return self._call("SetBaseExperiments", {
            "forceDisableExperiments": [int(x) for x in (disable or self.FORCE_DISABLE)],
            "forceEnableExperiments": [int(x) for x in (enable or self.FORCE_ENABLE)],
        })

    def inject_pro_experiments(self) -> RpcResponse:
        """一键注入全部 Pro 实验"""
        return self.set_base_experiments()

    # ═══════════════════════════════════════════════════
    #  Cascade 对话
    # ═══════════════════════════════════════════════════

    def start_cascade(self, **kw) -> RpcResponse:
        return self._call("StartCascade", {**self._meta(), **kw})

    def cancel_cascade_invocation(self, **kw) -> RpcResponse:
        return self._call("CancelCascadeInvocation", {**self._meta(), **kw})

    def cancel_cascade_invocation_and_wait(self, **kw) -> RpcResponse:
        return self._call("CancelCascadeInvocationAndWait", {**self._meta(), **kw})

    def cancel_cascade_steps(self, **kw) -> RpcResponse:
        return self._call("CancelCascadeSteps", {**self._meta(), **kw})

    def queue_cascade_message(self, **kw) -> RpcResponse:
        return self._call("QueueCascadeMessage", {**self._meta(), **kw})

    def send_user_cascade_message(self, **kw) -> RpcResponse:
        return self._call("SendUserCascadeMessage", {**self._meta(), **kw})

    def handle_cascade_user_interaction(self, **kw) -> RpcResponse:
        return self._call("HandleCascadeUserInteraction", {**self._meta(), **kw})

    def interrupt_with_queued_message(self, **kw) -> RpcResponse:
        return self._call("InterruptWithQueuedMessage", {**self._meta(), **kw})

    def move_queued_message(self, **kw) -> RpcResponse:
        return self._call("MoveQueuedMessage", {**self._meta(), **kw})

    def remove_from_queue(self, **kw) -> RpcResponse:
        return self._call("RemoveFromQueue", {**self._meta(), **kw})

    def branch_cascade(self, **kw) -> RpcResponse:
        return self._call("BranchCascade", {**self._meta(), **kw})

    def branch_cascade_and_generate_code_map(self, **kw) -> RpcResponse:
        return self._call("BranchCascadeAndGenerateCodeMap", {**self._meta(), **kw})

    def converge_arena_cascades(self, **kw) -> RpcResponse:
        return self._call("ConvergeArenaCascades", {**self._meta(), **kw})

    def spawn_arena_mode_mid_conversation(self, **kw) -> RpcResponse:
        return self._call("SpawnArenaModeMidConversation", {**self._meta(), **kw})

    def initialize_cascade_panel_state(self, **kw) -> RpcResponse:
        return self._call("InitializeCascadePanelState", {**self._meta(), **kw})

    def send_action_to_chat_panel(self, **kw) -> RpcResponse:
        return self._call("SendActionToChatPanel", {**self._meta(), **kw})

    def update_panel_state_with_user_status(self, **kw) -> RpcResponse:
        return self._call("UpdatePanelStateWithUserStatus", {**self._meta(), **kw})

    def acknowledge_cascade_code_edit(self, **kw) -> RpcResponse:
        return self._call("AcknowledgeCascadeCodeEdit", {**self._meta(), **kw})

    def revert_to_cascade_step(self, **kw) -> RpcResponse:
        return self._call("RevertToCascadeStep", {**self._meta(), **kw})

    def resolve_outstanding_steps(self, **kw) -> RpcResponse:
        return self._call("ResolveOutstandingSteps", {**self._meta(), **kw})

    def get_patch_and_code_change(self, **kw) -> RpcResponse:
        return self._call("GetPatchAndCodeChange", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Trajectory
    # ═══════════════════════════════════════════════════

    def get_all_cascade_trajectories(self) -> RpcResponse:
        return self._call("GetAllCascadeTrajectories", self._meta())

    def get_cascade_trajectory(self, **kw) -> RpcResponse:
        return self._call("GetCascadeTrajectory", {**self._meta(), **kw})

    def get_cascade_trajectory_steps(self, **kw) -> RpcResponse:
        return self._call("GetCascadeTrajectorySteps", {**self._meta(), **kw})

    def get_cascade_trajectory_generator_metadata(self, **kw) -> RpcResponse:
        return self._call("GetCascadeTrajectoryGeneratorMetadata", {**self._meta(), **kw})

    def get_cascade_transcript_for_trajectory_id(self, **kw) -> RpcResponse:
        return self._call("GetCascadeTranscriptForTrajectoryId", {**self._meta(), **kw})

    def archive_cascade_trajectory(self, **kw) -> RpcResponse:
        return self._call("ArchiveCascadeTrajectory", {**self._meta(), **kw})

    def delete_cascade_trajectory(self, **kw) -> RpcResponse:
        return self._call("DeleteCascadeTrajectory", {**self._meta(), **kw})

    def rename_cascade_trajectory(self, **kw) -> RpcResponse:
        return self._call("RenameCascadeTrajectory", {**self._meta(), **kw})

    def create_trajectory_share(self, **kw) -> RpcResponse:
        return self._call("CreateTrajectoryShare", {**self._meta(), **kw})

    def get_user_trajectory(self, **kw) -> RpcResponse:
        return self._call("GetUserTrajectory", {**self._meta(), **kw})

    def get_user_trajectory_debug(self, **kw) -> RpcResponse:
        return self._call("GetUserTrajectoryDebug", {**self._meta(), **kw})

    def get_user_trajectory_descriptions(self, **kw) -> RpcResponse:
        return self._call("GetUserTrajectoryDescriptions", {**self._meta(), **kw})

    def replay_ground_truth_trajectory(self, **kw) -> RpcResponse:
        return self._call("ReplayGroundTruthTrajectory", {**self._meta(), **kw})

    def sync_explore_agent_run(self, **kw) -> RpcResponse:
        return self._call("SyncExploreAgentRun", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Streaming
    # ═══════════════════════════════════════════════════

    def stream_cascade_panel_reactive_updates(self, **kw) -> RpcResponse:
        return self._call("StreamCascadePanelReactiveUpdates", {**self._meta(), **kw})

    def stream_cascade_reactive_updates(self, **kw) -> RpcResponse:
        return self._call("StreamCascadeReactiveUpdates", {**self._meta(), **kw})

    def stream_cascade_summaries_reactive_updates(self, **kw) -> RpcResponse:
        return self._call("StreamCascadeSummariesReactiveUpdates", {**self._meta(), **kw})

    def stream_user_trajectory_reactive_updates(self, **kw) -> RpcResponse:
        return self._call("StreamUserTrajectoryReactiveUpdates", {**self._meta(), **kw})

    def stream_terminal_shell_command(self, **kw) -> RpcResponse:
        return self._call("StreamTerminalShellCommand", {**self._meta(), **kw})

    def handle_streaming_command(self, **kw) -> RpcResponse:
        return self._call("HandleStreamingCommand", {**self._meta(), **kw})

    def handle_streaming_tab(self, **kw) -> RpcResponse:
        return self._call("HandleStreamingTab", {**self._meta(), **kw})

    def handle_streaming_terminal_command(self, **kw) -> RpcResponse:
        return self._call("HandleStreamingTerminalCommand", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Memory
    # ═══════════════════════════════════════════════════

    def get_cascade_memories(self) -> RpcResponse:
        return self._call("GetCascadeMemories", self._meta())

    def delete_cascade_memory(self, **kw) -> RpcResponse:
        return self._call("DeleteCascadeMemory", {**self._meta(), **kw})

    def update_cascade_memory(self, **kw) -> RpcResponse:
        return self._call("UpdateCascadeMemory", {**self._meta(), **kw})

    def get_user_memories(self) -> RpcResponse:
        return self._call("GetUserMemories", self._meta())

    # ═══════════════════════════════════════════════════
    #  CodeMap
    # ═══════════════════════════════════════════════════

    def generate_code_map(self, **kw) -> RpcResponse:
        return self._call("GenerateCodeMap", {**self._meta(), **kw})

    def get_code_maps_for_file(self, **kw) -> RpcResponse:
        return self._call("GetCodeMapsForFile", {**self._meta(), **kw})

    def get_code_maps_for_repos(self, **kw) -> RpcResponse:
        return self._call("GetCodeMapsForRepos", {**self._meta(), **kw})

    def get_code_map_suggestions(self) -> RpcResponse:
        return self._call("GetCodeMapSuggestions", self._meta())

    def dismiss_code_map_suggestion(self, **kw) -> RpcResponse:
        return self._call("DismissCodeMapSuggestion", {**self._meta(), **kw})

    def save_code_map_from_json(self, **kw) -> RpcResponse:
        return self._call("SaveCodeMapFromJson", {**self._meta(), **kw})

    def update_code_map_metadata(self, **kw) -> RpcResponse:
        return self._call("UpdateCodeMapMetadata", {**self._meta(), **kw})

    def get_shared_code_map(self, **kw) -> RpcResponse:
        return self._call("GetSharedCodeMap", {**self._meta(), **kw})

    def share_code_map(self, **kw) -> RpcResponse:
        return self._call("ShareCodeMap", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  MCP Plugins
    # ═══════════════════════════════════════════════════

    def get_available_cascade_plugins(self) -> RpcResponse:
        return self._call("GetAvailableCascadePlugins", self._meta())

    def get_cascade_plugin_by_id(self, **kw) -> RpcResponse:
        return self._call("GetCascadePluginById", {**self._meta(), **kw})

    def install_cascade_plugin(self, **kw) -> RpcResponse:
        return self._call("InstallCascadePlugin", {**self._meta(), **kw})

    def get_mcp_server_states(self) -> RpcResponse:
        return self._call("GetMcpServerStates", self._meta())

    def get_mcp_registry_servers(self) -> RpcResponse:
        return self._call("GetMcpRegistryServers", self._meta())

    def get_mcp_prompt(self, **kw) -> RpcResponse:
        return self._call("GetMcpPrompt", {**self._meta(), **kw})

    def refresh_mcp_servers(self) -> RpcResponse:
        return self._call("RefreshMcpServers", self._meta())

    def toggle_mcp_tool(self, **kw) -> RpcResponse:
        return self._call("ToggleMcpTool", {**self._meta(), **kw})

    def save_mcp_server_to_config_file(self, **kw) -> RpcResponse:
        return self._call("SaveMcpServerToConfigFile", {**self._meta(), **kw})

    def update_mcp_server_in_config_file(self, **kw) -> RpcResponse:
        return self._call("UpdateMcpServerInConfigFile", {**self._meta(), **kw})

    def get_all_acp_registries(self) -> RpcResponse:
        return self._call("GetAllAcpRegistries", self._meta())

    # ═══════════════════════════════════════════════════
    #  模型 & 配置
    # ═══════════════════════════════════════════════════

    def get_cascade_model_configs(self) -> RpcResponse:
        return self._call("GetCascadeModelConfigs", self._meta())

    def get_command_model_configs(self) -> RpcResponse:
        return self._call("GetCommandModelConfigs", self._meta())

    def get_model_statuses(self) -> RpcResponse:
        return self._call("GetModelStatuses", self._meta())

    def get_external_model(self, **kw) -> RpcResponse:
        return self._call("GetExternalModel", {**self._meta(), **kw})

    def get_lifeguard_config(self) -> RpcResponse:
        return self._call("GetLifeguardConfig", self._meta())

    def get_all_plans(self) -> RpcResponse:
        return self._call("GetAllPlans", self._meta())

    def get_all_rules(self) -> RpcResponse:
        return self._call("GetAllRules", self._meta())

    def get_all_skills(self) -> RpcResponse:
        return self._call("GetAllSkills", self._meta())

    def get_all_workflows(self) -> RpcResponse:
        return self._call("GetAllWorkflows", self._meta())

    def get_default_web_origins(self) -> RpcResponse:
        return self._call("GetDefaultWebOrigins", self._meta())

    # ═══════════════════════════════════════════════════
    #  状态 & 用户
    # ═══════════════════════════════════════════════════

    def get_user_status(self) -> RpcResponse:
        return self._call("GetUserStatus", self._meta())

    def get_user_settings(self) -> RpcResponse:
        return self._call("GetUserSettings", self._meta())

    def set_user_settings(self, **kw) -> RpcResponse:
        return self._call("SetUserSettings", {**self._meta(), **kw})

    def get_profile_data(self) -> RpcResponse:
        return self._call("GetProfileData", self._meta())

    def get_status(self) -> RpcResponse:
        return self._call("GetStatus", self._meta())

    def get_auth_token(self) -> RpcResponse:
        return self._call("GetAuthToken", self._meta())

    def get_primary_api_key_for_devs(self) -> RpcResponse:
        return self._call("GetPrimaryApiKeyForDevsOnly", self._meta())

    def migrate_api_key(self, **kw) -> RpcResponse:
        return self._call("MigrateApiKey", {**self._meta(), **kw})

    def get_processes(self) -> RpcResponse:
        return self._call("GetProcesses", self._meta())

    def get_brain_status(self) -> RpcResponse:
        return self._call("GetBrainStatus", self._meta())

    def get_changelog(self) -> RpcResponse:
        return self._call("GetChangelog", self._meta())

    def get_debug_diagnostics(self) -> RpcResponse:
        return self._call("GetDebugDiagnostics", self._meta())

    # ═══════════════════════════════════════════════════
    #  Chat
    # ═══════════════════════════════════════════════════

    def check_chat_capacity(self, **kw) -> RpcResponse:
        return self._call("CheckChatCapacity", {**self._meta(), **kw})

    def check_user_message_rate_limit(self, **kw) -> RpcResponse:
        return self._call("CheckUserMessageRateLimit", {**self._meta(), **kw})

    def get_chat_message(self, **kw) -> RpcResponse:
        return self._call("GetChatMessage", {**self._meta(), **kw})

    def raw_get_chat_message(self, **kw) -> RpcResponse:
        return self._call("RawGetChatMessage", {**self._meta(), **kw})

    def get_message_token_count(self, **kw) -> RpcResponse:
        return self._call("GetMessageTokenCount", {**self._meta(), **kw})

    def get_conversation_tags(self, **kw) -> RpcResponse:
        return self._call("GetConversationTags", {**self._meta(), **kw})

    def update_conversation_tags(self, **kw) -> RpcResponse:
        return self._call("UpdateConversationTags", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Workspace & File
    # ═══════════════════════════════════════════════════

    def add_tracked_workspace(self, **kw) -> RpcResponse:
        return self._call("AddTrackedWorkspace", {**self._meta(), **kw})

    def remove_tracked_workspace(self, **kw) -> RpcResponse:
        return self._call("RemoveTrackedWorkspace", {**self._meta(), **kw})

    def get_workspace_infos(self) -> RpcResponse:
        return self._call("GetWorkspaceInfos", self._meta())

    def get_workspace_edit_state(self, **kw) -> RpcResponse:
        return self._call("GetWorkspaceEditState", {**self._meta(), **kw})

    def update_workspace_trust(self, **kw) -> RpcResponse:
        return self._call("UpdateWorkspaceTrust", {**self._meta(), **kw})

    def get_repo_infos(self) -> RpcResponse:
        return self._call("GetRepoInfos", self._meta())

    def get_matching_indexed_repos(self, **kw) -> RpcResponse:
        return self._call("GetMatchingIndexedRepos", {**self._meta(), **kw})

    def stat_uri(self, **kw) -> RpcResponse:
        return self._call("StatUri", {**self._meta(), **kw})

    def on_edit(self, **kw) -> RpcResponse:
        return self._call("OnEdit", {**self._meta(), **kw})

    def cancel_request(self, **kw) -> RpcResponse:
        return self._call("CancelRequest", {**self._meta(), **kw})

    def exit(self) -> RpcResponse:
        return self._call("Exit", self._meta())

    def mount_cascade_filesystem(self, **kw) -> RpcResponse:
        return self._call("MountCascadeFilesystem", {**self._meta(), **kw})

    def unmount_cascade_filesystem(self, **kw) -> RpcResponse:
        return self._call("UnmountCascadeFilesystem", {**self._meta(), **kw})

    def create_worktree(self, **kw) -> RpcResponse:
        return self._call("CreateWorktree", {**self._meta(), **kw})

    def resolve_worktree_changes(self, **kw) -> RpcResponse:
        return self._call("ResolveWorktreeChanges", {**self._meta(), **kw})

    def undo_worktree_merge(self, **kw) -> RpcResponse:
        return self._call("UndoWorktreeMerge", {**self._meta(), **kw})

    def get_active_app_deployment_for_workspace(self, **kw) -> RpcResponse:
        return self._call("GetActiveAppDeploymentForWorkspace", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Code Completion / Generation
    # ═══════════════════════════════════════════════════

    def provide_completion_feedback(self, **kw) -> RpcResponse:
        return self._call("ProvideCompletionFeedback", {**self._meta(), **kw})

    def generate_commit_message(self, **kw) -> RpcResponse:
        return self._call("GenerateCommitMessage", {**self._meta(), **kw})

    def generate_vibe_and_replace_streaming(self, **kw) -> RpcResponse:
        return self._call("GenerateVibeAndReplaceStreaming", {**self._meta(), **kw})

    def capture_code(self, **kw) -> RpcResponse:
        return self._call("CaptureCode", {**self._meta(), **kw})

    def capture_file(self, **kw) -> RpcResponse:
        return self._call("CaptureFile", {**self._meta(), **kw})

    def check_bugs(self, **kw) -> RpcResponse:
        return self._call("CheckBugs", {**self._meta(), **kw})

    def submit_bug_report(self, **kw) -> RpcResponse:
        return self._call("SubmitBugReport", {**self._meta(), **kw})

    def get_class_infos(self, **kw) -> RpcResponse:
        return self._call("GetClassInfos", {**self._meta(), **kw})

    def get_functions(self, **kw) -> RpcResponse:
        return self._call("GetFunctions", {**self._meta(), **kw})

    def get_code_validation_states(self, **kw) -> RpcResponse:
        return self._call("GetCodeValidationStates", {**self._meta(), **kw})

    def get_matching_code_context(self, **kw) -> RpcResponse:
        return self._call("GetMatchingCodeContext", {**self._meta(), **kw})

    def get_matching_context_scope_items(self, **kw) -> RpcResponse:
        return self._call("GetMatchingContextScopeItems", {**self._meta(), **kw})

    def get_suggested_context_scope_items(self, **kw) -> RpcResponse:
        return self._call("GetSuggestedContextScopeItems", {**self._meta(), **kw})

    def get_system_prompt_and_tools(self, **kw) -> RpcResponse:
        return self._call("GetSystemPromptAndTools", {**self._meta(), **kw})

    def run_code_alignment(self, **kw) -> RpcResponse:
        return self._call("RunCodeAlignment", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Context & Pinning
    # ═══════════════════════════════════════════════════

    def set_pinned_context(self, **kw) -> RpcResponse:
        return self._call("SetPinnedContext", {**self._meta(), **kw})

    def set_pinned_guideline(self, **kw) -> RpcResponse:
        return self._call("SetPinnedGuideline", {**self._meta(), **kw})

    def refresh_context_for_ide_action(self, **kw) -> RpcResponse:
        return self._call("RefreshContextForIdeAction", {**self._meta(), **kw})

    def force_background_research_refresh(self, **kw) -> RpcResponse:
        return self._call("ForceBackgroundResearchRefresh", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Customization & Config
    # ═══════════════════════════════════════════════════

    def create_customization_file(self, **kw) -> RpcResponse:
        return self._call("CreateCustomizationFile", {**self._meta(), **kw})

    def refresh_customization(self) -> RpcResponse:
        return self._call("RefreshCustomization", self._meta())

    def edit_configuration(self, **kw) -> RpcResponse:
        return self._call("EditConfiguration", {**self._meta(), **kw})

    def copy_builtin_workflow_to_workspace(self, **kw) -> RpcResponse:
        return self._call("CopyBuiltinWorkflowToWorkspace", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Unleash & Experiments
    # ═══════════════════════════════════════════════════

    def get_unleash_data(self) -> RpcResponse:
        return self._call("GetUnleashData", self._meta())

    def should_enable_unleash(self, **kw) -> RpcResponse:
        return self._call("ShouldEnableUnleash", {**self._meta(), **kw})

    def update_dev_experiments(self, **kw) -> RpcResponse:
        return self._call("UpdateDevExperiments", {**self._meta(), **kw})

    def update_enterprise_experiments_from_url(self, **kw) -> RpcResponse:
        return self._call("UpdateEnterpriseExperimentsFromUrl", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Record / Telemetry
    # ═══════════════════════════════════════════════════

    def record_event(self, **kw) -> RpcResponse:
        return self._call("RecordEvent", {**self._meta(), **kw})

    def record_lints(self, **kw) -> RpcResponse:
        return self._call("RecordLints", {**self._meta(), **kw})

    def record_chat_feedback(self, **kw) -> RpcResponse:
        return self._call("RecordChatFeedback", {**self._meta(), **kw})

    def record_chat_panel_session(self, **kw) -> RpcResponse:
        return self._call("RecordChatPanelSession", {**self._meta(), **kw})

    def record_commit_message_save(self, **kw) -> RpcResponse:
        return self._call("RecordCommitMessageSave", {**self._meta(), **kw})

    def record_search_doc_open(self, **kw) -> RpcResponse:
        return self._call("RecordSearchDocOpen", {**self._meta(), **kw})

    def record_search_results_view(self, **kw) -> RpcResponse:
        return self._call("RecordSearchResultsView", {**self._meta(), **kw})

    def record_system_metrics(self, **kw) -> RpcResponse:
        return self._call("RecordSystemMetrics", {**self._meta(), **kw})

    def record_user_grep(self, **kw) -> RpcResponse:
        return self._call("RecordUserGrep", {**self._meta(), **kw})

    def record_user_step_snapshot(self, **kw) -> RpcResponse:
        return self._call("RecordUserStepSnapshot", {**self._meta(), **kw})

    def log_cascade_session(self, **kw) -> RpcResponse:
        return self._call("LogCascadeSession", {**self._meta(), **kw})

    def upload_recent_commands(self, **kw) -> RpcResponse:
        return self._call("UploadRecentCommands", {**self._meta(), **kw})

    def progress_bars(self, **kw) -> RpcResponse:
        return self._call("ProgressBars", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  杂项
    # ═══════════════════════════════════════════════════

    def get_deep_wiki(self, **kw) -> RpcResponse:
        return self._call("GetDeepWiki", {**self._meta(), **kw})

    def get_transcription(self, **kw) -> RpcResponse:
        return self._call("GetTranscription", {**self._meta(), **kw})

    def get_web_docs_options(self) -> RpcResponse:
        return self._call("GetWebDocsOptions", self._meta())

    def get_windsurf(self, **kw) -> RpcResponse:
        return self._call("GetWindsurf", {**self._meta(), **kw})

    def save_windsurf(self, **kw) -> RpcResponse:
        return self._call("SaveWindsurf", {**self._meta(), **kw})

    def validate_windsurf(self, **kw) -> RpcResponse:
        return self._call("ValidateWindsurf", {**self._meta(), **kw})

    def get_team_organizational_controls(self) -> RpcResponse:
        return self._call("GetTeamOrganizationalControls", self._meta())

    def get_knowledge_base_items_for_team(self, **kw) -> RpcResponse:
        return self._call("GetKnowledgeBaseItemsForTeam", {**self._meta(), **kw})

    def get_github_pull_request_search_info(self, **kw) -> RpcResponse:
        return self._call("GetGithubPullRequestSearchInfo", {**self._meta(), **kw})

    def get_revert_preview(self, **kw) -> RpcResponse:
        return self._call("GetRevertPreview", {**self._meta(), **kw})

    def import_from_cursor(self, **kw) -> RpcResponse:
        return self._call("ImportFromCursor", {**self._meta(), **kw})

    def reset_onboarding(self) -> RpcResponse:
        return self._call("ResetOnboarding", self._meta())

    def skip_onboarding(self) -> RpcResponse:
        return self._call("SkipOnboarding", self._meta())

    def setup_university_sandbox(self, **kw) -> RpcResponse:
        return self._call("SetupUniversitySandbox", {**self._meta(), **kw})

    def update_auto_cascade_github_credentials(self, **kw) -> RpcResponse:
        return self._call("UpdateAutoCascadeGithubCredentials", {**self._meta(), **kw})

    def well_supported_languages(self) -> RpcResponse:
        return self._call("WellSupportedLanguages", self._meta())

    # ═══════════════════════════════════════════════════
    #  通用
    # ═══════════════════════════════════════════════════

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        """调用任意 LS 方法"""
        return self._call(method, payload, **kw)

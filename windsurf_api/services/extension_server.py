"""ExtensionServerService — 50 RPC methods

扩展服务: IDE 交互、终端、文件操作、代码编辑、音频录制等。
逆向自 exa.extension_server_pb.ExtensionServerService

注意: 此服务运行在本地 Extension 端口, 需要 CSRF token。
"""
from ..transport import ConnectTransport, RpcResponse
from ..models import metadata


SERVICE = "exa.extension_server_pb.ExtensionServerService"


class ExtensionServerService:
    """ExtensionServer 完整封装 (50 methods)"""

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    # ═══════════════════════════════════════════════════
    #  注解 & 标记
    # ═══════════════════════════════════════════════════

    def add_annotation(self, **kw) -> RpcResponse:
        return self._call("AddAnnotation", {**self._meta(), **kw})

    def remove_annotation(self, **kw) -> RpcResponse:
        return self._call("RemoveAnnotation", {**self._meta(), **kw})

    def show_annotation(self, **kw) -> RpcResponse:
        return self._call("ShowAnnotation", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  代码编辑
    # ═══════════════════════════════════════════════════

    def write_cascade_edit(self, **kw) -> RpcResponse:
        return self._call("WriteCascadeEdit", {**self._meta(), **kw})

    def insert_code_at_cursor(self, **kw) -> RpcResponse:
        return self._call("InsertCodeAtCursor", {**self._meta(), **kw})

    def cancel_vibe_and_replace(self, **kw) -> RpcResponse:
        return self._call("CancelVibeAndReplace", {**self._meta(), **kw})

    def unmount_changes(self, **kw) -> RpcResponse:
        return self._call("UnmountChanges", {**self._meta(), **kw})

    def save_document(self, **kw) -> RpcResponse:
        return self._call("SaveDocument", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  文件 & Diff
    # ═══════════════════════════════════════════════════

    def open_file_pointer(self, **kw) -> RpcResponse:
        return self._call("OpenFilePointer", {**self._meta(), **kw})

    def open_virtual_file(self, **kw) -> RpcResponse:
        return self._call("OpenVirtualFile", {**self._meta(), **kw})

    def open_diff_zones(self, **kw) -> RpcResponse:
        return self._call("OpenDiffZones", {**self._meta(), **kw})

    def open_multi_diff(self, **kw) -> RpcResponse:
        return self._call("OpenMultiDiff", {**self._meta(), **kw})

    def find_all_references(self, **kw) -> RpcResponse:
        return self._call("FindAllReferences", {**self._meta(), **kw})

    def search_query(self, **kw) -> RpcResponse:
        return self._call("SearchQuery", {**self._meta(), **kw})

    def load_code_map(self, **kw) -> RpcResponse:
        return self._call("LoadCodeMap", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  终端
    # ═══════════════════════════════════════════════════

    def open_terminal(self, **kw) -> RpcResponse:
        return self._call("OpenTerminal", {**self._meta(), **kw})

    def show_terminal(self, **kw) -> RpcResponse:
        return self._call("ShowTerminal", {**self._meta(), **kw})

    def read_terminal(self, **kw) -> RpcResponse:
        return self._call("ReadTerminal", {**self._meta(), **kw})

    def check_terminal_shell_support(self, **kw) -> RpcResponse:
        return self._call("CheckTerminalShellSupport", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  音频
    # ═══════════════════════════════════════════════════

    def start_audio_recording(self, **kw) -> RpcResponse:
        return self._call("StartAudioRecording", {**self._meta(), **kw})

    def end_audio_recording(self, **kw) -> RpcResponse:
        return self._call("EndAudioRecording", {**self._meta(), **kw})

    def get_current_audio_recording(self, **kw) -> RpcResponse:
        return self._call("GetCurrentAudioRecording", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Lints
    # ═══════════════════════════════════════════════════

    def get_lint_errors(self, **kw) -> RpcResponse:
        return self._call("GetLintErrors", {**self._meta(), **kw})

    def get_lints_for_acknowledger(self, **kw) -> RpcResponse:
        return self._call("GetLintsForAcknowledger", {**self._meta(), **kw})

    def watch_for_lints(self, **kw) -> RpcResponse:
        return self._call("WatchForLints", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Native Values (键值存储)
    # ═══════════════════════════════════════════════════

    def get_native_values(self, **kw) -> RpcResponse:
        return self._call("GetNativeValues", {**self._meta(), **kw})

    def set_native_value(self, **kw) -> RpcResponse:
        return self._call("SetNativeValue", {**self._meta(), **kw})

    def clear_native_value(self, **kw) -> RpcResponse:
        return self._call("ClearNativeValue", {**self._meta(), **kw})

    def subscribe_native_values(self, **kw) -> RpcResponse:
        return self._call("SubscribeNativeValues", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  Secrets
    # ═══════════════════════════════════════════════════

    def get_secret_value(self, **kw) -> RpcResponse:
        return self._call("GetSecretValue", {**self._meta(), **kw})

    def store_secret_value(self, **kw) -> RpcResponse:
        return self._call("StoreSecretValue", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  实验
    # ═══════════════════════════════════════════════════

    def check_experiment(self, **kw) -> RpcResponse:
        return self._call("CheckExperiment", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  设置 & 导航
    # ═══════════════════════════════════════════════════

    def open_setting(self, **kw) -> RpcResponse:
        return self._call("OpenSetting", {**self._meta(), **kw})

    def open_external_url(self, url: str = "", **kw) -> RpcResponse:
        return self._call("OpenExternalUrl", {**self._meta(), "url": url, **kw})

    def get_redirect_uri(self, **kw) -> RpcResponse:
        return self._call("GetRedirectUri", {**self._meta(), **kw})

    def open_windsurf_rules_file(self, **kw) -> RpcResponse:
        return self._call("OpenWindsurfRulesFile", {**self._meta(), **kw})

    def delete_windsurf_rules_file(self, **kw) -> RpcResponse:
        return self._call("DeleteWindsurfRulesFile", {**self._meta(), **kw})

    def delete_windsurf_workflow(self, **kw) -> RpcResponse:
        return self._call("DeleteWindsurfWorkflow", {**self._meta(), **kw})

    def open_configure_plugins_page(self, **kw) -> RpcResponse:
        return self._call("OpenConfigurePluginsPage", {**self._meta(), **kw})

    def open_conversation_workspace_quick_pick(self, **kw) -> RpcResponse:
        return self._call("OpenConversationWorkspaceQuickPick", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  杂项
    # ═══════════════════════════════════════════════════

    def execute_command(self, **kw) -> RpcResponse:
        return self._call("ExecuteCommand", {**self._meta(), **kw})

    def language_server_started(self, **kw) -> RpcResponse:
        return self._call("LanguageServerStarted", {**self._meta(), **kw})

    def log_event(self, **kw) -> RpcResponse:
        return self._call("LogEvent", {**self._meta(), **kw})

    def logout_windsurf(self, **kw) -> RpcResponse:
        return self._call("LogoutWindsurf", {**self._meta(), **kw})

    def handle_async_post_message(self, **kw) -> RpcResponse:
        return self._call("HandleAsyncPostMessage", {**self._meta(), **kw})

    def notify_mcp_state_changed(self, **kw) -> RpcResponse:
        return self._call("NotifyMcpStateChanged", {**self._meta(), **kw})

    def refresh(self, **kw) -> RpcResponse:
        return self._call("Refresh", {**self._meta(), **kw})

    def update_cascade_trajectory_summaries(self, **kw) -> RpcResponse:
        return self._call("UpdateCascadeTrajectorySummaries", {**self._meta(), **kw})

    # ═══════════════════════════════════════════════════
    #  通用
    # ═══════════════════════════════════════════════════

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        """调用任意 ExtensionServer 方法"""
        return self._call(method, payload, **kw)

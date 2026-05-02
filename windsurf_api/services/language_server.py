"""LanguageServerService — 172 RPC methods (本地)

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

    @staticmethod
    def find_process() -> dict:
        """查找 LS 进程 (Windows)"""
        try:
            r = subprocess.run(
                ['powershell', '-Command',
                 'Get-Process language_server_windows_x64 -EA SilentlyContinue '
                 '| Select Id,@{N="Cmd";E={(Get-CimInstance Win32_Process -Filter '
                 '"ProcessId=$($_.Id)").CommandLine}} | ConvertTo-Json'],
                capture_output=True, text=True, timeout=10)
            if not r.stdout.strip(): return None
            data = json.loads(r.stdout)
            if isinstance(data, dict): data = [data]
            for proc in data:
                pid = proc.get('Id')
                cmd = proc.get('Cmd', '')
                port_m = re.search(r'--port[=\s]+(\d+)', cmd)
                port = int(port_m.group(1)) if port_m else None
                if pid: return {'pid': pid, 'port': port, 'cmdline': cmd}
        except Exception: pass
        return None

    @staticmethod
    def find_port() -> int:
        """通过 Heartbeat 探测 LS 端口"""
        proc = LanguageServerService.find_process()
        if proc and proc.get('port'): return proc['port']
        t = ConnectTransport("http://127.0.0.1:0", timeout=2)
        for port in range(49152, 49250):
            t.base_url = f"http://127.0.0.1:{port}"
            r = t.call(SERVICE, "Heartbeat", {"metadata": {}})
            if r.status != 0: return port
        return 0

    @staticmethod
    def read_csrf_from_process(pid: int) -> str:
        """从 LS 命令行读 CSRF token"""
        try:
            r = subprocess.run(
                ['powershell', '-Command',
                 f'(Get-CimInstance Win32_Process -Filter "ProcessId={pid}").CommandLine'],
                capture_output=True, text=True, timeout=5)
            m = re.search(r'WINDSURF_CSRF_TOKEN[=]([^\s\"]+)', r.stdout)
            return m.group(1) if m else ''
        except Exception: return ''

    def auto_connect(self) -> bool:
        """自动发现 LS 并连接"""
        proc = self.find_process()
        if not proc: return False
        self.port = proc.get('port') or self.find_port()
        if proc.get('pid'):
            self.csrf_token = self.read_csrf_from_process(proc['pid'])
        self._transport = None
        return bool(self.port)

    def set_base_experiments(self, disable: list = None, enable: list = None) -> RpcResponse:
        """注入实验 flags"""
        return self._call("SetBaseExperiments", {
            "forceDisableExperiments": [int(x) for x in (disable or self.FORCE_DISABLE)],
            "forceEnableExperiments": [int(x) for x in (enable or self.FORCE_ENABLE)],
        })

    def inject_pro_experiments(self) -> RpcResponse:
        """一键注入全部 Pro 实验"""
        return self.set_base_experiments()

    # ── 补全 ──

    def accept_completion(self, *, completionId: str = "", **kw) -> RpcResponse:
        """接受代码补全

        Args:
            completionId: 补全 ID
        """
        return self._call("AcceptCompletion", {**self._meta(), "completionId": completionId, **kw})

    def cancel_request(self, *, requestId: str = "", **kw) -> RpcResponse:
        """取消请求

        Args:
            requestId: 请求 ID
        """
        return self._call("CancelRequest", {**self._meta(), "requestId": requestId, **kw})

    def get_completions(self, *, document: dict = None, **kw) -> RpcResponse:
        """获取代码补全

        Args:
            document: 文档信息 {uri, languageId, content, cursorOffset}
        """
        return self._call("GetCompletions", {**self._meta(), "document": document or {}, **kw})

    def provide_completion_feedback(self, *, completionId: str = "",
                                    accepted: bool = False, **kw) -> RpcResponse:
        """提供补全反馈

        Args:
            completionId: 补全 ID
            accepted: 是否接受
        """
        return self._call("ProvideCompletionFeedback", {
            **self._meta(), "completionId": completionId, "accepted": accepted, **kw})

    # ── Cascade 对话 ──

    def start_cascade(self, *, message: str = "", trajectoryId: str = "", **kw) -> RpcResponse:
        """启动 Cascade 对话

        Args:
            message: 用户消息
            trajectoryId: 对话轨迹 ID (留空则新建)
        """
        return self._call("StartCascade", {
            **self._meta(), "message": message, "trajectoryId": trajectoryId, **kw})

    def send_user_cascade_message(self, *, message: str = "",
                                  trajectoryId: str = "", **kw) -> RpcResponse:
        """发送 Cascade 用户消息

        Args:
            message: 用户消息
            trajectoryId: 对话轨迹 ID
        """
        return self._call("SendUserCascadeMessage", {
            **self._meta(), "message": message, "trajectoryId": trajectoryId, **kw})

    def queue_cascade_message(self, *, message: str = "", trajectoryId: str = "", **kw) -> RpcResponse:
        """将消息加入 Cascade 队列

        Args:
            message: 消息内容
            trajectoryId: 轨迹 ID
        """
        return self._call("QueueCascadeMessage", {
            **self._meta(), "message": message, "trajectoryId": trajectoryId, **kw})

    def move_queued_message(self, *, messageId: str = "", **kw) -> RpcResponse:
        """移动队列中的消息

        Args:
            messageId: 消息 ID
        """
        return self._call("MoveQueuedMessage", {**self._meta(), "messageId": messageId, **kw})

    def remove_from_queue(self, *, messageId: str = "", **kw) -> RpcResponse:
        """从队列移除消息

        Args:
            messageId: 消息 ID
        """
        return self._call("RemoveFromQueue", {**self._meta(), "messageId": messageId, **kw})

    def interrupt_with_queued_message(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """用队列消息中断当前 Cascade

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("InterruptWithQueuedMessage", {
            **self._meta(), "trajectoryId": trajectoryId, **kw})

    def cancel_cascade_invocation(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """取消 Cascade 调用

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("CancelCascadeInvocation", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def cancel_cascade_invocation_and_wait(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """取消 Cascade 调用并等待完成

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("CancelCascadeInvocationAndWait", {
            **self._meta(), "trajectoryId": trajectoryId, **kw})

    def cancel_cascade_steps(self, *, trajectoryId: str = "", stepIds: list = None, **kw) -> RpcResponse:
        """取消 Cascade 指定步骤

        Args:
            trajectoryId: 轨迹 ID
            stepIds: 步骤 ID 列表
        """
        return self._call("CancelCascadeSteps", {
            **self._meta(), "trajectoryId": trajectoryId, "stepIds": stepIds or [], **kw})

    def branch_cascade(self, *, trajectoryId: str = "", stepId: str = "", **kw) -> RpcResponse:
        """分支 Cascade 对话

        Args:
            trajectoryId: 轨迹 ID
            stepId: 分支起点步骤 ID
        """
        return self._call("BranchCascade", {
            **self._meta(), "trajectoryId": trajectoryId, "stepId": stepId, **kw})

    def branch_cascade_and_generate_code_map(self, *, trajectoryId: str = "",
                                             stepId: str = "", **kw) -> RpcResponse:
        """分支 Cascade 并生成 Code Map

        Args:
            trajectoryId: 轨迹 ID
            stepId: 分支起点步骤 ID
        """
        return self._call("BranchCascadeAndGenerateCodeMap", {
            **self._meta(), "trajectoryId": trajectoryId, "stepId": stepId, **kw})

    def converge_arena_cascades(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """收敛 Arena 模式 Cascade

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("ConvergeArenaCascades", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def spawn_arena_mode_mid_conversation(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """对话中途生成 Arena 模式

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("SpawnArenaModeMidConversation", {
            **self._meta(), "trajectoryId": trajectoryId, **kw})

    def handle_cascade_user_interaction(self, *, trajectoryId: str = "",
                                        action: str = "", **kw) -> RpcResponse:
        """处理 Cascade 用户交互 (确认/拒绝)

        Args:
            trajectoryId: 轨迹 ID
            action: 交互动作
        """
        return self._call("HandleCascadeUserInteraction", {
            **self._meta(), "trajectoryId": trajectoryId, "action": action, **kw})

    def acknowledge_cascade_code_edit(self, *, trajectoryId: str = "",
                                      stepId: str = "", **kw) -> RpcResponse:
        """确认 Cascade 代码编辑

        Args:
            trajectoryId: 轨迹 ID
            stepId: 步骤 ID
        """
        return self._call("AcknowledgeCascadeCodeEdit", {
            **self._meta(), "trajectoryId": trajectoryId, "stepId": stepId, **kw})

    def resolve_outstanding_steps(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """解决未完成的步骤

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("ResolveOutstandingSteps", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def revert_to_cascade_step(self, *, trajectoryId: str = "", stepId: str = "", **kw) -> RpcResponse:
        """回退到 Cascade 指定步骤

        Args:
            trajectoryId: 轨迹 ID
            stepId: 目标步骤 ID
        """
        return self._call("RevertToCascadeStep", {
            **self._meta(), "trajectoryId": trajectoryId, "stepId": stepId, **kw})

    def get_revert_preview(self, *, trajectoryId: str = "", stepId: str = "", **kw) -> RpcResponse:
        """获取回退预览

        Args:
            trajectoryId: 轨迹 ID
            stepId: 目标步骤 ID
        """
        return self._call("GetRevertPreview", {
            **self._meta(), "trajectoryId": trajectoryId, "stepId": stepId, **kw})

    # ── Cascade 轨迹管理 ──

    def get_all_cascade_trajectories(self, **kw) -> RpcResponse:
        """获取所有 Cascade 对话轨迹"""
        return self._call("GetAllCascadeTrajectories", {**self._meta(), **kw})

    def get_cascade_trajectory(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """获取 Cascade 轨迹详情

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("GetCascadeTrajectory", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def get_cascade_trajectory_steps(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """获取轨迹的所有步骤

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("GetCascadeTrajectorySteps", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def get_cascade_trajectory_generator_metadata(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """获取轨迹生成器元数据

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("GetCascadeTrajectoryGeneratorMetadata", {
            **self._meta(), "trajectoryId": trajectoryId, **kw})

    def get_cascade_transcript_for_trajectory_id(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """获取轨迹对话记录

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("GetCascadeTranscriptForTrajectoryId", {
            **self._meta(), "trajectoryId": trajectoryId, **kw})

    def archive_cascade_trajectory(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """归档 Cascade 轨迹

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("ArchiveCascadeTrajectory", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def delete_cascade_trajectory(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """删除 Cascade 轨迹

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("DeleteCascadeTrajectory", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def rename_cascade_trajectory(self, *, trajectoryId: str = "", name: str = "", **kw) -> RpcResponse:
        """重命名 Cascade 轨迹

        Args:
            trajectoryId: 轨迹 ID
            name: 新名称
        """
        return self._call("RenameCascadeTrajectory", {
            **self._meta(), "trajectoryId": trajectoryId, "name": name, **kw})

    def create_trajectory_share(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """创建轨迹分享

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("CreateTrajectoryShare", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def replay_ground_truth_trajectory(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """重放 Ground Truth 轨迹

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("ReplayGroundTruthTrajectory", {
            **self._meta(), "trajectoryId": trajectoryId, **kw})

    def get_user_trajectory(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """获取用户轨迹

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("GetUserTrajectory", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def get_user_trajectory_debug(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """获取用户轨迹调试信息

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("GetUserTrajectoryDebug", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def get_user_trajectory_descriptions(self, **kw) -> RpcResponse:
        """获取用户轨迹描述列表"""
        return self._call("GetUserTrajectoryDescriptions", {**self._meta(), **kw})

    def get_conversation_tags(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """获取对话标签

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("GetConversationTags", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def update_conversation_tags(self, *, trajectoryId: str = "", tags: list = None, **kw) -> RpcResponse:
        """更新对话标签

        Args:
            trajectoryId: 轨迹 ID
            tags: 标签列表
        """
        return self._call("UpdateConversationTags", {
            **self._meta(), "trajectoryId": trajectoryId, "tags": tags or [], **kw})

    # ── Cascade 记忆 ──

    def get_cascade_memories(self, **kw) -> RpcResponse:
        """获取 Cascade 记忆列表"""
        return self._call("GetCascadeMemories", {**self._meta(), **kw})

    def get_user_memories(self, **kw) -> RpcResponse:
        """获取用户记忆"""
        return self._call("GetUserMemories", {**self._meta(), **kw})

    def delete_cascade_memory(self, *, memoryId: str = "", **kw) -> RpcResponse:
        """删除 Cascade 记忆

        Args:
            memoryId: 记忆 ID
        """
        return self._call("DeleteCascadeMemory", {**self._meta(), "memoryId": memoryId, **kw})

    def update_cascade_memory(self, *, memoryId: str = "", content: str = "", **kw) -> RpcResponse:
        """更新 Cascade 记忆

        Args:
            memoryId: 记忆 ID
            content: 新内容
        """
        return self._call("UpdateCascadeMemory", {
            **self._meta(), "memoryId": memoryId, "content": content, **kw})

    # ── Cascade 面板 / 状态 ──

    def initialize_cascade_panel_state(self, **kw) -> RpcResponse:
        """初始化 Cascade 面板状态"""
        return self._call("InitializeCascadePanelState", {**self._meta(), **kw})

    def send_action_to_chat_panel(self, *, action: str = "", data: dict = None, **kw) -> RpcResponse:
        """向 Chat 面板发送动作

        Args:
            action: 动作类型
            data: 动作数据
        """
        return self._call("SendActionToChatPanel", {
            **self._meta(), "action": action, "data": data or {}, **kw})

    def update_panel_state_with_user_status(self, **kw) -> RpcResponse:
        """用用户状态更新面板"""
        return self._call("UpdatePanelStateWithUserStatus", {**self._meta(), **kw})

    def progress_bars(self, **kw) -> RpcResponse:
        """获取进度条状态"""
        return self._call("ProgressBars", {**self._meta(), **kw})

    # ── MCP 插件 ──

    def get_available_cascade_plugins(self, **kw) -> RpcResponse:
        """获取可用 Cascade 插件列表"""
        return self._call("GetAvailableCascadePlugins", {**self._meta(), **kw})

    def get_cascade_plugin_by_id(self, *, pluginId: str = "", **kw) -> RpcResponse:
        """按 ID 获取 Cascade 插件

        Args:
            pluginId: 插件 ID
        """
        return self._call("GetCascadePluginById", {**self._meta(), "pluginId": pluginId, **kw})

    def install_cascade_plugin(self, *, pluginId: str = "", **kw) -> RpcResponse:
        """安装 Cascade 插件

        Args:
            pluginId: 插件 ID
        """
        return self._call("InstallCascadePlugin", {**self._meta(), "pluginId": pluginId, **kw})

    def get_mcp_prompt(self, *, serverId: str = "", promptName: str = "", **kw) -> RpcResponse:
        """获取 MCP Prompt

        Args:
            serverId: MCP 服务器 ID
            promptName: Prompt 名称
        """
        return self._call("GetMcpPrompt", {
            **self._meta(), "serverId": serverId, "promptName": promptName, **kw})

    def get_mcp_registry_servers(self, **kw) -> RpcResponse:
        """获取 MCP 注册表服务器列表"""
        return self._call("GetMcpRegistryServers", {**self._meta(), **kw})

    def get_mcp_server_states(self, **kw) -> RpcResponse:
        """获取 MCP 服务器状态"""
        return self._call("GetMcpServerStates", {**self._meta(), **kw})

    def get_all_acp_registries(self, **kw) -> RpcResponse:
        """获取所有 ACP 注册表"""
        return self._call("GetAllAcpRegistries", {**self._meta(), **kw})

    def refresh_mcp_servers(self, **kw) -> RpcResponse:
        """刷新 MCP 服务器"""
        return self._call("RefreshMcpServers", {**self._meta(), **kw})

    def save_mcp_server_to_config_file(self, *, config: dict = None, **kw) -> RpcResponse:
        """保存 MCP 服务器到配置文件

        Args:
            config: 服务器配置
        """
        return self._call("SaveMcpServerToConfigFile", {**self._meta(), "config": config or {}, **kw})

    def update_mcp_server_in_config_file(self, *, serverId: str = "",
                                         config: dict = None, **kw) -> RpcResponse:
        """更新配置文件中的 MCP 服务器

        Args:
            serverId: 服务器 ID
            config: 新配置
        """
        return self._call("UpdateMcpServerInConfigFile", {
            **self._meta(), "serverId": serverId, "config": config or {}, **kw})

    def toggle_mcp_tool(self, *, serverId: str = "", toolName: str = "",
                        enabled: bool = True, **kw) -> RpcResponse:
        """切换 MCP 工具启用状态

        Args:
            serverId: 服务器 ID
            toolName: 工具名称
            enabled: 是否启用
        """
        return self._call("ToggleMcpTool", {
            **self._meta(), "serverId": serverId, "toolName": toolName, "enabled": enabled, **kw})

    # ── Code Map ──

    def generate_code_map(self, *, repoPath: str = "", **kw) -> RpcResponse:
        """生成 Code Map

        Args:
            repoPath: 仓库路径
        """
        return self._call("GenerateCodeMap", {**self._meta(), "repoPath": repoPath, **kw})

    def get_code_map_suggestions(self, **kw) -> RpcResponse:
        """获取 Code Map 建议"""
        return self._call("GetCodeMapSuggestions", {**self._meta(), **kw})

    def dismiss_code_map_suggestion(self, *, suggestionId: str = "", **kw) -> RpcResponse:
        """忽略 Code Map 建议

        Args:
            suggestionId: 建议 ID
        """
        return self._call("DismissCodeMapSuggestion", {**self._meta(), "suggestionId": suggestionId, **kw})

    def get_code_maps_for_file(self, *, filePath: str = "", **kw) -> RpcResponse:
        """获取文件相关的 Code Map

        Args:
            filePath: 文件路径
        """
        return self._call("GetCodeMapsForFile", {**self._meta(), "filePath": filePath, **kw})

    def get_code_maps_for_repos(self, *, repoPaths: list = None, **kw) -> RpcResponse:
        """获取仓库的 Code Map

        Args:
            repoPaths: 仓库路径列表
        """
        return self._call("GetCodeMapsForRepos", {**self._meta(), "repoPaths": repoPaths or [], **kw})

    def get_shared_code_map(self, *, shareId: str = "", **kw) -> RpcResponse:
        """获取共享的 Code Map

        Args:
            shareId: 分享 ID
        """
        return self._call("GetSharedCodeMap", {**self._meta(), "shareId": shareId, **kw})

    def share_code_map(self, *, codeMapId: str = "", **kw) -> RpcResponse:
        """分享 Code Map

        Args:
            codeMapId: Code Map ID
        """
        return self._call("ShareCodeMap", {**self._meta(), "codeMapId": codeMapId, **kw})

    def save_code_map_from_json(self, *, jsonData: str = "", **kw) -> RpcResponse:
        """从 JSON 保存 Code Map

        Args:
            jsonData: JSON 数据
        """
        return self._call("SaveCodeMapFromJson", {**self._meta(), "jsonData": jsonData, **kw})

    def update_code_map_metadata(self, *, codeMapId: str = "", metadata_: dict = None, **kw) -> RpcResponse:
        """更新 Code Map 元数据

        Args:
            codeMapId: Code Map ID
            metadata_: 元数据
        """
        return self._call("UpdateCodeMapMetadata", {
            **self._meta(), "codeMapId": codeMapId, "metadata": metadata_ or {}, **kw})

    # ── 模型 / 配置 ──

    def get_cascade_model_configs(self, **kw) -> RpcResponse:
        """获取 Cascade 模型配置"""
        return self._call("GetCascadeModelConfigs", {**self._meta(), **kw})

    def get_command_model_configs(self, **kw) -> RpcResponse:
        """获取命令模型配置"""
        return self._call("GetCommandModelConfigs", {**self._meta(), **kw})

    def get_external_model(self, *, modelId: str = "", **kw) -> RpcResponse:
        """获取外部模型

        Args:
            modelId: 模型 ID
        """
        return self._call("GetExternalModel", {**self._meta(), "modelId": modelId, **kw})

    def get_model_statuses(self, **kw) -> RpcResponse:
        """获取模型状态"""
        return self._call("GetModelStatuses", {**self._meta(), **kw})

    def get_lifeguard_config(self, **kw) -> RpcResponse:
        """获取 Lifeguard 安全配置"""
        return self._call("GetLifeguardConfig", {**self._meta(), **kw})

    # ── 用户 / 状态 ──

    def get_auth_token(self, **kw) -> RpcResponse:
        """获取当前认证 Token"""
        return self._call("GetAuthToken", {**self._meta(), **kw})

    def get_brain_status(self, **kw) -> RpcResponse:
        """获取 Brain 索引状态"""
        return self._call("GetBrainStatus", {**self._meta(), **kw})

    def get_profile_data(self, **kw) -> RpcResponse:
        """获取用户 Profile 数据"""
        return self._call("GetProfileData", {**self._meta(), **kw})

    def get_status(self, **kw) -> RpcResponse:
        """获取 LS 状态"""
        return self._call("GetStatus", {**self._meta(), **kw})

    def get_user_settings(self, **kw) -> RpcResponse:
        """获取用户设置"""
        return self._call("GetUserSettings", {**self._meta(), **kw})

    def set_user_settings(self, *, settings: dict = None, **kw) -> RpcResponse:
        """设置用户配置

        Args:
            settings: 设置字典
        """
        return self._call("SetUserSettings", {**self._meta(), "settings": settings or {}, **kw})

    def get_user_status(self, **kw) -> RpcResponse:
        """获取用户状态 (订阅/额度等)"""
        return self._call("GetUserStatus", {**self._meta(), **kw})

    def get_team_organizational_controls(self, **kw) -> RpcResponse:
        """获取团队组织管控"""
        return self._call("GetTeamOrganizationalControls", {**self._meta(), **kw})

    def get_primary_api_key_for_devs_only(self, **kw) -> RpcResponse:
        """[Dev Only] 获取主 API Key"""
        return self._call("GetPrimaryApiKeyForDevsOnly", {**self._meta(), **kw})

    def migrate_api_key(self, *, oldKey: str = "", newKey: str = "", **kw) -> RpcResponse:
        """迁移 API Key

        Args:
            oldKey: 旧 Key
            newKey: 新 Key
        """
        return self._call("MigrateApiKey", {**self._meta(), "oldKey": oldKey, "newKey": newKey, **kw})

    # ── 工作区 ──

    def add_tracked_workspace(self, *, workspacePath: str = "", **kw) -> RpcResponse:
        """添加追踪的工作区

        Args:
            workspacePath: 工作区路径
        """
        return self._call("AddTrackedWorkspace", {**self._meta(), "workspacePath": workspacePath, **kw})

    def remove_tracked_workspace(self, *, workspacePath: str = "", **kw) -> RpcResponse:
        """移除追踪的工作区

        Args:
            workspacePath: 工作区路径
        """
        return self._call("RemoveTrackedWorkspace", {**self._meta(), "workspacePath": workspacePath, **kw})

    def get_workspace_infos(self, **kw) -> RpcResponse:
        """获取工作区信息"""
        return self._call("GetWorkspaceInfos", {**self._meta(), **kw})

    def get_workspace_edit_state(self, **kw) -> RpcResponse:
        """获取工作区编辑状态"""
        return self._call("GetWorkspaceEditState", {**self._meta(), **kw})

    def get_repo_infos(self, **kw) -> RpcResponse:
        """获取仓库信息"""
        return self._call("GetRepoInfos", {**self._meta(), **kw})

    def stat_uri(self, *, uri: str = "", **kw) -> RpcResponse:
        """获取 URI 文件状态

        Args:
            uri: 文件 URI
        """
        return self._call("StatUri", {**self._meta(), "uri": uri, **kw})

    # ── Worktree ──

    def create_worktree(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """创建 Worktree

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("CreateWorktree", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def resolve_worktree_changes(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """解决 Worktree 变更

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("ResolveWorktreeChanges", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def undo_worktree_merge(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """撤销 Worktree 合并

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("UndoWorktreeMerge", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    # ── 流式操作 ──

    def handle_streaming_command_injected(self, **kw) -> RpcResponse:
        """处理流式命令注入"""
        return self._call("HandleStreamingCommandInjected", {**self._meta(), **kw})

    def handle_streaming_tab(self, **kw) -> RpcResponse:
        """处理流式 Tab 补全"""
        return self._call("HandleStreamingTab", {**self._meta(), **kw})

    def handle_streaming_tab_v2(self, **kw) -> RpcResponse:
        """处理流式 Tab 补全 V2"""
        return self._call("HandleStreamingTabV2", {**self._meta(), **kw})

    def handle_streaming_terminal_command(self, **kw) -> RpcResponse:
        """处理流式终端命令"""
        return self._call("HandleStreamingTerminalCommand", {**self._meta(), **kw})

    def stream_cascade_panel_reactive_updates(self, **kw) -> RpcResponse:
        """流式接收 Cascade 面板响应式更新"""
        return self._call("StreamCascadePanelReactiveUpdates", {**self._meta(), **kw})

    def stream_cascade_reactive_updates(self, **kw) -> RpcResponse:
        """流式接收 Cascade 响应式更新"""
        return self._call("StreamCascadeReactiveUpdates", {**self._meta(), **kw})

    def stream_cascade_summaries_reactive_updates(self, **kw) -> RpcResponse:
        """流式接收 Cascade 摘要响应式更新"""
        return self._call("StreamCascadeSummariesReactiveUpdates", {**self._meta(), **kw})

    def stream_terminal_shell_command(self, *, command: str = "", **kw) -> RpcResponse:
        """流式执行终端命令

        Args:
            command: Shell 命令
        """
        return self._call("StreamTerminalShellCommand", {**self._meta(), "command": command, **kw})

    def stream_user_trajectory_reactive_updates(self, **kw) -> RpcResponse:
        """流式接收用户轨迹响应式更新"""
        return self._call("StreamUserTrajectoryReactiveUpdates", {**self._meta(), **kw})

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

    def check_bugs(self, **kw) -> RpcResponse:
        """检查 Bug"""
        return self._call("CheckBugs", {**self._meta(), **kw})

    def check_chat_capacity(self, *, modelUid: str = "", **kw) -> RpcResponse:
        """检查聊天容量

        Args:
            modelUid: 模型 UID
        """
        return self._call("CheckChatCapacity", {**self._meta(), "modelUid": modelUid, **kw})

    def check_user_message_rate_limit(self, *, modelUid: str = "", **kw) -> RpcResponse:
        """检查用户消息速率限制

        Args:
            modelUid: 模型 UID
        """
        return self._call("CheckUserMessageRateLimit", {**self._meta(), "modelUid": modelUid, **kw})

    def edit_configuration(self, *, key: str = "", value: str = "", **kw) -> RpcResponse:
        """编辑配置

        Args:
            key: 配置键
            value: 配置值
        """
        return self._call("EditConfiguration", {**self._meta(), "key": key, "value": value, **kw})

    def exit(self, **kw) -> RpcResponse:
        """退出 LS 进程"""
        return self._call("Exit", {**self._meta(), **kw})

    def force_background_research_refresh(self, **kw) -> RpcResponse:
        """强制刷新后台研究"""
        return self._call("ForceBackgroundResearchRefresh", {**self._meta(), **kw})

    def generate_commit_message(self, *, diff: str = "", **kw) -> RpcResponse:
        """生成 Commit 消息

        Args:
            diff: Git diff 内容
        """
        return self._call("GenerateCommitMessage", {**self._meta(), "diff": diff, **kw})

    def generate_vibe_and_replace_streaming(self, **kw) -> RpcResponse:
        """生成 Vibe 并流式替换"""
        return self._call("GenerateVibeAndReplaceStreaming", {**self._meta(), **kw})

    def get_active_app_deployment_for_workspace(self, **kw) -> RpcResponse:
        """获取工作区活跃应用部署"""
        return self._call("GetActiveAppDeploymentForWorkspace", {**self._meta(), **kw})

    def get_all_plans(self, **kw) -> RpcResponse:
        """获取所有计划"""
        return self._call("GetAllPlans", {**self._meta(), **kw})

    def get_all_rules(self, **kw) -> RpcResponse:
        """获取所有规则"""
        return self._call("GetAllRules", {**self._meta(), **kw})

    def get_all_skills(self, **kw) -> RpcResponse:
        """获取所有技能"""
        return self._call("GetAllSkills", {**self._meta(), **kw})

    def get_all_workflows(self, **kw) -> RpcResponse:
        """获取所有 Workflow"""
        return self._call("GetAllWorkflows", {**self._meta(), **kw})

    def get_changelog(self, **kw) -> RpcResponse:
        """获取变更日志"""
        return self._call("GetChangelog", {**self._meta(), **kw})

    def get_chat_message(self, *, messageId: str = "", **kw) -> RpcResponse:
        """获取聊天消息

        Args:
            messageId: 消息 ID
        """
        return self._call("GetChatMessage", {**self._meta(), "messageId": messageId, **kw})

    def get_class_infos(self, *, filePath: str = "", **kw) -> RpcResponse:
        """获取类信息

        Args:
            filePath: 文件路径
        """
        return self._call("GetClassInfos", {**self._meta(), "filePath": filePath, **kw})

    def get_code_validation_states(self, **kw) -> RpcResponse:
        """获取代码验证状态"""
        return self._call("GetCodeValidationStates", {**self._meta(), **kw})

    def get_debug_diagnostics(self, **kw) -> RpcResponse:
        """获取调试诊断信息"""
        return self._call("GetDebugDiagnostics", {**self._meta(), **kw})

    def get_deep_wiki(self, *, repoUrl: str = "", **kw) -> RpcResponse:
        """获取 DeepWiki 内容

        Args:
            repoUrl: 仓库 URL
        """
        return self._call("GetDeepWiki", {**self._meta(), "repoUrl": repoUrl, **kw})

    def get_default_web_origins(self, **kw) -> RpcResponse:
        """获取默认 Web Origins"""
        return self._call("GetDefaultWebOrigins", {**self._meta(), **kw})

    def get_functions(self, *, filePath: str = "", **kw) -> RpcResponse:
        """获取函数列表

        Args:
            filePath: 文件路径
        """
        return self._call("GetFunctions", {**self._meta(), "filePath": filePath, **kw})

    def get_github_pull_request_search_info(self, **kw) -> RpcResponse:
        """获取 GitHub PR 搜索信息"""
        return self._call("GetGithubPullRequestSearchInfo", {**self._meta(), **kw})

    def get_knowledge_base_items_for_team(self, **kw) -> RpcResponse:
        """获取团队知识库条目"""
        return self._call("GetKnowledgeBaseItemsForTeam", {**self._meta(), **kw})

    def get_matching_code_context(self, *, query: str = "", **kw) -> RpcResponse:
        """获取匹配的代码上下文

        Args:
            query: 查询文本
        """
        return self._call("GetMatchingCodeContext", {**self._meta(), "query": query, **kw})

    def get_matching_context_scope_items(self, *, query: str = "", **kw) -> RpcResponse:
        """获取匹配的上下文范围项

        Args:
            query: 查询文本
        """
        return self._call("GetMatchingContextScopeItems", {**self._meta(), "query": query, **kw})

    def get_matching_indexed_repos(self, *, query: str = "", **kw) -> RpcResponse:
        """获取匹配的已索引仓库

        Args:
            query: 查询文本
        """
        return self._call("GetMatchingIndexedRepos", {**self._meta(), "query": query, **kw})

    def get_message_token_count(self, *, message: str = "", **kw) -> RpcResponse:
        """获取消息 Token 数量

        Args:
            message: 消息内容
        """
        return self._call("GetMessageTokenCount", {**self._meta(), "message": message, **kw})

    def get_patch_and_code_change(self, *, trajectoryId: str = "", stepId: str = "", **kw) -> RpcResponse:
        """获取 Patch 和代码变更

        Args:
            trajectoryId: 轨迹 ID
            stepId: 步骤 ID
        """
        return self._call("GetPatchAndCodeChange", {
            **self._meta(), "trajectoryId": trajectoryId, "stepId": stepId, **kw})

    def get_processes(self, **kw) -> RpcResponse:
        """获取进程列表"""
        return self._call("GetProcesses", {**self._meta(), **kw})

    def get_suggested_context_scope_items(self, **kw) -> RpcResponse:
        """获取建议的上下文范围项"""
        return self._call("GetSuggestedContextScopeItems", {**self._meta(), **kw})

    def get_system_prompt_and_tools(self, **kw) -> RpcResponse:
        """获取系统 Prompt 和工具列表"""
        return self._call("GetSystemPromptAndTools", {**self._meta(), **kw})

    def get_transcription(self, *, audioData: str = "", **kw) -> RpcResponse:
        """获取音频转录

        Args:
            audioData: 音频数据 (base64)
        """
        return self._call("GetTranscription", {**self._meta(), "audioData": audioData, **kw})

    def get_unleash_data(self, **kw) -> RpcResponse:
        """获取 Unleash 特性开关数据"""
        return self._call("GetUnleashData", {**self._meta(), **kw})

    def get_web_docs_options(self, **kw) -> RpcResponse:
        """获取 Web 文档选项"""
        return self._call("GetWebDocsOptions", {**self._meta(), **kw})

    def get_windsurf_js_app_deployment(self, *, deploymentId: str = "", **kw) -> RpcResponse:
        """获取 Windsurf JS 应用部署

        Args:
            deploymentId: 部署 ID
        """
        return self._call("GetWindsurfJSAppDeployment", {**self._meta(), "deploymentId": deploymentId, **kw})

    def heartbeat(self, **kw) -> RpcResponse:
        """心跳 (保活)"""
        return self._call("Heartbeat", {**self._meta(), **kw})

    def import_from(self, *, source: str = "", **kw) -> RpcResponse:
        """从指定源导入

        Args:
            source: 导入源
        """
        return self._call("ImportFrom", {**self._meta(), "source": source, **kw})

    # ── 遥测记录 ──

    def log_cascade_session(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Cascade 会话日志

        Args:
            data: 会话数据
        """
        return self._call("LogCascadeSession", {**self._meta(), "data": data or {}, **kw})

    def record_chat_feedback(self, *, messageId: str = "", feedback: str = "", **kw) -> RpcResponse:
        """记录聊天反馈

        Args:
            messageId: 消息 ID
            feedback: 反馈 (thumbsUp/thumbsDown)
        """
        return self._call("RecordChatFeedback", {
            **self._meta(), "messageId": messageId, "feedback": feedback, **kw})

    def record_chat_panel_session(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Chat 面板会话

        Args:
            data: 会话数据
        """
        return self._call("RecordChatPanelSession", {**self._meta(), "data": data or {}, **kw})

    def record_commit_message_save(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录 Commit 消息保存

        Args:
            data: 保存数据
        """
        return self._call("RecordCommitMessageSave", {**self._meta(), "data": data or {}, **kw})

    def record_event(self, *, eventType: str = "", data: dict = None, **kw) -> RpcResponse:
        """记录通用事件

        Args:
            eventType: 事件类型
            data: 事件数据
        """
        return self._call("RecordEvent", {**self._meta(), "eventType": eventType, "data": data or {}, **kw})

    def record_lints(self, *, lints: list = None, **kw) -> RpcResponse:
        """记录 Lint 结果

        Args:
            lints: Lint 数据列表
        """
        return self._call("RecordLints", {**self._meta(), "lints": lints or [], **kw})

    def record_search_doc_open(self, *, docId: str = "", **kw) -> RpcResponse:
        """记录搜索文档打开

        Args:
            docId: 文档 ID
        """
        return self._call("RecordSearchDocOpen", {**self._meta(), "docId": docId, **kw})

    def record_search_results_view(self, *, data: dict = None, **kw) -> RpcResponse:
        """记录搜索结果查看

        Args:
            data: 查看数据
        """
        return self._call("RecordSearchResultsView", {**self._meta(), "data": data or {}, **kw})

    def record_system_metrics(self, *, metrics: dict = None, **kw) -> RpcResponse:
        """记录系统指标

        Args:
            metrics: 系统指标数据
        """
        return self._call("RecordSystemMetrics", {**self._meta(), "metrics": metrics or {}, **kw})

    def record_user_grep(self, *, query: str = "", **kw) -> RpcResponse:
        """记录用户 Grep 搜索

        Args:
            query: 搜索关键词
        """
        return self._call("RecordUserGrep", {**self._meta(), "query": query, **kw})

    def record_user_step_snapshot(self, *, trajectoryId: str = "", stepId: str = "", **kw) -> RpcResponse:
        """记录用户步骤快照

        Args:
            trajectoryId: 轨迹 ID
            stepId: 步骤 ID
        """
        return self._call("RecordUserStepSnapshot", {
            **self._meta(), "trajectoryId": trajectoryId, "stepId": stepId, **kw})

    # ── 配置 / Customization ──

    def copy_builtin_workflow_to_workspace(self, *, workflowId: str = "", **kw) -> RpcResponse:
        """复制内置 Workflow 到工作区

        Args:
            workflowId: Workflow ID
        """
        return self._call("CopyBuiltinWorkflowToWorkspace", {
            **self._meta(), "workflowId": workflowId, **kw})

    def create_customization_file(self, *, type_: str = "", **kw) -> RpcResponse:
        """创建自定义文件

        Args:
            type_: 自定义类型
        """
        return self._call("CreateCustomizationFile", {**self._meta(), "type": type_, **kw})

    def refresh_context_for_ide_action(self, *, action: str = "", **kw) -> RpcResponse:
        """刷新 IDE 动作上下文

        Args:
            action: IDE 动作
        """
        return self._call("RefreshContextForIdeAction", {**self._meta(), "action": action, **kw})

    def refresh_customization(self, **kw) -> RpcResponse:
        """刷新自定义配置"""
        return self._call("RefreshCustomization", {**self._meta(), **kw})

    def set_pinned_context(self, *, context: list = None, **kw) -> RpcResponse:
        """设置固定上下文

        Args:
            context: 上下文项列表
        """
        return self._call("SetPinnedContext", {**self._meta(), "context": context or [], **kw})

    def set_pinned_guideline(self, *, guideline: str = "", **kw) -> RpcResponse:
        """设置固定准则

        Args:
            guideline: 准则内容
        """
        return self._call("SetPinnedGuideline", {**self._meta(), "guideline": guideline, **kw})

    def update_dev_experiments(self, *, experiments: dict = None, **kw) -> RpcResponse:
        """更新开发者实验

        Args:
            experiments: 实验配置
        """
        return self._call("UpdateDevExperiments", {**self._meta(), "experiments": experiments or {}, **kw})

    def update_enterprise_experiments_from_url(self, *, url: str = "", **kw) -> RpcResponse:
        """从 URL 更新企业实验

        Args:
            url: 实验配置 URL
        """
        return self._call("UpdateEnterpriseExperimentsFromUrl", {**self._meta(), "url": url, **kw})

    # ── 编辑 / 文件操作 ──

    def on_edit(self, *, uri: str = "", changes: list = None, **kw) -> RpcResponse:
        """通知文件编辑

        Args:
            uri: 文件 URI
            changes: 编辑变更列表
        """
        return self._call("OnEdit", {**self._meta(), "uri": uri, "changes": changes or [], **kw})

    def mount_cascade_filesystem(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """挂载 Cascade 文件系统

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("MountCascadeFilesystem", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def unmount_cascade_filesystem(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """卸载 Cascade 文件系统

        Args:
            trajectoryId: 轨迹 ID
        """
        return self._call("UnmountCascadeFilesystem", {**self._meta(), "trajectoryId": trajectoryId, **kw})

    def raw_get_chat_message(self, *, messageId: str = "", **kw) -> RpcResponse:
        """获取原始聊天消息

        Args:
            messageId: 消息 ID
        """
        return self._call("RawGetChatMessage", {**self._meta(), "messageId": messageId, **kw})

    # ── Onboarding / 杂项 ──

    def reset_onboarding(self, **kw) -> RpcResponse:
        """重置 Onboarding 状态"""
        return self._call("ResetOnboarding", {**self._meta(), **kw})

    def skip_onboarding(self, **kw) -> RpcResponse:
        """跳过 Onboarding"""
        return self._call("SkipOnboarding", {**self._meta(), **kw})

    def setup_university_sandbox(self, **kw) -> RpcResponse:
        """设置大学沙箱环境"""
        return self._call("SetupUniversitySandbox", {**self._meta(), **kw})

    def should_enable_unleash(self, **kw) -> RpcResponse:
        """检查是否应启用 Unleash"""
        return self._call("ShouldEnableUnleash", {**self._meta(), **kw})

    def submit_bug_report(self, *, title: str = "", description: str = "", **kw) -> RpcResponse:
        """提交 Bug 报告

        Args:
            title: 标题
            description: 描述
        """
        return self._call("SubmitBugReport", {
            **self._meta(), "title": title, "description": description, **kw})

    def sync_explore_agent_run(self, *, runId: str = "", **kw) -> RpcResponse:
        """同步 Explore Agent 运行

        Args:
            runId: 运行 ID
        """
        return self._call("SyncExploreAgentRun", {**self._meta(), "runId": runId, **kw})

    def update_auto_cascade_github_credentials(self, *, token: str = "", **kw) -> RpcResponse:
        """更新 Auto-Cascade GitHub 凭证

        Args:
            token: GitHub Token
        """
        return self._call("UpdateAutoCascadeGithubCredentials", {
            **self._meta(), "token": token, **kw})

    def upload_recent_commands(self, *, commands: list = None, **kw) -> RpcResponse:
        """上传最近使用的命令

        Args:
            commands: 命令列表
        """
        return self._call("UploadRecentCommands", {**self._meta(), "commands": commands or [], **kw})

    # ── Windsurf JS 应用 ──

    def save_windsurf_js_app_project_name(self, *, projectName: str = "", **kw) -> RpcResponse:
        """保存 Windsurf JS 应用项目名

        Args:
            projectName: 项目名称
        """
        return self._call("SaveWindsurfJSAppProjectName", {
            **self._meta(), "projectName": projectName, **kw})

    def validate_windsurf_js_app_project_name(self, *, projectName: str = "", **kw) -> RpcResponse:
        """验证 Windsurf JS 应用项目名

        Args:
            projectName: 项目名称
        """
        return self._call("ValidateWindsurfJSAppProjectName", {
            **self._meta(), "projectName": projectName, **kw})

    # ── 语言 ──

    def well_supported_languages(self, **kw) -> RpcResponse:
        """获取良好支持的语言列表"""
        return self._call("WellSupportedLanguages", {**self._meta(), **kw})

    # ── 通用 ──

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        """调用任意 LS 方法"""
        return self._call(method, payload, **kw)

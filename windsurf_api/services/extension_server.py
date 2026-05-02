"""ExtensionServerService — 49 RPC methods

IDE 扩展交互: 编辑器操作、终端、文件、代码注解、音频录制、Lint、搜索等。
逆向自 exa.extension_server_pb.ExtensionServerService
"""
from ..transport import ConnectTransport, RpcResponse
from ..models import metadata


SERVICE = "exa.extension_server_pb.ExtensionServerService"


class ExtensionServerService:
    """IDE 扩展交互服务 — 与 Windsurf 编辑器深度集成"""

    def __init__(self, transport: ConnectTransport, api_key: str = ""):
        self.t = transport
        self.api_key = api_key

    def _call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self.t.call(SERVICE, method, payload or {}, **kw)

    def _meta(self) -> dict:
        return {"metadata": metadata(self.api_key)}

    # ── 代码注解 ──

    def add_annotation(self, *, uri: str = "", range: dict = None,
                       text: str = "", type: str = "", **kw) -> RpcResponse:
        """在编辑器中添加代码注解 (行内提示)

        Args:
            uri: 文件 URI
            range: 注解位置 {"start": {"line": 0, "character": 0}, "end": ...}
            text: 注解文本
            type: 注解类型 (如 "info", "warning")
        """
        return self._call("AddAnnotation", {
            **self._meta(), "uri": uri, "range": range or {}, "text": text, "type": type, **kw})

    def remove_annotation(self, *, annotationId: str = "", **kw) -> RpcResponse:
        """移除代码注解

        Args:
            annotationId: 注解 ID
        """
        return self._call("RemoveAnnotation", {**self._meta(), "annotationId": annotationId, **kw})

    def show_annotation(self, *, annotationId: str = "", **kw) -> RpcResponse:
        """显示/高亮指定注解

        Args:
            annotationId: 注解 ID
        """
        return self._call("ShowAnnotation", {**self._meta(), "annotationId": annotationId, **kw})

    # ── Cascade 对话 ──

    def cancel_vibe_and_replace_trajectory(self, *, trajectoryId: str = "", **kw) -> RpcResponse:
        """取消 Vibe 模式并替换对话轨迹

        Args:
            trajectoryId: 要替换的轨迹 ID
        """
        return self._call("CancelVibeAndReplaceTrajectory", {
            **self._meta(), "trajectoryId": trajectoryId, **kw})

    def update_cascade_trajectory_summaries(self, *, trajectoryIds: list = None, **kw) -> RpcResponse:
        """更新 Cascade 对话轨迹摘要

        Args:
            trajectoryIds: 轨迹 ID 列表
        """
        return self._call("UpdateCascadeTrajectorySummaries", {
            **self._meta(), "trajectoryIds": trajectoryIds or [], **kw})

    def write_cascade_edit(self, *, uri: str = "", edits: list = None, **kw) -> RpcResponse:
        """写入 Cascade 生成的代码编辑

        Args:
            uri: 目标文件 URI
            edits: 编辑操作列表
        """
        return self._call("WriteCascadeEdit", {**self._meta(), "uri": uri, "edits": edits or [], **kw})

    # ── 实验 / 功能检测 ──

    def check_experiment(self, *, experimentKey: str = "", **kw) -> RpcResponse:
        """检查指定实验 (Feature Flag) 是否启用

        Args:
            experimentKey: 实验 Key (如 "cascade_enable_mcp_tools")
        """
        return self._call("CheckExperiment", {**self._meta(), "experimentKey": experimentKey, **kw})

    # ── 终端 ──

    def check_terminal_shell_support(self, *, shellType: str = "", **kw) -> RpcResponse:
        """检查终端 Shell 是否支持指定功能

        Args:
            shellType: Shell 类型 (如 "bash", "powershell")
        """
        return self._call("CheckTerminalShellSupport", {**self._meta(), "shellType": shellType, **kw})

    def open_terminal(self, *, name: str = "", cwd: str = "", command: str = "", **kw) -> RpcResponse:
        """打开 IDE 内置终端

        Args:
            name: 终端名称
            cwd: 工作目录
            command: 初始执行命令
        """
        return self._call("OpenTerminal", {
            **self._meta(), "name": name, "cwd": cwd, "command": command, **kw})

    def show_terminal(self, *, terminalId: str = "", **kw) -> RpcResponse:
        """显示/聚焦指定终端

        Args:
            terminalId: 终端 ID
        """
        return self._call("ShowTerminal", {**self._meta(), "terminalId": terminalId, **kw})

    def read_terminal(self, *, terminalId: str = "", **kw) -> RpcResponse:
        """读取终端当前输出内容

        Args:
            terminalId: 终端 ID
        """
        return self._call("ReadTerminal", {**self._meta(), "terminalId": terminalId, **kw})

    # ── 原生 KV 存储 ──

    def get_native_values(self, *, keys: list = None, **kw) -> RpcResponse:
        """获取 IDE 原生存储的键值对

        Args:
            keys: 要获取的 key 列表
        """
        return self._call("GetNativeValues", {**self._meta(), "keys": keys or [], **kw})

    def set_native_value(self, *, key: str = "", value: str = "", **kw) -> RpcResponse:
        """设置 IDE 原生存储的键值对

        Args:
            key: 存储 key
            value: 存储值
        """
        return self._call("SetNativeValue", {**self._meta(), "key": key, "value": value, **kw})

    def clear_native_value(self, *, key: str = "", **kw) -> RpcResponse:
        """清除 IDE 原生存储的指定 key

        Args:
            key: 要清除的 key
        """
        return self._call("ClearNativeValue", {**self._meta(), "key": key, **kw})

    def subscribe_native_values(self, *, keys: list = None, **kw) -> RpcResponse:
        """订阅原生存储值变更 (流式)

        Args:
            keys: 要订阅的 key 列表
        """
        return self._call("SubscribeNativeValues", {**self._meta(), "keys": keys or [], **kw})

    # ── Secret 存储 ──

    def get_secret_value(self, *, key: str = "", **kw) -> RpcResponse:
        """获取加密存储的 Secret 值

        Args:
            key: Secret key
        """
        return self._call("GetSecretValue", {**self._meta(), "key": key, **kw})

    def store_secret_value(self, *, key: str = "", value: str = "", **kw) -> RpcResponse:
        """存储加密 Secret

        Args:
            key: Secret key
            value: Secret 值
        """
        return self._call("StoreSecretValue", {**self._meta(), "key": key, "value": value, **kw})

    # ── 文件 / 编辑器 ──

    def delete_windsurf_rules_file(self, *, uri: str = "", **kw) -> RpcResponse:
        """删除 Windsurf Rules 文件 (.windsurfrules)

        Args:
            uri: 文件 URI
        """
        return self._call("DeleteWindsurfRulesFile", {**self._meta(), "uri": uri, **kw})

    def delete_windsurf_workflow(self, *, workflowId: str = "", **kw) -> RpcResponse:
        """删除 Windsurf Workflow

        Args:
            workflowId: 工作流 ID
        """
        return self._call("DeleteWindsurfWorkflow", {**self._meta(), "workflowId": workflowId, **kw})

    def open_windsurf_rules_file(self, *, uri: str = "", **kw) -> RpcResponse:
        """在编辑器中打开 Windsurf Rules 文件

        Args:
            uri: 文件 URI
        """
        return self._call("OpenWindsurfRulesFile", {**self._meta(), "uri": uri, **kw})

    def save_document(self, *, uri: str = "", **kw) -> RpcResponse:
        """保存编辑器中的文档

        Args:
            uri: 文件 URI
        """
        return self._call("SaveDocument", {**self._meta(), "uri": uri, **kw})

    def open_file_pointer(self, *, uri: str = "", line: int = 0, character: int = 0, **kw) -> RpcResponse:
        """在编辑器中打开文件并定位到指定位置

        Args:
            uri: 文件 URI
            line: 行号 (0-indexed)
            character: 列号
        """
        return self._call("OpenFilePointer", {
            **self._meta(), "uri": uri, "line": line, "character": character, **kw})

    def open_virtual_file(self, *, uri: str = "", content: str = "", language: str = "", **kw) -> RpcResponse:
        """打开虚拟文件 (内存中, 不存在于磁盘)

        Args:
            uri: 虚拟文件 URI
            content: 文件内容
            language: 语言标识 (如 "python")
        """
        return self._call("OpenVirtualFile", {
            **self._meta(), "uri": uri, "content": content, "language": language, **kw})

    def open_diff_zones(self, *, original: str = "", modified: str = "", **kw) -> RpcResponse:
        """打开 Diff 对比视图 (代码变更区域)

        Args:
            original: 原始内容/URI
            modified: 修改后内容/URI
        """
        return self._call("OpenDiffZones", {**self._meta(), "original": original, "modified": modified, **kw})

    def open_multi_diff(self, *, files: list = None, **kw) -> RpcResponse:
        """打开多文件 Diff 视图

        Args:
            files: 文件对列表 [{original, modified}, ...]
        """
        return self._call("OpenMultiDiff", {**self._meta(), "files": files or [], **kw})

    def unmount_changes(self, *, uri: str = "", **kw) -> RpcResponse:
        """撤销挂载的代码变更

        Args:
            uri: 文件 URI
        """
        return self._call("UnmountChanges", {**self._meta(), "uri": uri, **kw})

    def insert_code_at(self, *, uri: str = "", line: int = 0, code: str = "", **kw) -> RpcResponse:
        """在指定位置插入代码

        Args:
            uri: 文件 URI
            line: 插入行号
            code: 代码内容
        """
        return self._call("InsertCodeAt", {**self._meta(), "uri": uri, "line": line, "code": code, **kw})

    # ── 音频录制 ──

    def start_audio_recording(self, **kw) -> RpcResponse:
        """开始音频录制 (语音输入)"""
        return self._call("StartAudioRecording", {**self._meta(), **kw})

    def end_audio_recording(self, **kw) -> RpcResponse:
        """结束音频录制"""
        return self._call("EndAudioRecording", {**self._meta(), **kw})

    def get_current_audio_recording(self, **kw) -> RpcResponse:
        """获取当前音频录制状态和数据"""
        return self._call("GetCurrentAudioRecording", {**self._meta(), **kw})

    # ── 代码智能 ──

    def get_lsp_completion_items(self, *, uri: str = "", position: dict = None, **kw) -> RpcResponse:
        """获取 LSP 补全项

        Args:
            uri: 文件 URI
            position: 光标位置 {"line": 0, "character": 0}
        """
        return self._call("GetLSPCompletionItems", {
            **self._meta(), "uri": uri, "position": position or {}, **kw})

    def get_lint_errors(self, *, uri: str = "", **kw) -> RpcResponse:
        """获取文件的 Lint 错误列表

        Args:
            uri: 文件 URI
        """
        return self._call("GetLintErrors", {**self._meta(), "uri": uri, **kw})

    def get_lints_for(self, *, uri: str = "", **kw) -> RpcResponse:
        """获取指定文件的 Lint 诊断

        Args:
            uri: 文件 URI
        """
        return self._call("GetLintsFor", {**self._meta(), "uri": uri, **kw})

    def watch_for_lints(self, *, uris: list = None, **kw) -> RpcResponse:
        """监听 Lint 诊断变更 (流式)

        Args:
            uris: 要监听的文件 URI 列表
        """
        return self._call("WatchForLints", {**self._meta(), "uris": uris or [], **kw})

    def find_all_references(self, *, uri: str = "", position: dict = None, **kw) -> RpcResponse:
        """查找符号的所有引用

        Args:
            uri: 文件 URI
            position: 符号位置 {"line": 0, "character": 0}
        """
        return self._call("FindAllReferences", {
            **self._meta(), "uri": uri, "position": position or {}, **kw})

    def load_code_map(self, *, workspacePath: str = "", **kw) -> RpcResponse:
        """加载工作区代码地图 (符号索引)

        Args:
            workspacePath: 工作区路径
        """
        return self._call("LoadCodeMap", {**self._meta(), "workspacePath": workspacePath, **kw})

    # ── 搜索 ──

    def search_query(self, *, query: str = "", includePattern: str = "",
                     maxResults: int = 0, **kw) -> RpcResponse:
        """执行工作区搜索

        Args:
            query: 搜索关键词
            includePattern: 文件匹配模式 (如 "*.py")
            maxResults: 最大结果数
        """
        return self._call("SearchQuery", {
            **self._meta(), "query": query, "includePattern": includePattern,
            "maxResults": maxResults, **kw})

    # ── IDE 控制 ──

    def execute_command(self, *, command: str = "", args: list = None, **kw) -> RpcResponse:
        """执行 VS Code / Windsurf 命令

        Args:
            command: 命令 ID (如 "workbench.action.openSettings")
            args: 命令参数列表
        """
        return self._call("ExecuteCommand", {**self._meta(), "command": command, "args": args or [], **kw})

    def get_redirect_uri(self, *, provider: str = "", **kw) -> RpcResponse:
        """获取 OAuth 重定向 URI

        Args:
            provider: OAuth 提供商 (如 "github")
        """
        return self._call("GetRedirectUri", {**self._meta(), "provider": provider, **kw})

    def handle_async(self, *, requestId: str = "", **kw) -> RpcResponse:
        """处理异步请求结果

        Args:
            requestId: 异步请求 ID
        """
        return self._call("HandleAsync", {**self._meta(), "requestId": requestId, **kw})

    def language_server_started(self, *, port: int = 0, **kw) -> RpcResponse:
        """通知扩展: Language Server 已启动

        Args:
            port: LS 监听端口
        """
        return self._call("LanguageServerStarted", {**self._meta(), "port": port, **kw})

    def log_event(self, *, event: str = "", data: dict = None, **kw) -> RpcResponse:
        """记录事件日志

        Args:
            event: 事件名称
            data: 事件数据
        """
        return self._call("LogEvent", {**self._meta(), "event": event, "data": data or {}, **kw})

    def logout_windsurf(self, **kw) -> RpcResponse:
        """登出 Windsurf 账号"""
        return self._call("LogoutWindsurf", {**self._meta(), **kw})

    def notify_mcp_state_changed(self, *, state: str = "", **kw) -> RpcResponse:
        """通知 MCP 插件状态变更

        Args:
            state: 新状态
        """
        return self._call("NotifyMcpStateChanged", {**self._meta(), "state": state, **kw})

    def open_configure_plugins_page(self, **kw) -> RpcResponse:
        """打开插件配置页面"""
        return self._call("OpenConfigurePluginsPage", {**self._meta(), **kw})

    def open_conversation_workspace_quick_pick(self, **kw) -> RpcResponse:
        """打开对话工作区快速选择菜单"""
        return self._call("OpenConversationWorkspaceQuickPick", {**self._meta(), **kw})

    def open_external_url(self, *, url: str = "", **kw) -> RpcResponse:
        """在系统浏览器中打开外部 URL

        Args:
            url: 目标 URL
        """
        return self._call("OpenExternalUrl", {**self._meta(), "url": url, **kw})

    def open_setting(self, *, settingId: str = "", **kw) -> RpcResponse:
        """打开 IDE 设置页面

        Args:
            settingId: 设置项 ID (如 "editor.fontSize")
        """
        return self._call("OpenSetting", {**self._meta(), "settingId": settingId, **kw})

    def refresh_uris(self, *, uris: list = None, **kw) -> RpcResponse:
        """刷新文件 URI 缓存

        Args:
            uris: 要刷新的 URI 列表
        """
        return self._call("RefreshURIs", {**self._meta(), "uris": uris or [], **kw})

    def call(self, method: str, payload: dict = None, **kw) -> RpcResponse:
        return self._call(method, payload, **kw)

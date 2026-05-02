"""Windsurf API — 全服务调用示例 / All Services Demo

覆盖全部 13 个 gRPC 服务的典型调用方法。
每个服务展示最常用的接口及其参数/响应。

使用前替换 API_KEY。
"""
import json

from windsurf_api import WindsurfClient, TeamsTier, ExperimentKey

API_KEY = "sk-ws-YOUR_KEY_HERE"

def pp(label, r):
    """格式化打印 RpcResponse"""
    if hasattr(r, 'ok'):
        tag = "✓" if r.ok else f"✗[{r.status}]"
        data = json.dumps(r.data, indent=2, ensure_ascii=False, default=str)[:500] if r.data else "{}"
        print(f"  {tag} {label}\n    {data}\n")
    else:
        print(f"  {label}: {r}\n")


# ═══════════════════════════════════════════════════════
#  初始化客户端
# ═══════════════════════════════════════════════════════
ws = WindsurfClient(api_key=API_KEY)


# ═══════════════════════════════════════════════════════
#  1. SeatManagementService (145 methods) — 用户·团队·计费
# ═══════════════════════════════════════════════════════
print("=" * 60)
print("1. SeatManagementService — 用户·团队·计费")
print("=" * 60)

# 1.1 用户状态 (解析为 UserStatus 对象)
status = ws.get_user_status()
print(f"  Email:    {status.email}")
print(f"  Plan:     {status.plan_name} (tier={status.teams_tier})")
print(f"  Credits:  {status.total_credits:,}")
print(f"  Pro:      {status.is_pro}")
print()

# 1.2 用户订阅详情
pp("GetUserSubscription", ws.seat.get_user_subscription())

# 1.3 计划状态
pp("GetPlanStatus", ws.seat.get_plan_status())

# 1.4 Pro 试用资格
pp("CheckProTrialEligibility", ws.seat.check_pro_trial_eligibility())

# 1.5 用量配置
pp("UsageConfig", ws.seat.usage_config())

# 1.6 API Key 摘要
pp("GetApiKeySummary", ws.seat.get_api_key_summary())

# 1.7 个人资料
pp("GetProfileData", ws.seat.get_profile_data())

# 1.8 GitHub 账号状态
pp("GetGitHubAccountStatus", ws.seat.get_github_account_status())

# 1.9 Netlify 账号状态
pp("GetNetlifyAccountStatus", ws.seat.get_netlify_account_status())

# 1.10 团队信息
pp("GetTeamInfo", ws.seat.get_team_info())

# 1.11 团队功能
pp("GetTeamsFeatures", ws.seat.get_teams_features())

# 1.12 检查登录方式
pp("CheckUserLoginMethod", ws.seat.check_user_login_method(email="test@example.com"))

# 1.13 推荐码验证
pp("IsValidReferralCode", ws.seat.is_valid_referral_code(referralCode="ABC123"))

# 1.14 SSO 提供商
pp("GetSSOProviders", ws.seat.get_sso_providers())

# 1.15 许可证
pp("GetLicense", ws.seat.get_license())

# 1.16 团队计费
pp("GetTeamBilling", ws.seat.get_team_billing())

# 1.17 Wrapped 2024
pp("GetWrapped2024", ws.seat.get_wrapped2024())


# ═══════════════════════════════════════════════════════
#  2. ApiServerService (170 methods) — AI模型·聊天·部署
# ═══════════════════════════════════════════════════════
print("=" * 60)
print("2. ApiServerService — AI模型·聊天·部署")
print("=" * 60)

# 2.1 模型提供商 (解析为 ModelProvider 列表)
providers = ws.get_models()
for p in providers:
    print(f"  {p.display_name}: {len(p.models)} models")
print()

# 2.2 Cascade 模型配置
pp("GetCascadeModelConfigs", ws.api_server.get_cascade_model_configs())

# 2.3 模型状态
pp("GetModelStatuses", ws.api_server.get_model_statuses())

# 2.4 聊天容量检查 (返回解析后的 dict)
capacity = ws.api_server.check_chat_capacity("gpt-4")
pp("CheckChatCapacity(gpt-4)", capacity)

# 2.5 速率限制
rate = ws.api_server.check_user_message_rate_limit("gpt-4")
pp("CheckUserMessageRateLimit(gpt-4)", rate)

# 2.6 生命保障配置
pp("GetLifeguardConfig", ws.api_server.get_lifeguard_config())

# 2.7 扩展统计
pp("GetExtensionStats", ws.api_server.get_extension_stats())

# 2.8 OIDC 提供商
pp("GetAllOidcProviders", ws.api_server.get_all_oidc_providers())

# 2.9 混合部署状态
pp("CheckHybridDeploymentStatus", ws.api_server.check_hybrid_deployment_status())

# 2.10 配置
pp("GetConfig", ws.api_server.get_config())

# 2.11 检查邮箱是否有 SSO
pp("CheckEmailForSSO", ws.api_server.check_email_for_sso(email="test@company.com"))

# 2.12 SSO 提供商配置
pp("GetSSOProviders", ws.api_server.get_sso_providers())


# ═══════════════════════════════════════════════════════
#  3. LanguageServerService (172 methods) — 本地LS交互
# ═══════════════════════════════════════════════════════
print("=" * 60)
print("3. LanguageServerService — 本地LS交互")
print("=" * 60)

# 3.1 自动连接本地 LS
connected = ws.ls.auto_connect()
if connected:
    print(f"  ✓ LS 连接成功: port={ws.ls.port}")
    if ws.ls.csrf_token:
        print(f"  ✓ CSRF Token: {ws.ls.csrf_token[:20]}...")
    print()

    # 3.2 心跳
    pp("Heartbeat", ws.ls.heartbeat())

    # 3.3 获取实验配置
    pp("GetExperiments", ws.ls.get_experiments())

    # 3.4 注入 Pro 实验 (一键解锁)
    pp("InjectProExperiments", ws.ls.inject_pro_experiments())

    # 3.5 获取 Cascade 面板状态
    pp("InitializeCascadePanelState", ws.ls.initialize_cascade_panel_state())

    # 3.6 获取工作区信息
    pp("GetWorkspaceInfo", ws.ls.get_workspace_info())

    # 3.7 获取 Cascade 对话轨迹
    pp("GetCascadeTrajectories", ws.ls.get_cascade_trajectories())

    # 3.8 获取 Cascade 用户信息
    pp("GetCascadeUserInfo", ws.ls.get_cascade_user_info())

    # 3.9 代码地图
    pp("GetCodeMap", ws.ls.get_code_map())

    # 3.10 补全
    pp("GetCompletions", ws.ls.get_completions())
else:
    print("  ✗ LS 未连接 (请确保 Windsurf 正在运行)\n")


# ═══════════════════════════════════════════════════════
#  4. ExtensionServerService (49 methods) — IDE扩展交互
# ═══════════════════════════════════════════════════════
print("=" * 60)
print("4. ExtensionServerService — IDE扩展交互")
print("=" * 60)

# ExtensionServer 需要通过 LS 连接
if ws.ls.port:
    ext_t = ws.ls.t  # 复用 LS 的 transport
    from windsurf_api.services.extension_server import ExtensionServerService
    ext = ExtensionServerService(ext_t, ws.api_key)

    # 4.1 检查实验
    pp("CheckExperiment", ext.check_experiment(experimentKey="cascade_enable_mcp_tools"))

    # 4.2 获取原生值
    pp("GetNativeValues", ext.get_native_values())

    # 4.3 日志事件
    pp("LogEvent", ext.log_event(event="sdk_test", data={}))

    # 4.4 执行命令
    pp("ExecuteCommand", ext.execute_command(command="workbench.action.openSettings"))

    # 4.5 搜索
    pp("SearchQuery", ext.search_query(query="hello"))
else:
    print("  (需要 LS 连接)\n")


# ═══════════════════════════════════════════════════════
#  5. CascadePluginsService (5 methods) — MCP插件
# ═══════════════════════════════════════════════════════
print("=" * 60)
print("5. CascadePluginsService — MCP插件")
print("=" * 60)

# 5.1 获取 MCP 客户端信息 (OAuth secrets)
pp("GetMcpClientInfos", ws.plugins.get_mcp_client_infos())

# 5.2 可用插件
pp("GetAvailableCascadePlugins", ws.plugins.get_available_cascade_plugins())

# 5.3 ACP 注册表
pp("GetAllAcpRegistries", ws.plugins.get_all_acp_registries())

# 5.4 按 ID 获取插件
pp("GetCascadePluginById", ws.plugins.get_cascade_plugin_by_id(pluginId="example-id"))


# ═══════════════════════════════════════════════════════
#  6. AnalyticsService (3 methods) — 分析
# ═══════════════════════════════════════════════════════
print("=" * 60)
print("6. AnalyticsService — 分析")
print("=" * 60)

pp("GetCascadeAnalytics", ws.analytics.get_cascade_analytics())
pp("GetLeaderboardStatus", ws.analytics.get_leaderboard_status())
pp("GetGlobalLeaderboard", ws.analytics.get_global_leaderboard())


# ═══════════════════════════════════════════════════════
#  7. UserAnalyticsService (6 methods) — 用户分析
# ═══════════════════════════════════════════════════════
print("=" * 60)
print("7. UserAnalyticsService — 用户分析")
print("=" * 60)

pp("GetBasicUserAnalytics", ws.user_analytics.get_basic_user_analytics())
pp("GetCompleteUserAnalytics", ws.user_analytics.get_complete_user_analytics())
pp("GetPersonalLeaderboard", ws.user_analytics.get_personal_leaderboard())
pp("GetTeamLeaderboard", ws.user_analytics.get_team_leaderboard())


# ═══════════════════════════════════════════════════════
#  8. ProductAnalyticsService (8 methods) — 产品分析
# ═══════════════════════════════════════════════════════
print("=" * 60)
print("8. ProductAnalyticsService — 产品分析")
print("=" * 60)

pp("GetCascadeStats", ws.product_analytics.get_cascade_stats())
pp("GetSessionStats", ws.product_analytics.get_session_stats())
pp("GetGlobalLeaderboardApiKey", ws.product_analytics.get_global_leaderboard_api_key())


# ═══════════════════════════════════════════════════════
#  9-13. 杂项服务 — BrowserPreview, FileSystem, Dev, Auth, Chat
# ═══════════════════════════════════════════════════════
print("=" * 60)
print("9-13. 杂项小服务")
print("=" * 60)

# BrowserPreview (3)
print("  BrowserPreviewService:")
pp("  SendScreenshot", ws.browser_preview.send_screenshot(url="https://example.com", data=""))

# FileSystem (3)
print("  FileSystemProviderService:")
pp("  Stat", ws.filesystem.stat(path="/"))

# Auth (1)
print("  AuthService:")
pp("  GetUserJwt", ws.auth_service.get_user_jwt())

# Dev (1)
print("  DevService:")
pp("  Dev", ws.dev.dev())

# ChatClientServer (1)
print("  ChatClientServerService:")
pp("  StartChatClientRequestStream", ws.chat_client.start_chat_client_request_stream())


# ═══════════════════════════════════════════════════════
#  通用调用 — 直接调用任意 gRPC 方法
# ═══════════════════════════════════════════════════════
print("=" * 60)
print("通用调用 — 任意 gRPC 方法")
print("=" * 60)

# 方式 1: 通过 service 的 call()
pp("seat.call('GetUserStatus')",
   ws.seat.call("GetUserStatus", {"metadata": {"apiKey": API_KEY}}))

# 方式 2: 通过客户端的 call()
pp("ws.call(service, method)",
   ws.call("exa.seat_management_pb.SeatManagementService",
           "GetPlanStatus",
           {"metadata": {"apiKey": API_KEY}}))

print("\n🎉 全部示例执行完毕!")

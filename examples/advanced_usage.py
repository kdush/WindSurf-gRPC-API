"""Windsurf API — 高级用法示例 / Advanced Usage Examples

覆盖: 注册流程、Pro 解锁、团队管理、Internal 方法、流式调用等。
"""
import json
from windsurf_api import WindsurfClient, ExperimentKey
from windsurf_api.auth import oauth_login, email_login, check_providers

API_KEY = "sk-ws-YOUR_KEY_HERE"


def pp(label, r):
    if hasattr(r, 'ok'):
        tag = "✓" if r.ok else f"✗[{r.status}]"
        data = json.dumps(r.data, indent=2, ensure_ascii=False, default=str)[:400]
        print(f"  {tag} {label}\n    {data}\n")
    else:
        print(f"  {label}: {r}\n")


# ═══════════════════════════════════════════════════════
#  示例 1: 完整注册流程 (Firebase → RegisterUser → API Key)
# ═══════════════════════════════════════════════════════
def demo_registration():
    """通过 GitHub OAuth 完成注册"""
    print("=== 完整注册流程 ===")
    ws = WindsurfClient()

    # 步骤 1: Firebase OAuth 登录
    # 需要先在 github.com/settings/tokens 创建 Personal Access Token
    GITHUB_TOKEN = "ghp_YOUR_GITHUB_TOKEN"
    fb = ws.login_github(GITHUB_TOKEN)
    if not fb.ok:
        print(f"  ✗ Firebase 失败: {fb.display_name}")
        return
    print(f"  ✓ Firebase: {fb.email} (id={fb.local_id[:8]}...)")

    # 步骤 2: 注册 Windsurf 用户
    result = ws.register()
    if not result.ok:
        print(f"  ✗ 注册失败: {result.user}")
        return
    print(f"  ✓ API Key: {result.api_key}")

    # 步骤 3: 验证
    status = ws.get_user_status()
    print(f"  ✓ {status.email}, Credits={status.total_credits:,}")
    print()


# ═══════════════════════════════════════════════════════
#  示例 2: Pro 实验注入 (本地 LS)
# ═══════════════════════════════════════════════════════
def demo_pro_injection():
    """一键解锁 Pro 功能 (通过修改本地 LS 实验)"""
    print("=== Pro 实验注入 ===")
    ws = WindsurfClient()

    # 自动发现本地 LS 进程 + CSRF token
    if not ws.ls.auto_connect():
        print("  ✗ 未找到 Windsurf LS 进程，请确保 Windsurf 已启动")
        return

    print(f"  ✓ LS port={ws.ls.port}")

    # 查看当前实验
    r = ws.ls.get_experiments()
    if r.ok:
        exps = r.data.get("experiments", [])
        print(f"  当前实验: {len(exps)} 个")
        for e in exps[:5]:
            print(f"    {e.get('key','?')}: {e.get('value','?')}")

    # 注入 Pro 实验
    r = ws.inject_pro()
    pp("注入结果", r)

    # 自定义实验: 启用指定 key, 禁用指定 key
    r = ws.inject_experiments(
        enable=[ExperimentKey.CASCADE_ENABLE_MCP_TOOLS,
                ExperimentKey.CASCADE_WEB_APP_DEPLOYMENTS_ENABLED],
        disable=[ExperimentKey.CASCADE_ENFORCE_QUOTA]
    )
    pp("自定义实验", r)
    print()


# ═══════════════════════════════════════════════════════
#  示例 3: 团队管理
# ═══════════════════════════════════════════════════════
def demo_team_management():
    """团队创建、成员管理、SSO 配置"""
    print("=== 团队管理 ===")
    ws = WindsurfClient(api_key=API_KEY)

    # 获取团队信息
    pp("GetTeamInfo", ws.seat.get_team_info())

    # 获取团队功能
    pp("GetTeamsFeatures", ws.seat.get_teams_features())

    # 获取团队计费
    pp("GetTeamBilling", ws.seat.get_team_billing())

    # 获取团队成员
    pp("GetTeamMembers", ws.seat.get_team_members())

    # 获取角色列表
    pp("GetRoles", ws.seat.get_roles())

    # 团队分析
    pp("GetTeamAnalytics", ws.seat.get_team_analytics())

    # 获取群组
    pp("GetGroups", ws.seat.get_groups())

    # SSO 配置
    pp("GetSSOProviders", ws.seat.get_sso_providers())

    # 创建团队 (危险操作, 注释掉)
    # pp("CreateTeam", ws.seat.create_multi_tenant_team(teamName="MyTeam"))

    # 邀请成员 (危险操作, 注释掉)
    # pp("InviteTeamMembers", ws.seat.invite_team_members(
    #     emails=["user@example.com"],
    #     roleId="member"
    # ))
    print()


# ═══════════════════════════════════════════════════════
#  示例 4: Internal 方法 (需要 secret)
# ═══════════════════════════════════════════════════════
def demo_internal_methods():
    """Internal 管理方法 — 需要服务端 secret"""
    print("=== Internal 方法 ===")
    ws = WindsurfClient(api_key=API_KEY)
    SECRET = "YOUR_INTERNAL_SECRET"

    # 升级计划
    pp("UpdatePlanDetailsInternal", ws.seat.update_plan_details_internal(
        secret=SECRET,
        email="user@example.com",
        teamsTier=2,  # Pro
        hasPaidFeatures=True,
    ))

    # 添加额度
    pp("AddExtraFlexCreditsInternal", ws.seat.add_extra_flex_credits_internal(
        secret=SECRET,
        email="user@example.com",
        credits=10000,
    ))

    # 重置配额
    pp("ResetQuotaUsageInternal", ws.seat.reset_quota_usage_internal(
        secret=SECRET,
        email="user@example.com",
    ))

    # 使 Devin 缓存失效
    pp("InvalidateDevinCaches", ws.seat.invalidate_devin_caches(secret=SECRET))

    # 获取 Devin Session Token
    pp("GetSelfDevinSessionToken", ws.seat.get_self_devin_session_token())
    print()


# ═══════════════════════════════════════════════════════
#  示例 5: AI 模型与聊天
# ═══════════════════════════════════════════════════════
def demo_ai_chat():
    """AI 模型配置与聊天容量检查"""
    print("=== AI 模型与聊天 ===")
    ws = WindsurfClient(api_key=API_KEY)

    # 所有模型提供商
    providers = ws.get_models()
    for p in providers:
        print(f"  [{p.name}] {p.display_name}")
        for m in p.models[:3]:
            if isinstance(m, dict):
                uid = m.get("modelUid", m.get("name", "?"))
                display = m.get("displayName", uid)
                print(f"    {uid}: {display}")
        if len(p.models) > 3:
            print(f"    ... +{len(p.models)-3} more")
    print()

    # Cascade 模型配置
    pp("GetCascadeModelConfigs", ws.api_server.get_cascade_model_configs())

    # 模型状态 (哪些在线)
    pp("GetModelStatuses", ws.api_server.get_model_statuses())

    # 聊天容量 (每个模型单独检查)
    for model_uid in ["gpt-4", "claude-3.5-sonnet", "gemini-pro"]:
        r = ws.api_server.check_chat_capacity(model_uid)
        has = r.get("hasCapacity", "?") if r.ok else r.status
        print(f"  {model_uid}: capacity={has}")

    # 速率限制
    r = ws.check_rate_limit()
    pp("RateLimit", r)
    print()


# ═══════════════════════════════════════════════════════
#  示例 6: MCP 插件系统
# ═══════════════════════════════════════════════════════
def demo_mcp_plugins():
    """MCP 插件管理"""
    print("=== MCP 插件 ===")
    ws = WindsurfClient(api_key=API_KEY)

    # 获取 MCP 客户端信息 (包含 OAuth secrets)
    r = ws.plugins.get_mcp_client_infos()
    if r.ok:
        infos = r.data.get("clientInfos", []) if isinstance(r.data, dict) else []
        print(f"  MCP Clients: {len(infos)} 个")
        for info in infos[:5]:
            if isinstance(info, dict):
                print(f"    - {info.get('name', '?')}: {info.get('clientId', '?')[:20]}...")
    print()

    # 可用插件列表
    r = ws.plugins.get_available_cascade_plugins()
    if r.ok:
        plugins = r.data.get("plugins", []) if isinstance(r.data, dict) else []
        print(f"  可用插件: {len(plugins)} 个")
        for p in plugins[:5]:
            if isinstance(p, dict):
                print(f"    - {p.get('name', '?')}: {p.get('description', '')[:50]}")
    print()

    # ACP 注册表
    pp("GetAllAcpRegistries", ws.plugins.get_all_acp_registries())
    print()


# ═══════════════════════════════════════════════════════
#  示例 7: OAuth 认证探测
# ═══════════════════════════════════════════════════════
def demo_auth_providers():
    """检测 Firebase OAuth 提供商状态"""
    print("=== OAuth 提供商检测 ===")
    results = check_providers()
    for name, st in results.items():
        tag = "✓" if st == "enabled" else "✗"
        print(f"  {tag} {name}: {st}")
    print()


# ═══════════════════════════════════════════════════════
#  示例 8: Cascade 对话操作 (需要 LS 连接)
# ═══════════════════════════════════════════════════════
def demo_cascade_operations():
    """Cascade AI 对话管理"""
    print("=== Cascade 对话操作 ===")
    ws = WindsurfClient(api_key=API_KEY)

    if not ws.ls.auto_connect():
        print("  ✗ 需要 Windsurf 运行中")
        return

    # 获取对话轨迹
    pp("GetCascadeTrajectories", ws.ls.get_cascade_trajectories())

    # 初始化面板状态
    pp("InitializeCascadePanelState", ws.ls.initialize_cascade_panel_state())

    # 用户信息
    pp("GetCascadeUserInfo", ws.ls.get_cascade_user_info())

    # 存储用户偏好
    pp("StoreCascadeUserPreferences", ws.ls.store_cascade_user_preferences())

    # 记忆管理
    pp("GetCascadeMemories", ws.ls.get_cascade_memories())

    # 获取工作区上下文
    pp("GetWorkspaceInfo", ws.ls.get_workspace_info())

    # 代码地图
    pp("GetCodeMap", ws.ls.get_code_map())

    # 获取补全
    pp("GetCompletions", ws.ls.get_completions())
    print()


# ═══════════════════════════════════════════════════════
#  主入口 — 选择要运行的示例
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    demos = {
        "1": ("注册流程", demo_registration),
        "2": ("Pro 注入", demo_pro_injection),
        "3": ("团队管理", demo_team_management),
        "4": ("Internal 方法", demo_internal_methods),
        "5": ("AI 模型与聊天", demo_ai_chat),
        "6": ("MCP 插件", demo_mcp_plugins),
        "7": ("OAuth 探测", demo_auth_providers),
        "8": ("Cascade 操作", demo_cascade_operations),
    }

    print("Windsurf API 高级示例")
    print("-" * 40)
    for k, (name, _) in demos.items():
        print(f"  {k}. {name}")
    print("  a. 全部运行")
    print()

    choice = input("选择 (1-8/a): ").strip()
    if choice == "a":
        for _, (_, fn) in demos.items():
            fn()
    elif choice in demos:
        demos[choice][1]()
    else:
        print("无效选择")

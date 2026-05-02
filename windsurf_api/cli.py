"""windsurf_api CLI — 命令行工具

用法:
    python -m windsurf_api status <api_key>                查看用户状态
    python -m windsurf_api register --github <token>       GitHub 注册
    python -m windsurf_api register --google <token>       Google 注册
    python -m windsurf_api models <api_key>                查看可用模型
    python -m windsurf_api capacity <api_key>              检查容量
    python -m windsurf_api mcp                             MCP OAuth 凭据
    python -m windsurf_api trial <api_key>                 Pro 试用检查
    python -m windsurf_api inject                          注入 LS 实验
    python -m windsurf_api scan <api_key>                  扫描 API 端点
    python -m windsurf_api providers                       检查 OAuth providers
    python -m windsurf_api proto <ls_binary_path>          提取 gRPC 协议
    python -m windsurf_api proxy --keys k1,k2 --port 8080  启动反代服务器
    python -m windsurf_api daemon                          启动 Pro 注入守护
"""
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')


def cmd_status(args):
    from .client import WindsurfClient
    if not args:
        print("用法: status <api_key>")
        return
    ws = WindsurfClient(api_key=args[0])
    st = ws.get_user_status()
    print(f"  Email:   {st.email}")
    print(f"  Plan:    {st.plan_name} (tier={st.teams_tier})")
    print(f"  Credits: {st.available_prompt_credits:,}P + {st.available_flow_credits:,}F = {st.total_credits:,}")
    print(f"  Daily:   {st.daily_quota_pct}%  Weekly: {st.weekly_quota_pct}%")
    print(f"  Period:  {st.plan_start} → {st.plan_end}")
    if st.referral_code:
        print(f"  Referral: {st.referral_code}")
    if st.has_paid_features:
        print(f"  Pro:     ✓")


def cmd_register(args):
    from .client import WindsurfClient
    ws = WindsurfClient()

    if "--github" in args:
        token = args[args.index("--github") + 1]
        fb = ws.login_github(token)
    elif "--google" in args:
        token = args[args.index("--google") + 1]
        fb = ws.login_google(token)
    elif "--microsoft" in args:
        token = args[args.index("--microsoft") + 1]
        fb = ws.login_microsoft(token)
    else:
        print("用法: register --github <token>")
        return

    if not fb.ok:
        print(f"  ✗ Firebase 登录失败: {fb.display_name}")
        return

    print(f"  ✓ Firebase: {fb.email}")
    result = ws.register()
    if result.ok:
        print(f"  ✓ API Key: {result.api_key}")
        st = ws.get_user_status()
        print(f"  ✓ Credits: {st.total_credits:,}")
    else:
        print(f"  ✗ 注册失败: {result.user}")


def cmd_models(args):
    from .client import WindsurfClient
    if not args:
        print("用法: models <api_key>")
        return
    ws = WindsurfClient(api_key=args[0])
    providers = ws.get_models()
    print(f"  {len(providers)} 个模型提供商:")
    for p in providers:
        print(f"    {p.display_name} ({p.name})")
        for m in p.models[:5]:
            name = m.get("displayName", m.get("name", "?")) if isinstance(m, dict) else str(m)
            print(f"      - {name}")


def cmd_capacity(args):
    from .client import WindsurfClient
    if not args:
        print("用法: capacity <api_key>")
        return
    ws = WindsurfClient(api_key=args[0])
    r = ws.check_capacity()
    print(json.dumps(r.data if hasattr(r, 'data') else r, indent=2, ensure_ascii=False, default=str))


def cmd_mcp(_args):
    from .client import WindsurfClient
    ws = WindsurfClient()
    r = ws.get_mcp_secrets()
    print(json.dumps(r.data if hasattr(r, 'data') else r, indent=2, ensure_ascii=False, default=str))


def cmd_trial(args):
    from .client import WindsurfClient
    if not args:
        print("用法: trial <api_key>")
        return
    ws = WindsurfClient(api_key=args[0])
    r = ws.check_pro_trial()
    print(json.dumps(r.data if hasattr(r, 'data') else r, indent=2, ensure_ascii=False, default=str))


def cmd_inject(_args):
    from .client import WindsurfClient
    ws = WindsurfClient()
    print("  探测 LS 进程...")
    connected = ws.ls.auto_connect()
    if not connected:
        print("  ✗ LS 未找到, Windsurf 需要运行中")
        return
    print(f"  ✓ LS port={ws.ls.port}, csrf={'有' if ws.ls.csrf_token else '无'}")
    r = ws.inject_pro()
    print(f"  结果: status={r.status}, ok={r.ok}")
    if r.data:
        print(f"  {json.dumps(r.data, indent=2, ensure_ascii=False, default=str)[:500]}")


def cmd_scan(args):
    from .client import WindsurfClient
    if not args:
        print("用法: scan <api_key>")
        return
    ws = WindsurfClient(api_key=args[0])

    # 扫描 SeatManagement 关键方法
    methods = [
        "GetUserStatus", "GetPlanStatus", "GetUserSubscription",
        "CheckProTrialEligibility", "GetTeamsFeatures",
        "GetCustomerPortal", "GetTeamBilling", "GetUsageConfig",
        "GetApiKeySummary", "GetProfileData", "GetWrapped",
        "GetGitHubAccountStatus", "GetNetlifyAccountStatus",
        "GetCascadeAnalytics", "GetLicense",
    ]
    print("  扫描 SeatManagement...")
    for m in methods:
        r = ws.seat.call(m, {"metadata": {"apiKey": args[0]}})
        tag = "✓" if r.ok else f"[{r.status}]"
        print(f"    {tag} {m}")

    # 扫描 ApiServer
    api_methods = [
        "GetModelProviders", "GetCascadeModelConfigs", "GetModelStatuses",
        "CheckChatCapacity", "GetLifeguardConfig", "GetExtensionStats",
        "GetAllOidcProviders", "CheckHybridDeploymentStatus",
    ]
    print("\n  扫描 ApiServer...")
    for m in api_methods:
        r = ws.api_server.call(m, {"metadata": {"apiKey": args[0]}})
        tag = "✓" if r.ok else f"[{r.status}]"
        print(f"    {tag} {m}")

    # 扫描 Plugins
    print("\n  扫描 Plugins...")
    r = ws.plugins.get_mcp_client_infos()
    print(f"    {'✓' if r.ok else f'[{r.status}]'} GetMcpClientInfos")
    r = ws.plugins.get_available_cascade_plugins()
    print(f"    {'✓' if r.ok else f'[{r.status}]'} GetAvailableCascadePlugins")


def cmd_providers(_args):
    from .auth import check_providers
    results = check_providers()
    for name, status in results.items():
        tag = "✓" if status == "enabled" else "✗"
        print(f"  {tag} {name}: {status}")


def cmd_proto(args):
    """从 LS binary 提取 gRPC 协议"""
    import re
    if not args:
        # 自动查找
        import os
        candidates = [
            r"D:\Windsurf\resources\app\extensions\windsurf\bin\language_server_windows_x64.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Windsurf",
                         "resources", "app", "extensions", "windsurf", "bin",
                         "language_server_windows_x64.exe"),
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)
        if not path:
            print("用法: proto <ls_binary_path>")
            return
    else:
        path = args[0]

    print(f"  分析: {path}")
    with open(path, 'rb') as f:
        data = f.read()

    services = {}
    for m in re.finditer(rb'/exa\.([a-z_]+)_pb\.([A-Za-z]+Service)/([A-Za-z]+)', data):
        pkg, svc, method = m.group(1).decode(), m.group(2).decode(), m.group(3).decode()
        full = f"exa.{pkg}_pb.{svc}"
        services.setdefault(full, set()).add(method)

    total = sum(len(v) for v in services.values())
    print(f"\n  {len(services)} 服务, {total} 方法:\n")
    for svc in sorted(services):
        methods = sorted(services[svc])
        print(f"  [{svc}] ({len(methods)})")
        for m in methods:
            print(f"    {m}")
        print()


def cmd_proxy(args):
    """启动 OpenAI 兼容反代"""
    import os
    keys = []
    port = 8080
    auth = ""
    verbose = False

    i = 0
    while i < len(args):
        if args[i] in ("--keys", "-k") and i + 1 < len(args):
            keys.extend([k.strip() for k in args[i + 1].split(",") if k.strip()])
            i += 2
        elif args[i] in ("--key-file", "-f") and i + 1 < len(args):
            with open(args[i + 1]) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        keys.append(line)
            i += 2
        elif args[i] in ("--port", "-p") and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif args[i] in ("--auth", "-a") and i + 1 < len(args):
            auth = args[i + 1]
            i += 2
        elif args[i] in ("--verbose", "-v"):
            verbose = True
            i += 1
        else:
            i += 1

    env_keys = os.environ.get("WINDSURF_KEYS", "")
    if env_keys:
        keys.extend([k.strip() for k in env_keys.split(",") if k.strip()])

    if not keys:
        print("用法: proxy --keys sk-ws-key1,sk-ws-key2 [--port 8080] [--auth token]")
        print("  或: proxy --key-file keys.txt")
        print("  或: 设置环境变量 WINDSURF_KEYS")
        return

    keys = list(dict.fromkeys(keys))
    from .proxy.server import ProxyServer
    server = ProxyServer(keys=keys, port=port, auth_token=auth, verbose=verbose)
    server.start()


def cmd_daemon(args):
    """启动 Pro 注入守护进程"""
    interval = 30
    key = ""
    i = 0
    while i < len(args):
        if args[i] == "--interval" and i + 1 < len(args):
            interval = int(args[i + 1])
            i += 2
        elif args[i] == "--key" and i + 1 < len(args):
            key = args[i + 1]
            i += 2
        else:
            i += 1

    from .tools.pro_daemon import ProDaemon
    daemon = ProDaemon(check_interval=interval, api_key=key)
    daemon.start()


COMMANDS = {
    "status": cmd_status,
    "register": cmd_register,
    "models": cmd_models,
    "capacity": cmd_capacity,
    "mcp": cmd_mcp,
    "trial": cmd_trial,
    "inject": cmd_inject,
    "scan": cmd_scan,
    "providers": cmd_providers,
    "proto": cmd_proto,
    "proxy": cmd_proxy,
    "daemon": cmd_daemon,
}


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return

    cmd = args[0]
    if cmd not in COMMANDS:
        print(f"未知命令: {cmd}")
        print(f"可用: {', '.join(COMMANDS.keys())}")
        return

    COMMANDS[cmd](args[1:])


if __name__ == "__main__":
    main()

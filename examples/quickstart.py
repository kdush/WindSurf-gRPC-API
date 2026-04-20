"""windsurf-api 快速上手示例 / Quick Start Example

使用前请先获取一个 Windsurf API Key (sk-ws-...)
Before using, get a Windsurf API Key (sk-ws-...)
"""
from windsurf_api import WindsurfClient, TeamsTier

# ── 1. 创建客户端 / Create client ──────────────────────
API_KEY = "sk-ws-YOUR_KEY_HERE"  # 替换为你的 key / Replace with your key
ws = WindsurfClient(api_key=API_KEY)
print(f"Client: {ws}\n")

# ── 2. 查看用户状态 / Check user status ────────────────
status = ws.get_user_status()
print("=== User Status ===")
print(f"  Email:    {status.email}")
print(f"  Plan:     {status.plan_name}")
print(f"  Tier:     {status.teams_tier}")
print(f"  Is Pro:   {status.is_pro}")
print(f"  Credits:  {status.total_credits:,}")
print(f"  Quota:    {status.daily_quota_pct}% daily, {status.weekly_quota_pct}% weekly")
print()

# ── 3. 查看模型 / List models ──────────────────────────
print("=== AI Models ===")
for p in ws.get_models():
    print(f"  {p.display_name} ({len(p.models)} models)")
    for m in p.models[:3]:
        name = m.get("displayName", m.get("name", "?")) if isinstance(m, dict) else str(m)
        print(f"    - {name}")
print()

# ── 4. 检查容量 / Check capacity ──────────────────────
print("=== Capacity ===")
r = ws.check_capacity()
print(f"  Has capacity: {r.data}")
print()

# ── 5. 检查限速 / Check rate limit ────────────────────
print("=== Rate Limit ===")
r = ws.check_rate_limit()
print(f"  Rate limit: {r.data}")
print()

# ── 6. MCP 插件 / MCP Plugins ─────────────────────────
print("=== Plugins ===")
r = ws.get_plugins()
print(f"  Plugins: {r.data}")
print()

# ── 7. 底层服务调用 / Low-level service calls ─────────
print("=== Advanced: Direct Service Access ===")
r = ws.seat.get_plan_status()
print(f"  Plan status: ok={r.ok}, status={r.status}")

r = ws.api_server.get_model_statuses()
print(f"  Model statuses: ok={r.ok}")

r = ws.seat.check_pro_trial_eligibility()
print(f"  Pro trial: ok={r.ok}")

print("\nDone! 🎉")

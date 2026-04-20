# windsurf-api

**Unofficial Python SDK for Windsurf IDE** — Reverse-engineered gRPC protocol with 13 services and 560+ methods.

非官方 Windsurf IDE Python SDK —— 逆向完整 gRPC 协议，13 个服务、560+ 方法全覆盖。

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](#)

---

## Features / 特性

- **Zero dependencies** — Pure Python stdlib, no `pip install` headaches | 零依赖，纯标准库
- **560+ methods** across 13 gRPC services | 13 个服务 560+ 方法全覆盖
- **Type-safe** — Dataclass models with IDE autocomplete | 类型安全，IDE 自动补全
- **Beginner-friendly** — One import, three lines to start | 新手友好，三行代码上手
- **CLI included** — Command-line tool for quick operations | 自带命令行工具

## Install / 安装

```bash
# Clone this repo / 克隆仓库
git clone https://github.com/YOUR_USERNAME/windsurf-api.git
cd windsurf-api

# Install / 安装
pip install -e .

# Or just copy windsurf_api/ folder to your project
# 或者直接把 windsurf_api/ 文件夹复制到你的项目里
```

## Quick Start / 快速上手

```python
from windsurf_api import WindsurfClient

# Create client with your API key / 用 API Key 创建客户端
ws = WindsurfClient(api_key="sk-ws-...")

# Check user status / 查看用户状态
status = ws.get_user_status()
print(f"Email: {status.email}")
print(f"Plan:  {status.plan_name}")
print(f"Credits: {status.total_credits:,}")

# List available AI models / 列出可用 AI 模型
for provider in ws.get_models():
    print(f"{provider.display_name}: {len(provider.models)} models")
```

## Authentication / 认证

Windsurf uses Firebase Authentication. You can login with GitHub/Google/Microsoft OAuth, or email/password.

Windsurf 使用 Firebase 认证，支持 GitHub/Google/Microsoft OAuth 或邮箱密码登录。

```python
from windsurf_api import WindsurfClient

ws = WindsurfClient()

# GitHub OAuth login / GitHub 登录
firebase_user = ws.login_github("your_github_access_token")

# Google OAuth login / Google 登录
firebase_user = ws.login_google("your_google_id_token")

# Email login / 邮箱登录
firebase_user = ws.login_email("you@example.com", "password")

# Register to get API Key / 注册获取 API Key
result = ws.register()
if result.ok:
    print(f"API Key: {result.api_key}")
```

## Services / 服务一览

| Service | Methods | Description |
|---------|---------|-------------|
| `ws.seat` | 143 | User, team, billing, subscription, SSO |
| `ws.api_server` | 159 | Models, chat, completions, deployments |
| `ws.ls` | 174 | Local Language Server (completions, diagnostics) |
| `ws.extension` | 48 | Extension features (files, terminal, audio) |
| `ws.plugins` | 7 | MCP plugins, Cascade plugins |
| `ws.analytics` | 8 | Telemetry |
| `ws.user_analytics` | 7 | User analytics |
| `ws.product_analytics` | 2 | Product analytics |
| `ws.browser_preview` | 3 | Browser preview |
| `ws.filesystem` | 3 | File system provider |
| `ws.dev` | 3 | Dev tools |
| `ws.auth_service` | 1 | Auth JWT |
| `ws.chat_client` | 1 | Chat stream |

**Total: 559 methods** across 13 services.

## Examples / 使用示例

### Check Capacity / 检查容量

```python
ws = WindsurfClient(api_key="sk-ws-...")
r = ws.check_capacity()
print(r.data)  # {'hasCapacity': True}
```

### Team Management / 团队管理

```python
ws.seat.get_team_info()
ws.seat.get_users()
ws.seat.create_multi_tenant_team(name="My Team")
```

### MCP Plugin Secrets / MCP 插件凭据

```python
r = ws.plugins.get_mcp_client_infos()
print(r.data)  # Contains OAuth client IDs & secrets
```

### Language Server Experiments / LS 实验注入

```python
# Auto-discover local LS process / 自动发现本地 LS 进程
ws.ls.auto_connect()

# Inject Pro experiments / 注入 Pro 实验
ws.inject_pro()

# Or manually set experiments / 或手动设置实验
from windsurf_api import ExperimentKey
ws.inject_experiments(
    disable=[ExperimentKey.CASCADE_ENFORCE_QUOTA],  # 204
    enable=[ExperimentKey.CASCADE_ENABLE_MCP_TOOLS],  # 245
)
```

### Raw gRPC Call / 原始 gRPC 调用

```python
# Call any method on any service / 调用任意服务的任意方法
r = ws.call(
    "exa.seat_management_pb.SeatManagementService",
    "GetUserStatus",
    {"metadata": {"apiKey": "sk-ws-..."}}
)
print(r.ok, r.status, r.data)
```

## CLI / 命令行

```bash
# User status / 用户状态
python -m windsurf_api status <api_key>

# Register with GitHub / GitHub 注册
python -m windsurf_api register --github <token>

# List models / 模型列表
python -m windsurf_api models <api_key>

# Check capacity / 容量检查
python -m windsurf_api capacity <api_key>

# MCP secrets / MCP 凭据
python -m windsurf_api mcp

# Pro trial check / Pro 试用检查
python -m windsurf_api trial <api_key>

# Inject LS experiments / 注入实验
python -m windsurf_api inject

# Scan endpoints / 扫描端点
python -m windsurf_api scan <api_key>

# Extract gRPC protocol from LS binary / 从 LS 提取协议
python -m windsurf_api proto
```

## Protocol Details / 协议细节

Windsurf uses **Connect-protocol** — a gRPC-compatible protocol:

| Detail | Value |
|--------|-------|
| Transport | HTTP/1.1 (not HTTP/2) |
| Encoding | JSON (not protobuf binary) |
| Endpoint | `POST {base_url}/{service}/{method}` |
| Header | `Connect-Protocol-Version: 1` |
| Content-Type | `application/json` |

### Servers / 服务器

| Server | URL |
|--------|-----|
| API Server | `https://server.self-serve.windsurf.com` |
| Register | `https://register.windsurf.com` |
| EU Server | `https://eu.windsurf.com/_route/api_server` |
| Inference | `https://inference.codeium.com` |
| Feature Flags | `https://unleash.codeium.com/api` |
| Local LS | `http://127.0.0.1:{random_port}` |

## Key Enums / 关键枚举

```python
from windsurf_api import TeamsTier, BillingStrategy, ExperimentKey

# Plan tiers / 套餐层级
TeamsTier.PRO           # 2
TeamsTier.TRIAL         # 9
TeamsTier.TEAMS         # 1
TeamsTier.ENTERPRISE_SAAS  # 3
TeamsTier.PRO_ULTIMATE  # 8

# Billing / 计费
BillingStrategy.CREDITS  # 1
BillingStrategy.QUOTA    # 2

# Experiments / 实验 Flag
ExperimentKey.CASCADE_ENFORCE_QUOTA              # 204
ExperimentKey.CASCADE_ENABLE_MCP_TOOLS           # 245
ExperimentKey.CASCADE_PLAN_BASED_CONFIG_OVERRIDE # 266
```

## Project Structure / 项目结构

```
windsurf-api/
├── README.md
├── LICENSE
├── pyproject.toml
├── setup.py
├── examples/
│   └── quickstart.py
└── windsurf_api/              # Python package
    ├── __init__.py            # Public API exports
    ├── client.py              # WindsurfClient (main entry)
    ├── transport.py           # Connect-protocol HTTP layer
    ├── auth.py                # Firebase authentication
    ├── models.py              # Dataclass models & enums
    ├── cli.py                 # CLI tool
    ├── __main__.py            # python -m windsurf_api
    └── services/
        ├── seat_management.py # 143 methods
        ├── api_server.py      # 159 methods
        ├── language_server.py # 174 methods
        ├── extension_server.py# 48 methods
        ├── plugins.py         # 7 methods
        ├── analytics.py       # 17 methods
        └── misc.py            # 8 methods
```

## Disclaimer / 免责声明

This project is for **educational and research purposes only**. It is an unofficial reverse-engineering effort and is not affiliated with, endorsed by, or associated with Windsurf/Codeium in any way.

本项目仅供**学习和研究**使用。这是一个非官方的逆向工程项目，与 Windsurf/Codeium 无任何关联。

## License

MIT License — see [LICENSE](LICENSE)

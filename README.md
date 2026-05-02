<![CDATA[<div align="center">

# WindSurf-gRPC-API

**Windsurf IDE 全协议逆向 Python SDK**

通过逆向 Windsurf Language Server 二进制文件，提取全部 13 个 gRPC 服务、567+ RPC 方法。<br>
内置 OpenAI / Anthropic / Gemini 三协议兼容反代服务器。零依赖。

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)](#)

[快速开始](#快速开始) · [多协议反代](#多协议反代服务器) · [API 参考](#api-参考) · [协议原理](#协议原理)

</div>

---

## 概览

[Windsurf](https://windsurf.com) 是一个 AI 编程 IDE（类似 Cursor），底层通过 **Connect Protocol**（gRPC-over-HTTP/1.1 + JSON）与服务器通信。

本项目对 Windsurf 的 Language Server 二进制进行了完整逆向工程，将全部通信协议封装为 Python SDK：

| 特性 | 说明 |
|------|------|
| **13 个 gRPC 服务** | 用户管理、AI 模型、聊天、补全、团队、插件、部署等 |
| **567+ RPC 方法** | 每个方法对应一个服务端接口，100% 覆盖 |
| **多协议反代** | 内置 OpenAI / Anthropic / Gemini 三协议兼容代理 |
| **高级工具集** | 批量注册、Pro 注入守护、Cascade 自动化 |
| **零依赖** | 仅使用 Python 标准库，无需安装任何第三方包 |
| **CLI 工具** | 命令行直接操作，无需写代码 |

---

## 安装

```bash
git clone https://github.com/fendoushaonian/WindSurf-gRPC-API.git
cd WindSurf-gRPC-API
pip install -e .
```

或直接将 `windsurf_api/` 目录复制到项目中使用。

---

## 快速开始

```python
from windsurf_api import WindsurfClient

ws = WindsurfClient(api_key="sk-ws-xxxxxxx")

# 查看用户状态
s = ws.get_user_status()
print(s.email, s.plan_name, s.total_credits, s.is_pro)

# 查看可用 AI 模型
for p in ws.get_models():
    print(f"{p.display_name}: {[m.get('displayName','?') for m in p.models]}")

# 检查容量
r = ws.check_capacity()
print(r.data)  # {'hasCapacity': True}
```

---

## 核心功能

### 1. 用户状态 & 额度

```python
s = ws.get_user_status()
print(f"邮箱: {s.email}")
print(f"套餐: {s.plan_name}")              # Free / Pro / Trial
print(f"层级: {s.teams_tier}")              # 0=Free, 2=Pro, 9=Trial
print(f"Prompt 额度: {s.available_prompt_credits}")
print(f"Flow 额度: {s.available_flow_credits}")
print(f"总额度: {s.total_credits}")
print(f"日配额: {s.daily_quota_pct}%")
print(f"是 Pro: {s.is_pro}")
```

### 2. 认证 & 注册

支持 GitHub / Google / Microsoft OAuth 和邮箱密码：

```python
ws = WindsurfClient()

# OAuth 登录（任选一种）
user = ws.login_github("github_access_token")
user = ws.login_google("google_id_token")
user = ws.login_microsoft("microsoft_id_token")

# 邮箱密码
user = ws.login_email("you@email.com", "password")
user = ws.signup_email("new@email.com", "password")   # 新账号注册

# 登录后获取 API Key
if user.ok:
    result = ws.register()
    print(result.api_key)  # sk-ws-xxxxxxx
```

认证流程：`OAuth → Firebase id_token → Windsurf RegisterUser → API Key (sk-ws-...)`

### 3. 团队管理

```python
ws.seat.get_team_info()
ws.seat.get_users()
ws.seat.create_multi_tenant_team(teamName="My Team")
ws.seat.add_users_to_team(emails=["a@test.com"])
ws.seat.remove_users_from_team(emails=["a@test.com"])
ws.seat.get_teams_features()
```

### 4. MCP 插件

```python
ws.plugins.get_mcp_client_infos()           # OAuth 凭据
ws.plugins.get_available_cascade_plugins()   # 插件列表
```

### 5. LS 实验注入

通过本地 Language Server 注入 Feature Flags，解锁功能：

```python
from windsurf_api import ExperimentKey

ws.ls.auto_connect()    # 自动探测 LS 进程并连接
ws.inject_pro()         # 一键注入 Pro（关闭额度限制 + 开启 Pro 功能）

# 精细控制
ws.inject_experiments(
    disable=[ExperimentKey.CASCADE_ENFORCE_QUOTA],
    enable=[ExperimentKey.CASCADE_ENABLE_MCP_TOOLS],
)
```

> 需要 Windsurf IDE 正在运行。自动扫描端口、读取 CSRF token、连接 LS。

### 6. 通用调用

调用任意 gRPC 服务/方法：

```python
r = ws.call(
    "exa.seat_management_pb.SeatManagementService",
    "GetUserStatus",
    {"metadata": {"apiKey": "sk-ws-xxx"}}
)
print(r.ok, r.status, r.data)
```

---

## 多协议反代服务器

内置三协议兼容反代，将 Windsurf 后端的 AI 能力包装为 OpenAI / Anthropic / Gemini API 格式。

### 启动

```bash
# 命令行
python -m windsurf_api.proxy --keys sk-ws-key1,sk-ws-key2 --port 8080
python -m windsurf_api.proxy --key-file keys.txt --auth my-secret
```

```python
# 代码
from windsurf_api.proxy import ProxyServer

server = ProxyServer(keys=["sk-ws-key1", "sk-ws-key2"], port=8080, auth_token="my-secret")
server.start()           # 阻塞
server.start_background() # 后台线程
```

### 支持端点

| 协议 | 端点 | 流式 | 说明 |
|------|------|:----:|------|
| **OpenAI** | `POST /v1/chat/completions` | ✅ | 聊天补全 |
| **OpenAI** | `GET /v1/models` | — | 模型列表 |
| **Anthropic** | `POST /v1/messages` | ✅ | Messages API |
| **Gemini** | `POST /v1beta/models/{model}:generateContent` | — | 生成内容 |
| **Gemini** | `POST /v1beta/models/{model}:streamGenerateContent` | ✅ | 流式生成 |
| 通用 | `GET /v1/status` | — | Key 池状态 |
| 通用 | `GET /health` | — | 健康检查 |

### 三种 SDK 直连示例

所有协议共享同一套 Windsurf 后端模型，任何协议都能调用 Claude、GPT、Gemini 等全部模型。

```python
# ── OpenAI SDK ──
import openai
client = openai.OpenAI(base_url="http://localhost:8080/v1", api_key="my-secret")
r = client.chat.completions.create(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True,
)
for chunk in r:
    print(chunk.choices[0].delta.content or "", end="")
```

```python
# ── Anthropic SDK ──
import anthropic
client = anthropic.Anthropic(base_url="http://localhost:8080", api_key="my-secret")
msg = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}],
)
print(msg.content[0].text)
```

```python
# ── Gemini SDK ──
import google.generativeai as genai
genai.configure(
    api_key="my-secret",
    transport="rest",
    client_options={"api_endpoint": "http://localhost:8080"},
)
model = genai.GenerativeModel("gemini-2.5-pro")
response = model.generate_content("Hello!")
print(response.text)
```

### 认证方式

| 协议 | 认证方式 |
|------|---------|
| OpenAI | `Authorization: Bearer <token>` |
| Anthropic | `x-api-key: <token>` 或 `Authorization: Bearer <token>` |
| Gemini | `?key=<token>` 或 `Authorization: Bearer <token>` |

### 反代架构

```
┌─────────────────────────────────────────────────────────────┐
│                     反代服务器 (Python)                       │
│                                                             │
│  OpenAI 请求 ──→ ┐                                          │
│  Anthropic 请求 ─→ 格式转换 ──→ Windsurf Connect API ──→ 响应 │
│  Gemini 请求 ──→ ┘             (gRPC-over-HTTP)             │
│                                                             │
│  特性: Key 池轮换 · 自动降级 · SSE 流式 · CORS              │
└─────────────────────────────────────────────────────────────┘
```

---

## 高级工具集

```python
from windsurf_api.tools import AccountFactory, ProDaemon, CascadeBot
```

| 工具 | 说明 |
|------|------|
| `AccountFactory` | 批量 OAuth 注册，自动获取 API Key |
| `ProDaemon` | Pro 实验注入守护进程，持续监控并自动注入 |
| `CascadeBot` | Cascade 对话自动化，程序化调用 AI 助手 |

---

## 命令行工具

```bash
# 用户状态
python -m windsurf_api status <key>

# 可用模型
python -m windsurf_api models <key>

# 注册新账号
python -m windsurf_api register --github <token>

# 容量检查
python -m windsurf_api capacity <key>

# MCP 凭据
python -m windsurf_api mcp

# Pro 试用检查
python -m windsurf_api trial <key>

# LS 实验注入
python -m windsurf_api inject

# API 端点扫描
python -m windsurf_api scan <key>

# OAuth 提供商检测
python -m windsurf_api providers

# 协议提取
python -m windsurf_api proto
```

---

## API 参考

### 13 个 gRPC 服务

| 服务 | 访问方式 | 方法数 | 功能 |
|------|---------|:------:|------|
| **SeatManagement** | `ws.seat` | 148 | 用户注册、登录、套餐、团队、计费、SSO、配额、推荐 |
| **ApiServer** | `ws.api_server` | 170 | AI 模型、聊天补全、代码补全、部署、遥测 |
| **LanguageServer** | `ws.ls` | 172 | 本地补全、诊断、Cascade 聊天、实验注入 |
| **ExtensionServer** | `ws.extension` | 49 | 文件操作、终端、音频、设置、Git |
| **CascadePlugins** | `ws.plugins` | 5 | MCP 插件管理 |
| **Analytics** | `ws.analytics` | 8 | 使用数据记录 |
| **UserAnalytics** | `ws.user_analytics` | 7 | 用户行为分析 |
| **ProductAnalytics** | `ws.product_analytics` | 2 | 产品分析上报 |
| **BrowserPreview** | `ws.browser_preview` | 3 | 浏览器预览 |
| **FileSystemProvider** | `ws.filesystem` | 3 | 文件系统读写 |
| **Dev** | `ws.dev` | 3 | 开发调试 |
| **Auth** | `ws.auth_service` | 1 | JWT 认证 |
| **ChatClient** | `ws.chat_client` | 1 | 聊天流式请求 |

### 返回值

大部分方法返回 `RpcResponse`：

```python
r = ws.seat.get_plan_status()
r.ok       # bool — 请求是否成功
r.status   # int  — HTTP 状态码
r.data     # dict — 响应数据
```

高层方法返回解析后的对象：

```python
s = ws.get_user_status()   # → UserStatus
s.email, s.plan_name, s.is_pro, s.total_credits

models = ws.get_models()   # → List[ModelProvider]
models[0].display_name, models[0].models
```

### 枚举

```python
from windsurf_api import TeamsTier, BillingStrategy, ExperimentKey

# 套餐层级
TeamsTier.PRO              # 2
TeamsTier.TRIAL            # 9
TeamsTier.PRO_ULTIMATE     # 8

# 计费策略
BillingStrategy.CREDITS    # 1
BillingStrategy.QUOTA      # 2

# Feature Flags
ExperimentKey.CASCADE_ENFORCE_QUOTA               # 204
ExperimentKey.CASCADE_ENABLE_MCP_TOOLS            # 245
ExperimentKey.CASCADE_ENABLE_AUTOMATED_MEMORIES   # 224
ExperimentKey.CASCADE_PLAN_BASED_CONFIG_OVERRIDE  # 266
```

---

## 协议原理

### Connect Protocol

Windsurf 使用 [Connect Protocol](https://connectrpc.com/)（gRPC 的 HTTP/1.1 + JSON 简化版），本质上就是普通 REST 请求：

```http
POST /exa.seat_management_pb.SeatManagementService/GetUserStatus HTTP/1.1
Host: server.self-serve.windsurf.com
Content-Type: application/json
Connect-Protocol-Version: 1

{"metadata": {"apiKey": "sk-ws-xxx", "ideName": "windsurf"}}
```

```json
// 响应
{
  "userStatus": {
    "email": "you@gmail.com",
    "planStatus": {
      "planInfo": {"planName": "Pro", "teamsTier": 2},
      "availablePromptCredits": "15000"
    }
  }
}
```

### 服务端

| 服务器 | 地址 | 用途 |
|--------|------|------|
| 主 API | `https://server.self-serve.windsurf.com` | 核心接口 |
| 注册 | `https://register.windsurf.com` | 账号注册 |
| 欧洲 | `https://eu.windsurf.com/_route/api_server` | EU 节点 |
| 推理 | `https://inference.codeium.com` | AI 推理 |
| Flags | `https://unleash.codeium.com/api` | Feature Flags |
| 本地 LS | `http://127.0.0.1:{random_port}` | Language Server |

### 认证流程

```
GitHub/Google/Microsoft OAuth
        │
        ▼
   Firebase Auth  ──→  id_token
        │
        ▼
 register.windsurf.com/RegisterUser  ──→  api_key (sk-ws-xxx)
        │
        ▼
 所有请求携带: {"metadata": {"apiKey": "sk-ws-xxx"}}
```

### 本地 Language Server

Windsurf 运行时会启动一个本地 LS 进程，监听随机端口。本库自动完成：

1. **端口扫描** — 通过 `netstat` 发现 LS 进程
2. **Token 提取** — 读取 CSRF token
3. **连接** — 建立 Connect 协议通信

---

## 项目结构

```
WindSurf-gRPC-API/
├── pyproject.toml              # 项目配置
├── setup.py                    # 兼容旧版 pip
├── examples/
│   ├── quickstart.py           # 快速上手示例
│   ├── advanced_usage.py       # 进阶用法
│   └── all_services_demo.py    # 全服务演示
│
└── windsurf_api/
    ├── __init__.py             # 包入口 & 导出
    ├── client.py               # WindsurfClient 主类
    ├── transport.py            # Connect 协议传输层
    ├── auth.py                 # Firebase OAuth 认证
    ├── models.py               # 数据模型 & 枚举
    ├── cli.py                  # CLI 命令行工具
    │
    ├── services/               # 13 个 gRPC 服务实现
    │   ├── seat_management.py  # 用户/团队/计费 (148 methods)
    │   ├── api_server.py       # 模型/聊天/部署 (170 methods)
    │   ├── language_server.py  # 本地 LS (172 methods)
    │   ├── extension_server.py # 扩展功能 (49 methods)
    │   ├── plugins.py          # MCP 插件 (5 methods)
    │   ├── analytics.py        # 分析服务 (17 methods)
    │   └── misc.py             # 其他服务 (9 methods)
    │
    ├── proxy/                  # 多协议反代服务器
    │   ├── server.py           # HTTP 服务器 & 路由
    │   ├── streaming.py        # SSE 流式传输
    │   ├── key_pool.py         # Key 池管理 & 轮换
    │   └── model_map.py        # 模型名称映射
    │
    └── tools/                  # 高级工具
        ├── account_factory.py  # 批量注册
        ├── pro_daemon.py       # Pro 注入守护
        └── cascade_bot.py      # Cascade 自动化
```

---

## FAQ

**Q: API Key 怎么获取？**
A: 方法一：用本库 `ws.login_github()` + `ws.register()` 自动获取。方法二：从 Windsurf 本地存储提取。

**Q: 401 / 403 错误？**
A: Key 无效或已过期，需要重新获取。

**Q: LS 方法报错？**
A: 需要 Windsurf IDE 正在运行。先 `ws.ls.auto_connect()` 连接本地 LS。

**Q: 反代支持哪些模型？**
A: 所有 Windsurf 支持的模型（Claude、GPT、Gemini 等），三种协议均可调用全部模型。

**Q: 需要装依赖吗？**
A: 不需要。零依赖，Python 3.12+ 标准库即可。

---

## 免责声明

本项目**仅供学习和研究**使用。这是非官方逆向工程项目，与 Windsurf / Codeium 无任何关联。使用者需自行遵守相关法律法规及服务条款。

## License

[MIT](LICENSE)
]]>

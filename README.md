# windsurf-api

> 把 Windsurf IDE 的**整套后端协议**逆向成了 Python 库，560+ 个接口随便调。

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![零依赖](https://img.shields.io/badge/依赖-无-brightgreen.svg)](#)

---

## 这是什么？

Windsurf 是一个 AI 编程 IDE（类似 Cursor）。它的客户端和服务器之间用 gRPC 协议通信。

我把 Windsurf 的 Language Server 二进制文件**完整逆向**了，提取出了它和服务器通信的全部协议：

- **13 个 gRPC 服务**（用户管理、AI 模型、聊天、插件、团队……）
- **560+ 个 RPC 方法**（每个方法就是一个 API 接口）
- 全部封装成了 Python 类，`ws.xxx()` 就能调

**零依赖** —— 只用 Python 自带的标准库，不需要装任何第三方包。

---

## 安装

两种方式，选一种就行：

**方式一：pip 安装（推荐）**
```bash
git clone https://github.com/fendoushaonian/WindSurf-gRPC-API.git
cd WindSurf-gRPC-API
pip install -e .
```

**方式二：直接复制**
把 `windsurf_api/` 文件夹丢到你项目里，直接 import 就能用。

---

## 三行代码上手

```python
from windsurf_api import WindsurfClient

ws = WindsurfClient(api_key="你的key")   # 创建客户端
status = ws.get_user_status()             # 查状态
print(status.email, status.plan_name, status.total_credits)
```

输出类似：
```
you@gmail.com Pro 30000
```

就这么简单。下面详细说每个功能。

---

## 功能大全

### 1. 查看用户状态

看你的账号是什么套餐、还剩多少额度：

```python
from windsurf_api import WindsurfClient

ws = WindsurfClient(api_key="sk-ws-xxxxxxx")
s = ws.get_user_status()

print(f"邮箱:     {s.email}")
print(f"套餐:     {s.plan_name}")        # Free / Pro / Trial
print(f"层级:     {s.teams_tier}")        # 0=免费 2=Pro 9=Trial
print(f"Prompt额度: {s.available_prompt_credits}")
print(f"Flow额度:   {s.available_flow_credits}")
print(f"总额度:   {s.total_credits}")
print(f"日配额:   {s.daily_quota_pct}%")
print(f"周配额:   {s.weekly_quota_pct}%")
print(f"是Pro吗:  {s.is_pro}")
```

### 2. 查看 AI 模型

看 Windsurf 当前支持哪些 AI 模型：

```python
for p in ws.get_models():
    print(f"\n{p.display_name}:")
    for m in p.models:
        name = m.get("displayName", m.get("name", "?")) if isinstance(m, dict) else str(m)
        print(f"  - {name}")
```

输出类似：
```
Anthropic:
  - Claude Sonnet 4
  - Claude 3.5 Haiku
OpenAI:
  - GPT-4.1
  - o3
Google:
  - Gemini 2.5 Pro
...
```

### 3. 登录 & 注册

Windsurf 用 Firebase 做认证。支持三种 OAuth + 邮箱密码：

```python
ws = WindsurfClient()

# GitHub 登录（最常用）
user = ws.login_github("你的github_access_token")

# Google 登录
user = ws.login_google("你的google_id_token")

# Microsoft 登录
user = ws.login_microsoft("你的microsoft_id_token")

# 邮箱密码登录
user = ws.login_email("you@email.com", "password123")

# 邮箱密码注册（新账号）
user = ws.signup_email("new@email.com", "password123")

# 登录成功后，注册 Windsurf 拿 API Key
if user.ok:
    result = ws.register()
    print(f"拿到 API Key: {result.api_key}")  # sk-ws-xxxxxxx
```

**认证流程说白了就是：**
1. 先用 GitHub/Google/邮箱 登录 Firebase → 拿到 `id_token`
2. 拿 `id_token` 去 Windsurf 注册 → 拿到 `api_key`（`sk-ws-` 开头）
3. 之后所有操作都用这个 `api_key`

### 4. 检查容量 & 限速

```python
# 还能不能发消息
r = ws.check_capacity()
print(r.data)  # {'hasCapacity': True} 就是还能用

# 有没有被限速
r = ws.check_rate_limit()
print(r.data)
```

### 5. 团队功能

```python
# 查看团队信息
ws.seat.get_team_info()

# 查看团队成员
ws.seat.get_users()

# 创建团队
ws.seat.create_multi_tenant_team(name="我的团队")

# 添加成员
ws.seat.add_users_to_team(emails=["a@test.com", "b@test.com"])

# 移除成员
ws.seat.remove_users_from_team(emails=["a@test.com"])

# 团队功能开关
ws.seat.get_teams_features()
```

### 6. MCP 插件

MCP 是 Windsurf 的插件系统。可以拿到 OAuth 凭据和插件列表：

```python
# 拿 MCP 的 OAuth client ID 和 secret
r = ws.plugins.get_mcp_client_infos()
print(r.data)

# 查看可用插件
r = ws.get_plugins()
print(r.data)
```

### 7. Pro 试用

```python
# 检查你的账号能不能激活 Pro 试用
r = ws.check_pro_trial()
print(r.data)
```

### 8. 推荐码

```python
# 处理推荐码
ws.seat.process_referral_code("ABC123")

# 验证推荐码是否有效
ws.seat.is_valid_referral_code("ABC123")
```

### 9. GitHub & Netlify 连接状态

```python
ws.seat.get_github_account_status()
ws.seat.get_netlify_account_status()
```

### 10. LS 实验注入

Windsurf 用「实验 Flag」控制功能开关。可以通过本地 Language Server 注入：

```python
# 自动找到本地 LS 进程并连接
ws.ls.auto_connect()

# 一键注入 Pro 实验（关闭额度限制，开启 Pro 功能）
ws.inject_pro()

# 或者手动控制要开/关哪些实验
from windsurf_api import ExperimentKey
ws.inject_experiments(
    disable=[ExperimentKey.CASCADE_ENFORCE_QUOTA],     # 关掉额度强制
    enable=[ExperimentKey.CASCADE_ENABLE_MCP_TOOLS],   # 开启 MCP 工具
)
```

> **注意：** LS 实验注入需要 Windsurf 正在运行。它会自动找到 LS 进程、读取 CSRF token、连接本地端口。

### 11. 底层直接调用

每个服务的每个方法都可以直接调：

```python
# 用户管理服务 (143 个方法)
ws.seat.get_plan_status()
ws.seat.get_customer_portal()
ws.seat.get_api_key_summary()
ws.seat.check_pro_trial_eligibility()

# API 服务 (159 个方法)
ws.api_server.get_cascade_model_configs()
ws.api_server.get_model_statuses()
ws.api_server.get_extension_stats()

# 插件服务
ws.plugins.get_mcp_client_infos()
ws.plugins.get_available_cascade_plugins()

# 扩展服务 (48 个方法)
ws.extension.open_external_url("https://example.com")
ws.extension.get_terminal_buffer()

# LS 服务 (174 个方法，需要本地 LS)
ws.ls.auto_connect()
ws.ls.heartbeat()
ws.ls.get_completions()
ws.ls.accept_completion()
```

### 12. 万能调用

如果你知道具体的 gRPC 服务名和方法名，可以直接裸调：

```python
r = ws.call(
    "exa.seat_management_pb.SeatManagementService",  # 服务全名
    "GetUserStatus",                                   # 方法名
    {"metadata": {"apiKey": "sk-ws-xxx"}}              # 参数
)
print(r.ok)      # True/False
print(r.status)  # HTTP 状态码
print(r.data)    # 返回数据（字典）
```

---

## 命令行工具

不写代码也能用，直接命令行操作：

```bash
# 查看账号状态
python -m windsurf_api status sk-ws-你的key

# 查看可用模型
python -m windsurf_api models sk-ws-你的key

# GitHub 注册新账号
python -m windsurf_api register --github 你的github_token

# 检查容量
python -m windsurf_api capacity sk-ws-你的key

# 查看 MCP 凭据
python -m windsurf_api mcp

# Pro 试用检查
python -m windsurf_api trial sk-ws-你的key

# 注入 LS 实验（需要 Windsurf 运行中）
python -m windsurf_api inject

# 扫描 API 端点
python -m windsurf_api scan sk-ws-你的key

# 检查 OAuth 登录方式
python -m windsurf_api providers

# 从 LS 二进制提取协议
python -m windsurf_api proto
```

---

## 13 个服务详细说明

通过逆向 Windsurf 的 Language Server 二进制文件，我提取出了全部 13 个 gRPC 服务：

| 服务 | 代码里怎么用 | 方法数 | 干什么的 |
|------|-------------|--------|---------|
| **SeatManagement** | `ws.seat` | 143 | 用户注册、登录、套餐、团队、计费、SSO、配额 |
| **ApiServer** | `ws.api_server` | 159 | AI 模型管理、聊天补全、代码补全、部署、遥测 |
| **LanguageServer** | `ws.ls` | 174 | 本地补全、诊断、Cascade 聊天、实验注入 |
| **ExtensionServer** | `ws.extension` | 48 | 文件操作、终端、音频、设置、Git 操作 |
| **CascadePlugins** | `ws.plugins` | 7 | MCP 插件管理、Cascade 插件列表 |
| **Analytics** | `ws.analytics` | 8 | 使用数据记录 |
| **UserAnalytics** | `ws.user_analytics` | 7 | 用户行为分析 |
| **ProductAnalytics** | `ws.product_analytics` | 2 | 产品分析上报 |
| **BrowserPreview** | `ws.browser_preview` | 3 | 浏览器预览功能 |
| **FileSystemProvider** | `ws.filesystem` | 3 | 文件系统读写 |
| **Dev** | `ws.dev` | 3 | 开发调试工具 |
| **Auth** | `ws.auth_service` | 1 | JWT 认证 |
| **ChatClient** | `ws.chat_client` | 1 | 聊天流式请求 |

---

## 协议原理

### Windsurf 怎么跟服务器通信？

Windsurf 用的不是标准 gRPC（需要 HTTP/2），而是 **Connect-protocol** —— 一种兼容 gRPC 的简化协议：

```
普通 gRPC:    HTTP/2 + Protobuf 二进制        → 很复杂
Connect:      HTTP/1.1 + JSON                  → 很简单，跟普通 REST API 差不多
```

**说白了就是发 POST 请求，body 是 JSON：**

```
POST https://server.self-serve.windsurf.com/exa.seat_management_pb.SeatManagementService/GetUserStatus
Content-Type: application/json
Connect-Protocol-Version: 1

{"metadata": {"apiKey": "sk-ws-xxx", "ideName": "windsurf"}}
```

服务器返回的也是 JSON：
```json
{
  "userStatus": {
    "email": "you@gmail.com",
    "planStatus": {
      "planInfo": {"planName": "Pro", "teamsTier": 2},
      "availablePromptCredits": "15000",
      "availableFlowCredits": "15000"
    }
  }
}
```

### 服务器地址

| 服务器 | 地址 | 说明 |
|--------|------|------|
| 主 API | `https://server.self-serve.windsurf.com` | 大部分接口都走这里 |
| 注册 | `https://register.windsurf.com` | 专门用来注册的 |
| 欧洲节点 | `https://eu.windsurf.com/_route/api_server` | 欧洲用户用这个 |
| 推理服务 | `https://inference.codeium.com` | AI 模型推理 |
| Feature Flag | `https://unleash.codeium.com/api` | 功能开关控制 |
| 本地 LS | `http://127.0.0.1:{随机端口}` | 本地 Language Server |

### 认证流程

```
你的代码
  │
  ├── 1. GitHub/Google OAuth ──→ Firebase (Google) ──→ 拿到 id_token
  │
  ├── 2. id_token ──→ register.windsurf.com/RegisterUser ──→ 拿到 api_key (sk-ws-xxx)
  │
  └── 3. 之后所有请求都在 JSON 里带上:
         {"metadata": {"apiKey": "sk-ws-xxx"}}
```

### 本地 LS 是什么？

Windsurf 启动后，会在本地跑一个 Language Server 进程（`language_server_windows_x64.exe`）。
这个进程开了个随机端口的 HTTP 服务，也是 Connect 协议。

本库的 `ws.ls` 会自动：
1. 找到 LS 进程（通过 `netstat` 扫端口）
2. 读取 CSRF token（从进程内存读环境变量）
3. 连接到本地端口

连上之后就可以调 174 个方法了（补全、聊天、实验注入等）。

---

## 返回值说明

大部分方法返回 `RpcResponse` 对象：

```python
r = ws.seat.get_plan_status()

r.ok       # True 或 False —— 请求是否成功
r.status   # HTTP 状态码 (200, 400, 401, 500...)
r.data     # 返回数据 (dict) —— 就是服务器返回的 JSON
```

少数方法返回解析好的对象：

```python
# get_user_status 返回 UserStatus 对象
s = ws.get_user_status()
s.email              # 邮箱
s.plan_name          # 套餐名
s.is_pro             # 是否Pro
s.total_credits      # 总额度

# get_models 返回 ModelProvider 列表
models = ws.get_models()
models[0].display_name  # 提供商名
models[0].models        # 模型列表
```

---

## 关键枚举值

```python
from windsurf_api import TeamsTier, BillingStrategy, ExperimentKey

# 套餐层级 —— 服务器返回的数字代表什么
TeamsTier.UNSPECIFIED     # 0  未指定
TeamsTier.TEAMS           # 1  Teams
TeamsTier.PRO             # 2  Pro
TeamsTier.ENTERPRISE_SAAS # 3  企业版
TeamsTier.PRO_ULTIMATE    # 8  Pro Ultimate
TeamsTier.TRIAL           # 9  试用

# 计费策略
BillingStrategy.CREDITS   # 1  按额度计费
BillingStrategy.QUOTA     # 2  按配额计费

# 实验 Flag（Feature Flag ID）
ExperimentKey.CASCADE_ENFORCE_QUOTA              # 204  额度强制
ExperimentKey.CASCADE_ENABLE_AUTOMATED_MEMORIES  # 224  自动记忆
ExperimentKey.CASCADE_ENABLE_MCP_TOOLS           # 245  MCP 工具
ExperimentKey.CASCADE_PLAN_BASED_CONFIG_OVERRIDE # 266  套餐配置覆盖
ExperimentKey.CASCADE_ENABLE_PROXY_WEB_SERVER    # 290  代理 Web 服务器
ExperimentKey.CASCADE_WEB_APP_DEPLOYMENTS_ENABLED# 300  Web 部署
ExperimentKey.CASCADE_WINDSURF_BROWSER_TOOLS_ENABLED # 328  浏览器工具
```

---

## 项目结构

```
windsurf-api/
├── README.md               ← 你现在在看的这个
├── LICENSE                  ← MIT 开源协议
├── pyproject.toml           ← pip install 用的配置
├── setup.py                 ← 兼容旧版 pip
├── examples/
│   └── quickstart.py        ← 跑一下就知道怎么用了
│
└── windsurf_api/            ← 核心代码（就这一个文件夹）
    ├── __init__.py          ← from windsurf_api import ... 的入口
    ├── client.py            ← WindsurfClient 主类
    ├── transport.py         ← HTTP 请求发送层 (Connect 协议)
    ├── auth.py              ← Firebase 登录/注册
    ├── models.py            ← 数据类型定义 (UserStatus 等)
    ├── cli.py               ← 命令行工具
    ├── __main__.py          ← python -m windsurf_api 入口
    └── services/            ← 13 个服务的实现
        ├── seat_management.py   ← 用户/团队/计费 (143 方法)
        ├── api_server.py        ← 模型/聊天/部署 (159 方法)
        ├── language_server.py   ← 本地 LS (174 方法)
        ├── extension_server.py  ← 扩展功能 (48 方法)
        ├── plugins.py           ← 插件 (7 方法)
        ├── analytics.py         ← 分析 (17 方法)
        └── misc.py              ← 其他小服务 (8 方法)
```

---

## 常见问题

**Q: API Key 从哪来？**
A: 打开 Windsurf → 登录 → 用本库的 `ws.login_github()` + `ws.register()` 就能拿到。或者从 Windsurf 的本地存储里提取。

**Q: 调用返回 401 / 400 怎么办？**
A: 401 = Key 无效或过期，换一个。400 = 参数不对，看看方法需要什么参数。

**Q: LS 相关的方法报错？**
A: LS 方法需要 Windsurf 正在运行。先确保 Windsurf 开着，然后 `ws.ls.auto_connect()`。

**Q: 需要装什么依赖吗？**
A: 不需要！零依赖，Python 3.8+ 自带的标准库就够了。

---

## 免责声明

本项目**仅供学习和研究**使用。
这是一个非官方的逆向工程项目，与 Windsurf / Codeium 公司无任何关联。
请遵守相关法律法规和服务条款。

## License

[MIT](LICENSE) — 随便用，注明出处就行。

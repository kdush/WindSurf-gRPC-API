<div align="center">

# Windsurf Toolkit

**Windsurf IDE 全功能工具箱 — 单文件 5MB .exe，零依赖**

多协议反代 (OpenAI / Anthropic / Gemini) · Pro 注入 · Key 管理 · 额度监控 · GUI 面板

[![Rust](https://img.shields.io/badge/rust-1.75+-orange?logo=rust)](https://www.rust-lang.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

## 功能

| 模块 | 命令 | 说明 |
|------|------|------|
| **多协议反代** | `proxy` | OpenAI / Anthropic / Gemini 三协议兼容代理，SSE 流式 + 多 Key 轮换 |
| **GUI 面板** | `gui` | 原生桌面面板，集成全部功能（egui） |
| **Pro 注入** | `daemon` | 自动检测本地 LS 进程并注入 Pro 实验 |
| **Key 验证** | `check` | 批量验证 Key 有效性和额度 |
| **额度监控** | `monitor` | 持续监控 Key 额度变化，定时刷新 |
| **用户状态** | `status` | 查看单个 Key 的账号详情 |
| **模型列表** | `models` | 列出所有可用 AI 模型 |

---

## 快速开始

### 启动反代

```bash
# 单 Key
windsurf-toolkit proxy --keys sk-ws-你的key --port 8080

# 多 Key（逗号分隔）
windsurf-toolkit proxy --keys sk-ws-key1,sk-ws-key2,sk-ws-key3

# 从文件加载 Key
windsurf-toolkit proxy --key-file keys.txt --port 8080

# 开启 Web 管理面板 + 认证
windsurf-toolkit proxy --key-file keys.txt --auth my-secret --dashboard
```

面板地址: `http://localhost:8080/dashboard`

### 启动 GUI

```bash
windsurf-toolkit gui
```

---

## 多协议反代

将 Windsurf 后端的 AI 能力包装为三种主流 API 格式，任何协议都能调用全部模型。

### 支持端点

| 协议 | 方法 | 路径 | 流式 | 说明 |
|------|------|------|:----:|------|
| **OpenAI** | POST | `/v1/chat/completions` | ✅ | 聊天补全 |
| **OpenAI** | GET | `/v1/models` | — | 模型列表 |
| **Anthropic** | POST | `/v1/messages` | ✅ | Messages API |
| **Gemini** | POST | `/v1beta/models/{model}:generateContent` | — | 生成内容 |
| **Gemini** | POST | `/v1beta/models/{model}:streamGenerateContent` | ✅ | 流式生成 |
| 通用 | GET | `/v1/status` | — | Key 池状态 |
| 通用 | GET | `/health` | — | 健康检查 |
| 通用 | GET | `/dashboard` | — | Web 管理面板 |

### 认证方式

| 协议 | 认证方式 |
|------|---------|
| OpenAI | `Authorization: Bearer <token>` |
| Anthropic | `x-api-key: <token>` 或 `Authorization: Bearer <token>` |
| Gemini | `?key=<token>` 或 `Authorization: Bearer <token>` |

### 客户端连接

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

---

## 其他命令

### 批量验证 Key

```bash
windsurf-toolkit check --keys sk-ws-key1,sk-ws-key2,sk-ws-key3
windsurf-toolkit check --key-file keys.txt
```

### 额度监控（每 5 分钟）

```bash
windsurf-toolkit monitor --key-file keys.txt --interval 300
```

### 查看用户状态

```bash
windsurf-toolkit status sk-ws-你的key
```

### Pro 注入守护

```bash
windsurf-toolkit daemon --key sk-ws-你的key --interval 30
```

---

## 支持模型

| 厂商 | 模型 |
|------|------|
| **Anthropic** | Claude Sonnet 4, Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3.7 Sonnet |
| **OpenAI** | GPT-4o, GPT-4o Mini, GPT-4.1, o3, o3-mini, o4-mini |
| **Google** | Gemini 2.5 Pro, Gemini 2.0 Flash, Gemini 2.5 Flash |
| **xAI** | Grok 3, Grok 3 Mini |
| **DeepSeek** | DeepSeek V3, DeepSeek R1 |

---

## 架构

```
windsurf-toolkit (单文件 .exe)
│
├── proxy/            多协议反代服务器
│   ├── server.rs     axum 路由 + 状态管理
│   ├── streaming.rs  Windsurf → SSE 流式转换
│   ├── anthropic.rs  Anthropic Messages API 兼容层
│   ├── gemini.rs     Gemini API 兼容层
│   ├── key_pool.rs   Key 池 (轮换 + 冷却 + 健康检查)
│   └── models_map.rs 模型名称映射
│
├── client/           Windsurf Connect 协议客户端
│   ├── transport.rs  gRPC-over-HTTP 传输层
│   └── models.rs     请求/响应模型
│
├── gui/              原生桌面面板 (egui)
│   ├── app.rs        应用主框架
│   ├── pages/        功能页面 (12 页)
│   ├── theme.rs      主题样式
│   └── widgets.rs    自定义组件
│
├── daemon/           Pro 实验注入守护
├── monitor/          额度监控
└── web/              Web Dashboard
```

## Key 文件格式

```text
# 每行一个 Key，# 开头为注释
sk-ws-key-001
sk-ws-key-002
sk-ws-key-003
```

也可以用环境变量: `WINDSURF_KEYS=sk-ws-key1,sk-ws-key2`

## 构建

```bash
cargo build --release
# 产物: target/release/windsurf-toolkit.exe (~5.4 MB)
```

## 技术栈

| 组件 | 依赖 | 说明 |
|------|------|------|
| 异步运行时 | tokio | 全特性 async runtime |
| HTTP 服务器 | axum + tower-http | 路由 + CORS |
| HTTP 客户端 | reqwest | TLS + 流式 |
| 序列化 | serde + serde_json | JSON 处理 |
| CLI | clap | 命令行解析 |
| GUI | eframe + egui | 原生桌面界面 |
| 日志 | tracing | 结构化日志 |

## License

[MIT](LICENSE)

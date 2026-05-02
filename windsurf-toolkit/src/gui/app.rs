use eframe::egui::{self, RichText, Vec2, CornerRadius, Stroke, Sense, Color32, CursorIcon};
use std::sync::{Arc, Mutex};
use crate::gui::theme::*;
use crate::gui::icons;
use crate::gui::config::Config;
use crate::gui::key_detector;
#[cfg(windows)]
use crate::gui::csrf_finder;
use crate::proxy::{models_map, server as proxy_server};
use crate::client::WindsurfClient;
use crate::daemon::injector;

/// 异步任务完成后发送的事件
#[derive(Debug, Clone)]
pub enum AsyncEvent {
    KeyChecked { key: String, healthy: bool, plan: String, credits: Option<i64>, message: String, status_json: Option<serde_json::Value> },
    ApiResult { label: String, ok: bool, status: u16, body: String },
    ModelsRefreshed { models: Vec<ModelInfo>, source: String },
}

/// 事件队列 (异步任务 → UI 线程)
pub type EventQueue = Arc<Mutex<Vec<AsyncEvent>>>;

// ═══════════════════════════════════════
//  页面枚举
// ═══════════════════════════════════════
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Page {
    Dashboard,
    Proxy,
    Keys,
    UserStatus,
    Models,
    Monitor,
    Inject,
    Account,
    Team,
    Mcp,
    Settings,
}

// ═══════════════════════════════════════
//  数据结构
// ═══════════════════════════════════════
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum KeySource {
    /// 用户手动添加
    Manual,
    /// 从 Windsurf 编辑器自动检测
    Windsurf,
    /// 从文件导入
    File,
}

/// 当前 Unix 时间戳 (秒)
pub fn now_unix() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs() as i64)
        .unwrap_or(0)
}

#[derive(Debug, Clone)]
pub struct KeyInfo {
    pub full_key: String,
    pub preview: String,
    pub healthy: bool,
    pub calls: u64,
    pub errors: u64,
    pub credits: Option<i64>,
    pub plan: String,
    /// 完整的 GetUserStatus 响应 (用于详细信息展示)
    pub status_json: Option<serde_json::Value>,
    /// Key 来源标记 (用于区分自动同步/手动添加)
    pub source: KeySource,
    /// 是否是 Windsurf 当前正在使用的活跃 Key
    pub is_active: bool,
    /// 最后一次从 Windsurf 检测到的时间戳 (秒)
    pub last_detected_unix: Option<i64>,
}

#[derive(Debug, Clone)]
pub struct ModelInfo {
    pub name: String,
    pub provider: String,
}

/// 根据模型名/UID 猜测厂商
pub fn guess_provider(label: &str, uid: &str) -> String {
    let s = format!("{} {}", label, uid).to_lowercase();
    if s.contains("claude") || s.contains("anthropic") { "anthropic".to_string() }
    else if s.contains("gpt") || s.contains("o3") || s.contains("o4") || s.contains("openai") || s.contains("codex") { "openai".to_string() }
    else if s.contains("gemini") || s.contains("google") { "google".to_string() }
    else if s.contains("grok") || s.contains("xai") { "xai".to_string() }
    else if s.contains("deepseek") { "deepseek".to_string() }
    else if s.contains("qwen") { "qwen".to_string() }
    else if s.contains("kimi") || s.contains("moonshot") { "moonshot".to_string() }
    else if s.contains("glm") || s.contains("zhipu") { "zhipu".to_string() }
    else if s.contains("private") || s.contains("windsurf") { "windsurf".to_string() }
    else { "?".to_string() }
}

/// 从 Windsurf LS 二进制提取所有 MODEL_* 枚举 (约 200+ 个)
/// 扫描 NUL 分隔的 C 字符串, 过滤干净的模型名
pub fn read_models_from_ls_binary() -> Option<Vec<ModelInfo>> {
    let candidates = [
        r"D:\Windsurf\resources\app\extensions\windsurf\bin\language_server_windows_x64.exe",
        r"C:\Program Files\Windsurf\resources\app\extensions\windsurf\bin\language_server_windows_x64.exe",
    ];
    let path = candidates.iter().find(|p| std::path::Path::new(p).exists())?;
    let bytes = std::fs::read(path).ok()?;

    // NUL 分隔扫描: 只在 NUL 边界处开始/结束匹配 (避免相邻字符串拼接成长串)
    let mut found = std::collections::HashSet::new();
    let needle = b"MODEL_";
    let valid_prefixes: &[&str] = &[
        "CLAUDE_", "GPT_", "GOOGLE_", "XAI_", "DEEPSEEK_", "QWEN_", "MOONSHOT_",
        "GLM_", "MINIMAX_", "LLAMA_", "CODEMAP_", "CASCADE_", "COGNITION_",
        "CHAT_", "PRIVATE_", "SWE_", "ALIAS_", "DEVIN_", "CODESTRAL_", "MISTRAL_",
        "KIMI_", "O3_", "O4_", "O1_", "GROK_", "GEMINI_", "AMAZON_", "LIFEGUARD_",
        "EMBEDDING_", "WHISPER_", "NOVA_",
    ];

    // 连接噪声片段 (这些出现在字符串里意味着它是拼接的垃圾)
    let noise_markers = ["VARIANTS", "LANGUAGE_", "SUPERCOMPLETE", "TREE_SITTER", "COMPLETION_SPEED"];

    let mut i = 0;
    while i + needle.len() <= bytes.len() {
        if &bytes[i..i+needle.len()] == needle {
            // 要求前一字节是字符串边界 (NUL / 低控制字符 / 非字母数字下划线)
            let at_boundary = i == 0 || {
                let prev = bytes[i - 1];
                !(prev.is_ascii_alphanumeric() || prev == b'_')
            };
            if !at_boundary {
                i += needle.len();
                continue;
            }
            let start = i;
            let mut end = i + needle.len();
            while end < bytes.len() && end - start < 70 {
                let c = bytes[end];
                if c.is_ascii_uppercase() || c.is_ascii_digit() || c == b'_' {
                    end += 1;
                } else {
                    break;
                }
            }
            let len = end - start;
            if len >= 10 && len <= 70 {
                if let Ok(s) = std::str::from_utf8(&bytes[start..end]) {
                    let suffix = &s[6..];
                    if valid_prefixes.iter().any(|p| suffix.starts_with(p))
                        && !s.ends_with("_UNSPECIFIED") && !s.ends_with("_UNKNOWN")
                        && !s.ends_with("_INVALID") && !s.ends_with("_DEFAULT")
                        && !noise_markers.iter().any(|m| s.contains(m))
                        // 排除 MODEL_CASCADE_NNNNN (纯数字尾缀,非真实模型)
                        && !(s.starts_with("MODEL_CASCADE_") && s[14..].chars().all(|c| c.is_ascii_digit()))
                        && !(s.starts_with("MODEL_CHAT_") && s[11..].chars().all(|c| c.is_ascii_digit()))
                    {
                        found.insert(s.to_string());
                    }
                }
            }
            i = end;
        } else {
            i += 1;
        }
    }

    let mut result: Vec<_> = found.into_iter().map(|name| {
        let provider = guess_provider(&name, &name);
        ModelInfo { name, provider }
    }).collect();
    result.sort_by(|a, b| a.name.cmp(&b.name));
    Some(result)
}

/// 从本地 user_settings.pb 提取所有 MODEL_* 枚举值 (兜底)
pub fn read_models_from_settings_pb() -> Option<Vec<ModelInfo>> {
    let userprofile = std::env::var("USERPROFILE").ok()?;
    let pb_path = std::path::PathBuf::from(userprofile).join(".codeium").join("windsurf").join("user_settings.pb");
    let bytes = std::fs::read(&pb_path).ok()?;
    let text = String::from_utf8_lossy(&bytes);
    let mut found = std::collections::HashSet::new();
    let bytes_t = text.as_bytes();
    let needle = b"MODEL_";
    let mut i = 0;
    while i + needle.len() <= bytes_t.len() {
        if &bytes_t[i..i+needle.len()] == needle {
            let start = i;
            let mut end = i + needle.len();
            while end < bytes_t.len() {
                let c = bytes_t[end];
                if c.is_ascii_uppercase() || c.is_ascii_digit() || c == b'_' {
                    end += 1;
                } else { break; }
            }
            let len = end - start;
            // 合理长度 8-80
            if len >= 8 && len <= 80 {
                if let Ok(s) = std::str::from_utf8(&bytes_t[start..end]) {
                    // 排除 MODEL_UNSPECIFIED 等
                    if !s.ends_with("_UNSPECIFIED") && !s.ends_with("_UNKNOWN") {
                        found.insert(s.to_string());
                    }
                }
            }
            i = end;
        } else {
            i += 1;
        }
    }
    let mut result: Vec<_> = found.into_iter().map(|name| {
        let provider = guess_provider(&name, &name);
        ModelInfo { name, provider }
    }).collect();
    result.sort_by(|a, b| a.name.cmp(&b.name));
    Some(result)
}

// ═══════════════════════════════════════
//  应用状态
// ═══════════════════════════════════════
pub struct AppState {
    pub current_page: Page,
    pub keys: Vec<KeyInfo>,
    pub models: Vec<ModelInfo>,
    pub new_key_input: String,

    // Proxy
    pub proxy_running: bool,
    pub proxy_host: String,
    pub proxy_port: u16,
    pub auth_token: String,
    pub server_url: String,
    pub cooldown_secs: u64,
    pub max_errors: u32,

    // Monitor
    pub monitor_running: bool,
    pub monitor_interval: u64,

    // Pro 注入
    pub inject_running: bool,
    pub inject_check_interval: u32,
    pub inject_status: String,

    // 账号
    pub login_email: String,
    pub login_password: String,
    pub login_github_token: String,
    pub login_status: String,
    pub registered_keys: Vec<String>,

    // 用户状态
    pub user_status_key: String,
    pub user_status_result: String,

    // 解析后的真实用户信息 (来自 GetUserStatus)
    pub parsed_user_name: String,
    pub parsed_user_email: String,
    pub parsed_user_id: String,
    pub parsed_user_team: String,
    pub parsed_user_tier: String,
    pub parsed_user_plan: String,
    pub parsed_user_billing: String,
    pub parsed_credits_prompt: i64,
    pub parsed_credits_flow: i64,
    pub parsed_user_loaded: bool,

    // 团队
    pub team_name_input: String,
    pub team_info_result: String,
    pub team_id_input: String,
    pub team_email_input: String,
    pub team_domain_input: String,
    pub internal_secret: String,
    pub team_billing_result: String,
    pub team_members_result: String,
    pub team_role_input: String,

    // MCP
    pub mcp_result: String,
    pub mcp_server_id: String,
    pub mcp_tool_name: String,
    pub mcp_plugin_result: String,
    pub mcp_server_result: String,
    pub mcp_config_json: String,

    // 订阅 / 计费
    pub subscription_result: String,
    pub billing_result: String,

    // SSO
    pub sso_email: String,
    pub sso_result: String,

    // LS 状态
    pub ls_port: u16,
    pub ls_connected: bool,
    pub ls_status: String,
    pub ls_csrf_token: String,

    // 注入详情
    pub inject_log: Vec<String>,

    // 推荐码
    pub referral_code: String,
    pub referral_result: String,

    // 日志
    pub log_messages: Vec<String>,
    pub total_requests: u64,

    // 异步事件队列 + Tokio runtime
    pub events: EventQueue,
    pub runtime: Option<Arc<tokio::runtime::Runtime>>,
    pub dirty: bool,  // 是否需要保存配置

    // 实时 API 结果显示 (用于在页面内显示最近的调用结果)
    pub api_result_label: String,
    pub api_result_text: String,
    pub api_result_ok: bool,

    // 实际运行的任务句柄 (用于 abort)
    pub proxy_task: Option<tokio::task::AbortHandle>,
    pub inject_task: Option<tokio::task::AbortHandle>,

    // UI 临时状态
    pub keys_reveal_idx: Option<usize>,  // 当前展开显示的 Key 索引
    pub auto_refreshed_models: bool,     // 是否已自动从 API 刷新过模型列表

    // ── 密钥池实时同步 (与 Windsurf 编辑器 Key 同步) ──
    pub auto_sync_keys: bool,            // 开启自动同步 Windsurf 当前 Key
    pub key_sync_interval_secs: u64,     // 同步间隔 (秒, 默认 10)
    pub last_key_sync_unix: i64,         // 上次同步时间
    pub active_key_full: String,         // 检测到的 Windsurf 当前活跃 Key

    // API 结果弹窗
    pub show_result_modal: bool,
    pub result_modal_pending: bool,      // 等待 API 响应中
    pub result_modal_show_raw: bool,     // 是否在弹窗内展开原始 JSON
    pub result_modal_label: String,      // 弹窗标题 (用户点击的按钮名)
}

impl Default for AppState {
    fn default() -> Self {
        let models = models_map::list_models()
            .iter()
            .map(|m| ModelInfo {
                name: m.id.clone(),
                provider: m.owned_by.clone(),
            })
            .collect();

        Self {
            current_page: Page::Dashboard,
            keys: Vec::new(),
            models,
            new_key_input: String::new(),
            proxy_running: false,
            proxy_host: "0.0.0.0".to_string(),
            proxy_port: 8080,
            auth_token: String::new(),
            server_url: "https://server.self-serve.windsurf.com".to_string(),
            cooldown_secs: 60,
            max_errors: 10,
            monitor_running: false,
            monitor_interval: 300,
            inject_running: false,
            inject_check_interval: 30,
            inject_status: "未启动".to_string(),
            login_email: String::new(),
            login_password: String::new(),
            login_github_token: String::new(),
            login_status: String::new(),
            registered_keys: Vec::new(),
            user_status_key: String::new(),
            user_status_result: String::new(),
            parsed_user_name: String::new(),
            parsed_user_email: String::new(),
            parsed_user_id: String::new(),
            parsed_user_team: String::new(),
            parsed_user_tier: String::new(),
            parsed_user_plan: String::new(),
            parsed_user_billing: String::new(),
            parsed_credits_prompt: 0,
            parsed_credits_flow: 0,
            parsed_user_loaded: false,
            team_name_input: String::new(),
            team_info_result: String::new(),
            team_id_input: String::new(),
            team_email_input: String::new(),
            team_domain_input: String::new(),
            internal_secret: String::new(),
            team_billing_result: String::new(),
            team_members_result: String::new(),
            team_role_input: String::new(),
            mcp_result: String::new(),
            mcp_server_id: String::new(),
            mcp_tool_name: String::new(),
            mcp_plugin_result: String::new(),
            mcp_server_result: String::new(),
            mcp_config_json: String::new(),
            subscription_result: String::new(),
            billing_result: String::new(),
            sso_email: String::new(),
            sso_result: String::new(),
            ls_port: 0,
            ls_connected: false,
            ls_status: "未连接".to_string(),
            ls_csrf_token: String::new(),
            inject_log: Vec::new(),
            referral_code: String::new(),
            referral_result: String::new(),
            log_messages: vec!["Windsurf Toolkit 已启动".to_string()],
            total_requests: 0,
            events: Arc::new(Mutex::new(Vec::new())),
            runtime: None,
            dirty: false,
            api_result_label: String::new(),
            api_result_text: String::new(),
            api_result_ok: false,
            proxy_task: None,
            inject_task: None,
            keys_reveal_idx: None,
            auto_refreshed_models: false,
            auto_sync_keys: true,
            key_sync_interval_secs: 10,
            last_key_sync_unix: 0,
            active_key_full: String::new(),
            show_result_modal: false,
            result_modal_pending: false,
            result_modal_show_raw: false,
            result_modal_label: String::new(),
        }
    }
}

impl AppState {
    /// 从持久化配置加载
    pub fn apply_config(&mut self, cfg: &Config) {
        self.proxy_host = cfg.proxy_host.clone();
        self.proxy_port = cfg.proxy_port;
        self.server_url = cfg.server_url.clone();
        self.auth_token = cfg.auth_token.clone();
        self.cooldown_secs = cfg.cooldown_secs;
        self.max_errors = cfg.max_errors;
        self.monitor_interval = cfg.monitor_interval;
        self.inject_check_interval = cfg.inject_check_interval;
        self.ls_port = cfg.ls_port;
        self.internal_secret = cfg.internal_secret.clone();

        self.keys = cfg.keys.iter().map(|k| {
            let preview = if k.len() > 16 {
                format!("{}...{}", &k[..12], &k[k.len()-4..])
            } else { k.clone() };
            KeyInfo {
                full_key: k.clone(),
                preview,
                healthy: true,
                calls: 0,
                errors: 0,
                credits: None,
                plan: String::new(),
                status_json: None,
                source: KeySource::Manual,
                is_active: false,
                last_detected_unix: None,
            }
        }).collect();
    }

    /// 导出为配置
    pub fn export_config(&self) -> Config {
        Config {
            keys: self.keys.iter().map(|k| k.full_key.clone()).collect(),
            proxy_host: self.proxy_host.clone(),
            proxy_port: self.proxy_port,
            server_url: self.server_url.clone(),
            auth_token: self.auth_token.clone(),
            cooldown_secs: self.cooldown_secs,
            max_errors: self.max_errors,
            monitor_interval: self.monitor_interval,
            inject_check_interval: self.inject_check_interval,
            ls_port: self.ls_port,
            internal_secret: self.internal_secret.clone(),
        }
    }

    /// 标记需要保存配置
    pub fn mark_dirty(&mut self) {
        self.dirty = true;
    }

    /// 推送日志 + 标记需要保存
    pub fn log(&mut self, msg: impl Into<String>) {
        let msg = msg.into();
        self.log_messages.push(msg);
        if self.log_messages.len() > 500 {
            self.log_messages.drain(0..100);
        }
    }

    /// 异步校验 Key (调用 GetUserStatus + 解析 Plan/Credits)
    pub fn check_key_async(&self, key: String) {
        let Some(runtime) = self.runtime.clone() else { return };
        let events = self.events.clone();
        let server = self.server_url.clone();
        runtime.spawn(async move {
            let client = WindsurfClient::new(&server, &key);
            let resp = client.get_user_status().await;

            // 真实路径: planName 在 /planInfo/planName, 配额在 /planInfo/monthlyPromptCredits + monthlyFlowCredits
            let plan = resp.data.pointer("/planInfo/planName")
                .and_then(|v| v.as_str())
                .map(|s| s.to_string())
                .or_else(|| resp.data.pointer("/planInfo/teamsTier").and_then(|v| v.as_str()).map(|s| s.replace("TEAMS_TIER_", "").replace("_", " ")))
                .unwrap_or_default();

            // 累加 prompt + flow credits 作为剩余总额度
            let prompt_credits = resp.data.pointer("/planInfo/monthlyPromptCredits").and_then(|v| v.as_i64());
            let flow_credits = resp.data.pointer("/planInfo/monthlyFlowCredits").and_then(|v| v.as_i64());
            let credits = match (prompt_credits, flow_credits) {
                (Some(p), Some(f)) => Some(p + f),
                (Some(p), None) => Some(p),
                (None, Some(f)) => Some(f),
                (None, None) => None,
            };

            let event = AsyncEvent::KeyChecked {
                key: key.clone(),
                healthy: resp.ok,
                plan,
                credits,
                status_json: if resp.ok { Some(resp.data.clone()) } else { None },
                message: if resp.ok {
                    format!("✓ Key 有效 (HTTP {})", resp.status)
                } else {
                    format!("✗ Key 无效 (HTTP {}): {}", resp.status, resp.data)
                },
            };
            if let Ok(mut q) = events.lock() { q.push(event); }
        });
    }

    /// 启动实际的代理服务器
    pub fn start_proxy_real(&mut self) -> bool {
        if self.keys.is_empty() {
            self.log("⚠ 未配置密钥，无法启动代理");
            return false;
        }
        let Some(runtime) = self.runtime.clone() else {
            self.log("⚠ Runtime 未就绪");
            return false;
        };
        let keys: Vec<String> = self.keys.iter().map(|k| k.full_key.clone()).collect();
        let port = self.proxy_port;
        let host = self.proxy_host.clone();
        let server = self.server_url.clone();
        let auth = if self.auth_token.is_empty() { None } else { Some(self.auth_token.clone()) };
        let cooldown = self.cooldown_secs;
        let max_errors = self.max_errors;

        let handle = runtime.spawn(async move {
            proxy_server::start_proxy(keys, port, &host, &server, auth, cooldown, max_errors).await;
        });
        self.proxy_task = Some(handle.abort_handle());
        self.proxy_running = true;
        self.log(format!("✓ 代理服务已启动 → http://{}:{}", self.proxy_host, self.proxy_port));
        true
    }

    /// 停止代理
    pub fn stop_proxy_real(&mut self) {
        if let Some(handle) = self.proxy_task.take() {
            handle.abort();
            self.proxy_running = false;
            self.log("代理服务已停止");
        }
    }

    /// 启动 Pro 注入守护
    pub fn start_inject_real(&mut self) -> bool {
        let key = self.keys.iter().find(|k| k.healthy).map(|k| k.full_key.clone());
        let Some(key) = key else {
            self.log("⚠ 未配置有效密钥，无法启动注入守护");
            return false;
        };
        let Some(runtime) = self.runtime.clone() else {
            self.log("⚠ Runtime 未就绪");
            return false;
        };
        let interval = self.inject_check_interval as u64;

        let handle = runtime.spawn(async move {
            injector::start_daemon(&key, interval).await;
        });
        self.inject_task = Some(handle.abort_handle());
        self.inject_running = true;
        self.inject_status = "守护运行中".to_string();
        self.log("✓ Pro 注入守护已启动");
        true
    }

    /// 停止 Pro 注入守护
    pub fn stop_inject_real(&mut self) {
        if let Some(handle) = self.inject_task.take() {
            handle.abort();
            self.inject_running = false;
            self.inject_status = "已停止".to_string();
            self.log("Pro 注入守护已停止");
        }
    }

    /// 异步自动发现 LS 进程 (端口 + CSRF) — 真实调用
    pub fn discover_ls_async(&self) {
        let Some(runtime) = self.runtime.clone() else { return };
        let events = self.events.clone();
        runtime.spawn(async move {
            // 步骤 1: 用 tasklist 找所有 windsurf/LS 进程 PID (不需要管理员权限)
            let tl_output = tokio::process::Command::new("tasklist")
                .args(["/FO", "CSV", "/NH"])
                .output().await;

            let mut target_pids: Vec<u32> = Vec::new();
            let mut debug_info = String::new();

            if let Ok(o) = &tl_output {
                let stdout = String::from_utf8_lossy(&o.stdout);
                for line in stdout.lines() {
                    let lower = line.to_lowercase();
                    // 只找 LS 进程 (language_server_*) — 排除 Windsurf 渲染进程
                    // 渲染进程也监听端口但走的是 extension.js 的 HTTP server, CSRF 来源不同
                    if lower.contains("language_server") {
                        // CSV 格式: "name.exe","PID","Services","..."
                        let parts: Vec<&str> = line.split("\",\"").collect();
                        if parts.len() >= 2 {
                            if let Ok(pid) = parts[1].trim_matches('"').parse::<u32>() {
                                target_pids.push(pid);
                            }
                        }
                    }
                }
                debug_info.push_str(&format!("tasklist: 找到 {} 个 LS 进程 (PIDs={:?}); ",
                    target_pids.len(),
                    target_pids.iter().take(5).collect::<Vec<_>>()));
            } else {
                debug_info.push_str("tasklist 执行失败; ");
            }

            // 步骤 2: 用 netstat -ano 获取所有监听端口 + 端口->PID 映射
            let ns_output = tokio::process::Command::new("netstat")
                .args(["-ano", "-p", "TCP"])
                .output().await;

            let mut ports: Vec<u16> = Vec::new();
            let mut port_to_pid: std::collections::HashMap<u16, u32> = std::collections::HashMap::new();
            if let Ok(o) = &ns_output {
                let stdout = String::from_utf8_lossy(&o.stdout);
                for line in stdout.lines() {
                    let trimmed = line.trim();
                    if !trimmed.contains("LISTENING") { continue; }
                    let parts: Vec<&str> = trimmed.split_whitespace().collect();
                    if parts.len() < 5 { continue; }
                    let local_addr = parts[1];
                    let pid_str = parts[parts.len() - 1];
                    let pid: u32 = match pid_str.parse() { Ok(p) => p, Err(_) => continue };
                    if !target_pids.contains(&pid) { continue; }
                    if !local_addr.starts_with("127.0.0.1:") && !local_addr.starts_with("0.0.0.0:")
                        && !local_addr.starts_with("[::]:") && !local_addr.starts_with("[::1]:") {
                        continue;
                    }
                    if let Some(port_s) = local_addr.rsplit(':').next() {
                        if let Ok(p) = port_s.parse::<u16>() {
                            if p > 1024 && p < 65000 && !ports.contains(&p) {
                                ports.push(p);
                                port_to_pid.insert(p, pid);
                            }
                        }
                    }
                }
                debug_info.push_str(&format!("netstat: 发现 {} 个监听端口 = {:?}", ports.len(), ports));
            } else {
                debug_info.push_str("netstat 执行失败");
            }

            ports.sort();
            let port_str = ports.iter().map(|p| p.to_string()).collect::<Vec<_>>().join(",");

            // CSRF Token: 探测 LS 端口成功后会从对应 PID 内存中提取
            let mut token = String::new();
            let _ = &port_to_pid; // 用于后续 CSRF 提取

            // 尝试每个端口的 Heartbeat — LS 即使返回 401/403 (缺 CSRF) 也算「LS 存活」
            let client = reqwest::Client::builder()
                .timeout(std::time::Duration::from_secs(3))
                .build().unwrap();
            let mut found_port: u16 = 0;
            let mut found_status: u16 = 0;
            let ls_service = "exa.language_server_pb.LanguageServerService";
            for p in port_str.split(',').filter_map(|s| s.trim().parse::<u16>().ok()) {
                let url = format!("http://127.0.0.1:{}/{}/Heartbeat", p, ls_service);
                let mut req = client.post(&url).header("Content-Type", "application/json")
                    .header("Connect-Protocol-Version", "1");
                if !token.is_empty() {
                    req = req.header("x-codeium-csrf-token", &token);
                }
                let body = serde_json::json!({"metadata": {}}).to_string();
                if let Ok(resp) = req.body(body).send().await {
                    let s = resp.status().as_u16();
                    // 200 OK / 401 missing CSRF / 403 invalid CSRF / 412 protocol mismatch — 都说明这是 LS
                    if s == 200 || s == 401 || s == 403 || s == 412 {
                        // 进一步验证: 必须是 connect-rpc 错误格式 (含 'unauthenticated' 或 JSON)
                        let txt = resp.text().await.unwrap_or_default();
                        if s == 200 || txt.contains("unauthenticated") || txt.contains("CSRF") || txt.contains("\"code\"") {
                            found_port = p;
                            found_status = s;
                            break;
                        }
                    }
                }
            }

            // 步骤 3: 从 LS 进程的环境变量读取 CSRF Token (需管理员权限)
            #[cfg(windows)]
            if found_port > 0 {
                if let Some(&pid) = port_to_pid.get(&found_port) {
                    debug_info.push_str(&format!(" · 读取 PID {} 环境变量...", pid));
                    if let Some(csrf) = csrf_finder::find_csrf_for_ls(pid, found_port).await {
                        token = csrf;
                        debug_info.push_str(" ✓ WINDSURF_CSRF_TOKEN");
                    } else {
                        debug_info.push_str(" ✗ 未读到 CSRF (可能非管理员运行)");
                    }
                }
            }

            let csrf_status = if !token.is_empty() {
                format!("已读取 · UUID {}", token)
            } else {
                "未读取 (需要 Administrator 权限读取 LS 进程内存)".to_string()
            };

            let (label, body, ok) = if found_port > 0 {
                let body = serde_json::json!({
                    "port": found_port,
                    "csrf": token,
                    "csrf_status": csrf_status,
                    "ls_status_code": found_status,
                    "ls_responded": true,
                    "scanned_ports": port_str,
                    "connected": true,
                    "note": if token.is_empty() {
                        "LS 已检测到但 CSRF Token 未获取 · 注入操作需要 CSRF (受限)"
                    } else {
                        "LS 完整连接 · 可执行注入"
                    }
                }).to_string();
                (format!("LS 探测 · 端口 {} (HTTP {})", found_port, found_status), body, true)
            } else if !port_str.is_empty() {
                let body = serde_json::json!({
                    "connected": false,
                    "scanned_ports": port_str,
                    "reason": "进程在监听但端口未响应 LS gRPC · 可能不是 LS 端口",
                    "_debug": debug_info
                }).to_string();
                ("LS 探测 · 端口未响应".to_string(), body, false)
            } else {
                let body = serde_json::json!({
                    "connected": false,
                    "reason": "未找到运行中的 Windsurf LS 进程",
                    "_debug": debug_info,
                    "hint": "请检查 PowerShell 是否能访问 Get-NetTCPConnection (需要管理员权限读取非本进程端口)"
                }).to_string();
                ("LS 探测 · 未找到".to_string(), body, false)
            };

            if let Ok(mut q) = events.lock() {
                q.push(AsyncEvent::ApiResult {
                    label,
                    ok,
                    status: if ok { found_status } else { 0 },
                    body,
                });
            }
        });
    }

    /// 调用本地 LS RPC (通用) — 自动注入 metadata 和 CSRF
    pub fn call_ls_async(&self, label: String, method: String, mut payload: serde_json::Value) {
        let Some(runtime) = self.runtime.clone() else { return };
        let events = self.events.clone();
        let port = self.ls_port;
        let csrf = self.ls_csrf_token.clone();
        // 取第一个健康的 API key 作为 metadata.apiKey
        let api_key = self.keys.iter().find(|k| k.healthy)
            .or_else(|| self.keys.first())
            .map(|k| k.full_key.clone())
            .unwrap_or_default();

        // 如果 payload 是 object 且没有 metadata 字段, 自动注入
        if let Some(obj) = payload.as_object_mut() {
            if !obj.contains_key("metadata") {
                obj.insert("metadata".to_string(), serde_json::json!({
                    "ideName": "WINDSURF",
                    "ideVersion": "1.112.0",
                    "extensionName": "windsurf",
                    "extensionVersion": "1.112.0",
                    "apiKey": api_key,
                    "locale": "en",
                    "sessionId": uuid::Uuid::new_v4().to_string(),
                }));
            }
        }

        runtime.spawn(async move {
            if port == 0 {
                if let Ok(mut q) = events.lock() {
                    q.push(AsyncEvent::ApiResult {
                        label,
                        ok: false,
                        status: 0,
                        body: "{\"error\":\"LS 端口未配置 · 请先点击「自动检测 LS」\"}".to_string(),
                    });
                }
                return;
            }
            let client = reqwest::Client::builder()
                .timeout(std::time::Duration::from_secs(10))
                .build().unwrap();
            let url = format!("http://127.0.0.1:{}/exa.language_server_pb.LanguageServerService/{}", port, method);
            let mut req = client.post(&url)
                .header("Content-Type", "application/json")
                .header("Connect-Protocol-Version", "1");
            if !csrf.is_empty() {
                req = req.header("x-codeium-csrf-token", &csrf);
            }
            let resp = req.json(&payload).send().await;
            let event = match resp {
                Ok(r) => {
                    let status = r.status().as_u16();
                    let ok = r.status().is_success();
                    let body = r.text().await.unwrap_or_default();
                    AsyncEvent::ApiResult { label, ok, status, body }
                }
                Err(e) => AsyncEvent::ApiResult {
                    label,
                    ok: false,
                    status: 0,
                    body: format!("{{\"error\":\"{}\"}}", e),
                }
            };
            if let Ok(mut q) = events.lock() { q.push(event); }
        });
    }

    /// 一键注入 Pro 实验 — 真实调用 SetBaseExperiments
    pub fn inject_pro_async(&self) {
        // 数字 ExperimentKey: 强制启用 Cascade 高级特性, 禁用配额
        let payload = serde_json::json!({
            "forceDisableExperiments": [204],  // CASCADE_ENFORCE_QUOTA
            "forceEnableExperiments": [
                266,  // CASCADE_PLAN_BASED_CONFIG_OVERRIDE
                245,  // CASCADE_ENABLE_MCP_TOOLS
                300,  // CASCADE_WEB_APP_DEPLOYMENTS_ENABLED
                290,  // CASCADE_ENABLE_PROXY_WEB_SERVER
                224,  // CASCADE_ENABLE_AUTOMATED_MEMORIES
                328,  // CASCADE_WINDSURF_BROWSER_TOOLS_ENABLED
            ]
        });
        self.call_ls_async("注入 Pro 实验".into(), "SetBaseExperiments".into(), payload);
    }

    /// 清除注入的实验
    pub fn clear_experiments_async(&self) {
        let payload = serde_json::json!({
            "forceDisableExperiments": [],
            "forceEnableExperiments": []
        });
        self.call_ls_async("清除注入".into(), "SetBaseExperiments".into(), payload);
    }

    /// 查询当前实验状态 (LS 没有 GetBaseExperiments, 使用 GetUserSettings)
    pub fn query_experiments_async(&self) {
        let payload = serde_json::json!({});
        self.call_ls_async("查询实验".into(), "GetUserSettings".into(), payload);
    }

    /// LS 心跳 / 状态
    pub fn ls_heartbeat_async(&self) {
        self.call_ls_async("LS 心跳".into(), "Heartbeat".into(), serde_json::json!({}));
    }

    /// 从 Windsurf 编辑器自动检测并导入 API Key
    /// 返回 (新增数, 检测到总数, 来源说明)
    pub fn detect_and_import_keys(&mut self) -> (usize, usize, String) {
        let result = key_detector::detect_windsurf_keys();
        let total = result.keys.len();
        let mut added = 0;

        for key in &result.keys {
            if !self.keys.iter().any(|k| &k.full_key == key) {
                let preview = if key.len() > 16 {
                    format!("{}...{}", &key[..12], &key[key.len()-4..])
                } else { key.clone() };
                self.keys.push(KeyInfo {
                    full_key: key.clone(),
                    preview,
                    healthy: true,
                    calls: 0,
                    errors: 0,
                    credits: None,
                    plan: String::new(),
                    status_json: None,
                    source: KeySource::Windsurf,
                    is_active: false,
                    last_detected_unix: Some(now_unix()),
                });
                added += 1;
                // 自动后台校验
                self.check_key_async(key.clone());
            }
        }

        if added > 0 {
            self.mark_dirty();
        }

        let source = if total == 0 {
            format!("未找到 Windsurf API Key (扫描了 {} 个位置)", result.scanned.len())
        } else if !result.found_in.is_empty() {
            format!("从 {} 检测到 {} 个 Key", result.found_in[0], total)
        } else {
            format!("检测到 {} 个 Key", total)
        };

        self.log(format!("自动检测: {} (新增 {})", source, added));
        (added, total, source)
    }

    /// 异步刷新模型列表 (聚合调用 GetCascadeModelConfigs / GetCliModelConfigs / GetCommandModelConfigs)
    pub fn refresh_models_async(&self) {
        let key = self.keys.iter().find(|k| k.healthy).map(|k| k.full_key.clone());
        let Some(key) = key else { return };
        let Some(runtime) = self.runtime.clone() else { return };
        let events = self.events.clone();
        let server = self.server_url.clone();
        runtime.spawn(async move {
            let client = WindsurfClient::new(&server, &key);

            // 三个 RPC 并行调用，合并去重
            let payload_cli = serde_json::json!({ "metadata": client.metadata() });
            let payload_cmd = serde_json::json!({ "metadata": client.metadata() });
            let (cascade, cli, cmd) = tokio::join!(
                client.get_cascade_model_configs(),
                client.call("api_server_pb.ApiServerService", "GetCliModelConfigs", &payload_cli),
                client.call("api_server_pb.ApiServerService", "GetCommandModelConfigs", &payload_cmd),
            );

            let mut models = Vec::new();
            let mut seen = std::collections::HashSet::new();

            for (resp, source_label) in [(cascade, "cascade"), (cli, "cli"), (cmd, "command")] {
                if !resp.ok { continue }
                if let Some(arr) = resp.data.get("clientModelConfigs").and_then(|v| v.as_array()) {
                    for cfg in arr {
                        let uid = cfg.get("modelUid").and_then(|v| v.as_str()).unwrap_or("");
                        let label = cfg.get("label").and_then(|v| v.as_str()).unwrap_or(uid);
                        if uid.is_empty() { continue; }
                        if !seen.insert(uid.to_string()) { continue; }

                        let provider = guess_provider(label, uid);
                        models.push(ModelInfo {
                            name: format!("{} ({})", label, uid),
                            provider,
                        });
                    }
                }
                let _ = source_label;
            }

            // 兜底 1: 扫描 Windsurf LS 二进制, 提取全部 MODEL_* 枚举 (约 200+ 个)
            if let Some(extra) = read_models_from_ls_binary() {
                for m in extra {
                    if seen.insert(m.name.clone()) {
                        models.push(m);
                    }
                }
            }
            // 兜底 2: user_settings.pb (作为补充, 可能有 LS 二进制没有的)
            if let Some(extra) = read_models_from_settings_pb() {
                for m in extra {
                    if seen.insert(m.name.clone()) {
                        models.push(m);
                    }
                }
            }

            // 稳定排序: 已启用的 (API 返回) 在前, 其余按名字
            models.sort_by(|a, b| a.name.cmp(&b.name));

            let source = format!("✓ 已聚合 {} 个模型 (API + LS 二进制 + 本地枚举)", models.len());
            if let Ok(mut q) = events.lock() {
                q.push(AsyncEvent::ModelsRefreshed { models, source });
            }
        });
    }

    /// 异步调用任意 gRPC 方法 (用于真实测试)
    pub fn call_api_async(&self, label: String, service: String, method: String, key: String) {
        let Some(runtime) = self.runtime.clone() else { return };
        let events = self.events.clone();
        let server = self.server_url.clone();
        runtime.spawn(async move {
            let client = WindsurfClient::new(&server, &key);
            let payload = serde_json::json!({ "metadata": client.metadata() });
            let resp = client.call(&service, &method, &payload).await;
            let body = serde_json::to_string_pretty(&resp.data).unwrap_or_else(|_| resp.data.to_string());
            if let Ok(mut q) = events.lock() {
                q.push(AsyncEvent::ApiResult { label, ok: resp.ok, status: resp.status, body });
            }
        });
    }
}

// ═══════════════════════════════════════
//  主应用
// ═══════════════════════════════════════
pub struct ToolkitApp {
    pub state: AppState,
    fonts_loaded: bool,
}

impl ToolkitApp {
    pub fn new(cc: &eframe::CreationContext<'_>) -> Self {
        egui_extras::install_image_loaders(&cc.egui_ctx);
        setup_fonts(&cc.egui_ctx);
        apply_theme(&cc.egui_ctx);

        let mut state = AppState::default();

        // 初始化 Tokio runtime
        match tokio::runtime::Builder::new_multi_thread()
            .worker_threads(2)
            .enable_all()
            .build()
        {
            Ok(rt) => state.runtime = Some(Arc::new(rt)),
            Err(e) => state.log(format!("⚠ Runtime 初始化失败: {}", e)),
        }

        // 加载持久化配置
        let cfg = Config::load();
        state.apply_config(&cfg);
        state.log(format!("配置已加载 · {} 个密钥", state.keys.len()));

        // 如果没有任何 Key，自动从 Windsurf 编辑器检测
        if state.keys.is_empty() {
            state.log("未配置密钥，尝试从 Windsurf 编辑器自动导入...".to_string());
            let (added, _, _) = state.detect_and_import_keys();
            if added > 0 {
                state.log(format!("✓ 已自动导入 {} 个密钥，正在后台校验有效性", added));
            }
        }

        Self { state, fonts_loaded: true }
    }

    /// 周期性同步 Windsurf 当前 Key (自动检测 + 合并到密钥池 + 标记 active)
    /// 被 update() 每隔 N 秒调用一次
    fn sync_keys_with_windsurf(&mut self) {
        let detection = key_detector::detect_windsurf_keys();
        if detection.keys.is_empty() {
            // Windsurf 未运行或无法读取配置; 清除 active 标记
            for k in self.state.keys.iter_mut() { k.is_active = false; }
            return;
        }
        let now = now_unix();
        let mut added = 0;

        // Windsurf 会按最新排在前,第一个就是当前正在使用的
        let active_candidate = detection.keys.first().cloned().unwrap_or_default();
        self.state.active_key_full = active_candidate.clone();

        for key in &detection.keys {
            // 找到或新增
            if let Some(existing) = self.state.keys.iter_mut().find(|k| &k.full_key == key) {
                // 已存在: 标记最新检测时间 + 来源升级为 Windsurf (如果是 Manual)
                existing.last_detected_unix = Some(now);
                if existing.source == KeySource::Manual {
                    existing.source = KeySource::Windsurf;
                }
            } else {
                // 新 Key: 自动添加 + 校验
                let preview = if key.len() > 16 {
                    format!("{}...{}", &key[..12], &key[key.len()-4..])
                } else { key.clone() };
                self.state.keys.push(KeyInfo {
                    full_key: key.clone(),
                    preview,
                    healthy: true,
                    calls: 0,
                    errors: 0,
                    credits: None,
                    plan: String::new(),
                    status_json: None,
                    source: KeySource::Windsurf,
                    is_active: false,
                    last_detected_unix: Some(now),
                });
                self.state.check_key_async(key.clone());
                added += 1;
            }
        }

        // 更新 active 标记 (只有 1 个 active)
        for k in self.state.keys.iter_mut() {
            k.is_active = k.full_key == active_candidate;
        }

        if added > 0 {
            self.state.log(format!("密钥池自动同步: 新增 {} 个 Windsurf Key", added));
            self.state.mark_dirty();
        }
    }

    /// 处理异步事件队列
    fn drain_events(&mut self) {
        let events: Vec<AsyncEvent> = {
            let Ok(mut q) = self.state.events.lock() else { return };
            std::mem::take(&mut *q)
        };
        for event in events {
            match event {
                AsyncEvent::KeyChecked { key, healthy, plan, credits, message, status_json } => {
                    if let Some(k) = self.state.keys.iter_mut().find(|k| k.full_key == key) {
                        k.healthy = healthy;
                        k.plan = plan;
                        if credits.is_some() { k.credits = credits; }
                        if status_json.is_some() { k.status_json = status_json; }
                    }
                    self.state.log(message);
                    // 首次检测到有效 Key 时自动刷新模型列表
                    if healthy && !self.state.auto_refreshed_models {
                        self.state.auto_refreshed_models = true;
                        self.state.refresh_models_async();
                    }
                }
                AsyncEvent::ApiResult { label, ok, status, body } => {
                    let tag = if ok { "✓" } else { "✗" };
                    self.state.log(format!("{} [{}] HTTP {}", tag, label, status));
                    self.state.api_result_label = format!("{} {} · HTTP {}", tag, label, status);
                    self.state.api_result_text = body.clone();
                    self.state.api_result_ok = ok;
                    // 弹窗加载结束
                    self.state.result_modal_pending = false;

                    // LS 探测结果: 解析端口/CSRF
                    if label.contains("LS 探测") && ok {
                        if let Ok(json) = serde_json::from_str::<serde_json::Value>(&body) {
                            if let Some(p) = json.get("port").and_then(|v| v.as_u64()) {
                                self.state.ls_port = p as u16;
                            }
                            if let Some(t) = json.get("csrf").and_then(|v| v.as_str()) {
                                self.state.ls_csrf_token = t.to_string();
                            }
                            self.state.ls_connected = true;
                            self.state.ls_status = format!("已连接 · 端口 {} · CSRF {}",
                                self.state.ls_port,
                                if self.state.ls_csrf_token.is_empty() { "(无)" } else { "(已读取)" });
                        }
                    } else if label.contains("LS 探测") {
                        self.state.ls_connected = false;
                        self.state.ls_status = "未找到运行中的 Windsurf LS".to_string();
                    }
                    // 如果是 GetUserStatus,解析为结构化字段
                    if ok && (label.contains("用户状态") || label.contains("UserStatus")) {
                        if let Ok(json) = serde_json::from_str::<serde_json::Value>(&body) {
                            self.state.parsed_user_name = json.pointer("/userStatus/name").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            self.state.parsed_user_email = json.pointer("/userStatus/email").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            self.state.parsed_user_id = json.pointer("/userStatus/userId").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            self.state.parsed_user_team = json.pointer("/userStatus/teamId").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            self.state.parsed_user_tier = json.pointer("/userStatus/teamsTier").and_then(|v| v.as_str())
                                .or_else(|| json.pointer("/planInfo/teamsTier").and_then(|v| v.as_str()))
                                .unwrap_or("").to_string();
                            self.state.parsed_user_plan = json.pointer("/planInfo/planName").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            self.state.parsed_user_billing = json.pointer("/planInfo/billingStrategy").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            self.state.parsed_credits_prompt = json.pointer("/planInfo/monthlyPromptCredits").and_then(|v| v.as_i64()).unwrap_or(0);
                            self.state.parsed_credits_flow = json.pointer("/planInfo/monthlyFlowCredits").and_then(|v| v.as_i64()).unwrap_or(0);
                            self.state.parsed_user_loaded = true;
                        }
                    }
                }
                AsyncEvent::ModelsRefreshed { models, source } => {
                    if !models.is_empty() {
                        self.state.models = models;
                    }
                    self.state.log(source);
                }
            }
        }
    }
}

impl eframe::App for ToolkitApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // 先处理异步事件
        self.drain_events();

        // 自动保存配置
        if self.state.dirty {
            let cfg = self.state.export_config();
            if let Err(e) = cfg.save() {
                self.state.log(format!("⚠ 保存配置失败: {}", e));
            }
            self.state.dirty = false;
        }

        // ── 密钥池实时同步: 周期性检测 Windsurf 当前使用的 Key ──
        if self.state.auto_sync_keys {
            let now = now_unix();
            let interval = self.state.key_sync_interval_secs as i64;
            if now - self.state.last_key_sync_unix >= interval {
                self.state.last_key_sync_unix = now;
                self.sync_keys_with_windsurf();
            }
        }

        // 持续重绘 (处理后台事件)
        ctx.request_repaint_after(std::time::Duration::from_millis(500));

        // ── 自定义标题栏 ──
        egui::TopBottomPanel::top("title_bar")
            .exact_height(40.0)
            .frame(egui::Frame::new()
                .fill(BG_WHITE)
                .stroke(Stroke::new(1.0, BORDER_LIGHT))
                .inner_margin(egui::Margin::symmetric(12, 0)))
            .show(ctx, |ui| {
                self.render_title_bar(ui, ctx);
            });

        // 侧边栏 — 现代化 窄而清爽
        egui::SidePanel::left("sidebar")
            .exact_width(SIDEBAR_WIDTH)
            .resizable(false)
            .frame(egui::Frame::new()
                .fill(BG_SIDEBAR)
                .stroke(Stroke::new(1.0, BORDER_LIGHT))
                .inner_margin(egui::Margin::same(0)))
            .show(ctx, |ui| {
                self.render_sidebar(ui);
            });

        // 主内容区 — 大留白
        egui::CentralPanel::default()
            .frame(egui::Frame::new().fill(BG_PANEL).inner_margin(egui::Margin::symmetric(32, 28)))
            .show(ctx, |ui| {
                egui::ScrollArea::vertical().auto_shrink([false; 2]).show(ui, |ui| {
                    match self.state.current_page {
                        Page::Dashboard => super::pages::dashboard::render(ui, &self.state),
                        Page::Proxy => super::pages::proxy_page::render(ui, &mut self.state),
                        Page::Keys => super::pages::keys_page::render(ui, &mut self.state),
                        Page::UserStatus => super::pages::user_status_page::render(ui, &mut self.state),
                        Page::Models => super::pages::models_page::render(ui, &mut self.state),
                        Page::Monitor => super::pages::monitor_page::render(ui, &mut self.state),
                        Page::Inject => super::pages::inject_page::render(ui, &mut self.state),
                        Page::Account => super::pages::account_page::render(ui, &mut self.state),
                        Page::Team => super::pages::team_page::render(ui, &mut self.state),
                        Page::Mcp => super::pages::mcp_page::render(ui, &mut self.state),
                        Page::Settings => super::pages::settings_page::render(ui, &mut self.state),
                    }
                    ui.add_space(20.0);
                });
            });
    }
}

impl ToolkitApp {
    fn render_sidebar(&mut self, ui: &mut egui::Ui) {
        ui.add_space(22.0);

        // ── Logo 头部 ──
        ui.horizontal(|ui| {
            ui.add_space(18.0);
            // 图标胶囊背景
            egui::Frame::new()
                .fill(ACCENT_LIGHT)
                .corner_radius(CornerRadius::same(8))
                .inner_margin(egui::Margin::same(6))
                .show(ui, |ui| {
                    ui.add(egui::Image::from_bytes("bytes://logo.svg", icons::ICON_LOGO)
                        .fit_to_exact_size(Vec2::new(18.0, 18.0))
                        .tint(ACCENT));
                });
            ui.add_space(10.0);
            ui.vertical(|ui| {
                ui.add_space(1.0);
                ui.label(RichText::new("Windsurf").color(TEXT_PRIMARY).size(15.0).strong());
                ui.label(RichText::new("Toolkit").color(TEXT_MUTED).size(10.5));
            });
        });

        ui.add_space(24.0);

        // ── 分组: 核心 ──
        self.section_label(ui, "核心");
        self.nav_item(ui, "bytes://dashboard.svg", icons::ICON_DASHBOARD, "总览", Page::Dashboard);
        self.nav_item(ui, "bytes://proxy.svg", icons::ICON_PROXY, "代理服务", Page::Proxy);
        self.nav_item(ui, "bytes://key.svg", icons::ICON_KEY, "密钥管理", Page::Keys);
        self.nav_item(ui, "bytes://models.svg", icons::ICON_MODELS, "模型列表", Page::Models);

        ui.add_space(14.0);
        self.section_label(ui, "协议");
        self.nav_item(ui, "bytes://monitor.svg", icons::ICON_MONITOR, "用户状态", Page::UserStatus);
        self.nav_item(ui, "bytes://check.svg", icons::ICON_CHECK, "额度监控", Page::Monitor);
        self.nav_item(ui, "bytes://inject.svg", icons::ICON_INJECT, "Pro 注入", Page::Inject);
        self.nav_item(ui, "bytes://plus.svg", icons::ICON_PLUS, "账号工具", Page::Account);

        ui.add_space(14.0);
        self.section_label(ui, "高级");
        self.nav_item(ui, "bytes://team.svg", icons::ICON_TEAM, "团队管理", Page::Team);
        self.nav_item(ui, "bytes://mcp.svg", icons::ICON_REFRESH, "MCP 插件", Page::Mcp);

        // ── 底部 ──
        ui.with_layout(egui::Layout::bottom_up(egui::Align::LEFT), |ui| {
            ui.add_space(16.0);

            // 状态卡
            ui.horizontal(|ui| {
                ui.add_space(14.0);
                let w = ui.available_width() - 14.0;
                ui.allocate_ui(Vec2::new(w, 0.0), |ui| {
                    egui::Frame::new()
                        .fill(if self.state.proxy_running { ACCENT_GREEN_LIGHT } else { BG_SUBTLE })
                        .corner_radius(CornerRadius::same(8))
                        .inner_margin(egui::Margin::symmetric(10, 8))
                        .show(ui, |ui| {
                            let (color, label) = if self.state.proxy_running {
                                (ACCENT_GREEN, "运行中")
                            } else {
                                (TEXT_MUTED, "已停止")
                            };
                            ui.horizontal(|ui| {
                                ui.label(RichText::new("●").color(color).size(9.0));
                                ui.label(RichText::new("代理服务").color(TEXT_SECONDARY).size(11.0));
                                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                                    ui.label(RichText::new(label).color(color).size(11.0).strong());
                                });
                            });
                        });
                });
            });

            ui.add_space(6.0);
            self.nav_item(ui, "bytes://settings2.svg", icons::ICON_SETTINGS, "设置", Page::Settings);

            ui.add_space(8.0);
            // 细分隔线
            ui.horizontal(|ui| {
                ui.add_space(14.0);
                let w = ui.available_width() - 14.0;
                ui.allocate_ui(Vec2::new(w, 1.0), |ui| {
                    let rect = ui.max_rect();
                    ui.painter().line_segment(
                        [rect.left_center(), rect.right_center()],
                        Stroke::new(1.0, BORDER_LIGHT),
                    );
                });
            });
        });
    }

    fn section_label(&self, ui: &mut egui::Ui, text: &str) {
        ui.horizontal(|ui| {
            ui.add_space(18.0);
            ui.label(RichText::new(text.to_uppercase())
                .color(TEXT_MUTED)
                .size(10.0)
                .strong());
        });
        ui.add_space(4.0);
    }

    /// 自定义标题栏 — 可拖拽 · 有窗口控制按钮
    fn render_title_bar(&mut self, ui: &mut egui::Ui, ctx: &egui::Context) {
        ui.horizontal(|ui| {
            ui.add_space(4.0);

            // Logo + 标题
            ui.add(egui::Image::from_bytes("bytes://title_logo.svg", icons::ICON_LOGO)
                .fit_to_exact_size(Vec2::new(18.0, 18.0))
                .tint(ACCENT));
            ui.add_space(8.0);
            ui.label(RichText::new("Windsurf Toolkit").color(TEXT_PRIMARY).size(13.0).strong());
            ui.add_space(8.0);
            ui.label(RichText::new("v1.0").color(TEXT_MUTED).size(11.0));

            // 中间 — 可拖拽区域 (双击最大化)
            let drag_rect = {
                let avail = ui.available_width() - 140.0;  // 为右侧按钮留位
                let (rect, _) = ui.allocate_exact_size(Vec2::new(avail, 40.0), egui::Sense::click_and_drag());
                rect
            };
            let drag_resp = ui.interact(drag_rect, egui::Id::new("title_drag"), egui::Sense::click_and_drag());
            if drag_resp.is_pointer_button_down_on() {
                ctx.send_viewport_cmd(egui::ViewportCommand::StartDrag);
            }
            if drag_resp.double_clicked() {
                let is_max = ctx.input(|i| i.viewport().maximized.unwrap_or(false));
                ctx.send_viewport_cmd(egui::ViewportCommand::Maximized(!is_max));
            }

            // 右侧 — 窗口控制按钮
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                ui.add_space(2.0);
                if window_btn(ui, "✕", ACCENT_RED).clicked() {
                    ctx.send_viewport_cmd(egui::ViewportCommand::Close);
                }
                if window_btn(ui, "▢", TEXT_SECONDARY).clicked() {
                    let is_max = ctx.input(|i| i.viewport().maximized.unwrap_or(false));
                    ctx.send_viewport_cmd(egui::ViewportCommand::Maximized(!is_max));
                }
                if window_btn(ui, "─", TEXT_SECONDARY).clicked() {
                    ctx.send_viewport_cmd(egui::ViewportCommand::Minimized(true));
                }
            });
        });
    }

    fn nav_item(&mut self, ui: &mut egui::Ui, uri: &'static str, icon_bytes: &'static [u8], label: &str, page: Page) {
        let is_active = self.state.current_page == page;

        // 左右 padding
        ui.horizontal(|ui| {
            ui.add_space(10.0);
            let avail = ui.available_width() - 10.0;

            let (fill, text_color) = if is_active {
                (ACCENT_LIGHT, ACCENT)
            } else {
                (Color32::TRANSPARENT, TEXT_SECONDARY)
            };

            let response = egui::Frame::new()
                .fill(fill)
                .corner_radius(CornerRadius::same(7))
                .inner_margin(egui::Margin::symmetric(10, 7))
                .show(ui, |ui| {
                    ui.set_min_width(avail - 20.0);
                    ui.horizontal(|ui| {
                        ui.add(
                            egui::Image::from_bytes(uri, icon_bytes)
                                .fit_to_exact_size(ICON_SIZE)
                                .tint(text_color)
                        );
                        ui.add_space(10.0);
                        ui.label(RichText::new(label).color(text_color).size(13.0)
                            .strong());
                    });
                })
                .response;

            let response = response.interact(Sense::click());

            if response.clicked() {
                self.state.current_page = page;
            }

            if response.hovered() {
                ui.ctx().set_cursor_icon(CursorIcon::PointingHand);
            }
        });
        ui.add_space(2.0);
    }
}

/// 标题栏窗口控制按钮
fn window_btn(ui: &mut egui::Ui, glyph: &str, hover_color: Color32) -> egui::Response {
    let (rect, resp) = ui.allocate_exact_size(Vec2::new(36.0, 28.0), Sense::click());
    let hovered = resp.hovered();
    let bg = if hovered {
        if hover_color == ACCENT_RED { ACCENT_RED_LIGHT } else { BG_HOVER }
    } else {
        Color32::TRANSPARENT
    };
    let fg = if hovered { hover_color } else { TEXT_SECONDARY };
    ui.painter().rect_filled(rect, CornerRadius::same(5), bg);
    ui.painter().text(
        rect.center(),
        egui::Align2::CENTER_CENTER,
        glyph,
        egui::FontId::proportional(13.0),
        fg,
    );
    if hovered { ui.ctx().set_cursor_icon(CursorIcon::PointingHand); }
    resp
}

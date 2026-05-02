use axum::{
    body::Body,
    extract::{Path, Query, State},
    http::{HeaderMap, StatusCode},
    response::{IntoResponse, Json, Response},
    routing::{get, post},
    Router,
};
use serde_json::{json, Value};
use std::sync::Arc;
use tower_http::cors::CorsLayer;

use crate::client::models::*;
use crate::client::WindsurfClient;
use crate::web::DASHBOARD_HTML;
use super::key_pool::KeyPool;
use super::models_map::{resolve_model, list_models};
use super::streaming::windsurf_to_sse;

/// 反代服务器共享状态
#[derive(Clone)]
pub struct ProxyState {
    pub key_pool: KeyPool,
    pub server_url: String,
    pub auth_token: Option<String>,
}

impl ProxyState {
    /// 用指定 Key 创建 Windsurf 客户端
    pub fn client_with_key(&self, key: &str) -> WindsurfClient {
        WindsurfClient::new(&self.server_url, key)
    }
}

/// 启动反代服务器
pub async fn start_proxy(
    keys: Vec<String>,
    port: u16,
    host: &str,
    server_url: &str,
    auth_token: Option<String>,
    cooldown: u64,
    max_errors: u32,
) {
    let state = ProxyState {
        key_pool: KeyPool::new(keys, cooldown, max_errors),
        server_url: server_url.to_string(),
        auth_token,
    };

    let app = Router::new()
        .route("/", get(handle_root))
        .route("/health", get(handle_health))
        .route("/v1/health", get(handle_health))
        .route("/v1/models", get(handle_models))
        .route("/v1/status", get(handle_status))
        // OpenAI 兼容
        .route("/v1/chat/completions", post(handle_chat_completions))
        // Anthropic 兼容
        .route("/v1/messages", post(super::anthropic::handle_messages))
        // Gemini 兼容
        .route("/v1beta/models/*model_action", post(handle_gemini_dispatch))
        .route("/dashboard", get(handle_dashboard))
        .layer(CorsLayer::permissive())
        .with_state(Arc::new(state));

    let addr = format!("{}:{}", host, port);
    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();

    tracing::info!("🚀 Windsurf Multi-Protocol Proxy on http://{}", addr);
    tracing::info!("   OpenAI 兼容:");
    tracing::info!("     POST /v1/chat/completions");
    tracing::info!("     GET  /v1/models");
    tracing::info!("   Anthropic 兼容:");
    tracing::info!("     POST /v1/messages");
    tracing::info!("   Gemini 兼容:");
    tracing::info!("     POST /v1beta/models/{{model}}:generateContent");
    tracing::info!("     POST /v1beta/models/{{model}}:streamGenerateContent");
    tracing::info!("   通用:");
    tracing::info!("     GET  /v1/status");
    tracing::info!("     GET  /health");
    tracing::info!("     GET  /dashboard");

    axum::serve(listener, app).await.unwrap();
}

// ═══════════════════════════════════════
//  Handlers
// ═══════════════════════════════════════

async fn handle_health(State(state): State<Arc<ProxyState>>) -> Json<Value> {
    Json(json!({
        "status": "ok",
        "keys": state.key_pool.available_count(),
        "total": state.key_pool.size(),
    }))
}

async fn handle_models(State(_state): State<Arc<ProxyState>>) -> Json<Value> {
    let models = list_models();
    Json(json!({
        "object": "list",
        "data": models,
    }))
}

async fn handle_status(State(state): State<Arc<ProxyState>>) -> Json<Value> {
    Json(json!({
        "keys": state.key_pool.status(),
        "total": state.key_pool.size(),
        "available": state.key_pool.available_count(),
    }))
}

async fn handle_dashboard() -> Response {
    Response::builder()
        .status(200)
        .header("Content-Type", "text/html; charset=utf-8")
        .body(Body::from(DASHBOARD_HTML))
        .unwrap()
}

async fn handle_root(State(state): State<Arc<ProxyState>>) -> Response {
    let html = format!(r##"<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>Windsurf Toolkit Proxy</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif;background:#f8fafc;color:#0f172a;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}}
.container{{max-width:680px;width:100%;background:white;border-radius:12px;border:1px solid #e5e7eb;padding:40px;box-shadow:0 4px 16px rgba(0,0,0,0.04)}}
.logo{{display:flex;align-items:center;gap:12px;margin-bottom:24px}}
.logo-box{{width:40px;height:40px;border-radius:10px;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;font-size:20px}}
h1{{font-size:24px;font-weight:600;margin-bottom:4px}}
.subtitle{{color:#64748b;font-size:14px}}
.status{{background:#dcfce7;color:#15803d;padding:8px 14px;border-radius:100px;display:inline-flex;align-items:center;gap:8px;font-size:13px;font-weight:600;margin:16px 0 24px}}
.status-dot{{width:8px;height:8px;background:#22c55e;border-radius:50%;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:0.5}}}}
.section-title{{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;margin:24px 0 8px}}
.endpoint{{display:flex;align-items:center;gap:12px;padding:10px 14px;background:#f8fafc;border-radius:8px;margin-bottom:8px;border:1px solid #f1f5f9}}
.method{{font-size:11px;font-weight:700;padding:3px 8px;border-radius:4px;font-family:monospace}}
.method.get{{background:#dcfce7;color:#15803d}}
.method.post{{background:#e0e7ff;color:#4338ca}}
.path{{font-family:'SF Mono',Consolas,monospace;font-size:13px;color:#0f172a;flex:1}}
.desc{{font-size:12px;color:#64748b}}
.stats{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-top:16px}}
.stat{{background:#f8fafc;padding:14px;border-radius:8px;border:1px solid #f1f5f9}}
.stat-label{{font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px}}
.stat-value{{font-size:24px;font-weight:700;color:#0f172a;margin-top:4px}}
a.btn{{display:inline-block;background:#6366f1;color:white;text-decoration:none;padding:10px 16px;border-radius:8px;font-weight:600;font-size:13px;margin-top:16px}}
a.btn:hover{{background:#4f46e5}}
</style></head>
<body><div class="container">
<div class="logo">
<div class="logo-box">W</div>
<div><h1>Windsurf Toolkit Proxy</h1><div class="subtitle">OpenAI / Anthropic / Gemini 多协议反代</div></div>
</div>
<div class="status"><div class="status-dot"></div> 服务运行中</div>

<div class="stats">
<div class="stat"><div class="stat-label">密钥总数</div><div class="stat-value">{total}</div></div>
<div class="stat"><div class="stat-label">可用密钥</div><div class="stat-value">{avail}</div></div>
</div>

<div class="section-title">OpenAI 兼容</div>
<div class="endpoint"><span class="method post">POST</span><span class="path">/v1/chat/completions</span><span class="desc">聊天补全 (流式/非流式)</span></div>
<div class="endpoint"><span class="method get">GET</span><span class="path">/v1/models</span><span class="desc">模型列表</span></div>
<div class="section-title">Anthropic 兼容</div>
<div class="endpoint"><span class="method post">POST</span><span class="path">/v1/messages</span><span class="desc">Messages API (流式/非流式)</span></div>
<div class="section-title">Gemini 兼容</div>
<div class="endpoint"><span class="method post">POST</span><span class="path">/v1beta/models/&#123;model&#125;:generateContent</span><span class="desc">生成内容</span></div>
<div class="endpoint"><span class="method post">POST</span><span class="path">/v1beta/models/&#123;model&#125;:streamGenerateContent</span><span class="desc">流式生成</span></div>
<div class="section-title">通用</div>
<div class="endpoint"><span class="method get">GET</span><span class="path">/health</span><span class="desc">健康检查</span></div>
<div class="endpoint"><span class="method get">GET</span><span class="path">/v1/status</span><span class="desc">Key 池状态</span></div>
<div class="endpoint"><span class="method get">GET</span><span class="path">/dashboard</span><span class="desc">Web 管理面板</span></div>

<a href="/dashboard" class="btn">打开管理面板 →</a>
</div></body></html>"##,
        total = state.key_pool.size(),
        avail = state.key_pool.available_count(),
    );

    Response::builder()
        .status(200)
        .header("Content-Type", "text/html; charset=utf-8")
        .body(Body::from(html))
        .unwrap()
}

async fn handle_chat_completions(
    State(state): State<Arc<ProxyState>>,
    headers: HeaderMap,
    Json(body): Json<OpenAIChatRequest>,
) -> Response {
    // 验证 auth token
    if let Some(ref required_token) = state.auth_token {
        let auth = headers
            .get("authorization")
            .and_then(|v| v.to_str().ok())
            .unwrap_or("");
        let token = auth.strip_prefix("Bearer ").unwrap_or("");
        if token != required_token {
            return (
                StatusCode::UNAUTHORIZED,
                Json(json!({"error": {"message": "Unauthorized", "type": "auth_error"}})),
            ).into_response();
        }
    }

    // 验证 messages
    if body.messages.is_empty() {
        return (
            StatusCode::BAD_REQUEST,
            Json(json!({"error": {"message": "messages is required", "type": "invalid_request_error"}})),
        ).into_response();
    }

    // 获取 Key
    let key = match state.key_pool.next() {
        Some(k) => k,
        None => {
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(json!({"error": {"message": "No available API keys", "type": "server_error"}})),
            ).into_response();
        }
    };

    // 解析模型
    let model_uid = resolve_model(&body.model);
    let client = state.client_with_key(&key);

    if body.stream {
        handle_streaming(client, &state.key_pool, &key, &model_uid, &body).await
    } else {
        handle_non_streaming(client, &state.key_pool, &key, &model_uid, &body).await
    }
}

async fn handle_non_streaming(
    client: WindsurfClient,
    pool: &KeyPool,
    key: &str,
    model_uid: &str,
    body: &OpenAIChatRequest,
) -> Response {
    let result = client.chat_completions(
        &body.messages,
        model_uid,
        body.temperature,
        body.max_tokens,
    ).await;

    if !result.ok {
        let status = result.status;
        if status == 401 || status == 403 {
            pool.report_error(key, "auth_error", true);
        } else if status == 429 {
            pool.report_error(key, "rate_limited", false);
        } else {
            pool.report_error(key, &format!("status_{}", status), false);
        }
        return (
            StatusCode::from_u16(status).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
            Json(json!({"error": {"message": result.data.to_string(), "type": "api_error"}})),
        ).into_response();
    }

    pool.report_success(key);

    // 提取内容
    let content = extract_content(&result.data);
    let chat_id = format!("chatcmpl-{}", uuid::Uuid::new_v4().simple());
    let created = chrono::Utc::now().timestamp();

    let response = OpenAIChatResponse {
        id: chat_id,
        object: "chat.completion".to_string(),
        created,
        model: model_uid.to_string(),
        choices: vec![OpenAIChoice {
            index: 0,
            message: ChatMessage {
                role: "assistant".to_string(),
                content,
            },
            finish_reason: "stop".to_string(),
        }],
        usage: OpenAIUsage::default(),
    };

    Json(serde_json::to_value(response).unwrap()).into_response()
}

async fn handle_streaming(
    client: WindsurfClient,
    pool: &KeyPool,
    key: &str,
    model_uid: &str,
    body: &OpenAIChatRequest,
) -> Response {
    let stream_result = client.chat_completions_stream(
        &body.messages,
        model_uid,
        body.temperature,
        body.max_tokens,
    ).await;

    match stream_result {
        Ok(response) => {
            if !response.status().is_success() {
                let status = response.status().as_u16();
                if status == 401 || status == 403 {
                    pool.report_error(key, "auth_error", true);
                } else if status == 429 {
                    pool.report_error(key, "rate_limited", false);
                } else {
                    pool.report_error(key, &format!("status_{}", status), false);
                }
                let body_text = response.text().await.unwrap_or_default();
                return (
                    StatusCode::from_u16(status).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
                    Json(json!({"error": {"message": body_text, "type": "api_error"}})),
                ).into_response();
            }

            pool.report_success(key);

            let chat_id = format!("chatcmpl-{}", uuid::Uuid::new_v4().simple());
            let created = chrono::Utc::now().timestamp();

            let sse_body = windsurf_to_sse(response, chat_id, model_uid.to_string(), created);

            Response::builder()
                .status(200)
                .header("Content-Type", "text/event-stream")
                .header("Cache-Control", "no-cache")
                .header("Connection", "keep-alive")
                .header("Access-Control-Allow-Origin", "*")
                .body(sse_body)
                .unwrap()
        }
        Err(e) => {
            pool.report_error(key, &e.to_string(), false);
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                Json(json!({"error": {"message": format!("Stream error: {}", e), "type": "server_error"}})),
            ).into_response()
        }
    }
}

/// Gemini 通配路由分发: 根据路径后缀决定流式/非流式
async fn handle_gemini_dispatch(
    state: State<Arc<ProxyState>>,
    Path(model_action): Path<String>,
    query: Query<super::gemini::GeminiQuery>,
    headers: HeaderMap,
    body: Json<super::gemini::GeminiRequest>,
) -> Response {
    if model_action.ends_with(":streamGenerateContent") {
        let model_path = model_action.trim_start_matches('/').to_string();
        super::gemini::handle_stream_generate_content(
            state,
            Path(model_path),
            query,
            headers,
            body,
        ).await
    } else if model_action.ends_with(":generateContent") {
        let model_path = model_action.trim_start_matches('/').to_string();
        super::gemini::handle_generate_content(
            state,
            Path(model_path),
            query,
            headers,
            body,
        ).await
    } else {
        (StatusCode::NOT_FOUND, Json(json!({
            "error": {"code": 404, "message": "Method not found", "status": "NOT_FOUND"}
        }))).into_response()
    }
}

/// 从 Windsurf 非流式响应中提取文本
pub fn extract_content(data: &Value) -> String {
    if let Some(content) = data.get("content").and_then(|v| v.as_str()) {
        return content.to_string();
    }
    if let Some(msg) = data.get("message") {
        if let Some(content) = msg.get("content").and_then(|v| v.as_str()) {
            return content.to_string();
        }
        if let Some(s) = msg.as_str() {
            return s.to_string();
        }
    }
    if let Some(result) = data.get("result") {
        if let Some(content) = result.get("content").and_then(|v| v.as_str()) {
            return content.to_string();
        }
    }
    if let Some(choices) = data.get("choices").and_then(|v| v.as_array()) {
        if let Some(first) = choices.first() {
            if let Some(content) = first.get("message").and_then(|m| m.get("content")).and_then(|v| v.as_str()) {
                return content.to_string();
            }
        }
    }
    data.to_string()
}

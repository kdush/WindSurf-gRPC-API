//! Anthropic Messages API 兼容层
//!
//! 端点:
//!   POST /v1/messages          — 非流式 + 流式 (stream: true)
//!
//! 认证方式:
//!   x-api-key: <token>  或  Authorization: Bearer <token>
//!
//! 完整兼容 anthropic SDK (Python / TS) 的请求/响应格式.

use axum::{
    body::Body,
    extract::State,
    http::{HeaderMap, StatusCode},
    response::{IntoResponse, Json, Response},
};
use bytes::Bytes;
use futures_util::StreamExt;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::sync::Arc;

use crate::client::models::ChatMessage;
use crate::client::WindsurfClient;
use super::key_pool::KeyPool;
use super::models_map::resolve_model;
use super::server::ProxyState;
use super::streaming::extract_delta_content;

// ═══════════════════════════════════════
//  Anthropic 请求/响应数据结构
// ═══════════════════════════════════════

/// Anthropic Messages API 请求
#[derive(Debug, Clone, Deserialize)]
pub struct AnthropicRequest {
    pub model: String,
    pub messages: Vec<AnthropicMessage>,
    #[serde(default)]
    pub system: Option<String>,
    pub max_tokens: u32,
    #[serde(default)]
    pub stream: bool,
    #[serde(default)]
    pub temperature: Option<f64>,
    #[serde(default)]
    pub top_p: Option<f64>,
    #[serde(default)]
    pub top_k: Option<u32>,
    #[serde(default)]
    pub stop_sequences: Option<Vec<String>>,
    #[serde(default)]
    pub metadata: Option<Value>,
}

/// Anthropic 消息 (支持字符串和 content block 两种格式)
#[derive(Debug, Clone, Deserialize)]
pub struct AnthropicMessage {
    pub role: String,
    pub content: AnthropicContent,
}

/// content 字段: 可以是字符串或 content block 数组
#[derive(Debug, Clone, Deserialize)]
#[serde(untagged)]
pub enum AnthropicContent {
    Text(String),
    Blocks(Vec<AnthropicContentBlock>),
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct AnthropicContentBlock {
    #[serde(rename = "type")]
    pub block_type: String,
    #[serde(default)]
    pub text: Option<String>,
    #[serde(default)]
    pub source: Option<Value>,
}

/// Anthropic 非流式响应
#[derive(Debug, Clone, Serialize)]
pub struct AnthropicResponse {
    pub id: String,
    #[serde(rename = "type")]
    pub msg_type: String,
    pub role: String,
    pub content: Vec<AnthropicResponseBlock>,
    pub model: String,
    pub stop_reason: String,
    pub stop_sequence: Option<String>,
    pub usage: AnthropicUsage,
}

#[derive(Debug, Clone, Serialize)]
pub struct AnthropicResponseBlock {
    #[serde(rename = "type")]
    pub block_type: String,
    pub text: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct AnthropicUsage {
    pub input_tokens: u32,
    pub output_tokens: u32,
}

// ═══════════════════════════════════════
//  格式转换
// ═══════════════════════════════════════

/// 将 Anthropic 请求转为内部 ChatMessage 列表
fn to_chat_messages(req: &AnthropicRequest) -> Vec<ChatMessage> {
    let mut messages = Vec::new();

    // system 提升为 system message
    if let Some(ref sys) = req.system {
        if !sys.is_empty() {
            messages.push(ChatMessage {
                role: "system".to_string(),
                content: sys.clone(),
            });
        }
    }

    for msg in &req.messages {
        let text = match &msg.content {
            AnthropicContent::Text(s) => s.clone(),
            AnthropicContent::Blocks(blocks) => {
                blocks
                    .iter()
                    .filter_map(|b| {
                        if b.block_type == "text" {
                            b.text.clone()
                        } else {
                            None
                        }
                    })
                    .collect::<Vec<_>>()
                    .join("\n")
            }
        };
        messages.push(ChatMessage {
            role: msg.role.clone(),
            content: text,
        });
    }

    messages
}

// ═══════════════════════════════════════
//  认证
// ═══════════════════════════════════════

/// 从请求头中提取认证 token (x-api-key 优先, 其次 Authorization: Bearer)
fn extract_auth_token(headers: &HeaderMap) -> String {
    if let Some(key) = headers.get("x-api-key").and_then(|v| v.to_str().ok()) {
        return key.to_string();
    }
    let auth = headers
        .get("authorization")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("");
    auth.strip_prefix("Bearer ").unwrap_or("").to_string()
}

// ═══════════════════════════════════════
//  Handler
// ═══════════════════════════════════════

/// POST /v1/messages
pub async fn handle_messages(
    State(state): State<Arc<ProxyState>>,
    headers: HeaderMap,
    Json(body): Json<AnthropicRequest>,
) -> Response {
    // 验证 auth
    if let Some(ref required_token) = state.auth_token {
        let token = extract_auth_token(&headers);
        if token != *required_token {
            return (
                StatusCode::UNAUTHORIZED,
                Json(json!({
                    "type": "error",
                    "error": {"type": "authentication_error", "message": "Invalid API key"}
                })),
            ).into_response();
        }
    }

    // 验证 messages
    if body.messages.is_empty() {
        return (
            StatusCode::BAD_REQUEST,
            Json(json!({
                "type": "error",
                "error": {"type": "invalid_request_error", "message": "messages: at least 1 message is required"}
            })),
        ).into_response();
    }

    // 获取 Key
    let key = match state.key_pool.next() {
        Some(k) => k,
        None => {
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(json!({
                    "type": "error",
                    "error": {"type": "overloaded_error", "message": "No available API keys"}
                })),
            ).into_response();
        }
    };

    let model_uid = resolve_model(&body.model);
    let client = state.client_with_key(&key);
    let messages = to_chat_messages(&body);

    if body.stream {
        anthropic_streaming(client, &state.key_pool, &key, &model_uid, &messages, &body).await
    } else {
        anthropic_non_streaming(client, &state.key_pool, &key, &model_uid, &messages, &body).await
    }
}

// ═══════════════════════════════════════
//  非流式
// ═══════════════════════════════════════

async fn anthropic_non_streaming(
    client: WindsurfClient,
    pool: &KeyPool,
    key: &str,
    model_uid: &str,
    messages: &[ChatMessage],
    body: &AnthropicRequest,
) -> Response {
    let result = client.chat_completions(
        messages,
        model_uid,
        body.temperature,
        Some(body.max_tokens),
    ).await;

    if !result.ok {
        report_error(pool, key, result.status);
        return anthropic_error(result.status, &result.data.to_string());
    }

    pool.report_success(key);

    let content = super::server::extract_content(&result.data);
    let msg_id = format!("msg_{}", uuid::Uuid::new_v4().simple());

    let response = AnthropicResponse {
        id: msg_id,
        msg_type: "message".to_string(),
        role: "assistant".to_string(),
        content: vec![AnthropicResponseBlock {
            block_type: "text".to_string(),
            text: content,
        }],
        model: model_uid.to_string(),
        stop_reason: "end_turn".to_string(),
        stop_sequence: None,
        usage: AnthropicUsage {
            input_tokens: 0,
            output_tokens: 0,
        },
    };

    Json(serde_json::to_value(response).unwrap()).into_response()
}

// ═══════════════════════════════════════
//  流式
// ═══════════════════════════════════════

async fn anthropic_streaming(
    client: WindsurfClient,
    pool: &KeyPool,
    key: &str,
    model_uid: &str,
    messages: &[ChatMessage],
    body: &AnthropicRequest,
) -> Response {
    let stream_result = client.chat_completions_stream(
        messages,
        model_uid,
        body.temperature,
        Some(body.max_tokens),
    ).await;

    match stream_result {
        Ok(response) => {
            if !response.status().is_success() {
                let status = response.status().as_u16();
                report_error(pool, key, status);
                let body_text = response.text().await.unwrap_or_default();
                return anthropic_error(status, &body_text);
            }

            pool.report_success(key);

            let msg_id = format!("msg_{}", uuid::Uuid::new_v4().simple());
            let model = model_uid.to_string();

            let stream = async_stream::stream! {
                // event: message_start
                let start = json!({
                    "type": "message_start",
                    "message": {
                        "id": msg_id,
                        "type": "message",
                        "role": "assistant",
                        "content": [],
                        "model": model,
                        "stop_reason": null,
                        "stop_sequence": null,
                        "usage": {"input_tokens": 0, "output_tokens": 0}
                    }
                });
                yield Ok::<Bytes, std::io::Error>(
                    Bytes::from(format!("event: message_start\ndata: {}\n\n", start))
                );

                // event: content_block_start
                let block_start = json!({
                    "type": "content_block_start",
                    "index": 0,
                    "content_block": {"type": "text", "text": ""}
                });
                yield Ok(Bytes::from(
                    format!("event: content_block_start\ndata: {}\n\n", block_start)
                ));

                // event: ping
                yield Ok(Bytes::from(
                    "event: ping\ndata: {\"type\":\"ping\"}\n\n".to_string()
                ));

                // 逐块读取 Windsurf 响应
                let mut byte_stream = response.bytes_stream();
                let mut buffer = String::new();

                while let Some(chunk_result) = byte_stream.next().await {
                    match chunk_result {
                        Ok(bytes) => {
                            buffer.push_str(&String::from_utf8_lossy(&bytes));

                            while let Some(pos) = buffer.find('\n') {
                                let line_str = buffer[..pos].trim().to_string();
                                buffer = buffer[pos + 1..].to_string();

                                if line_str.is_empty() {
                                    continue;
                                }

                                if let Some(text) = extract_delta_content(&line_str) {
                                    if !text.is_empty() {
                                        let delta = json!({
                                            "type": "content_block_delta",
                                            "index": 0,
                                            "delta": {"type": "text_delta", "text": text}
                                        });
                                        yield Ok(Bytes::from(
                                            format!("event: content_block_delta\ndata: {}\n\n", delta)
                                        ));
                                    }
                                }
                            }
                        }
                        Err(_) => break,
                    }
                }

                // 处理 buffer 剩余数据
                if !buffer.trim().is_empty() {
                    if let Some(text) = extract_delta_content(buffer.trim()) {
                        if !text.is_empty() {
                            let delta = json!({
                                "type": "content_block_delta",
                                "index": 0,
                                "delta": {"type": "text_delta", "text": text}
                            });
                            yield Ok(Bytes::from(
                                format!("event: content_block_delta\ndata: {}\n\n", delta)
                            ));
                        }
                    }
                }

                // event: content_block_stop
                let block_stop = json!({"type": "content_block_stop", "index": 0});
                yield Ok(Bytes::from(
                    format!("event: content_block_stop\ndata: {}\n\n", block_stop)
                ));

                // event: message_delta
                let msg_delta = json!({
                    "type": "message_delta",
                    "delta": {"stop_reason": "end_turn", "stop_sequence": null},
                    "usage": {"output_tokens": 0}
                });
                yield Ok(Bytes::from(
                    format!("event: message_delta\ndata: {}\n\n", msg_delta)
                ));

                // event: message_stop
                yield Ok(Bytes::from(
                    "event: message_stop\ndata: {\"type\":\"message_stop\"}\n\n".to_string()
                ));
            };

            Response::builder()
                .status(200)
                .header("Content-Type", "text/event-stream")
                .header("Cache-Control", "no-cache")
                .header("Connection", "keep-alive")
                .header("Access-Control-Allow-Origin", "*")
                .body(Body::from_stream(stream))
                .unwrap()
        }
        Err(e) => {
            pool.report_error(key, &e.to_string(), false);
            anthropic_error(500, &format!("Stream error: {}", e))
        }
    }
}

// ═══════════════════════════════════════
//  辅助函数
// ═══════════════════════════════════════

fn report_error(pool: &KeyPool, key: &str, status: u16) {
    if status == 401 || status == 403 {
        pool.report_error(key, "auth_error", true);
    } else if status == 429 {
        pool.report_error(key, "rate_limited", false);
    } else {
        pool.report_error(key, &format!("status_{}", status), false);
    }
}

fn anthropic_error(status: u16, message: &str) -> Response {
    let error_type = match status {
        401 => "authentication_error",
        403 => "permission_error",
        404 => "not_found_error",
        429 => "rate_limit_error",
        500..=599 => "api_error",
        _ => "invalid_request_error",
    };

    (
        StatusCode::from_u16(status).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
        Json(json!({
            "type": "error",
            "error": {"type": error_type, "message": message}
        })),
    ).into_response()
}

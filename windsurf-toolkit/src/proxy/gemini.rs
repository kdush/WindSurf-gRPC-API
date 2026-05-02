//! Google Gemini API 兼容层
//!
//! 端点:
//!   POST /v1beta/models/{model}:generateContent       — 非流式
//!   POST /v1beta/models/{model}:streamGenerateContent  — 流式
//!
//! 认证方式:
//!   ?key=<token>  或  Authorization: Bearer <token>
//!
//! 完整兼容 google-generativeai SDK (Python / TS) 的请求/响应格式.

use axum::{
    body::Body,
    extract::{Path, Query, State},
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
//  Gemini 请求/响应数据结构
// ═══════════════════════════════════════

/// Gemini generateContent 请求
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct GeminiRequest {
    #[serde(default)]
    pub contents: Vec<GeminiContent>,
    #[serde(default)]
    pub system_instruction: Option<GeminiSystemInstruction>,
    #[serde(default)]
    pub generation_config: Option<GeminiGenerationConfig>,
    #[serde(default)]
    pub safety_settings: Option<Vec<Value>>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct GeminiContent {
    #[serde(default)]
    pub role: Option<String>,
    pub parts: Vec<GeminiPart>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct GeminiPart {
    #[serde(default)]
    pub text: Option<String>,
    #[serde(default, rename = "inlineData")]
    pub inline_data: Option<Value>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct GeminiSystemInstruction {
    pub parts: Vec<GeminiPart>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct GeminiGenerationConfig {
    #[serde(default)]
    pub temperature: Option<f64>,
    #[serde(default)]
    pub top_p: Option<f64>,
    #[serde(default)]
    pub top_k: Option<u32>,
    #[serde(default)]
    pub max_output_tokens: Option<u32>,
    #[serde(default)]
    pub stop_sequences: Option<Vec<String>>,
    #[serde(default)]
    pub candidate_count: Option<u32>,
}

/// Gemini 非流式响应
#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GeminiResponse {
    pub candidates: Vec<GeminiCandidate>,
    pub usage_metadata: GeminiUsageMetadata,
    pub model_version: String,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GeminiCandidate {
    pub content: GeminiContent,
    pub finish_reason: String,
    pub index: u32,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GeminiUsageMetadata {
    pub prompt_token_count: u32,
    pub candidates_token_count: u32,
    pub total_token_count: u32,
}

/// URL 查询参数
#[derive(Debug, Deserialize)]
pub struct GeminiQuery {
    #[serde(default)]
    pub key: Option<String>,
    #[serde(default)]
    pub alt: Option<String>,
}

// ═══════════════════════════════════════
//  格式转换
// ═══════════════════════════════════════

/// 将 Gemini 请求转为内部 ChatMessage 列表
fn to_chat_messages(req: &GeminiRequest) -> Vec<ChatMessage> {
    let mut messages = Vec::new();

    // systemInstruction → system message
    if let Some(ref sys) = req.system_instruction {
        let text: String = sys.parts.iter()
            .filter_map(|p| p.text.clone())
            .collect::<Vec<_>>()
            .join("\n");
        if !text.is_empty() {
            messages.push(ChatMessage {
                role: "system".to_string(),
                content: text,
            });
        }
    }

    for content in &req.contents {
        let role = match content.role.as_deref() {
            Some("model") => "assistant",
            Some("user") | None => "user",
            Some(r) => r,
        };
        let text: String = content.parts.iter()
            .filter_map(|p| p.text.clone())
            .collect::<Vec<_>>()
            .join("\n");
        messages.push(ChatMessage {
            role: role.to_string(),
            content: text,
        });
    }

    messages
}

/// 从路径中提取模型名 (去掉 :generateContent / :streamGenerateContent 后缀)
fn extract_model_from_path(model_path: &str) -> String {
    model_path
        .split(':')
        .next()
        .unwrap_or(model_path)
        .to_string()
}

// ═══════════════════════════════════════
//  认证
// ═══════════════════════════════════════

fn extract_auth_token(headers: &HeaderMap, query: &GeminiQuery) -> String {
    // ?key=xxx 优先
    if let Some(ref key) = query.key {
        if !key.is_empty() {
            return key.clone();
        }
    }
    // Authorization: Bearer xxx
    let auth = headers
        .get("authorization")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("");
    auth.strip_prefix("Bearer ").unwrap_or("").to_string()
}

// ═══════════════════════════════════════
//  Handlers
// ═══════════════════════════════════════

/// POST /v1beta/models/{model}:generateContent
pub async fn handle_generate_content(
    State(state): State<Arc<ProxyState>>,
    Path(model_path): Path<String>,
    Query(query): Query<GeminiQuery>,
    headers: HeaderMap,
    Json(body): Json<GeminiRequest>,
) -> Response {
    // 验证 auth
    if let Some(ref required_token) = state.auth_token {
        let token = extract_auth_token(&headers, &query);
        if token != *required_token {
            return gemini_error(401, "API key not valid. Please pass a valid API key.");
        }
    }

    if body.contents.is_empty() {
        return gemini_error(400, "Request must contain at least one content.");
    }

    let key = match state.key_pool.next() {
        Some(k) => k,
        None => return gemini_error(503, "No available API keys"),
    };

    let model_name = extract_model_from_path(&model_path);
    let model_uid = resolve_model(&model_name);
    let client = state.client_with_key(&key);
    let messages = to_chat_messages(&body);
    let temperature = body.generation_config.as_ref().and_then(|c| c.temperature);
    let max_tokens = body.generation_config.as_ref().and_then(|c| c.max_output_tokens);

    gemini_non_streaming(client, &state.key_pool, &key, &model_uid, &messages, temperature, max_tokens).await
}

/// POST /v1beta/models/{model}:streamGenerateContent
pub async fn handle_stream_generate_content(
    State(state): State<Arc<ProxyState>>,
    Path(model_path): Path<String>,
    Query(query): Query<GeminiQuery>,
    headers: HeaderMap,
    Json(body): Json<GeminiRequest>,
) -> Response {
    // 验证 auth
    if let Some(ref required_token) = state.auth_token {
        let token = extract_auth_token(&headers, &query);
        if token != *required_token {
            return gemini_error(401, "API key not valid. Please pass a valid API key.");
        }
    }

    if body.contents.is_empty() {
        return gemini_error(400, "Request must contain at least one content.");
    }

    let key = match state.key_pool.next() {
        Some(k) => k,
        None => return gemini_error(503, "No available API keys"),
    };

    let model_name = extract_model_from_path(&model_path);
    let model_uid = resolve_model(&model_name);
    let client = state.client_with_key(&key);
    let messages = to_chat_messages(&body);
    let temperature = body.generation_config.as_ref().and_then(|c| c.temperature);
    let max_tokens = body.generation_config.as_ref().and_then(|c| c.max_output_tokens);

    gemini_streaming(client, &state.key_pool, &key, &model_uid, &messages, temperature, max_tokens).await
}

// ═══════════════════════════════════════
//  非流式
// ═══════════════════════════════════════

async fn gemini_non_streaming(
    client: WindsurfClient,
    pool: &KeyPool,
    key: &str,
    model_uid: &str,
    messages: &[ChatMessage],
    temperature: Option<f64>,
    max_tokens: Option<u32>,
) -> Response {
    let result = client.chat_completions(
        messages,
        model_uid,
        temperature,
        max_tokens,
    ).await;

    if !result.ok {
        report_error(pool, key, result.status);
        return gemini_error(result.status, &result.data.to_string());
    }

    pool.report_success(key);

    let content = super::server::extract_content(&result.data);

    let response = GeminiResponse {
        candidates: vec![GeminiCandidate {
            content: GeminiContent {
                role: Some("model".to_string()),
                parts: vec![GeminiPart {
                    text: Some(content),
                    inline_data: None,
                }],
            },
            finish_reason: "STOP".to_string(),
            index: 0,
        }],
        usage_metadata: GeminiUsageMetadata {
            prompt_token_count: 0,
            candidates_token_count: 0,
            total_token_count: 0,
        },
        model_version: model_uid.to_string(),
    };

    Json(serde_json::to_value(response).unwrap()).into_response()
}

// ═══════════════════════════════════════
//  流式
// ═══════════════════════════════════════

async fn gemini_streaming(
    client: WindsurfClient,
    pool: &KeyPool,
    key: &str,
    model_uid: &str,
    messages: &[ChatMessage],
    temperature: Option<f64>,
    max_tokens: Option<u32>,
) -> Response {
    let stream_result = client.chat_completions_stream(
        messages,
        model_uid,
        temperature,
        max_tokens,
    ).await;

    match stream_result {
        Ok(response) => {
            if !response.status().is_success() {
                let status = response.status().as_u16();
                report_error(pool, key, status);
                let body_text = response.text().await.unwrap_or_default();
                return gemini_error(status, &body_text);
            }

            pool.report_success(key);

            let model = model_uid.to_string();

            let stream = async_stream::stream! {
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
                                        let chunk = json!({
                                            "candidates": [{
                                                "content": {
                                                    "role": "model",
                                                    "parts": [{"text": text}]
                                                },
                                                "index": 0
                                            }],
                                            "usageMetadata": {
                                                "promptTokenCount": 0,
                                                "candidatesTokenCount": 0,
                                                "totalTokenCount": 0
                                            }
                                        });
                                        yield Ok::<Bytes, std::io::Error>(
                                            Bytes::from(format!("data: {}\n\n", chunk))
                                        );
                                    }
                                }
                            }
                        }
                        Err(_) => break,
                    }
                }

                // 处理 buffer 剩余
                if !buffer.trim().is_empty() {
                    if let Some(text) = extract_delta_content(buffer.trim()) {
                        if !text.is_empty() {
                            let chunk = json!({
                                "candidates": [{
                                    "content": {
                                        "role": "model",
                                        "parts": [{"text": text}]
                                    },
                                    "index": 0
                                }],
                                "usageMetadata": {
                                    "promptTokenCount": 0,
                                    "candidatesTokenCount": 0,
                                    "totalTokenCount": 0
                                }
                            });
                            yield Ok(Bytes::from(format!("data: {}\n\n", chunk)));
                        }
                    }
                }

                // 结束 chunk (带 finishReason)
                let finish = json!({
                    "candidates": [{
                        "content": {
                            "role": "model",
                            "parts": [{"text": ""}]
                        },
                        "finishReason": "STOP",
                        "index": 0
                    }],
                    "usageMetadata": {
                        "promptTokenCount": 0,
                        "candidatesTokenCount": 0,
                        "totalTokenCount": 0
                    },
                    "modelVersion": model
                });
                yield Ok(Bytes::from(format!("data: {}\n\n", finish)));
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
            gemini_error(500, &format!("Stream error: {}", e))
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

fn gemini_error(status: u16, message: &str) -> Response {
    let code = match status {
        400 => "INVALID_ARGUMENT",
        401 | 403 => "PERMISSION_DENIED",
        404 => "NOT_FOUND",
        429 => "RESOURCE_EXHAUSTED",
        503 => "UNAVAILABLE",
        _ => "INTERNAL",
    };

    (
        StatusCode::from_u16(status).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
        Json(json!({
            "error": {
                "code": status,
                "message": message,
                "status": code
            }
        })),
    ).into_response()
}

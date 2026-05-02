use axum::body::Body;
use bytes::Bytes;
use futures_util::StreamExt;
use reqwest::Response;
use serde_json::Value;

use crate::client::models::{OpenAIStreamChunk, OpenAIStreamChoice, OpenAIDelta};

/// 将 Windsurf 流式响应转换为 OpenAI SSE 格式的 Body
pub fn windsurf_to_sse(
    response: Response,
    chat_id: String,
    model: String,
    created: i64,
) -> Body {
    let stream = async_stream::stream! {
        // 发送 role chunk
        let role_chunk = OpenAIStreamChunk {
            id: chat_id.clone(),
            object: "chat.completion.chunk".to_string(),
            created,
            model: model.clone(),
            choices: vec![OpenAIStreamChoice {
                index: 0,
                delta: OpenAIDelta {
                    role: Some("assistant".to_string()),
                    content: Some(String::new()),
                },
                finish_reason: None,
            }],
        };
        let line = format!("data: {}\n\n", serde_json::to_string(&role_chunk).unwrap());
        yield Ok::<Bytes, std::io::Error>(Bytes::from(line));

        // 逐块读取 Windsurf 响应
        let mut byte_stream = response.bytes_stream();
        let mut buffer = String::new();

        while let Some(chunk_result) = byte_stream.next().await {
            match chunk_result {
                Ok(bytes) => {
                    buffer.push_str(&String::from_utf8_lossy(&bytes));

                    // 按换行分割
                    while let Some(pos) = buffer.find('\n') {
                        let line_str = buffer[..pos].trim().to_string();
                        buffer = buffer[pos + 1..].to_string();

                        if line_str.is_empty() {
                            continue;
                        }

                        // 尝试解析 JSON
                        let content = extract_delta_content(&line_str);
                        if let Some(text) = content {
                            if !text.is_empty() {
                                let chunk = OpenAIStreamChunk {
                                    id: chat_id.clone(),
                                    object: "chat.completion.chunk".to_string(),
                                    created,
                                    model: model.clone(),
                                    choices: vec![OpenAIStreamChoice {
                                        index: 0,
                                        delta: OpenAIDelta {
                                            role: None,
                                            content: Some(text),
                                        },
                                        finish_reason: None,
                                    }],
                                };
                                let sse_line = format!("data: {}\n\n",
                                    serde_json::to_string(&chunk).unwrap());
                                yield Ok(Bytes::from(sse_line));
                            }
                        }
                    }
                }
                Err(_) => break,
            }
        }

        // 处理 buffer 中剩余数据
        if !buffer.trim().is_empty() {
            if let Some(text) = extract_delta_content(buffer.trim()) {
                if !text.is_empty() {
                    let chunk = OpenAIStreamChunk {
                        id: chat_id.clone(),
                        object: "chat.completion.chunk".to_string(),
                        created,
                        model: model.clone(),
                        choices: vec![OpenAIStreamChoice {
                            index: 0,
                            delta: OpenAIDelta {
                                role: None,
                                content: Some(text),
                            },
                            finish_reason: None,
                        }],
                    };
                    let sse_line = format!("data: {}\n\n",
                        serde_json::to_string(&chunk).unwrap());
                    yield Ok(Bytes::from(sse_line));
                }
            }
        }

        // 发送 finish chunk
        let finish_chunk = OpenAIStreamChunk {
            id: chat_id.clone(),
            object: "chat.completion.chunk".to_string(),
            created,
            model: model.clone(),
            choices: vec![OpenAIStreamChoice {
                index: 0,
                delta: OpenAIDelta {
                    role: None,
                    content: None,
                },
                finish_reason: Some("stop".to_string()),
            }],
        };
        let finish_line = format!("data: {}\n\n", serde_json::to_string(&finish_chunk).unwrap());
        yield Ok(Bytes::from(finish_line));

        // [DONE]
        yield Ok(Bytes::from("data: [DONE]\n\n"));
    };

    Body::from_stream(stream)
}

/// 从 Windsurf 流式响应块中提取文本内容
pub fn extract_delta_content(line: &str) -> Option<String> {
    // 尝试解析为 JSON
    if let Ok(obj) = serde_json::from_str::<Value>(line) {
        // {"result": {"content": "..."}}
        if let Some(result) = obj.get("result") {
            if let Some(content) = result.get("content").and_then(|v| v.as_str()) {
                return Some(content.to_string());
            }
            if let Some(text) = result.get("text").and_then(|v| v.as_str()) {
                return Some(text.to_string());
            }
            if let Some(delta) = result.get("delta").and_then(|v| v.as_str()) {
                return Some(delta.to_string());
            }
        }
        // {"content": "..."}
        if let Some(content) = obj.get("content").and_then(|v| v.as_str()) {
            return Some(content.to_string());
        }
        // {"delta": {"content": "..."}}
        if let Some(delta) = obj.get("delta") {
            if let Some(content) = delta.get("content").and_then(|v| v.as_str()) {
                return Some(content.to_string());
            }
        }
        // {"text": "..."}
        if let Some(text) = obj.get("text").and_then(|v| v.as_str()) {
            return Some(text.to_string());
        }
    }

    // SSE 格式: "data: {...}"
    if line.starts_with("data: ") {
        let data = &line[6..];
        if data == "[DONE]" {
            return None;
        }
        return extract_delta_content(data);
    }

    None
}

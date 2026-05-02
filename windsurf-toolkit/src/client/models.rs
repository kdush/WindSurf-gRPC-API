use serde::{Deserialize, Serialize};

/// Windsurf 请求元数据
#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RequestMetadata {
    pub api_key: String,
    pub ide_name: String,
    pub ide_version: String,
    pub extension_version: String,
    pub locale: String,
}

impl RequestMetadata {
    pub fn new(api_key: &str) -> Self {
        Self {
            api_key: api_key.to_string(),
            ide_name: "windsurf".to_string(),
            ide_version: "1.7.3".to_string(),
            extension_version: "2.30.4".to_string(),
            locale: "en".to_string(),
        }
    }
}

/// RPC 响应
#[derive(Debug, Clone)]
pub struct RpcResponse {
    pub ok: bool,
    pub status: u16,
    pub data: serde_json::Value,
}

/// 用户状态
#[derive(Debug, Clone, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct UserStatus {
    #[serde(default)]
    pub email: String,
    #[serde(default)]
    pub plan_name: String,
    #[serde(default)]
    pub teams_tier: String,
    #[serde(default)]
    pub available_prompt_credits: i64,
    #[serde(default)]
    pub available_flow_credits: i64,
    #[serde(default)]
    pub has_paid_features: bool,
    #[serde(default)]
    pub referral_code: String,
    #[serde(default)]
    pub plan_start: String,
    #[serde(default)]
    pub plan_end: String,
}

/// 模型提供商
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ModelProvider {
    #[serde(default)]
    pub model_uid: String,
    #[serde(default)]
    pub display_name: String,
    #[serde(default)]
    pub provider: String,
    #[serde(default)]
    pub is_available: bool,
}

/// 容量检查结果
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CapacityResult {
    #[serde(default)]
    pub has_capacity: bool,
    #[serde(default)]
    pub message: String,
}

/// 聊天消息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub role: String,
    pub content: String,
}

/// 聊天补全请求 (Windsurf 格式)
#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct WindsurfChatRequest {
    pub metadata: RequestMetadata,
    pub messages: Vec<ChatMessage>,
    pub model_uid: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub temperature: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_tokens: Option<u32>,
}

/// 聊天补全请求 (OpenAI 格式)
#[derive(Debug, Clone, Deserialize)]
pub struct OpenAIChatRequest {
    pub model: String,
    pub messages: Vec<ChatMessage>,
    #[serde(default)]
    pub stream: bool,
    pub temperature: Option<f64>,
    pub max_tokens: Option<u32>,
}

/// OpenAI 格式响应
#[derive(Debug, Clone, Serialize)]
pub struct OpenAIChatResponse {
    pub id: String,
    pub object: String,
    pub created: i64,
    pub model: String,
    pub choices: Vec<OpenAIChoice>,
    pub usage: OpenAIUsage,
}

#[derive(Debug, Clone, Serialize)]
pub struct OpenAIChoice {
    pub index: u32,
    pub message: ChatMessage,
    pub finish_reason: String,
}

#[derive(Debug, Clone, Serialize, Default)]
pub struct OpenAIUsage {
    pub prompt_tokens: u32,
    pub completion_tokens: u32,
    pub total_tokens: u32,
}

/// SSE 流式 chunk
#[derive(Debug, Clone, Serialize)]
pub struct OpenAIStreamChunk {
    pub id: String,
    pub object: String,
    pub created: i64,
    pub model: String,
    pub choices: Vec<OpenAIStreamChoice>,
}

#[derive(Debug, Clone, Serialize)]
pub struct OpenAIStreamChoice {
    pub index: u32,
    pub delta: OpenAIDelta,
    pub finish_reason: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct OpenAIDelta {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub role: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
}

/// Key 状态
#[derive(Debug, Clone, Serialize)]
pub struct KeyStatus {
    pub key_preview: String,
    pub healthy: bool,
    pub available: bool,
    pub total_calls: u64,
    pub total_errors: u64,
    pub error_message: String,
}

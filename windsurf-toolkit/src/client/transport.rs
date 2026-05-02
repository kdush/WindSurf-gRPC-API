use reqwest::{Client, Response};
use serde_json::Value;
use std::time::Duration;

use super::models::{RequestMetadata, RpcResponse};

const DEFAULT_TIMEOUT: u64 = 30;

/// Windsurf Connect-protocol 客户端
#[derive(Clone)]
pub struct WindsurfClient {
    client: Client,
    base_url: String,
    api_key: String,
}

impl WindsurfClient {
    /// 创建新客户端
    pub fn new(base_url: &str, api_key: &str) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(DEFAULT_TIMEOUT))
            .danger_accept_invalid_certs(true)
            .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            .build()
            .expect("Failed to build HTTP client");

        Self {
            client,
            base_url: base_url.trim_end_matches('/').to_string(),
            api_key: api_key.to_string(),
        }
    }

    /// 创建连接到官方服务器的客户端
    pub fn official(api_key: &str) -> Self {
        Self::new("https://server.self-serve.windsurf.com", api_key)
    }

    /// 创建连接到注册服务器的客户端
    pub fn register_server() -> Self {
        Self::new("https://register.windsurf.com", "")
    }

    /// 获取 API Key
    pub fn api_key(&self) -> &str {
        &self.api_key
    }

    /// 设置 API Key
    pub fn set_api_key(&mut self, key: &str) {
        self.api_key = key.to_string();
    }

    /// 构建元数据
    pub fn metadata(&self) -> RequestMetadata {
        RequestMetadata::new(&self.api_key)
    }

    /// 调用 gRPC 方法 (非流式)
    pub async fn call(&self, service: &str, method: &str, payload: &Value) -> RpcResponse {
        let url = format!("{}/{}/{}", self.base_url, service, method);

        let result = self.client
            .post(&url)
            .header("Content-Type", "application/json")
            .header("Connect-Protocol-Version", "1")
            .header("Referer", "https://windsurf.com/")
            .header("Origin", "https://windsurf.com")
            .json(payload)
            .send()
            .await;

        match result {
            Ok(resp) => {
                let status = resp.status().as_u16();
                let ok = resp.status().is_success();
                let data = resp.json::<Value>().await.unwrap_or(Value::Null);
                RpcResponse { ok, status, data }
            }
            Err(e) => RpcResponse {
                ok: false,
                status: 0,
                data: Value::String(format!("Transport error: {}", e)),
            },
        }
    }

    /// 流式调用 — 返回 Response 供调用方逐块读取
    pub async fn call_stream(
        &self,
        service: &str,
        method: &str,
        payload: &Value,
    ) -> Result<Response, reqwest::Error> {
        let url = format!("{}/{}/{}", self.base_url, service, method);

        self.client
            .post(&url)
            .header("Content-Type", "application/json")
            .header("Connect-Protocol-Version", "1")
            .header("Referer", "https://windsurf.com/")
            .header("Origin", "https://windsurf.com")
            .json(payload)
            .send()
            .await
    }

    // ═══════════════════════════════════════
    //  高级 API 方法
    // ═══════════════════════════════════════

    /// 获取用户状态
    pub async fn get_user_status(&self) -> RpcResponse {
        let payload = serde_json::json!({
            "metadata": self.metadata()
        });
        self.call(
            "exa.seat_management_pb.SeatManagementService",
            "GetUserStatus",
            &payload,
        ).await
    }

    /// 获取模型列表
    pub async fn get_model_providers(&self) -> RpcResponse {
        let payload = serde_json::json!({
            "metadata": self.metadata()
        });
        self.call(
            "exa.api_server_pb.ApiServerService",
            "GetModelProviders",
            &payload,
        ).await
    }

    /// 检查聊天容量
    pub async fn check_chat_capacity(&self, model_uid: &str) -> RpcResponse {
        let mut payload = serde_json::json!({
            "metadata": self.metadata()
        });
        if !model_uid.is_empty() {
            payload["modelUid"] = Value::String(model_uid.to_string());
        }
        self.call(
            "exa.api_server_pb.ApiServerService",
            "CheckChatCapacity",
            &payload,
        ).await
    }

    /// 检查限速
    pub async fn check_rate_limit(&self, model_uid: &str) -> RpcResponse {
        let mut payload = serde_json::json!({
            "metadata": self.metadata()
        });
        if !model_uid.is_empty() {
            payload["modelUid"] = Value::String(model_uid.to_string());
        }
        self.call(
            "exa.api_server_pb.ApiServerService",
            "CheckUserMessageRateLimit",
            &payload,
        ).await
    }

    /// 非流式聊天补全
    pub async fn chat_completions(
        &self,
        messages: &[super::models::ChatMessage],
        model_uid: &str,
        temperature: Option<f64>,
        max_tokens: Option<u32>,
    ) -> RpcResponse {
        let mut payload = serde_json::json!({
            "metadata": self.metadata(),
            "messages": messages,
            "modelUid": model_uid,
        });
        if let Some(t) = temperature {
            payload["temperature"] = serde_json::json!(t);
        }
        if let Some(m) = max_tokens {
            payload["maxTokens"] = serde_json::json!(m);
        }
        self.call(
            "exa.api_server_pb.ApiServerService",
            "GetChatCompletions",
            &payload,
        ).await
    }

    /// 流式聊天补全 — 返回 Response 流
    pub async fn chat_completions_stream(
        &self,
        messages: &[super::models::ChatMessage],
        model_uid: &str,
        temperature: Option<f64>,
        max_tokens: Option<u32>,
    ) -> Result<Response, reqwest::Error> {
        let mut payload = serde_json::json!({
            "metadata": self.metadata(),
            "messages": messages,
            "modelUid": model_uid,
        });
        if let Some(t) = temperature {
            payload["temperature"] = serde_json::json!(t);
        }
        if let Some(m) = max_tokens {
            payload["maxTokens"] = serde_json::json!(m);
        }
        self.call_stream(
            "exa.api_server_pb.ApiServerService",
            "GetStreamingExternalChatCompletions",
            &payload,
        ).await
    }

    /// 获取 Cascade 模型配置
    pub async fn get_cascade_model_configs(&self) -> RpcResponse {
        let payload = serde_json::json!({
            "metadata": self.metadata()
        });
        self.call(
            "exa.api_server_pb.ApiServerService",
            "GetCascadeModelConfigs",
            &payload,
        ).await
    }

    /// 获取模型状态
    pub async fn get_model_statuses(&self) -> RpcResponse {
        let payload = serde_json::json!({
            "metadata": self.metadata()
        });
        self.call(
            "exa.api_server_pb.ApiServerService",
            "GetModelStatuses",
            &payload,
        ).await
    }
}

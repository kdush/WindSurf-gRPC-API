use serde::Serialize;
use std::collections::HashMap;
use std::sync::LazyLock;

/// 模型信息
#[derive(Debug, Clone)]
pub struct ModelInfo {
    pub uid: &'static str,
    pub provider: &'static str,
    pub compat_name: &'static str,
    pub display_name: &'static str,
}

/// 所有已知模型
static MODELS: LazyLock<Vec<ModelInfo>> = LazyLock::new(|| {
    vec![
        // Anthropic
        ModelInfo { uid: "claude-sonnet-4-20250514", provider: "anthropic", compat_name: "claude-sonnet-4-20250514", display_name: "Claude Sonnet 4" },
        ModelInfo { uid: "claude-3-5-sonnet", provider: "anthropic", compat_name: "claude-3-5-sonnet-20241022", display_name: "Claude 3.5 Sonnet" },
        ModelInfo { uid: "claude-3-5-haiku", provider: "anthropic", compat_name: "claude-3-5-haiku-20241022", display_name: "Claude 3.5 Haiku" },
        ModelInfo { uid: "claude-3-7-sonnet", provider: "anthropic", compat_name: "claude-3-7-sonnet-20250219", display_name: "Claude 3.7 Sonnet" },
        // OpenAI
        ModelInfo { uid: "gpt-4o", provider: "openai", compat_name: "gpt-4o", display_name: "GPT-4o" },
        ModelInfo { uid: "gpt-4o-mini", provider: "openai", compat_name: "gpt-4o-mini", display_name: "GPT-4o Mini" },
        ModelInfo { uid: "gpt-4.1", provider: "openai", compat_name: "gpt-4.1", display_name: "GPT-4.1" },
        ModelInfo { uid: "o3", provider: "openai", compat_name: "o3", display_name: "o3" },
        ModelInfo { uid: "o3-mini", provider: "openai", compat_name: "o3-mini", display_name: "o3-mini" },
        ModelInfo { uid: "o4-mini", provider: "openai", compat_name: "o4-mini", display_name: "o4-mini" },
        // Google
        ModelInfo { uid: "gemini-2.5-pro", provider: "google", compat_name: "gemini-2.5-pro", display_name: "Gemini 2.5 Pro" },
        ModelInfo { uid: "gemini-2.0-flash", provider: "google", compat_name: "gemini-2.0-flash", display_name: "Gemini 2.0 Flash" },
        ModelInfo { uid: "gemini-2.5-flash", provider: "google", compat_name: "gemini-2.5-flash", display_name: "Gemini 2.5 Flash" },
        // xAI
        ModelInfo { uid: "grok-3", provider: "xai", compat_name: "grok-3", display_name: "Grok 3" },
        ModelInfo { uid: "grok-3-mini", provider: "xai", compat_name: "grok-3-mini", display_name: "Grok 3 Mini" },
        // DeepSeek
        ModelInfo { uid: "deepseek-v3", provider: "deepseek", compat_name: "deepseek-chat", display_name: "DeepSeek V3" },
        ModelInfo { uid: "deepseek-r1", provider: "deepseek", compat_name: "deepseek-reasoner", display_name: "DeepSeek R1" },
    ]
});

/// 反向映射表
static REVERSE_MAP: LazyLock<HashMap<String, String>> = LazyLock::new(|| {
    let mut map = HashMap::new();
    for m in MODELS.iter() {
        map.insert(m.uid.to_string(), m.uid.to_string());
        map.insert(m.compat_name.to_string(), m.uid.to_string());
        map.insert(m.display_name.to_lowercase(), m.uid.to_string());
    }
    map
});

/// 解析模型名为 Windsurf modelUid
pub fn resolve_model(name: &str) -> String {
    if name.is_empty() {
        return "claude-sonnet-4-20250514".to_string();
    }

    // 精确匹配
    if let Some(uid) = REVERSE_MAP.get(name) {
        return uid.clone();
    }

    // 小写匹配
    let lower = name.to_lowercase();
    if let Some(uid) = REVERSE_MAP.get(&lower) {
        return uid.clone();
    }

    // 前缀匹配
    for m in MODELS.iter() {
        if m.uid.starts_with(&lower) || lower.starts_with(m.uid) {
            return m.uid.to_string();
        }
    }

    // 找不到 → 原样返回
    name.to_string()
}

/// OpenAI /v1/models 格式
#[derive(Debug, Serialize)]
pub struct OpenAIModel {
    pub id: String,
    pub object: String,
    pub created: i64,
    pub owned_by: String,
}

/// 列出所有模型 (OpenAI 格式)
pub fn list_models() -> Vec<OpenAIModel> {
    MODELS
        .iter()
        .map(|m| OpenAIModel {
            id: m.uid.to_string(),
            object: "model".to_string(),
            created: 1700000000,
            owned_by: m.provider.to_string(),
        })
        .collect()
}

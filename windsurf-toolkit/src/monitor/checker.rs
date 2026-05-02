use std::time::Duration;
use tokio::time::sleep;
use crate::client::WindsurfClient;

/// Key 健康检查结果
#[derive(Debug)]
pub struct KeyCheckResult {
    pub key_preview: String,
    pub valid: bool,
    pub email: String,
    pub plan: String,
    pub credits: i64,
    pub error: String,
}

/// 启动额度监控 (定期检查所有 Key)
pub async fn start_monitor(keys: Vec<String>, interval_secs: u64) {
    tracing::info!("📊 额度监控启动 ({}个Key, 间隔{}s)", keys.len(), interval_secs);

    loop {
        let results = check_all_keys(&keys).await;
        print_report(&results);
        sleep(Duration::from_secs(interval_secs)).await;
    }
}

/// 一次性检查所有 Key
pub async fn check_all_keys(keys: &[String]) -> Vec<KeyCheckResult> {
    let mut results = Vec::new();

    for key in keys {
        let result = check_single_key(key).await;
        results.push(result);
    }

    results
}

/// 检查单个 Key
pub async fn check_single_key(key: &str) -> KeyCheckResult {
    let preview = if key.len() > 16 {
        format!("{}...{}", &key[..12], &key[key.len()-4..])
    } else {
        key.to_string()
    };

    let client = WindsurfClient::official(key);
    let resp = client.get_user_status().await;

    if !resp.ok {
        return KeyCheckResult {
            key_preview: preview,
            valid: false,
            email: String::new(),
            plan: String::new(),
            credits: 0,
            error: format!("HTTP {}: {}", resp.status, resp.data),
        };
    }

    let data = &resp.data;
    let email = data.get("email")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();
    let plan = data.get("planName")
        .and_then(|v| v.as_str())
        .unwrap_or("unknown")
        .to_string();
    let prompt_credits = data.get("availablePromptCredits")
        .and_then(|v| v.as_i64())
        .unwrap_or(0);
    let flow_credits = data.get("availableFlowCredits")
        .and_then(|v| v.as_i64())
        .unwrap_or(0);

    KeyCheckResult {
        key_preview: preview,
        valid: true,
        email,
        plan,
        credits: prompt_credits + flow_credits,
        error: String::new(),
    }
}

/// 打印检查报告
fn print_report(results: &[KeyCheckResult]) {
    let now = chrono::Local::now().format("%H:%M:%S");
    println!("\n╔══════════════════════════════════════════════════╗");
    println!("║  Key 状态报告  [{}]                       ║", now);
    println!("╠══════════════════════════════════════════════════╣");

    let mut total_credits = 0i64;
    let mut valid_count = 0;

    for r in results {
        if r.valid {
            valid_count += 1;
            total_credits += r.credits;
            println!("║  ✅ {} │ {} │ {:>8} credits ║",
                     r.key_preview, r.plan, r.credits);
        } else {
            println!("║  ❌ {} │ {} ║",
                     r.key_preview, r.error);
        }
    }

    println!("╠══════════════════════════════════════════════════╣");
    println!("║  有效: {}/{} │ 总额度: {:>10}             ║",
             valid_count, results.len(), total_credits);
    println!("╚══════════════════════════════════════════════════╝");
}

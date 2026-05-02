use std::time::Duration;
use tokio::time::sleep;
use serde_json::json;


const LS_SERVICE: &str = "exa.language_server_pb.LanguageServerService";

/// Pro 实验 Key 列表
const PRO_EXPERIMENTS: &[&str] = &[
    "gpt4_enabled",
    "premium_models_enabled",
    "advanced_reasoning_enabled",
    "unlimited_usage",
    "pro_features_enabled",
    "cascade_premium_enabled",
];

/// Pro 注入守护进程
pub async fn start_daemon(api_key: &str, check_interval: u64) {
    tracing::info!("🛡️  Pro 注入守护进程启动");
    tracing::info!("   检查间隔: {}s", check_interval);

    let mut connected = false;
    let mut port: u16 = 0;
    let mut csrf_token = String::new();

    loop {
        if !connected {
            // 尝试发现 LS 进程
            match discover_ls().await {
                Some((p, token)) => {
                    port = p;
                    csrf_token = token;
                    connected = true;
                    tracing::info!("🔗 发现 LS 进程 (port={})", port);

                    // 立即注入
                    if inject_pro(port, &csrf_token, api_key).await {
                        tracing::info!("✅ Pro 实验注入成功!");
                    } else {
                        tracing::warn!("⚠️  注入失败，稍后重试");
                        connected = false;
                    }
                }
                None => {
                    tracing::debug!("等待 LS 进程...");
                }
            }
        } else {
            // 已连接 — 心跳检查
            if !heartbeat(port, &csrf_token).await {
                tracing::warn!("⚠️  LS 断开连接，等待重启...");
                connected = false;
                port = 0;
                csrf_token.clear();
            }
        }

        sleep(Duration::from_secs(if connected { check_interval } else { 10 })).await;
    }
}

/// 发现本地 LS 进程
async fn discover_ls() -> Option<(u16, String)> {
    // Windows: 通过 PowerShell 查找 Windsurf LS 进程
    let output = tokio::process::Command::new("powershell")
        .args([
            "-NoProfile", "-Command",
            r#"Get-Process | Where-Object { $_.ProcessName -like '*windsurf*' -or $_.ProcessName -like '*codeium*' } | ForEach-Object { Get-NetTCPConnection -OwningProcess $_.Id -State Listen 2>$null } | Select-Object -ExpandProperty LocalPort | Sort-Object -Unique"#
        ])
        .output()
        .await
        .ok()?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    for line in stdout.lines() {
        if let Ok(p) = line.trim().parse::<u16>() {
            if p > 1024 {
                // 尝试连接
                let client = reqwest::Client::builder()
                    .timeout(Duration::from_secs(3))
                    .danger_accept_invalid_certs(true)
                    .build()
                    .ok()?;

                let url = format!("http://127.0.0.1:{}/{}/Heartbeat", p, LS_SERVICE);
                let result = client
                    .post(&url)
                    .header("Content-Type", "application/json")
                    .header("Connect-Protocol-Version", "1")
                    .body("{}")
                    .send()
                    .await;

                if let Ok(resp) = result {
                    if resp.status().is_success() || resp.status().as_u16() == 412 {
                        // 尝试读取 CSRF token
                        let token = read_csrf_token().await.unwrap_or_default();
                        return Some((p, token));
                    }
                }
            }
        }
    }
    None
}

/// 读取 CSRF token
async fn read_csrf_token() -> Option<String> {
    let output = tokio::process::Command::new("powershell")
        .args([
            "-NoProfile", "-Command",
            r#"Get-Process | Where-Object { $_.ProcessName -like '*windsurf*' } | ForEach-Object { $_.CommandLine } | Select-String -Pattern '--csrf-token=(\S+)' | ForEach-Object { $_.Matches[0].Groups[1].Value }"#
        ])
        .output()
        .await
        .ok()?;

    let token = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if token.is_empty() { None } else { Some(token) }
}

/// 心跳检查
async fn heartbeat(port: u16, csrf_token: &str) -> bool {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(5))
        .danger_accept_invalid_certs(true)
        .build()
        .unwrap();

    let url = format!("http://127.0.0.1:{}/{}/Heartbeat", port, LS_SERVICE);
    let mut req = client
        .post(&url)
        .header("Content-Type", "application/json")
        .header("Connect-Protocol-Version", "1");

    if !csrf_token.is_empty() {
        req = req.header("x-codeium-csrf-token", csrf_token);
    }

    match req.body("{}").send().await {
        Ok(resp) => resp.status().is_success(),
        Err(_) => false,
    }
}

/// 注入 Pro 实验
async fn inject_pro(port: u16, csrf_token: &str, api_key: &str) -> bool {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(10))
        .danger_accept_invalid_certs(true)
        .build()
        .unwrap();

    let url = format!("http://127.0.0.1:{}/{}/SetBaseExperiments", port, LS_SERVICE);

    // 构建实验 payload
    let experiments: Vec<serde_json::Value> = PRO_EXPERIMENTS
        .iter()
        .map(|key| json!({"key": key, "value": true}))
        .collect();

    let payload = json!({
        "metadata": {
            "apiKey": api_key,
            "ideName": "windsurf",
            "ideVersion": "1.7.3",
            "extensionVersion": "2.30.4",
            "locale": "en"
        },
        "experiments": experiments
    });

    let mut req = client
        .post(&url)
        .header("Content-Type", "application/json")
        .header("Connect-Protocol-Version", "1");

    if !csrf_token.is_empty() {
        req = req.header("x-codeium-csrf-token", csrf_token);
    }

    match req.json(&payload).send().await {
        Ok(resp) => resp.status().is_success(),
        Err(e) => {
            tracing::error!("注入请求失败: {}", e);
            false
        }
    }
}

#![allow(dead_code, unused_imports)]

mod client;
mod proxy;
mod daemon;
mod monitor;
mod web;
mod gui;

use clap::{Parser, Subcommand};
use std::fs;

#[derive(Parser)]
#[command(
    name = "windsurf-toolkit",
    version = "1.0.0",
    about = "⚡ Windsurf IDE 全功能工具箱 — 反代/注入/监控/面板",
    long_about = "Windsurf IDE 全功能工具箱\n\n\
        功能:\n  \
        • proxy  — OpenAI 兼容反代服务器 (streaming + 多Key轮换)\n  \
        • daemon — Pro 实验注入守护进程\n  \
        • check  — 批量验证 Key 有效性和额度\n  \
        • monitor — 持续监控 Key 额度\n  \
        • status — 查看单个 Key 用户状态\n  \
        • models — 列出可用 AI 模型\n  \
        • gui    — 启动图形界面 (默认)"
)]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Clone, Subcommand)]
enum Commands {
    /// 启动 OpenAI 兼容反代服务器
    Proxy {
        /// API Key 列表 (逗号分隔)
        #[arg(short, long)]
        keys: Option<String>,

        /// Key 文件路径 (每行一个)
        #[arg(short = 'f', long)]
        key_file: Option<String>,

        /// 监听端口
        #[arg(short, long, default_value = "8080")]
        port: u16,

        /// 监听地址
        #[arg(long, default_value = "0.0.0.0")]
        host: String,

        /// 客户端认证 token
        #[arg(short, long)]
        auth: Option<String>,

        /// Windsurf API 服务器
        #[arg(short, long, default_value = "https://server.self-serve.windsurf.com")]
        server: String,

        /// Key 错误冷却秒数
        #[arg(long, default_value = "60")]
        cooldown: u64,

        /// 连续错误阈值
        #[arg(long, default_value = "10")]
        max_errors: u32,

        /// 开启 Web 管理面板
        #[arg(long)]
        dashboard: bool,
    },

    /// Pro 实验注入守护进程
    Daemon {
        /// API Key
        #[arg(short, long, default_value = "")]
        key: String,

        /// 检查间隔秒数
        #[arg(short, long, default_value = "30")]
        interval: u64,
    },

    /// 批量验证 Key 有效性
    Check {
        /// API Key 列表 (逗号分隔)
        #[arg(short, long)]
        keys: Option<String>,

        /// Key 文件路径
        #[arg(short = 'f', long)]
        key_file: Option<String>,
    },

    /// 持续监控 Key 额度
    Monitor {
        /// API Key 列表 (逗号分隔)
        #[arg(short, long)]
        keys: Option<String>,

        /// Key 文件路径
        #[arg(short = 'f', long)]
        key_file: Option<String>,

        /// 检查间隔秒数
        #[arg(short, long, default_value = "300")]
        interval: u64,
    },

    /// 查看用户状态
    Status {
        /// API Key
        #[arg()]
        key: String,
    },

    /// 列出可用模型
    Models,

    /// 启动图形界面
    Gui,
}

/// 从参数收集 Keys
fn collect_keys(keys_arg: &Option<String>, file_arg: &Option<String>) -> Vec<String> {
    let mut keys = Vec::new();

    if let Some(ref k) = keys_arg {
        keys.extend(k.split(',').map(|s| s.trim().to_string()).filter(|s| !s.is_empty()));
    }

    if let Some(ref path) = file_arg {
        match fs::read_to_string(path) {
            Ok(content) => {
                for line in content.lines() {
                    let line = line.trim();
                    if !line.is_empty() && !line.starts_with('#') {
                        keys.push(line.to_string());
                    }
                }
            }
            Err(e) => {
                eprintln!("❌ 无法读取 Key 文件 {}: {}", path, e);
                std::process::exit(1);
            }
        }
    }

    // 环境变量
    if let Ok(env_keys) = std::env::var("WINDSURF_KEYS") {
        keys.extend(env_keys.split(',').map(|s| s.trim().to_string()).filter(|s| !s.is_empty()));
    }

    // 去重
    let mut seen = std::collections::HashSet::new();
    keys.retain(|k| seen.insert(k.clone()));

    keys
}

#[tokio::main]
async fn main() {
    // 初始化日志
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .with_target(false)
        .init();

    let cli = Cli::parse();

    match cli.command.clone().unwrap_or(Commands::Gui) {
        Commands::Proxy {
            keys, key_file, port, host, auth, server,
            cooldown, max_errors, dashboard,
        } => {
            let all_keys = collect_keys(&keys, &key_file);
            if all_keys.is_empty() {
                eprintln!("❌ 没有提供 API Key!");
                eprintln!("   用 --keys sk-ws-xxx 或 --key-file keys.txt 或设置 WINDSURF_KEYS 环境变量");
                std::process::exit(1);
            }

            tracing::info!("📦 加载了 {} 个 API Key", all_keys.len());

            if dashboard {
                // 启动带面板的反代 — 在 proxy 路由中加入 /dashboard
                tracing::info!("📊 Web 面板已开启: http://{}:{}/dashboard", host, port);
            }

            proxy::start_proxy(all_keys, port, &host, &server, auth, cooldown, max_errors).await;
        }

        Commands::Daemon { key, interval } => {
            daemon::start_daemon(&key, interval).await;
        }

        Commands::Check { keys, key_file } => {
            let all_keys = collect_keys(&keys, &key_file);
            if all_keys.is_empty() {
                eprintln!("❌ 没有提供 Key");
                std::process::exit(1);
            }
            println!("🔍 检查 {} 个 Key...\n", all_keys.len());
            let results = monitor::checker::check_all_keys(&all_keys).await;
            let valid = results.iter().filter(|r| r.valid).count();
            let total_credits: i64 = results.iter().filter(|r| r.valid).map(|r| r.credits).sum();

            println!("╔══════════════════════════════════════════════════╗");
            println!("║  Key 验证报告                                   ║");
            println!("╠══════════════════════════════════════════════════╣");
            for r in &results {
                if r.valid {
                    println!("║  ✅ {} │ {} │ {:>6} cr ║",
                             r.key_preview, r.plan, r.credits);
                } else {
                    println!("║  ❌ {} │ {}  ║", r.key_preview, r.error);
                }
            }
            println!("╠══════════════════════════════════════════════════╣");
            println!("║  有效: {}/{} │ 总额度: {:>10}             ║",
                     valid, results.len(), total_credits);
            println!("╚══════════════════════════════════════════════════╝");
        }

        Commands::Monitor { keys, key_file, interval } => {
            let all_keys = collect_keys(&keys, &key_file);
            if all_keys.is_empty() {
                eprintln!("❌ 没有提供 Key");
                std::process::exit(1);
            }
            monitor::start_monitor(all_keys, interval).await;
        }

        Commands::Status { key } => {
            let client = client::WindsurfClient::official(&key);
            let resp = client.get_user_status().await;
            if resp.ok {
                let d = &resp.data;
                println!("📋 用户状态:");
                println!("  Email:   {}", d.get("email").and_then(|v| v.as_str()).unwrap_or("-"));
                println!("  Plan:    {}", d.get("planName").and_then(|v| v.as_str()).unwrap_or("-"));
                println!("  Tier:    {}", d.get("teamsTier").and_then(|v| v.as_str()).unwrap_or("-"));
                println!("  Credits: P={} F={}",
                         d.get("availablePromptCredits").and_then(|v| v.as_i64()).unwrap_or(0),
                         d.get("availableFlowCredits").and_then(|v| v.as_i64()).unwrap_or(0));
                println!("  Pro:     {}", d.get("hasPaidFeatures").and_then(|v| v.as_bool()).unwrap_or(false));
                println!("  Period:  {} → {}",
                         d.get("planStart").and_then(|v| v.as_str()).unwrap_or("-"),
                         d.get("planEnd").and_then(|v| v.as_str()).unwrap_or("-"));
            } else {
                eprintln!("❌ 查询失败: HTTP {} — {}", resp.status, resp.data);
            }
        }

        Commands::Models => {
            let models = proxy::models_map::list_models();
            println!("🤖 可用模型 ({}):\n", models.len());
            for m in &models {
                println!("  {} ({})", m.id, m.owned_by);
            }
        }

        Commands::Gui => {
            if let Err(e) = gui::run_gui() {
                eprintln!("❌ GUI 启动失败: {}", e);
                std::process::exit(1);
            }
        }
    }
}

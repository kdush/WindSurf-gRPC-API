use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// 持久化到磁盘的配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub keys: Vec<String>,
    pub proxy_host: String,
    pub proxy_port: u16,
    pub server_url: String,
    pub auth_token: String,
    pub cooldown_secs: u64,
    pub max_errors: u32,
    pub monitor_interval: u64,
    pub inject_check_interval: u32,
    pub ls_port: u16,
    pub internal_secret: String,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            keys: Vec::new(),
            proxy_host: "0.0.0.0".to_string(),
            proxy_port: 8080,
            server_url: "https://server.self-serve.windsurf.com".to_string(),
            auth_token: String::new(),
            cooldown_secs: 60,
            max_errors: 10,
            monitor_interval: 300,
            inject_check_interval: 30,
            ls_port: 0,
            internal_secret: String::new(),
        }
    }
}

impl Config {
    /// 获取配置文件路径 (%APPDATA%/windsurf-toolkit/config.json)
    pub fn path() -> PathBuf {
        let appdata = std::env::var("APPDATA")
            .or_else(|_| std::env::var("HOME"))
            .unwrap_or_else(|_| ".".to_string());
        PathBuf::from(appdata).join("windsurf-toolkit").join("config.json")
    }

    /// 从磁盘加载，如果失败返回默认值
    pub fn load() -> Self {
        let path = Self::path();
        match std::fs::read_to_string(&path) {
            Ok(content) => serde_json::from_str(&content).unwrap_or_default(),
            Err(_) => Self::default(),
        }
    }

    /// 保存到磁盘
    pub fn save(&self) -> Result<(), String> {
        let path = Self::path();
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).map_err(|e| format!("创建目录失败: {}", e))?;
        }
        let content = serde_json::to_string_pretty(self).map_err(|e| format!("序列化失败: {}", e))?;
        std::fs::write(&path, content).map_err(|e| format!("写入失败: {}", e))?;
        Ok(())
    }
}

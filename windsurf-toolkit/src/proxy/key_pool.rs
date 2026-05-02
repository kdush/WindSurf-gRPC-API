use parking_lot::RwLock;
use std::sync::Arc;
use std::time::{Duration, Instant};

use crate::client::models::KeyStatus;

/// 单个 Key 的运行状态
#[derive(Debug, Clone)]
struct KeyState {
    key: String,
    healthy: bool,
    total_calls: u64,
    total_errors: u64,
    consecutive_errors: u32,
    last_used: Option<Instant>,
    last_error: Option<Instant>,
    cooldown_until: Option<Instant>,
    error_message: String,
}

impl KeyState {
    fn new(key: String) -> Self {
        Self {
            key,
            healthy: true,
            total_calls: 0,
            total_errors: 0,
            consecutive_errors: 0,
            last_used: None,
            last_error: None,
            cooldown_until: None,
            error_message: String::new(),
        }
    }

    fn is_available(&self) -> bool {
        if !self.healthy {
            return false;
        }
        match self.cooldown_until {
            Some(until) => Instant::now() >= until,
            None => true,
        }
    }
}

/// 多 Key 轮换池
/// 线程安全，支持高并发访问
#[derive(Clone)]
pub struct KeyPool {
    inner: Arc<RwLock<KeyPoolInner>>,
}

struct KeyPoolInner {
    states: Vec<KeyState>,
    index: usize,
    cooldown: Duration,
    max_errors: u32,
}

impl KeyPool {
    /// 创建 Key 池
    ///
    /// # Arguments
    /// * `keys` - API Key 列表
    /// * `cooldown_secs` - 错误后冷却秒数
    /// * `max_errors` - 连续错误阈值 (超过则标记不健康)
    pub fn new(keys: Vec<String>, cooldown_secs: u64, max_errors: u32) -> Self {
        let states: Vec<KeyState> = keys
            .into_iter()
            .filter(|k| !k.trim().is_empty())
            .map(|k| KeyState::new(k.trim().to_string()))
            .collect();

        Self {
            inner: Arc::new(RwLock::new(KeyPoolInner {
                states,
                index: 0,
                cooldown: Duration::from_secs(cooldown_secs),
                max_errors,
            })),
        }
    }

    /// 池中 Key 总数
    pub fn size(&self) -> usize {
        self.inner.read().states.len()
    }

    /// 可用 Key 数量
    pub fn available_count(&self) -> usize {
        self.inner.read().states.iter().filter(|s| s.is_available()).count()
    }

    /// 获取下一个可用 Key (Round-Robin)
    pub fn next(&self) -> Option<String> {
        let mut pool = self.inner.write();
        let n = pool.states.len();
        if n == 0 {
            return None;
        }

        // Round-Robin 找可用的
        for _ in 0..n {
            let idx = pool.index % n;
            pool.index += 1;
            if pool.states[idx].is_available() {
                pool.states[idx].last_used = Some(Instant::now());
                pool.states[idx].total_calls += 1;
                return Some(pool.states[idx].key.clone());
            }
        }

        // 全部冷却中 — 返回最快解除冷却的
        let soonest = pool.states.iter_mut()
            .min_by_key(|s| s.cooldown_until.unwrap_or(Instant::now()));
        soonest.map(|s| {
            s.last_used = Some(Instant::now());
            s.total_calls += 1;
            s.key.clone()
        })
    }

    /// 报告调用成功
    pub fn report_success(&self, key: &str) {
        let mut pool = self.inner.write();
        if let Some(state) = pool.states.iter_mut().find(|s| s.key == key) {
            state.healthy = true;
            state.consecutive_errors = 0;
            state.error_message.clear();
        }
    }

    /// 报告调用错误
    pub fn report_error(&self, key: &str, message: &str, permanent: bool) {
        let mut pool = self.inner.write();
        let cooldown = pool.cooldown;
        let max_errors = pool.max_errors;

        if let Some(state) = pool.states.iter_mut().find(|s| s.key == key) {
            state.total_errors += 1;
            state.consecutive_errors += 1;
            state.last_error = Some(Instant::now());
            state.error_message = message.to_string();

            if permanent {
                state.healthy = false;
                state.cooldown_until = None; // 永久禁用
            } else if state.consecutive_errors >= max_errors {
                state.healthy = false;
                state.cooldown_until = Some(Instant::now() + cooldown * 5);
            } else {
                state.cooldown_until = Some(Instant::now() + cooldown);
            }
        }
    }

    /// 重置所有 Key 状态
    pub fn reset_all(&self) {
        let mut pool = self.inner.write();
        for state in pool.states.iter_mut() {
            state.healthy = true;
            state.consecutive_errors = 0;
            state.cooldown_until = None;
            state.error_message.clear();
        }
    }

    /// 动态添加 Key
    pub fn add_key(&self, key: &str) {
        let mut pool = self.inner.write();
        let key = key.trim().to_string();
        if !key.is_empty() && !pool.states.iter().any(|s| s.key == key) {
            pool.states.push(KeyState::new(key));
        }
    }

    /// 动态移除 Key
    pub fn remove_key(&self, key: &str) {
        let mut pool = self.inner.write();
        pool.states.retain(|s| s.key != key);
    }

    /// 获取所有 Key 状态快照
    pub fn status(&self) -> Vec<KeyStatus> {
        let pool = self.inner.read();
        pool.states
            .iter()
            .map(|s| {
                let preview = if s.key.len() > 16 {
                    format!("{}...{}", &s.key[..12], &s.key[s.key.len()-4..])
                } else {
                    s.key.clone()
                };
                KeyStatus {
                    key_preview: preview,
                    healthy: s.healthy,
                    available: s.is_available(),
                    total_calls: s.total_calls,
                    total_errors: s.total_errors,
                    error_message: s.error_message.clone(),
                }
            })
            .collect()
    }
}

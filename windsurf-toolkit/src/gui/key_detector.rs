use std::path::PathBuf;
use std::collections::HashSet;

/// 已知的 Windsurf 配置文件路径
fn candidate_paths() -> Vec<PathBuf> {
    let mut paths = Vec::new();
    let appdata = std::env::var("APPDATA").ok();
    let userprofile = std::env::var("USERPROFILE").ok();
    let local = std::env::var("LOCALAPPDATA").ok();
    let home = std::env::var("HOME").ok();

    // Windsurf 编辑器主存储 (Windows)
    if let Some(a) = &appdata {
        let windsurf = PathBuf::from(a).join("Windsurf");
        paths.push(windsurf.join("User").join("globalStorage").join("state.vscdb"));
        paths.push(windsurf.join("User").join("globalStorage").join("storage.json"));

        // Cache/Storage 目录 (新版本 Windsurf 在这里存储 session token)
        paths.extend(scan_dir_files(&windsurf.join("Cache").join("Cache_Data"), 30));
        paths.extend(scan_dir_files(&windsurf.join("Code Cache").join("js"), 30));
        paths.extend(scan_dir_files(&windsurf.join("IndexedDB"), 50));
        paths.extend(scan_dir_files(&windsurf.join("Local Storage").join("leveldb"), 30));
        paths.extend(scan_dir_files(&windsurf.join("Session Storage"), 30));
    }

    // .codeium 目录 (跨平台)
    if let Some(u) = &userprofile {
        let codeium = PathBuf::from(u).join(".codeium").join("windsurf");
        paths.push(codeium.join("user_settings.pb"));
        paths.push(codeium.join("config.json"));
        paths.push(PathBuf::from(u).join(".codeium").join("config.json"));
    }
    if let Some(h) = &home {
        let codeium = PathBuf::from(h).join(".codeium").join("windsurf");
        paths.push(codeium.join("user_settings.pb"));
        paths.push(codeium.join("config.json"));
    }

    // VSCode/Cursor 中的 Codeium 扩展存储 (备选)
    if let Some(a) = &appdata {
        paths.push(PathBuf::from(a).join("Code").join("User").join("globalStorage").join("codeium.codeium").join("data.json"));
        paths.push(PathBuf::from(a).join("Cursor").join("User").join("globalStorage").join("codeium.codeium").join("data.json"));
    }
    if let Some(l) = &local {
        paths.push(PathBuf::from(l).join("Programs").join("Windsurf").join("resources").join("config.json"));
    }

    paths
}

/// 列出目录中的小文件 (用于扫描 cache)
fn scan_dir_files(dir: &PathBuf, max: usize) -> Vec<PathBuf> {
    let Ok(entries) = std::fs::read_dir(dir) else { return Vec::new() };
    let mut paths: Vec<PathBuf> = entries
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| {
            if !p.is_file() { return false; }
            let Ok(meta) = p.metadata() else { return false };
            // 只扫描合理大小的文件 (1KB ~ 5MB)
            meta.len() > 1024 && meta.len() < 5 * 1024 * 1024
        })
        .take(max)
        .collect();
    // 优先扫描最新文件
    paths.sort_by(|a, b| {
        let am = a.metadata().and_then(|m| m.modified()).ok();
        let bm = b.metadata().and_then(|m| m.modified()).ok();
        bm.cmp(&am)
    });
    paths
}

/// 尝试读取文件 (即使被锁定，也尝试通过临时副本读取)
fn try_read_bytes(path: &PathBuf) -> Option<Vec<u8>> {
    if !path.exists() {
        return None;
    }
    // 直接读取
    if let Ok(bytes) = std::fs::read(path) {
        return Some(bytes);
    }
    // 复制到临时文件再读取 (绕过文件锁)
    let temp_dir = std::env::temp_dir();
    let temp_path = temp_dir.join(format!(
        "windsurf-toolkit-detect-{}.bin",
        path.file_name().and_then(|s| s.to_str()).unwrap_or("file")
    ));
    if std::fs::copy(path, &temp_path).is_ok() {
        let result = std::fs::read(&temp_path).ok();
        let _ = std::fs::remove_file(&temp_path);
        return result;
    }
    None
}

/// 在字节流中扫描 Windsurf API Key (sk-ws-... 格式)
fn extract_keys(data: &[u8]) -> Vec<String> {
    let text = String::from_utf8_lossy(data);
    let mut found = HashSet::new();

    // 状态机扫描: 寻找 "sk-ws-" 后跟字母数字/下划线/破折号 (最少 16 个字符)
    let bytes = text.as_bytes();
    let needle = b"sk-ws-";
    let mut i = 0;
    while i + needle.len() <= bytes.len() {
        if &bytes[i..i+needle.len()] == needle {
            let start = i;
            let mut end = i + needle.len();
            // 收集合法字符
            while end < bytes.len() {
                let c = bytes[end];
                if c.is_ascii_alphanumeric() || c == b'_' || c == b'-' || c == b'.' {
                    end += 1;
                } else {
                    break;
                }
            }
            let key_len = end - start;
            // 合理的 sk-ws- key 长度: 22 ~ 256
            // 新版 Windsurf key 格式: sk-ws-01-... (~100 chars)
            // 旧版: sk-ws-XXXXX (~20+ chars)
            if key_len >= 22 && key_len <= 256 {
                if let Ok(s) = std::str::from_utf8(&bytes[start..end]) {
                    found.insert(s.to_string());
                }
            }
            i = end;
        } else {
            i += 1;
        }
    }

    found.into_iter().collect()
}

/// 探测系统中所有的 Windsurf API Key
pub fn detect_windsurf_keys() -> DetectionResult {
    let mut result = DetectionResult::default();

    for path in candidate_paths() {
        if !path.exists() {
            continue;
        }
        result.scanned.push(path.display().to_string());

        if let Some(bytes) = try_read_bytes(&path) {
            let keys = extract_keys(&bytes);
            for k in keys {
                if !result.keys.contains(&k) {
                    result.keys.push(k);
                    result.found_in.push(path.display().to_string());
                }
            }
        }
    }

    // 按长度降序排列 — 新版 sk-ws-01- (~100 chars) 比旧版 sk-ws- (~30 chars) 更可能有效
    let mut indexed: Vec<(String, String)> = result.keys.iter()
        .zip(result.found_in.iter())
        .map(|(k, f)| (k.clone(), f.clone()))
        .collect();
    indexed.sort_by(|a, b| b.0.len().cmp(&a.0.len()));
    result.keys = indexed.iter().map(|(k, _)| k.clone()).collect();
    result.found_in = indexed.iter().map(|(_, f)| f.clone()).collect();

    result
}

/// 探测结果
#[derive(Debug, Default)]
pub struct DetectionResult {
    pub keys: Vec<String>,
    pub found_in: Vec<String>,
    pub scanned: Vec<String>,
}

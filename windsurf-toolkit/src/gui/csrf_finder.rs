//! 从 Windsurf Language Server 进程提取 CSRF Token
//!
//! 发现: Windsurf 通过环境变量 `WINDSURF_CSRF_TOKEN` 把 CSRF 传给 LS.
//! 实现: 通过 PEB (Process Environment Block) 读取 LS 进程的 env 块,
//!       从中提取 `WINDSURF_CSRF_TOKEN=<UUID>`.
//!
//! 需要 PROCESS_QUERY_INFORMATION | PROCESS_VM_READ 权限 (管理员).
#![cfg(windows)]

use std::ffi::c_void;

#[link(name = "kernel32")]
extern "system" {
    fn OpenProcess(access: u32, inherit: i32, pid: u32) -> isize;
    fn CloseHandle(h: isize) -> i32;
    fn ReadProcessMemory(h: isize, base: *const c_void, buf: *mut u8, size: usize, read: *mut usize) -> i32;
}

#[link(name = "ntdll")]
extern "system" {
    fn NtQueryInformationProcess(
        process: isize,
        class: u32,
        info: *mut c_void,
        len: u32,
        ret_len: *mut u32,
    ) -> i32;
}

const PROCESS_QUERY_INFORMATION: u32 = 0x0400;
const PROCESS_VM_READ: u32 = 0x0010;

/// ProcessBasicInformation 结构 (x64)
#[repr(C)]
#[derive(Default)]
struct ProcessBasicInformation {
    _reserved1: usize,
    peb_base_address: usize,
    _reserved2: [usize; 2],
    _unique_process_id: usize,
    _reserved3: usize,
}

/// 读取进程的完整环境变量块 (UTF-16 LE, NUL 分隔, 双 NUL 结尾)
pub fn read_process_env(pid: u32) -> Option<String> {
    let h = unsafe { OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, 0, pid) };
    if h == 0 { return None; }

    let result = (|| -> Option<String> {
        // 1. 获取 PEB 地址
        let mut pbi = ProcessBasicInformation::default();
        let mut ret_len: u32 = 0;
        let nt_status = unsafe {
            NtQueryInformationProcess(
                h, 0,
                &mut pbi as *mut _ as *mut c_void,
                std::mem::size_of::<ProcessBasicInformation>() as u32,
                &mut ret_len,
            )
        };
        if nt_status != 0 { return None; }
        let peb = pbi.peb_base_address;
        if peb == 0 { return None; }

        // 2. 读 PEB->ProcessParameters (offset 0x20 on x64)
        let mut ptr_buf = [0u8; 8];
        let mut bytes_read: usize = 0;
        let ok = unsafe {
            ReadProcessMemory(h, (peb + 0x20) as *const c_void,
                ptr_buf.as_mut_ptr(), 8, &mut bytes_read)
        };
        if ok == 0 { return None; }
        let process_params = usize::from_le_bytes(ptr_buf);

        // 3. 读 ProcessParameters->Environment (offset 0x80 on x64)
        let ok = unsafe {
            ReadProcessMemory(h, (process_params + 0x80) as *const c_void,
                ptr_buf.as_mut_ptr(), 8, &mut bytes_read)
        };
        if ok == 0 { return None; }
        let env_addr = usize::from_le_bytes(ptr_buf);

        // 4. 读 ProcessParameters->EnvironmentSize (offset 0x3F0 on x64)
        let ok = unsafe {
            ReadProcessMemory(h, (process_params + 0x3F0) as *const c_void,
                ptr_buf.as_mut_ptr(), 8, &mut bytes_read)
        };
        let env_size = if ok != 0 {
            let declared = usize::from_le_bytes(ptr_buf);
            // 如果声明值不可信, 默认用 2MB
            if declared >= 1024 && declared <= 4 * 1024 * 1024 { declared } else { 2 * 1024 * 1024 }
        } else {
            2 * 1024 * 1024
        };

        // 5. 读取整个 env 块
        let mut buf = vec![0u8; env_size];
        let ok = unsafe {
            ReadProcessMemory(h, env_addr as *const c_void,
                buf.as_mut_ptr(), env_size, &mut bytes_read)
        };
        if ok == 0 || bytes_read < 4 { return None; }
        buf.truncate(bytes_read);

        // 6. UTF-16 LE 解码
        let u16_slice: &[u16] = unsafe {
            std::slice::from_raw_parts(buf.as_ptr() as *const u16, bytes_read / 2)
        };
        Some(String::from_utf16_lossy(u16_slice))
    })();

    unsafe { CloseHandle(h); }
    result
}

/// 从 LS 进程读取 `WINDSURF_CSRF_TOKEN` 环境变量值
pub fn read_csrf_token(pid: u32) -> Option<String> {
    let env = read_process_env(pid)?;
    // env 字符串是 NUL 分隔, 每个 entry 形如 "KEY=VALUE"
    for entry in env.split('\0') {
        if let Some(rest) = entry.strip_prefix("WINDSURF_CSRF_TOKEN=") {
            let token = rest.trim().to_string();
            if !token.is_empty() { return Some(token); }
        }
    }
    None
}

/// 找到 LS 的 CSRF Token (向后兼容的 API)
/// 先读环境变量, 若无则返回 None
pub async fn find_csrf_for_ls(pid: u32, _port: u16) -> Option<String> {
    read_csrf_token(pid)
}

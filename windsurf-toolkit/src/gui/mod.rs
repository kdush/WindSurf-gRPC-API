pub mod app;
pub mod theme;
pub mod icons;
pub mod widgets;
pub mod config;
pub mod key_detector;
pub mod csrf_finder;
pub mod membership;
pub mod pages;

pub use app::ToolkitApp;

/// 启动 GUI 应用
pub fn run_gui() -> eframe::Result<()> {
    // 尝试自动提权 (Windows UAC), 已是管理员时直接继续
    #[cfg(windows)]
    {
        let already_tried = std::env::args().any(|a| a == "--elevated" || a == "--no-elevate");
        if !already_tried && !is_elevated() {
            if relaunch_elevated() {
                // 提权子进程已启动, 当前进程退出
                std::process::exit(0);
            }
            // 提权被用户拒绝或失败, 继续以非管理员运行
        }
    }

    let options = eframe::NativeOptions {
        viewport: eframe::egui::ViewportBuilder::default()
            .with_title("Windsurf Toolkit")
            .with_inner_size([1280.0, 820.0])
            .with_min_inner_size([960.0, 600.0])
            .with_decorations(false)    // 禁用 Windows 默认标题栏
            .with_transparent(false)
            .with_resizable(true),
        ..Default::default()
    };

    eframe::run_native(
        "Windsurf Toolkit",
        options,
        Box::new(|cc| Ok(Box::new(ToolkitApp::new(cc)))),
    )
}

/// 判断当前进程是否以管理员身份运行
#[cfg(windows)]
fn is_elevated() -> bool {
    use std::ffi::c_void;
    use std::mem::size_of;

    #[link(name = "advapi32")]
    extern "system" {
        fn OpenProcessToken(process: isize, access: u32, token: *mut isize) -> i32;
        fn GetTokenInformation(token: isize, class: u32, info: *mut c_void,
                               len: u32, ret_len: *mut u32) -> i32;
    }
    #[link(name = "kernel32")]
    extern "system" {
        fn GetCurrentProcess() -> isize;
        fn CloseHandle(h: isize) -> i32;
    }

    const TOKEN_QUERY: u32 = 0x0008;
    const TOKEN_ELEVATION: u32 = 20;

    unsafe {
        let mut token: isize = 0;
        if OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &mut token) == 0 {
            return false;
        }
        let mut elevation: u32 = 0;
        let mut ret_len: u32 = 0;
        let ok = GetTokenInformation(
            token,
            TOKEN_ELEVATION,
            &mut elevation as *mut _ as *mut c_void,
            size_of::<u32>() as u32,
            &mut ret_len,
        );
        CloseHandle(token);
        ok != 0 && elevation != 0
    }
}

/// 通过 ShellExecute runas 动作重启自身以请求 UAC 提权
/// 返回 true 表示提权子进程已启动 (应退出当前进程)
#[cfg(windows)]
fn relaunch_elevated() -> bool {
    use std::os::windows::ffi::OsStrExt;

    #[link(name = "shell32")]
    extern "system" {
        fn ShellExecuteW(
            hwnd: isize,
            operation: *const u16,
            file: *const u16,
            parameters: *const u16,
            directory: *const u16,
            show_cmd: i32,
        ) -> isize;
    }

    let exe = match std::env::current_exe() {
        Ok(p) => p,
        Err(_) => return false,
    };
    // 附加 --elevated 标志, 防止循环提权
    let mut args: Vec<String> = std::env::args().skip(1).collect();
    args.push("--elevated".to_string());
    let params = args.join(" ");

    let to_wide = |s: &std::ffi::OsStr| -> Vec<u16> {
        s.encode_wide().chain(std::iter::once(0)).collect()
    };
    let verb: Vec<u16> = "runas\0".encode_utf16().collect();
    let file: Vec<u16> = to_wide(exe.as_os_str());
    let params_os = std::ffi::OsString::from(&params);
    let params_w: Vec<u16> = to_wide(&params_os);
    let dir: Vec<u16> = match exe.parent() {
        Some(d) => to_wide(d.as_os_str()),
        None => vec![0u16],
    };

    // SW_SHOWNORMAL = 1
    let result = unsafe {
        ShellExecuteW(0, verb.as_ptr(), file.as_ptr(), params_w.as_ptr(), dir.as_ptr(), 1)
    };

    // 返回值 > 32 表示成功
    result > 32
}

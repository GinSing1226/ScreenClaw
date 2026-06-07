//! ScreenClaw - AI应用的可视化操作必备伴侣

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::atomic::{AtomicBool, AtomicU32};
use std::sync::Arc;
use std::process::Child;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, WindowEvent
};
use serde::{Deserialize, Serialize};
use tokio::sync::Mutex;

/// Python 服务进程 PID，用于 Ctrl+C / 控制台关闭时同步清理
pub static PYTHON_SERVICE_PID: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0);

/// Windows 控制台 Ctrl+C 处理器 — 收到信号后立即 taskkill Python 子进程树
#[cfg(target_os = "windows")]
unsafe extern "system" fn console_ctrl_handler(ctrl_type: u32) -> i32 {
    use std::sync::atomic::Ordering;
    const CTRL_C_EVENT: u32 = 0;
    const CTRL_BREAK_EVENT: u32 = 1;
    const CTRL_CLOSE_EVENT: u32 = 2;

    if matches!(ctrl_type, CTRL_C_EVENT | CTRL_BREAK_EVENT | CTRL_CLOSE_EVENT) {
        let pid = PYTHON_SERVICE_PID.load(Ordering::SeqCst);
        if pid != 0 {
            use std::os::windows::process::CommandExt;
            const CREATE_NO_WINDOW: u32 = 0x08000000;
            let _ = std::process::Command::new("taskkill")
                .args(["/F", "/T", "/PID", &pid.to_string()])
                .creation_flags(CREATE_NO_WINDOW)
                .status();
        }
    }
    0 // FALSE — 继续传递给默认处理程序以终止进程
}

// 全局状态
pub struct AppState {
    pub python_process: Mutex<Option<Child>>,
    pub is_service_running: AtomicBool,
    pub config: Mutex<Config>,
    pub hotkey_thread_id: AtomicU32, // 热键监听线程ID，用于通知重新注册
}

// 配置结构 - 与Python AppConfig匹配
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Config {
    pub server: ServerConfig,
    pub screenshot: ScreenshotConfig,
    #[serde(default)]
    pub input: InputConfig,
    pub security: SecurityConfig,
    #[serde(default)]
    pub log: LogConfig,
    pub ui: UIConfig,
    #[serde(default)]
    pub delegated: DelegatedConfig,
    #[serde(default)]
    pub scroll_screenshot: ScrollScreenshotConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    #[serde(default = "default_port")]
    pub port: u16,
    #[serde(default)]
    pub host: String,
    #[serde(default)]
    pub token: String,
    #[serde(default)]
    pub local_ip: String,
    #[serde(default = "default_true")]
    pub auto_start: bool,
    #[serde(default = "default_true")]
    pub service_enabled: bool,
}

fn default_port() -> u16 { 12261 }
fn default_true() -> bool { true }

impl Default for ServerConfig {
    fn default() -> Self {
        ServerConfig {
            port: 12261,
            host: "0.0.0.0".to_string(),
            token: String::new(),
            local_ip: "127.0.0.1".to_string(),
            auto_start: true,
            service_enabled: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScreenshotConfig {
    #[serde(default = "default_coordinate_type")]
    pub default_coordinate_type: String,
    #[serde(default = "default_color_mode")]
    pub default_color_mode: String,
    #[serde(default = "default_grid_density")]
    pub default_grid_density: f32,
    #[serde(default = "default_grid_opacity")]
    pub default_grid_opacity: i32,
    #[serde(default = "default_grid_color")]
    pub default_grid_color: String,
    #[serde(default = "default_number_density")]
    pub default_number_density: i32,
    #[serde(default = "default_number_decimal")]
    pub default_number_decimal: i32,
    #[serde(default = "default_number_size")]
    pub default_number_size: i32,
    #[serde(default = "default_number_color")]
    pub default_number_color: String,
    #[serde(default = "default_number_opacity")]
    pub default_number_opacity: i32,
    #[serde(default = "default_image_quality")]
    pub image_quality: i32,
    #[serde(default = "default_max_image_width")]
    pub max_image_width: i32,
}

fn default_coordinate_type() -> String { "grid".to_string() }
fn default_color_mode() -> String { "grayscale".to_string() }
fn default_grid_density() -> f32 { 5.0 }
fn default_grid_opacity() -> i32 { 50 }
fn default_grid_color() -> String { "#ff0000".to_string() }
fn default_number_density() -> i32 { 2 }
fn default_number_decimal() -> i32 { 0 }
fn default_number_size() -> i32 { 12 }
fn default_number_color() -> String { "#ff0000".to_string() }
fn default_number_opacity() -> i32 { 100 }
fn default_image_quality() -> i32 { 85 }
fn default_max_image_width() -> i32 { 1920 }

impl Default for ScreenshotConfig {
    fn default() -> Self {
        ScreenshotConfig {
            default_coordinate_type: default_coordinate_type(),
            default_color_mode: default_color_mode(),
            default_grid_density: default_grid_density(),
            default_grid_opacity: default_grid_opacity(),
            default_grid_color: default_grid_color(),
            default_number_density: default_number_density(),
            default_number_decimal: default_number_decimal(),
            default_number_size: default_number_size(),
            default_number_color: default_number_color(),
            default_number_opacity: default_number_opacity(),
            image_quality: default_image_quality(),
            max_image_width: default_max_image_width(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct InputConfig {
    #[serde(default = "default_newline_mapping")]
    pub newline_mapping: std::collections::HashMap<String, String>,
}

fn default_newline_mapping() -> std::collections::HashMap<String, String> {
    let mut map = std::collections::HashMap::new();
    map.insert("pc".to_string(), "shift+enter".to_string());
    map.insert("mobile".to_string(), "enter".to_string());
    map
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SecurityConfig {
    #[serde(default)]
    pub blocked_processes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct LogConfig {
    #[serde(default = "default_retention_days")]
    pub retention_days: i32,
}

fn default_retention_days() -> i32 { 30 }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UIConfig {
    #[serde(default = "default_language")]
    pub language: String,
}

fn default_language() -> String { "zh_CN".to_string() }

impl Default for UIConfig {
    fn default() -> Self {
        UIConfig {
            language: default_language(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DelegatedConfig {
    #[serde(default)]
    pub active: bool,
    #[serde(default = "default_exit_hotkey")]
    pub exit_hotkey: String,
}

fn default_exit_hotkey() -> String { "ctrl+alt+z".to_string() }

impl Default for DelegatedConfig {
    fn default() -> Self {
        DelegatedConfig {
            active: false,
            exit_hotkey: default_exit_hotkey(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScrollScreenshotConfig {
    #[serde(default = "default_max_scrolls")]
    pub max_scrolls: i32,
    #[serde(default = "default_max_scroll_wait")]
    pub max_scroll_wait: f32,
    #[serde(default = "default_max_timeout")]
    pub max_timeout: i32,
    #[serde(default = "default_default_scroll_percent")]
    pub default_scroll_percent: f32,
    #[serde(default = "default_default_scroll_wait")]
    pub default_scroll_wait: f32,
    #[serde(default = "default_max_adjust_retries")]
    pub max_adjust_retries: i32,
    #[serde(default = "default_target_overlap_min")]
    pub target_overlap_min: f32,
    #[serde(default = "default_target_overlap_max")]
    pub target_overlap_max: f32,
    #[serde(default = "default_stop_threshold")]
    pub stop_threshold: f32,
    #[serde(default = "default_scroll_image_quality")]
    pub image_quality: i32,
}

fn default_max_scrolls() -> i32 { 5 }
fn default_max_scroll_wait() -> f32 { 30.0 }
fn default_max_timeout() -> i32 { 60 }
fn default_default_scroll_percent() -> f32 { 0.85 }
fn default_default_scroll_wait() -> f32 { 1.0 }
fn default_max_adjust_retries() -> i32 { 4 }
fn default_target_overlap_min() -> f32 { 0.35 }
fn default_target_overlap_max() -> f32 { 0.45 }
fn default_stop_threshold() -> f32 { 0.0001 }
fn default_scroll_image_quality() -> i32 { 95 }

impl Default for ScrollScreenshotConfig {
    fn default() -> Self {
        ScrollScreenshotConfig {
            max_scrolls: default_max_scrolls(),
            max_scroll_wait: default_max_scroll_wait(),
            max_timeout: default_max_timeout(),
            default_scroll_percent: default_default_scroll_percent(),
            default_scroll_wait: default_default_scroll_wait(),
            max_adjust_retries: default_max_adjust_retries(),
            target_overlap_min: default_target_overlap_min(),
            target_overlap_max: default_target_overlap_max(),
            stop_threshold: default_stop_threshold(),
            image_quality: default_scroll_image_quality(),
        }
    }
}

// HTTP客户端
mod http;
mod commands;
mod tray;

fn main() {
    // 注册控制台 Ctrl+C 处理器，确保退出时清理 Python 服务进程
    #[cfg(target_os = "windows")]
    {
        use windows_sys::Win32::System::Console::SetConsoleCtrlHandler;
        unsafe {
            SetConsoleCtrlHandler(Some(console_ctrl_handler), 1);
        }
    }

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_http::init())
        .manage(Arc::new(AppState {
            python_process: Mutex::new(None),
            is_service_running: AtomicBool::new(false),
            config: Mutex::new(Config::default()),
            hotkey_thread_id: AtomicU32::new(0),
        }))
        .setup(|app| {
            // 加载或创建配置
            let config = load_or_create_config();

            // 更新AppState中的配置
            let state = app.state::<Arc<AppState>>();
            tauri::async_runtime::block_on(async {
                let mut app_config = state.config.lock().await;
                *app_config = config.clone();
            });

            // 创建托盘菜单 - 根据语言设置和托管状态显示不同文本
            let language = config.ui.language.as_str();
            let delegated_active = config.delegated.active;
            let (show_text, quit_text, delegated_text) = match language {
                "zh_CN" => (
                    "显示窗口",
                    "退出",
                    if delegated_active { "退出托管" } else { "进入托管" }
                ),
                _ => (
                    "Show Window",
                    "Quit",
                    if delegated_active { "Exit Delegated" } else { "Enter Delegated" }
                ),
            };
            let show_item = MenuItem::with_id(app, "show", show_text, true, None::<&str>)?;
            let delegated_item = MenuItem::with_id(app, "delegated", delegated_text, true, None::<&str>)?;
            let quit_item = MenuItem::with_id(app, "quit", quit_text, true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_item, &delegated_item, &quit_item])?;

            // 选择图标
            let tray_icon = if delegated_active {
                tauri::image::Image::from_bytes(include_bytes!("../icons/icon-delegated.ico"))
                    .expect("Failed to load delegated icon")
            } else {
                // 使用默认图标，如果 default_window_icon 返回 None，则从文件加载
                app.default_window_icon()
                    .map(|i| i.to_owned())
                    .unwrap_or_else(|| {
                        tauri::image::Image::from_bytes(include_bytes!("../icons/icon.ico"))
                            .expect("Failed to load default icon")
                    })
            };

            // 设置托盘图标
            let menu_for_tray = menu.clone();
            let _tray = TrayIconBuilder::with_id("main-tray")
                .icon(tray_icon)
                .menu(&menu)
                .tooltip("ScreenClaw")
                .show_menu_on_left_click(false)
                .on_menu_event(move |app, event| {
                    match event.id.as_ref() {
                        "show" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_always_on_top(true);
                                let _ = window.set_focus();
                                let win = window.clone();
                                std::thread::spawn(move || {
                                    std::thread::sleep(std::time::Duration::from_millis(100));
                                    let _ = win.set_always_on_top(false);
                                });
                            }
                        }
                        "delegated" => {
                            // 调用 Python 托管 API 切换状态
                            let app_handle = app.clone();
                            let menu_clone = menu_for_tray.clone();
                            std::thread::spawn(move || {
                                // 从配置文件实时读取（Python 端可能已更新）
                                let config_path = get_config_path();
                                let (port, token, is_active) = read_delegated_state(&config_path);

                                let action = if is_active { "exit" } else { "enter" };
                                println!("[TRAY] Delegated action: {} (active={})", action, is_active);

                                match call_delegated_api(action, port, &token) {
                                    Ok(resp) => {
                                        println!("[TRAY] Delegated {} successful: {}", action, resp);
                                        let new_active = action == "enter";
                                        update_delegated_ui(&app_handle, &menu_clone, new_active);
                                    }
                                    Err(e) => println!("[TRAY] Failed to call delegated API: {}", e),
                                }
                            });
                        }
                        "quit" => {
                            // 退出前同步停止 Python 服务
                            println!("[TRAY] Quit menu clicked, stopping Python service...");
                            let pid = PYTHON_SERVICE_PID.load(std::sync::atomic::Ordering::SeqCst);
                            if pid != 0 {
                                #[cfg(target_os = "windows")]
                                {
                                    use std::os::windows::process::CommandExt;
                                    const CREATE_NO_WINDOW: u32 = 0x08000000;
                                    let _ = std::process::Command::new("taskkill")
                                        .args(["/F", "/T", "/PID", &pid.to_string()])
                                        .creation_flags(CREATE_NO_WINDOW)
                                        .status();
                                    PYTHON_SERVICE_PID.store(0, std::sync::atomic::Ordering::SeqCst);
                                }
                            }
                            println!("[TRAY] Service stopped, exiting...");
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click { button: MouseButton::Left, button_state: MouseButtonState::Up, .. } = event {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_always_on_top(true);
                            let _ = window.set_focus();
                            // 短暂延迟后取消置顶，避免窗口一直置顶
                            let win = window.clone();
                            std::thread::spawn(move || {
                                std::thread::sleep(std::time::Duration::from_millis(100));
                                let _ = win.set_always_on_top(false);
                            });
                        }
                    }
                })
                .build(app)?;

            // 后台启动Python服务（不阻塞窗口渲染）
            let state = app.state::<Arc<AppState>>();
            let state_clone = state.inner().clone();
            std::thread::spawn(move || {
                tauri::async_runtime::block_on(async {
                    commands::start_python_service(state_clone).await;
                });
            });

            // 启动全局快捷键监听（退出托管模式快捷键）
            let menu_clone = menu.clone();
            let state = app.state::<Arc<AppState>>();
            let state_clone = state.inner().clone();
            start_hotkey_listener(app.handle().clone(), menu_clone, state_clone, &config);

            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                // 关闭窗口时最小化到托盘
                window.hide().unwrap();
                api.prevent_close();
            }
        })
        .invoke_handler(tauri::generate_handler![
            commands::start_service,
            commands::stop_service,
            commands::get_service_status,
            commands::get_config,
            commands::update_config,
            commands::regenerate_token,
            commands::get_logs,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

/// 获取项目根目录
/// - 打包环境：返回 exe 所在目录（用户会随意放置 exe）
/// - 开发环境：向上3级找到项目根目录（exe 在 src-tauri/target/debug/）
pub fn get_project_root() -> std::path::PathBuf {
    let exe_path = std::env::current_exe()
        .expect("Failed to get current exe path");

    let exe_dir = exe_path
        .parent()
        .expect("Failed to get parent directory")
        .to_path_buf();

    // 检查 exe 同级目录是否有 data/config.json（打包环境）
    let data_in_exe_dir = exe_dir.join("data").join("config.json");
    if data_in_exe_dir.exists() {
        return exe_dir;
    }

    // 开发环境：向上3级
    // exe 在 src-tauri/target/debug/ 或 src-tauri/target/release/
    println!("[PATH] Returning dev root (development environment)");
    exe_dir.parent()
        .and_then(|p| p.parent())
        .and_then(|p| p.parent())
        .map(|p| p.to_path_buf())
        .unwrap_or(exe_dir)
}

/// 获取data目录路径
pub fn get_data_dir() -> std::path::PathBuf {
    get_project_root().join("data")
}

/// 获取config.json路径
pub fn get_config_path() -> std::path::PathBuf {
    get_data_dir().join("config.json")
}

fn generate_token() -> String {
    // 生成32字符的十六进制Token
    format!("{:016x}{:016x}",
        rand::random::<u64>(),
        rand::random::<u64>()
    )
}

fn get_local_ip() -> String {
    // 获取本机局域网IP
    use std::net::UdpSocket;
    match UdpSocket::bind("0.0.0.0:0") {
        Ok(socket) => {
            if socket.connect("8.8.8.8:80").is_ok() {
                if let Ok(addr) = socket.local_addr() {
                    return addr.ip().to_string();
                }
            }
        }
        Err(_) => {}
    }
    "127.0.0.1".to_string()
}

/// 调用 Python 托管 API
fn call_delegated_api(action: &str, port: u16, token: &str) -> Result<String, String> {
    let client = reqwest::blocking::Client::new();
    let url = format!("http://127.0.0.1:{}/api/delegated", port);
    let body = serde_json::json!({ "action": action });

    let response = client
        .post(&url)
        .header("Authorization", format!("Bearer {}", token))
        .header("Content-Type", "application/json")
        .body(body.to_string())
        .send()
        .map_err(|e| format!("HTTP request failed: {}", e))?;

    let status = response.status();
    let text = response.text()
        .map_err(|e| format!("Failed to read response: {}", e))?;

    if !status.is_success() {
        return Err(format!("HTTP {} - {}", status, text));
    }

    // 检查响应中的 success 字段
    if let Ok(json) = serde_json::from_str::<serde_json::Value>(&text) {
        if let Some(success) = json.get("success").and_then(|s| s.as_bool()) {
            if !success {
                let msg = json.get("message").and_then(|m| m.as_str()).unwrap_or("Unknown error");
                return Err(format!("API error: {}", msg));
            }
        }
    }

    Ok(text)
}

/// 更新托管模式的托盘图标和菜单文本
fn update_delegated_ui(app_handle: &tauri::AppHandle, menu: &Menu<tauri::Wry>, active: bool) {
    // 更新图标
    if let Some(tray) = app_handle.tray_by_id("main-tray") {
        let new_icon = if active {
            tauri::image::Image::from_bytes(include_bytes!("../icons/icon-delegated.ico"))
                .map(|img: tauri::image::Image| img.to_owned())
                .ok()
        } else {
            app_handle.default_window_icon().map(|img| img.to_owned())
        };
        if let Some(icon) = new_icon {
            let _ = tray.set_icon(Some(icon));
        }
    }

    // 更新菜单文本
    let state = app_handle.state::<Arc<AppState>>();
    let language = tauri::async_runtime::block_on(async {
        let cfg = state.config.lock().await;
        cfg.ui.language.clone()
    });
    let delegated_text = match language.as_str() {
        "zh_CN" => if active { "退出托管" } else { "进入托管" },
        _ => if active { "Exit Delegated" } else { "Enter Delegated" },
    };
    if let Some(item) = menu.get("delegated") {
        if let Some(menu_item) = item.as_menuitem() {
            let _ = menu_item.set_text(delegated_text);
        }
    }
}

/// WM_USER + 1，用于通知热键线程重新注册快捷键
const WM_REHOTKEY: u32 = 0x0401;
/// WM_USER + 2，Python 通知 Rust 托管状态变更
const WM_DELEGATED_SYNC: u32 = 0x0402;

/// 启动全局热键监听器（退出托管快捷键）
/// 使用 GetMessageW 阻塞等待，零 CPU 占用
/// 收到 WM_REHOTKEY 消息时重新注册快捷键
fn start_hotkey_listener(app_handle: tauri::AppHandle, menu: Menu<tauri::Wry>, state: Arc<AppState>, config: &Config) {
    let initial_hotkey = config.delegated.exit_hotkey.clone();
    let config_path = get_config_path();

    std::thread::spawn(move || {
        #[cfg(target_os = "windows")]
        {
            use std::ptr;
            use windows_sys::Win32::UI::Input::KeyboardAndMouse::*;
            use windows_sys::Win32::UI::WindowsAndMessaging::*;
            use windows_sys::Win32::System::Threading::GetCurrentThreadId;

            let mut current_hotkey = initial_hotkey;
            let (mut modifiers, mut vk) = parse_hotkey(&current_hotkey);

            unsafe {
                if RegisterHotKey(ptr::null_mut(), 1, modifiers, vk) == 0 {
                    println!("[HOTKEY] Failed to register hotkey: {}", current_hotkey);
                    return;
                }
                println!("[HOTKEY] Registered exit delegated hotkey: {}", current_hotkey);
            }

            // 记录线程 ID，供外部通知重注册
            let tid = unsafe { GetCurrentThreadId() };
            state.hotkey_thread_id.store(tid, std::sync::atomic::Ordering::SeqCst);
            println!("[HOTKEY] Listener thread ID: {}", tid);

            // 写入线程 ID 到文件，供 Python 侧 PostThreadMessageW 使用
            let tid_path = get_data_dir().join(".hotkey_tid");
            let _ = std::fs::write(&tid_path, tid.to_string());

            let mut msg: MSG = unsafe { std::mem::zeroed() };
            loop {
                let ret = unsafe { GetMessageW(&mut msg, ptr::null_mut(), 0, 0) };
                if ret == 0 {
                    break; // WM_QUIT
                }

                if msg.message == WM_HOTKEY {
                    // 快捷键触发 → 退出托管
                    println!("[HOTKEY] Exit delegated hotkey triggered");
                    let (port, token) = read_server_config(&config_path);
                    println!("[HOTKEY] Using port={}, token_len={}", port, token.len());
                    match call_delegated_api("exit", port, &token) {
                        Ok(resp) => {
                            println!("[HOTKEY] API response: {}", resp);
                            update_delegated_ui(&app_handle, &menu, false);
                        }
                        Err(e) => println!("[HOTKEY] Failed to exit delegated: {}", e),
                    }
                } else if msg.message == WM_REHOTKEY {
                    // 配置变更 → 重新注册快捷键
                    println!("[HOTKEY] Re-register signal received");
                    unsafe { UnregisterHotKey(ptr::null_mut(), 1); }

                    // 从配置文件读取最新快捷键
                    if let Some(new_hotkey) = std::fs::read_to_string(&config_path)
                        .ok()
                        .and_then(|content| {
                            serde_json::from_str::<serde_json::Value>(&content).ok()
                        })
                        .and_then(|json| {
                            json.get("delegated")
                                .and_then(|c| c.get("exit_hotkey"))
                                .and_then(|h| h.as_str())
                                .map(|s| s.to_string())
                        })
                    {
                        current_hotkey = new_hotkey;
                        let (new_mod, new_vk) = parse_hotkey(&current_hotkey);
                        modifiers = new_mod;
                        vk = new_vk;
                    }

                    unsafe {
                        if RegisterHotKey(ptr::null_mut(), 1, modifiers, vk) == 0 {
                            println!("[HOTKEY] Failed to re-register hotkey: {}", current_hotkey);
                            return;
                        }
                    }
                    println!("[HOTKEY] Re-registered hotkey: {}", current_hotkey);
                } else if msg.message == WM_DELEGATED_SYNC {
                    // Python 通知：托管状态变更 → 读 config → 更新托盘图标
                    println!("[HOTKEY] Delegated sync signal received");
                    let (_, _, is_active) = read_delegated_state(&config_path);
                    println!("[HOTKEY] Delegated state from config: active={}", is_active);
                    update_delegated_ui(&app_handle, &menu, is_active);
                }
            }

            unsafe { UnregisterHotKey(ptr::null_mut(), 1); }
        }

        #[cfg(not(target_os = "windows"))]
        {
            println!("[HOTKEY] Global hotkey not supported on this platform");
            let _ = (app_handle, menu, config_path); // suppress unused warnings
        }
    });
}

/// 从配置文件读取 server.port 和 server.token
fn read_server_config(config_path: &std::path::Path) -> (u16, String) {
    match std::fs::read_to_string(config_path) {
        Ok(content) => {
            match serde_json::from_str::<serde_json::Value>(&content) {
                Ok(json) => {
                    let server = json.get("server");
                    let port = server
                        .and_then(|s| s.get("port"))
                        .and_then(|p| p.as_u64())
                        .unwrap_or(12261) as u16;
                    let token = server
                        .and_then(|s| s.get("token"))
                        .and_then(|t| t.as_str())
                        .unwrap_or("")
                        .to_string();
                    (port, token)
                }
                Err(_) => (12261, String::new())
            }
        }
        Err(_) => (12261, String::new())
    }
}

/// 从配置文件读取 server.port、server.token 和 delegated.active
fn read_delegated_state(config_path: &std::path::Path) -> (u16, String, bool) {
    match std::fs::read_to_string(config_path) {
        Ok(content) => {
            match serde_json::from_str::<serde_json::Value>(&content) {
                Ok(json) => {
                    let server = json.get("server");
                    let port = server
                        .and_then(|s| s.get("port"))
                        .and_then(|p| p.as_u64())
                        .unwrap_or(12261) as u16;
                    let token = server
                        .and_then(|s| s.get("token"))
                        .and_then(|t| t.as_str())
                        .unwrap_or("")
                        .to_string();
                    let active = json.get("delegated")
                        .and_then(|c| c.get("active"))
                        .and_then(|a| a.as_bool())
                        .unwrap_or(false);
                    (port, token, active)
                }
                Err(_) => (12261, String::new(), false)
            }
        }
        Err(_) => (12261, String::new(), false)
    }
}

/// 解析快捷键字符串为 Win32 modifiers + VK code
#[cfg(target_os = "windows")]
fn parse_hotkey(hotkey: &str) -> (u32, u32) {
    use windows_sys::Win32::UI::Input::KeyboardAndMouse::*;

    let mut modifiers = 0u32;
    let mut vk = 0x41u32; // 'Z'

    for part in hotkey.to_lowercase().split('+') {
        let part = part.trim();
        match part {
            "ctrl" | "control" => modifiers |= MOD_CONTROL,
            "alt" => modifiers |= MOD_ALT,
            "shift" => modifiers |= MOD_SHIFT,
            "win" | "windows" => modifiers |= MOD_WIN,
            // Single character key
            c if c.len() == 1 => {
                if let Some(ch) = c.chars().next() {
                    vk = ch.to_uppercase().next().unwrap_or('Z') as u32;
                }
            }
            // Function keys
            f if f.starts_with('f') && f.len() <= 3 => {
                if let Ok(n) = f[1..].parse::<u32>() {
                    vk = (VK_F1 as u32) + n - 1;
                }
            }
            // Named keys
            "escape" | "esc" => vk = VK_ESCAPE as u32,
            "space" => vk = VK_SPACE as u32,
            "tab" => vk = VK_TAB as u32,
            "enter" | "return" => vk = VK_RETURN as u32,
            _ => {}
        }
    }

    (modifiers, vk)
}

fn load_or_create_config() -> Config {
    let config_path = get_config_path();

    let mut config = if config_path.exists() {
        match std::fs::read_to_string(&config_path) {
            Ok(content) => {
                match serde_json::from_str::<Config>(&content) {
                    Ok(config) => config,
                    Err(e) => {
                        println!("Failed to parse config: {}", e);
                        let mut c = Config::default();
                        c.server.token = generate_token();
                        c.server.local_ip = get_local_ip();
                        c
                    }
                }
            }
            Err(e) => {
                println!("Failed to read config: {}", e);
                let mut c = Config::default();
                c.server.token = generate_token();
                c.server.local_ip = get_local_ip();
                c
            }
        }
    } else {
        let mut c = Config::default();
        c.server.token = generate_token();
        c.server.local_ip = get_local_ip();
        c
    };

    // 启动时重置托管状态
    config.delegated.active = false;

    // 保存配置（含重置后的状态）
    if let Some(parent) = config_path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    match serde_json::to_string_pretty(&config) {
        Ok(json) => {
            if let Err(e) = std::fs::write(&config_path, json) {
                println!("Failed to save config: {}", e);
            } else {
                println!("Config loaded and delegated reset at {:?}", config_path);
            }
        }
        Err(e) => println!("Failed to serialize config: {}", e),
    }

    config
}

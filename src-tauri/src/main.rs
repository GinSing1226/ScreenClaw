//! ScreenClaw - AI应用的可视化操作必备伴侣

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::atomic::AtomicBool;
use std::sync::Arc;
use std::process::Child;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, WindowEvent
};
use serde::{Deserialize, Serialize};
use tokio::sync::Mutex;

// 全局状态
pub struct AppState {
    pub python_process: Mutex<Option<Child>>,
    pub is_service_running: AtomicBool,
    pub config: Mutex<Config>,
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
fn default_grid_density() -> f32 { 5.0 }
fn default_grid_opacity() -> i32 { 50 }
fn default_grid_color() -> String { "#00FF00".to_string() }
fn default_number_density() -> i32 { 2 }
fn default_number_decimal() -> i32 { 0 }
fn default_number_size() -> i32 { 8 }
fn default_number_color() -> String { "#00FF00".to_string() }
fn default_number_opacity() -> i32 { 100 }
fn default_image_quality() -> i32 { 85 }
fn default_max_image_width() -> i32 { 1920 }

impl Default for ScreenshotConfig {
    fn default() -> Self {
        ScreenshotConfig {
            default_coordinate_type: default_coordinate_type(),
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

// HTTP客户端
mod http;
mod commands;
mod tray;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_http::init())
        .manage(Arc::new(AppState {
            python_process: Mutex::new(None),
            is_service_running: AtomicBool::new(false),
            config: Mutex::new(Config::default()),
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

            // 创建托盘菜单 - 根据语言设置显示不同文本
            let language = config.ui.language.as_str();
            let (show_text, quit_text) = match language {
                "zh_CN" => ("显示窗口", "退出"),
                "en_US" => ("Show Window", "Quit"),
                _ => ("Show Window", "Quit"),
            };
            let show_item = MenuItem::with_id(app, "show", show_text, true, None::<&str>)?;
            let quit_item = MenuItem::with_id(app, "quit", quit_text, true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show_item, &quit_item])?;

            // 设置托盘图标
            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, event| {
                    match event.id.as_ref() {
                        "show" => {
                            if let Some(window) = app.get_webview_window("main") {
                                window.show().unwrap();
                                window.set_focus().unwrap();
                            }
                        }
                        "quit" => {
                            // 退出前先停止 Python 服务
                            println!("[TRAY] Quit menu clicked, stopping Python service...");
                            let state = app.state::<Arc<AppState>>();
                            // spawn 任务来异步停止服务
                            let state_clone = state.inner().clone();
                            std::thread::spawn(move || {
                                tauri::async_runtime::block_on(async {
                                    commands::stop_python_service(state_clone).await;
                                });
                            });
                            println!("[TRAY] Exit command sent...");
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click { button: MouseButton::Left, button_state: MouseButtonState::Up, .. } = event {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            window.show().unwrap();
                            window.set_focus().unwrap();
                        }
                    }
                })
                .build(app)?;

            // 启动Python服务
            let state = app.state::<Arc<AppState>>();
            tauri::async_runtime::block_on(async {
                commands::start_python_service(state.inner().clone()).await;
            });

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
            commands::confirm_operation,
            commands::regenerate_token,
            commands::get_logs,
            commands::open_devtools,
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

fn load_or_create_config() -> Config {
    let config_path = get_config_path();

    if config_path.exists() {
        match std::fs::read_to_string(&config_path) {
            Ok(content) => {
                match serde_json::from_str(&content) {
                    Ok(config) => return config,
                    Err(e) => println!("Failed to parse config: {}", e),
                }
            }
            Err(e) => println!("Failed to read config: {}", e),
        }
    }

    // 创建默认配置
    let mut config = Config::default();
    config.server.token = generate_token();
    config.server.local_ip = get_local_ip();

    // 保存配置
    if let Some(parent) = config_path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    match serde_json::to_string_pretty(&config) {
        Ok(json) => {
            if let Err(e) = std::fs::write(&config_path, json) {
                println!("Failed to save config: {}", e);
            } else {
                println!("Created default config at {:?}", config_path);
            }
        }
        Err(e) => println!("Failed to serialize config: {}", e),
    }

    config
}

//! ScreenClaw - AI应用的可视化操作必备伴侣

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::process::{Command, Child};
use std::time::Duration;
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager, Runtime, State, WindowEvent
};
use serde::{Deserialize, Serialize};
use tokio::sync::Mutex;

// 全局状态
pub struct AppState {
    pub python_process: Mutex<Option<Child>>,
    pub is_service_running: AtomicBool,
    pub config: Mutex<Config>,
}

// 配置结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub server: ServerConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub port: u16,
    pub token: String,
    pub local_ip: String,
}

impl Default for Config {
    fn default() -> Self {
        Config {
            server: ServerConfig {
                port: 12261,
                token: String::new(),
                local_ip: String::from("127.0.0.1"),
            },
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
            // 加载配置
            let config = load_config().unwrap_or_default();

            // 设置托盘图标
            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&app.handle())
                .menu_on_left_click(false)
                .on_menu_event(|app, event| {
                    match event.id.as_ref() {
                        "show" => {
                            if let Some(window) = app.get_webview_window("main") {
                                window.show().unwrap();
                                window.set_focus().unwrap();
                            }
                        }
                        "quit" => {
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
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn load_config() -> Option<Config> {
    let config_path = std::env::current_exe().ok()?
        .parent()?
        .join("config.json");

    if config_path.exists() {
        let content = std::fs::read_to_string(config_path).ok()?;
        serde_json::from_str(&content).ok()
    } else {
        None
    }
}

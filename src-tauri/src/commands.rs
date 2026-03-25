//! Tauri命令

use std::sync::Arc;
use std::process::{Command, Child};
use tauri::State;
use serde::{Deserialize, Serialize};

use crate::AppState;
use crate::Config;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceStatus {
    pub is_running: bool,
    pub port: u16,
    pub local_ip: String,
    pub token: String,
}

/// 启动Python服务
#[tauri::command]
pub async fn start_service(
    state: State<'_, Arc<AppState>>,
) -> Result<(), String> {
    start_python_service(state.inner().clone()).await;
    Ok(())
}

/// 停止Python服务
#[tauri::command]
pub async fn stop_service(
    state: State<'_, Arc<AppState>>,
) -> Result<(), String> {
    stop_python_service(state.inner().clone()).await;
    Ok(())
}

/// 获取服务状态
#[tauri::command]
pub async fn get_service_status(
    state: State<'_, Arc<AppState>>,
) -> Result<ServiceStatus, String> {
    let is_running = state.is_service_running.load(std::sync::atomic::Ordering::SeqCst);
    let config = state.config.lock().await;

    Ok(ServiceStatus {
        is_running,
        port: config.server.port,
        local_ip: config.server.local_ip.clone(),
        token: config.server.token.clone(),
    })
}

/// 获取配置
#[tauri::command]
pub async fn get_config(
    state: State<'_, Arc<AppState>>,
) -> Result<Config, String> {
    let config = state.config.lock().await;
    Ok(config.clone())
}

/// 更新配置
#[tauri::command]
pub async fn update_config(
    state: State<'_, Arc<AppState>>,
    new_config: Config,
) -> Result<(), String> {
    let mut config = state.config.lock().await;
    *config = new_config;
    Ok(())
}

/// 确认操作（用于SendInput前弹窗确认）
#[tauri::command]
pub async fn confirm_operation(
    process_name: String,
    ai_app_type: String,
) -> Result<bool, String> {
    // 这个函数会被前端调用，显示确认对话框
    // 返回用户的选择
    // 这里返回true，实际实现需要与前端交互
    Ok(true)
}

/// 启动Python服务的内部函数
pub async fn start_python_service(state: Arc<AppState>) {
    // 检查是否已经在运行
    if state.is_service_running.load(std::sync::atomic::Ordering::SeqCst) {
        println!("Python service is already running");
        return;
    }

    // 获取可执行文件目录
    let exe_dir = std::env::current_exe()
        .expect("Failed to get current exe path")
        .parent()
        .expect("Failed to get parent directory")
        .to_path_buf();

    let python_exe = exe_dir.join("python-service.exe");

    // 检查文件是否存在
    if !python_exe.exists() {
        println!("Python service not found: {:?}", python_exe);
        return;
    }

    // 启动进程
    match Command::new(&python_exe)
        .current_dir(&exe_dir)
        .spawn()
    {
        Ok(child) => {
            let mut process = state.python_process.lock().await;
            *process = Some(child);
            state.is_service_running.store(true, std::sync::atomic::Ordering::SeqCst);
            println!("Python service started");
        }
        Err(e) => {
            println!("Failed to start Python service: {}", e);
        }
    }
}

/// 停止Python服务的内部函数
pub async fn stop_python_service(state: Arc<AppState>) {
    let mut process = state.python_process.lock().await;

    if let Some(mut child) = process.take() {
        match child.kill() {
            Ok(_) => {
                println!("Python service stopped");
            }
            Err(e) => {
                println!("Failed to stop Python service: {}", e);
            }
        }
    }

    state.is_service_running.store(false, std::sync::atomic::Ordering::SeqCst);
}

//! Tauri命令

use std::sync::Arc;
use std::process::Command;
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

/// 获取项目根目录
fn get_project_root() -> std::path::PathBuf {
    let exe_dir = std::env::current_exe()
        .expect("Failed to get current exe path")
        .parent()
        .expect("Failed to get parent directory")
        .to_path_buf();

    // 开发模式：exe在 src-tauri/target/debug/
    // exe_dir = src-tauri/target/debug/
    // parent() = src-tauri/target/
    // parent() = src-tauri/
    // parent() = 项目根目录
    exe_dir.parent()
        .and_then(|p| p.parent())
        .and_then(|p| p.parent())
        .map(|p| p.to_path_buf())
        .unwrap_or(exe_dir)
}

/// 获取data目录路径
fn get_data_dir() -> std::path::PathBuf {
    get_project_root().join("data")
}

/// 获取config.json路径
fn get_config_path() -> std::path::PathBuf {
    get_data_dir().join("config.json")
}

/// 获取服务状态
#[tauri::command]
pub async fn get_service_status(
    state: State<'_, Arc<AppState>>,
) -> Result<ServiceStatus, String> {
    let is_running = state.is_service_running.load(std::sync::atomic::Ordering::SeqCst);

    // 重新读取配置文件以获取最新信息（Python可能更新了local_ip）
    let config_path = get_config_path();

    let (port, local_ip, token) = if config_path.exists() {
        match std::fs::read_to_string(&config_path) {
            Ok(content) => {
                match serde_json::from_str::<serde_json::Value>(&content) {
                    Ok(json) => {
                        let server = json.get("server");
                        (
                            server.and_then(|s| s.get("port")).and_then(|p| p.as_u64()).unwrap_or(12261) as u16,
                            server.and_then(|s| s.get("local_ip")).and_then(|p| p.as_str()).unwrap_or("127.0.0.1").to_string(),
                            server.and_then(|s| s.get("token")).and_then(|p| p.as_str()).unwrap_or("").to_string(),
                        )
                    }
                    Err(_) => {
                        let config = state.config.lock().await;
                        (config.server.port, config.server.local_ip.clone(), config.server.token.clone())
                    }
                }
            }
            Err(_) => {
                let config = state.config.lock().await;
                (config.server.port, config.server.local_ip.clone(), config.server.token.clone())
            }
        }
    } else {
        let config = state.config.lock().await;
        (config.server.port, config.server.local_ip.clone(), config.server.token.clone())
    };

    Ok(ServiceStatus {
        is_running,
        port,
        local_ip,
        token,
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
    let config_path = get_config_path();

    // 确保data目录存在
    if let Some(parent) = config_path.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|e| format!("Failed to create data directory: {}", e))?;
    }

    // 保存到文件
    let config_content = serde_json::to_string_pretty(&new_config)
        .map_err(|e| format!("Failed to serialize config: {}", e))?;

    std::fs::write(&config_path, config_content)
        .map_err(|e| format!("Failed to write config: {}", e))?;

    // 更新内存中的配置
    let mut config = state.config.lock().await;
    *config = new_config;

    Ok(())
}

/// 重新生成Token
#[tauri::command]
pub async fn regenerate_token(
    state: State<'_, Arc<AppState>>,
) -> Result<String, String> {
    let config_path = get_config_path();

    // 确保data目录存在
    if let Some(parent) = config_path.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|e| format!("Failed to create data directory: {}", e))?;
    }

    // 如果配置文件不存在，创建默认配置
    if !config_path.exists() {
        // 创建默认配置
        let default_config = crate::Config::default();
        let default_content = serde_json::to_string_pretty(&default_config)
            .map_err(|e| format!("Failed to serialize default config: {}", e))?;
        std::fs::write(&config_path, default_content)
            .map_err(|e| format!("Failed to write default config: {}", e))?;
    }

    // 读取当前配置
    let config_content = std::fs::read_to_string(&config_path)
        .map_err(|e| format!("Failed to read config: {}", e))?;

    let mut config_json: serde_json::Value = serde_json::from_str(&config_content)
        .map_err(|e| format!("Failed to parse config: {}", e))?;

    // 生成新Token (32字符十六进制)
    let new_token = format!("{:016x}{:016x}",
        rand::random::<u64>(),
        rand::random::<u64>()
    );

    // 更新配置中的Token
    if let Some(server) = config_json.get_mut("server") {
        if let Some(obj) = server.as_object_mut() {
            obj.insert("token".to_string(), serde_json::json!(new_token));
        }
    }

    // 保存配置
    let updated_content = serde_json::to_string_pretty(&config_json)
        .map_err(|e| format!("Failed to serialize config: {}", e))?;

    std::fs::write(&config_path, updated_content)
        .map_err(|e| format!("Failed to write config: {}", e))?;

    // 更新内存中的配置
    let mut config = state.config.lock().await;
    config.server.token = new_token.clone();

    Ok(new_token)
}

/// 确认操作（用于SendInput前弹窗确认）
#[tauri::command]
pub async fn confirm_operation(
    _process_name: String,
    _ai_app_type: String,
) -> Result<bool, String> {
    // 这个函数会被前端调用，显示确认对话框
    // 返回用户的选择
    // 这里返回true，实际实现需要与前端交互
    Ok(true)
}

/// 日志项结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogItem {
    pub timestamp: String,
    pub source: String,          // 日志来源（文件名前缀，如 openclaw-test）
    pub client_ip: String,       // 客户端IP地址
    pub process_id: i32,
    pub process_name: String,    // 被操作的应用名
    pub session_id: String,      // 会话ID
    pub instruction: String,
    pub params: serde_json::Value,  // 请求参数
    pub result: serde_json::Value,
}

/// 从日志文件名提取信息（如 openclaw-test-2026-03-26.jsonl）
/// 返回 (source, session_id)
/// - source: openclaw（AI应用名）
/// - session_id: test（会话ID）
fn extract_info_from_filename(filename: &str) -> (String, String) {
    // 移除 .jsonl 扩展名
    let name = filename.strip_suffix(".jsonl").unwrap_or(filename);

    // 分割文件名：openclaw-test-2026-03-26
    let parts: Vec<&str> = name.split('-').collect();

    if parts.len() >= 5 {
        // 格式：{source}-{session_id}-{YYYY}-{MM}-{DD}
        // 检查最后3个部分是否是日期
        let date_start = parts.len() - 3;
        if parts[date_start].len() == 4 && parts[date_start].chars().all(|c| c.is_numeric()) {
            // 找到日期部分
            let source = parts[0].to_string();
            let session_id = parts[1..date_start].join("-");
            return (source, session_id);
        }
    }

    // 默认情况：返回整个名称作为 source，空字符串作为 session_id
    (name.to_string(), String::new())
}

/// 获取日志
#[tauri::command]
pub async fn get_logs() -> Result<Vec<LogItem>, String> {
    // 获取项目根目录下的logs目录
    let logs_dir = get_project_root().join("logs");

    if !logs_dir.exists() {
        return Ok(Vec::new());
    }

    let mut logs = Vec::new();

    // 读取所有.jsonl文件
    if let Ok(entries) = std::fs::read_dir(&logs_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.extension().map(|e| e == "jsonl").unwrap_or(false) {
                // 从文件名提取 source 和 session_id
                let filename = path.file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("");
                let (source, session_id) = extract_info_from_filename(filename);

                if let Ok(content) = std::fs::read_to_string(&path) {
                    for line in content.lines() {
                        if line.trim().is_empty() {
                            continue;
                        }
                        if let Ok(json) = serde_json::from_str::<serde_json::Value>(line) {
                            // 转换为LogItem格式
                            let log = LogItem {
                                timestamp: json.get("timestamp")
                                    .and_then(|v| v.as_str())
                                    .unwrap_or("")
                                    .to_string(),
                                source: source.clone(),
                                client_ip: json.get("client_ip")
                                    .and_then(|v| v.as_str())
                                    .unwrap_or("unknown")
                                    .to_string(),
                                process_id: json.get("process_id")
                                    .and_then(|v| v.as_i64())
                                    .unwrap_or(0) as i32,
                                process_name: json.get("process_name")
                                    .and_then(|v| v.as_str())
                                    .unwrap_or("")
                                    .to_string(),
                                session_id: session_id.clone(),
                                instruction: json.get("instruction")
                                    .and_then(|v| v.as_str())
                                    .unwrap_or("")
                                    .to_string(),
                                params: json.get("params")
                                    .cloned()
                                    .unwrap_or(serde_json::json!({})),
                                result: json.get("result")
                                    .cloned()
                                    .unwrap_or(serde_json::json!({"success": false})),
                            };
                            logs.push(log);
                        }
                    }
                }
            }
        }
    }

    // 按时间倒序排列，最多返回100条
    logs.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
    logs.truncate(100);

    Ok(logs)
}

/// 启动Python服务的内部函数
pub async fn start_python_service(state: Arc<AppState>) {
    // 检查是否已经在运行
    if state.is_service_running.load(std::sync::atomic::Ordering::SeqCst) {
        println!("Python service is already running");
        return;
    }

    let project_root = get_project_root();
    let python_dir = project_root.join("python");
    let python_exe = python_dir.join("python-service.exe");

    // 判断是开发模式还是生产模式
    let result = if python_exe.exists() {
        // 生产模式：使用打包的exe
        println!("Starting Python service (production mode)...");
        Command::new(&python_exe)
            .current_dir(&python_dir)
            .spawn()
    } else {
        // 开发模式：使用python解释器
        println!("Starting Python service (development mode)...");
        let main_py = python_dir.join("main.py");
        if !main_py.exists() {
            println!("Python main.py not found: {:?}", main_py);
            return;
        }
        Command::new("python")
            .arg(&main_py)
            .current_dir(&python_dir)
            .spawn()
    };

    match result {
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

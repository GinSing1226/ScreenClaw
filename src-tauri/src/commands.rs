//! Tauri命令

use std::sync::Arc;
use std::process::Command;
use tauri::State;
use serde::{Deserialize, Serialize};

use crate::AppState;
use crate::Config;
use crate::{get_project_root, get_config_path};

/// 打开开发者工具（提示用户使用 F12）
#[tauri::command]
pub async fn open_devtools() -> Result<(), String> {
    // Tauri v2: devtools 已启用，用户可以直接按 F12 打开
    Err("Please press F12 to open developer tools".to_string())
}

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

/// 从日志文件名提取信息（如 openclaw__test__2026-03-26.jsonl）
/// 返回 (source, session_id)
/// - source: openclaw（AI应用名）
/// - session_id: test（会话ID）
fn extract_info_from_filename(filename: &str) -> (String, String) {
    // 移除 .jsonl 扩展名
    let name = filename.strip_suffix(".jsonl").unwrap_or(filename);

    // 按双下划线分割：{app}__{session}__{date}
    let parts: Vec<&str> = name.split("__").collect();

    if parts.len() >= 3 {
        let source = parts[0].to_string();
        let session_id = parts[1].to_string();
        return (source, session_id);
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
    println!("[START] Attempting to start Python service...");

    // 检查是否已经在运行
    if state.is_service_running.load(std::sync::atomic::Ordering::SeqCst) {
        println!("[START] Python service is already running, skipping...");
        return;
    }

    // 立即标记为正在运行，防止重复启动
    state.is_service_running.store(true, std::sync::atomic::Ordering::SeqCst);

    let project_root = get_project_root();

    // 优先在 exe 同级目录查找 python-service.exe（打包环境）
    let python_exe = project_root.join("python-service.exe");

    // 判断是开发模式还是生产模式
    let result = if python_exe.exists() {
        // 生产模式：使用打包的 exe
        println!("Starting Python service (production mode): {:?}", python_exe);
        #[cfg(target_os = "windows")]
        {
            use std::os::windows::process::CommandExt;
            // 使用 CREATE_NEW_PROCESS_GROUP，然后用 taskkill /T 杀进程树
            const CREATE_NEW_PROCESS_GROUP: u32 = 0x00000200;
            Command::new(&python_exe)
                .current_dir(&project_root)
                .creation_flags(CREATE_NEW_PROCESS_GROUP)
                .spawn()
        }
        #[cfg(not(target_os = "windows"))]
        {
            Command::new(&python_exe)
                .current_dir(&project_root)
                .spawn()
        }
    } else {
        // 开发模式：使用 python 解释器
        let python_dir = project_root.join("python");
        let main_py = python_dir.join("main.py");
        println!("Starting Python service (development mode): {:?}", main_py);
        if !main_py.exists() {
            println!("Python main.py not found: {:?}", main_py);
            return;
        }
        #[cfg(target_os = "windows")]
        {
            Command::new("python")
                .arg(&main_py)
                .current_dir(&python_dir)
                .spawn()
        }
        #[cfg(not(target_os = "windows"))]
        {
            Command::new("python")
                .arg(&main_py)
                .current_dir(&python_dir)
                .spawn()
        }
    };

    match result {
        Ok(child) => {
            let pid = child.id();
            let mut process = state.python_process.lock().await;
            *process = Some(child);
            println!("[START] Python service started successfully, PID: {}", pid);
        }
        Err(e) => {
            println!("[START] Failed to start Python service: {}", e);
            // 重置运行状态
            state.is_service_running.store(false, std::sync::atomic::Ordering::SeqCst);
        }
    }
}

/// 停止Python服务的内部函数
pub async fn stop_python_service(state: Arc<AppState>) {
    println!("[STOP] Attempting to stop Python service...");

    let mut process = state.python_process.lock().await;

    if let Some(mut child) = process.take() {
        let pid = child.id();
        println!("[STOP] Found Python process with PID: {}", pid);

        // Windows: 直接使用 taskkill /F /T 杀死整个进程树
        // 这样可以确保 PyInstaller 的子进程也被清理
        #[cfg(target_os = "windows")]
        {
            use std::os::windows::process::CommandExt;
            const CREATE_NO_WINDOW: u32 = 0x08000000;
            println!("[STOP] Using taskkill to terminate process tree...");
            let result = std::process::Command::new("taskkill")
                .args(["/F", "/T", "/PID", &pid.to_string()])
                .creation_flags(CREATE_NO_WINDOW)
                .output();
            match result {
                Ok(output) => {
                    println!("[STOP] taskkill output: {}", String::from_utf8_lossy(&output.stdout));
                }
                Err(e) => {
                    println!("[STOP] taskkill failed: {}, falling back to kill", e);
                    let _ = child.kill();
                }
            }
        }

        #[cfg(not(target_os = "windows"))]
        {
            let _ = child.kill();
        }

        // 等待进程退出
        let _ = child.wait();
        println!("[STOP] Python process {} terminated", pid);
    } else {
        println!("[STOP] No Python process found to stop");
    }

    state.is_service_running.store(false, std::sync::atomic::Ordering::SeqCst);
    println!("[STOP] Python service stop completed");
}

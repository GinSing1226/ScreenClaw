//! HTTP客户端模块（预留）
//! 当前托管模式使用 blocking 同步调用（见 main.rs call_delegated_api）
//! 此异步版本预留给未来高频 Rust→Python 通信场景

#![allow(dead_code)]

use serde::{Deserialize, Serialize};

/// API响应结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error_code: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<T>,
}

/// 进程信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessInfo {
    pub process_id: i32,
    pub process_name: String,
    pub window_title: String,
}

/// 截图响应数据
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScreenshotData {
    pub image_path: String,
    pub image_base64: String,
}

/// 健康检查数据
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthData {
    pub version: String,
    pub uptime_seconds: i64,
}

/// HTTP客户端
pub struct HttpClient {
    base_url: String,
    token: String,
    client: reqwest::Client,
}

impl HttpClient {
    pub fn new(port: u16, token: String) -> Self {
        Self {
            base_url: format!("http://127.0.0.1:{}", port),
            token,
            client: reqwest::Client::new(),
        }
    }

    /// 发送GET请求
    pub async fn get<T: for<'de> Deserialize<'de>>(
        &self,
        path: &str,
    ) -> Result<ApiResponse<T>, String> {
        let url = format!("{}{}", self.base_url, path);

        let response = self.client
            .get(&url)
            .header("Authorization", format!("Bearer {}", self.token))
            .send()
            .await
            .map_err(|e| e.to_string())?;

        let status = response.status();
        let body = response.text().await.map_err(|e| e.to_string())?;

        if status.is_success() {
            serde_json::from_str(&body).map_err(|e| e.to_string())
        } else {
            Err(format!("HTTP {}: {}", status, body))
        }
    }

    /// 发送POST请求
    pub async fn post<T: for<'de> Deserialize<'de>, B: Serialize>(
        &self,
        path: &str,
        body: &B,
    ) -> Result<ApiResponse<T>, String> {
        let url = format!("{}{}", self.base_url, path);

        let response = self.client
            .post(&url)
            .header("Authorization", format!("Bearer {}", self.token))
            .json(body)
            .send()
            .await
            .map_err(|e| e.to_string())?;

        let status = response.status();
        let response_body = response.text().await.map_err(|e| e.to_string())?;

        if status.is_success() {
            serde_json::from_str(&response_body).map_err(|e| e.to_string())
        } else {
            Err(format!("HTTP {}: {}", status, response_body))
        }
    }

    /// 健康检查
    pub async fn health_check(&self) -> Result<bool, String> {
        let result: ApiResponse<HealthData> = self.get("/api/health").await?;
        Ok(result.success)
    }

    /// 获取进程列表
    pub async fn get_process_list(
        &self,
        ai_app_type: &str,
        session_id: &str,
        keyword: Option<&str>,
    ) -> Result<Vec<ProcessInfo>, String> {
        #[derive(Serialize)]
        struct Request {
            ai_app_type: String,
            session_id: String,
            keyword: String,
        }

        let body = Request {
            ai_app_type: ai_app_type.to_string(),
            session_id: session_id.to_string(),
            keyword: keyword.unwrap_or("").to_string(),
        };

        #[derive(Deserialize)]
        struct ProcessListData {
            processes: Vec<ProcessInfo>,
        }

        let result: ApiResponse<ProcessListData> = self.post("/api/get_process_list", &body).await?;

        if result.success {
            Ok(result.data.map(|d| d.processes).unwrap_or_default())
        } else {
            Err(result.message)
        }
    }
}

use serde::{Deserialize, Serialize};
use tauri::State;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;

#[derive(Debug, Serialize, Deserialize)]
pub struct LogEntry {
    pub id: String,
    pub timestamp: String,
    pub level: String,
    pub category: String,
    pub message: String,
    pub details: Option<HashMap<String, serde_json::Value>>,
    pub source: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LogFilter {
    pub level: Option<String>,
    pub category: Option<String>,
    pub start_time: Option<String>,
    pub end_time: Option<String>,
    pub limit: Option<usize>,
    pub offset: Option<usize>,
    pub search: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BandwidthLimits {
    pub upload_kbps: u32,
    pub download_kbps: u32,
    pub enabled: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Statistics {
    pub total_uploads: u64,
    pub total_downloads: u64,
    pub total_shares: u64,
    pub active_connections: u32,
    pub bandwidth_usage: BandwidthUsage,
    pub storage_usage: StorageUsage,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BandwidthUsage {
    pub upload_rate: f64,
    pub download_rate: f64,
    pub total_uploaded: u64,
    pub total_downloaded: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct StorageUsage {
    pub used_bytes: u64,
    pub free_bytes: u64,
    pub total_bytes: u64,
    pub cache_size: u64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ExportOptions {
    pub include_servers: bool,
    pub include_preferences: bool,
    pub include_shares: bool,
    pub password: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ImportOptions {
    pub merge: bool,
    pub password: Option<String>,
}

// State management
pub struct SystemState {
    bandwidth_limits: Arc<Mutex<BandwidthLimits>>,
    logs: Arc<Mutex<Vec<LogEntry>>>,
}

impl SystemState {
    pub fn new() -> Self {
        Self {
            bandwidth_limits: Arc::new(Mutex::new(BandwidthLimits {
                upload_kbps: 0,
                download_kbps: 0,
                enabled: false,
            })),
            logs: Arc::new(Mutex::new(Vec::new())),
        }
    }
}

#[tauri::command]
pub async fn get_logs(
    filter: Option<LogFilter>,
    state: State<'_, SystemState>,
) -> Result<Vec<LogEntry>, String> {
    let logs = state.logs.lock().await;
    
    let mut filtered_logs = logs.clone();
    
    if let Some(f) = filter {
        // Apply level filter
        if let Some(level) = f.level {
            filtered_logs.retain(|log| log.level == level);
        }
        
        // Apply category filter
        if let Some(category) = f.category {
            filtered_logs.retain(|log| log.category == category);
        }
        
        // Apply search filter
        if let Some(search) = f.search {
            let search_lower = search.to_lowercase();
            filtered_logs.retain(|log| {
                log.message.to_lowercase().contains(&search_lower) ||
                log.category.to_lowercase().contains(&search_lower)
            });
        }
        
        // Apply pagination
        let offset = f.offset.unwrap_or(0);
        let limit = f.limit.unwrap_or(100);
        
        filtered_logs = filtered_logs
            .into_iter()
            .skip(offset)
            .take(limit)
            .collect();
    }
    
    Ok(filtered_logs)
}

#[tauri::command]
pub async fn set_bandwidth_limit(
    limits: BandwidthLimits,
    state: State<'_, SystemState>,
) -> Result<(), String> {
    let mut current_limits = state.bandwidth_limits.lock().await;
    *current_limits = limits;
    
    // Here you would also update the Python backend
    // For now, we just store it in memory
    
    Ok(())
}

#[tauri::command]
pub async fn get_bandwidth_limit(
    state: State<'_, SystemState>,
) -> Result<BandwidthLimits, String> {
    let limits = state.bandwidth_limits.lock().await;
    Ok(limits.clone())
}

#[tauri::command]
pub async fn get_statistics() -> Result<Statistics, String> {
    // This would fetch real statistics from the Python backend
    // For now, return mock data
    
    Ok(Statistics {
        total_uploads: 42,
        total_downloads: 128,
        total_shares: 15,
        active_connections: 3,
        bandwidth_usage: BandwidthUsage {
            upload_rate: 125.5,
            download_rate: 450.2,
            total_uploaded: 1024 * 1024 * 512, // 512 MB
            total_downloaded: 1024 * 1024 * 2048, // 2 GB
        },
        storage_usage: StorageUsage {
            used_bytes: 1024 * 1024 * 1024 * 10, // 10 GB
            free_bytes: 1024 * 1024 * 1024 * 90, // 90 GB
            total_bytes: 1024 * 1024 * 1024 * 100, // 100 GB
            cache_size: 1024 * 1024 * 256, // 256 MB
        },
    })
}

#[tauri::command]
pub async fn export_data(options: ExportOptions) -> Result<String, String> {
    // This would call the Python backend to export settings
    // For now, return a mock base64 encoded string
    
    let export_data = serde_json::json!({
        "version": "1.0.0",
        "created_at": chrono::Utc::now().to_rfc3339(),
        "settings": {
            "servers": if options.include_servers {
                serde_json::json!([
                    {
                        "host": "news.example.com",
                        "port": 563,
                        "ssl": true,
                        "username": "user123"
                    }
                ])
            } else {
                serde_json::json!([])
            },
            "preferences": if options.include_preferences {
                serde_json::json!({
                    "theme": "dark",
                    "auto_start": false,
                    "minimize_to_tray": true
                })
            } else {
                serde_json::json!({})
            },
            "shares": if options.include_shares {
                serde_json::json!([])
            } else {
                serde_json::json!([])
            }
        }
    });
    
    let json_str = serde_json::to_string(&export_data)
        .map_err(|e| e.to_string())?;
    
    // Base64 encode
    use base64::{Engine as _, engine::general_purpose};
    let encoded = general_purpose::STANDARD.encode(json_str.as_bytes());
    
    Ok(encoded)
}

#[tauri::command]
pub async fn import_data(
    data: String,
    options: ImportOptions
) -> Result<HashMap<String, serde_json::Value>, String> {
    // This would call the Python backend to import settings
    // For now, return mock result
    
    use base64::{Engine as _, engine::general_purpose};
    
    // Decode from base64
    let decoded = general_purpose::STANDARD
        .decode(data.as_bytes())
        .map_err(|e| e.to_string())?;
    
    let json_str = String::from_utf8(decoded)
        .map_err(|e| e.to_string())?;
    
    // Parse JSON
    let _import_data: serde_json::Value = serde_json::from_str(&json_str)
        .map_err(|e| e.to_string())?;
    
    // Return import result
    let mut result = HashMap::new();
    result.insert("imported".to_string(), serde_json::json!({
        "servers": 1,
        "preferences": 5,
        "shares": 0
    }));
    result.insert("skipped".to_string(), serde_json::json!({
        "servers": 0,
        "preferences": 2,
        "shares": 0
    }));
    result.insert("errors".to_string(), serde_json::json!([]));
    
    Ok(result)
}

#[tauri::command]
pub async fn clear_cache() -> Result<u64, String> {
    // This would clear the application cache
    // For now, return mock size cleared
    
    Ok(1024 * 1024 * 128) // 128 MB cleared
}

#[tauri::command]
pub async fn get_system_info() -> Result<HashMap<String, serde_json::Value>, String> {
    let mut info = HashMap::new();
    
    // Get system information
    info.insert("os".to_string(), serde_json::json!(std::env::consts::OS));
    info.insert("arch".to_string(), serde_json::json!(std::env::consts::ARCH));
    info.insert("version".to_string(), serde_json::json!(env!("CARGO_PKG_VERSION")));
    
    // Get memory info
    if let Ok(mem_info) = sys_info::mem_info() {
        info.insert("memory".to_string(), serde_json::json!({
            "total": mem_info.total * 1024,
            "free": mem_info.free * 1024,
            "used": (mem_info.total - mem_info.free) * 1024
        }));
    }
    
    // Get CPU info
    if let Ok(cpu_num) = sys_info::cpu_num() {
        info.insert("cpu_cores".to_string(), serde_json::json!(cpu_num));
    }
    
    Ok(info)
}

#[tauri::command]
pub async fn restart_services() -> Result<(), String> {
    // This would restart background services
    // For now, just return success
    
    Ok(())
}

// Initialize system commands
pub fn init_system_commands() -> SystemState {
    SystemState::new()
}
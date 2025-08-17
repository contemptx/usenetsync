use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use std::collections::HashMap;
use std::fs;
use std::process::Command as ProcessCommand;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogEntry {
    pub timestamp: String,
    pub level: String,
    pub message: String,
    pub source: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BandwidthLimits {
    pub upload_kbps: u32,
    pub download_kbps: u32,
    pub enabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemStats {
    pub cpu_usage: f32,
    pub memory_usage: f32,
    pub disk_usage: f32,
    pub network_speed: NetworkSpeed,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkSpeed {
    pub upload: u64,
    pub download: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemInfo {
    pub os: String,
    pub version: String,
    pub arch: String,
    pub cpu_cores: usize,
    pub total_memory: u64,
    pub free_memory: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExportOptions {
    pub include_logs: bool,
    pub include_settings: bool,
    pub include_shares: bool,
    pub encrypt: bool,
}

pub struct SystemState {
    logs: Arc<Mutex<Vec<LogEntry>>>,
    bandwidth_limits: Arc<Mutex<BandwidthLimits>>,
    statistics: Arc<Mutex<HashMap<String, f64>>>,
}

impl SystemState {
    pub fn new() -> Self {
        Self {
            logs: Arc::new(Mutex::new(Vec::new())),
            bandwidth_limits: Arc::new(Mutex::new(BandwidthLimits {
                upload_kbps: 0,
                download_kbps: 0,
                enabled: false,
            })),
            statistics: Arc::new(Mutex::new(HashMap::new())),
        }
    }
    
    pub async fn add_log(&self, level: String, message: String, source: Option<String>) {
        let mut logs = self.logs.lock().await;
        logs.push(LogEntry {
            timestamp: chrono::Utc::now().to_rfc3339(),
            level,
            message,
            source,
        });
        
        // Keep only last 10000 logs
        if logs.len() > 10000 {
            logs.drain(0..logs.len() - 10000);
        }
    }
}

pub fn init_system_commands() -> SystemState {
    SystemState::new()
}

#[tauri::command]
pub async fn get_logs(
    filter: Option<serde_json::Value>,
    state: tauri::State<'_, SystemState>,
) -> Result<Vec<LogEntry>, String> {
    let logs = state.logs.lock().await;
    
    // Apply filters if provided
    if let Some(filter_obj) = filter {
        let level_filter = filter_obj.get("level").and_then(|v| v.as_str());
        let source_filter = filter_obj.get("source").and_then(|v| v.as_str());
        let search = filter_obj.get("search").and_then(|v| v.as_str());
        
        let filtered: Vec<LogEntry> = logs.iter()
            .filter(|log| {
                if let Some(level) = level_filter {
                    if log.level != level {
                        return false;
                    }
                }
                if let Some(source) = source_filter {
                    if log.source.as_deref() != Some(source) {
                        return false;
                    }
                }
                if let Some(search_term) = search {
                    if !log.message.contains(search_term) {
                        return false;
                    }
                }
                true
            })
            .cloned()
            .collect();
            
        Ok(filtered)
    } else {
        Ok(logs.to_vec())
    }
}

#[tauri::command]
pub async fn set_bandwidth_limit(
    upload_kbps: u32,
    download_kbps: u32,
    enabled: bool,
    state: tauri::State<'_, SystemState>,
) -> Result<(), String> {
    let mut limits = state.bandwidth_limits.lock().await;
    *limits = BandwidthLimits {
        upload_kbps,
        download_kbps,
        enabled,
    };
    
    // Log the change
    state.add_log(
        "INFO".to_string(),
        format!("Bandwidth limits updated: Upload: {} kbps, Download: {} kbps, Enabled: {}", 
                upload_kbps, download_kbps, enabled),
        Some("system".to_string())
    ).await;
    
    // Call Python backend to apply limits
    ProcessCommand::new("python3")
        .args(&[
            "-c",
            &format!(
                "from src.core.integrated_backend import create_integrated_backend; \
                 backend = create_integrated_backend({{}}); \
                 backend.set_bandwidth_limits({}, {})",
                upload_kbps * 1024, download_kbps * 1024
            )
        ])
        .spawn()
        .map_err(|e| e.to_string())?;
    
    Ok(())
}

#[tauri::command]
pub async fn get_bandwidth_limit(
    state: tauri::State<'_, SystemState>,
) -> Result<BandwidthLimits, String> {
    let limits = state.bandwidth_limits.lock().await;
    Ok(limits.clone())
}

#[tauri::command]
pub async fn get_statistics(_state: tauri::State<'_, SystemState>) -> Result<SystemStats, String> {
    // Get real system statistics
    let mut sys = sysinfo::System::new_all();
    sys.refresh_all();
    
    // Calculate CPU usage
    let cpu_usage = sys.global_cpu_usage();
    
    // Calculate memory usage
    let total_mem = sys.total_memory();
    let used_mem = sys.used_memory();
    let memory_usage = if total_mem > 0 {
        (used_mem as f32 / total_mem as f32) * 100.0
    } else {
        0.0
    };
    
    // Calculate disk usage
    let mut total_disk = 0u64;
    let mut used_disk = 0u64;
    for disk in sys.disks() {
        total_disk += disk.total_space();
        used_disk += disk.total_space() - disk.available_space();
    }
    let disk_usage = if total_disk > 0 {
        (used_disk as f32 / total_disk as f32) * 100.0
    } else {
        0.0
    };
    
    // Network speed would require more sophisticated tracking
    let network_speed = NetworkSpeed {
        upload: 0,
        download: 0,
    };
    
    Ok(SystemStats {
        cpu_usage,
        memory_usage,
        disk_usage,
        network_speed,
    })
}

#[tauri::command]
pub async fn export_data(options: serde_json::Value, state: tauri::State<'_, SystemState>) -> Result<String, String> {
    use base64::{Engine as _, engine::general_purpose};
    
    let export_opts: ExportOptions = serde_json::from_value(options)
        .map_err(|e| e.to_string())?;
    
    let mut export_data = serde_json::json!({});
    
    if export_opts.include_logs {
        let logs = state.logs.lock().await;
        export_data["logs"] = serde_json::json!(logs.clone());
    }
    
    if export_opts.include_settings {
        let limits = state.bandwidth_limits.lock().await;
        export_data["settings"] = serde_json::json!({
            "bandwidth_limits": limits.clone()
        });
    }
    
    if export_opts.include_shares {
        // Call Python backend to get shares
        let output = ProcessCommand::new("python3")
            .args(&[
                "-c",
                "from src.cli import UsenetSyncCLI; cli = UsenetSyncCLI(); \
                 import json; print(json.dumps(cli.list_shares()))"
            ])
            .output()
            .map_err(|e| e.to_string())?;
        
        if output.status.success() {
            let shares_json = String::from_utf8_lossy(&output.stdout);
            if let Ok(shares) = serde_json::from_str::<serde_json::Value>(&shares_json) {
                export_data["shares"] = shares;
            }
        }
    }
    
    let json_str = serde_json::to_string(&export_data)
        .map_err(|e| e.to_string())?;
    
    if export_opts.encrypt {
        Ok(general_purpose::STANDARD.encode(json_str))
    } else {
        Ok(json_str)
    }
}

#[tauri::command]
pub async fn import_data(data: String, options: serde_json::Value, state: tauri::State<'_, SystemState>) -> Result<bool, String> {
    use base64::{Engine as _, engine::general_purpose};
    
    let encrypted = options.get("encrypted").and_then(|v| v.as_bool()).unwrap_or(false);
    
    let json_str = if encrypted {
        let decoded = general_purpose::STANDARD.decode(&data)
            .map_err(|e| e.to_string())?;
        String::from_utf8(decoded)
            .map_err(|e| e.to_string())?
    } else {
        data
    };
    
    let import_data: serde_json::Value = serde_json::from_str(&json_str)
        .map_err(|e| e.to_string())?;
    
    // Import logs
    if let Some(logs_data) = import_data.get("logs") {
        if let Ok(imported_logs) = serde_json::from_value::<Vec<LogEntry>>(logs_data.clone()) {
            let mut logs = state.logs.lock().await;
            logs.extend(imported_logs);
        }
    }
    
    // Import settings
    if let Some(settings_data) = import_data.get("settings") {
        if let Some(limits_data) = settings_data.get("bandwidth_limits") {
            if let Ok(imported_limits) = serde_json::from_value::<BandwidthLimits>(limits_data.clone()) {
                let mut limits = state.bandwidth_limits.lock().await;
                *limits = imported_limits;
            }
        }
    }
    
    state.add_log(
        "INFO".to_string(),
        "Data imported successfully".to_string(),
        Some("system".to_string())
    ).await;
    
    Ok(true)
}

#[tauri::command]
pub async fn clear_cache(state: tauri::State<'_, SystemState>) -> Result<(), String> {
    // Clear application cache directories
    let cache_dirs = vec![
        dirs::cache_dir().map(|d| d.join("usenet-sync")),
        Some(std::env::temp_dir().join("usenet-sync")),
    ];
    
    for cache_dir in cache_dirs.into_iter().flatten() {
        if cache_dir.exists() {
            // Remove cache directory contents
            if let Err(e) = fs::remove_dir_all(&cache_dir) {
                // Try to at least clear files if directory removal fails
                if let Ok(entries) = fs::read_dir(&cache_dir) {
                    for entry in entries.flatten() {
                        let _ = fs::remove_file(entry.path());
                    }
                }
            }
            // Recreate the directory
            let _ = fs::create_dir_all(&cache_dir);
        }
    }
    
    // Clear Python cache
    ProcessCommand::new("python3")
        .args(&[
            "-c",
            "from src.core.integrated_backend import create_integrated_backend; \
             backend = create_integrated_backend({{}}); \
             backend.data_manager.clear_cache()"
        ])
        .spawn()
        .map_err(|e| e.to_string())?;
    
    state.add_log(
        "INFO".to_string(),
        "Cache cleared successfully".to_string(),
        Some("system".to_string())
    ).await;
    
    Ok(())
}

#[tauri::command]
pub async fn get_system_info() -> Result<SystemInfo, String> {
    let mut sys = sysinfo::System::new_all();
    sys.refresh_all();
    
    Ok(SystemInfo {
        os: std::env::consts::OS.to_string(),
        version: sys.os_version().unwrap_or_else(|| "Unknown".to_string()),
        arch: std::env::consts::ARCH.to_string(),
        cpu_cores: num_cpus::get(),
        total_memory: sys.total_memory(),
        free_memory: sys.available_memory(),
    })
}

#[tauri::command]
pub async fn restart_services(state: tauri::State<'_, SystemState>) -> Result<(), String> {
    // Restart Python backend service
    #[cfg(not(target_os = "windows"))]
    {
        // Stop existing service
        ProcessCommand::new("pkill")
            .args(&["-f", "usenet_sync_backend"])
            .output()
            .map_err(|e| format!("Failed to stop service: {}", e))?;
        
        std::thread::sleep(std::time::Duration::from_secs(2));
        
        // Start service
        ProcessCommand::new("python3")
            .args(&["src/usenet_sync_backend.py", "--daemon"])
            .current_dir("/workspace")
            .spawn()
            .map_err(|e| format!("Failed to start service: {}", e))?;
    }
    
    #[cfg(target_os = "windows")]
    {
        // Stop existing service
        ProcessCommand::new("taskkill")
            .args(&["/F", "/IM", "python.exe", "/FI", "WINDOWTITLE eq UsenetSync Backend"])
            .output()
            .map_err(|e| format!("Failed to stop service: {}", e))?;
        
        std::thread::sleep(std::time::Duration::from_secs(2));
        
        // Start service
        ProcessCommand::new("python")
            .args(&["src\\usenet_sync_backend.py", "--daemon"])
            .current_dir("C:\\workspace")
            .spawn()
            .map_err(|e| format!("Failed to start service: {}", e))?;
    }
    
    state.add_log(
        "INFO".to_string(),
        "Services restarted successfully".to_string(),
        Some("system".to_string())
    ).await;
    
    Ok(())
}

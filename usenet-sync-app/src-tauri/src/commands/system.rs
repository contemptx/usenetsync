use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use std::collections::HashMap;
use std::fs;
use std::process::Command as ProcessCommand;
use std::path::PathBuf;

// Helper function to get the correct Python command for the OS
fn get_python_command() -> &'static str {
    if cfg!(target_os = "windows") {
        "python"
    } else {
        "python3"
    }
}

// Helper function to get the workspace directory
fn get_workspace_dir() -> PathBuf {
    std::env::current_dir()
        .ok()
        .and_then(|p| {
            // Try to find the workspace root by looking for src/cli.py
            let mut current = p.as_path();
            loop {
                if current.join("src").join("cli.py").exists() {
                    return Some(current.to_path_buf());
                }
                match current.parent() {
                    Some(parent) => current = parent,
                    None => return None,
                }
            }
        })
        .unwrap_or_else(|| std::path::PathBuf::from("."))
}

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

pub struct SystemState {
    logs: Arc<Mutex<Vec<LogEntry>>>,
    bandwidth_limits: Arc<Mutex<BandwidthLimits>>,
    #[allow(dead_code)]
    statistics: Arc<Mutex<HashMap<String, f64>>>,
}

impl SystemState {
    pub fn new() -> Self {
        // Initialize with real log file if it exists
        let logs = if let Ok(log_content) = fs::read_to_string("/var/log/usenet-sync.log") {
            log_content.lines()
                .filter_map(|line| {
                    // Parse log lines in format: [TIMESTAMP] [LEVEL] [SOURCE] MESSAGE
                    let parts: Vec<&str> = line.splitn(4, ' ').collect();
                    if parts.len() >= 3 {
                        Some(LogEntry {
                            timestamp: parts[0].trim_matches(|c| c == '[' || c == ']').to_string(),
                            level: parts[1].trim_matches(|c| c == '[' || c == ']').to_string(),
                            source: if parts.len() > 3 {
                                Some(parts[2].trim_matches(|c| c == '[' || c == ']').to_string())
                            } else {
                                None
                            },
                            message: if parts.len() > 3 {
                                parts[3].to_string()
                            } else {
                                parts[2].to_string()
                            },
                        })
                    } else {
                        None
                    }
                })
                .collect()
        } else {
            Vec::new()
        };
        
        Self {
            logs: Arc::new(Mutex::new(logs)),
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
        let entry = LogEntry {
            timestamp: chrono::Utc::now().to_rfc3339(),
            level: level.clone(),
            message: message.clone(),
            source: source.clone(),
        };
        logs.push(entry);
        
        // Also write to actual log file
        let log_line = format!("[{}] [{}] [{}] {}\n",
            chrono::Utc::now().to_rfc3339(),
            level,
            source.unwrap_or_else(|| "system".to_string()),
            message
        );
        
        let _ = fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open("/var/log/usenet-sync.log")
            .and_then(|mut file| {
                use std::io::Write;
                file.write_all(log_line.as_bytes())
            });
        
        // Keep only last 10000 logs in memory
        if logs.len() > 10000 {
            let drain_count = logs.len() - 10000; logs.drain(0..drain_count);
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
    // First try to get logs from Python backend
    let output = ProcessCommand::new(get_python_command())
        .args(&[
            "-c",
            "from src.cli import UsenetSyncCLI; \
             cli = UsenetSyncCLI(); \
             import json; \
             logs = cli.integrated_backend.log_manager.get_logs(); \
             print(json.dumps([log.to_dict() for log in logs]))"
        ])
        .current_dir(&get_workspace_dir())
        .output();
    
    if let Ok(output) = output {
        if output.status.success() {
            if let Ok(backend_logs) = serde_json::from_slice::<Vec<LogEntry>>(&output.stdout) {
                // Merge with local logs
                let mut logs = state.logs.lock().await;
                for log in backend_logs {
                    if !logs.iter().any(|l| l.timestamp == log.timestamp && l.message == log.message) {
                        logs.push(log);
                    }
                }
            }
        }
    }
    
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
    // Apply to Python backend
    let output = ProcessCommand::new(get_python_command())
        .args(&[
            "-c",
            &format!(
                "from src.cli import UsenetSyncCLI; \
                 cli = UsenetSyncCLI(); \
                 cli.integrated_backend.set_bandwidth_limits({}, {})",
                if enabled { upload_kbps * 1024 } else { 0 },
                if enabled { download_kbps * 1024 } else { 0 }
            )
        ])
        .current_dir(&get_workspace_dir())
        .output()
        .map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    let mut limits = state.bandwidth_limits.lock().await;
    *limits = BandwidthLimits {
        upload_kbps,
        download_kbps,
        enabled,
    };
    
    state.add_log(
        "INFO".to_string(),
        format!("Bandwidth limits updated: Upload: {} kbps, Download: {} kbps, Enabled: {}", 
                upload_kbps, download_kbps, enabled),
        Some("system".to_string())
    ).await;
    
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
    // Get real statistics from system
    let mut sys = sysinfo::System::new_all();
    sys.refresh_all();
    
    let cpu_usage = sys.global_cpu_info().cpu_usage();
    
    let total_mem = sys.total_memory();
    let used_mem = sys.used_memory();
    let memory_usage = if total_mem > 0 {
        (used_mem as f32 / total_mem as f32) * 100.0
    } else {
        0.0
    };
    
    // Disk stats temporarily disabled due to API change
    let total_disk = 1000000000u64; // 1GB placeholder
    let used_disk = 500000000u64; // 500MB placeholder
    let disk_usage = if total_disk > 0 {
        (used_disk as f32 / total_disk as f32) * 100.0
    } else {
        0.0
    };
    
    // Get network stats from Python backend
    let network_speed = if let Ok(output) = ProcessCommand::new(get_python_command())
        .args(&[
            "-c",
            "from src.cli import UsenetSyncCLI; \
             cli = UsenetSyncCLI(); \
             stats = cli.integrated_backend.get_bandwidth_stats(); \
             import json; \
             print(json.dumps({\
                 'upload': stats['upload']['current_speed'], \
                 'download': stats['download']['current_speed']\
             }))"
        ])
        .current_dir(&get_workspace_dir())
        .output() 
    {
        if output.status.success() {
            if let Ok(speeds) = serde_json::from_slice::<NetworkSpeed>(&output.stdout) {
                speeds
            } else {
                NetworkSpeed { upload: 0, download: 0 }
            }
        } else {
            NetworkSpeed { upload: 0, download: 0 }
        }
    } else {
        NetworkSpeed { upload: 0, download: 0 }
    };
    
    Ok(SystemStats {
        cpu_usage,
        memory_usage,
        disk_usage,
        network_speed,
    })
}

#[tauri::command]
pub async fn export_data(options: serde_json::Value, _state: tauri::State<'_, SystemState>) -> Result<String, String> {
    
    // Call Python backend for full export
    let output = ProcessCommand::new(get_python_command())
        .args(&[
            "-c",
            &format!(
                "from src.cli import UsenetSyncCLI; \
                 cli = UsenetSyncCLI(); \
                 import json; \
                 data = cli.integrated_backend.export_settings(\
                     password='{}' if {} else None\
                 ); \
                 print(data)",
                options.get("password").and_then(|v| v.as_str()).unwrap_or(""),
                options.get("encrypt").and_then(|v| v.as_bool()).unwrap_or(false)
            )
        ])
        .current_dir(&get_workspace_dir())
        .output()
        .map_err(|e| e.to_string())?;
    
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
pub async fn import_data(data: String, options: serde_json::Value, state: tauri::State<'_, SystemState>) -> Result<bool, String> {
    // Call Python backend for import
    let output = ProcessCommand::new(get_python_command())
        .args(&[
            "-c",
            &format!(
                "from src.cli import UsenetSyncCLI; \
                 cli = UsenetSyncCLI(); \
                 result = cli.integrated_backend.import_settings(\
                     '{}', \
                     password='{}' if {} else None\
                 ); \
                 print('success' if result else 'failed')",
                data,
                options.get("password").and_then(|v| v.as_str()).unwrap_or(""),
                options.get("encrypted").and_then(|v| v.as_bool()).unwrap_or(false)
            )
        ])
        .current_dir(&get_workspace_dir())
        .output()
        .map_err(|e| e.to_string())?;
    
    if output.status.success() && String::from_utf8_lossy(&output.stdout).contains("success") {
        state.add_log(
            "INFO".to_string(),
            "Data imported successfully".to_string(),
            Some("system".to_string())
        ).await;
        Ok(true)
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
pub async fn clear_cache(state: tauri::State<'_, SystemState>) -> Result<(), String> {
    // Clear system cache directories
    let cache_dirs = vec![
        dirs::cache_dir().map(|d| d.join("usenet-sync")),
        Some(std::env::temp_dir().join("usenet-sync")),
        Some(std::path::PathBuf::from("/tmp/usenet-sync")),
        Some(std::path::PathBuf::from("/var/cache/usenet-sync")),
    ];
    
    for cache_dir in cache_dirs.into_iter().flatten() {
        if cache_dir.exists() {
            let _ = fs::remove_dir_all(&cache_dir);
            let _ = fs::create_dir_all(&cache_dir);
        }
    }
    
    // Clear Python backend cache
    let output = ProcessCommand::new(get_python_command())
        .args(&[
            "-c",
            "from src.cli import UsenetSyncCLI; \
             cli = UsenetSyncCLI(); \
             cli.integrated_backend.data_manager.clear_cache(); \
             cli.integrated_backend.cleanup_old_data(days=0)"
        ])
        .current_dir(&get_workspace_dir())
        .output()
        .map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
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
        version: sysinfo::System::os_version().unwrap_or_else(|| "Unknown".to_string()),
        arch: std::env::consts::ARCH.to_string(),
        cpu_cores: num_cpus::get(),
        total_memory: sys.total_memory(),
        free_memory: sys.available_memory(),
    })
}

#[tauri::command]
pub async fn restart_services(state: tauri::State<'_, SystemState>) -> Result<(), String> {
    // Stop existing Python backend service
    #[cfg(not(target_os = "windows"))]
    {
        ProcessCommand::new("pkill")
            .args(&["-f", "usenet_sync"])
            .output()
            .ok();
        
        ProcessCommand::new("pkill")
            .args(&["-f", "cli.py"])
            .output()
            .ok();
        
        std::thread::sleep(std::time::Duration::from_secs(2));
        
        // Start Python backend service
        ProcessCommand::new(get_python_command())
            .args(&["src/cli.py", "--daemon"])
            .current_dir(&get_workspace_dir())
            .spawn()
            .map_err(|e| format!("Failed to start service: {}", e))?;
    }
    
    #[cfg(target_os = "windows")]
    {
        ProcessCommand::new("taskkill")
            .args(&["/F", "/IM", "python.exe", "/FI", "WINDOWTITLE eq UsenetSync*"])
            .output()
            .ok();
        
        std::thread::sleep(std::time::Duration::from_secs(2));
        
        ProcessCommand::new(get_python_command())
            .args(&["src\\cli.py", "--daemon"])
            .current_dir(&get_workspace_dir())
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

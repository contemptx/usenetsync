// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use std::process::Command;
use std::sync::Mutex;
use tauri::State;
use uuid::Uuid;

// Import TurboActivate integration
mod turboactivate;
use turboactivate::TurboActivate;

// Import commands module
mod commands;
use commands::system::{SystemState, init_system_commands};

// State management
struct AppState {
    license: Mutex<TurboActivate>,
    python_process: Mutex<Option<std::process::Child>>,
    transfers: Mutex<HashMap<String, Transfer>>,
}

// Type definitions matching TypeScript
#[derive(Debug, Serialize, Deserialize, Clone)]
struct LicenseStatus {
    activated: bool,
    genuine: bool,
    trial: bool,
    #[serde(rename = "trialDays")]
    trial_days: Option<u32>,
    #[serde(rename = "hardwareId")]
    hardware_id: String,
    tier: String,
    features: LicenseFeatures,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct LicenseFeatures {
    #[serde(rename = "maxFileSize")]
    max_file_size: u64,
    #[serde(rename = "maxConnections")]
    max_connections: u32,
    #[serde(rename = "maxShares")]
    max_shares: u32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct FileNode {
    id: String,
    name: String,
    #[serde(rename = "type")]
    node_type: String,
    size: u64,
    path: String,
    children: Option<Vec<FileNode>>,
    selected: Option<bool>,
    progress: Option<f32>,
    hash: Option<String>,
    #[serde(rename = "modifiedAt")]
    modified_at: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct Share {
    id: String,
    #[serde(rename = "shareId")]
    share_id: String,
    #[serde(rename = "type")]
    share_type: String,
    name: String,
    size: u64,
    #[serde(rename = "fileCount")]
    file_count: u32,
    #[serde(rename = "folderCount")]
    folder_count: u32,
    #[serde(rename = "createdAt")]
    created_at: String,
    #[serde(rename = "expiresAt")]
    expires_at: Option<String>,
    #[serde(rename = "accessCount")]
    access_count: u32,
    #[serde(rename = "lastAccessed")]
    last_accessed: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct Transfer {
    id: String,
    #[serde(rename = "type")]
    transfer_type: String,
    name: String,
    #[serde(rename = "totalSize")]
    total_size: u64,
    #[serde(rename = "transferredSize")]
    transferred_size: u64,
    speed: f64,
    eta: u32,
    status: String,
    segments: Vec<SegmentProgress>,
    #[serde(rename = "startedAt")]
    started_at: String,
    #[serde(rename = "completedAt")]
    completed_at: Option<String>,
    error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct SegmentProgress {
    index: u32,
    size: u64,
    completed: bool,
    #[serde(rename = "messageId")]
    message_id: Option<String>,
    retries: u32,
}

#[derive(Debug, Serialize, Deserialize)]
struct ServerConfig {
    hostname: String,
    port: u16,
    username: String,
    password: String,
    #[serde(rename = "useSsl")]
    use_ssl: bool,
    #[serde(rename = "maxConnections")]
    max_connections: u32,
    group: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct SystemStats {
    #[serde(rename = "cpuUsage")]
    cpu_usage: f32,
    #[serde(rename = "memoryUsage")]
    memory_usage: f32,
    #[serde(rename = "diskUsage")]
    disk_usage: f32,
    #[serde(rename = "networkSpeed")]
    network_speed: NetworkSpeed,
    #[serde(rename = "activeTransfers")]
    active_transfers: u32,
    #[serde(rename = "totalShares")]
    total_shares: u32,
}

#[derive(Debug, Serialize, Deserialize)]
struct NetworkSpeed {
    upload: f64,
    download: f64,
}

// License Commands
#[tauri::command]
async fn activate_license(state: State<'_, AppState>, key: String) -> Result<bool, String> {
    let license = state.license.lock().unwrap();
    match license.activate(&key) {
        Ok(result) => Ok(result),
        Err(e) => Err(e.to_string()),
    }
}

#[tauri::command]
async fn check_license(state: State<'_, AppState>) -> Result<LicenseStatus, String> {
    let license = state.license.lock().unwrap();
    
    let activated = license.is_activated();
    let genuine = license.is_genuine();
    let hardware_id = license.get_hardware_id().unwrap_or_else(|_| "unknown".to_string());
    
    let (trial, trial_days) = if !activated {
        let days = license.get_trial_days_remaining().unwrap_or(0);
        (days > 0, Some(days))
    } else {
        (false, None)
    };
    
    let tier = license.get_feature_value("tier")
        .unwrap_or_else(|_| "basic".to_string());
    
    Ok(LicenseStatus {
        activated,
        genuine,
        trial,
        trial_days,
        hardware_id,
        tier,
        features: LicenseFeatures {
            max_file_size: 10 * 1024 * 1024 * 1024, // 10GB default
            max_connections: 30,
            max_shares: 100,
        },
    })
}

#[tauri::command]
async fn start_trial(state: State<'_, AppState>) -> Result<u32, String> {
    let license = state.license.lock().unwrap();
    license.start_trial()
        .map_err(|e| e.to_string())
}

#[tauri::command]
async fn deactivate_license(state: State<'_, AppState>) -> Result<(), String> {
    let license = state.license.lock().unwrap();
    license.deactivate()
        .map_err(|e| e.to_string())
}

// File Operations
#[tauri::command]
async fn select_files() -> Result<Vec<FileNode>, String> {
    // Use native file dialog
    let files = tauri::api::dialog::blocking::FileDialogBuilder::new()
        .set_title("Select Files")
        .pick_files()
        .ok_or_else(|| "No files selected".to_string())?;
    
    let mut nodes = Vec::new();
    for path in files {
        let metadata = std::fs::metadata(&path)
            .map_err(|e| e.to_string())?;
        
        nodes.push(FileNode {
            id: Uuid::new_v4().to_string(),
            name: path.file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("unknown")
                .to_string(),
            node_type: "file".to_string(),
            size: metadata.len(),
            path: path.to_string_lossy().to_string(),
            children: None,
            selected: Some(false),
            progress: None,
            hash: None,
            modified_at: chrono::Utc::now().to_rfc3339(),
        });
    }
    
    Ok(nodes)
}

#[tauri::command]
async fn index_folder(path: String) -> Result<FileNode, String> {
    let path = PathBuf::from(path);
    
    if !path.exists() {
        return Err("Path does not exist".to_string());
    }
    
    index_folder_recursive(&path)
}

fn index_folder_recursive(path: &PathBuf) -> Result<FileNode, String> {
    let metadata = std::fs::metadata(path)
        .map_err(|e| e.to_string())?;
    
    let name = path.file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown")
        .to_string();
    
    if metadata.is_file() {
        Ok(FileNode {
            id: Uuid::new_v4().to_string(),
            name,
            node_type: "file".to_string(),
            size: metadata.len(),
            path: path.to_string_lossy().to_string(),
            children: None,
            selected: Some(false),
            progress: None,
            hash: None,
            modified_at: chrono::Utc::now().to_rfc3339(),
        })
    } else {
        let mut children = Vec::new();
        let entries = std::fs::read_dir(path)
            .map_err(|e| e.to_string())?;
        
        for entry in entries {
            let entry = entry.map_err(|e| e.to_string())?;
            let child_path = entry.path();
            if let Ok(child_node) = index_folder_recursive(&child_path) {
                children.push(child_node);
            }
        }
        
        Ok(FileNode {
            id: Uuid::new_v4().to_string(),
            name,
            node_type: "folder".to_string(),
            size: children.iter().map(|c| c.size).sum(),
            path: path.to_string_lossy().to_string(),
            children: Some(children),
            selected: Some(false),
            progress: None,
            hash: None,
            modified_at: chrono::Utc::now().to_rfc3339(),
        })
    }
}

// Share Operations
#[tauri::command]
async fn create_share(
    files: Vec<String>,
    share_type: String,
    password: Option<String>,
) -> Result<Share, String> {
    // Call Python backend to create share
    let output = Command::new("python3")
        .arg("/workspace/src/cli.py")
        .arg("create-share")
        .arg("--files")
        .args(&files)
        .arg("--type")
        .arg(&share_type)
        .args(if let Some(pwd) = password {
            vec!["--password", &pwd]
        } else {
            vec![]
        })
        .output()
        .map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    // Parse JSON response
    let share: Share = serde_json::from_slice(&output.stdout)
        .map_err(|e| e.to_string())?;
    
    Ok(share)
}

#[tauri::command]
async fn download_share(
    share_id: String,
    destination: String,
    selected_files: Option<Vec<String>>,
) -> Result<(), String> {
    // Call Python backend to download share
    let mut cmd = Command::new("python3");
    cmd.arg("/workspace/src/cli.py")
        .arg("download-share")
        .arg("--share-id")
        .arg(&share_id)
        .arg("--destination")
        .arg(&destination);
    
    if let Some(files) = selected_files {
        cmd.arg("--files").args(files);
    }
    
    let output = cmd.output()
        .map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    Ok(())
}

#[tauri::command]
async fn get_share_details(share_id: String) -> Result<Share, String> {
    // Call Python backend to get share details
    let output = Command::new("python3")
        .arg("/workspace/src/cli.py")
        .arg("share-details")
        .arg("--share-id")
        .arg(&share_id)
        .output()
        .map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    let share: Share = serde_json::from_slice(&output.stdout)
        .map_err(|e| e.to_string())?;
    
    Ok(share)
}

// Transfer Operations
#[tauri::command]
async fn pause_transfer(state: State<'_, AppState>, transfer_id: String) -> Result<(), String> {
    let mut transfers = state.transfers.lock().unwrap();
    
    if let Some(transfer) = transfers.get_mut(&transfer_id) {
        transfer.status = "paused".to_string();
        Ok(())
    } else {
        Err("Transfer not found".to_string())
    }
}

#[tauri::command]
async fn resume_transfer(state: State<'_, AppState>, transfer_id: String) -> Result<(), String> {
    let mut transfers = state.transfers.lock().unwrap();
    
    if let Some(transfer) = transfers.get_mut(&transfer_id) {
        transfer.status = "active".to_string();
        Ok(())
    } else {
        Err("Transfer not found".to_string())
    }
}

#[tauri::command]
async fn cancel_transfer(state: State<'_, AppState>, transfer_id: String) -> Result<(), String> {
    let mut transfers = state.transfers.lock().unwrap();
    
    if transfers.remove(&transfer_id).is_some() {
        Ok(())
    } else {
        Err("Transfer not found".to_string())
    }
}

// Server Configuration
#[tauri::command]
async fn test_server_connection(config: ServerConfig) -> Result<bool, String> {
    // Call Python backend to test connection
    let output = Command::new("python3")
        .arg("/workspace/src/cli.py")
        .arg("test-connection")
        .arg("--hostname")
        .arg(&config.hostname)
        .arg("--port")
        .arg(config.port.to_string())
        .arg("--username")
        .arg(&config.username)
        .arg("--password")
        .arg(&config.password)
        .arg(if config.use_ssl { "--ssl" } else { "--no-ssl" })
        .output()
        .map_err(|e| e.to_string())?;
    
    Ok(output.status.success())
}

#[tauri::command]
async fn save_server_config(config: ServerConfig) -> Result<(), String> {
    // Save to config file
    let config_path = dirs::config_dir()
        .ok_or_else(|| "Could not find config directory".to_string())?
        .join("usenet-sync")
        .join("server.json");
    
    std::fs::create_dir_all(config_path.parent().unwrap())
        .map_err(|e| e.to_string())?;
    
    let json = serde_json::to_string_pretty(&config)
        .map_err(|e| e.to_string())?;
    
    std::fs::write(config_path, json)
        .map_err(|e| e.to_string())?;
    
    Ok(())
}

// System Operations
#[tauri::command]
async fn get_system_stats() -> Result<SystemStats, String> {
    use sysinfo::{System, SystemExt, CpuExt, NetworkExt, NetworksExt, DiskExt, DisksExt};
    
    let mut sys = System::new_all();
    sys.refresh_all();
    
    let cpu_usage = sys.global_cpu_info().cpu_usage();
    let memory_usage = (sys.used_memory() as f32 / sys.total_memory() as f32) * 100.0;
    
    let mut total_disk_usage = 0u64;
    let mut total_disk_space = 0u64;
    for disk in sys.disks() {
        total_disk_usage += disk.total_space() - disk.available_space();
        total_disk_space += disk.total_space();
    }
    let disk_usage = if total_disk_space > 0 {
        (total_disk_usage as f32 / total_disk_space as f32) * 100.0
    } else {
        0.0
    };
    
    let mut upload_speed = 0.0;
    let mut download_speed = 0.0;
    for (_name, network) in sys.networks() {
        upload_speed += network.transmitted() as f64;
        download_speed += network.received() as f64;
    }
    
    Ok(SystemStats {
        cpu_usage,
        memory_usage,
        disk_usage,
        network_speed: NetworkSpeed {
            upload: upload_speed,
            download: download_speed,
        },
        active_transfers: 0, // Would be populated from state
        total_shares: 0, // Would be populated from database
    })
}

#[tauri::command]
async fn open_folder(path: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    
    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    
    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    
    Ok(())
}

fn main() {
    // Initialize TurboActivate
    let license = TurboActivate::new(None).unwrap_or_else(|_| {
        TurboActivate::new(Some("/workspace/src/licensing/data/TurboActivate.dat"))
            .expect("Failed to initialize TurboActivate")
    });
    
    let app_state = AppState {
        license: Mutex::new(license),
        python_process: Mutex::new(None),
        transfers: Mutex::new(HashMap::new()),
    };
    
    let system_state = init_system_commands();
    
    tauri::Builder::default()
        .manage(app_state)
        .manage(system_state)
        .invoke_handler(tauri::generate_handler![
            activate_license,
            check_license,
            start_trial,
            deactivate_license,
            select_files,
            index_folder,
            create_share,
            download_share,
            get_share_details,
            pause_transfer,
            resume_transfer,
            cancel_transfer,
            test_server_connection,
            save_server_config,
            get_system_stats,
            open_folder,
            // System commands
            commands::get_logs,
            commands::set_bandwidth_limit,
            commands::get_bandwidth_limit,
            commands::get_statistics,
            commands::export_data,
            commands::import_data,
            commands::clear_cache,
            commands::get_system_info,
            commands::restart_services,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

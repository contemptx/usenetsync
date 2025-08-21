// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use serde_json;
use std::collections::HashMap;
use std::path::PathBuf;
use std::process::Command;
use std::sync::Mutex;
use tauri::State;
// use uuid::Uuid; // Not needed

// Import TurboActivate integration
mod turboactivate;
use turboactivate::TurboActivate;

// Import commands module
mod commands;
use commands::system::init_system_commands;

// Import unified backend integration
mod unified_backend;
use unified_backend::execute_unified_command;

// Helper function to get the workspace directory
fn get_workspace_dir() -> PathBuf {
    std::env::current_dir()
        .ok()
        .and_then(|p| {
            // Try to find the workspace root by looking for src/gui_backend_bridge.py
            let mut current = p.as_path();
            loop {
                // Check for unified backend first
                if current.join("src").join("gui_backend_bridge.py").exists() {
                    return Some(current.to_path_buf());
                }
                // Fallback to old CLI for compatibility
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



// Type definitions
#[allow(dead_code)]
struct AppState {
    turboactivate: TurboActivate,
    python_process: Mutex<Option<std::process::Child>>,
    transfers: Mutex<HashMap<String, Transfer>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Transfer {
    id: String,
    status: String,
    progress: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ServerConfig {
    hostname: String,
    port: u16,
    username: String,
    password: String,
    use_ssl: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[allow(non_snake_case)]
struct SystemStats {
    totalFiles: u64,
    totalSize: u64,
    totalShares: u64,
    activeUploads: u64,
    activeDownloads: u64,
    cpuUsage: f32,
    memoryUsage: f32,
    diskUsage: f32,
    uploadSpeed: NetworkSpeed,
    downloadSpeed: NetworkSpeed,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct NetworkSpeed {
    current: f64,
    average: f64,
    peak: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Share {
    id: String,
    name: String,
    size: u64,
    created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct FileNode {
    id: String,
    name: String,
    path: String,
    size: u64,
    is_directory: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct LicenseStatus {
    valid: bool,
    trial: bool,
    days_remaining: u32,
}



// License Management Commands
#[tauri::command]
async fn activate_license(_state: State<'_, AppState>, _key: String) -> Result<bool, String> {
    Ok(true) // TurboActivate would be implemented here
}

#[tauri::command]
async fn check_license(_state: State<'_, AppState>) -> Result<LicenseStatus, String> {
    let valid = true; // TurboActivate would check this
    let trial = false;
    let days_remaining = 30;
    
    Ok(LicenseStatus {
        valid,
        trial,
        days_remaining,
    })
}

#[tauri::command]
async fn start_trial(_state: State<'_, AppState>) -> Result<u32, String> {
    Ok(30) // Trial days
}

#[tauri::command]
async fn deactivate_license(_state: State<'_, AppState>) -> Result<(), String> {
    Ok(()) // Deactivation would happen here
}

// File Selection Commands
#[tauri::command]
async fn select_files(_app: tauri::AppHandle) -> Result<Vec<FileNode>, String> {
    // This would open a file dialog in production
    // For now, return mock data
    Ok(vec![
        FileNode {
            id: "file1".to_string(),
            name: "document.pdf".to_string(),
            path: "/home/user/document.pdf".to_string(),
            size: 1024000,
            is_directory: false,
        }
    ])
}

#[tauri::command]
async fn select_folder(_app: tauri::AppHandle) -> Result<FileNode, String> {
    // This would open a folder dialog in production
    // For now, return mock data
    Ok(FileNode {
        id: "folder1".to_string(),
        name: "Documents".to_string(),
        path: "/home/user/Documents".to_string(),
        size: 0,
        is_directory: true,
    })
}

#[tauri::command]
async fn index_folder(path: String) -> Result<FileNode, String> {
    // Index the folder using unified backend
    let args = serde_json::json!({
        "path": path
    });
    
    let result = execute_unified_command("index_folder", args)
        .map_err(|e| format!("Failed to index folder: {}", e))?;
    
    if result.success {
        Ok(FileNode {
            id: "indexed".to_string(),
            name: std::path::Path::new(&path)
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("folder")
                .to_string(),
            path,
            size: 0,
            is_directory: true,
        })
    } else {
        Err(result.error.unwrap_or_else(|| "Failed to index".to_string()))
    }
}

// Share Management Commands
#[tauri::command]
async fn create_share(files: Vec<String>, share_type: String, password: Option<String>) -> Result<Share, String> {
    let args = serde_json::json!({
        "files": files,
        "share_type": share_type,
        "password": password
    });
    
    let result = execute_unified_command("create_share", args)
        .map_err(|e| format!("Failed to create share: {}", e))?;
    
    if result.success {
        if let Some(data) = result.data {
            let share: Share = serde_json::from_value(data)
                .map_err(|e| format!("Failed to parse share: {}", e))?;
            Ok(share)
        } else {
            Err("No share data returned".to_string())
        }
    } else {
        Err(result.error.unwrap_or_else(|| "Failed to create share".to_string()))
    }
}

#[tauri::command]
async fn get_shares() -> Result<Vec<Share>, String> {
    let args = serde_json::json!({});
    
    let result = execute_unified_command("get_shares", args)
        .map_err(|e| format!("Failed to get shares: {}", e))?;
    
    if result.success {
        if let Some(data) = result.data {
            let shares: Vec<Share> = serde_json::from_value(data)
                .map_err(|e| format!("Failed to parse shares: {}", e))?;
            Ok(shares)
        } else {
            Ok(Vec::new())
        }
    } else {
        Err(result.error.unwrap_or_else(|| "Failed to get shares".to_string()))
    }
}

#[tauri::command]
async fn download_share(share_id: String, destination: String, selected_files: Option<Vec<String>>) -> Result<(), String> {
    let args = serde_json::json!({
        "share_id": share_id,
        "destination": destination,
        "selected_files": selected_files
    });
    
    let result = execute_unified_command("download_share", args)
        .map_err(|e| format!("Failed to download share: {}", e))?;
    
    if result.success {
        Ok(())
    } else {
        Err(result.error.unwrap_or_else(|| "Failed to download share".to_string()))
    }
}

#[tauri::command]
async fn get_share_details(share_id: String) -> Result<Share, String> {
    let args = serde_json::json!({
        "share_id": share_id
    });
    
    let result = execute_unified_command("get_share_details", args)
        .map_err(|e| format!("Failed to get share details: {}", e))?;
    
    if result.success {
        if let Some(data) = result.data {
            let share: Share = serde_json::from_value(data)
                .map_err(|e| format!("Failed to parse share details: {}", e))?;
            Ok(share)
        } else {
            Err("No share data returned".to_string())
        }
    } else {
        Err(result.error.unwrap_or_else(|| "Failed to get share details".to_string()))
    }
}

// Folder Management Commands
#[tauri::command]
async fn add_folder(path: String, name: Option<String>) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "path": path,
        "name": name
    });
    
    let result = execute_unified_command("add_folder", args)
        .map_err(|e| format!("Failed to add folder: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Failed to add folder".to_string()))
    }
}

#[tauri::command]
async fn index_folder_full(folder_id: String) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "folder_id": folder_id
    });
    
    let result = execute_unified_command("index_folder", args)
        .map_err(|e| format!("Failed to index folder: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Failed to index folder".to_string()))
    }
}

#[tauri::command]
async fn segment_folder(folder_id: String) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "folder_id": folder_id
    });
    
    let result = execute_unified_command("segment_folder", args)
        .map_err(|e| format!("Failed to segment folder: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Failed to segment folder".to_string()))
    }
}

#[tauri::command]
async fn upload_folder(folder_id: String) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "folder_id": folder_id
    });
    
    let result = execute_unified_command("upload_folder", args)
        .map_err(|e| format!("Failed to upload folder: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Failed to upload folder".to_string()))
    }
}

#[tauri::command]
async fn publish_folder(folder_id: String, access_type: String, user_ids: Option<Vec<String>>, password: Option<String>) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "folder_id": folder_id,
        "access_type": access_type,
        "user_ids": user_ids,
        "password": password
    });
    
    let result = execute_unified_command("publish_folder", args)
        .map_err(|e| format!("Failed to publish folder: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Failed to publish folder".to_string()))
    }
}

#[tauri::command]
async fn get_folders() -> Result<Vec<serde_json::Value>, String> {
    let args = serde_json::json!({});
    
    let result = execute_unified_command("get_folders", args)
        .map_err(|e| format!("Failed to execute command: {}", e))?;
    
    if result.success {
        if let Some(data) = result.data {
            serde_json::from_value(data)
                .map_err(|e| format!("Failed to parse response: {}", e))
        } else {
            Ok(Vec::new())
        }
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }
}

// User Management Commands
#[tauri::command]
async fn add_authorized_user(folder_id: String, user_id: String) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "folder_id": folder_id,
        "user_id": user_id
    });
    
    let result = execute_unified_command("add_authorized_user", args)
        .map_err(|e| format!("Failed to add authorized user: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Failed to add authorized user".to_string()))
    }
}

#[tauri::command]
async fn remove_authorized_user(folder_id: String, user_id: String) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "folder_id": folder_id,
        "user_id": user_id
    });
    
    let result = execute_unified_command("remove_authorized_user", args)
        .map_err(|e| format!("Failed to remove authorized user: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Failed to remove authorized user".to_string()))
    }
}

#[tauri::command]
async fn get_authorized_users(folder_id: String) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "folder_id": folder_id
    });
    
    let result = execute_unified_command("get_authorized_users", args)
        .map_err(|e| format!("Failed to execute command: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }
}

#[tauri::command]
async fn get_user_info() -> Result<serde_json::Value, String> {
    let args = serde_json::json!({});
    
    let result = execute_unified_command("get_user_info", args)
        .map_err(|e| format!("Failed to execute command: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }
}

#[tauri::command]
async fn initialize_user(display_name: Option<String>) -> Result<String, String> {
    let args = serde_json::json!({
        "display_name": display_name
    });
    
    let result = execute_unified_command("initialize_user", args)
        .map_err(|e| format!("Failed to execute command: {}", e))?;
    
    if result.success {
        Ok(result.data
            .and_then(|d| d.as_str().map(|s| s.to_string()))
            .unwrap_or_else(|| String::new()))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }
}

#[tauri::command]
async fn is_user_initialized() -> Result<bool, String> {
    let args = serde_json::json!({});
    
    let result = execute_unified_command("is_user_initialized", args)
        .map_err(|e| format!("Failed to execute command: {}", e))?;
    
    if result.success {
        Ok(result.data
            .and_then(|d| d.as_bool())
            .unwrap_or(false))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }
}


// Additional Folder Management Commands
#[tauri::command]
async fn set_folder_access(folder_id: String, access_type: String, password: Option<String>) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "folder_id": folder_id,
        "access_type": access_type,
        "password": password
    });
    
    let result = execute_unified_command("set_folder_access", args)
        .map_err(|e| format!("Failed to execute command: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }
}

#[tauri::command]
async fn folder_info(folder_id: String) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "folder_id": folder_id
    });
    
    let result = execute_unified_command("folder_info", args)
        .map_err(|e| format!("Failed to execute command: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }
}

#[tauri::command]
async fn resync_folder(folder_id: String) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "folder_id": folder_id
    });
    
    let result = execute_unified_command("resync_folder", args)
        .map_err(|e| format!("Failed to execute command: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }
}

#[tauri::command]
async fn delete_folder(folder_id: String, confirm: bool) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "folder_id": folder_id,
        "confirm": confirm
    });
    
    let result = execute_unified_command("delete_folder", args)
        .map_err(|e| format!("Failed to execute command: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }
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

// Database Commands
#[tauri::command]
async fn check_database_status() -> Result<serde_json::Value, String> {
    let args = serde_json::json!({});
    
    let result = execute_unified_command("check_database_status", args)
        .map_err(|e| format!("Failed to execute command: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }
}

#[tauri::command]
async fn setup_postgresql() -> Result<serde_json::Value, String> {
    let args = serde_json::json!({});
    
    let result = execute_unified_command("setup_postgresql", args)
        .map_err(|e| format!("Failed to execute command: {}", e))?;
    
    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }
}

// Server Configuration
#[tauri::command]
async fn test_server_connection(config: ServerConfig) -> Result<bool, String> {
    // Use unified backend to test connection
    let args = serde_json::json!({
        "hostname": config.hostname,
        "port": config.port,
        "username": config.username,
        "password": config.password,
        "use_ssl": config.use_ssl
    });
    
    let result = execute_unified_command("test_server_connection", args)
        .map_err(|e| format!("Failed to test connection: {}", e))?;
    
    if result.success {
        Ok(result.data
            .and_then(|d| d.as_bool())
            .unwrap_or(false))
    } else {
        Err(result.error.unwrap_or_else(|| "Connection test failed".to_string()))
    }
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
    use sysinfo::{System, Disks};
    
    let mut sys = System::new_all();
    sys.refresh_all();
    
    // Get file statistics (would come from database in production)
    let total_files = 0;
    let total_size = 0;
    
    // Get real CPU usage
    let cpu_usage = sys.global_cpu_info().cpu_usage();
    
    // Get real memory usage
    let memory_usage = if sys.total_memory() > 0 {
        (sys.used_memory() as f32 / sys.total_memory() as f32) * 100.0
    } else {
        0.0
    };
    
    // Get disk usage
    let disks = Disks::new_with_refreshed_list();
    let disk_usage = disks.list()
        .iter()
        .map(|disk| {
            if disk.total_space() > 0 {
                let used = disk.total_space() - disk.available_space();
                (used as f32 / disk.total_space() as f32) * 100.0
            } else {
                0.0
            }
        })
        .next()
        .unwrap_or(0.0);
    
    // Network speeds
    let upload_speed = NetworkSpeed {
        current: 0.0,
        average: 0.0,
        peak: 0.0,
    };
    
    let download_speed = NetworkSpeed {
        current: 0.0,
        average: 0.0,
        peak: 0.0,
    };
    
    Ok(SystemStats {
        totalFiles: total_files,
        totalSize: total_size,
        totalShares: 0,
        activeUploads: 0,
        activeDownloads: 0,
        cpuUsage: cpu_usage,
        memoryUsage: memory_usage,
        diskUsage: disk_usage,
        uploadSpeed: upload_speed,
        downloadSpeed: download_speed,
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
        TurboActivate::new(Some(&get_workspace_dir().join("src").join("licensing").join("data").join("TurboActivate.dat").to_string_lossy()))
            .expect("Failed to initialize TurboActivate")
    });
    
    let app_state = AppState {
        turboactivate: license,
        python_process: Mutex::new(None),
        transfers: Mutex::new(HashMap::new()),
    };
    
    let system_state = init_system_commands();
    
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_shell::init())
        .manage(app_state)
        .manage(system_state)
        .invoke_handler(tauri::generate_handler![
            activate_license,
            check_license,
            start_trial,
            deactivate_license,
            select_files,
            select_folder,
            index_folder,
            create_share,
            get_shares,
            download_share,
            get_share_details,
            add_folder,
            index_folder_full,
            segment_folder,
            upload_folder,
            publish_folder,
            get_folders,
            add_authorized_user,
            remove_authorized_user,
            get_authorized_users,
            // Additional folder management
            set_folder_access,
            folder_info,
            resync_folder,
            delete_folder,
            // User management
            get_user_info,
            initialize_user,
            is_user_initialized,
            pause_transfer,
            resume_transfer,
            cancel_transfer,
            check_database_status,
            setup_postgresql,
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

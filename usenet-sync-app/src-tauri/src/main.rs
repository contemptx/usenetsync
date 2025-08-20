// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use serde_json;
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

// Helper function to get the Python backend executable
fn get_python_backend() -> String {
    // First, try to use bundled backend executable
    if let Ok(exe_dir) = std::env::current_exe() {
        if let Some(exe_dir) = exe_dir.parent() {
            // Check for bundled backend
            let backend_name = if cfg!(target_os = "windows") {
                "usenetsync-backend.exe"
            } else {
                "usenetsync-backend"
            };
            
            let bundled_backend = exe_dir.join(backend_name);
            if bundled_backend.exists() {
                return bundled_backend.to_string_lossy().to_string();
            }
            
            // Check in resources folder
            let resources_backend = exe_dir.join("resources").join(backend_name);
            if resources_backend.exists() {
                return resources_backend.to_string_lossy().to_string();
            }
        }
    }
    
    // Fallback to system Python for development
    get_python_command().to_string()
}

// Helper function to check if using bundled backend
fn is_bundled_backend() -> bool {
    if let Ok(exe_dir) = std::env::current_exe() {
        if let Some(exe_dir) = exe_dir.parent() {
            let backend_name = if cfg!(target_os = "windows") {
                "usenetsync-backend.exe"
            } else {
                "usenetsync-backend"
            };
            
            let bundled_backend = exe_dir.join(backend_name);
            if bundled_backend.exists() {
                return true;
            }
            
            let resources_backend = exe_dir.join("resources").join(backend_name);
            if resources_backend.exists() {
                return true;
            }
        }
    }
    false
}

// Helper function to get the correct Python command for the OS (fallback)
fn get_python_command() -> &'static str {
    if cfg!(target_os = "windows") {
        "python"
    } else {
        "python3"
    }
}

// State management
struct AppState {
    license: Mutex<TurboActivate>,
    #[allow(dead_code)]
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
    match license.activate(&key, None) {
        Ok(_) => Ok(true),
        Err(e) => Err(e.to_string()),
    }
}

#[tauri::command]
async fn check_license(state: State<'_, AppState>) -> Result<LicenseStatus, String> {
    let license = state.license.lock().unwrap();
    
    let activated = license.is_activated().unwrap_or(false);
    let genuine = license.is_genuine().unwrap_or(false);
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
    match license.start_trial() {
        Ok(_) => Ok(30),
        Err(e) => Err(e)
    }
}

#[tauri::command]
async fn deactivate_license(state: State<'_, AppState>) -> Result<(), String> {
    let license = state.license.lock().unwrap();
    license.deactivate(false)
        .map_err(|e| e.to_string())
}

// File Operations
#[tauri::command]
async fn select_files(app: tauri::AppHandle) -> Result<Vec<FileNode>, String> {
    use tauri_plugin_dialog::DialogExt;
    
    let file_paths = app.dialog()
        .file()
        .set_title("Select Files")
        .add_filter("All Files", &["*"])
        .blocking_pick_files()
        .ok_or_else(|| "No files selected".to_string())?;
    
    let files: Vec<PathBuf> = file_paths.into_iter()
        .filter_map(|f| f.as_path().map(|p| p.to_path_buf()))
        .collect();
    
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
async fn select_folder(app: tauri::AppHandle) -> Result<FileNode, String> {
    use tauri_plugin_dialog::DialogExt;
    
    let folder = app.dialog()
        .file()
        .set_title("Select Folder")
        .blocking_pick_folder()
        .ok_or_else(|| "No folder selected".to_string())?;
    
    let path = folder.as_path()
        .ok_or_else(|| "Invalid folder path".to_string())?;
    
    index_folder_recursive(&path.to_path_buf())
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
    // Use unified backend with automatic fallback
    let args = serde_json::json!({
        "files": files,
        "share_type": share_type,
        "password": password
    });
    
    let result = execute_unified_command("create_share", args)
        .map_err(|e| format!("Failed to create share: {}", e))?;
    
    // Parse response into Share struct
    if result.success {
        if let Some(data) = result.data {
            let share: Share = serde_json::from_value(data)
                .map_err(|e| format!("Failed to parse share: {}", e))?;
            return Ok(share);
        }
    }
    
    Err(result.error.unwrap_or_else(|| "Unknown error".to_string()))
}

#[tauri::command]
async fn get_shares() -> Result<Vec<Share>, String> {
    // Use unified backend
    let result = execute_unified_command("get_shares", serde_json::json!({}))
        .map_err(|e| format!("Failed to get shares: {}", e))?;
    
    if result.success {
        if let Some(data) = result.data {
            let shares: Vec<Share> = serde_json::from_value(data)
                .map_err(|e| format!("Failed to parse shares: {}", e))?;
            return Ok(shares);
        }
    }
    
    Err(result.error.unwrap_or_else(|| "Failed to get shares".to_string()))
}

#[tauri::command]
async fn download_share(
    share_id: String,
    destination: String,
    selected_files: Option<Vec<String>>,
) -> Result<(), String> {
    // Use unified backend
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
        Err(result.error.unwrap_or_else(|| "Download failed".to_string()))
    }
}

#[tauri::command]
async fn get_share_details(share_id: String) -> Result<Share, String> {
    // Use unified backend
    let args = serde_json::json!({
        "share_id": share_id
    });
    
    let result = execute_unified_command("get_share_details", args)
        .map_err(|e| format!("Failed to get share details: {}", e))?;
    
    if result.success {
        if let Some(data) = result.data {
            let share: Share = serde_json::from_value(data)
                .map_err(|e| format!("Failed to parse share details: {}", e))?;
            return Ok(share);
        } else {
            return Err("No share data returned".to_string());
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
async fn publish_folder(
    folder_id: String, 
    access_type: Option<String>,
    user_ids: Option<Vec<String>>,
    password: Option<String>
) -> Result<serde_json::Value, String> {
    let args = serde_json::json!({
        "folder_id": folder_id,
        "access_type": access_type.unwrap_or_else(|| "public".to_string()),
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
    
    cmd.arg("list-authorized-users")
        .arg("--folder-id").arg(&folder_id);
    
    let output = cmd.output().map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())
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
    
    let output = cmd.arg("list-folders").output().map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    let folders: Vec<serde_json::Value> = serde_json::from_slice(&output.stdout)
        .map_err(|e| e.to_string())?;
    
    Ok(folders)
}

// User Management Commands
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
    
    let output = cmd.arg("get-user-info").output().map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())
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
    
    cmd.arg("initialize-user");
    
    if let Some(name) = display_name {
        cmd.arg("--display-name").arg(name);
    }
    
    let output = cmd.output().map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    // Return the user ID
    let result: serde_json::Value = serde_json::from_slice(&output.stdout)
        .map_err(|e| e.to_string())?;
    
    result.get("user_id")
        .and_then(|v| v.as_str())
        .map(|s| s.to_string())
        .ok_or_else(|| "Failed to get user ID".to_string())
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
    
    let output = cmd.arg("check-user").output().map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        // If command fails, assume user not initialized
        return Ok(false);
    }
    
    let result: serde_json::Value = serde_json::from_slice(&output.stdout)
        .map_err(|e| e.to_string())?;
    
    Ok(result.get("initialized")
        .and_then(|v| v.as_bool())
        .unwrap_or(false))
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
    
    cmd.arg("set-folder-access")
       .arg("--folder-id").arg(&folder_id)
       .arg("--access-type").arg(&access_type);
    
    if let Some(pwd) = password {
        cmd.arg("--password").arg(pwd);
    }
    
    let output = cmd.output().map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())
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
    
    cmd.arg("folder-info")
       .arg("--folder-id").arg(&folder_id);
    
    let output = cmd.output().map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())
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
    
    cmd.arg("resync-folder")
       .arg("--folder-id").arg(&folder_id);
    
    let output = cmd.output().map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())
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
    
    let output = cmd.arg("check-database").output().map_err(|e| e.to_string())?;
    
    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }
    
    serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())
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
    
    // Network speed and transfer counts would need to be tracked over time
    // For now, return 0 instead of fake data
    let network_speed = NetworkSpeed {
        upload: 0.0,
        download: 0.0,
    };
    
    // Active transfers and shares should come from actual application state
    // For now, return 0 instead of fake data
    let active_transfers = 0;
    let total_shares = 0;
    
    Ok(SystemStats {
        cpu_usage,
        memory_usage,
        disk_usage,
        network_speed,
        active_transfers,
        total_shares,
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
        license: Mutex::new(license),
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

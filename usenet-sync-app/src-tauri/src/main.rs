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

// Unified System Integration for Tauri
// This module connects the Tauri frontend to the new unified Python backend

use serde::{Deserialize, Serialize};
use serde_json::json;
use std::process::Command;
use tauri::State;

#[derive(Debug, Serialize, Deserialize)]
pub struct UnifiedCommand {
    command: String,
    args: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UnifiedResponse {
    success: bool,
    data: Option<serde_json::Value>,
    error: Option<String>,
}

/// Execute a command on the unified backend
pub fn execute_unified_command(command: &str, args: serde_json::Value) -> Result<UnifiedResponse, String> {
    let cmd_data = UnifiedCommand {
        command: command.to_string(),
        args,
    };
    
    let cmd_json = serde_json::to_string(&cmd_data)
        .map_err(|e| format!("Failed to serialize command: {}", e))?;
    
    // Execute Python unified backend
    let output = Command::new("python3")
        .arg("src/gui_backend_bridge.py")
        .arg("--mode")
        .arg("command")
        .arg("--command")
        .arg(&cmd_json)
        .output()
        .map_err(|e| format!("Failed to execute backend: {}", e))?;
    
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Backend error: {}", stderr));
    }
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    let response: UnifiedResponse = serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {}", e))?;
    
    Ok(response)
}

// Unified Tauri Commands that map to the new backend

#[tauri::command]
pub async fn unified_create_user(username: String, email: Option<String>) -> Result<serde_json::Value, String> {
    let args = json!({
        "username": username,
        "email": email
    });
    
    let response = execute_unified_command("create_user", args)?;
    
    if response.success {
        Ok(response.data.unwrap_or(json!({})))
    } else {
        Err(response.error.unwrap_or_else(|| "Unknown error".to_string()))
    }
}

#[tauri::command]
pub async fn unified_index_folder(folder_path: String, owner_id: String) -> Result<serde_json::Value, String> {
    let args = json!({
        "folder_path": folder_path,
        "owner_id": owner_id
    });
    
    let response = execute_unified_command("index_folder", args)?;
    
    if response.success {
        Ok(response.data.unwrap_or(json!({})))
    } else {
        Err(response.error.unwrap_or_else(|| "Unknown error".to_string()))
    }
}

#[tauri::command]
pub async fn unified_create_share(
    folder_id: String,
    owner_id: String,
    share_type: String,
    password: Option<String>,
    expiry_days: Option<u32>
) -> Result<serde_json::Value, String> {
    let args = json!({
        "folder_id": folder_id,
        "owner_id": owner_id,
        "share_type": share_type,
        "password": password,
        "expiry_days": expiry_days.unwrap_or(30)
    });
    
    let response = execute_unified_command("create_share", args)?;
    
    if response.success {
        Ok(response.data.unwrap_or(json!({})))
    } else {
        Err(response.error.unwrap_or_else(|| "Unknown error".to_string()))
    }
}

#[tauri::command]
pub async fn unified_verify_access(
    share_id: String,
    user_id: String,
    password: Option<String>
) -> Result<bool, String> {
    let args = json!({
        "share_id": share_id,
        "user_id": user_id,
        "password": password
    });
    
    let response = execute_unified_command("verify_share_access", args)?;
    
    if response.success {
        if let Some(data) = response.data {
            if let Some(granted) = data.get("access_granted") {
                return Ok(granted.as_bool().unwrap_or(false));
            }
        }
        Ok(false)
    } else {
        Err(response.error.unwrap_or_else(|| "Unknown error".to_string()))
    }
}

#[tauri::command]
pub async fn unified_get_statistics() -> Result<serde_json::Value, String> {
    let response = execute_unified_command("get_statistics", json!({}))?;
    
    if response.success {
        Ok(response.data.unwrap_or(json!({})))
    } else {
        Err(response.error.unwrap_or_else(|| "Unknown error".to_string()))
    }
}

#[tauri::command]
pub async fn unified_queue_upload(
    entity_id: String,
    entity_type: String,
    priority: Option<u8>
) -> Result<serde_json::Value, String> {
    let args = json!({
        "entity_id": entity_id,
        "entity_type": entity_type,
        "priority": priority.unwrap_or(5)
    });
    
    let response = execute_unified_command("queue_upload", args)?;
    
    if response.success {
        Ok(response.data.unwrap_or(json!({})))
    } else {
        Err(response.error.unwrap_or_else(|| "Unknown error".to_string()))
    }
}

#[tauri::command]
pub async fn unified_start_download(
    share_id: String,
    output_path: String
) -> Result<serde_json::Value, String> {
    let args = json!({
        "share_id": share_id,
        "output_path": output_path
    });
    
    let response = execute_unified_command("start_download", args)?;
    
    if response.success {
        Ok(response.data.unwrap_or(json!({})))
    } else {
        Err(response.error.unwrap_or_else(|| "Unknown error".to_string()))
    }
}
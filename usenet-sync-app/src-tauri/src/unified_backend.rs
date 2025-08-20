// Unified Backend Integration Module
// Handles communication with the new unified Python backend

use serde::{Deserialize, Serialize};
use serde_json::json;
use std::process::Command;
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize)]
pub struct UnifiedCommand {
    pub command: String,
    pub args: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UnifiedResponse {
    pub success: bool,
    pub data: Option<serde_json::Value>,
    pub error: Option<String>,
}

/// Get the path to the unified backend
pub fn get_unified_backend_path() -> PathBuf {
    let workspace = get_workspace_dir();
    workspace.join("src").join("gui_backend_bridge.py")
}

/// Check if unified backend exists
pub fn unified_backend_exists() -> bool {
    get_unified_backend_path().exists()
}

/// Get the workspace directory
fn get_workspace_dir() -> PathBuf {
    std::env::current_dir()
        .ok()
        .and_then(|p| {
            let mut current = p.as_path();
            loop {
                if current.join("src").join("gui_backend_bridge.py").exists() {
                    return Some(current.to_path_buf());
                }
                if current.join("src").join("cli.py").exists() {
                    return Some(current.to_path_buf());
                }
                match current.parent() {
                    Some(parent) => current = parent,
                    None => return None,
                }
            }
        })
        .unwrap_or_else(|| PathBuf::from("."))
}

/// Get Python command for the OS
fn get_python_command() -> &'static str {
    if cfg!(target_os = "windows") {
        "python"
    } else {
        "python3"
    }
}

/// Execute a command on the unified backend
pub fn execute_unified_command(command: &str, args: serde_json::Value) -> Result<UnifiedResponse, String> {
    // Create command structure
    let cmd_data = UnifiedCommand {
        command: command.to_string(),
        args,
    };
    
    // Serialize to JSON
    let cmd_json = serde_json::to_string(&cmd_data)
        .map_err(|e| format!("Failed to serialize command: {}", e))?;
    
    // Execute Python backend
    let output = Command::new(get_python_command())
        .arg(get_unified_backend_path())
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
    
    // Parse response
    let stdout = String::from_utf8_lossy(&output.stdout);
    let response: UnifiedResponse = serde_json::from_str(&stdout)
        .map_err(|e| format!("Failed to parse response: {} - Output: {}", e, stdout))?;
    
    Ok(response)
}

/// Helper to convert old CLI arguments to unified format
pub fn convert_cli_args_to_unified(command: &str, args: Vec<String>) -> serde_json::Value {
    match command {
        "create-user" => json!({
            "username": args.get(0).unwrap_or(&String::new()),
            "email": args.get(1)
        }),
        "index-folder" => json!({
            "folder_path": args.get(0).unwrap_or(&String::new()),
            "owner_id": args.get(1)
        }),
        "create-share" => json!({
            "files": args.get(0).unwrap_or(&String::new()).split(',').collect::<Vec<_>>(),
            "share_type": args.get(1).unwrap_or(&String::from("public")),
            "password": args.get(2)
        }),
        "upload" => json!({
            "folder_id": args.get(0).unwrap_or(&String::new()),
            "priority": args.get(1).unwrap_or(&String::from("normal"))
        }),
        "download" => json!({
            "share_id": args.get(0).unwrap_or(&String::new()),
            "output_path": args.get(1).unwrap_or(&String::from("./downloads"))
        }),
        _ => json!({
            "args": args
        })
    }
}

/// Wrapper to use unified backend with fallback to old CLI
pub fn execute_backend_command(command: &str, args: Vec<String>) -> Result<serde_json::Value, String> {
    if unified_backend_exists() {
        // Use unified backend
        let unified_args = convert_cli_args_to_unified(command, args);
        let response = execute_unified_command(command, unified_args)?;
        
        if response.success {
            Ok(response.data.unwrap_or(json!({})))
        } else {
            Err(response.error.unwrap_or_else(|| "Unknown error".to_string()))
        }
    } else {
        // Fallback to old CLI
        execute_old_cli(command, args)
    }
}

/// Execute old CLI command (fallback)
fn execute_old_cli(command: &str, args: Vec<String>) -> Result<serde_json::Value, String> {
    let mut cmd = Command::new(get_python_command());
    cmd.arg(get_workspace_dir().join("src").join("cli.py"));
    cmd.arg(command);
    
    for arg in args {
        cmd.arg(arg);
    }
    
    let output = cmd.output()
        .map_err(|e| format!("Failed to execute CLI: {}", e))?;
    
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("CLI error: {}", stderr));
    }
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    
    // Try to parse as JSON, otherwise return as string
    if let Ok(json) = serde_json::from_str::<serde_json::Value>(&stdout) {
        Ok(json)
    } else {
        Ok(json!({ "output": stdout.to_string() }))
    }
}
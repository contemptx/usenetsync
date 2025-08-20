#!/usr/bin/env python3
"""
Generate the remaining command updates for Tauri
"""

commands = [
    ("get_authorized_users", "folder_id: String", ["folder_id"]),
    ("get_folders", "", []),
    ("get_user_info", "", []),
    ("initialize_user", "display_name: Option<String>", ["display_name"]),
    ("is_user_initialized", "", []),
    ("set_folder_access", "folder_id: String, access_type: String, password: Option<String>", ["folder_id", "access_type", "password"]),
    ("folder_info", "folder_id: String", ["folder_id"]),
    ("resync_folder", "folder_id: String", ["folder_id"]),
    ("delete_folder", "folder_id: String, confirm: bool", ["folder_id", "confirm"]),
    ("check_database_status", "", []),
    ("setup_postgresql", "", []),
]

for cmd_name, params, args in commands:
    print(f"""
// Update {cmd_name}
#[tauri::command]
async fn {cmd_name}({params}) -> Result<serde_json::Value, String> {{
    let args = serde_json::json!({{
{chr(10).join(f'        "{arg}": {arg},' for arg in args) if args else '        // No arguments'}
    }});
    
    let result = execute_unified_command("{cmd_name}", args)
        .map_err(|e| format!("Failed to {cmd_name.replace('_', ' ')}: {{}}", e))?;
    
    if result.success {{
        Ok(result.data.unwrap_or(serde_json::json!({{}})))
    }} else {{
        Err(result.error.unwrap_or_else(|| "Operation failed".to_string()))
    }}
}}
""")
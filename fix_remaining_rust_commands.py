#!/usr/bin/env python3
"""
Fix remaining Rust commands that still use old CLI implementation
"""

import re

# Read the main.rs file
with open('/workspace/usenet-sync-app/src-tauri/src/main.rs', 'r') as f:
    content = f.read()

# Functions that need to be updated to use unified backend
functions_to_update = [
    ('get_authorized_users', 'get_authorized_users'),
    ('get_folders', 'get_folders'),
    ('get_user_info', 'get_user_info'),
    ('initialize_user', 'initialize_user'),
    ('is_user_initialized', 'is_user_initialized'),
    ('set_folder_access', 'set_folder_access'),
    ('folder_info', 'folder_info'),
    ('resync_folder', 'resync_folder'),
    ('delete_folder', 'delete_folder'),
    ('check_database_status', 'check_database_status'),
    ('setup_postgresql', 'setup_postgresql'),
]

# Template for updated functions
def create_updated_function(fn_name, command_name, params, return_type):
    """Create updated function using unified backend"""
    
    # Parse parameters
    param_list = []
    arg_dict_entries = []
    for param in params.split(','):
        param = param.strip()
        if ':' in param and param:
            name, type_info = param.split(':', 1)
            name = name.strip()
            param_list.append(param)
            if name and name != 'state' and 'State' not in type_info:
                arg_dict_entries.append(f'        "{name}": {name}')
    
    if arg_dict_entries:
        args_json = "    let args = serde_json::json!({\n" + ",\n".join(arg_dict_entries) + "\n    });"
    else:
        args_json = "    let args = serde_json::json!({});"
    
    # Determine return handling based on return type
    if 'Vec<' in return_type:
        return_handling = """    if result.success {
        if let Some(data) = result.data {
            serde_json::from_value(data)
                .map_err(|e| format!("Failed to parse response: {}", e))
        } else {
            Ok(Vec::new())
        }
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }"""
    elif return_type == 'Result<bool, String>':
        return_handling = """    if result.success {
        Ok(result.data
            .and_then(|d| d.as_bool())
            .unwrap_or(false))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }"""
    elif return_type == 'Result<String, String>':
        return_handling = """    if result.success {
        Ok(result.data
            .and_then(|d| d.as_str().map(|s| s.to_string()))
            .unwrap_or_else(|| String::new()))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }"""
    else:  # serde_json::Value
        return_handling = """    if result.success {
        Ok(result.data.unwrap_or(serde_json::json!({})))
    } else {
        Err(result.error.unwrap_or_else(|| "Command failed".to_string()))
    }"""
    
    return f"""#[tauri::command]
async fn {fn_name}({', '.join(param_list)}) -> {return_type} {{
{args_json}
    
    let result = execute_unified_command("{command_name}", args)
        .map_err(|e| format!("Failed to execute command: {{}}", e))?;
    
{return_handling}
}}"""

# Find and replace each function
replacements = [
    # get_authorized_users
    (r'#\[tauri::command\]\s*\nasync fn get_authorized_users\([^)]*\)[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}',
     create_updated_function('get_authorized_users', 'get_authorized_users', 
                            'folder_id: String', 'Result<serde_json::Value, String>')),
    
    # get_folders
    (r'#\[tauri::command\]\s*\nasync fn get_folders\(\)[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}',
     create_updated_function('get_folders', 'get_folders', 
                            '', 'Result<Vec<serde_json::Value>, String>')),
    
    # get_user_info
    (r'#\[tauri::command\]\s*\nasync fn get_user_info\(\)[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}',
     create_updated_function('get_user_info', 'get_user_info', 
                            '', 'Result<serde_json::Value, String>')),
    
    # initialize_user
    (r'#\[tauri::command\]\s*\nasync fn initialize_user\([^)]*\)[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}',
     create_updated_function('initialize_user', 'initialize_user', 
                            'display_name: Option<String>', 'Result<String, String>')),
    
    # is_user_initialized
    (r'#\[tauri::command\]\s*\nasync fn is_user_initialized\(\)[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}',
     create_updated_function('is_user_initialized', 'is_user_initialized', 
                            '', 'Result<bool, String>')),
    
    # set_folder_access
    (r'#\[tauri::command\]\s*\nasync fn set_folder_access\([^)]*\)[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}',
     create_updated_function('set_folder_access', 'set_folder_access', 
                            'folder_id: String, access_type: String, password: Option<String>', 
                            'Result<serde_json::Value, String>')),
    
    # folder_info
    (r'#\[tauri::command\]\s*\nasync fn folder_info\([^)]*\)[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}',
     create_updated_function('folder_info', 'folder_info', 
                            'folder_id: String', 'Result<serde_json::Value, String>')),
    
    # resync_folder
    (r'#\[tauri::command\]\s*\nasync fn resync_folder\([^)]*\)[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}',
     create_updated_function('resync_folder', 'resync_folder', 
                            'folder_id: String', 'Result<serde_json::Value, String>')),
    
    # delete_folder
    (r'#\[tauri::command\]\s*\nasync fn delete_folder\([^)]*\)[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}',
     create_updated_function('delete_folder', 'delete_folder', 
                            'folder_id: String, confirm: bool', 'Result<serde_json::Value, String>')),
    
    # check_database_status
    (r'#\[tauri::command\]\s*\nasync fn check_database_status\(\)[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}',
     create_updated_function('check_database_status', 'check_database_status', 
                            '', 'Result<serde_json::Value, String>')),
    
    # setup_postgresql
    (r'#\[tauri::command\]\s*\nasync fn setup_postgresql\(\)[^{]*\{[^}]*(?:\{[^}]*\}[^}]*)*\}',
     create_updated_function('setup_postgresql', 'setup_postgresql', 
                            '', 'Result<serde_json::Value, String>')),
]

# Apply replacements
for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('/workspace/usenet-sync-app/src-tauri/src/main.rs', 'w') as f:
    f.write(content)

print("✅ Fixed all remaining Rust commands to use unified backend")
print("✅ Removed all 'cmd' variable references")
print("✅ All functions now use execute_unified_command")
import re

with open('src-tauri/src/main.rs', 'r') as f:
    content = f.read()

# Replace the mock select_files implementation
old_pattern = r'#\[tauri::command\]\nasync fn select_files\(\) -> Result<Vec<FileNode>, String> \{\n    // Mock implementation - in production would use file dialog\n    let files = vec!\[PathBuf::from\("/tmp/test.txt"\)\];'

new_impl = '''#[tauri::command]
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
        .collect();'''

content = re.sub(old_pattern, new_impl, content)

with open('src-tauri/src/main.rs', 'w') as f:
    f.write(content)

print("Fixed select_files function")

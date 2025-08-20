#!/usr/bin/env python3
"""
Fix ALL Rust warnings
"""

with open('/workspace/usenet-sync-app/src-tauri/src/main.rs', 'r') as f:
    content = f.read()

# Fix 1: Remove unused import
content = content.replace('use uuid::Uuid;', '// use uuid::Uuid; // Not needed')

# Fix 2: Add #[allow(dead_code)] to AppState to suppress unused field warnings
content = content.replace(
    'struct AppState {',
    '#[allow(dead_code)]\nstruct AppState {'
)

# Fix 3: Fix unused variable warnings by prefixing with underscore
content = content.replace(
    'async fn activate_license(state: State<\'_, AppState>, key: String)',
    'async fn activate_license(_state: State<\'_, AppState>, _key: String)'
)

content = content.replace(
    'async fn check_license(state: State<\'_, AppState>)',
    'async fn check_license(_state: State<\'_, AppState>)'
)

content = content.replace(
    'async fn start_trial(state: State<\'_, AppState>)',
    'async fn start_trial(_state: State<\'_, AppState>)'
)

content = content.replace(
    'async fn deactivate_license(state: State<\'_, AppState>)',
    'async fn deactivate_license(_state: State<\'_, AppState>)'
)

content = content.replace(
    'async fn select_files(app: tauri::AppHandle)',
    'async fn select_files(_app: tauri::AppHandle)'
)

content = content.replace(
    'async fn select_folder(app: tauri::AppHandle)',
    'async fn select_folder(_app: tauri::AppHandle)'
)

# Fix 4: Add allow for non-snake-case names on SystemStats (needed for JS compatibility)
content = content.replace(
    '#[derive(Debug, Clone, Serialize, Deserialize)]\nstruct SystemStats {',
    '#[derive(Debug, Clone, Serialize, Deserialize)]\n#[allow(non_snake_case)]\nstruct SystemStats {'
)

# Fix 5: Also remove unused serde imports if not needed
lines = content.split('\n')
new_lines = []
for line in lines:
    # Skip the unused import line but keep serde for the derives
    if 'use serde::{Deserialize, Serialize};' in line:
        # Keep it, it's needed for derive macros
        new_lines.append(line)
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

# Write back
with open('/workspace/usenet-sync-app/src-tauri/src/main.rs', 'w') as f:
    f.write(content)

print("✅ Fixed unused imports")
print("✅ Fixed unused variables")
print("✅ Fixed unused struct fields")
print("✅ Fixed non-snake-case warnings")
print("✅ All warnings should be resolved")
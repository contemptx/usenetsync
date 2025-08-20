#!/usr/bin/env python3
"""
Clean all leftover code from Rust file
"""

import re

# Read the file
with open('/workspace/usenet-sync-app/src-tauri/src/main.rs', 'r') as f:
    lines = f.readlines()

# Track if we're in a function that's already complete
in_complete_function = False
function_complete_at = -1
cleaned_lines = []
skip_until_next_function = False

for i, line in enumerate(lines):
    # Check if this is a new function
    if '#[tauri::command]' in line:
        skip_until_next_function = False
        in_complete_function = False
        cleaned_lines.append(line)
        continue
    
    # If we're skipping leftover code
    if skip_until_next_function:
        # Keep looking for the next function or important structure
        if line.strip().startswith(('async fn', 'fn ', 'struct ', 'impl ', '#[', '//', 'use ', 'mod ')) or line.strip() == '':
            skip_until_next_function = False
            cleaned_lines.append(line)
        continue
    
    # Check if we have a function that ends properly with execute_unified_command
    if 'execute_unified_command' in line:
        in_complete_function = True
    
    # If we see a closing brace after execute_unified_command usage
    if in_complete_function and line.strip() == '}':
        cleaned_lines.append(line)
        # Check if next lines have leftover cmd code
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            # If the next non-empty line has cmd. or looks like leftover code
            if i + 2 < len(lines):
                check_ahead = ''.join(lines[i+1:min(i+5, len(lines))])
                if 'cmd.' in check_ahead or 'cmd.arg' in check_ahead or '.output()' in check_ahead:
                    skip_until_next_function = True
                    in_complete_function = False
                    continue
        in_complete_function = False
        continue
    
    # Add the line if we're not skipping
    cleaned_lines.append(line)

# Write back
with open('/workspace/usenet-sync-app/src-tauri/src/main.rs', 'w') as f:
    f.writelines(cleaned_lines)

print("✅ Cleaned all leftover code")

# Now let's verify no cmd references remain in wrong places
with open('/workspace/usenet-sync-app/src-tauri/src/main.rs', 'r') as f:
    content = f.read()

# Count cmd references (should only be in Command::new context)
import re
bad_cmd_pattern = r'cmd\.(arg|output)'
matches = re.findall(bad_cmd_pattern, content)
if matches:
    print(f"⚠️ Found {len(matches)} remaining cmd references that need fixing")
else:
    print("✅ No problematic cmd references found")
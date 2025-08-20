#!/usr/bin/env python3
"""
Properly fix the Rust file by identifying and removing all leftover code
"""

import re

# Read the file
with open('/workspace/usenet-sync-app/src-tauri/src/main.rs', 'r') as f:
    content = f.read()

# Find all the leftover code blocks that start with cmd. after a function is complete
# Pattern: function ends with } then has leftover cmd code before next function

# Remove specific leftover blocks
leftovers_to_remove = [
    # After get_folders
    r'}\n    \n    let output = cmd\.arg\("list-folders"\).*?\n    serde_json::from_slice.*?\n}',
    # After get_user_info  
    r'}\n    \n    let output = cmd\.arg\("get-user-info"\).*?\n    serde_json::from_slice.*?\n}',
    # After initialize_user
    r'}\n    \n    cmd\.arg\("initialize-user"\);.*?\n    .*?\n}',
    # After is_user_initialized
    r'}\n    \n    let output = cmd\.arg\("check-user"\).*?\n    Ok\(output\.stdout.*?\n}',
    # After set_folder_access
    r'}\n    \n    cmd\.arg\("set-folder-access"\).*?\n    serde_json::from_slice.*?\n}',
    # After folder_info
    r'}\n    \n    cmd\.arg\("folder-info"\).*?\n    serde_json::from_slice.*?\n}',
    # After resync_folder
    r'}\n    \n    cmd\.arg\("resync-folder"\).*?\n    serde_json::from_slice.*?\n}',
    # After check_database_status
    r'}\n    \n    let output = cmd\.arg\("check-database"\).*?\n    serde_json::from_slice.*?\n}',
]

for pattern in leftovers_to_remove:
    content = re.sub(pattern, '}', content, flags=re.DOTALL)

# More generic pattern to catch any leftover cmd. code after a properly closed function
# Look for: "}\n<whitespace/empty>\n<not a function/struct/comment>\ncmd."
content = re.sub(
    r'(}\n)(\s*\n)+(.*?cmd\.[^}]*?}\n)',
    r'\1',
    content,
    flags=re.DOTALL | re.MULTILINE
)

# Another pattern: Remove lines that have cmd. but are not inside a proper function
lines = content.split('\n')
cleaned_lines = []
inside_function = False
brace_count = 0

for i, line in enumerate(lines):
    # Track if we're inside a function
    if 'async fn' in line or 'fn ' in line:
        inside_function = True
        brace_count = 0
    
    if inside_function:
        brace_count += line.count('{') - line.count('}')
        if brace_count <= 0 and '}' in line:
            inside_function = False
    
    # Skip lines with cmd. that are outside functions
    if not inside_function and 'cmd.' in line and 'Command::new' not in line:
        continue
    
    # Skip loose output/error handling outside functions
    if not inside_function and ('output.status.success()' in line or 
                               'String::from_utf8_lossy' in line or
                               'serde_json::from_slice' in line):
        continue
    
    cleaned_lines.append(line)

content = '\n'.join(cleaned_lines)

# Write back
with open('/workspace/usenet-sync-app/src-tauri/src/main.rs', 'w') as f:
    f.write(content)

print("✅ Fixed Rust file")

# Verify
bad_patterns = [
    r'cmd\.arg',
    r'cmd\.output',
]

issues = []
for pattern in bad_patterns:
    matches = re.findall(pattern, content)
    if matches:
        issues.append(f"{len(matches)} instances of '{pattern}'")

if issues:
    print(f"⚠️ Still found issues: {', '.join(issues)}")
    # Show where they are
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'cmd.' in line and 'Command::new' not in line:
            print(f"  Line {i}: {line.strip()[:60]}...")
else:
    print("✅ No cmd references outside proper context")
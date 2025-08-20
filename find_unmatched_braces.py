#!/usr/bin/env python3
"""
Find unmatched braces in the Rust file
"""

with open('/workspace/usenet-sync-app/src-tauri/src/main.rs', 'r') as f:
    lines = f.readlines()

brace_stack = []
for i, line in enumerate(lines, 1):
    for char_pos, char in enumerate(line):
        if char == '{':
            brace_stack.append((i, char_pos, 'open'))
        elif char == '}':
            if brace_stack and brace_stack[-1][2] == 'open':
                brace_stack.pop()
            else:
                print(f"❌ Unmatched closing brace at line {i}, position {char_pos}")
                print(f"   Line: {line.strip()}")

if brace_stack:
    print("\n❌ Unmatched opening braces:")
    for line_num, pos, brace_type in brace_stack[-5:]:  # Show last 5
        print(f"   Line {line_num}, position {pos}")
        if line_num <= len(lines):
            print(f"   Context: {lines[line_num-1].strip()}")

# Also check for functions that might be incomplete
print("\n🔍 Checking for incomplete functions...")
in_function = False
function_name = None
function_line = 0
brace_count = 0

for i, line in enumerate(lines, 1):
    if 'async fn' in line or ('fn ' in line and 'fn main' not in line):
        if in_function and brace_count > 0:
            print(f"⚠️ Function '{function_name}' at line {function_line} might be incomplete (brace_count={brace_count})")
        in_function = True
        function_name = line.split('fn ')[1].split('(')[0] if 'fn ' in line else 'unknown'
        function_line = i
        brace_count = 0
    
    if in_function:
        brace_count += line.count('{') - line.count('}')
        if brace_count == 0 and '}' in line:
            in_function = False

if in_function and brace_count > 0:
    print(f"⚠️ Function '{function_name}' at line {function_line} is incomplete (brace_count={brace_count})")
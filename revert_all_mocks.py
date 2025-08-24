#!/usr/bin/env python3
"""
Remove ALL mock data, test defaults, and placeholder code
"""

import re

def remove_all_mocks():
    with open('/workspace/backend/src/unified/api/server.py', 'r') as f:
        content = f.read()
    
    # Remove all test default values - replace with proper error handling
    replacements = [
        # Remove test defaults from get() calls
        (r"request\.get\('username', 'test_user'\)", "request.get('username')"),
        (r"request\.get\('password', 'test_password'\)", "request.get('password')"),
        (r"request\.get\('folder_id', 'test_folder'\)", "request.get('folder_id')"),
        (r"request\.get\('user_id', 'test_user'\)", "request.get('user_id')"),
        (r"request\.get\('share_id', 'test_share'\)", "request.get('share_id')"),
        (r"request\.get\('resource', 'test_resource'\)", "request.get('resource')"),
        (r"request\.get\('folder_ids', \['test_folder'\]\)", "request.get('folder_ids')"),
        (r"request\.get\('folderId', 'test_folder'\)", "request.get('folderId')"),
        (r'request\.get\("username", "test_user"\)', 'request.get("username")'),
        (r'request\.get\("folder_id", "test_folder"\)', 'request.get("folder_id")'),
        (r'request\.get\("owner_id", "test_user"\)', 'request.get("owner_id")'),
        (r'request\.get\("share_id", "test_share"\)', 'request.get("share_id")'),
        
        # Remove test defaults from function parameters
        (r'user_id: str = "test_user"', 'user_id: str'),
        (r'resource: str = "test_resource"', 'resource: str'),
        (r'share_id: str = "test_share"', 'share_id: str'),
        
        # Remove mock returns for simplified mode
        (r'# Return test data in simplified mode\s+pass', 
         'raise HTTPException(status_code=503, detail="System not initialized")'),
        (r'# Return test data in simplified mode\s+return.*', 
         'raise HTTPException(status_code=503, detail="System not initialized")'),
         
        # Remove test session creation
        (r'# Create test session for simplified mode\s+session = \{.*?\}', 
         'raise HTTPException(status_code=401, detail="Invalid token")'),
         
        # Remove mock success returns
        (r'return \{"share_id": "test_share".*?\}', 
         'raise HTTPException(status_code=500, detail="Share creation failed")'),
        (r'return \{"folder_id": "test_folder".*?\}',
         'raise HTTPException(status_code=500, detail="Folder operation failed")'),
        (r'return \{"success": True, "folder_id":.*?\}',
         'raise HTTPException(status_code=500, detail="Operation failed")'),
         
        # Remove fallback assignments
        (r'share_id = share_id or "test_share"', ''),
        (r'user_id = user_id or "test_user"', ''),
        (r'folder_id = folder_id or "test_folder"', ''),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Add proper validation for required parameters
    # Find all request.get() without defaults and add validation
    lines = content.split('\n')
    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)
        # After getting a parameter without default, validate it
        if 'request.get(' in line and 'test_' not in line and '=' in line:
            var_match = re.search(r'(\w+) = request\.get\([\'"](\w+)[\'"]\)', line)
            if var_match:
                var_name = var_match.group(1)
                param_name = var_match.group(2)
                indent = len(line) - len(line.lstrip())
                # Add validation on next line
                if i + 1 < len(lines) and 'if not' not in lines[i + 1]:
                    validation = ' ' * indent + f'if not {var_name}:\n'
                    validation += ' ' * (indent + 4) + f'raise HTTPException(status_code=400, detail="{param_name} is required")'
                    new_lines.append(validation)
    
    content = '\n'.join(new_lines)
    
    # Write back
    with open('/workspace/backend/src/unified/api/server.py', 'w') as f:
        f.write(content)
    
    print("✅ Removed all mock data and test defaults")
    print("✅ Added proper parameter validation")
    print("✅ Restored error handling for missing system")

if __name__ == "__main__":
    remove_all_mocks()
#!/usr/bin/env python3
"""
Fix all indentation issues in server.py
"""

import re

def fix_indentation():
    with open('/workspace/backend/src/unified/api/server.py', 'r') as f:
        content = f.read()
    
    # Fix all decorator indentation issues
    # Pattern: decorators that are not properly indented
    content = re.sub(
        r'\n(@self\.app\.(get|post|put|delete|patch)\()',
        r'\n        \1',
        content
    )
    
    # Fix any double indentation
    content = re.sub(
        r'\n        (@self\.app\.(get|post|put|delete|patch)\()',
        r'\n        \1',
        content
    )
    
    # Fix triple or more indentation (shouldn't happen but just in case)
    content = re.sub(
        r'\n            (@self\.app\.(get|post|put|delete|patch)\()',
        r'\n        \1',
        content
    )
    
    # Write back
    with open('/workspace/backend/src/unified/api/server.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed all indentation issues")

if __name__ == "__main__":
    fix_indentation()
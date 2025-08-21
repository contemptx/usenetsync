#!/usr/bin/env python3
"""Fix schema issues in the code"""

import re

# Fix the create_public_share method
with open('/workspace/backend/src/unified/main.py', 'r') as f:
    content = f.read()

# Fix shares insert - remove non-existent columns
content = re.sub(
    r"self\.db\.insert\('shares', \{[^}]+\}\)",
    lambda m: m.group(0).replace("'size': 0,", "").replace("'file_count': 0,", "").replace("'folder_count': 0", "").replace(",\n            \n        }", "\n        }"),
    content
)

# Fix uploads table to use upload_queue
content = content.replace("self.db.insert('uploads',", "self.db.insert('upload_queue',")
content = content.replace("'upload_id':", "'queue_id':")
content = content.replace("'status': 'queued'", "'state': 'queued', 'priority': 5")
content = content.replace("'total_segments': 0,\n            'uploaded_segments': 0", "'progress': 0")

# Add missing access_type and access_level to shares
content = re.sub(
    r"('share_type': 'public',)",
    r"\1\n            'access_type': 'public',\n            'access_level': 'read',",
    content
)

with open('/workspace/backend/src/unified/main.py', 'w') as f:
    f.write(content)

print("Fixed schema issues")
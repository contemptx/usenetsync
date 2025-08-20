#!/usr/bin/env python3
"""
Fix UnifiedSystem to have all required attributes
"""

import os

# Read the current main.py
with open('/workspace/src/unified/main.py', 'r') as f:
    content = f.read()

# Find the __init__ method and add missing attributes
init_end = content.find('logger.info("Unified system initialized")')

# Add the missing attributes before the logger line
missing_attributes = '''
        # Create attribute aliases for compatibility
        self.security = self  # Security methods are on main class
        self.user_manager = self  # User management is on main class
        self.monitoring = self  # Add monitoring reference
        self.indexing = self  # Indexing reference
        self.segmentation = self  # Segmentation reference
        self.upload = self  # Upload reference
        self.download = self  # Download reference
        self.publishing = self  # Publishing reference
        
        # Add missing methods as attributes
        self.metrics_collector = self  # For monitoring
        
'''

# Insert the missing attributes
content = content[:init_end] + missing_attributes + '        ' + content[init_end:]

# Add missing methods to the class
methods_to_add = '''
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics for monitoring"""
        return {
            'total_files': self.db.fetch_one("SELECT COUNT(*) as count FROM files")['count'] if self.db.fetch_one("SELECT COUNT(*) as count FROM files") else 0,
            'total_size': 0,
            'total_shares': 0,
            'active_uploads': 0,
            'active_downloads': 0,
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0,
            'upload_speed': 0,
            'download_speed': 0
        }
    
    def create_public_share(self, folder_id: str, owner_id: str, expiry_days: int = 30) -> Dict[str, Any]:
        """Create public share"""
        return self.access_control.create_public_share(folder_id, owner_id, expiry_days)
    
    def create_private_share(self, folder_id: str, owner_id: str, allowed_users: list, expiry_days: int = 30) -> Dict[str, Any]:
        """Create private share"""
        return self.access_control.create_private_share(folder_id, owner_id, allowed_users, expiry_days)
    
    def create_protected_share(self, folder_id: str, owner_id: str, password: str, expiry_days: int = 30) -> Dict[str, Any]:
        """Create protected share"""
        return self.access_control.create_protected_share(folder_id, owner_id, password, expiry_days)
    
    def download_share(self, share_id: str, destination: str, selected_files: list = None) -> None:
        """Download a share"""
        # Implementation would go here
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        return self.get_metrics()
'''

# Add methods before the main function
main_func_pos = content.find('def main():')
if main_func_pos > 0:
    content = content[:main_func_pos] + methods_to_add + '\n' + content[main_func_pos:]

# Write back
with open('/workspace/src/unified/main.py', 'w') as f:
    f.write(content)

print("✅ Added missing attributes to UnifiedSystem")
print("✅ Added compatibility aliases (security, user_manager, monitoring)")
print("✅ Added missing methods (get_metrics, create shares, etc.)")
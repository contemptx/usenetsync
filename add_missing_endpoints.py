#!/usr/bin/env python3
"""
Script to add all missing endpoints to the API server
"""

import re

# Read the current server.py file
with open('/workspace/backend/src/unified/api/server.py', 'r') as f:
    content = f.read()

# Find where to insert the new endpoints (before WebSocket)
websocket_pattern = r'(\s+@self\.app\.websocket\("/ws"\))'
match = re.search(websocket_pattern, content)
if not match:
    print("Could not find WebSocket endpoint")
    exit(1)

insert_pos = match.start()

# Define all the backup endpoints
backup_endpoints = '''
        # ==================== BACKUP & RECOVERY ENDPOINTS ====================
        
        @self.app.post("/api/v1/backup/create")
        async def create_backup(request: dict = {}):
            """Create system backup"""
            try:
                backup_type = request.get('type', 'full')
                compress = request.get('compress', True)
                encrypt = request.get('encrypt', False)
                
                # Get or initialize backup system
                if not hasattr(self, 'backup_system'):
                    from unified.backup_recovery import BackupRecoverySystem
                    import os
                    backup_dir = os.path.join(os.path.expanduser("~"), ".usenetsync", "backups")
                    self.backup_system = BackupRecoverySystem(backup_dir=backup_dir)
                
                # Create backup
                result = self.backup_system.create_backup(
                    self.system,
                    backup_type=backup_type,
                    compress=compress,
                    encrypt=encrypt
                )
                
                return result
            except Exception as e:
                logger.error(f"Failed to create backup: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/backup/restore")
        async def restore_backup(request: dict):
            """Restore from backup"""
            try:
                backup_id = request.get('backup_id')
                if not backup_id:
                    raise HTTPException(status_code=400, detail="backup_id is required")
                
                # Get or initialize backup system
                if not hasattr(self, 'backup_system'):
                    from unified.backup_recovery import BackupRecoverySystem
                    import os
                    backup_dir = os.path.join(os.path.expanduser("~"), ".usenetsync", "backups")
                    self.backup_system = BackupRecoverySystem(backup_dir=backup_dir)
                
                # Restore backup
                result = self.backup_system.restore_backup(backup_id, self.system)
                
                return result
            except Exception as e:
                logger.error(f"Failed to restore backup: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/backup/list")
        async def list_backups():
            """List all backups"""
            try:
                # Get or initialize backup system
                if not hasattr(self, 'backup_system'):
                    from unified.backup_recovery import BackupRecoverySystem
                    import os
                    backup_dir = os.path.join(os.path.expanduser("~"), ".usenetsync", "backups")
                    self.backup_system = BackupRecoverySystem(backup_dir=backup_dir)
                
                # List backups
                backups = self.backup_system.list_backups()
                
                return {"backups": backups}
            except Exception as e:
                logger.error(f"Failed to list backups: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/backup/verify")
        async def verify_backup(request: dict):
            """Verify backup integrity"""
            try:
                backup_id = request.get('backup_id')
                if not backup_id:
                    raise HTTPException(status_code=400, detail="backup_id is required")
                
                # Get or initialize backup system
                if not hasattr(self, 'backup_system'):
                    from unified.backup_recovery import BackupRecoverySystem
                    import os
                    backup_dir = os.path.join(os.path.expanduser("~"), ".usenetsync", "backups")
                    self.backup_system = BackupRecoverySystem(backup_dir=backup_dir)
                
                # Verify backup
                result = self.backup_system.verify_backup(backup_id)
                
                return result
            except Exception as e:
                logger.error(f"Failed to verify backup: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/backup/schedule")
        async def schedule_backup(request: dict):
            """Schedule automatic backups"""
            try:
                cron_expression = request.get('cron', '0 2 * * *')
                
                # Get or initialize backup system
                if not hasattr(self, 'backup_system'):
                    from unified.backup_recovery import BackupRecoverySystem
                    import os
                    backup_dir = os.path.join(os.path.expanduser("~"), ".usenetsync", "backups")
                    self.backup_system = BackupRecoverySystem(backup_dir=backup_dir)
                
                # Schedule backup
                self.backup_system.schedule_backup(cron_expression)
                
                return {
                    "success": True,
                    "cron": cron_expression,
                    "message": "Backup scheduled successfully"
                }
            except Exception as e:
                logger.error(f"Failed to schedule backup: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/v1/backup/{backup_id}")
        async def delete_backup(backup_id: str):
            """Delete a backup"""
            try:
                # Get or initialize backup system
                if not hasattr(self, 'backup_system'):
                    from unified.backup_recovery import BackupRecoverySystem
                    import os
                    backup_dir = os.path.join(os.path.expanduser("~"), ".usenetsync", "backups")
                    self.backup_system = BackupRecoverySystem(backup_dir=backup_dir)
                
                # Find and delete backup
                backup_file = self.backup_system._find_backup_file(backup_id)
                if backup_file and backup_file.exists():
                    import os
                    os.remove(backup_file)
                    return {"success": True, "message": "Backup deleted"}
                else:
                    raise HTTPException(status_code=404, detail="Backup not found")
                    
            except Exception as e:
                logger.error(f"Failed to delete backup: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/backup/{backup_id}/metadata")
        async def get_backup_metadata(backup_id: str):
            """Get backup metadata"""
            try:
                # Get or initialize backup system
                if not hasattr(self, 'backup_system'):
                    from unified.backup_recovery import BackupRecoverySystem
                    import os
                    backup_dir = os.path.join(os.path.expanduser("~"), ".usenetsync", "backups")
                    self.backup_system = BackupRecoverySystem(backup_dir=backup_dir)
                
                # Load metadata
                metadata = self.backup_system._load_metadata(backup_id)
                if metadata:
                    return {
                        "backup_id": metadata.backup_id,
                        "timestamp": metadata.timestamp.isoformat(),
                        "type": metadata.backup_type,
                        "size_bytes": metadata.size_bytes,
                        "checksum": metadata.checksum
                    }
                else:
                    raise HTTPException(status_code=404, detail="Backup metadata not found")
                    
            except Exception as e:
                logger.error(f"Failed to get backup metadata: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/backup/export")
        async def export_backup(request: dict):
            """Export backup to external storage"""
            try:
                backup_id = request.get('backup_id')
                export_path = request.get('export_path')
                
                if not backup_id or not export_path:
                    raise HTTPException(status_code=400, detail="backup_id and export_path are required")
                
                # Get or initialize backup system
                if not hasattr(self, 'backup_system'):
                    from unified.backup_recovery import BackupRecoverySystem
                    import os
                    backup_dir = os.path.join(os.path.expanduser("~"), ".usenetsync", "backups")
                    self.backup_system = BackupRecoverySystem(backup_dir=backup_dir)
                
                # Export backup
                backup_file = self.backup_system._find_backup_file(backup_id)
                if backup_file and backup_file.exists():
                    import shutil
                    shutil.copy2(backup_file, export_path)
                    return {
                        "success": True,
                        "exported_to": export_path,
                        "message": "Backup exported successfully"
                    }
                else:
                    raise HTTPException(status_code=404, detail="Backup not found")
                    
            except Exception as e:
                logger.error(f"Failed to export backup: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/backup/import")
        async def import_backup(request: dict):
            """Import backup from external storage"""
            try:
                import_path = request.get('import_path')
                
                if not import_path:
                    raise HTTPException(status_code=400, detail="import_path is required")
                
                # Get or initialize backup system
                if not hasattr(self, 'backup_system'):
                    from unified.backup_recovery import BackupRecoverySystem
                    import os
                    backup_dir = os.path.join(os.path.expanduser("~"), ".usenetsync", "backups")
                    self.backup_system = BackupRecoverySystem(backup_dir=backup_dir)
                
                # Import backup
                import shutil
                import os
                filename = os.path.basename(import_path)
                dest_path = os.path.join(self.backup_system.backup_dir, filename)
                shutil.copy2(import_path, dest_path)
                
                return {
                    "success": True,
                    "imported_file": filename,
                    "message": "Backup imported successfully"
                }
                    
            except Exception as e:
                logger.error(f"Failed to import backup: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
'''

# Insert the new endpoints
new_content = content[:insert_pos] + backup_endpoints + content[insert_pos:]

# Write the updated content back
with open('/workspace/backend/src/unified/api/server.py', 'w') as f:
    f.write(new_content)

print("Added backup endpoints successfully!")
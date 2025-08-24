#!/usr/bin/env python3
"""
Backup and Recovery System for Unified UsenetSync
Provides automated backup, restore, and disaster recovery capabilities
"""

import os
import sys
import json
import shutil
import sqlite3
import logging
import hashlib
import tarfile
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import subprocess

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unified.unified_system import UnifiedSystem
from unified.core.schema import UnifiedSchema

logger = logging.getLogger(__name__)

@dataclass
class BackupMetadata:
    """Backup metadata information"""
    backup_id: str
    timestamp: datetime
    db_type: str
    version: str
    size_bytes: int
    file_count: int
    segment_count: int
    checksum: str
    compression: str
    incremental: bool = False
    parent_backup: Optional[str] = None

class BackupRecoverySystem:
    """Comprehensive backup and recovery system"""
    
    def __init__(self, backup_dir: str = "/backup"):
        """
        Initialize backup system
        
        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup configuration
        self.retention_days = 30
        self.compression_level = 6
        self.incremental_enabled = True
        self.encrypt_backups = False
        
    def create_backup(self, system: UnifiedSystem, 
                     backup_type: str = "full",
                     compress: bool = True,
                     encrypt: bool = False) -> Dict[str, Any]:
        """
        Create a backup of the system
        
        Args:
            system: UnifiedSystem instance to backup
            backup_type: Type of backup (full, incremental, differential)
            compress: Whether to compress the backup
            encrypt: Whether to encrypt the backup
            
        Returns:
            Backup information dictionary
        """
        logger.info(f"Creating {backup_type} backup...")
        
        # Generate backup ID
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{backup_type}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(exist_ok=True)
        
        try:
            # 1. Backup database
            db_backup_file = self._backup_database(system, backup_path)
            
            # 2. Backup configuration
            config_backup_file = self._backup_configuration(backup_path)
            
            # 3. Backup metadata
            metadata = self._create_metadata(system, backup_id, backup_type)
            
            # 4. Create incremental backup if requested
            if backup_type == "incremental":
                parent_backup = self._get_last_full_backup()
                if parent_backup:
                    metadata.parent_backup = parent_backup
                    self._create_incremental_backup(system, backup_path, parent_backup)
            
            # 5. Compress if requested
            if compress:
                archive_file = self._compress_backup(backup_path, backup_id)
                # Remove uncompressed files
                shutil.rmtree(backup_path)
                backup_path = archive_file
                metadata.compression = "gzip"
            
            # 6. Encrypt if requested
            if encrypt:
                encrypted_file = self._encrypt_backup(backup_path)
                os.remove(backup_path)
                backup_path = encrypted_file
            
            # 7. Calculate checksum
            metadata.checksum = self._calculate_checksum(backup_path)
            
            # 8. Save metadata
            self._save_metadata(metadata)
            
            # 9. Clean old backups
            self._cleanup_old_backups()
            
            logger.info(f"Backup created successfully: {backup_id}")
            
            return {
                'success': True,
                'backup_id': backup_id,
                'path': str(backup_path),
                'size': metadata.size_bytes,
                'checksum': metadata.checksum,
                'timestamp': metadata.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            # Cleanup failed backup
            if backup_path.exists():
                if backup_path.is_dir():
                    shutil.rmtree(backup_path)
                else:
                    os.remove(backup_path)
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def restore_backup(self, backup_id: str, 
                       target_system: Optional[UnifiedSystem] = None,
                       verify: bool = True) -> Dict[str, Any]:
        """
        Restore from backup
        
        Args:
            backup_id: ID of backup to restore
            target_system: Target system to restore to
            verify: Whether to verify backup integrity
            
        Returns:
            Restore information dictionary
        """
        logger.info(f"Restoring from backup: {backup_id}")
        
        try:
            # 1. Load metadata
            metadata = self._load_metadata(backup_id)
            if not metadata:
                raise ValueError(f"Backup metadata not found: {backup_id}")
            
            # 2. Find backup file
            backup_file = self._find_backup_file(backup_id)
            if not backup_file:
                raise FileNotFoundError(f"Backup file not found: {backup_id}")
            
            # 3. Verify checksum if requested
            if verify:
                calculated_checksum = self._calculate_checksum(backup_file)
                if calculated_checksum != metadata.checksum:
                    raise ValueError("Backup checksum verification failed")
            
            # 4. Extract backup
            temp_dir = Path("/tmp") / f"restore_{backup_id}"
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Decrypt if needed
                if backup_file.suffix == '.enc':
                    backup_file = self._decrypt_backup(backup_file, temp_dir)
                
                # Decompress if needed
                if metadata.compression:
                    self._decompress_backup(backup_file, temp_dir)
                else:
                    shutil.copy(backup_file, temp_dir)
                
                # 5. Restore database
                db_file = temp_dir / "database.db"
                if not db_file.exists():
                    db_file = temp_dir / "database.sql"
                
                if db_file.exists():
                    self._restore_database(db_file, target_system or self._create_system(metadata))
                
                # 6. Restore configuration
                config_file = temp_dir / "config.json"
                if config_file.exists():
                    self._restore_configuration(config_file)
                
                # 7. Apply incremental changes if needed
                if metadata.incremental and metadata.parent_backup:
                    self._apply_incremental_changes(temp_dir, target_system)
                
                logger.info(f"Restore completed successfully from {backup_id}")
                
                return {
                    'success': True,
                    'backup_id': backup_id,
                    'restored_files': metadata.file_count,
                    'restored_segments': metadata.segment_count,
                    'timestamp': datetime.now().isoformat()
                }
                
            finally:
                # Cleanup temp directory
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Verify backup integrity
        
        Args:
            backup_id: ID of backup to verify
            
        Returns:
            Verification results
        """
        logger.info(f"Verifying backup: {backup_id}")
        
        try:
            # Load metadata
            metadata = self._load_metadata(backup_id)
            if not metadata:
                return {
                    'success': False,
                    'error': 'Metadata not found'
                }
            
            # Find backup file
            backup_file = self._find_backup_file(backup_id)
            if not backup_file:
                return {
                    'success': False,
                    'error': 'Backup file not found'
                }
            
            # Verify checksum
            calculated_checksum = self._calculate_checksum(backup_file)
            checksum_valid = calculated_checksum == metadata.checksum
            
            # Verify file integrity
            file_valid = backup_file.stat().st_size == metadata.size_bytes
            
            # Test extraction (without actually restoring)
            extraction_valid = self._test_extraction(backup_file)
            
            return {
                'success': checksum_valid and file_valid and extraction_valid,
                'backup_id': backup_id,
                'checksum_valid': checksum_valid,
                'file_size_valid': file_valid,
                'extraction_valid': extraction_valid,
                'metadata': asdict(metadata)
            }
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self, include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        List all available backups
        
        Args:
            include_metadata: Whether to include full metadata
            
        Returns:
            List of backup information
        """
        backups = []
        
        # Find all metadata files
        metadata_files = self.backup_dir.glob("*.metadata.json")
        
        for metadata_file in metadata_files:
            try:
                with open(metadata_file, 'r') as f:
                    metadata_dict = json.load(f)
                
                backup_info = {
                    'backup_id': metadata_dict['backup_id'],
                    'timestamp': metadata_dict['timestamp'],
                    'type': 'incremental' if metadata_dict.get('incremental') else 'full',
                    'size': metadata_dict['size_bytes'],
                    'compressed': bool(metadata_dict.get('compression')),
                    'encrypted': metadata_file.with_suffix('.enc').exists()
                }
                
                if include_metadata:
                    backup_info['metadata'] = metadata_dict
                
                # Check if backup file exists
                backup_file = self._find_backup_file(metadata_dict['backup_id'])
                backup_info['available'] = backup_file is not None
                
                backups.append(backup_info)
                
            except Exception as e:
                logger.warning(f"Error reading metadata {metadata_file}: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return backups
    
    def schedule_backup(self, cron_expression: str = "0 2 * * *"):
        """
        Schedule automatic backups
        
        Args:
            cron_expression: Cron expression for scheduling
        """
        # Create cron job
        cron_line = f"{cron_expression} /usr/bin/python3 {__file__} --auto-backup\n"
        
        # Add to crontab
        try:
            # Get current crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_cron = result.stdout if result.returncode == 0 else ""
            
            # Check if already scheduled
            if __file__ in current_cron:
                logger.info("Backup already scheduled")
                return
            
            # Add new cron job
            new_cron = current_cron + cron_line
            
            # Set new crontab
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(new_cron)
            
            logger.info(f"Backup scheduled: {cron_expression}")
            
        except Exception as e:
            logger.error(f"Failed to schedule backup: {e}")
    
    def _backup_database(self, system: UnifiedSystem, backup_path: Path) -> Path:
        """Backup database"""
        if system.db_type == 'sqlite':
            # SQLite backup
            db_backup = backup_path / "database.db"
            
            source = sqlite3.connect(system.db_manager.db_path)
            dest = sqlite3.connect(str(db_backup))
            
            with dest:
                source.backup(dest)
            
            source.close()
            dest.close()
            
            return db_backup
            
        elif system.db_type == 'postgresql':
            # PostgreSQL backup
            db_backup = backup_path / "database.sql"
            
            cmd = [
                'pg_dump',
                '-h', system.db_manager.host,
                '-d', system.db_manager.database,
                '-U', system.db_manager.user,
                '-f', str(db_backup),
                '--no-password'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = system.db_manager.password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"pg_dump failed: {result.stderr}")
            
            return db_backup
    
    def _backup_configuration(self, backup_path: Path) -> Path:
        """Backup configuration"""
        config_backup = backup_path / "config.json"
        
        # Get configuration from various sources
        config = {
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'environment': dict(os.environ),
            'settings': {}
        }
        
        # Try to load main config file
        config_files = [
            '/etc/usenetsync/usenetsync.conf',
            os.path.expanduser('~/.usenetsync.conf'),
            '/config/usenetsync.conf'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config['settings']['main_config'] = f.read()
                break
        
        with open(config_backup, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config_backup
    
    def _create_metadata(self, system: UnifiedSystem, backup_id: str, 
                        backup_type: str) -> BackupMetadata:
        """Create backup metadata"""
        stats = system.get_statistics()
        
        return BackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.now(),
            db_type=system.db_type,
            version='2.0.0',
            size_bytes=0,  # Will be updated after compression
            file_count=stats.get('total_files', 0),
            segment_count=stats.get('total_segments', 0),
            checksum='',  # Will be calculated later
            compression='none',
            incremental=(backup_type == 'incremental')
        )
    
    def _compress_backup(self, backup_path: Path, backup_id: str) -> Path:
        """Compress backup directory"""
        archive_file = self.backup_dir / f"{backup_id}.tar.gz"
        
        with tarfile.open(archive_file, 'w:gz', compresslevel=self.compression_level) as tar:
            tar.add(backup_path, arcname=backup_id)
        
        return archive_file
    
    def _decompress_backup(self, archive_file: Path, target_dir: Path):
        """Decompress backup archive"""
        with tarfile.open(archive_file, 'r:gz') as tar:
            tar.extractall(target_dir)
    
    def _encrypt_backup(self, backup_file: Path) -> Path:
        """Encrypt backup file"""
        from cryptography.fernet import Fernet
        
        # Generate or load encryption key
        key_file = self.backup_dir / ".encryption_key"
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
        
        fernet = Fernet(key)
        
        # Encrypt file
        encrypted_file = backup_file.with_suffix(backup_file.suffix + '.enc')
        
        with open(backup_file, 'rb') as f:
            encrypted_data = fernet.encrypt(f.read())
        
        with open(encrypted_file, 'wb') as f:
            f.write(encrypted_data)
        
        return encrypted_file
    
    def _decrypt_backup(self, encrypted_file: Path, target_dir: Path) -> Path:
        """Decrypt backup file"""
        from cryptography.fernet import Fernet
        
        # Load encryption key
        key_file = self.backup_dir / ".encryption_key"
        if not key_file.exists():
            raise ValueError("Encryption key not found")
        
        with open(key_file, 'rb') as f:
            key = f.read()
        
        fernet = Fernet(key)
        
        # Decrypt file
        decrypted_file = target_dir / encrypted_file.stem
        
        with open(encrypted_file, 'rb') as f:
            decrypted_data = fernet.decrypt(f.read())
        
        with open(decrypted_file, 'wb') as f:
            f.write(decrypted_data)
        
        return decrypted_file
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum"""
        hasher = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def _save_metadata(self, metadata: BackupMetadata):
        """Save backup metadata"""
        metadata_file = self.backup_dir / f"{metadata.backup_id}.metadata.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(asdict(metadata), f, indent=2, default=str)
    
    def _load_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Load backup metadata"""
        metadata_file = self.backup_dir / f"{backup_id}.metadata.json"
        
        if not metadata_file.exists():
            return None
        
        with open(metadata_file, 'r') as f:
            data = json.load(f)
        
        return BackupMetadata(
            backup_id=data['backup_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            db_type=data['db_type'],
            version=data['version'],
            size_bytes=data['size_bytes'],
            file_count=data['file_count'],
            segment_count=data['segment_count'],
            checksum=data['checksum'],
            compression=data['compression'],
            incremental=data.get('incremental', False),
            parent_backup=data.get('parent_backup')
        )
    
    def _find_backup_file(self, backup_id: str) -> Optional[Path]:
        """Find backup file by ID"""
        possible_files = [
            self.backup_dir / backup_id,
            self.backup_dir / f"{backup_id}.tar.gz",
            self.backup_dir / f"{backup_id}.tar.gz.enc"
        ]
        
        for file_path in possible_files:
            if file_path.exists():
                return file_path
        
        return None
    
    def _get_last_full_backup(self) -> Optional[str]:
        """Get ID of last full backup"""
        backups = self.list_backups(include_metadata=False)
        
        for backup in backups:
            if backup['type'] == 'full' and backup['available']:
                return backup['backup_id']
        
        return None
    
    def _create_incremental_backup(self, system: UnifiedSystem, 
                                  backup_path: Path, parent_backup: str):
        """Create incremental backup based on parent"""
        # Get changes since parent backup
        parent_metadata = self._load_metadata(parent_backup)
        if not parent_metadata:
            raise ValueError(f"Parent backup metadata not found: {parent_backup}")
        
        # Query for changes since parent backup timestamp
        changes = system.db_manager.fetchall("""
            SELECT * FROM files 
            WHERE modified_time > %s
        """, (parent_metadata.timestamp,))
        
        # Save only changed files
        changes_file = backup_path / "incremental_changes.json"
        with open(changes_file, 'w') as f:
            json.dump([dict(c) for c in changes], f, indent=2, default=str)
    
    def _apply_incremental_changes(self, temp_dir: Path, system: UnifiedSystem):
        """Apply incremental changes during restore"""
        changes_file = temp_dir / "incremental_changes.json"
        
        if not changes_file.exists():
            return
        
        with open(changes_file, 'r') as f:
            changes = json.load(f)
        
        for change in changes:
            # Apply change to database
            system.db_manager.execute("""
                INSERT OR REPLACE INTO files 
                (file_id, folder_id, file_path, file_hash, file_size, 
                 modified_time, version, segment_count, state)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple(change.values()))
    
    def _restore_database(self, db_file: Path, system: UnifiedSystem):
        """Restore database from backup"""
        if system.db_type == 'sqlite':
            # SQLite restore
            shutil.copy(db_file, system.db_manager.db_path)
            
        elif system.db_type == 'postgresql':
            # PostgreSQL restore
            cmd = [
                'psql',
                '-h', system.db_manager.host,
                '-d', system.db_manager.database,
                '-U', system.db_manager.user,
                '-f', str(db_file)
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = system.db_manager.password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"psql restore failed: {result.stderr}")
    
    def _restore_configuration(self, config_file: Path):
        """Restore configuration from backup"""
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Restore main config if present
        if 'main_config' in config.get('settings', {}):
            config_path = Path('/etc/usenetsync/usenetsync.conf')
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                f.write(config['settings']['main_config'])
    
    def _test_extraction(self, backup_file: Path) -> bool:
        """Test if backup can be extracted"""
        try:
            if backup_file.suffix == '.gz':
                with tarfile.open(backup_file, 'r:gz') as tar:
                    # Just test if we can read the archive
                    tar.getnames()
            return True
        except:
            return False
    
    def _cleanup_old_backups(self):
        """Remove backups older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        backups = self.list_backups(include_metadata=True)
        
        for backup in backups:
            backup_date = datetime.fromisoformat(backup['timestamp'])
            
            if backup_date < cutoff_date:
                logger.info(f"Removing old backup: {backup['backup_id']}")
                
                # Remove backup file
                backup_file = self._find_backup_file(backup['backup_id'])
                if backup_file:
                    os.remove(backup_file)
                
                # Remove metadata
                metadata_file = self.backup_dir / f"{backup['backup_id']}.metadata.json"
                if metadata_file.exists():
                    os.remove(metadata_file)
    
    def _create_system(self, metadata: BackupMetadata) -> UnifiedSystem:
        """Create system instance from metadata"""
        return UnifiedSystem(
            metadata.db_type,
            path='/tmp/restore.db' if metadata.db_type == 'sqlite' else None
        )


def test_backup_recovery():
    """Test backup and recovery system"""
    print("\n=== Testing Backup & Recovery System ===\n")
    
    # Create test system
    system = UnifiedSystem('sqlite', path='/tmp/test_backup.db')
    
    # Create backup system
    backup_system = BackupRecoverySystem(backup_dir='/tmp/backups')
    
    # Test 1: Create full backup
    print("1. Creating full backup...")
    result = backup_system.create_backup(system, backup_type='full', compress=True)
    
    if result['success']:
        print(f"   ✓ Backup created: {result['backup_id']}")
        print(f"   Size: {result['size']} bytes")
        print(f"   Checksum: {result['checksum'][:16]}...")
        backup_id = result['backup_id']
    else:
        print(f"   ✗ Backup failed: {result['error']}")
        return
    
    # Test 2: Verify backup
    print("\n2. Verifying backup...")
    verification = backup_system.verify_backup(backup_id)
    
    if verification['success']:
        print("   ✓ Backup verified successfully")
        print(f"   Checksum valid: {verification['checksum_valid']}")
        print(f"   File size valid: {verification['file_size_valid']}")
        print(f"   Extraction valid: {verification['extraction_valid']}")
    else:
        print(f"   ✗ Verification failed: {verification['error']}")
    
    # Test 3: List backups
    print("\n3. Listing backups...")
    backups = backup_system.list_backups(include_metadata=False)
    
    for backup in backups:
        print(f"   - {backup['backup_id']}")
        print(f"     Type: {backup['type']}")
        print(f"     Size: {backup['size']} bytes")
        print(f"     Available: {backup['available']}")
    
    # Test 4: Create incremental backup
    print("\n4. Creating incremental backup...")
    result = backup_system.create_backup(system, backup_type='incremental')
    
    if result['success']:
        print(f"   ✓ Incremental backup created: {result['backup_id']}")
    else:
        print(f"   ✗ Incremental backup failed: {result['error']}")
    
    # Test 5: Restore backup
    print("\n5. Testing restore...")
    restore_system = UnifiedSystem('sqlite', path='/tmp/restored.db')
    result = backup_system.restore_backup(backup_id, target_system=restore_system)
    
    if result['success']:
        print("   ✓ Restore completed successfully")
        print(f"   Restored files: {result['restored_files']}")
        print(f"   Restored segments: {result['restored_segments']}")
    else:
        print(f"   ✗ Restore failed: {result['error']}")
    
    print("\n✓ Backup & Recovery system test completed")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_backup_recovery()
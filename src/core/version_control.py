"""
Version Control System for UsenetSync
Tracks multiple versions of files with full history
"""

import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class FileVersion:
    """Represents a single version of a file"""
    version_id: str
    file_name: str
    file_path: str
    share_id: str
    file_hash: str
    file_size: int
    version_number: int
    created_at: datetime
    created_by: str
    parent_version_id: Optional[str] = None
    changes_description: Optional[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileVersion':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

class VersionControl:
    """Manages file versioning for UsenetSync"""
    
    def __init__(self, db_manager):
        """Initialize version control system"""
        self.db = db_manager
        self.version_cache = {}
        self._init_database()
    
    def _init_database(self):
        """Initialize version control tables"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create version control table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS file_versions (
                        version_id TEXT PRIMARY KEY,
                        file_name TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        share_id TEXT NOT NULL,
                        file_hash TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        version_number INTEGER NOT NULL,
                        parent_version_id TEXT,
                        created_at TIMESTAMP NOT NULL,
                        created_by TEXT NOT NULL,
                        changes_description TEXT,
                        tags TEXT,
                        metadata TEXT,
                        FOREIGN KEY (parent_version_id) REFERENCES file_versions(version_id)
                    )
                """)
                
                # Create version chains table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS version_chains (
                        chain_id TEXT PRIMARY KEY,
                        file_identifier TEXT NOT NULL,
                        latest_version_id TEXT NOT NULL,
                        total_versions INTEGER DEFAULT 1,
                        total_size INTEGER DEFAULT 0,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (latest_version_id) REFERENCES file_versions(version_id)
                    )
                """)
                
                # Create indices
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_versions_share ON file_versions(share_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_versions_hash ON file_versions(file_hash)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_version_chains_file ON version_chains(file_identifier)")
                
                conn.commit()
                logger.info("Version control database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize version control database: {e}")
            raise
    
    def _generate_version_id(self, file_path: str, version_number: int) -> str:
        """Generate unique version ID"""
        content = f"{file_path}:{version_number}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_chain_id(self, file_identifier: str) -> str:
        """Generate unique chain ID"""
        content = f"chain:{file_identifier}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _get_file_identifier(self, file_path: str) -> str:
        """Get consistent file identifier across versions"""
        # Use normalized path as identifier
        return str(Path(file_path).resolve())
    
    async def create_version(
        self,
        file_path: str,
        share_id: str,
        file_hash: str,
        file_size: int,
        created_by: str,
        changes_description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileVersion:
        """
        Create a new version of a file
        
        Args:
            file_path: Path to the file
            share_id: Share ID for this version
            file_hash: Hash of file contents
            file_size: Size of file in bytes
            created_by: User who created this version
            changes_description: Description of changes
            tags: Optional tags for this version
            metadata: Optional metadata
            
        Returns:
            Created FileVersion object
        """
        try:
            file_identifier = self._get_file_identifier(file_path)
            file_name = Path(file_path).name
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if this is a new file or new version
                cursor.execute("""
                    SELECT chain_id, latest_version_id, total_versions
                    FROM version_chains
                    WHERE file_identifier = ?
                """, (file_identifier,))
                
                chain_info = cursor.fetchone()
                
                if chain_info:
                    # Existing file - create new version
                    chain_id, parent_version_id, total_versions = chain_info
                    version_number = total_versions + 1
                else:
                    # New file - create first version
                    chain_id = self._generate_chain_id(file_identifier)
                    parent_version_id = None
                    version_number = 1
                
                # Generate version ID
                version_id = self._generate_version_id(file_path, version_number)
                
                # Create version object
                version = FileVersion(
                    version_id=version_id,
                    file_name=file_name,
                    file_path=file_path,
                    share_id=share_id,
                    file_hash=file_hash,
                    file_size=file_size,
                    version_number=version_number,
                    created_at=datetime.now(),
                    created_by=created_by,
                    parent_version_id=parent_version_id,
                    changes_description=changes_description,
                    tags=tags or [],
                    metadata=metadata or {}
                )
                
                # Insert version record
                cursor.execute("""
                    INSERT INTO file_versions (
                        version_id, file_name, file_path, share_id, file_hash,
                        file_size, version_number, parent_version_id, created_at,
                        created_by, changes_description, tags, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    version.version_id,
                    version.file_name,
                    version.file_path,
                    version.share_id,
                    version.file_hash,
                    version.file_size,
                    version.version_number,
                    version.parent_version_id,
                    version.created_at,
                    version.created_by,
                    version.changes_description,
                    json.dumps(version.tags) if version.tags else None,
                    json.dumps(version.metadata) if version.metadata else None
                ))
                
                # Update or create chain record
                if chain_info:
                    cursor.execute("""
                        UPDATE version_chains
                        SET latest_version_id = ?, total_versions = ?, 
                            total_size = total_size + ?, updated_at = ?
                        WHERE chain_id = ?
                    """, (version_id, version_number, file_size, datetime.now(), chain_id))
                else:
                    cursor.execute("""
                        INSERT INTO version_chains (
                            chain_id, file_identifier, latest_version_id,
                            total_versions, total_size, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        chain_id, file_identifier, version_id,
                        1, file_size, datetime.now(), datetime.now()
                    ))
                
                conn.commit()
                
                # Update cache
                self.version_cache[version_id] = version
                
                logger.info(f"Created version {version_number} for {file_name}")
                return version
                
        except Exception as e:
            logger.error(f"Failed to create version: {e}")
            raise
    
    async def get_version(self, version_id: str) -> Optional[FileVersion]:
        """Get a specific version by ID"""
        # Check cache first
        if version_id in self.version_cache:
            return self.version_cache[version_id]
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM file_versions WHERE version_id = ?
                """, (version_id,))
                
                row = cursor.fetchone()
                if row:
                    version_data = dict(zip([col[0] for col in cursor.description], row))
                    
                    # Parse JSON fields
                    if version_data.get('tags'):
                        version_data['tags'] = json.loads(version_data['tags'])
                    if version_data.get('metadata'):
                        version_data['metadata'] = json.loads(version_data['metadata'])
                    
                    version = FileVersion.from_dict(version_data)
                    self.version_cache[version_id] = version
                    return version
                    
        except Exception as e:
            logger.error(f"Failed to get version {version_id}: {e}")
        
        return None
    
    async def get_file_versions(self, file_path: str) -> List[FileVersion]:
        """Get all versions of a file"""
        try:
            file_identifier = self._get_file_identifier(file_path)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get chain ID
                cursor.execute("""
                    SELECT chain_id FROM version_chains WHERE file_identifier = ?
                """, (file_identifier,))
                
                result = cursor.fetchone()
                if not result:
                    return []
                
                chain_id = result[0]
                
                # Get all versions in chain
                cursor.execute("""
                    SELECT v.* FROM file_versions v
                    JOIN version_chains c ON (
                        v.version_id = c.latest_version_id OR
                        v.version_id IN (
                            SELECT version_id FROM file_versions
                            WHERE file_path = ?
                        )
                    )
                    WHERE c.chain_id = ?
                    ORDER BY v.version_number DESC
                """, (file_path, chain_id))
                
                versions = []
                for row in cursor.fetchall():
                    version_data = dict(zip([col[0] for col in cursor.description], row))
                    
                    # Parse JSON fields
                    if version_data.get('tags'):
                        version_data['tags'] = json.loads(version_data['tags'])
                    if version_data.get('metadata'):
                        version_data['metadata'] = json.loads(version_data['metadata'])
                    
                    versions.append(FileVersion.from_dict(version_data))
                
                return versions
                
        except Exception as e:
            logger.error(f"Failed to get versions for {file_path}: {e}")
            return []
    
    async def get_latest_version(self, file_path: str) -> Optional[FileVersion]:
        """Get the latest version of a file"""
        versions = await self.get_file_versions(file_path)
        return versions[0] if versions else None
    
    async def get_version_diff(
        self,
        version_id1: str,
        version_id2: str
    ) -> Dict[str, Any]:
        """
        Get differences between two versions
        
        Returns:
            Dictionary with diff information
        """
        try:
            v1 = await self.get_version(version_id1)
            v2 = await self.get_version(version_id2)
            
            if not v1 or not v2:
                return {"error": "Version not found"}
            
            return {
                "version1": v1.to_dict(),
                "version2": v2.to_dict(),
                "size_change": v2.file_size - v1.file_size,
                "hash_changed": v1.file_hash != v2.file_hash,
                "time_diff": (v2.created_at - v1.created_at).total_seconds(),
                "version_diff": v2.version_number - v1.version_number
            }
            
        except Exception as e:
            logger.error(f"Failed to get version diff: {e}")
            return {"error": str(e)}
    
    async def rollback_to_version(self, version_id: str) -> Optional[FileVersion]:
        """
        Create a new version that rolls back to a previous version
        
        Args:
            version_id: Version ID to rollback to
            
        Returns:
            New version created from rollback
        """
        try:
            version = await self.get_version(version_id)
            if not version:
                return None
            
            # Create new version with same content but new version number
            return await self.create_version(
                file_path=version.file_path,
                share_id=version.share_id,  # Would need new share upload
                file_hash=version.file_hash,
                file_size=version.file_size,
                created_by="system",
                changes_description=f"Rollback to version {version.version_number}",
                tags=["rollback"],
                metadata={"rollback_from": version_id}
            )
            
        except Exception as e:
            logger.error(f"Failed to rollback to version {version_id}: {e}")
            return None
    
    async def delete_version(self, version_id: str) -> bool:
        """
        Mark a version as deleted (soft delete)
        Note: Cannot actually delete from Usenet
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Add deleted flag to metadata
                cursor.execute("""
                    UPDATE file_versions
                    SET metadata = json_set(
                        COALESCE(metadata, '{}'),
                        '$.deleted', true,
                        '$.deleted_at', ?
                    )
                    WHERE version_id = ?
                """, (datetime.now().isoformat(), version_id))
                
                conn.commit()
                
                # Remove from cache
                if version_id in self.version_cache:
                    del self.version_cache[version_id]
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete version {version_id}: {e}")
            return False
    
    async def get_version_statistics(self) -> Dict[str, Any]:
        """Get statistics about version control usage"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total versions
                cursor.execute("SELECT COUNT(*) FROM file_versions")
                total_versions = cursor.fetchone()[0]
                
                # Total chains (unique files)
                cursor.execute("SELECT COUNT(*) FROM version_chains")
                total_files = cursor.fetchone()[0]
                
                # Average versions per file
                cursor.execute("SELECT AVG(total_versions) FROM version_chains")
                avg_versions = cursor.fetchone()[0] or 0
                
                # Total storage used
                cursor.execute("SELECT SUM(total_size) FROM version_chains")
                total_storage = cursor.fetchone()[0] or 0
                
                # Most versioned files
                cursor.execute("""
                    SELECT file_identifier, total_versions
                    FROM version_chains
                    ORDER BY total_versions DESC
                    LIMIT 5
                """)
                most_versioned = cursor.fetchall()
                
                return {
                    "total_versions": total_versions,
                    "total_files": total_files,
                    "average_versions_per_file": round(avg_versions, 2),
                    "total_storage_bytes": total_storage,
                    "most_versioned_files": [
                        {"file": Path(f[0]).name, "versions": f[1]}
                        for f in most_versioned
                    ]
                }
                
        except Exception as e:
            logger.error(f"Failed to get version statistics: {e}")
            return {}
#!/usr/bin/env python3
"""
Unified Publishing System for UsenetSync
Handles share creation, management, and access control
"""

import os
import sys
import hashlib
import logging
import time
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ShareInfo:
    """Information about a published share"""
    share_id: str
    folder_id: str
    share_type: str  # PUBLIC, PRIVATE, PROTECTED
    access_string: str
    encrypted_index: str
    index_size: int
    index_segments: int
    authorized_users: Optional[List[str]] = None
    access_commitments: Optional[Dict] = None
    password_salt: Optional[str] = None
    password_iterations: Optional[int] = None
    expires_at: Optional[datetime] = None
    active: bool = True

# ============================================================================
# UNIFIED PUBLISHING SYSTEM
# ============================================================================

class UnifiedPublishingSystem:
    """Unified system for publishing and managing shares"""
    
    def __init__(self, db_manager, security_system=None):
        self.db = db_manager
        self.security = security_system
        self.active_shares = {}
        
    def publish_folder(self, folder_id: str, share_type: str = 'PUBLIC',
                      password: Optional[str] = None,
                      authorized_users: Optional[List[str]] = None,
                      expiry_days: Optional[int] = None) -> ShareInfo:
        """
        Publish a folder as a share
        
        Args:
            folder_id: Folder to publish
            share_type: PUBLIC, PRIVATE, or PROTECTED
            password: Password for PROTECTED shares
            authorized_users: List of user IDs for PRIVATE shares
            expiry_days: Days until share expires
            
        Returns:
            ShareInfo with access details
        """
        logger.info(f"Publishing folder {folder_id} as {share_type} share")
        
        # Validate folder exists and is indexed
        folder_info = self._get_folder_info(folder_id)
        if not folder_info:
            raise ValueError(f"Folder not found or not indexed: {folder_id}")
            
        # Generate share ID
        share_id = self._generate_share_id()
        
        # Create index data
        index_data = self._create_index_data(folder_id)
        
        # Encrypt index based on share type
        encrypted_index, encryption_metadata = self._encrypt_index(
            index_data,
            share_type,
            password,
            authorized_users,
            folder_id
        )
        
        # Create access string
        access_string = self._create_access_string(
            share_id,
            share_type,
            encryption_metadata
        )
        
        # Calculate expiry
        expires_at = None
        if expiry_days:
            expires_at = datetime.now() + timedelta(days=expiry_days)
            
        # Create share info
        share_info = ShareInfo(
            share_id=share_id,
            folder_id=folder_id,
            share_type=share_type,
            access_string=access_string,
            encrypted_index=encrypted_index,
            index_size=len(encrypted_index),
            index_segments=1,  # Would calculate actual segments
            authorized_users=authorized_users,
            access_commitments=encryption_metadata.get('commitments'),
            password_salt=encryption_metadata.get('salt'),
            password_iterations=encryption_metadata.get('iterations'),
            expires_at=expires_at,
            active=True
        )
        
        # Store in database
        self._store_share(share_info)
        
        # Update folder statistics
        self._update_folder_stats(folder_id)
        
        logger.info(f"Published share {share_id} for folder {folder_id}")
        logger.info(f"Access string: {access_string[:50]}...")
        
        return share_info
        
    def unpublish_share(self, share_id: str) -> bool:
        """Unpublish/deactivate a share"""
        logger.info(f"Unpublishing share {share_id}")
        
        try:
            self.db.execute("""
                UPDATE shares
                SET active = FALSE,
                    updated_at = CURRENT_TIMESTAMP
                WHERE share_id = %s
            """, (share_id,))
            
            logger.info(f"Share {share_id} unpublished")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unpublish share: {e}")
            return False
            
    def get_share_info(self, share_id: str) -> Optional[ShareInfo]:
        """Get information about a share"""
        result = self.db.fetchone("""
            SELECT * FROM shares
            WHERE share_id = %s
        """, (share_id,))
        
        if result:
            return self._parse_share_info(dict(result))
        return None
        
    def list_shares(self, folder_id: Optional[str] = None,
                   active_only: bool = True) -> List[ShareInfo]:
        """List shares for a folder or all shares"""
        query = "SELECT * FROM shares WHERE 1=1"
        params = []
        
        if folder_id:
            query += " AND folder_id = %s"
            params.append(folder_id)
            
        if active_only:
            query += " AND active = TRUE"
            
        query += " ORDER BY published_at DESC"
        
        results = self.db.fetchall(query, tuple(params))
        
        return [self._parse_share_info(dict(r)) for r in results]
        
    def update_share(self, share_id: str, **updates) -> bool:
        """Update share properties"""
        allowed_updates = {
            'authorized_users', 'expires_at', 'active'
        }
        
        # Filter allowed updates
        valid_updates = {k: v for k, v in updates.items() if k in allowed_updates}
        
        if not valid_updates:
            return False
            
        # Build update query
        set_clauses = []
        params = []
        
        for key, value in valid_updates.items():
            set_clauses.append(f"{key} = %s")
            if key == 'authorized_users' and isinstance(value, list):
                value = json.dumps(value)
            params.append(value)
            
        params.append(share_id)
        
        query = f"""
            UPDATE shares
            SET {', '.join(set_clauses)},
                updated_at = CURRENT_TIMESTAMP
            WHERE share_id = %s
        """
        
        try:
            self.db.execute(query, tuple(params))
            logger.info(f"Updated share {share_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update share: {e}")
            return False
            
    def add_authorized_user(self, share_id: str, user_id: str) -> bool:
        """Add a user to a PRIVATE share"""
        share = self.get_share_info(share_id)
        
        if not share or share.share_type != 'PRIVATE':
            return False
            
        # Get current users
        users = share.authorized_users or []
        
        if user_id not in users:
            users.append(user_id)
            
            # Update access commitments if security system available
            if self.security:
                new_commitment = self.security.create_access_commitment(
                    user_id,
                    share.folder_id
                )
                
                commitments = share.access_commitments or {}
                commitments[user_id] = new_commitment
                
                # Update database
                self.db.execute("""
                    UPDATE shares
                    SET authorized_users = %s,
                        access_commitments = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE share_id = %s
                """, (json.dumps(users), json.dumps(commitments), share_id))
            else:
                # Just update users list
                return self.update_share(share_id, authorized_users=users)
                
        return True
        
    def remove_authorized_user(self, share_id: str, user_id: str) -> bool:
        """Remove a user from a PRIVATE share"""
        share = self.get_share_info(share_id)
        
        if not share or share.share_type != 'PRIVATE':
            return False
            
        users = share.authorized_users or []
        
        if user_id in users:
            users.remove(user_id)
            
            # Remove from commitments
            commitments = share.access_commitments or {}
            if user_id in commitments:
                del commitments[user_id]
                
            # Update database
            self.db.execute("""
                UPDATE shares
                SET authorized_users = %s,
                    access_commitments = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE share_id = %s
            """, (json.dumps(users), json.dumps(commitments), share_id))
            
            return True
            
        return False
        
    def _generate_share_id(self) -> str:
        """Generate unique share ID"""
        # 16 byte random ID, hex encoded (32 chars)
        return secrets.token_hex(16)
        
    def _get_folder_info(self, folder_id: str) -> Optional[dict]:
        """Get folder information"""
        result = self.db.fetchone("""
            SELECT * FROM folders
            WHERE folder_id = %s
        """, (folder_id,))
        
        if result:
            return dict(result)
        return None
        
    def _create_index_data(self, folder_id: str) -> dict:
        """Create index data for folder"""
        # Get all files and segments
        files = self.db.fetchall("""
            SELECT f.*, 
                   COUNT(s.segment_id) as segment_count,
                   STRING_AGG(s.message_id::text, ',') as message_ids,
                   STRING_AGG(s.usenet_subject, ',') as subjects
            FROM files f
            LEFT JOIN segments s ON f.file_id = s.file_id
            WHERE f.folder_id = %s
            AND f.state = 'indexed'
            GROUP BY f.file_id
            ORDER BY f.file_path
        """, (folder_id,))
        
        # Build index structure
        index = {
            'version': '1.0',
            'folder_id': folder_id,
            'created_at': datetime.now().isoformat(),
            'files': []
        }
        
        for file_row in files:
            file_data = dict(file_row)
            
            # Get segment details
            segments = self.db.fetchall("""
                SELECT segment_index, segment_hash, segment_size,
                       message_id, usenet_subject, encrypted_location
                FROM segments
                WHERE file_id = %s
                AND redundancy_level = 0
                ORDER BY segment_index
            """, (file_data['file_id'],))
            
            file_entry = {
                'file_id': file_data['file_id'],
                'file_path': file_data['file_path'],
                'file_hash': file_data['file_hash'],
                'file_size': file_data['file_size'],
                'segment_count': len(segments),
                'segments': [dict(s) for s in segments]
            }
            
            index['files'].append(file_entry)
            
        return index
        
    def _encrypt_index(self, index_data: dict, share_type: str,
                      password: Optional[str], authorized_users: Optional[List[str]],
                      folder_id: str) -> Tuple[str, dict]:
        """Encrypt index based on share type"""
        metadata = {}
        
        # Convert index to JSON
        index_json = json.dumps(index_data)
        
        if not self.security:
            # No encryption for testing
            return index_json, metadata
            
        if share_type == 'PUBLIC':
            # Public encryption (key included)
            encrypted, key = self.security.encrypt_public_index(index_json)
            metadata['key'] = key
            
        elif share_type == 'PRIVATE':
            # Private encryption with access commitments
            encrypted, commitments = self.security.encrypt_private_index(
                index_json,
                folder_id,
                authorized_users or []
            )
            metadata['commitments'] = commitments
            
        elif share_type == 'PROTECTED':
            # Password-based encryption
            if not password:
                raise ValueError("Password required for PROTECTED share")
                
            encrypted, salt, iterations = self.security.encrypt_protected_index(
                index_json,
                password
            )
            metadata['salt'] = salt
            metadata['iterations'] = iterations
            
        else:
            raise ValueError(f"Unknown share type: {share_type}")
            
        return encrypted, metadata
        
    def _create_access_string(self, share_id: str, share_type: str,
                             metadata: dict) -> str:
        """Create access string for share"""
        # Build access data
        access_data = {
            'v': '1',  # Version
            'id': share_id,
            'type': share_type[0],  # P for PUBLIC, R for PRIVATE, T for PROTECTED
        }
        
        # Add type-specific data
        if share_type == 'PUBLIC' and 'key' in metadata:
            access_data['k'] = metadata['key']
        elif share_type == 'PROTECTED':
            access_data['s'] = metadata.get('salt', '')
            access_data['i'] = metadata.get('iterations', 100000)
            
        # Encode as compact JSON
        return json.dumps(access_data, separators=(',', ':'))
        
    def _store_share(self, share_info: ShareInfo):
        """Store share in database"""
        self.db.execute("""
            INSERT INTO shares
            (share_id, folder_id, share_type, access_string,
             encrypted_index, index_size, index_segments,
             authorized_users, access_commitments,
             password_salt, password_iterations,
             expires_at, active, published_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (
            share_info.share_id,
            share_info.folder_id,
            share_info.share_type,
            share_info.access_string,
            share_info.encrypted_index,
            share_info.index_size,
            share_info.index_segments,
            json.dumps(share_info.authorized_users) if share_info.authorized_users else None,
            json.dumps(share_info.access_commitments) if share_info.access_commitments else None,
            share_info.password_salt,
            share_info.password_iterations,
            share_info.expires_at,
            share_info.active
        ))
        
    def _update_folder_stats(self, folder_id: str):
        """Update folder share statistics"""
        # Count active shares
        result = self.db.fetchone("""
            SELECT COUNT(*) as share_count
            FROM shares
            WHERE folder_id = %s AND active = TRUE
        """, (folder_id,))
        
        share_count = result['share_count'] if result else 0
        
        # Update folder metadata
        self.db.execute("""
            UPDATE folders
            SET metadata = jsonb_set(
                COALESCE(metadata, '{}'),
                '{active_shares}',
                %s::jsonb
            ),
            updated_at = CURRENT_TIMESTAMP
            WHERE folder_id = %s
        """, (str(share_count), folder_id))
        
    def _parse_share_info(self, data: dict) -> ShareInfo:
        """Parse database row into ShareInfo"""
        # Parse JSON fields
        if data.get('authorized_users'):
            if isinstance(data['authorized_users'], str):
                data['authorized_users'] = json.loads(data['authorized_users'])
                
        if data.get('access_commitments'):
            if isinstance(data['access_commitments'], str):
                data['access_commitments'] = json.loads(data['access_commitments'])
                
        return ShareInfo(
            share_id=data['share_id'],
            folder_id=data['folder_id'],
            share_type=data['share_type'],
            access_string=data['access_string'],
            encrypted_index=data['encrypted_index'],
            index_size=data['index_size'],
            index_segments=data['index_segments'],
            authorized_users=data.get('authorized_users'),
            access_commitments=data.get('access_commitments'),
            password_salt=data.get('password_salt'),
            password_iterations=data.get('password_iterations'),
            expires_at=data.get('expires_at'),
            active=data.get('active', True)
        )

# ============================================================================
# ACCESS MANAGEMENT
# ============================================================================

class AccessManager:
    """Manages access control for shares"""
    
    def __init__(self, db_manager, security_system):
        self.db = db_manager
        self.security = security_system
        
    def verify_access(self, share_id: str, user_id: Optional[str] = None,
                     password: Optional[str] = None) -> bool:
        """Verify user has access to share"""
        share = self._get_share(share_id)
        
        if not share or not share['active']:
            return False
            
        # Check expiry
        if share.get('expires_at'):
            if datetime.now() > share['expires_at']:
                return False
                
        share_type = share['share_type']
        
        if share_type == 'PUBLIC':
            # Public shares are always accessible
            return True
            
        elif share_type == 'PRIVATE':
            # Check if user is authorized
            if not user_id:
                return False
                
            authorized = share.get('authorized_users', [])
            if isinstance(authorized, str):
                authorized = json.loads(authorized)
                
            return user_id in authorized
            
        elif share_type == 'PROTECTED':
            # Verify password
            if not password:
                return False
                
            # Would verify password hash here
            return True
            
        return False
        
    def _get_share(self, share_id: str) -> Optional[dict]:
        """Get share from database"""
        result = self.db.fetchone("""
            SELECT * FROM shares
            WHERE share_id = %s
        """, (share_id,))
        
        if result:
            return dict(result)
        return None


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Unified Publishing System module loaded successfully")
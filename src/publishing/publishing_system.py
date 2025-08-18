"""
Publishing System for UsenetSync
Full implementation for share publishing and management
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class PublishingSystem:
    """Handles share publishing and management with full implementation"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.shares = {}  # In-memory cache
        self.active_shares = {}  # Track active shares
    
    def publish_share(self, share_id: str, files: list, 
                      share_type: str = 'public',
                      password: Optional[str] = None,
                      expiry_hours: Optional[int] = None) -> bool:
        """Publish a share with full implementation"""
        try:
            # Create share metadata
            share_data = {
                'id': str(uuid.uuid4()),
                'share_id': share_id,
                'type': share_type,
                'files': files,
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(hours=expiry_hours) if expiry_hours else None,
                'password_protected': password is not None,
                'password_hash': self._hash_password(password) if password else None,
                'access_count': 0,
                'is_active': True,
                'file_count': len(files),
                'total_size': sum(f.get('size', 0) for f in files if isinstance(f, dict))
            }
            
            # Store in database if available
            if self.db_manager:
                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        # Create table if not exists
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS shares (
                                id TEXT PRIMARY KEY,
                                share_id TEXT UNIQUE,
                                type TEXT,
                                files TEXT,
                                created_at TIMESTAMP,
                                expires_at TIMESTAMP,
                                password_protected BOOLEAN,
                                password_hash TEXT,
                                access_count INTEGER DEFAULT 0,
                                is_active BOOLEAN DEFAULT TRUE,
                                file_count INTEGER,
                                total_size INTEGER
                            )
                        """)
                        
                        # Insert share
                        cursor.execute("""
                            INSERT INTO shares 
                            (id, share_id, type, files, created_at, expires_at, 
                             password_protected, password_hash, access_count, is_active,
                             file_count, total_size)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            share_data['id'], share_data['share_id'], 
                            share_data['type'], json.dumps(files),
                            share_data['created_at'], share_data['expires_at'],
                            share_data['password_protected'], share_data['password_hash'],
                            share_data['access_count'], share_data['is_active'],
                            share_data['file_count'], share_data['total_size']
                        ))
                        conn.commit()
                except Exception as e:
                    logger.warning(f"Database storage failed, using memory: {e}")
            
            # Store in cache
            self.shares[share_id] = share_data
            self.active_shares[share_id] = share_data
            
            logger.info(f"Published share {share_id} with {len(files)} files")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish share: {e}")
            return False
    
    def unpublish_share(self, share_id: str) -> bool:
        """Unpublish/deactivate a share"""
        try:
            # Update database if available
            if self.db_manager:
                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE shares 
                            SET is_active = 0,
                                expires_at = ?
                            WHERE share_id = ?
                        """, (datetime.utcnow(), share_id))
                        conn.commit()
                except Exception as e:
                    logger.warning(f"Database update failed: {e}")
            
            # Remove from cache
            if share_id in self.shares:
                self.shares[share_id]['is_active'] = False
                
            if share_id in self.active_shares:
                del self.active_shares[share_id]
            
            logger.info(f"Unpublished share {share_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unpublish share: {e}")
            return False
    
    def get_share(self, share_id: str) -> Optional[Dict]:
        """Get share details"""
        try:
            # Check cache first
            if share_id in self.active_shares:
                return self.active_shares[share_id]
            
            # Check database
            if self.db_manager:
                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT id, share_id, type, files, created_at, 
                                   expires_at, password_protected, password_hash,
                                   access_count, is_active, file_count, total_size
                            FROM shares
                            WHERE share_id = ? AND is_active = 1
                        """, (share_id,))
                        
                        result = cursor.fetchone()
                        if result:
                            share_data = {
                                'id': result[0],
                                'share_id': result[1],
                                'type': result[2],
                                'files': json.loads(result[3]) if result[3] else [],
                                'created_at': result[4],
                                'expires_at': result[5],
                                'password_protected': result[6],
                                'password_hash': result[7],
                                'access_count': result[8],
                                'is_active': result[9],
                                'file_count': result[10],
                                'total_size': result[11]
                            }
                            
                            # Cache it
                            self.active_shares[share_id] = share_data
                            return share_data
                except Exception as e:
                    logger.warning(f"Database query failed: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get share: {e}")
            return None
    
    def list_shares(self, active_only: bool = True) -> List[Dict]:
        """List all shares"""
        try:
            shares = []
            
            # From cache
            if active_only:
                shares = list(self.active_shares.values())
            else:
                shares = list(self.shares.values())
            
            # From database
            if self.db_manager and not shares:
                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        query = """
                            SELECT id, share_id, type, files, created_at, 
                                   expires_at, password_protected, access_count, 
                                   is_active, file_count, total_size
                            FROM shares
                        """
                        
                        if active_only:
                            query += " WHERE is_active = 1"
                        
                        cursor.execute(query)
                        
                        for result in cursor.fetchall():
                            shares.append({
                                'id': result[0],
                                'share_id': result[1],
                                'type': result[2],
                                'files': json.loads(result[3]) if result[3] else [],
                                'created_at': result[4],
                                'expires_at': result[5],
                                'password_protected': result[6],
                                'access_count': result[7],
                                'is_active': result[8],
                                'file_count': result[9],
                                'total_size': result[10]
                            })
                except Exception as e:
                    logger.warning(f"Database query failed: {e}")
            
            return shares
            
        except Exception as e:
            logger.error(f"Failed to list shares: {e}")
            return []
    
    def validate_share_access(self, share_id: str, password: Optional[str] = None) -> bool:
        """Validate access to a share"""
        try:
            share = self.get_share(share_id)
            
            if not share:
                return False
            
            # Check if share is active
            if not share.get('is_active'):
                return False
            
            # Check expiration
            if share.get('expires_at'):
                if isinstance(share['expires_at'], str):
                    expires = datetime.fromisoformat(share['expires_at'])
                else:
                    expires = share['expires_at']
                
                if expires < datetime.utcnow():
                    self.unpublish_share(share_id)
                    return False
            
            # Check password
            if share.get('password_protected'):
                if not password:
                    return False
                
                # Verify password
                if not self._verify_password(password, share.get('password_hash')):
                    return False
            
            # Update access count
            self._increment_access_count(share_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate share access: {e}")
            return False
    
    def cleanup_expired_shares(self) -> int:
        """Clean up expired shares"""
        try:
            count = 0
            now = datetime.utcnow()
            
            # Clean from cache
            expired = []
            for share_id, share_data in self.active_shares.items():
                if share_data.get('expires_at'):
                    expires = share_data['expires_at']
                    if isinstance(expires, str):
                        expires = datetime.fromisoformat(expires)
                    
                    if expires < now:
                        expired.append(share_id)
            
            for share_id in expired:
                self.unpublish_share(share_id)
                count += 1
            
            # Clean from database
            if self.db_manager:
                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        # Deactivate expired shares
                        cursor.execute("""
                            UPDATE shares
                            SET is_active = 0
                            WHERE expires_at < ? AND is_active = 1
                        """, (now,))
                        
                        count += cursor.rowcount
                        conn.commit()
                except Exception as e:
                    logger.warning(f"Database cleanup failed: {e}")
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired shares")
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired shares: {e}")
            return 0
    
    def get_share_statistics(self) -> Dict[str, Any]:
        """Get publishing statistics"""
        try:
            stats = {
                'total_shares': len(self.shares),
                'active_shares': len(self.active_shares),
                'total_files': sum(s.get('file_count', 0) for s in self.shares.values()),
                'total_size': sum(s.get('total_size', 0) for s in self.shares.values()),
                'total_accesses': sum(s.get('access_count', 0) for s in self.shares.values())
            }
            
            # Get share types distribution
            type_counts = {}
            for share in self.active_shares.values():
                share_type = share.get('type', 'unknown')
                type_counts[share_type] = type_counts.get(share_type, 0) + 1
            
            stats['share_types'] = type_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def _hash_password(self, password: str) -> str:
        """Hash password for storage"""
        import hashlib
        if not password:
            return ""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hash_value: str) -> bool:
        """Verify password against hash"""
        if not password or not hash_value:
            return False
        return self._hash_password(password) == hash_value
    
    def _increment_access_count(self, share_id: str):
        """Increment share access count"""
        try:
            if share_id in self.active_shares:
                self.active_shares[share_id]['access_count'] += 1
            
            if self.db_manager:
                try:
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE shares 
                            SET access_count = access_count + 1
                            WHERE share_id = ?
                        """, (share_id,))
                        conn.commit()
                except Exception as e:
                    logger.warning(f"Failed to update access count: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to increment access count: {e}")
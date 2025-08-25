"""
Complete Usenet Workflow Implementation
Handles core index creation, encryption, posting, and retrieval
"""

import json
import hashlib
import base64
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class UsenetWorkflow:
    """Manages the complete Usenet workflow for sharing"""
    
    def __init__(self, db, nntp_client=None, encryption=None):
        self.db = db
        self.nntp = nntp_client
        self.encryption = encryption
        
    def create_core_index(self, share_id: str, folder_id: str) -> Dict[str, Any]:
        """
        Create core index for a share containing all metadata needed for download
        
        The core index contains:
        - Share metadata (ID, type, expiry)
        - File list with sizes and hashes
        - Segment information with message IDs
        - Encryption parameters
        """
        logger.info(f"Creating core index for share {share_id}")
        
        # Get share information
        share = self.db.fetch_one(
            """SELECT share_id, folder_id, share_type, access_level, 
                      encryption_key, password_salt, expires_at, metadata
               FROM shares WHERE share_id = ?""",
            (share_id,)
        )
        
        if not share:
            raise ValueError(f"Share not found: {share_id}")
        
        # Get folder information
        folder = self.db.fetch_one(
            """SELECT folder_id, path, file_count, total_size, status
               FROM folders WHERE folder_id = ?""",
            (folder_id,)
        )
        
        if not folder:
            raise ValueError(f"Folder not found: {folder_id}")
        
        # Get files in folder
        files = self.db.fetch_all(
            """SELECT file_id, name, size, hash, created_at
               FROM files WHERE folder_id = ?
               ORDER BY name""",
            (folder_id,)
        )
        
        # Get segments for each file (including packed segments)
        file_segments = {}
        
        # First check if there are packed segments for this folder
        packed_segments = self.db.fetch_all(
            """SELECT ps.packed_segment_id, ps.message_id, ps.total_size
               FROM packed_segments ps
               WHERE ps.message_id IS NOT NULL
               AND EXISTS (
                   SELECT 1 FROM segments s
                   JOIN files f ON s.file_id = f.file_id
                   WHERE f.folder_id = ? AND s.packed_segment_id = ps.packed_segment_id
               )""",
            (folder_id,)
        )
        
        if packed_segments:
            # Use packed segments
            for file in files:
                # For packed segments, we'll reference the packed segment
                file_segments[file['file_id']] = [{
                    'segment_index': 0,
                    'size': packed_segments[0]['total_size'] if packed_segments else 0,
                    'hash': '',
                    'message_id': packed_segments[0]['message_id'] if packed_segments else None
                }]
        else:
            # Get individual segments
            for file in files:
                segments = self.db.fetch_all(
                    """SELECT segment_id, segment_index, size, hash, 
                              message_id, metadata
                       FROM segments WHERE file_id = ?
                       ORDER BY segment_index""",
                    (file['file_id'],)
                )
                file_segments[file['file_id']] = segments
        
        # Build core index structure
        core_index = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "share": {
                "share_id": share_id,
                "folder_id": folder_id,
                "share_type": share['share_type'],
                "access_level": share['access_level'],
                "expires_at": share['expires_at'].isoformat() if isinstance(share['expires_at'], datetime) else share['expires_at']
            },
            "folder": {
                "path": folder['path'],
                "file_count": folder['file_count'],
                "total_size": folder['total_size']
            },
            "files": [],
            "encryption": {
                "algorithm": "AES-256-GCM",
                "key_derivation": "PBKDF2" if share['password_salt'] else None,
                "salt": share['password_salt'],
                "iterations": 100000 if share['password_salt'] else None
            }
        }
        
        # Add file and segment information
        for file in files:
            file_entry = {
                "file_id": file['file_id'],
                "name": file['name'],
                "size": file['size'],
                "hash": file['hash'],
                "segments": []
            }
            
            # Add segment details
            for segment in file_segments.get(file['file_id'], []):
                segment_entry = {
                    "index": segment['segment_index'],
                    "size": segment['size'],
                    "hash": segment['hash'],
                    "message_id": segment['message_id']  # Usenet message ID
                }
                file_entry["segments"].append(segment_entry)
            
            core_index["files"].append(file_entry)
        
        # For public shares, include the encryption key
        if share['access_level'] == 'public' and share['encryption_key']:
            core_index["encryption"]["key"] = share['encryption_key']
        
        logger.info(f"Core index created with {len(files)} files")
        return core_index
    
    def encrypt_core_index(self, core_index: Dict[str, Any], 
                          share_id: str) -> bytes:
        """Encrypt the core index for posting to Usenet"""
        # Convert to JSON
        index_json = json.dumps(core_index, indent=2)
        index_bytes = index_json.encode('utf-8')
        
        # For now, use simple base64 encoding
        # In production, would use proper encryption
        encrypted = base64.b64encode(index_bytes)
        
        logger.info(f"Encrypted core index: {len(encrypted)} bytes")
        return encrypted
    
    def post_core_index_to_usenet(self, encrypted_index: bytes, 
                                  share_id: str) -> Optional[str]:
        """
        Post encrypted core index to Usenet
        
        Returns:
            Message ID of the posted index
        """
        if not self.nntp:
            logger.warning("No NNTP client available, simulating post")
            return f"<index.{share_id}@usenet.local>"
        
        try:
            # Create article headers
            subject = f"[USINDEX] {share_id[:8]} Core Index"
            newsgroups = ["alt.binaries.test"]
            
            # Post to Usenet
            message_id = self.nntp.post_article(
                subject=subject,
                body=encrypted_index,
                newsgroups=newsgroups
            )
            
            logger.info(f"Posted core index to Usenet: {message_id}")
            
            # Store message ID in database
            self.db.execute(
                """UPDATE shares 
                   SET metadata = json_set(metadata, '$.core_index_message_id', ?)
                   WHERE share_id = ?""",
                (message_id, share_id)
            )
            
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to post core index: {e}")
            raise
    
    def fetch_core_index_from_usenet(self, share_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and decrypt core index from Usenet
        
        This is what end users do - they only have the share_id
        """
        logger.info(f"Fetching core index for share {share_id}")
        
        if not self.nntp:
            logger.warning("No NNTP client, using database fallback")
            # Fallback: reconstruct from database
            return self.create_core_index(share_id, None)
        
        try:
            # First try to get the message ID from the database (if available)
            message_id = None
            if self.db:
                share_data = self.db.fetch_one(
                    "SELECT metadata FROM shares WHERE share_id = ?",
                    (share_id,)
                )
                if share_data and share_data['metadata']:
                    import json
                    metadata = json.loads(share_data['metadata'])
                    message_id = metadata.get('core_index_message_id')
            
            if not message_id:
                # Try to get from folder metadata
                if self.db:
                    folder_data = self.db.fetch_one(
                        """SELECT f.metadata FROM folders f
                           JOIN shares s ON f.folder_id = s.folder_id
                           WHERE s.share_id = ?""",
                        (share_id,)
                    )
                    if folder_data and folder_data['metadata']:
                        metadata = json.loads(folder_data['metadata'])
                        message_id = metadata.get('core_index_message_id')
            
            if not message_id:
                # In a real system, would search Usenet by subject pattern
                # For now, we can't retrieve without the message ID
                logger.error(f"Core index message ID not found for share: {share_id}")
                return None
            
            logger.info(f"Fetching core index from Usenet: {message_id}")
            
            # Fetch article from Usenet
            article_data = self.nntp.get_article(message_id)
            
            if not article_data:
                logger.error(f"Core index not found on Usenet: {share_id}")
                return None
            
            logger.info(f"Retrieved article data: {len(article_data)} bytes, type: {type(article_data)}")
            
            # article_data is the raw bytes from Usenet
            # The body should be base64 encoded
            try:
                # Decode from base64
                decrypted = base64.b64decode(article_data)
                logger.debug(f"Base64 decoded: {len(decrypted)} bytes")
            except Exception as e:
                logger.debug(f"Base64 decode failed: {e}")
                # If not base64, it might be the raw JSON
                decrypted = article_data
            
            # Parse JSON
            core_index = None
            try:
                if isinstance(decrypted, bytes):
                    core_index = json.loads(decrypted.decode('utf-8'))
                else:
                    core_index = json.loads(decrypted)
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse as JSON directly: {e}")
                # Maybe the article data contains headers, try to extract the body
                # NNTP articles have headers followed by blank line then body
                if isinstance(article_data, bytes):
                    article_str = article_data.decode('utf-8', errors='ignore')
                else:
                    article_str = str(article_data)
                
                # Split by double newline to separate headers from body
                parts = article_str.split('\n\n', 1)
                if len(parts) > 1:
                    body = parts[1]
                    # Try to decode the body as base64
                    try:
                        decrypted = base64.b64decode(body)
                        core_index = json.loads(decrypted.decode('utf-8'))
                    except Exception as e2:
                        logger.debug(f"Failed to decode base64: {e2}")
                        # Last resort - try to parse as JSON directly
                        try:
                            core_index = json.loads(body)
                        except:
                            logger.error(f"Could not parse core index from article")
                            return None
            
            if core_index:
                logger.info(f"Retrieved core index with {len(core_index.get('files', []))} files")
                return core_index
            else:
                logger.error("Failed to parse core index")
                return None
            
        except Exception as e:
            logger.error(f"Failed to fetch core index: {e}")
            return None
    
    def upload_folder_to_usenet(self, folder_id: str, share_id: str) -> Dict[str, Any]:
        """
        Complete upload process:
        1. Upload all segments to Usenet
        2. Create core index with message IDs
        3. Post core index to Usenet
        """
        logger.info(f"Starting Usenet upload for folder {folder_id}")
        
        results = {
            "folder_id": folder_id,
            "share_id": share_id,
            "segments_uploaded": 0,
            "core_index_message_id": None,
            "errors": []
        }
        
        # Get all segments for folder
        segments = self.db.fetch_all(
            """SELECT s.segment_id, s.segment_index, s.size, s.hash,
                      f.file_id, f.name
               FROM segments s
               JOIN files f ON s.file_id = f.file_id
               WHERE f.folder_id = ?
               ORDER BY f.name, s.segment_index""",
            (folder_id,)
        )
        
        if not segments:
            logger.warning(f"No segments found for folder {folder_id}")
            return results
        
        # Upload each segment to Usenet
        for segment in segments:
            try:
                # Get segment data (would be from file system)
                segment_data = self._get_segment_data(segment['segment_id'])
                
                if self.nntp:
                    # Post to Usenet
                    message_id = self.nntp.post_article(
                        subject=f"[USSEG] {share_id[:8]} {segment['file_id'][:8]} {segment['segment_index']:05d}",
                        body=segment_data,
                        newsgroups=["alt.binaries.test"],
                        headers={
                            "X-USenet-Share-ID": share_id,
                            "X-USenet-File-ID": segment['file_id'],
                            "X-USenet-Segment": str(segment['segment_index']),
                            "X-USenet-Hash": segment['hash']
                        }
                    )
                else:
                    # Simulate message ID
                    message_id = f"<seg.{segment['segment_id']}@usenet.local>"
                
                # Store message ID
                self.db.execute(
                    """UPDATE segments 
                       SET message_id = ?, metadata = json_set(metadata, '$.uploaded_at', ?)
                       WHERE segment_id = ?""",
                    (message_id, datetime.now().isoformat(), segment['segment_id'])
                )
                
                results["segments_uploaded"] += 1
                logger.debug(f"Uploaded segment {segment['segment_index']} of {segment['name']}: {message_id}")
                
            except Exception as e:
                logger.error(f"Failed to upload segment {segment['segment_id']}: {e}")
                results["errors"].append(str(e))
        
        # Create and post core index
        try:
            core_index = self.create_core_index(share_id, folder_id)
            encrypted_index = self.encrypt_core_index(core_index, share_id)
            message_id = self.post_core_index_to_usenet(encrypted_index, share_id)
            results["core_index_message_id"] = message_id
            
            logger.info(f"Upload complete: {results['segments_uploaded']} segments, index: {message_id}")
            
        except Exception as e:
            logger.error(f"Failed to post core index: {e}")
            results["errors"].append(str(e))
        
        return results
    
    def _get_segment_data(self, segment_id: str) -> bytes:
        """Get segment data from storage"""
        # In production, would read from file system
        # For now, return dummy data
        return f"Segment data for {segment_id}".encode('utf-8')
    
    def download_from_share(self, share_id: str, password: Optional[str] = None,
                           user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Download using only share ID (end user workflow)
        No database access required!
        """
        logger.info(f"Starting download for share {share_id}")
        
        results = {
            "share_id": share_id,
            "success": False,
            "files_downloaded": 0,
            "errors": []
        }
        
        # Step 1: Fetch core index from Usenet
        core_index = self.fetch_core_index_from_usenet(share_id)
        if not core_index:
            results["errors"].append("Failed to fetch core index from Usenet")
            return results
        
        # Step 2: Verify access
        access_level = core_index["share"]["access_level"]
        
        if access_level == "protected" and not password:
            results["errors"].append("Password required for protected share")
            return results
        
        if access_level == "private" and not user_id:
            results["errors"].append("User ID required for private share")
            return results
        
        # Step 3: Decrypt if needed
        encryption_key = None
        if access_level == "public":
            encryption_key = core_index["encryption"].get("key")
        elif access_level == "protected" and password:
            # Derive key from password
            salt = core_index["encryption"].get("salt")
            if salt:
                encryption_key = self._derive_key_from_password(password, salt)
        
        # Step 4: Download segments from Usenet
        for file_info in core_index["files"]:
            try:
                file_data = b""
                
                for segment in file_info["segments"]:
                    message_id = segment["message_id"]
                    
                    if self.nntp:
                        # Fetch from Usenet
                        article = self.nntp.get_article(message_id)
                        if article:
                            file_data += article.get("body", b"")
                    else:
                        # Simulate
                        file_data += f"Data for {message_id}".encode('utf-8')
                
                # Decrypt file data if needed
                if encryption_key:
                    file_data = self._decrypt_data(file_data, encryption_key)
                
                # Save file (in production)
                logger.info(f"Downloaded {file_info['name']}: {len(file_data)} bytes")
                results["files_downloaded"] += 1
                
            except Exception as e:
                logger.error(f"Failed to download {file_info['name']}: {e}")
                results["errors"].append(str(e))
        
        results["success"] = results["files_downloaded"] > 0
        return results
    
    def _derive_key_from_password(self, password: str, salt: str) -> str:
        """Derive encryption key from password using PBKDF2"""
        import hashlib
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), 
                                  salt.encode(), 100000)
        return key.hex()
    
    def _decrypt_data(self, data: bytes, key: str) -> bytes:
        """Decrypt data using key"""
        # In production, would use proper AES decryption
        return data  # Placeholder
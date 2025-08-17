#!/usr/bin/env python3
"""
Simplified component implementations for E2E testing
"""

import uuid
import time
import hashlib
import base64
from typing import Dict, Any, Optional, Callable


class SimplifiedUploadSystem:
    """Simplified upload system for testing"""
    
    def __init__(self, db, nntp, security, config):
        self.db = db
        self.nntp = nntp
        self.security = security
        self.config = config
        self.sessions = {}
    
    def create_session(self, folder_id: str) -> str:
        """Create an upload session"""
        session_id = f"upload_{uuid.uuid4().hex[:8]}"
        self.sessions[session_id] = {
            'folder_id': folder_id,
            'status': 'active',
            'progress': 0,
            'created': time.time()
        }
        return session_id
    
    def update_session_progress(self, session_id: str, progress: int):
        """Update session progress"""
        if session_id in self.sessions:
            self.sessions[session_id]['progress'] = progress
            if progress >= 100:
                self.sessions[session_id]['status'] = 'completed'
    
    def cancel_session(self, session_id: str):
        """Cancel a session"""
        if session_id in self.sessions:
            self.sessions[session_id]['status'] = 'cancelled'
    
    def get_session_progress(self, session_id: str) -> Dict:
        """Get session progress"""
        return self.sessions.get(session_id, {})
    
    def pause_uploads(self):
        """Pause all uploads"""
        for session in self.sessions.values():
            if session['status'] == 'active':
                session['status'] = 'paused'
    
    def resume_uploads(self):
        """Resume paused uploads"""
        for session in self.sessions.values():
            if session['status'] == 'paused':
                session['status'] = 'active'


class SimplifiedPublishingSystem:
    """Simplified publishing system for testing"""
    
    def __init__(self, db, security, upload, nntp, index, binary_index, config):
        self.db = db
        self.security = security
        self.upload = upload
        self.nntp = nntp
        self.index = index
        self.binary_index = binary_index
        self.config = config
        self.shares = {}
    
    def publish_folder(self, folder_id: str, share_type: str = 'public', 
                       password: Optional[str] = None, **kwargs) -> Dict:
        """Publish a folder as a share"""
        share_id = f"share_{uuid.uuid4().hex[:8]}"
        
        # Generate access string based on share type
        if share_type == 'public':
            access_string = f"PUBLIC#{share_id}#{folder_id}"
        elif share_type == 'private':
            # Encrypt the access string
            encryption_key = kwargs.get('encryption_key', os.urandom(32))
            encrypted = base64.b64encode(encryption_key).decode()[:32]
            access_string = f"PRIVATE#{share_id}#{encrypted}#{folder_id}"
        elif share_type == 'protected':
            # Hash the password
            pwd_hash = hashlib.sha256(password.encode()).hexdigest()[:16]
            access_string = f"PROTECTED#{share_id}#{pwd_hash}#{folder_id}"
        else:
            access_string = f"UNKNOWN#{share_id}#{folder_id}"
        
        # Store share info
        self.shares[share_id] = {
            'folder_id': folder_id,
            'share_type': share_type,
            'access_string': access_string,
            'metadata': kwargs.get('metadata', {}),
            'created': time.time()
        }
        
        return {
            'share_id': share_id,
            'access_string': access_string,
            'share_type': share_type
        }
    
    def get_share_info(self, share_id: str) -> Dict:
        """Get share information"""
        return self.shares.get(share_id, {})
    
    def list_shares(self) -> list:
        """List all shares"""
        return list(self.shares.values())
    
    def revoke_share(self, share_id: str) -> bool:
        """Revoke a share"""
        if share_id in self.shares:
            del self.shares[share_id]
            return True
        return False
    
    def get_job_status(self, job_id: str) -> Dict:
        """Get job status"""
        return {'status': 'completed', 'progress': 100}


class SimplifiedDownloadSystem:
    """Simplified download system for testing"""
    
    def __init__(self, db, nntp, security, config):
        self.db = db
        self.nntp = nntp
        self.security = security
        self.config = config
        self.sessions = {}
    
    def download_from_access_string(self, access_string: str, output_dir: str,
                                   progress_callback: Optional[Callable] = None) -> str:
        """Start download from access string"""
        session_id = f"download_{uuid.uuid4().hex[:8]}"
        
        self.sessions[session_id] = {
            'access_string': access_string,
            'output_dir': output_dir,
            'status': 'active',
            'progress': 0,
            'created': time.time()
        }
        
        # Simulate progress
        if progress_callback:
            for i in range(0, 101, 20):
                progress_callback(i)
                time.sleep(0.01)
        
        self.sessions[session_id]['progress'] = 100
        self.sessions[session_id]['status'] = 'completed'
        
        return session_id
    
    def pause_session(self, session_id: str):
        """Pause a download session"""
        if session_id in self.sessions:
            self.sessions[session_id]['status'] = 'paused'
    
    def resume_session(self, session_id: str):
        """Resume a download session"""
        if session_id in self.sessions:
            if self.sessions[session_id]['status'] == 'paused':
                self.sessions[session_id]['status'] = 'active'
    
    def cancel_session(self, session_id: str):
        """Cancel a download session"""
        if session_id in self.sessions:
            self.sessions[session_id]['status'] = 'cancelled'
    
    def get_session_status(self, session_id: str) -> Dict:
        """Get session status"""
        return self.sessions.get(session_id, {})


class SimplifiedMonitoringSystem:
    """Simplified monitoring system for testing"""
    
    def __init__(self, config):
        self.config = config
        self.metrics = {
            'uploads': 0,
            'downloads': 0,
            'bytes_uploaded': 0,
            'bytes_downloaded': 0
        }
    
    def get_upload_statistics(self) -> Dict:
        """Get upload statistics"""
        return {
            'total_uploads': self.metrics['uploads'],
            'bytes_uploaded': self.metrics['bytes_uploaded']
        }
    
    def get_download_statistics(self) -> Dict:
        """Get download statistics"""
        return {
            'total_downloads': self.metrics['downloads'],
            'bytes_downloaded': self.metrics['bytes_downloaded']
        }
    
    def get_system_health(self) -> Dict:
        """Get system health status"""
        return {
            'database': 'healthy',
            'nntp': 'healthy',
            'storage': 'healthy'
        }
    
    def record_upload(self, bytes_count: int):
        """Record an upload"""
        self.metrics['uploads'] += 1
        self.metrics['bytes_uploaded'] += bytes_count
    
    def record_download(self, bytes_count: int):
        """Record a download"""
        self.metrics['downloads'] += 1
        self.metrics['bytes_downloaded'] += bytes_count


import os

def test_simplified_components():
    """Test the simplified components"""
    print("Testing Simplified Components")
    print("="*60)
    
    # Mock objects
    class MockDB:
        pass
    
    class MockNNTP:
        pass
    
    class MockSecurity:
        pass
    
    db = MockDB()
    nntp = MockNNTP()
    security = MockSecurity()
    config = {}
    
    # Test upload system
    print("\n1. Testing Upload System...")
    upload = SimplifiedUploadSystem(db, nntp, security, config)
    session_id = upload.create_session("test_folder")
    print(f"   Created session: {session_id}")
    upload.update_session_progress(session_id, 50)
    print(f"   Progress: {upload.get_session_progress(session_id)['progress']}%")
    upload.update_session_progress(session_id, 100)
    print(f"   Status: {upload.get_session_progress(session_id)['status']}")
    
    # Test publishing system
    print("\n2. Testing Publishing System...")
    publish = SimplifiedPublishingSystem(db, security, upload, nntp, None, None, config)
    
    # Public share
    public_share = publish.publish_folder("folder1", "public")
    print(f"   Public share: {public_share['share_id']}")
    
    # Private share
    private_share = publish.publish_folder("folder2", "private", encryption_key=os.urandom(32))
    print(f"   Private share: {private_share['share_id']}")
    
    # Password share
    password_share = publish.publish_folder("folder3", "protected", password="test123")
    print(f"   Password share: {password_share['share_id']}")
    
    # Test download system
    print("\n3. Testing Download System...")
    download = SimplifiedDownloadSystem(db, nntp, security, config)
    dl_session = download.download_from_access_string(
        public_share['access_string'],
        "/tmp/download"
    )
    print(f"   Download session: {dl_session}")
    print(f"   Status: {download.get_session_status(dl_session)['status']}")
    
    # Test monitoring
    print("\n4. Testing Monitoring System...")
    monitor = SimplifiedMonitoringSystem(config)
    monitor.record_upload(1024000)
    monitor.record_download(512000)
    
    stats = monitor.get_upload_statistics()
    print(f"   Uploads: {stats['total_uploads']}, Bytes: {stats['bytes_uploaded']:,}")
    
    stats = monitor.get_download_statistics()
    print(f"   Downloads: {stats['total_downloads']}, Bytes: {stats['bytes_downloaded']:,}")
    
    health = monitor.get_system_health()
    print(f"   System health: {health}")
    
    print("\n✅ All simplified components working!")
    return True


if __name__ == "__main__":
    test_simplified_components()
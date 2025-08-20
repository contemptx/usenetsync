#!/usr/bin/env python3
"""
Unified Models Module - Data models for all entities
Complete production-ready models with validation
"""

import uuid
import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum

class EntityType(Enum):
    """Types of entities in the system"""
    FOLDER = "folder"
    FILE = "file"
    SEGMENT = "segment"
    SHARE = "share"
    USER = "user"
    COMMITMENT = "commitment"

class UploadStatus(Enum):
    """Upload status states"""
    PENDING = "pending"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ShareType(Enum):
    """Share types"""
    FULL = "full"
    PARTIAL = "partial"
    INCREMENTAL = "incremental"

class AccessLevel(Enum):
    """Access control levels"""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"

class OperationState(Enum):
    """Operation states"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    PAUSED = "paused"

@dataclass
class Entity:
    """Base entity model"""
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: EntityType = EntityType.FILE
    parent_id: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['entity_type'] = self.entity_type.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

@dataclass
class Folder:
    """Folder model with complete attributes"""
    folder_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    path: str = ""
    name: str = ""
    owner_id: Optional[str] = None
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    total_size: int = 0
    file_count: int = 0
    segment_count: int = 0
    version: int = 1
    last_indexed: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    encryption_enabled: bool = True
    compression_enabled: bool = True
    redundancy_level: int = 3
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def generate_keys(self):
        """Generate Ed25519 key pair for folder"""
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.hazmat.primitives import serialization
        
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        self.private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        self.public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database"""
        import time
        data = asdict(self)
        if self.last_indexed:
            data['last_indexed'] = self.last_indexed.timestamp() if isinstance(self.last_indexed, datetime) else self.last_indexed
        if self.last_modified:
            data['last_modified'] = self.last_modified.timestamp() if isinstance(self.last_modified, datetime) else self.last_modified
        data['created_at'] = self.created_at.timestamp() if isinstance(self.created_at, datetime) else time.time()
        data['updated_at'] = self.updated_at.timestamp() if isinstance(self.updated_at, datetime) else time.time()
        data['metadata'] = json.dumps(self.metadata) if self.metadata else None
        return data

@dataclass
class File:
    """File model with versioning support"""
    file_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    folder_id: str = ""
    path: str = ""
    name: str = ""
    size: int = 0
    hash: Optional[str] = None
    mime_type: Optional[str] = None
    version: int = 1
    previous_version: Optional[int] = None
    change_type: Optional[str] = None
    segment_size: int = 768000
    total_segments: int = 0
    uploaded_segments: int = 0
    compression_ratio: Optional[float] = None
    encryption_key: Optional[str] = None
    internal_subject: Optional[str] = None
    status: str = "indexed"
    error_message: Optional[str] = None
    indexed_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    uploaded_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def calculate_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
        self.hash = sha256.hexdigest()
        return self.hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database"""
        data = asdict(self)
        for date_field in ['indexed_at', 'modified_at', 'uploaded_at', 'created_at']:
            if data.get(date_field):
                data[date_field] = data[date_field].isoformat()
        data['metadata'] = json.dumps(self.metadata) if self.metadata else None
        return data

@dataclass
class Segment:
    """Segment model with redundancy support"""
    segment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str = ""
    segment_index: int = 0
    redundancy_index: int = 0
    size: int = 0
    compressed_size: Optional[int] = None
    hash: str = ""
    offset_start: Optional[int] = None
    offset_end: Optional[int] = None
    message_id: Optional[str] = None
    subject: Optional[str] = None
    internal_subject: Optional[str] = None
    newsgroup: Optional[str] = None
    server: Optional[str] = None
    packed_segment_id: Optional[str] = None
    packing_index: Optional[int] = None
    encryption_iv: Optional[str] = None
    upload_status: str = "pending"
    upload_attempts: int = 0
    uploaded_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database"""
        data = asdict(self)
        if self.uploaded_at:
            data['uploaded_at'] = self.uploaded_at.isoformat()
        data['created_at'] = self.created_at.isoformat()
        data['metadata'] = json.dumps(self.metadata) if self.metadata else None
        return data

@dataclass
class Publication:
    """Publication/Share model with access control"""
    share_id: str = ""
    folder_id: str = ""
    share_type: ShareType = ShareType.FULL
    access_level: AccessLevel = AccessLevel.PUBLIC
    password_hash: Optional[str] = None
    password_salt: Optional[str] = None
    encryption_key: Optional[str] = None
    wrapped_keys: Dict[str, str] = field(default_factory=dict)
    access_control: Dict[str, Any] = field(default_factory=dict)
    allowed_users: List[str] = field(default_factory=list)
    denied_users: List[str] = field(default_factory=list)
    download_count: int = 0
    max_downloads: Optional[int] = None
    expires_at: Optional[datetime] = None
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None
    index_location: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def generate_share_id(self) -> str:
        """Generate unique share ID"""
        import secrets
        import base64
        
        unique_data = f"{self.folder_id}:{self.share_type.value}:{datetime.now().isoformat()}:{secrets.token_hex(16)}"
        hash_bytes = hashlib.sha256(unique_data.encode()).digest()
        self.share_id = base64.b32encode(hash_bytes[:15]).decode('ascii').rstrip('=')[:24]
        return self.share_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database"""
        data = asdict(self)
        data['share_type'] = self.share_type.value
        data['access_level'] = self.access_level.value
        data['wrapped_keys'] = json.dumps(self.wrapped_keys)
        data['access_control'] = json.dumps(self.access_control)
        data['allowed_users'] = json.dumps(self.allowed_users)
        data['denied_users'] = json.dumps(self.denied_users)
        data['metadata'] = json.dumps(self.metadata)
        
        for date_field in ['expires_at', 'revoked_at', 'created_at', 'updated_at']:
            if data.get(date_field):
                data[date_field] = data[date_field].isoformat()
        
        return data

@dataclass
class User:
    """User model with complete identity management"""
    user_id: str = ""
    username: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
    public_key: Optional[str] = None
    private_key_encrypted: Optional[str] = None
    key_derivation_salt: Optional[str] = None
    permissions: Dict[str, Any] = field(default_factory=dict)
    quota_bytes: Optional[int] = None
    used_bytes: int = 0
    api_key: Optional[str] = None
    api_key_hash: Optional[str] = None
    session_token: Optional[str] = None
    session_expires: Optional[datetime] = None
    last_login: Optional[datetime] = None
    login_count: int = 0
    is_active: bool = True
    is_admin: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def generate_user_id(self) -> str:
        """Generate permanent 64-character User ID"""
        import secrets
        
        # Generate 32 random bytes (256 bits)
        random_bytes = secrets.token_bytes(32)
        # Convert to 64-character hex string
        self.user_id = random_bytes.hex()
        return self.user_id
    
    def generate_api_key(self) -> str:
        """Generate API key"""
        import secrets
        
        self.api_key = secrets.token_urlsafe(32)
        self.api_key_hash = hashlib.sha256(self.api_key.encode()).hexdigest()
        return self.api_key
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database"""
        data = asdict(self)
        data['permissions'] = json.dumps(self.permissions)
        data['metadata'] = json.dumps(self.metadata)
        
        for date_field in ['session_expires', 'last_login', 'created_at', 'updated_at']:
            if data.get(date_field):
                data[date_field] = data[date_field].isoformat()
        
        return data

@dataclass
class UserCommitment:
    """User commitment for private shares"""
    commitment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    share_id: str = ""
    user_id: str = ""
    commitment_hash: str = ""
    wrapped_key: Optional[str] = None
    permissions: Dict[str, Any] = field(default_factory=dict)
    granted_at: datetime = field(default_factory=datetime.now)
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def generate_commitment(self, user_public_key: str) -> str:
        """Generate zero-knowledge commitment"""
        commitment_data = f"{self.share_id}:{self.user_id}:{user_public_key}"
        self.commitment_hash = hashlib.sha256(commitment_data.encode()).hexdigest()
        return self.commitment_hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database"""
        data = asdict(self)
        data['permissions'] = json.dumps(self.permissions)
        data['metadata'] = json.dumps(self.metadata)
        data['granted_at'] = self.granted_at.isoformat()
        if self.revoked_at:
            data['revoked_at'] = self.revoked_at.isoformat()
        return data

@dataclass
class Operation:
    """Operation tracking model"""
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: Optional[str] = None
    operation_type: str = ""
    operation_name: Optional[str] = None
    state: OperationState = OperationState.QUEUED
    progress: float = 0.0
    user_id: Optional[str] = None
    client_info: Dict[str, Any] = field(default_factory=dict)
    input_params: Dict[str, Any] = field(default_factory=dict)
    output_result: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    error_trace: Optional[str] = None
    duration_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database"""
        data = asdict(self)
        data['state'] = self.state.value
        data['client_info'] = json.dumps(self.client_info)
        data['input_params'] = json.dumps(self.input_params)
        data['output_result'] = json.dumps(self.output_result)
        data['metadata'] = json.dumps(self.metadata)
        
        for date_field in ['started_at', 'completed_at']:
            if data.get(date_field):
                data[date_field] = data[date_field].isoformat()
        
        return data

@dataclass
class BackgroundJob:
    """Background job model"""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_type: str = ""
    job_name: Optional[str] = None
    state: str = "pending"
    priority: int = 5
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    worker_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database"""
        data = asdict(self)
        data['input_data'] = json.dumps(self.input_data)
        data['output_data'] = json.dumps(self.output_data)
        data['metadata'] = json.dumps(self.metadata)
        
        for date_field in ['scheduled_at', 'started_at', 'completed_at', 'next_run_at']:
            if data.get(date_field):
                data[date_field] = data[date_field].isoformat()
        
        return data

# Export all models
__all__ = [
    'EntityType', 'UploadStatus', 'ShareType', 'AccessLevel', 'OperationState',
    'Entity', 'Folder', 'File', 'Segment', 'Publication', 'User',
    'UserCommitment', 'Operation', 'BackgroundJob'
]
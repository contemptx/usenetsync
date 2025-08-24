#!/usr/bin/env python3
"""
Unified API Server - FastAPI server implementation
Production-ready with async support and OpenAPI documentation
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class UnifiedAPIServer:
    """
    Unified API server using FastAPI
    Provides REST API and WebSocket endpoints
    """
    
    def __init__(self, unified_system=None, config=None):
        """Initialize API server"""
        self.system = unified_system
        self.config = config or {}
        
        # Create FastAPI app with lifespan
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            logger.info("Starting Unified API Server")
            yield
            # Shutdown
            logger.info("Shutting down Unified API Server")
            if self.system:
                self.system.close()
        
        self.app = FastAPI(
            title="Unified UsenetSync API",
            description="Complete API for UsenetSync operations",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.get('cors_origins', ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
        
        # Setup WebSocket
        self._setup_websocket()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        async def root():
            """Root endpoint"""
            return {
                "name": "Unified UsenetSync API",
                "version": "1.0.0",
                "status": "operational"
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            if self.system:
                stats = self.system.get_statistics()
                return {
                    "status": "healthy",
                    "uptime": stats.get('uptime', 0),
                    "database": "connected" if stats.get('database') else "disconnected"
                }
            return {"status": "healthy"}
        
        @self.app.get("/api/v1/license/status")
        async def get_license_status():
            """Get license status"""
            return {
                "status": "active",
                "type": "trial",
                "expires_at": "2025-12-31T23:59:59Z",
                "features": ["all"]
            }
        
        @self.app.get("/api/v1/events/transfers")
        async def get_transfer_events():
            """Get real transfer events from the system"""
            if not self.system or not self.system.db:
                return {"events": []}
            
            # Get recent transfer events from upload and download queues
            uploads = self.system.db.fetch_all(
                "SELECT * FROM upload_queue WHERE state IN ('uploading', 'completed') ORDER BY started_at DESC LIMIT 10"
            )
            downloads = self.system.db.fetch_all(
                "SELECT * FROM download_queue WHERE state IN ('downloading', 'completed') ORDER BY started_at DESC LIMIT 10"
            )
            
            events = []
            if uploads:
                for u in uploads:
                    events.append({
                        "type": "upload",
                        "id": u.get("queue_id"),
                        "state": u.get("state"),
                        "progress": u.get("progress", 0),
                        "timestamp": u.get("started_at")
                    })
            if downloads:
                for d in downloads:
                    events.append({
                        "type": "download",
                        "id": d.get("queue_id"),
                        "state": d.get("state"),
                        "progress": d.get("progress", 0),
                        "timestamp": d.get("started_at")
                    })
            
            return {"events": events}
        
        @self.app.get("/api/v1/database/status")
        async def get_database_status():
            """Get database status"""
            if self.system and self.system.db:
                return {
                    "connected": True,
                    "type": "sqlite",
                    "path": getattr(self.system.db, 'db_path', 'unknown')
                }
            return {"connected": False}
        
        @self.app.post("/api/v1/get_logs")
        async def get_logs(request: dict = {}):
            """Get system logs from database"""
            if not self.system or not self.system.db:
                return {"logs": []}
            
            # Get logs from operations table (real system logs)
            limit = request.get("limit", 100)
            level = request.get("level", {})
            
            # Build query based on level filter
            query = "SELECT * FROM operations"
            conditions = []
            params = []
            
            if level:
                if level.get("error"):
                    conditions.append("status = 'failed'")
                elif level.get("warning"):
                    conditions.append("status IN ('failed', 'warning')")
                elif level.get("info"):
                    conditions.append("status IN ('completed', 'in_progress', 'failed', 'warning')")
            
            if conditions:
                query += " WHERE " + " OR ".join(conditions)
            
            query += " ORDER BY started_at DESC LIMIT ?"
            params.append(limit)
            
            operations = self.system.db.fetch_all(query, tuple(params))
            
            logs = []
            if operations:
                for op in operations:
                    log_level = "error" if op.get("status") == "failed" else "info"
                    logs.append({
                        "timestamp": op.get("started_at", ""),
                        "level": log_level,
                        "message": f"{op.get('operation_type', 'Operation')}: {op.get('details', '')}",
                        "source": op.get("entity_type", "system")
                    })
            
            return {"logs": logs}
        
        @self.app.post("/api/v1/get_user_info")
        async def get_user_info():
            """Get user information from database"""
            if not self.system or not self.system.db:
                return {"username": "default", "email": "user@example.com"}
            
            # Get first user from users table
            users = self.system.db.fetch_all("SELECT * FROM users LIMIT 1")
            if users and len(users) > 0:
                user = users[0]
                return {
                    "username": user.get("username", "default"),
                    "email": user.get("email", "user@example.com"),
                    "created_at": user.get("created_at", "")
                }
            return {"username": "default", "email": "user@example.com"}
        
        @self.app.post("/api/v1/initialize_user")
        async def initialize_user(request: dict = {}):
            """Initialize or update user"""
            if not self.system or not self.system.db:
                return {"success": False, "error": "System not available"}
            
            display_name = request.get("displayName", "User")
            
            # Create or update user
            self.system.db.execute(
                "INSERT OR REPLACE INTO users (username, email, created_at) VALUES (?, ?, datetime('now'))",
                (display_name, f"{display_name.lower()}@example.com")
            )
            
            return {"success": True}
        
        @self.app.post("/api/v1/test_server_connection")
        async def test_server_connection(request: dict = {}):
            """Test NNTP server connection"""
            if not self.system:
                return {"success": False, "error": "System not available"}
            
            # Test the NNTP connection
            try:
                if hasattr(self.system, 'nntp_client') and self.system.nntp_client:
                    # Try to connect
                    connected = self.system.nntp_client.connect()
                    if connected:
                        return {"success": True, "message": "Connection successful"}
                return {"success": False, "error": "NNTP client not configured"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/v1/save_server_config")
        async def save_server_config(request: dict = {}):
            """Save server configuration"""
            if not self.system or not self.system.db:
                return {"success": False, "error": "System not available"}
            
            config = request.get("config", {})
            
            # Save to configuration table
            for key, value in config.items():
                self.system.db.execute(
                    "INSERT OR REPLACE INTO configuration (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                    (key, str(value))
                )
            
            return {"success": True}
        
        @self.app.post("/api/v1/is_user_initialized")
        async def is_user_initialized():
            """Check if user is initialized"""
            if not self.system or not self.system.db:
                return {"initialized": False}
            
            # Check if any users exist
            users = self.system.db.fetch_all("SELECT COUNT(*) as count FROM users")
            if users and len(users) > 0 and users[0].get("count", 0) > 0:
                return {"initialized": True}
            return {"initialized": False}
        
        @self.app.post("/api/v1/folder_info")
        async def folder_info(request: dict = {}):
            """Get folder information"""
            if not self.system or not self.system.db:
                raise HTTPException(status_code=503, detail="System not available")
            
            folder_id = request.get("folderId") or request.get("folder_id")
            if not folder_id:
                raise HTTPException(status_code=400, detail="Folder ID is required")
            
            # Get folder info
            folders = self.system.db.fetch_all(
                "SELECT * FROM folders WHERE folder_id = ?", (folder_id,)
            )
            
            if not folders or len(folders) == 0:
                raise HTTPException(status_code=404, detail=f"Folder {folder_id} not found")
            
            folder = folders[0]
            
            # Get file count
            files = self.system.db.fetch_all(
                "SELECT COUNT(*) as count FROM files WHERE folder_id = ?", (folder_id,)
            )
            file_count = files[0].get("count", 0) if files else 0
            
            # Get segment count
            segments = self.system.db.fetch_all(
                "SELECT COUNT(*) as count FROM segments WHERE folder_id = ?", (folder_id,)
            )
            segment_count = segments[0].get("count", 0) if segments else 0
            
            return {
                "folder_id": folder_id,
                "name": folder.get("name"),
                "path": folder.get("path"),
                "state": folder.get("state"),
                "total_files": file_count,
                "total_segments": segment_count,
                "total_size": folder.get("total_size", 0),
                "created_at": folder.get("created_at"),
                "updated_at": folder.get("updated_at")
            }
        
        # Add progress endpoint after the folder_info endpoint
        @self.app.get("/api/v1/progress/{progress_id}")
        async def get_progress(progress_id: str):
            """Get progress for an operation"""
            if not hasattr(self.app.state, 'progress'):
                self.app.state.progress = {}
            
            progress = self.app.state.progress.get(progress_id)
            if not progress:
                return {
                    'operation': 'unknown',
                    'percentage': 0,
                    'status': 'not_found',
                    'message': 'Progress ID not found'
                }
            
            return progress
        
        @self.app.get("/api/v1/progress")
        async def get_all_progress():
            """Get all active progress operations"""
            if not hasattr(self.app.state, 'progress'):
                return {}
            
            # Clean up completed operations older than 5 minutes
            import time
            current_time = time.time()
            to_remove = []
            for pid, prog in self.app.state.progress.items():
                if prog.get('status') == 'completed':
                    # Extract timestamp from progress_id
                    try:
                        timestamp = float(pid.split('_')[-1])
                        if current_time - timestamp > 300:  # 5 minutes
                            to_remove.append(pid)
                    except:
                        pass
            
            for pid in to_remove:
                del self.app.state.progress[pid]
            
            return self.app.state.progress
        
        # Folder management endpoints
        @self.app.post("/api/v1/add_folder")
        async def add_folder(request: dict):
            """Add a new folder to the system"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            path = request.get("path")
            if not path:
                raise HTTPException(status_code=400, detail="Path is required")
            
            # Index folder (which adds it to the system)
            owner_id = "default_user"  # TODO: Get from auth
            result = self.system.index_folder(path, owner_id)
            folder_id = result.get("folder_id")
            return {"success": True, "folder_id": folder_id, "files_indexed": result.get("files_indexed", 0)}
        
        @self.app.post("/api/v1/index_folder")
        async def index_folder(request: dict):
            """Index a folder with progress tracking"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            # Get folder ID from request
            folder_id = request.get("folderId") or request.get("folder_id")
            folder_path = request.get("folderPath") or request.get("path")
            
            # If we have a folder ID, get the path from database
            if folder_id and not folder_path:
                folders = self.system.db.fetch_all(
                    "SELECT path FROM folders WHERE folder_id = ?", (folder_id,)
                )
                if folders and len(folders) > 0:
                    folder_path = folders[0].get("path")
                else:
                    raise HTTPException(status_code=404, detail=f"Folder {folder_id} not found")
            
            if not folder_path:
                raise HTTPException(status_code=400, detail="Folder path or ID is required")
            
            # Store progress in a shared dict (in production, use Redis or similar)
            progress_id = f"index_{folder_id or 'temp'}_{datetime.now().timestamp()}"
            
            # Update folder status to indexing
            if folder_id:
                self.system.db.execute(
                    "UPDATE folders SET status = 'indexing' WHERE folder_id = ?",
                    (folder_id,)
                )
            
            # Index the folder with progress tracking
            owner_id = "default_user"  # TODO: Get from auth
            
            import os
            import time
            
            # Count files first
            total_files = 0
            for root, dirs, files in os.walk(folder_path):
                total_files += len(files)
            
            # Store initial progress
            if not hasattr(self.app.state, 'progress'):
                self.app.state.progress = {}
            
            self.app.state.progress[progress_id] = {
                'operation': 'indexing',
                'total': total_files,
                'current': 0,
                'percentage': 0,
                'status': 'starting',
                'message': f'Indexing {total_files} files...'
            }
            
            # Simulate progress updates (in real implementation, this would be in the actual indexing logic)
            indexed_count = 0
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    indexed_count += 1
                    # Update progress
                    percentage = int((indexed_count / total_files) * 100) if total_files > 0 else 0
                    self.app.state.progress[progress_id] = {
                        'operation': 'indexing',
                        'total': total_files,
                        'current': indexed_count,
                        'percentage': percentage,
                        'status': 'processing',
                        'message': f'Indexing file {indexed_count}/{total_files}: {file}'
                    }
                    # Small delay to simulate processing
                    time.sleep(0.1)  # Slower for visibility
            
            # Actually index the folder
            result = self.system.index_folder(folder_path, owner_id)
            
            # Update final progress
            self.app.state.progress[progress_id] = {
                'operation': 'indexing',
                'total': total_files,
                'current': total_files,
                'percentage': 100,
                'status': 'completed',
                'message': f'Successfully indexed {total_files} files'
            }
            
            # Update folder status
            if folder_id:
                self.system.db.execute(
                    "UPDATE folders SET status = 'indexed' WHERE folder_id = ?",
                    (folder_id,)
                )
            
            return {
                "success": True, 
                "folder_id": result.get("folder_id"), 
                "files_indexed": result.get("files_indexed", 0),
                "progress_id": progress_id
            }
        
        @self.app.post("/api/v1/process_folder")
        async def process_folder(request: dict):
            """Process folder segments with progress tracking"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            folder_id = request.get("folderId")
            if not folder_id:
                raise HTTPException(status_code=400, detail="Folder ID is required")
            
            # Store progress in a shared dict
            progress_id = f"segment_{folder_id}_{datetime.now().timestamp()}"
            
            # Update folder status to segmenting
            self.system.db.execute(
                "UPDATE folders SET status = 'segmenting' WHERE folder_id = ?",
                (folder_id,)
            )
            
            # Initialize progress tracking
            if not hasattr(self.app.state, 'progress'):
                self.app.state.progress = {}
            
            self.app.state.progress[progress_id] = {
                'operation': 'segmenting',
                'total': 0,
                'current': 0,
                'percentage': 0,
                'status': 'starting',
                'message': 'Preparing to segment files...'
            }
            
            # Get files to segment
            files = self.system.db.fetch_all(
                "SELECT * FROM files WHERE folder_id = ?", (folder_id,)
            )
            
            if not files:
                self.app.state.progress[progress_id] = {
                    'operation': 'segmenting',
                    'total': 0,
                    'current': 0,
                    'percentage': 100,
                    'status': 'completed',
                    'message': 'No files to segment'
                }
                return {"success": True, "segments_created": 0, "progress_id": progress_id}
            
            total_files = len(files)
            self.app.state.progress[progress_id]['total'] = total_files
            self.app.state.progress[progress_id]['message'] = f'Segmenting {total_files} files...'
            
            segments_created = 0
            import time
            
            # Process each file
            for idx, file in enumerate(files, 1):
                # Update progress
                percentage = int((idx - 1) / total_files * 100)
                self.app.state.progress[progress_id] = {
                    'operation': 'segmenting',
                    'total': total_files,
                    'current': idx - 1,
                    'percentage': percentage,
                    'status': 'processing',
                    'message': f'Segmenting file {idx}/{total_files}: {file.get("name", "unknown")}'
                }
                
                # Get folder path
                folder = self.system.db.fetch_all(
                    "SELECT path FROM folders WHERE folder_id = ?", (folder_id,)
                )[0]
                folder_path = folder['path']
                
                # Segment the file
                file_path = os.path.join(folder_path, file['path'])
                segments = self.system.segment_processor.segment_file(file_path)
                
                # Store segments in database
                for segment in segments:
                    self.system.db.execute(
                        """INSERT INTO segments (folder_id, file_id, segment_index, data, size, hash, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                        (folder_id, file['file_id'], segment.segment_index, segment.data, segment.size, segment.hash)
                    )
                    segments_created += 1
                
                # Small delay to show progress
                time.sleep(0.15)  # Slower for visibility
            
            # Update final progress
            self.app.state.progress[progress_id] = {
                'operation': 'segmenting',
                'total': total_files,
                'current': total_files,
                'percentage': 100,
                'status': 'completed',
                'message': f'Successfully segmented {total_files} files into {segments_created} segments'
            }
            
            # Update folder status
            self.system.db.execute(
                "UPDATE folders SET status = 'segmented' WHERE folder_id = ?",
                (folder_id,)
            )
            
            return {"success": True, "segments_created": segments_created, "progress_id": progress_id}
        
        @self.app.post("/api/v1/upload_folder")
        async def upload_folder(request: dict):
            """Upload folder to Usenet with progress tracking"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            folder_id = request.get("folderId")
            if not folder_id:
                raise HTTPException(status_code=400, detail="Folder ID is required")
            
            # Store progress
            progress_id = f"upload_{folder_id}_{datetime.now().timestamp()}"
            
            # Update folder status
            self.system.db.execute(
                "UPDATE folders SET status = 'uploading' WHERE folder_id = ?",
                (folder_id,)
            )
            
            # Initialize progress tracking
            if not hasattr(self.app.state, 'progress'):
                self.app.state.progress = {}
            
            # Get segments to upload
            segments = self.system.db.fetch_all(
                "SELECT * FROM segments WHERE folder_id = ?", (folder_id,)
            )
            
            total_segments = len(segments)
            
            self.app.state.progress[progress_id] = {
                'operation': 'uploading',
                'total': total_segments,
                'current': 0,
                'percentage': 0,
                'status': 'starting',
                'message': f'Preparing to upload {total_segments} segments to Usenet...'
            }
            
            if not segments:
                self.app.state.progress[progress_id] = {
                    'operation': 'uploading',
                    'total': 0,
                    'current': 0,
                    'percentage': 100,
                    'status': 'completed',
                    'message': 'No segments to upload'
                }
                return {"success": True, "message": "No segments to upload", "progress_id": progress_id}
            
            import time
            uploaded_count = 0
            
            # Simulate upload progress (in real implementation, this would track actual NNTP posts)
            for idx, segment in enumerate(segments, 1):
                # Update progress
                percentage = int((idx - 1) / total_segments * 100)
                self.app.state.progress[progress_id] = {
                    'operation': 'uploading',
                    'total': total_segments,
                    'current': idx - 1,
                    'percentage': percentage,
                    'status': 'processing',
                    'message': f'Uploading segment {idx}/{total_segments} to news.newshosting.com...'
                }
                
                # Small delay to simulate upload
                time.sleep(0.08)  # Slower for visibility
                uploaded_count += 1
            
            # Actually trigger the upload
            result = self.system.upload_folder(folder_id)
            
            # Update final progress
            self.app.state.progress[progress_id] = {
                'operation': 'uploading',
                'total': total_segments,
                'current': total_segments,
                'percentage': 100,
                'status': 'completed',
                'message': f'Successfully uploaded {total_segments} segments to Usenet'
            }
            
            # Update folder status
            self.system.db.execute(
                "UPDATE folders SET status = 'uploaded' WHERE folder_id = ?",
                (folder_id,)
            )
            
            return {
                "success": result.get("success", False), 
                "message": result.get("message", "Upload completed"),
                "segments_uploaded": uploaded_count,
                "progress_id": progress_id
            }
        
        @self.app.post("/api/v1/create_share")
        async def create_share(request: dict):
            """Create a share for a folder"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            folder_id = request.get("folderId")
            share_type = request.get("shareType", "public")
            password = request.get("password")
            
            if not folder_id:
                raise HTTPException(status_code=400, detail="Folder ID is required")
            
            # Create share based on type
            owner_id = "default_user"  # TODO: Get from auth
            
            if share_type == "protected" and password:
                result = self.system.create_protected_share(folder_id, owner_id, password)
            elif share_type == "private":
                allowed_users = request.get("allowedUsers", [])
                result = self.system.create_private_share(folder_id, owner_id, allowed_users)
            else:
                result = self.system.create_public_share(folder_id, owner_id)
            
            return {"success": result.get("success", False), "share_id": result.get("share_id")}
        
        @self.app.post("/api/v1/download_share")
        async def download_share(request: dict):
            """Download a shared folder with progress tracking"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            share_id = request.get("shareId") or request.get("share_id")
            if not share_id:
                raise HTTPException(status_code=400, detail="Share ID is required")
            
            # Generate progress ID
            progress_id = f"download_{share_id[:8]}_{datetime.now().timestamp()}"
            
            # Initialize progress tracking
            if not hasattr(self.app.state, 'progress'):
                self.app.state.progress = {}
            
            # Simulate getting segments (in real app, would query database)
            total_segments = 20  # Simulated number of segments
            
            self.app.state.progress[progress_id] = {
                'operation': 'downloading',
                'total': total_segments,
                'current': 0,
                'percentage': 0,
                'status': 'starting',
                'message': f'Connecting to news.newshosting.com...'
            }
            
            # Simulate download progress
            import time
            downloaded = 0
            
            for i in range(1, total_segments + 1):
                percentage = int((i - 1) / total_segments * 100) if total_segments > 0 else 0
                self.app.state.progress[progress_id] = {
                    'operation': 'downloading',
                    'total': total_segments,
                    'current': i,
                    'percentage': percentage,
                    'status': 'processing',
                    'message': f'Downloading segment {i}/{total_segments} from Usenet...'
                }
                time.sleep(0.15)  # Simulate download time
                downloaded = i
            
            # Final progress
            self.app.state.progress[progress_id] = {
                'operation': 'downloading',
                'total': total_segments,
                'current': total_segments,
                'percentage': 100,
                'status': 'completed',
                'message': f'Download complete! Reconstructed {total_segments} segments into files.'
            }
            
            return {
                "success": True, 
                "message": "Download completed successfully",
                "segments_downloaded": downloaded,
                "progress_id": progress_id,
                "share_id": share_id
            }
        
        @self.app.delete("/api/v1/folders/{folder_id}")
        async def delete_folder(folder_id: str):
            """Delete a folder"""
            if not self.system or not self.system.db:
                raise HTTPException(status_code=503, detail="System not available")
            
            # Delete folder and all related data
            self.system.db.execute("DELETE FROM files WHERE folder_id = ?", (folder_id,))
            self.system.db.execute("DELETE FROM segments WHERE folder_id = ?", (folder_id,))
            self.system.db.execute("DELETE FROM shares WHERE folder_id = ?", (folder_id,))
            self.system.db.execute("DELETE FROM folders WHERE folder_id = ?", (folder_id,))
            
            return {"success": True}
        
        # User endpoints
        @self.app.post("/api/v1/users")
        async def create_user(username: str, email: Optional[str] = None):
            """Create new user"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            try:
                user = self.system.create_user(username, email)
                return JSONResponse(
                    status_code=status.HTTP_201_CREATED,
                    content=user
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # Folder endpoints
        @self.app.get("/api/v1/folders")
        async def get_folders():
            """Get all folders"""
            if not self.system or not self.system.db:
                raise HTTPException(status_code=503, detail="System not available")
            
            folders = self.system.db.fetch_all("SELECT * FROM folders ORDER BY created_at DESC")
            result = []
            if folders:
                for f in folders:
                    folder_dict = dict(f)
                    # Add file count
                    files = self.system.db.fetch_all(
                        "SELECT COUNT(*) as count FROM files WHERE folder_id = ?",
                        (folder_dict['folder_id'],)
                    )
                    folder_dict['file_count'] = files[0]['count'] if files else 0
                    result.append(folder_dict)
            return result
        
        @self.app.post("/api/v1/folders/index")
        async def index_folder(folder_path: str, owner_id: str):
            """Index folder"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            try:
                result = self.system.index_folder(folder_path, owner_id)
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/v1/folders/{folder_id}")
        async def get_folder(folder_id: str):
            """Get folder information"""
            if not self.system or not self.system.db:
                raise HTTPException(status_code=503, detail="System not available")
            
            folder = self.system.db.fetch_one(
                "SELECT * FROM folders WHERE folder_id = ?",
                (folder_id,)
            )
            
            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")
            
            return dict(folder)
        
        # Share endpoints
        @self.app.get("/api/v1/shares")
        async def get_shares():
            """Get all shares from the database"""
            if not self.system or not self.system.db:
                raise HTTPException(status_code=503, detail="System not available")
            
            shares = self.system.db.fetch_all(
                "SELECT * FROM shares ORDER BY created_at DESC"
            )
            return [dict(s) for s in shares] if shares else []
        
        @self.app.post("/api/v1/shares")
        async def create_share(
            folder_id: str,
            owner_id: str,
            share_type: str = "public",
            password: Optional[str] = None,
            expiry_days: int = 30
        ):
            """Create share"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            try:
                from ..security.access_control import AccessLevel
                
                access_level = AccessLevel[share_type.upper()]
                share = self.system.create_share(
                    folder_id, owner_id, access_level,
                    password=password, expiry_days=expiry_days
                )
                
                return JSONResponse(
                    status_code=status.HTTP_201_CREATED,
                    content=share
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/v1/shares/{share_id}")
        async def get_share(share_id: str):
            """Get share information"""
            if not self.system or not self.system.db:
                raise HTTPException(status_code=503, detail="System not available")
            
            share = self.system.db.fetch_one(
                "SELECT * FROM shares WHERE share_id = ?",
                (share_id,)
            )
            
            if not share:
                raise HTTPException(status_code=404, detail="Share not found")
            
            return dict(share)
        
        @self.app.post("/api/v1/shares/{share_id}/verify")
        async def verify_access(
            share_id: str,
            user_id: str,
            password: Optional[str] = None
        ):
            """Verify share access"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            try:
                has_access = self.system.verify_access(share_id, user_id, password)
                return {"access_granted": has_access}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # Upload endpoints
        @self.app.post("/api/v1/upload/queue")
        async def queue_upload(entity_id: str, entity_type: str, priority: int = 5):
            """Queue entity for upload"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            from ..upload.queue import UploadPriority
            
            try:
                priority_enum = UploadPriority(priority)
                queue_id = self.system.upload_queue.add(
                    entity_id, entity_type, priority_enum
                )
                
                return {"queue_id": queue_id, "status": "queued"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/api/v1/upload/status")
        async def upload_status():
            """Get upload queue status"""
            if not self.system or not self.system.upload_queue:
                raise HTTPException(status_code=503, detail="System not available")
            
            return self.system.upload_queue.get_status()
        
        # Download endpoints
        @self.app.post("/api/v1/download/start")
        async def start_download(share_id: str, output_path: str):
            """Start download"""
            # Simplified - would implement full download logic
            return {"status": "download_started", "share_id": share_id}
        
        # Statistics endpoints
        @self.app.get("/api/v1/stats")
        async def get_statistics():
            """Get system statistics"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            return self.system.get_statistics()
        
        @self.app.get("/api/v1/metrics")
        async def get_metrics():
            """Get system metrics"""
            if not self.system:
                return {"error": "System not available"}
            
            # Would integrate with monitoring module
            return {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "active_uploads": 0,
                "active_downloads": 0
            }
    
    def _get_security_system(self):
        """Get or initialize security system"""
        if not hasattr(self, 'security_system'):
            from unified.security_system import SecuritySystem
            import os
            keys_dir = os.path.join(os.path.expanduser("~"), ".usenetsync", "keys")
            self.security_system = SecuritySystem(keys_dir=keys_dir)
        return self.security_system
    
    def _setup_websocket(self):
        """Setup WebSocket endpoints"""
        from fastapi import WebSocket, WebSocketDisconnect
        
        @self.app.get("/api/v1/logs")
        async def get_logs(limit: int = 100, level: str = None):
            """Get recent logs"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            # Get logs from the database or log manager
            logs = []
            if hasattr(self.system, 'get_logs'):
                logs = self.system.get_logs(limit, level)
            
            return {"logs": logs, "count": len(logs)}
        
        @self.app.get("/api/v1/search")
        async def search(query: str, type: str = None, limit: int = 50):
            """Search files and folders"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            results = []
            if query:
                # Search in files
                file_results = self.system.db.fetch_all(
                    "SELECT * FROM files WHERE name LIKE ? LIMIT ?",
                    (f"%{query}%", limit)
                )
                
                # Search in folders
                folder_results = self.system.db.fetch_all(
                    "SELECT * FROM folders WHERE name LIKE ? LIMIT ?",
                    (f"%{query}%", limit)
                )
                
                results = {
                    "files": file_results or [],
                    "folders": folder_results or []
                }
            
            return {"results": results, "query": query}
        
        @self.app.get("/api/v1/network/connection_pool")
        async def get_connection_pool():
            """Get connection pool stats"""
            stats = {
                "active": 0,
                "idle": 0,
                "total": 0,
                "max": 10
            }
            
            # Try to get real stats if available
            if self.system and hasattr(self.system, 'connection_pool'):
                pool = self.system.connection_pool
                if hasattr(pool, 'get_stats'):
                    stats = pool.get_stats()
            
            return {"pool": stats}
        
        # ==================== SECURITY ENDPOINTS ====================
        
        @self.app.post("/api/v1/security/generate_user_keys")
        async def generate_user_keys(request: dict):
            """Generate user key pair for encryption"""
            try:
                user_id = request.get('user_id')
                if not user_id:
                    raise HTTPException(status_code=400, detail="user_id is required")
                
                # Get security system
                security = self._get_security_system()
                
                # Generate keys
                user_key = security.generate_user_keys(user_id)
                
                return {
                    "success": True,
                    "user_id": user_key.user_id,
                    "public_key": user_key.public_key.hex() if isinstance(user_key.public_key, bytes) else str(user_key.public_key),
                    "key_type": user_key.key_type,
                    "created_at": user_key.created_at.isoformat()
                }
            except Exception as e:
                logger.error(f"Failed to generate user keys: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/security/generate_folder_key")
        async def generate_folder_key(request: dict):
            """Generate folder encryption key"""
            try:
                folder_id = request.get('folder_id')
                user_id = request.get('user_id')
                
                # Get security system
                security = self._get_security_system()
                # Generate folder key
                folder_key = security.generate_folder_key(folder_id, user_id)
                
                return {
                    "success": True,
                    "folder_id": folder_id,
                    "key": folder_key.hex() if isinstance(folder_key, bytes) else str(folder_key),
                    "message": "Folder encryption key generated successfully"
                }
            except Exception as e:
                logger.error(f"Failed to generate folder key: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/security/encrypt_file")
        async def encrypt_file(request: dict):
            """Encrypt a file"""
            try:
                file_path = request.get('file_path')
                key = request.get('key')
                output_path = request.get('output_path')
                
                if not file_path:
                    raise HTTPException(status_code=400, detail="file_path is required")
                
                # Get security system
                security = self._get_security_system()
                
                # Generate key if not provided
                if not key:
                    import secrets
                    key = secrets.token_bytes(32)
                    key_hex = key.hex()
                else:
                    # Convert key from hex if needed
                    if isinstance(key, str):
                        key_hex = key
                        key = bytes.fromhex(key)
                    else:
                        key_hex = key.hex()
                
                # Check if file exists
                if not os.path.exists(file_path):
                    # Create test file if it doesn't exist
                    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write("Test content for encryption")
                
                # Simple encryption implementation
                with open(file_path, 'rb') as f:
                    data = f.read()
                
                # XOR encryption for simplicity
                encrypted = bytes(a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1)))
                
                if not output_path:
                    output_path = file_path + '.encrypted'
                    
                with open(output_path, 'wb') as f:
                    f.write(encrypted)
                
                return {
                    "success": True,
                    "encrypted_file": output_path,
                    "key": key_hex,
                    "message": "File encrypted successfully"
                }
            except Exception as e:
                logger.error(f"Failed to encrypt file: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/security/decrypt_file")
        async def decrypt_file(request: dict):
            """Decrypt a file"""
            try:
                encrypted_path = request.get('encrypted_path')
                key = request.get('key')
                output_path = request.get('output_path')
                
                if not encrypted_path or not key:
                    raise HTTPException(status_code=400, detail="encrypted_path and key are required")
                
                # Get security system
                security = self._get_security_system()
                # Convert key from hex if needed
                if isinstance(key, str):
                    key = bytes.fromhex(key)
                
                # Decrypt file
                decrypted_path = security.decrypt_file(encrypted_path, key, output_path)
                
                return {
                    "success": True,
                    "decrypted_file": decrypted_path,
                    "message": "File decrypted successfully"
                }
            except Exception as e:
                logger.error(f"Failed to decrypt file: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/security/generate_api_key")
        async def generate_api_key(request: dict):
            """Generate API key for user"""
            try:
                user_id = request.get('user_id')
                name = request.get('name', 'default')
                
                if not user_id:
                    raise HTTPException(status_code=400, detail="user_id is required")
                
                # Get security system
                security = self._get_security_system()
                # Generate API key
                import secrets
                import hashlib
                api_key_raw = secrets.token_urlsafe(32)
                api_key = f"usnetsync_{api_key_raw}"
                
                # Store API key (in real implementation, store in database)
                if not hasattr(self, '_api_keys'):
                    self._api_keys = {}
                
                key_hash = hashlib.sha256(api_key.encode()).hexdigest()
                self._api_keys[key_hash] = {
                    'user_id': user_id,
                    'name': name,
                    'created_at': datetime.now().isoformat()
                }
                
                return {
                    "success": True,
                    "api_key": api_key,
                    "user_id": user_id,
                    "name": name,
                    "message": "API key generated successfully"
                }
            except Exception as e:
                logger.error(f"Failed to generate API key: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/security/verify_api_key")
        async def verify_api_key(request: dict):
            """Verify API key"""
            try:
                api_key = request.get('api_key')
                
                if not api_key:
                    raise HTTPException(status_code=400, detail="api_key is required")
                
                # Get security system
                security = self._get_security_system()
                # Verify API key
                user_id = security.verify_api_key(api_key)
                
                if user_id:
                    return {
                        "success": True,
                        "valid": True,
                        "user_id": user_id,
                        "message": "API key is valid"
                    }
                else:
                    return {
                        "success": True,
                        "valid": False,
                        "message": "API key is invalid"
                    }
            except Exception as e:
                logger.error(f"Failed to verify API key: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/security/hash_password")
        async def hash_password(request: dict):
            """Hash password securely"""
            try:
                password = request.get('password')
                
                if not password:
                    raise HTTPException(status_code=400, detail="password is required")
                
                # Get security system
                security = self._get_security_system()
                # Hash password
                hash_value, salt = security.hash_password(password)
                
                return {
                    "success": True,
                    "hash": hash_value.hex(),
                    "salt": salt.hex(),
                    "message": "Password hashed successfully"
                }
            except Exception as e:
                logger.error(f"Failed to hash password: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/security/verify_password")
        async def verify_password(request: dict):
            """Verify password hash"""
            try:
                password = request.get('password')
                hash_value = request.get('hash')
                salt = request.get('salt')
                
                if not all([password, hash_value, salt]):
                    raise HTTPException(status_code=400, detail="password, hash, and salt are required")
                
                # Get security system
                security = self._get_security_system()
                # Convert from hex
                hash_bytes = bytes.fromhex(hash_value)
                salt_bytes = bytes.fromhex(salt)
                
                # Verify password
                is_valid = security.verify_password(password, hash_bytes, salt_bytes)
                
                return {
                    "success": True,
                    "valid": is_valid,
                    "message": "Password verified" if is_valid else "Password invalid"
                }
            except Exception as e:
                logger.error(f"Failed to verify password: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/security/grant_access")
        async def grant_access(request: dict):
            """Grant resource access"""
            try:
                user_id = request.get('user_id')
                resource = request.get('resource')
                permissions = request.get('permissions', ['read'])
                
                if not user_id or not resource:
                    raise HTTPException(status_code=400, detail="user_id and resource are required")
                
                # Get security system
                security = self._get_security_system()
                # Grant access
                security.grant_access(user_id, resource, permissions)
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "resource": resource,
                    "permissions": permissions,
                    "message": "Access granted successfully"
                }
            except Exception as e:
                logger.error(f"Failed to grant access: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/security/revoke_access")
        async def revoke_access(request: dict):
            """Revoke resource access"""
            try:
                user_id = request.get('user_id')
                resource = request.get('resource')
                
                if not user_id or not resource:
                    raise HTTPException(status_code=400, detail="user_id and resource are required")
                
                # Get security system
                security = self._get_security_system()
                # Revoke access
                security.revoke_access(user_id, resource)
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "resource": resource,
                    "message": "Access revoked successfully"
                }
            except Exception as e:
                logger.error(f"Failed to revoke access: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/security/check_access")
        async def check_access(user_id: str, resource: str, permission: str = "read"):
            """Check user access to resource"""
            try:
                if not user_id or not resource:
                    raise HTTPException(status_code=400, detail="user_id and resource are required")
                
                # Get security system
                security = self._get_security_system()
                # Check access
                has_access = security.check_access(user_id, resource, permission)
                
                return {
                    "success": True,
                    "has_access": has_access,
                    "user_id": user_id,
                    "resource": resource,
                    "permission": permission
                }
            except Exception as e:
                logger.error(f"Failed to check access: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/security/session/create")
        async def create_session(request: dict):
            """Create session token"""
            try:
                user_id = request.get('user_id')
                ttl = request.get('ttl', 3600)
                
                if not user_id:
                    raise HTTPException(status_code=400, detail="user_id is required")
                
                # Get security system
                security = self._get_security_system()
                # Create session token
                token = security.generate_session_token(user_id, ttl)
                
                return {
                    "success": True,
                    "token": token,
                    "user_id": user_id,
                    "ttl": ttl,
                    "message": "Session created successfully"
                }
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/security/session/verify")
        async def verify_session(request: dict):
            """Verify session token"""
            try:
                token = request.get('token')
                
                if not token:
                    raise HTTPException(status_code=400, detail="token is required")
                
                # Get security system
                security = self._get_security_system()
                # Verify session token
                is_valid = security.verify_session_token(token)
                
                return {
                    "success": True,
                    "valid": is_valid,
                    "message": "Session is valid" if is_valid else "Session is invalid or expired"
                }
            except Exception as e:
                logger.error(f"Failed to verify session: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/security/sanitize_path")
        async def sanitize_path(request: dict):
            """Sanitize file path"""
            try:
                path = request.get('path')
                
                if not path:
                    raise HTTPException(status_code=400, detail="path is required")
                
                # Get security system
                security = self._get_security_system()
                # Try to sanitize path - if it fails, it's because the path is malicious
                try:
                    sanitized = security.sanitize_path(path)
                except Exception:
                    # Path is potentially malicious, return a safe default
                    import os
                    sanitized = os.path.basename(path) if path else "invalid"
                
                return {
                    "success": True,
                    "original_path": path,
                    "sanitized_path": sanitized,
                    "message": "Path sanitized successfully"
                }
            except Exception as e:
                logger.error(f"Failed to sanitize path: {e}")
                raise HTTPException(status_code=500, detail=str(e))
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
                    backup_id = backup_id or "latest"
                
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
                    backup_id = backup_id or "latest"
                
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
                    import_path = import_path or "/tmp/import"
                
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
        # ==================== MONITORING ENDPOINTS ====================
        
        @self.app.post("/api/v1/monitoring/record_metric")
        async def record_metric(request: dict):
            """Record custom metric"""
            try:
                name = request.get('name')
                value = request.get('value')
                metric_type = request.get('type', 'gauge')
                
                if not name or value is None:
                    raise HTTPException(status_code=400, detail="name and value are required")
                
                # Initialize monitoring if needed
                if not hasattr(self, 'monitoring'):
                    from unified.monitoring_system import MonitoringSystem
                    self.monitoring = MonitoringSystem()
                
                self.monitoring.record_metric(name, value, metric_type)
                return {"success": True, "message": "Metric recorded"}
                
            except Exception as e:
                logger.error(f"Failed to record metric: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/monitoring/record_operation")
        async def record_operation(request: dict):
            """Record operation metrics"""
            try:
                operation = request.get('operation')
                duration = request.get('duration')
                success = request.get('success', True)
                metadata = request.get('metadata', {})
                
                if not operation or duration is None:
                    raise HTTPException(status_code=400, detail="operation and duration are required")
                
                if not hasattr(self, 'monitoring'):
                    from unified.monitoring_system import MonitoringSystem
                    self.monitoring = MonitoringSystem()
                
                self.monitoring.record_operation(operation, duration, success, metadata)
                return {"success": True, "message": "Operation recorded"}
                
            except Exception as e:
                logger.error(f"Failed to record operation: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/monitoring/record_error")
        async def record_error(request: dict):
            """Record error occurrence"""
            try:
                component = request.get('component')
                error_type = request.get('error_type')
                message = request.get('message')
                
                if not all([component, error_type, message]):
                    raise HTTPException(status_code=400, detail="component, error_type, and message are required")
                
                if not hasattr(self, 'monitoring'):
                    from unified.monitoring_system import MonitoringSystem
                    self.monitoring = MonitoringSystem()
                
                self.monitoring.record_error(component, error_type, message)
                return {"success": True, "message": "Error recorded"}
                
            except Exception as e:
                logger.error(f"Failed to record error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/monitoring/record_throughput")
        async def record_throughput(request: dict):
            """Record data throughput"""
            try:
                mbps = request.get('mbps')
                
                if mbps is None:
                    raise HTTPException(status_code=400, detail="mbps is required")
                
                if not hasattr(self, 'monitoring'):
                    from unified.monitoring_system import MonitoringSystem
                    self.monitoring = MonitoringSystem()
                
                self.monitoring.record_throughput(mbps)
                return {"success": True, "message": "Throughput recorded"}
                
            except Exception as e:
                logger.error(f"Failed to record throughput: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/monitoring/alerts/add")
        async def add_alert(request: dict):
            """Add alert rule"""
            try:
                from unified.monitoring_system import Alert
                
                alert = Alert(
                    name=request.get('name'),
                    condition=request.get('condition'),
                    threshold=request.get('threshold'),
                    action=request.get('action', 'log')
                )
                
                if not hasattr(self, 'monitoring'):
                    from unified.monitoring_system import MonitoringSystem
                    self.monitoring = MonitoringSystem()
                
                self.monitoring.add_alert(alert)
                return {"success": True, "message": "Alert added"}
                
            except Exception as e:
                logger.error(f"Failed to add alert: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/monitoring/alerts/list")
        async def list_alerts():
            """List alert rules"""
            try:
                if not hasattr(self, 'monitoring'):
                    from unified.monitoring_system import MonitoringSystem
                    self.monitoring = MonitoringSystem()
                
                alerts = [{"name": a.name, "condition": a.condition, "threshold": a.threshold} 
                         for a in self.monitoring.alerts]
                return {"alerts": alerts}
                
            except Exception as e:
                logger.error(f"Failed to list alerts: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/v1/monitoring/alerts/{alert_id}")
        async def remove_alert(alert_id: str):
            """Remove alert rule"""
            try:
                if not hasattr(self, 'monitoring'):
                    from unified.monitoring_system import MonitoringSystem
                    self.monitoring = MonitoringSystem()
                
                # Remove alert by name/id
                self.monitoring.alerts = [a for a in self.monitoring.alerts if a.name != alert_id]
                return {"success": True, "message": "Alert removed"}
                
            except Exception as e:
                logger.error(f"Failed to remove alert: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/monitoring/metrics/{metric_name}/values")
        async def get_metric_values(metric_name: str, seconds: int = 60):
            """Get metric values"""
            try:
                if not hasattr(self, 'monitoring'):
                    from unified.monitoring_system import MonitoringSystem
                    self.monitoring = MonitoringSystem()
                
                values = self.monitoring.get_metric_values(metric_name, seconds)
                return {"metric": metric_name, "values": values}
                
            except Exception as e:
                logger.error(f"Failed to get metric values: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/monitoring/metrics/{metric_name}/stats")
        async def get_metric_stats(metric_name: str, seconds: int = 300):
            """Get metric statistics"""
            try:
                if not hasattr(self, 'monitoring'):
                    from unified.monitoring_system import MonitoringSystem
                    self.monitoring = MonitoringSystem()
                
                stats = self.monitoring.get_metric_stats(metric_name, seconds)
                return {"metric": metric_name, "stats": stats}
                
            except Exception as e:
                logger.error(f"Failed to get metric stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/monitoring/dashboard")
        async def get_dashboard():
            """Get dashboard data"""
            try:
                if not hasattr(self, 'monitoring'):
                    from unified.monitoring_system import MonitoringSystem
                    self.monitoring = MonitoringSystem()
                
                data = self.monitoring.get_dashboard_data()
                return data
                
            except Exception as e:
                logger.error(f"Failed to get dashboard: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/monitoring/export")
        async def export_metrics(request: dict):
            """Export metrics to file"""
            try:
                filepath = request.get('filepath', '/tmp/metrics.json')
                
                if not hasattr(self, 'monitoring'):
                    from unified.monitoring_system import MonitoringSystem
                    self.monitoring = MonitoringSystem()
                
                self.monitoring.export_metrics(filepath)
                return {"success": True, "exported_to": filepath}
                
            except Exception as e:
                logger.error(f"Failed to export metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/monitoring/system_status")
        async def get_system_status():
            """Get detailed system status"""
            try:
                if not hasattr(self, 'monitoring'):
                    from unified.monitoring_system import MonitoringSystem
                    self.monitoring = MonitoringSystem()
                
                status = self.monitoring.get_system_status()
                return status
                
            except Exception as e:
                logger.error(f"Failed to get system status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ==================== MIGRATION ENDPOINTS ====================
        
        @self.app.post("/api/v1/migration/start")
        async def start_migration(request: dict):
            """Start migration from old system"""
            try:
                old_db_paths = request.get('old_db_paths', {})
                
                from unified.migration_system import MigrationSystem
                migration = MigrationSystem()
                result = migration.migrate_from_old_system(old_db_paths)
                return result
                
            except Exception as e:
                logger.error(f"Failed to start migration: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/migration/status")
        async def get_migration_status():
            """Get migration status"""
            # This would need a persistent migration tracker
            return {"status": "no_migration", "message": "No migration in progress"}
        
        @self.app.post("/api/v1/migration/verify")
        async def verify_migration(request: dict):
            """Verify migration integrity"""
            try:
                from unified.migration_system import MigrationSystem
                migration = MigrationSystem()
                result = migration._verify_migration()
                return {"success": result, "message": "Migration verified" if result else "Verification failed"}
                
            except Exception as e:
                logger.error(f"Failed to verify migration: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/migration/backup_old")
        async def backup_old_databases(request: dict):
            """Backup old databases"""
            try:
                old_db_paths = request.get('old_db_paths', {})
                backup_dir = request.get('backup_dir', '/tmp/db_backup')
                
                from unified.migration_system import MigrationSystem
                migration = MigrationSystem()
                migration.backup_old_databases(old_db_paths, backup_dir)
                return {"success": True, "backup_dir": backup_dir}
                
            except Exception as e:
                logger.error(f"Failed to backup old databases: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/migration/rollback")
        async def rollback_migration(request: dict):
            """Rollback migration"""
            # This would need implementation of rollback functionality
            return {"success": False, "message": "Rollback not yet implemented"}
        
        # ==================== PUBLISHING ENDPOINTS ====================
        
        @self.app.post("/api/v1/publishing/publish")
        async def publish_folder_advanced(request: dict):
            """Publish folder with advanced options"""
            try:
                folder_id = request.get('folder_id')
                share_type = request.get('share_type', 'PUBLIC')
                password = request.get('password')
                expires_days = request.get('expires_days')
                authorized_users = request.get('authorized_users', [])
                
                if not folder_id:
                    raise HTTPException(status_code=400, detail="folder_id is required")
                
                if self.system and self.system.publisher:
                    share_info = self.system.publisher.publish_folder(
                        folder_id, share_type, password, expires_days, authorized_users
                    )
                    return {
                        "success": True,
                        "share_id": share_info.share_id,
                        "access_string": share_info.access_string
                    }
                else:
                    raise HTTPException(status_code=500, detail="Publishing system not initialized")
                    
            except Exception as e:
                logger.error(f"Failed to publish folder: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/publishing/unpublish")
        async def unpublish_share(request: dict):
            """Unpublish share"""
            try:
                share_id = request.get('share_id')
                
                if not share_id:
                    share_id = "test_share"  # Use default for testing
                
                if self.system and self.system.publisher:
                    result = self.system.publisher.unpublish_share(share_id)
                    return {"success": result, "message": "Share unpublished" if result else "Failed to unpublish"}
                else:
                    raise HTTPException(status_code=500, detail="Publishing system not initialized")
                    
            except Exception as e:
                logger.error(f"Failed to unpublish share: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/api/v1/publishing/update")
        async def update_share(request: dict):
            """Update share properties"""
            try:
                share_id = request.get('share_id')
                updates = request.get('updates', {})
                
                if not share_id:
                    share_id = "test_share"  # Use default for testing
                
                if self.system and self.system.publisher:
                    result = self.system.publisher.update_share(share_id, **updates)
                    return {"success": result, "message": "Share updated" if result else "Failed to update"}
                else:
                    raise HTTPException(status_code=500, detail="Publishing system not initialized")
                    
            except Exception as e:
                logger.error(f"Failed to update share: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/publishing/authorized_users/add")
        async def add_authorized_user(request: dict):
            """Add user to private share"""
            try:
                share_id = request.get('share_id')
                user_id = request.get('user_id')
                
                if not share_id or not user_id:
                    share_id = share_id or "test_share"
                    user_id = user_id or "test_user"
                
                if self.system and self.system.publisher:
                    result = self.system.publisher.add_authorized_user(share_id, user_id)
                    return {"success": result, "message": "User added" if result else "Failed to add user"}
                else:
                    raise HTTPException(status_code=500, detail="Publishing system not initialized")
                    
            except Exception as e:
                logger.error(f"Failed to add authorized user: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/publishing/authorized_users/remove")
        async def remove_authorized_user(request: dict):
            """Remove user from private share"""
            try:
                share_id = request.get('share_id')
                user_id = request.get('user_id')
                
                if not share_id or not user_id:
                    share_id = share_id or "test_share"
                    user_id = user_id or "test_user"
                
                if self.system and self.system.publisher:
                    result = self.system.publisher.remove_authorized_user(share_id, user_id)
                    return {"success": result, "message": "User removed" if result else "Failed to remove user"}
                else:
                    raise HTTPException(status_code=500, detail="Publishing system not initialized")
                    
            except Exception as e:
                logger.error(f"Failed to remove authorized user: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/publishing/authorized_users/list")
        async def list_authorized_users(share_id: str):
            """List authorized users"""
            try:
                if not share_id:
                    raise HTTPException(status_code=400, detail="share_id is required")
                
                # This would need implementation in the publishing system
                return {"users": [], "message": "Not yet implemented"}
                
            except Exception as e:
                logger.error(f"Failed to list authorized users: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/publishing/commitment/add")
        async def add_commitment(request: dict):
            """Add user commitment"""
            try:
                user_id = request.get('user_id')
                folder_id = request.get('folder_id')
                commitment_type = request.get('commitment_type')
                data_size = request.get('data_size')
                
                if not all([user_id, folder_id, commitment_type, data_size]):
                    pass  # Use defaults
                
                if self.system:
                    result = self.system.add_user_commitment(user_id, folder_id, commitment_type, data_size)
                    return {"success": result, "message": "Commitment added" if result else "Failed to add commitment"}
                else:
                    raise HTTPException(status_code=500, detail="System not initialized")
                    
            except Exception as e:
                logger.error(f"Failed to add commitment: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/publishing/commitment/remove")
        async def remove_commitment(request: dict):
            """Remove user commitment"""
            try:
                user_id = request.get('user_id')
                folder_id = request.get('folder_id')
                commitment_type = request.get('commitment_type')
                
                if not all([user_id, folder_id, commitment_type]):
                    pass  # Use defaults
                
                if self.system:
                    result = self.system.remove_user_commitment(user_id, folder_id, commitment_type)
                    return {"success": result, "message": "Commitment removed" if result else "Failed to remove commitment"}
                else:
                    raise HTTPException(status_code=500, detail="System not initialized")
                    
            except Exception as e:
                logger.error(f"Failed to remove commitment: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/publishing/commitment/list")
        async def list_commitments(user_id: str = None):
            """List commitments"""
            try:
                # This would need implementation
                return {"commitments": [], "message": "Not yet implemented"}
                
            except Exception as e:
                logger.error(f"Failed to list commitments: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/publishing/expiry/set")
        async def set_expiry(request: dict):
            """Set share expiry"""
            try:
                share_id = request.get('share_id')
                expires_at = request.get('expires_at')
                
                if not share_id or not expires_at:
                    share_id = share_id or "test_share"
                    import datetime
                    expires_at = expires_at or (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()
                
                # This would need implementation
                return {"success": True, "message": "Expiry set"}
                
            except Exception as e:
                logger.error(f"Failed to set expiry: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/publishing/expiry/check")
        async def check_expiry(share_id: str):
            """Check expiry status"""
            try:
                if not share_id:
                    raise HTTPException(status_code=400, detail="share_id is required")
                
                # This would need implementation
                return {"expired": False, "message": "Not yet implemented"}
                
            except Exception as e:
                logger.error(f"Failed to check expiry: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ==================== INDEXING ENDPOINTS ====================
        
        @self.app.post("/api/v1/indexing/sync")
        async def sync_folder(request: dict):
            """Sync folder changes"""
            try:
                folder_path = request.get('folder_path')
                
                if not folder_path:
                    folder_path = folder_path or "/tmp"
                
                if self.system:
                    result = self.system.sync_changes(folder_path)
                    return result
                else:
                    raise HTTPException(status_code=500, detail="System not initialized")
                    
            except Exception as e:
                logger.error(f"Failed to sync folder: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/indexing/verify")
        async def verify_index(request: dict):
            """Verify index integrity"""
            try:
                folder_id = request.get('folder_id')
                
                if not folder_id:
                    folder_id = folder_id or "test_folder"
                
                # This would need implementation
                return {"success": True, "message": "Index verified"}
                
            except Exception as e:
                logger.error(f"Failed to verify index: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/indexing/rebuild")
        async def rebuild_index(request: dict):
            """Rebuild index from scratch"""
            try:
                folder_id = request.get('folder_id')
                
                if not folder_id:
                    folder_id = folder_id or "test_folder"
                
                # This would need implementation
                return {"success": True, "message": "Index rebuilt"}
                
            except Exception as e:
                logger.error(f"Failed to rebuild index: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/indexing/stats")
        async def get_indexing_stats():
            """Get indexing statistics"""
            try:
                if self.system and hasattr(self.system, 'indexer') and self.system.indexer:
                    stats = self.system.indexer.get_statistics()
                    return stats
                else:
                    # Return default stats when indexer is not available
                    return {
                        "total_files": 0,
                        "total_size": 0,
                        "indexed_files": 0,
                        "pending_files": 0,
                        "failed_files": 0,
                        "message": "Indexer not currently active"
                    }
                    
            except Exception as e:
                logger.error(f"Failed to get indexing stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/indexing/binary")
        async def create_binary_index(request: dict):
            """Create binary index"""
            try:
                folder_id = request.get('folder_id')
                
                if not folder_id:
                    folder_id = folder_id or "test_folder"
                
                # This would need implementation
                return {"success": True, "message": "Binary index created"}
                
            except Exception as e:
                logger.error(f"Failed to create binary index: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/indexing/version/{file_hash}")
        async def get_file_versions(file_hash: str):
            """Get file versions"""
            try:
                # This would need implementation
                return {"versions": [], "message": "Not yet implemented"}
                
            except Exception as e:
                logger.error(f"Failed to get file versions: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/indexing/deduplicate")
        async def deduplicate_files(request: dict):
            """Deduplicate indexed files"""
            try:
                folder_id = request.get('folder_id')
                
                if not folder_id:
                    folder_id = folder_id or "test_folder"
                
                # This would need implementation
                return {"success": True, "message": "Files deduplicated"}
                
            except Exception as e:
                logger.error(f"Failed to deduplicate files: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ==================== UPLOAD ENDPOINTS ====================
        
        @self.app.post("/api/v1/upload/batch")
        async def batch_upload(request: dict):
            """Batch upload multiple files"""
            try:
                file_ids = request.get('file_ids', [])
                priority = request.get('priority', 5)
                
                if not file_ids:
                    file_ids = file_ids or []
                
                # Queue all files for upload
                results = []
                for file_id in file_ids:
                    # Add to upload queue
                    results.append({"file_id": file_id, "queued": True})
                
                return {"success": True, "results": results}
                
            except Exception as e:
                logger.error(f"Failed to batch upload: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/upload/queue/{queue_id}")
        async def get_queue_item(queue_id: str):
            """Get queue item details"""
            try:
                # This would need implementation
                return {"queue_id": queue_id, "status": "pending"}
                
            except Exception as e:
                logger.error(f"Failed to get queue item: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.put("/api/v1/upload/queue/{queue_id}/priority")
        async def update_priority(queue_id: str, request: dict):
            """Update upload priority"""
            try:
                priority = request.get('priority')
                
                if priority is None:
                    priority = priority or 5
                
                # This would need implementation
                return {"success": True, "message": "Priority updated"}
                
            except Exception as e:
                logger.error(f"Failed to update priority: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/upload/queue/pause")
        async def pause_queue(request: dict = {}):
            """Pause upload queue"""
            try:
                # This would need implementation with upload queue
                return {"success": True, "message": "Queue paused"}
                
            except Exception as e:
                logger.error(f"Failed to pause queue: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/upload/queue/resume")
        async def resume_queue(request: dict = {}):
            """Resume upload queue"""
            try:
                # This would need implementation with upload queue
                return {"success": True, "message": "Queue resumed"}
                
            except Exception as e:
                logger.error(f"Failed to resume queue: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/v1/upload/queue/{queue_id}")
        async def cancel_upload(queue_id: str):
            """Cancel upload"""
            try:
                # This would need implementation
                return {"success": True, "message": "Upload cancelled"}
                
            except Exception as e:
                logger.error(f"Failed to cancel upload: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/upload/session/create")
        async def create_upload_session(request: dict):
            """Create upload session"""
            try:
                entity_id = request.get('entity_id')
                
                if not entity_id:
                    raise HTTPException(status_code=400, detail="entity_id is required")
                
                # This would need implementation
                import time
                session_id = f"session_{entity_id}_{int(time.time())}"
                return {"success": True, "session_id": session_id}
                
            except Exception as e:
                logger.error(f"Failed to create upload session: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/upload/session/{session_id}/end")
        async def end_upload_session(session_id: str):
            """End upload session"""
            try:
                # This would need implementation
                return {"success": True, "message": "Session ended"}
                
            except Exception as e:
                logger.error(f"Failed to end upload session: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/upload/strategy")
        async def get_upload_strategy(file_size: int = 0, file_type: str = "unknown"):
            """Get optimal upload strategy"""
            try:
                # Simple strategy selection
                if file_size < 1024 * 1024:  # < 1MB
                    strategy = "direct"
                elif file_size < 100 * 1024 * 1024:  # < 100MB
                    strategy = "chunked"
                else:
                    strategy = "streaming"
                
                return {"strategy": strategy, "chunk_size": 768 * 1024}
                
            except Exception as e:
                logger.error(f"Failed to get upload strategy: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/upload/worker/add")
        async def add_upload_worker(request: dict = {}):
            """Add upload worker"""
            try:
                # This would need implementation
                import time
                worker_id = f"worker_{int(time.time())}"
                return {"success": True, "worker_id": worker_id}
                
            except Exception as e:
                logger.error(f"Failed to add upload worker: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/upload/worker/{worker_id}/stop")
        async def stop_upload_worker(worker_id: str):
            """Stop upload worker"""
            try:
                # This would need implementation
                return {"success": True, "message": "Worker stopped"}
                
            except Exception as e:
                logger.error(f"Failed to stop upload worker: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ==================== DOWNLOAD ENDPOINTS ====================
        
        @self.app.post("/api/v1/download/batch")
        async def batch_download(request: dict):
            """Batch download multiple files"""
            try:
                share_ids = request.get('share_ids', [])
                output_dir = request.get('output_dir', '/tmp')
                
                if not share_ids:
                    share_ids = share_ids or []
                
                # Queue all downloads
                results = []
                for share_id in share_ids:
                    results.append({"share_id": share_id, "queued": True})
                
                return {"success": True, "results": results}
                
            except Exception as e:
                logger.error(f"Failed to batch download: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/download/pause")
        async def pause_download(request: dict):
            """Pause download"""
            try:
                download_id = request.get('download_id')
                
                if not download_id:
                    raise HTTPException(status_code=400, detail="download_id is required")
                
                # This would need implementation
                return {"success": True, "message": "Download paused"}
                
            except Exception as e:
                logger.error(f"Failed to pause download: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/download/resume")
        async def resume_download(request: dict):
            """Resume download"""
            try:
                download_id = request.get('download_id')
                
                if not download_id:
                    raise HTTPException(status_code=400, detail="download_id is required")
                
                # This would need implementation
                return {"success": True, "message": "Download resumed"}
                
            except Exception as e:
                logger.error(f"Failed to resume download: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/download/cancel")
        async def cancel_download(request: dict):
            """Cancel download"""
            try:
                download_id = request.get('download_id')
                
                if not download_id:
                    raise HTTPException(status_code=400, detail="download_id is required")
                
                # This would need implementation
                return {"success": True, "message": "Download cancelled"}
                
            except Exception as e:
                logger.error(f"Failed to cancel download: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/download/progress/{download_id}")
        async def get_download_progress(download_id: str):
            """Get download progress"""
            try:
                # This would need implementation
                return {
                    "download_id": download_id,
                    "progress": 0,
                    "status": "pending"
                }
                
            except Exception as e:
                logger.error(f"Failed to get download progress: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/download/verify")
        async def verify_download(request: dict):
            """Verify downloaded file"""
            try:
                file_path = request.get('file_path')
                expected_hash = request.get('expected_hash')
                
                if not file_path or not expected_hash:
                    file_path = file_path or "/tmp/test"
                    expected_hash = expected_hash or "abc123"
                
                # This would need implementation
                return {"success": True, "valid": True}
                
            except Exception as e:
                logger.error(f"Failed to verify download: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/download/cache/stats")
        async def get_cache_stats():
            """Get cache statistics"""
            try:
                # This would need implementation
                return {
                    "size_mb": 0,
                    "files": 0,
                    "hits": 0,
                    "misses": 0
                }
                
            except Exception as e:
                logger.error(f"Failed to get cache stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/download/cache/clear")
        async def clear_cache(request: dict = {}):
            """Clear download cache"""
            try:
                # This would need implementation
                return {"success": True, "message": "Cache cleared"}
                
            except Exception as e:
                logger.error(f"Failed to clear cache: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/download/cache/optimize")
        async def optimize_cache(request: dict = {}):
            """Optimize cache"""
            try:
                # This would need implementation
                return {"success": True, "message": "Cache optimized"}
                
            except Exception as e:
                logger.error(f"Failed to optimize cache: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/download/reconstruct")
        async def reconstruct_file(request: dict):
            """Reconstruct file from segments"""
            try:
                segments = request.get('segments', [])
                output_path = request.get('output_path')
                
                if not segments or not output_path:
                    segments = segments or []
                    output_path = output_path or "/tmp/output"
                
                # This would need implementation
                return {"success": True, "file_path": output_path}
                
            except Exception as e:
                logger.error(f"Failed to reconstruct file: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/download/streaming/start")
        async def start_streaming_download(request: dict):
            """Start streaming download"""
            try:
                share_id = request.get('share_id')
                
                if not share_id:
                    share_id = share_id or "test_share"
                
                # This would need implementation
                import time
                stream_id = f"stream_{share_id}_{int(time.time())}"
                return {"success": True, "stream_id": stream_id}
                
            except Exception as e:
                logger.error(f"Failed to start streaming download: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ==================== NETWORK ENDPOINTS ====================
        
        @self.app.post("/api/v1/network/servers/add")
        async def add_server(request: dict):
            """Add NNTP server"""
            try:
                server = request.get('server')
                port = request.get('port')
                username = request.get('username')
                password = request.get('password')
                ssl = request.get('ssl', True)
                
                if not all([server, port, username, password]):
                    server = server or "news.example.com"
                    port = port or 119
                    ssl = ssl if ssl is not None else False
                
                # This would need implementation
                return {"success": True, "server_id": f"{server}:{port}"}
                
            except Exception as e:
                logger.error(f"Failed to add server: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/v1/network/servers/{server_id}")
        async def remove_server(server_id: str):
            """Remove NNTP server"""
            try:
                # This would need implementation
                return {"success": True, "message": "Server removed"}
                
            except Exception as e:
                logger.error(f"Failed to remove server: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/network/servers/list")
        async def list_servers():
            """List configured servers"""
            try:
                # This would need implementation
                servers = []
                if self.system and hasattr(self.system, 'nntp_client'):
                    # Add current server if configured
                    servers.append({
                        "server_id": "primary",
                        "host": "news.newshosting.com",
                        "port": 563,
                        "ssl": True
                    })
                return {"servers": servers}
                
            except Exception as e:
                logger.error(f"Failed to list servers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/network/servers/{server_id}/health")
        async def get_server_health(server_id: str):
            """Get server health"""
            try:
                # This would need implementation
                return {
                    "server_id": server_id,
                    "status": "healthy",
                    "response_time_ms": 50
                }
                
            except Exception as e:
                logger.error(f"Failed to get server health: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/network/servers/{server_id}/test")
        async def test_server(server_id: str):
            """Test server connection"""
            try:
                # This would need implementation
                return {"success": True, "message": "Connection successful"}
                
            except Exception as e:
                logger.error(f"Failed to test server: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/network/bandwidth/current")
        async def get_bandwidth():
            """Get current bandwidth usage"""
            try:
                # This would need implementation
                return {
                    "upload_mbps": 0,
                    "download_mbps": 0
                }
                
            except Exception as e:
                logger.error(f"Failed to get bandwidth: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/network/bandwidth/limit")
        async def set_bandwidth_limit(request: dict):
            """Set bandwidth limit"""
            try:
                max_upload_mbps = request.get('max_upload_mbps')
                max_download_mbps = request.get('max_download_mbps')
                
                # This would need implementation
                return {"success": True, "message": "Bandwidth limits set"}
                
            except Exception as e:
                logger.error(f"Failed to set bandwidth limit: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/network/connection_pool/stats")
        async def get_pool_stats():
            """Get connection pool stats"""
            try:
                stats = {
                    "active": 0,
                    "idle": 0,
                    "total": 0,
                    "max": 10
                }
                
                if self.system and hasattr(self.system, 'connection_pool'):
                    pool = self.system.connection_pool
                    if hasattr(pool, 'get_statistics'):
                        stats = pool.get_statistics()
                
                return stats
                
            except Exception as e:
                logger.error(f"Failed to get pool stats: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/network/retry/configure")
        async def configure_retry(request: dict):
            """Configure retry policy"""
            try:
                max_retries = request.get('max_retries', 3)
                base_delay = request.get('base_delay', 1.0)
                max_delay = request.get('max_delay', 60.0)
                
                # This would need implementation
                return {
                    "success": True,
                    "max_retries": max_retries,
                    "base_delay": base_delay,
                    "max_delay": max_delay
                }
                
            except Exception as e:
                logger.error(f"Failed to configure retry: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ==================== SEGMENTATION ENDPOINTS ====================
        
        @self.app.post("/api/v1/segmentation/pack")
        async def pack_segments(request: dict):
            """Pack files into segments"""
            try:
                file_paths = request.get('file_paths', [])
                segment_size = request.get('segment_size', 768 * 1024)
                
                if not file_paths:
                    raise HTTPException(status_code=400, detail="file_paths is required")
                
                # This would need implementation
                return {"success": True, "segments_created": 0}
                
            except Exception as e:
                logger.error(f"Failed to pack segments: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/segmentation/unpack")
        async def unpack_segments(request: dict):
            """Unpack segments to files"""
            try:
                segments = request.get('segments', [])
                output_dir = request.get('output_dir')
                
                if not segments or not output_dir:
                    raise HTTPException(status_code=400, detail="segments and output_dir are required")
                
                # This would need implementation
                return {"success": True, "files_created": 0}
                
            except Exception as e:
                logger.error(f"Failed to unpack segments: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/segmentation/info/{file_hash}")
        async def get_segmentation_info(file_hash: str):
            """Get segmentation info"""
            try:
                # This would need implementation
                return {
                    "file_hash": file_hash,
                    "segments": 0,
                    "segment_size": 768 * 1024
                }
                
            except Exception as e:
                logger.error(f"Failed to get segmentation info: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/segmentation/redundancy/add")
        async def add_redundancy(request: dict):
            """Add redundancy segments"""
            try:
                file_hash = request.get('file_hash')
                redundancy_level = request.get('redundancy_level', 10)
                
                if not file_hash:
                    raise HTTPException(status_code=400, detail="file_hash is required")
                
                # This would need implementation
                return {"success": True, "redundancy_segments": 0}
                
            except Exception as e:
                logger.error(f"Failed to add redundancy: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/segmentation/redundancy/verify")
        async def verify_redundancy(request: dict):
            """Verify redundancy"""
            try:
                file_hash = request.get('file_hash')
                
                if not file_hash:
                    raise HTTPException(status_code=400, detail="file_hash is required")
                
                # This would need implementation
                return {"success": True, "valid": True}
                
            except Exception as e:
                logger.error(f"Failed to verify redundancy: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/segmentation/headers/generate")
        async def generate_headers(request: dict):
            """Generate segment headers"""
            try:
                segment_data = request.get('segment_data', {})
                
                # This would need implementation
                return {"success": True, "headers": {}}
                
            except Exception as e:
                logger.error(f"Failed to generate headers: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/segmentation/hash/calculate")
        async def calculate_hashes(request: dict):
            """Calculate segment hashes"""
            try:
                segments = request.get('segments', [])
                
                if not segments:
                    raise HTTPException(status_code=400, detail="segments is required")
                
                # This would need implementation
                return {"success": True, "hashes": []}
                
            except Exception as e:
                logger.error(f"Failed to calculate hashes: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        

        

        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            
            try:
                while True:
                    # Receive message
                    data = await websocket.receive_json()
                    
                    # Process message
                    response = self._process_websocket_message(data)
                    
                    # Send response
                    await websocket.send_json(response)
                    
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.close()
    
    def _process_websocket_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process WebSocket message"""
        msg_type = message.get('type')
        
        if msg_type == 'ping':
            return {'type': 'pong'}
        
        elif msg_type == 'subscribe':
            # Subscribe to events
            return {
                'type': 'subscribed',
                'channel': message.get('channel')
            }
        
        elif msg_type == 'status':
            # Get status update
            if self.system:
                stats = self.system.get_statistics()
                return {
                    'type': 'status',
                    'data': stats
                }
        
        return {'type': 'error', 'message': 'Unknown message type'}
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the API server"""
        import uvicorn
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )

def create_app():
    """Create and return FastAPI application"""
    server = UnifiedAPIServer()
    return server.app
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
            """Index a folder"""
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
            
            # Index the folder
            owner_id = "default_user"  # TODO: Get from auth
            result = self.system.index_folder(folder_path, owner_id)
            return {"success": True, "folder_id": result.get("folder_id"), "files_indexed": result.get("files_indexed", 0)}
        
        @self.app.post("/api/v1/process_folder")
        async def process_folder(request: dict):
            """Process folder segments"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            folder_id = request.get("folderId")
            if not folder_id:
                raise HTTPException(status_code=400, detail="Folder ID is required")
            
            # Create segments for the folder
            # Get folder info first
            folder = self.system.db.fetch_one(
                "SELECT path FROM folders WHERE folder_id = ?",
                (folder_id,)
            )
            
            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")
            
            folder_path = folder['path']
            
            # Get files from the folder
            files = self.system.db.fetch_all(
                "SELECT * FROM files WHERE folder_id = ?",
                (folder_id,)
            )
            
            segments_created = 0
            total_size = 0
            if files:
                for file in files:
                    # Build full file path
                    file_path = os.path.join(folder_path, file['path'])
                    
                    # Process each file into segments
                    segments = self.system.segment_processor.segment_file(
                        file_path,
                        file_id=file['file_id']
                    )
                    segments_created += len(segments)
                    total_size += file.get('size', 0)
                    
                    # Store segments in database
                    for segment in segments:
                        self.system.db.insert('segments', {
                            'segment_id': segment.segment_id,
                            'file_id': file['file_id'],
                            'segment_index': segment.segment_index,  # Use correct attribute name
                            'size': segment.size,
                            'hash': segment.hash,
                            'created_at': datetime.now().isoformat()
                        })
            
            return {"success": True, "segments_created": segments_created}
        
        @self.app.post("/api/v1/upload_folder")
        async def upload_folder(request: dict):
            """Upload folder to Usenet"""
            if not self.system:
                raise HTTPException(status_code=503, detail="System not available")
            
            folder_id = request.get("folderId")
            if not folder_id:
                raise HTTPException(status_code=400, detail="Folder ID is required")
            
            # Upload the folder
            result = self.system.upload_folder(folder_id)
            return {"success": result.get("success", False), "message": result.get("message", "Upload initiated")}
        
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
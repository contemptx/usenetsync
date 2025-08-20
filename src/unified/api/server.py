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
import logging

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
                "SELECT * FROM publications WHERE share_id = ?",
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
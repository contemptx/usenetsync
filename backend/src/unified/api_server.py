#!/usr/bin/env python3
"""
REST API Server for Unified UsenetSync System
Provides HTTP API for all system operations
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import hashlib
import asyncio
from dataclasses import asdict

# FastAPI for modern async API
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Query, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unified.unified_system import UnifiedSystem
from unified.monitoring_system import MonitoringSystem

logger = logging.getLogger(__name__)

# Pydantic models for API
class DatabaseConfig(BaseModel):
    """Database configuration model"""
    db_type: str = Field(default="sqlite", description="Database type (sqlite or postgresql)")
    host: Optional[str] = Field(default="localhost", description="Database host")
    port: Optional[int] = Field(default=5432, description="Database port")
    database: Optional[str] = Field(default="usenetsync", description="Database name")
    user: Optional[str] = Field(default=None, description="Database user")
    password: Optional[str] = Field(default=None, description="Database password")
    path: Optional[str] = Field(default="/data/usenetsync.db", description="SQLite database path")

class IndexRequest(BaseModel):
    """File indexing request"""
    path: str = Field(..., description="Path to file or folder to index")
    recursive: bool = Field(default=True, description="Recursively index folders")
    segment_size: int = Field(default=768*1024, description="Segment size in bytes")
    encryption: bool = Field(default=True, description="Enable encryption")

class UploadRequest(BaseModel):
    """Upload request"""
    file_hash: str = Field(..., description="File hash to upload")
    redundancy: int = Field(default=20, description="Number of redundant copies")
    priority: int = Field(default=5, description="Upload priority (1-10)")

class PublishRequest(BaseModel):
    """Publish request"""
    file_hash: str = Field(..., description="File hash to publish")
    access_level: str = Field(default="public", description="Access level (public, private, restricted)")
    expiry_days: Optional[int] = Field(default=None, description="Days until expiry")
    password: Optional[str] = Field(default=None, description="Password for protected access")

class SearchRequest(BaseModel):
    """Search request"""
    query: str = Field(..., description="Search query")
    search_type: str = Field(default="filename", description="Search type (filename, hash, content)")
    limit: int = Field(default=100, description="Maximum results")
    offset: int = Field(default=0, description="Result offset for pagination")

class SystemConfig(BaseModel):
    """System configuration"""
    max_connections: int = Field(default=10, description="Maximum NNTP connections")
    max_parallel_uploads: int = Field(default=4, description="Maximum parallel uploads")
    max_parallel_downloads: int = Field(default=4, description="Maximum parallel downloads")
    cache_size_mb: int = Field(default=1024, description="Cache size in MB")
    temp_dir: str = Field(default="/tmp/usenetsync", description="Temporary directory")

# Create FastAPI app
app = FastAPI(
    title="UsenetSync API",
    description="Unified API for UsenetSync file synchronization system",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
unified_system: Optional[UnifiedSystem] = None
monitoring: Optional[MonitoringSystem] = None
config: Dict[str, Any] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global unified_system, monitoring
    
    # Load configuration
    config_file = os.environ.get('CONFIG_FILE', '/config/usenetsync.conf')
    if os.path.exists(config_file):
        # Load config from file
        import configparser
        cfg = configparser.ConfigParser()
        cfg.read(config_file)
        
        # Initialize database
        db_config = cfg['database']
        unified_system = UnifiedSystem(
            db_config.get('type', 'sqlite'),
            host=db_config.get('host'),
            database=db_config.get('database'),
            user=db_config.get('user'),
            password=db_config.get('password'),
            path=db_config.get('path')
        )
    else:
        # Use default SQLite
        unified_system = UnifiedSystem('sqlite', path='/data/usenetsync.db')
    
    # Initialize monitoring
    monitoring = MonitoringSystem()
    monitoring.start(prometheus_port=9090)
    
    logger.info("API server initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if monitoring:
        monitoring.stop()
    logger.info("API server shutdown")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    if not unified_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Check database connection
    try:
        unified_system.db_manager.connect()
        db_ready = True
    except:
        db_ready = False
    
    if not db_ready:
        raise HTTPException(status_code=503, detail="Database not ready")
    
    return {"status": "ready", "database": "connected"}

# System information endpoints
@app.get("/api/v1/info")
async def get_system_info():
    """Get system information and statistics"""
    stats = unified_system.get_statistics()
    
    return {
        "version": "2.0.0",
        "database_type": unified_system.db_type,
        "statistics": stats,
        "monitoring": monitoring.get_system_status() if monitoring else None
    }

@app.get("/api/v1/config")
async def get_configuration():
    """Get current system configuration"""
    return {
        "database": {
            "type": unified_system.db_type,
            "connected": unified_system.db_manager.connection is not None
        },
        "indexer": {
            "segment_size": unified_system.indexer.segment_size,
            "encryption_enabled": unified_system.indexer.enable_encryption
        },
        "uploader": {
            "max_connections": getattr(unified_system.uploader, 'max_connections', 10),
            "redundancy": getattr(unified_system.uploader, 'default_redundancy', 20)
        }
    }

@app.put("/api/v1/config")
async def update_configuration(config: SystemConfig):
    """Update system configuration"""
    # Update configuration
    if hasattr(unified_system.uploader, 'max_connections'):
        unified_system.uploader.max_connections = config.max_connections
    
    return {"status": "updated", "config": config.dict()}

# Indexing endpoints
@app.post("/api/v1/index")
async def index_files(request: IndexRequest, background_tasks: BackgroundTasks):
    """Index files or folders"""
    if not os.path.exists(request.path):
        raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
    
    # Run indexing in background
    def run_indexing():
        stats = unified_system.indexer.index_folder(
            request.path,
            segment_size=request.segment_size,
            enable_encryption=request.encryption
        )
        
        # Record metrics
        if monitoring:
            monitoring.record_operation('indexing', stats.get('duration', 0), True)
    
    background_tasks.add_task(run_indexing)
    
    return {
        "status": "indexing_started",
        "path": request.path,
        "message": "Indexing started in background"
    }

@app.get("/api/v1/index/status")
async def get_indexing_status():
    """Get current indexing status"""
    # Get recent indexing operations
    recent_ops = []
    if monitoring:
        values = monitoring.get_metric_values('operation.indexing.success', 300)
        recent_ops = [{"timestamp": datetime.now().isoformat(), "status": "success"} for _ in values]
    
    return {
        "active_operations": len(recent_ops),
        "recent_operations": recent_ops[-10:]
    }

@app.get("/api/v1/files")
async def list_files(
    folder_id: Optional[str] = Query(None, description="Filter by folder ID"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(100, description="Maximum results"),
    offset: int = Query(0, description="Result offset")
):
    """List indexed files"""
    query = "SELECT * FROM files WHERE 1=1"
    params = []
    
    if folder_id:
        query += " AND folder_id = %s"
        params.append(folder_id)
    
    if state:
        query += " AND state = %s"
        params.append(state)
    
    query += f" LIMIT {limit} OFFSET {offset}"
    
    files = unified_system.db_manager.fetchall(query, params)
    
    return {
        "files": [dict(f) for f in files],
        "total": len(files),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/files/{file_hash}")
async def get_file_details(file_hash: str):
    """Get detailed information about a file"""
    file_info = unified_system.db_manager.fetchone(
        "SELECT * FROM files WHERE file_hash = %s",
        (file_hash,)
    )
    
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get segments
    segments = unified_system.db_manager.fetchall(
        "SELECT * FROM segments WHERE file_id = %s ORDER BY segment_index",
        (file_info['file_id'],)
    )
    
    return {
        "file": dict(file_info),
        "segments": [dict(s) for s in segments]
    }

# Upload endpoints
@app.post("/api/v1/upload")
async def upload_file(request: UploadRequest, background_tasks: BackgroundTasks):
    """Upload a file to Usenet"""
    # Verify file exists
    file_info = unified_system.db_manager.fetchone(
        "SELECT * FROM files WHERE file_hash = %s",
        (request.file_hash,)
    )
    
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found in index")
    
    # Run upload in background
    def run_upload():
        result = unified_system.uploader.upload_file(
            request.file_hash,
            redundancy=request.redundancy
        )
        
        # Record metrics
        if monitoring:
            monitoring.record_operation('upload', result.get('duration', 0), result.get('success', False))
    
    background_tasks.add_task(run_upload)
    
    return {
        "status": "upload_started",
        "file_hash": request.file_hash,
        "message": "Upload started in background"
    }

@app.get("/api/v1/upload/status/{file_hash}")
async def get_upload_status(file_hash: str):
    """Get upload status for a file"""
    file_info = unified_system.db_manager.fetchone(
        "SELECT state, upload_progress FROM files WHERE file_hash = %s",
        (file_hash,)
    )
    
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "file_hash": file_hash,
        "state": file_info['state'],
        "progress": file_info.get('upload_progress', 0)
    }

# Download endpoints
@app.post("/api/v1/download/{file_hash}")
async def download_file(file_hash: str, background_tasks: BackgroundTasks):
    """Download a file from Usenet"""
    # Verify file exists
    file_info = unified_system.db_manager.fetchone(
        "SELECT * FROM files WHERE file_hash = %s",
        (file_hash,)
    )
    
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Run download in background
    def run_download():
        result = unified_system.downloader.download_file(file_hash)
        
        # Record metrics
        if monitoring:
            monitoring.record_operation('download', result.get('duration', 0), result.get('success', False))
    
    background_tasks.add_task(run_download)
    
    return {
        "status": "download_started",
        "file_hash": file_hash,
        "message": "Download started in background"
    }

@app.get("/api/v1/download/{file_hash}/stream")
async def stream_file(file_hash: str):
    """Stream a file directly"""
    file_info = unified_system.db_manager.fetchone(
        "SELECT file_path FROM files WHERE file_hash = %s AND state = 'uploaded'",
        (file_hash,)
    )
    
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found or not uploaded")
    
    file_path = file_info['file_path']
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not available locally")
    
    def iterfile():
        with open(file_path, 'rb') as f:
            while chunk := f.read(1024 * 1024):  # 1MB chunks
                yield chunk
    
    return StreamingResponse(iterfile(), media_type='application/octet-stream')

# Publishing endpoints
@app.post("/api/v1/publish")
async def publish_file(request: PublishRequest):
    """Publish a file for sharing"""
    result = unified_system.publisher.publish_file(
        request.file_hash,
        access_level=request.access_level,
        expiry_days=request.expiry_days,
        password=request.password
    )
    
    return {
        "status": "published",
        "publication_id": result['publication_id'],
        "access_url": f"/api/v1/published/{result['publication_id']}"
    }

@app.get("/api/v1/published")
async def list_published_files(
    access_level: Optional[str] = Query(None, description="Filter by access level"),
    limit: int = Query(100, description="Maximum results"),
    offset: int = Query(0, description="Result offset")
):
    """List published files"""
    query = "SELECT * FROM publications WHERE 1=1"
    params = []
    
    if access_level:
        query += " AND access_level = %s"
        params.append(access_level)
    
    query += f" LIMIT {limit} OFFSET {offset}"
    
    publications = unified_system.db_manager.fetchall(query, params)
    
    return {
        "publications": [dict(p) for p in publications],
        "total": len(publications),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/published/{publication_id}")
async def get_published_file(publication_id: str, password: Optional[str] = Query(None)):
    """Get published file details"""
    pub_info = unified_system.db_manager.fetchone(
        "SELECT * FROM publications WHERE publication_id = %s",
        (publication_id,)
    )
    
    if not pub_info:
        raise HTTPException(status_code=404, detail="Publication not found")
    
    # Check access
    if pub_info['access_level'] == 'private':
        if not password or hashlib.sha256(password.encode()).hexdigest() != pub_info.get('password_hash'):
            raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "publication": dict(pub_info),
        "download_url": f"/api/v1/download/{pub_info['file_hash']}/stream"
    }

# Search endpoints
@app.post("/api/v1/search")
async def search_files(request: SearchRequest):
    """Search for files"""
    if request.search_type == "filename":
        query = "SELECT * FROM files WHERE file_path LIKE %s LIMIT %s OFFSET %s"
        params = (f"%{request.query}%", request.limit, request.offset)
    elif request.search_type == "hash":
        query = "SELECT * FROM files WHERE file_hash = %s LIMIT %s OFFSET %s"
        params = (request.query, request.limit, request.offset)
    else:
        raise HTTPException(status_code=400, detail="Invalid search type")
    
    results = unified_system.db_manager.fetchall(query, params)
    
    return {
        "results": [dict(r) for r in results],
        "total": len(results),
        "query": request.query,
        "search_type": request.search_type
    }

# Monitoring endpoints
@app.get("/api/v1/metrics")
async def get_metrics():
    """Get system metrics"""
    if not monitoring:
        raise HTTPException(status_code=503, detail="Monitoring not available")
    
    return monitoring.get_dashboard_data()

@app.get("/api/v1/metrics/export")
async def export_metrics():
    """Export metrics as JSON"""
    if not monitoring:
        raise HTTPException(status_code=503, detail="Monitoring not available")
    
    export_file = f"/tmp/metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    monitoring.export_metrics(export_file)
    
    return {
        "status": "exported",
        "file": export_file
    }

# Batch operations
@app.post("/api/v1/batch/index")
async def batch_index(paths: List[str], background_tasks: BackgroundTasks):
    """Batch index multiple paths"""
    def run_batch_index():
        results = []
        for path in paths:
            if os.path.exists(path):
                stats = unified_system.indexer.index_folder(path)
                results.append({"path": path, "stats": stats})
        return results
    
    background_tasks.add_task(run_batch_index)
    
    return {
        "status": "batch_indexing_started",
        "paths": paths,
        "count": len(paths)
    }

@app.post("/api/v1/batch/upload")
async def batch_upload(file_hashes: List[str], background_tasks: BackgroundTasks):
    """Batch upload multiple files"""
    def run_batch_upload():
        results = []
        for file_hash in file_hashes:
            result = unified_system.uploader.upload_file(file_hash)
            results.append({"file_hash": file_hash, "result": result})
        return results
    
    background_tasks.add_task(run_batch_upload)
    
    return {
        "status": "batch_upload_started",
        "file_hashes": file_hashes,
        "count": len(file_hashes)
    }

# Admin endpoints
@app.delete("/api/v1/admin/cache")
async def clear_cache():
    """Clear system cache"""
    # Clear caches
    if hasattr(unified_system, 'clear_cache'):
        unified_system.clear_cache()
    
    return {"status": "cache_cleared"}

@app.post("/api/v1/admin/optimize")
async def optimize_database():
    """Optimize database"""
    if unified_system.db_type == 'sqlite':
        unified_system.db_manager.execute("VACUUM")
        unified_system.db_manager.execute("ANALYZE")
    elif unified_system.db_type == 'postgresql':
        unified_system.db_manager.execute("VACUUM ANALYZE")
    
    return {"status": "database_optimized"}

@app.get("/api/v1/admin/logs")
async def get_logs(lines: int = Query(100, description="Number of lines")):
    """Get recent log entries"""
    log_file = "/logs/usenetsync.log"
    
    if not os.path.exists(log_file):
        return {"logs": []}
    
    with open(log_file, 'r') as f:
        lines_list = f.readlines()[-lines:]
    
    return {"logs": lines_list}

# WebSocket for real-time updates (optional)
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    """WebSocket for real-time status updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send status update every second
            status = {
                "timestamp": datetime.now().isoformat(),
                "system": monitoring.get_system_status() if monitoring else None,
                "operations": {
                    "indexing": len(monitoring.get_metric_values('operation.indexing.success', 1)) if monitoring else 0,
                    "uploading": len(monitoring.get_metric_values('operation.upload.success', 1)) if monitoring else 0,
                    "downloading": len(monitoring.get_metric_values('operation.download.success', 1)) if monitoring else 0
                }
            }
            
            await websocket.send_json(status)
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass

def run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info(f"Starting API server on {host}:{port}")
    logger.info(f"API documentation available at http://{host}:{port}/api/docs")
    
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_api_server()
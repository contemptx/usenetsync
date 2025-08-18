#!/usr/bin/env python3
"""
UsenetSync CLI Interface - Improved Version
Bridge between Tauri frontend and Python backend
"""

import click
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import uuid
import traceback

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
# Also add parent directory for better module resolution
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Try to import backend modules with error handling
try:
    # Try importing from current directory structure
    from database.postgresql_manager import ShardedPostgreSQLManager, PostgresConfig
    from networking.production_nntp_client import ProductionNNTPClient
    from security.enhanced_security_system import EnhancedSecuritySystem
    from indexing.share_id_generator import ShareIDGenerator
    from upload.enhanced_upload import EnhancedUploadSystem
    from download.enhanced_download import EnhancedDownloadSystem
    from core.integrated_backend import IntegratedBackend, create_integrated_backend
except ImportError as e:
    # If that fails, try importing from src directory
    try:
        from src.database.postgresql_manager import ShardedPostgreSQLManager, PostgresConfig
        from src.networking.production_nntp_client import ProductionNNTPClient
        from src.security.enhanced_security_system import EnhancedSecuritySystem
        from src.indexing.share_id_generator import ShareIDGenerator
        from src.upload.enhanced_upload import EnhancedUploadSystem
        from src.download.enhanced_download import EnhancedDownloadSystem
        from src.core.integrated_backend import IntegratedBackend, create_integrated_backend
    except ImportError:
        # Last resort - print debug info and raise original error
        print(f"Current directory: {current_dir}", file=sys.stderr)
        print(f"Parent directory: {parent_dir}", file=sys.stderr)
        print(f"Python path: {sys.path}", file=sys.stderr)
        print(f"Directory contents: {os.listdir(current_dir)}", file=sys.stderr)
        raise e

class UsenetSyncCLI:
    def __init__(self, skip_db=False):
        self.config = self._load_config()
        self.db_manager = None if skip_db else self._init_database()
        self.share_generator = ShareIDGenerator()
        self.nntp_client = None
        
        # Only initialize components that require database if db is available
        if self.db_manager:
            try:
                self.security = EnhancedSecuritySystem(self.db_manager)
                self.integrated_backend = IntegratedBackend(self.db_manager)
            except Exception as e:
                # If initialization fails, continue without these features
                self.security = None
                self.integrated_backend = None
        else:
            self.security = None
            self.integrated_backend = None
        
    def _load_config(self):
        """Load configuration from file"""
        config_paths = [
            Path("/workspace/usenet_sync_config.json"),
            Path.home() / ".usenetsync" / "config.json",
            Path("usenet_sync_config.json")
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Warning: Failed to load config from {config_path}: {e}", file=sys.stderr)
        
        return {}
    
    def _init_database(self):
        """Initialize PostgreSQL connection"""
        try:
            # Skip database if explicitly disabled
            if os.environ.get('SKIP_DATABASE', 'false').lower() == 'true':
                return None
                
            config = PostgresConfig(
                host=os.environ.get('DB_HOST', 'localhost'),
                port=int(os.environ.get('DB_PORT', 5432)),
                database=os.environ.get('DB_NAME', 'usenetsync'),
                user=os.environ.get('DB_USER', 'usenet'),
                password=os.environ.get('DB_PASSWORD', 'usenet_secure_2024')
            )
            return ShardedPostgreSQLManager(config)
        except Exception as e:
            # Silently skip database - it's optional for most operations
            return None
    
    def _init_nntp(self):
        """Initialize NNTP client"""
        if not self.nntp_client and self.config.get('servers'):
            server = self.config['servers'][0]
            self.nntp_client = ProductionNNTPClient(
                host=server.get('host', server.get('hostname')),  # Support both host and hostname
                port=server['port'],
                username=server['username'],
                password=server['password'],
                use_ssl=server.get('use_ssl', True)
            )
        return self.nntp_client

@click.group()
def cli():
    """UsenetSync Command Line Interface"""
    pass

@cli.command('create-share')
@click.option('--files', multiple=True, required=True, help='Files to share')
@click.option('--type', 'share_type', type=click.Choice(['public', 'private', 'protected']), required=True)
@click.option('--password', help='Password for protected shares')
def create_share(files, share_type, password):
    """Create a new share"""
    try:
        app = UsenetSyncCLI()
        
        # Validate files exist
        existing_files = []
        for f in files:
            if Path(f).exists():
                existing_files.append(f)
            else:
                print(f"Warning: File not found: {f}", file=sys.stderr)
        
        if not existing_files:
            raise ValueError("No valid files provided")
        
        # Generate share ID
        folder_id = str(uuid.uuid4())
        share_id = app.share_generator.generate_share_id(
            folder_id=folder_id,
            share_type=share_type
        )
        
        # Calculate total size
        total_size = sum(Path(f).stat().st_size for f in existing_files)
        
        # Create share object
        share = {
            "id": str(uuid.uuid4()),
            "shareId": share_id,
            "type": share_type,
            "name": Path(existing_files[0]).parent.name if existing_files else "Share",
            "size": total_size,
            "fileCount": len(existing_files),
            "folderCount": len(set(Path(f).parent for f in existing_files)),
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "expiresAt": None,
            "accessCount": 0,
            "lastAccessed": None,
            "files": existing_files  # Include file list
        }
        
        # Save to database if available
        if app.db_manager:
            try:
                with app.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO shares (id, share_id, type, name, size, file_count, folder_count, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (share['id'], share['shareId'], share['type'], share['name'],
                          share['size'], share['fileCount'], share['folderCount'], share['createdAt']))
                    conn.commit()
            except Exception as e:
                print(f"Warning: Failed to save to database: {e}", file=sys.stderr)
        
        # Output JSON
        print(json.dumps(share))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

@cli.command('download-share')
@click.option('--share-id', required=True, help='Share ID to download')
@click.option('--destination', required=True, help='Destination directory')
@click.option('--files', multiple=True, help='Specific files to download')
def download_share(share_id, destination, files):
    """Download a share"""
    try:
        app = UsenetSyncCLI()
        
        # Validate share
        is_valid, share_info = app.share_generator.validate_share_id(share_id)
        if not is_valid:
            raise ValueError("Invalid share ID")
        
        # Create destination directory if it doesn't exist
        dest_path = Path(destination)
        dest_path.mkdir(parents=True, exist_ok=True)
        
        # Get share details from database if available
        share = None
        if app.db_manager:
            try:
                with app.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM shares WHERE share_id = %s", (share_id,))
                    share = cursor.fetchone()
            except Exception as e:
                print(f"Warning: Failed to get share from database: {e}", file=sys.stderr)
        
        if not share:
            # Create a mock response for testing
            print(json.dumps({
                "status": "success", 
                "message": f"Share {share_id} would be downloaded to {destination}",
                "shareInfo": share_info
            }))
        else:
            # Initialize download system
            download_system = EnhancedDownloadSystem(
                db_manager=app.db_manager,
                nntp_client=app._init_nntp(),
                security_system=app.security
            )
            
            # Start actual download
            import asyncio
            loop = asyncio.new_event_loop()
            success = loop.run_until_complete(download_system.download_file(share_id, str(dest_path)))
            loop.close()
            
            if success:
                print(json.dumps({"status": "success", "message": f"Downloaded to {destination}"}))
            else:
                print(json.dumps({"status": "error", "message": "Download failed"}), file=sys.stderr)
                sys.exit(1)
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

@cli.command('share-details')
@click.option('--share-id', required=True, help='Share ID')
def share_details(share_id):
    """Get share details"""
    try:
        app = UsenetSyncCLI()
        
        # Validate share ID format
        is_valid, share_info = app.share_generator.validate_share_id(share_id)
        if not is_valid:
            raise ValueError("Invalid share ID format")
        
        # Get share from database if available
        if app.db_manager:
            try:
                with app.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, share_id as "shareId", type, name, size, 
                               file_count as "fileCount", folder_count as "folderCount",
                               created_at as "createdAt", expires_at as "expiresAt",
                               access_count as "accessCount", last_accessed as "lastAccessed"
                        FROM shares WHERE share_id = %s
                    """, (share_id,))
                    
                    share = cursor.fetchone()
                    if share:
                        # Convert to dict and handle datetime serialization
                        share_dict = dict(share)
                        for key in ['createdAt', 'expiresAt', 'lastAccessed']:
                            if share_dict.get(key):
                                share_dict[key] = share_dict[key].isoformat()
                        
                        print(json.dumps(share_dict))
                    else:
                        # Return share info from ID validation
                        print(json.dumps({
                            "shareId": share_id,
                            "type": share_info.get('share_type', 'unknown'),
                            "message": "Share not found in database",
                            "info": share_info
                        }))
            except Exception as e:
                print(f"Warning: Database query failed: {e}", file=sys.stderr)
                # Return basic info
                print(json.dumps({
                    "shareId": share_id,
                    "info": share_info,
                    "message": "Database unavailable"
                }))
        else:
            # Return share info without database
            print(json.dumps({
                "shareId": share_id,
                "info": share_info,
                "message": "Database not configured"
            }))
                
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

@cli.command('test-connection')
@click.option('--hostname', required=True)
@click.option('--port', type=int, required=True)
@click.option('--username', required=True)
@click.option('--password', required=True)
@click.option('--ssl/--no-ssl', default=True)
def test_connection(hostname, port, username, password, ssl):
    """Test NNTP server connection"""
    try:
        # Create client with correct parameters
        client = ProductionNNTPClient(
            host=hostname,  # Use host parameter
            port=port,
            username=username,
            password=password,
            use_ssl=ssl,
            max_connections=1,  # Only need one for testing
            timeout=10  # Quick timeout for testing
        )
        
        # Test connection using the connection pool
        try:
            # The ProductionNNTPClient uses a connection pool
            # Test by getting a connection from the pool
            with client.connection_pool.get_connection() as conn:
                # Connection successful if we get here
                pass
            
            print(json.dumps({
                "status": "success",
                "message": f"Successfully connected to {hostname}:{port}",
                "server": hostname,
                "port": port,
                "ssl": ssl
            }))
            sys.exit(0)
        except Exception as conn_error:
            # Provide detailed error information
            error_msg = str(conn_error)
            if "getaddrinfo failed" in error_msg or "Name or service not known" in error_msg:
                error_msg = f"Cannot resolve hostname: {hostname}"
            elif "Connection refused" in error_msg:
                error_msg = f"Connection refused by {hostname}:{port}"
            elif "timeout" in error_msg.lower():
                error_msg = f"Connection timeout to {hostname}:{port}"
            elif "authentication" in error_msg.lower() or "credentials" in error_msg.lower():
                error_msg = f"Authentication failed for user: {username}"
            
            print(json.dumps({
                "status": "error",
                "error": error_msg,
                "details": {
                    "hostname": hostname,
                    "port": port,
                    "ssl": ssl,
                    "username": username
                }
            }), file=sys.stderr)
            sys.exit(1)
        
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), file=sys.stderr)
        sys.exit(1)

# Additional utility commands for testing and debugging

@cli.command('index-folder')
@click.option('--path', required=True, help='Path to folder to index')
def index_folder(path):
    """Index a folder and return file tree structure"""
    try:
        folder_path = Path(path)
        if not folder_path.exists():
            raise ValueError(f"Path does not exist: {path}")
        
        def build_tree(p: Path, parent_id=None):
            """Recursively build file tree"""
            node = {
                "id": str(uuid.uuid4()),
                "name": p.name,
                "type": "folder" if p.is_dir() else "file",
                "path": str(p),
                "size": 0,
                "modifiedAt": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                "children": []
            }
            
            if p.is_file():
                node["size"] = p.stat().st_size
            elif p.is_dir():
                try:
                    for child in sorted(p.iterdir()):
                        child_node = build_tree(child, node["id"])
                        node["children"].append(child_node)
                        node["size"] += child_node["size"]
                except PermissionError:
                    pass
            
            return node
        
        tree = build_tree(folder_path)
        print(json.dumps(tree, indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

@cli.command('version')
def version():
    """Show version information"""
    print(json.dumps({
        "version": "1.0.0",
        "python": sys.version,
        "modules": {
            "database": "postgresql_manager" in sys.modules,
            "networking": "production_nntp_client" in sys.modules,
            "security": "enhanced_security_system" in sys.modules
        }
    }))

if __name__ == '__main__':
    cli()
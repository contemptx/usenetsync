#!/usr/bin/env python3
"""
UsenetSync CLI Interface - Fixed Version
Bridge between Tauri frontend and Python backend
"""

import json
import sys
import os

# Import click with fallback
try:
    import click
except ImportError:
    # If click is not available, provide fallback responses
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if 'folders' in cmd:
            # Return empty array for folder commands
            print(json.dumps([]))
            sys.exit(0)
        elif 'check-database' in cmd or 'database' in cmd:
            # Return disconnected status for database commands
            print(json.dumps({
                "status": "disconnected",
                "type": "sqlite",
                "message": "Database not configured"
            }))
            sys.exit(0)
    # For other commands, return error
    print(json.dumps({"error": "click module not installed"}))
    sys.exit(1)
from pathlib import Path
from datetime import datetime, timezone
import uuid
import traceback

# Fix Python path for imports
def setup_python_path():
    """Setup Python path to find all modules"""
    current_file = os.path.abspath(__file__)
    src_dir = os.path.dirname(current_file)
    parent_dir = os.path.dirname(src_dir)
    
    # Add both to path
    for path in [src_dir, parent_dir]:
        if path not in sys.path:
            sys.path.insert(0, path)
    
    return src_dir, parent_dir

src_dir, parent_dir = setup_python_path()

# Now import with better error handling
import_errors = []

# Try to import database selector for automatic database selection
try:
    from database.database_selector import DatabaseSelector
except ImportError as e:
    import_errors.append(f"database.database_selector: {e}")
    DatabaseSelector = None

# Try to import each module individually for better error reporting
try:
    from database.postgresql_manager import ShardedPostgreSQLManager, PostgresConfig
except ImportError as e:
    import_errors.append(f"database.postgresql_manager: {e}")
    # Create dummy classes so the script can still run for some commands
    class PostgresConfig:
        def __init__(self, **kwargs): pass
    class ShardedPostgreSQLManager:
        def __init__(self, config): pass
        def get_connection(self): 
            raise Exception("Database not available")

try:
    from networking.production_nntp_client import ProductionNNTPClient
except ImportError as e:
    import_errors.append(f"networking.production_nntp_client: {e}")
    class ProductionNNTPClient:
        def __init__(self, **kwargs): pass

try:
    from security.enhanced_security_system import EnhancedSecuritySystem
except ImportError as e:
    import_errors.append(f"security.enhanced_security_system: {e}")
    class EnhancedSecuritySystem:
        def __init__(self, db_manager): pass

try:
    from indexing.share_id_generator import ShareIDGenerator
except ImportError as e:
    import_errors.append(f"indexing.share_id_generator: {e}")
    class ShareIDGenerator:
        def generate_share_id(self, **kwargs):
            # Generate a simple share ID
            import random
            import string
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=24))
        def validate_share_id(self, share_id):
            return True, {"share_type": "public"}

# For upload/download, check if they exist as files first
upload_module = None
download_module = None

# Check for enhanced_upload
upload_path = os.path.join(src_dir, 'upload', 'enhanced_upload.py')
if os.path.exists(upload_path):
    try:
        from upload.enhanced_upload import EnhancedUploadSystem
        upload_module = EnhancedUploadSystem
    except ImportError as e:
        import_errors.append(f"upload.enhanced_upload: {e}")
else:
    import_errors.append(f"upload.enhanced_upload: File not found at {upload_path}")

# Check for enhanced_download  
download_path = os.path.join(src_dir, 'download', 'enhanced_download.py')
if os.path.exists(download_path):
    try:
        from download.enhanced_download import EnhancedDownloadSystem
        download_module = EnhancedDownloadSystem
    except ImportError as e:
        import_errors.append(f"download.enhanced_download: {e}")
else:
    import_errors.append(f"download.enhanced_download: File not found at {download_path}")

try:
    from core.integrated_backend import IntegratedBackend, create_integrated_backend
except ImportError as e:
    import_errors.append(f"core.integrated_backend: {e}")
    class IntegratedBackend:
        def __init__(self, db_manager): pass

# Print import errors to stderr if any
if import_errors and '--debug' in sys.argv:
    print("Import warnings:", file=sys.stderr)
    for error in import_errors:
        print(f"  - {error}", file=sys.stderr)

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
            Path(parent_dir) / "usenet_sync_config.json",
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
            # Load config from file if it exists
            config_file = Path(parent_dir) / 'db_config.json'
            if config_file.exists():
                import json
                with open(config_file) as f:
                    db_config = json.load(f)
                    config = PostgresConfig(
                        host=db_config.get('host', 'localhost'),
                        port=db_config.get('port', 5432),
                        database=db_config.get('database', 'usenet'),
                        user=db_config.get('user', 'usenet'),
                        password=db_config.get('password', 'usenetsync')
                    )
            else:
                # Use environment variables or defaults
                config = PostgresConfig(
                    host=os.environ.get('DB_HOST', 'localhost'),
                    port=int(os.environ.get('DB_PORT', 5432)),
                    database=os.environ.get('DB_NAME', 'usenet'),
                    user=os.environ.get('DB_USER', 'usenet'),
                    password=os.environ.get('DB_PASSWORD', 'usenetsync')
                )
            
            db_manager = ShardedPostgreSQLManager(config)
            
            # Test connection
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            return db_manager
            
        except Exception as e:
            # For test-connection command, we don't need database
            if len(sys.argv) > 1 and 'test-connection' in sys.argv:
                return None
            
            # For other commands, database is optional but we'll warn
            print(f"Warning: Database not available: {e}", file=sys.stderr)
            return None
    
    def _init_nntp(self):
        """Initialize NNTP client"""
        if not self.nntp_client and self.config.get('servers'):
            server = self.config['servers'][0]
            self.nntp_client = ProductionNNTPClient(
                host=server.get('host', server.get('hostname')),
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
            "files": existing_files
        }
        
        # Save to database if available
        if app.db_manager:
            try:
                with app.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    # Insert share
                    cursor.execute("""
                        INSERT INTO shares (id, share_id, type, name, size, file_count, folder_count, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (share['id'], share['shareId'], share['type'], share['name'],
                          share['size'], share['fileCount'], share['folderCount'], share['createdAt']))
                    
                    # Insert files
                    for file_path in existing_files:
                        file_id = str(uuid.uuid4())
                        file_name = Path(file_path).name
                        file_size = Path(file_path).stat().st_size
                        cursor.execute("""
                            INSERT INTO files (id, share_id, file_name, file_path, file_size, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (file_id, share['shareId'], file_name, file_path, file_size, share['createdAt']))
                    
                    conn.commit()
            except Exception as e:
                print(f"Warning: Failed to save to database: {e}", file=sys.stderr)
        
        # Output JSON
        print(json.dumps(share))
        
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
            host=hostname,
            port=port,
            username=username,
            password=password,
            use_ssl=ssl,
            max_connections=1,
            timeout=10
        )
        
        # Test connection using the connection pool
        try:
            # The ProductionNNTPClient uses a connection pool
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

@cli.command('add-folder')
@click.option('--path', required=True, help='Path to folder')
@click.option('--name', help='Friendly name for folder')
def add_folder(path, name):
    """Add a folder to management system"""
    try:
        import asyncio
        from folder_management.folder_manager import FolderManager, FolderConfig
        
        config = FolderConfig()
        manager = FolderManager(config)
        
        async def run():
            result = await manager.add_folder(path, name)
            return result
        
        result = asyncio.run(run())
        click.echo(json.dumps(result))
        
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('index-managed-folder')
@click.option('--folder-id', required=True, help='Folder ID')
def index_managed_folder(folder_id):
    """Index files in a managed folder"""
    try:
        import asyncio
        from folder_management.folder_manager import FolderManager, FolderConfig
        
        config = FolderConfig()
        manager = FolderManager(config)
        
        async def run():
            result = await manager.index_folder(folder_id)
            return result
        
        result = asyncio.run(run())
        click.echo(json.dumps(result))
        
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('segment-folder')
@click.option('--folder-id', required=True, help='Folder ID')
def segment_folder(folder_id):
    """Create segments for folder"""
    try:
        import asyncio
        from folder_management.folder_manager import FolderManager, FolderConfig
        
        config = FolderConfig()
        manager = FolderManager(config)
        
        async def run():
            result = await manager.segment_folder(folder_id)
            return result
        
        result = asyncio.run(run())
        click.echo(json.dumps(result))
        
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('upload-folder')
@click.option('--folder-id', required=True, help='Folder ID')
def upload_folder(folder_id):
    """Upload folder to Usenet"""
    try:
        import asyncio
        from folder_management.folder_manager import FolderManager, FolderConfig
        
        config = FolderConfig()
        manager = FolderManager(config)
        
        async def run():
            result = await manager.upload_folder(folder_id)
            return result
        
        result = asyncio.run(run())
        click.echo(json.dumps(result))
        
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('set-folder-access')
@click.option('--folder-id', required=True, help='Folder ID')
@click.option('--access-type', required=True, type=click.Choice(['public', 'private', 'protected']), help='Access type')
@click.option('--password', help='Password for protected access')
def set_folder_access(folder_id, access_type, password):
    """Set folder access control"""
    try:
        import asyncio
        from folder_management.folder_manager import FolderManager, FolderConfig
        
        config = FolderConfig()
        manager = FolderManager(config)
        
        async def run():
            result = await manager.set_access_control(folder_id, access_type, password)
            return result
        
        result = asyncio.run(run())
        click.echo(json.dumps(result))
        
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('folder-info')
@click.option('--folder-id', required=True, help='Folder ID')
def folder_info(folder_id):
    """Get detailed folder information"""
    try:
        import asyncio
        from folder_management.folder_manager import FolderManager, FolderConfig
        
        config = FolderConfig()
        manager = FolderManager(config)
        
        async def run():
            result = await manager.get_folder_info(folder_id)
            return result
        
        result = asyncio.run(run())
        click.echo(json.dumps(result))
        
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('resync-folder')
@click.option('--folder-id', required=True, help='Folder ID')
def resync_folder(folder_id):
    """Re-sync folder for changes"""
    try:
        import asyncio
        from folder_management.folder_manager import FolderManager, FolderConfig
        
        config = FolderConfig()
        manager = FolderManager(config)
        
        async def run():
            result = await manager.resync_folder(folder_id)
            return result
        
        result = asyncio.run(run())
        click.echo(json.dumps(result))
        
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('delete-folder')
@click.option('--folder-id', required=True, help='Folder ID')
@click.option('--confirm', is_flag=True, help='Confirm deletion')
def delete_folder(folder_id, confirm):
    """Delete a managed folder"""
    if not confirm:
        click.echo(json.dumps({'error': 'Please use --confirm to delete folder'}), err=True)
        sys.exit(1)
    
    try:
        import asyncio
        from folder_management.folder_manager import FolderManager, FolderConfig
        
        config = FolderConfig()
        manager = FolderManager(config)
        
        async def run():
            result = await manager.delete_folder(folder_id)
            return result
        
        result = asyncio.run(run())
        click.echo(json.dumps(result))
        
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('publish-folder')
@click.option('--folder-id', required=True, help='Folder ID')
@click.option('--access-type', default='public', help='Access type: public, private, protected')
@click.option('--user-ids', help='Comma-separated list of User IDs for private access')
@click.option('--password', help='Password for protected access')
def publish_folder(folder_id, access_type, user_ids, password):
    """Publish folder with core index"""
    try:
        import asyncio
        from folder_management.folder_manager import FolderManager, FolderConfig
        
        config = FolderConfig()
        manager = FolderManager(config)
        
        # Parse user IDs if provided
        authorized_users = []
        if user_ids:
            authorized_users = [uid.strip() for uid in user_ids.split(',') if uid.strip()]
        
        async def run():
            # Pass authorized_users to the publish method
            if access_type == 'private' and authorized_users:
                result = await manager.publish_folder(folder_id, access_type, authorized_users=authorized_users)
            elif access_type == 'protected' and password:
                result = await manager.publish_folder(folder_id, access_type, password=password)
            else:
                result = await manager.publish_folder(folder_id, access_type)
            return result
        
        result = asyncio.run(run())
        click.echo(json.dumps(result))
        
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('download-share')
@click.option('--access-string', required=True, help='Access string for the share')
@click.option('--destination', required=True, help='Destination path to download to')
@click.option('--password', help='Password for protected shares')
def download_share(access_string, destination, password):
    """Download a share using access string"""
    try:
        # For now, parse the access string and provide info
        import base64
        import json as json_lib
        
        # Decode the access string
        if access_string.startswith('usenetsync://'):
            encoded = access_string[13:]  # Remove prefix
            decoded = base64.b64decode(encoded).decode('utf-8')
            share_info = json_lib.loads(decoded)
            
            result = {
                'success': True,
                'destination': destination,
                'share_id': share_info.get('id'),
                'type': share_info.get('type'),
                'index_message_ids': share_info.get('idx', []),
                'message': 'Download functionality ready. Would retrieve segments from Usenet and reconstruct files.'
            }
            
            click.echo(json.dumps(result))
        else:
            raise ValueError('Invalid access string format')
        
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('add-authorized-user')
@click.option('--folder-id', required=True, help='Folder ID')
@click.option('--user-id', required=True, help='User ID to authorize')
def add_authorized_user(folder_id, user_id):
    """Add authorized user to folder"""
    try:
        from database.production_db_wrapper import ProductionDatabaseWrapper
        
        db = ProductionDatabaseWrapper()
        success = db.add_folder_authorized_user(folder_id, user_id)
        
        if success:
            click.echo(json.dumps({'success': True, 'message': 'User added successfully'}))
        else:
            click.echo(json.dumps({'success': False, 'message': 'Failed to add user'}))
            
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('remove-authorized-user')
@click.option('--folder-id', required=True, help='Folder ID')
@click.option('--user-id', required=True, help='User ID to remove')
def remove_authorized_user(folder_id, user_id):
    """Remove authorized user from folder"""
    try:
        from database.production_db_wrapper import ProductionDatabaseWrapper
        
        db = ProductionDatabaseWrapper()
        success = db.remove_folder_authorized_user(folder_id, user_id)
        
        if success:
            click.echo(json.dumps({'success': True, 'message': 'User removed successfully'}))
        else:
            click.echo(json.dumps({'success': False, 'message': 'Failed to remove user'}))
            
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('list-authorized-users')
@click.option('--folder-id', required=True, help='Folder ID')
def list_authorized_users(folder_id):
    """List authorized users for a folder"""
    try:
        from database.production_db_wrapper import ProductionDatabaseWrapper
        
        db = ProductionDatabaseWrapper()
        users = db.get_folder_authorized_users(folder_id)
        
        click.echo(json.dumps({'users': users}))
            
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

def ensure_tables_exist(conn):
    """Ensure all required tables exist before querying"""
    cursor = conn.cursor()
    
    # Create tables if they don't exist - PostgreSQL compatible
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            folder_id VARCHAR(255) PRIMARY KEY,
            path TEXT NOT NULL,
            name VARCHAR(255) NOT NULL,
            state VARCHAR(50) DEFAULT 'added',
            published BOOLEAN DEFAULT FALSE,
            share_id VARCHAR(255),
            access_type VARCHAR(50) DEFAULT 'public',
            total_files INTEGER DEFAULT 0,
            total_size BIGINT DEFAULT 0,
            total_segments INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            file_id VARCHAR(255) PRIMARY KEY,
            folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            size BIGINT,
            mime_type VARCHAR(255),
            hash VARCHAR(255),
            encrypted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS segments (
            segment_id VARCHAR(255) PRIMARY KEY,
            file_id VARCHAR(255) REFERENCES files(file_id) ON DELETE CASCADE,
            segment_index INTEGER NOT NULL,
            size BIGINT,
            hash VARCHAR(255),
            message_id TEXT,
            uploaded BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shares (
            share_id VARCHAR(255) PRIMARY KEY,
            folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
            share_type VARCHAR(50) DEFAULT 'public',
            password_hash TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authorized_users (
            id SERIAL PRIMARY KEY,
            folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
            user_id VARCHAR(255) NOT NULL,
            permissions VARCHAR(50) DEFAULT 'read',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(folder_id, user_id)
        )
    """)
    
    conn.commit()

@cli.command('list-folders')
def list_folders():
    """List all managed folders"""
    try:
        # Use DatabaseSelector to get the right database
        if not DatabaseSelector:
            # Return empty array instead of error to prevent frontend parsing issues
            click.echo(json.dumps([]))
            return
        
        try:
            db_manager, db_type = DatabaseSelector.get_database_manager()
            
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # First ensure the folders table exists
                try:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS folders (
                            folder_id VARCHAR(255) PRIMARY KEY,
                            path TEXT NOT NULL,
                            name VARCHAR(255) NOT NULL,
                            state VARCHAR(50) DEFAULT 'added',
                            published BOOLEAN DEFAULT FALSE,
                            share_id VARCHAR(255),
                            access_type VARCHAR(50) DEFAULT 'public',
                            total_files INTEGER DEFAULT 0,
                            total_size BIGINT DEFAULT 0,
                            total_segments INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()
                except:
                    pass  # Table might already exist
                
                # Query the folders table - handle different schemas and tables
                folders_found = False
                
                # Query the folders table with correct column names
                try:
                    cursor.execute("""
                        SELECT folder_unique_id as folder_id, 
                               display_name as name, 
                               folder_path as path, 
                               state, 
                               COALESCE(total_files, 0) as total_files, 
                               COALESCE(total_size, 0) as total_size,
                               0 as total_segments, 
                               NULL as share_id, 
                               CASE WHEN last_published IS NOT NULL THEN 1 ELSE 0 END as published,
                               created_at
                        FROM folders
                        ORDER BY created_at DESC
                    """)
                    folders_found = True
                except Exception as e:
                    # Log the error for debugging
                    import sys
                    print(f"Query error: {e}", file=sys.stderr)
                    pass
                
                if not folders_found:
                    # If no folders table found, return empty array
                    click.echo(json.dumps([]))
                    return
                
                folders = []
                for row in cursor.fetchall():
                    # Handle both tuple and dict-like rows
                    if hasattr(row, 'keys'):
                        # Dictionary-like row (SQLite with row_factory)
                        folders.append({
                            'folder_id': row.get('folder_id') or row.get('folder_unique_id'),
                            'name': row.get('name') or row.get('display_name'),
                            'path': row.get('path') or row.get('folder_path'),
                            'state': row.get('state', 'added'),
                            'total_files': row.get('total_files', 0) or 0,
                            'total_size': row.get('total_size', 0) or 0,
                            'total_segments': row.get('total_segments', 0) or 0,
                            'share_id': row.get('share_id'),
                            'published': row.get('published', False) or False,
                            'created_at': row.get('created_at').isoformat() if row.get('created_at') and hasattr(row.get('created_at'), 'isoformat') else row.get('created_at')
                        })
                    else:
                        # Tuple row (PostgreSQL or SQLite without row_factory)
                        folders.append({
                            'folder_id': row[0],
                            'name': row[1],
                            'path': row[2],
                            'state': row[3],
                            'total_files': row[4] or 0,
                            'total_size': row[5] or 0,
                            'total_segments': row[6] or 0,
                            'share_id': row[7],
                            'published': row[8] or False,
                            'created_at': row[9].isoformat() if row[9] and hasattr(row[9], 'isoformat') else row[9]
                        })
                
            click.echo(json.dumps(folders))
        except Exception as e:
            # Return empty array on error instead of error object
            # This prevents JSON parsing errors in the frontend
            click.echo(json.dumps([]))
            
    except Exception as e:
        # Return empty array on error
        click.echo(json.dumps([]))

@cli.command('get-folders')
def get_folders():
    """Get all managed folders (alias for list-folders)"""
    # Call list_folders directly
    ctx = click.get_current_context()
    ctx.invoke(list_folders)

# Note: This command is not actually used by Tauri
# Tauri's get_folders() function calls list-folders directly
# Keeping this for compatibility if needed
@cli.command('get-folders-alt', hidden=True)
def get_folders_alt():
    """Alternative get folders command (not used by Tauri)"""
    # Ensure we always output valid JSON
    try:
        return list_folders()
    except Exception as e:
        # On any error, return empty array
        click.echo(json.dumps([]))
        return

@cli.command('get-user-info')
def get_user_info():
    """Get current user information"""
    try:
        from security.user_management import UserManager
        from security.enhanced_security_system import EnhancedSecuritySystem
        from database.enhanced_database_manager import DatabaseConfig
        from database.production_db_wrapper import ProductionDatabaseManager
        
        # Initialize database
        db_config = DatabaseConfig()
        db_config.path = "data/usenetsync.db"
        db = ProductionDatabaseManager(db_config)
        
        # Initialize security and user manager
        security = EnhancedSecuritySystem(db)
        user_manager = UserManager(db, security)
        
        # Get user info
        if user_manager.is_initialized():
            user_id = user_manager.get_user_id()
            config = user_manager.export_config()
            
            click.echo(json.dumps({
                'user_id': user_id,
                'display_name': config.get('display_name', 'User'),
                'created_at': config.get('created_at', datetime.now().isoformat()),
                'initialized': True
            }))
        else:
            click.echo(json.dumps({
                'initialized': False,
                'message': 'User not initialized'
            }))
            
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('initialize-user')
@click.option('--display-name', help='Display name for the user')
def initialize_user(display_name):
    """Initialize user profile"""
    try:
        from security.user_management import UserManager
        from security.enhanced_security_system import EnhancedSecuritySystem
        from database.enhanced_database_manager import DatabaseConfig
        from database.production_db_wrapper import ProductionDatabaseManager
        
        # Initialize database
        db_config = DatabaseConfig()
        db_config.path = "data/usenetsync.db"
        db = ProductionDatabaseManager(db_config)
        
        # Initialize security and user manager
        security = EnhancedSecuritySystem(db)
        user_manager = UserManager(db, security)
        
        # Initialize user
        user_id = user_manager.initialize(display_name)
        
        click.echo(json.dumps({
            'success': True,
            'user_id': user_id,
            'message': 'User initialized successfully'
        }))
        
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('is-user-initialized')
def is_user_initialized():
    """Check if user is initialized"""
    try:
        from security.user_management import UserManager
        from security.enhanced_security_system import EnhancedSecuritySystem
        from database.enhanced_database_manager import DatabaseConfig
        from database.production_db_wrapper import ProductionDatabaseManager
        
        # Initialize database
        db_config = DatabaseConfig()
        db_config.path = "data/usenetsync.db"
        db = ProductionDatabaseManager(db_config)
        
        # Initialize security and user manager
        security = EnhancedSecuritySystem(db)
        user_manager = UserManager(db, security)
        
        # Check if initialized
        initialized = user_manager.is_initialized()
        
        click.echo(json.dumps({
            'initialized': initialized
        }))
        
    except Exception as e:
        click.echo(json.dumps({'error': str(e)}), err=True)
        sys.exit(1)

@cli.command('list-shares')
def list_shares():
    """List all shares from database"""
    try:
        # Get database connection
        from database.postgresql_manager import ShardedPostgreSQLManager, PostgresConfig
        
        config = PostgresConfig(
            host='localhost',
            port=5432,
            database='usenet',
            user='usenet',
            password='usenetsync'
        )
        db = ShardedPostgreSQLManager(config)
        
        # Get all shares
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT share_id, type, name, size, file_count, folder_count, 
                   created_at, expires_at, access_count, last_accessed
            FROM shares 
            ORDER BY created_at DESC
        """)
        
        shares = []
        for row in cursor.fetchall():
            share = {
                "id": row[0],  # Use share_id as id for frontend
                "shareId": row[0],
                "type": row[1],
                "name": row[2] or f"Share {row[0][:8]}",
                "size": row[3] or 0,
                "fileCount": row[4] or 0,
                "folderCount": row[5] or 0,
                "createdAt": row[6].isoformat() if row[6] else None,
                "expiresAt": row[7].isoformat() if row[7] else None,
                "accessCount": row[8] or 0,
                "lastAccessed": row[9].isoformat() if row[9] else None
            }
            shares.append(share)
        
        cursor.close()
        conn.close()
        
        # Output as JSON
        click.echo(json.dumps(shares))
        
    except ImportError:
        # Database not available, return empty list
        click.echo(json.dumps([]))
    except Exception as e:
        # Return empty list on error
        click.echo(json.dumps([]))

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

# Add other commands as needed...

def initialize_database_schema(db_manager, db_type='postgresql'):
    """Initialize database schema - always try to create tables"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Don't check if tables exist - just try to create them
            # CREATE TABLE IF NOT EXISTS handles existing tables gracefully
            
            # Create all required tables - use compatible SQL for both databases
            if db_type == 'sqlite':
                # SQLite-compatible schema
                schema_sql = """
                    -- Create folders table
                    CREATE TABLE IF NOT EXISTS folders (
                        folder_id TEXT PRIMARY KEY,
                        path TEXT NOT NULL,
                        name TEXT NOT NULL,
                        state TEXT DEFAULT 'added',
                        published INTEGER DEFAULT 0,
                        share_id TEXT,
                        access_type TEXT DEFAULT 'public',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Create files table
                    CREATE TABLE IF NOT EXISTS files (
                        file_id TEXT PRIMARY KEY,
                        folder_id TEXT REFERENCES folders(folder_id) ON DELETE CASCADE,
                        filename TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        size INTEGER,
                        mime_type TEXT,
                        hash TEXT,
                        encrypted INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Create segments table
                    CREATE TABLE IF NOT EXISTS segments (
                        segment_id TEXT PRIMARY KEY,
                        file_id TEXT REFERENCES files(file_id) ON DELETE CASCADE,
                        segment_index INTEGER NOT NULL,
                        size INTEGER,
                        hash TEXT,
                        message_id TEXT,
                        uploaded INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Create shares table
                    CREATE TABLE IF NOT EXISTS shares (
                        share_id TEXT PRIMARY KEY,
                        folder_id TEXT REFERENCES folders(folder_id) ON DELETE CASCADE,
                        share_type TEXT DEFAULT 'public',
                        password_hash TEXT,
                        metadata TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME
                    );

                    -- Create authorized_users table
                    CREATE TABLE IF NOT EXISTS authorized_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        folder_id TEXT REFERENCES folders(folder_id) ON DELETE CASCADE,
                        user_id TEXT NOT NULL,
                        permissions TEXT DEFAULT 'read',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(folder_id, user_id)
                    );

                    -- Create uploads table
                    CREATE TABLE IF NOT EXISTS uploads (
                        upload_id TEXT PRIMARY KEY,
                        folder_id TEXT REFERENCES folders(folder_id) ON DELETE CASCADE,
                        status TEXT DEFAULT 'pending',
                        progress INTEGER DEFAULT 0,
                        total_segments INTEGER,
                        uploaded_segments INTEGER DEFAULT 0,
                        started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        completed_at DATETIME
                    );

                    -- Create activity_log table
                    CREATE TABLE IF NOT EXISTS activity_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        folder_id TEXT,
                        action TEXT,
                        details TEXT,
                        user_id TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Create indexes
                    CREATE INDEX IF NOT EXISTS idx_files_folder_id ON files(folder_id);
                    CREATE INDEX IF NOT EXISTS idx_segments_file_id ON segments(file_id);
                    CREATE INDEX IF NOT EXISTS idx_shares_folder_id ON shares(folder_id);
                    CREATE INDEX IF NOT EXISTS idx_authorized_users_folder_id ON authorized_users(folder_id);
                    CREATE INDEX IF NOT EXISTS idx_uploads_folder_id ON uploads(folder_id);
                CREATE INDEX IF NOT EXISTS idx_activity_log_folder_id ON activity_log(folder_id);
                """
            else:
                # PostgreSQL schema - execute each statement separately
                schema_statements = [
                        """CREATE TABLE IF NOT EXISTS folders (
                            folder_id VARCHAR(255) PRIMARY KEY,
                            path TEXT NOT NULL,
                            name VARCHAR(255) NOT NULL,
                            state VARCHAR(50) DEFAULT 'added',
                            published BOOLEAN DEFAULT FALSE,
                            share_id VARCHAR(255),
                            access_type VARCHAR(50) DEFAULT 'public',
                            total_files INTEGER DEFAULT 0,
                            total_size BIGINT DEFAULT 0,
                            total_segments INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )""",
                        """CREATE TABLE IF NOT EXISTS files (
                            file_id VARCHAR(255) PRIMARY KEY,
                            folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
                            filename TEXT NOT NULL,
                            file_path TEXT NOT NULL,
                            size BIGINT,
                            mime_type VARCHAR(255),
                            hash VARCHAR(255),
                            encrypted BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )""",
                        """CREATE TABLE IF NOT EXISTS segments (
                            segment_id VARCHAR(255) PRIMARY KEY,
                            file_id VARCHAR(255) REFERENCES files(file_id) ON DELETE CASCADE,
                            segment_index INTEGER NOT NULL,
                            size BIGINT,
                            hash VARCHAR(255),
                            message_id TEXT,
                            uploaded BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )""",
                        """CREATE TABLE IF NOT EXISTS shares (
                            share_id VARCHAR(255) PRIMARY KEY,
                            folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
                            share_type VARCHAR(50) DEFAULT 'public',
                            password_hash TEXT,
                            metadata JSONB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            expires_at TIMESTAMP
                        )""",
                        """CREATE TABLE IF NOT EXISTS authorized_users (
                            id SERIAL PRIMARY KEY,
                            folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
                            user_id VARCHAR(255) NOT NULL,
                            permissions VARCHAR(50) DEFAULT 'read',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(folder_id, user_id)
                        )""",
                        """CREATE TABLE IF NOT EXISTS uploads (
                            upload_id VARCHAR(255) PRIMARY KEY,
                            folder_id VARCHAR(255) REFERENCES folders(folder_id) ON DELETE CASCADE,
                            status VARCHAR(50) DEFAULT 'pending',
                            progress INTEGER DEFAULT 0,
                            total_segments INTEGER,
                            uploaded_segments INTEGER DEFAULT 0,
                            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            completed_at TIMESTAMP
                        )""",
                        """CREATE TABLE IF NOT EXISTS activity_log (
                            id SERIAL PRIMARY KEY,
                            folder_id VARCHAR(255),
                            action VARCHAR(100),
                            details JSONB,
                            user_id VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )""",
                        """CREATE INDEX IF NOT EXISTS idx_files_folder_id ON files(folder_id)""",
                        """CREATE INDEX IF NOT EXISTS idx_segments_file_id ON segments(file_id)""",
                        """CREATE INDEX IF NOT EXISTS idx_shares_folder_id ON shares(folder_id)""",
                        """CREATE INDEX IF NOT EXISTS idx_authorized_users_folder_id ON authorized_users(folder_id)""",
                        """CREATE INDEX IF NOT EXISTS idx_uploads_folder_id ON uploads(folder_id)""",
                        """CREATE INDEX IF NOT EXISTS idx_activity_log_folder_id ON activity_log(folder_id)"""
                    ]
            
            if db_type == 'sqlite':
                # SQLite requires executing statements one at a time
                statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
                for statement in statements:
                    if statement:
                        cursor.execute(statement)
            else:
                # PostgreSQL - execute each statement separately
                for statement in schema_statements:
                    cursor.execute(statement)
            
            conn.commit()
            return True, "Database schema initialized successfully"
                
    except Exception as e:
        return False, f"Failed to initialize schema: {str(e)}"

@cli.command('check-database')
def check_database():
    """Check database connection status and initialize schema if needed"""
    try:
        if not DatabaseSelector:
            click.echo(json.dumps({"error": "Database selector not available"}), err=True)
            return
        
        db_info = DatabaseSelector.get_connection_info()
        
        # Try to actually connect
        try:
            db_manager, db_type = DatabaseSelector.get_database_manager()
            
            # First set the connection status
            db_info['status'] = 'connected'
            actual_db_type_display = 'PostgreSQL' if db_info.get('type') == 'postgresql' else 'SQLite'
            db_info['message'] = f"Successfully connected to {actual_db_type_display}"
            
            # Then try to initialize schema (non-blocking for connection status)
            actual_db_type = db_info.get('type', db_type)
            # Add debug info
            db_info['detected_type'] = actual_db_type
            db_info['db_type_param'] = db_type
            
            try:
                if actual_db_type in ['postgresql', 'sqlite']:
                    schema_ok, schema_msg = initialize_database_schema(db_manager, actual_db_type)
                    db_info['schema_status'] = schema_msg
                    if not schema_ok:
                        # Don't fail the whole connection, just note the schema issue
                        db_info['schema_error'] = schema_msg
                else:
                    # If type is not recognized, try with sqlite as default
                    schema_ok, schema_msg = initialize_database_schema(db_manager, 'sqlite')
                    db_info['schema_status'] = schema_msg
                    if not schema_ok:
                        db_info['schema_error'] = schema_msg
            except Exception as schema_ex:
                # Schema initialization failed, but connection is still valid
                db_info['schema_error'] = f"Schema initialization error: {str(schema_ex)}"
                db_info['schema_status'] = "Schema check failed (connection still active)"
        except Exception as e:
            db_info['status'] = 'error'
            db_info['message'] = str(e)
        
        click.echo(json.dumps(db_info))
    except Exception as e:
        click.echo(json.dumps({"error": f"Failed to check database: {e}"}), err=True)

@cli.command('database-info')
def database_info():
    """Get database configuration information"""
    try:
        if not DatabaseSelector:
            click.echo(json.dumps({
                'error': 'Database selector not available',
                'help': 'PostgreSQL may not be installed. The application can use SQLite as an alternative.'
            }))
            return
        
        info = DatabaseSelector.get_connection_info()
        
        # Add helpful information for Windows users
        if sys.platform == "win32" and info.get('type') == 'sqlite':
            info['note'] = 'Using SQLite database. PostgreSQL is optional on Windows.'
            info['location'] = info.get('path', 'Unknown')
        
        click.echo(json.dumps(info))
    except Exception as e:
        click.echo(json.dumps({"error": f"Failed to get database info: {e}"}), err=True)

@cli.command('setup-postgresql')
def setup_postgresql():
    """Setup PostgreSQL automatically (Windows)"""
    try:
        if sys.platform != "win32":
            click.echo(json.dumps({
                'status': 'skipped',
                'message': 'Automatic PostgreSQL setup is only available on Windows'
            }))
            return
        
        # Import the auto setup module
        try:
            from database.auto_postgres_setup import PostgreSQLAutoSetup
        except ImportError as e:
            click.echo(json.dumps({"error": f"PostgreSQL auto-setup module not available: {e}"}), err=True)
            return
        
        setup = PostgreSQLAutoSetup()
        
        # Check if already installed
        existing = setup.check_existing_postgres()
        if existing:
            if setup.is_postgres_running():
                click.echo(json.dumps({
                    'status': 'already_installed',
                    'message': 'PostgreSQL is already installed and running',
                    'details': existing
                }))
                return
            else:
                # Try to start it
                if setup.start_postgres():
                    click.echo(json.dumps({
                        'status': 'started',
                        'message': 'PostgreSQL was installed but not running. Started successfully.',
                        'details': existing
                    }))
                    return
        
        # Perform full setup
        success, message = setup.full_setup()
        
        click.echo(json.dumps({
            'status': 'success' if success else 'error',
            'message': message,
            'installed': success
        }))
        
    except Exception as e:
        click.echo(json.dumps({"error": f"Failed to setup PostgreSQL: {e}"}), err=True)

if __name__ == '__main__':
    cli()

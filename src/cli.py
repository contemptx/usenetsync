#!/usr/bin/env python3
"""
UsenetSync CLI Interface
Bridge between Tauri frontend and Python backend
"""

import click
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import uuid

# Add the src directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import backend modules
from database.postgresql_manager import ShardedPostgreSQLManager, PostgresConfig
from networking.production_nntp_client import ProductionNNTPClient
from security.enhanced_security_system import EnhancedSecuritySystem
from indexing.share_id_generator import ShareIDGenerator
from upload.enhanced_upload import EnhancedUploadSystem
from download.enhanced_download import EnhancedDownloadSystem
from upload.enhanced_upload import EnhancedUploadSystem
from core.integrated_backend import IntegratedBackend, create_integrated_backend

class UsenetSyncCLI:
    def __init__(self):
        self.config = self._load_config()
        self.db_manager = self._init_database()
        self.security = EnhancedSecuritySystem(self.db_manager)
        self.share_generator = ShareIDGenerator()
        self.nntp_client = None
        
        # Initialize integrated backend with all new features
        self.integrated_backend = IntegratedBackend(self.db_manager)
        
    def _load_config(self):
        """Load configuration from file"""
        config_path = Path("/workspace/usenet_sync_config.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}
    
    def _init_database(self):
        """Initialize PostgreSQL connection"""
        config = PostgresConfig(
            host="localhost",
            port=5432,
            database="usenetsync",
            user="usenet",
            password="usenet_secure_2024"
        )
        return ShardedPostgreSQLManager(config)
    
    def _init_nntp(self):
        """Initialize NNTP client"""
        if not self.nntp_client and self.config.get('servers'):
            server = self.config['servers'][0]
            self.nntp_client = ProductionNNTPClient(
                hostname=server['hostname'],
                port=server['port'],
                username=server['username'],
                password=server['password'],
                use_ssl=server['use_ssl']
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
        
        # Generate share ID
        folder_id = str(uuid.uuid4())
        share_id = app.share_generator.generate_share_id(
            folder_id=folder_id,
            share_type=share_type
        )
        
        # Calculate total size
        total_size = sum(Path(f).stat().st_size for f in files if Path(f).exists())
        
        # Create share object
        share = {
            "id": str(uuid.uuid4()),
            "shareId": share_id,
            "type": share_type,
            "name": Path(files[0]).parent.name if files else "Share",
            "size": total_size,
            "fileCount": len(files),
            "folderCount": len(set(Path(f).parent for f in files)),
            "createdAt": datetime.utcnow().isoformat(),
            "expiresAt": None,
            "accessCount": 0,
            "lastAccessed": None
        }
        
        # Save to database
        with app.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO shares (id, share_id, type, name, size, file_count, folder_count, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (share['id'], share['shareId'], share['type'], share['name'],
                  share['size'], share['fileCount'], share['folderCount'], share['createdAt']))
            conn.commit()
        
        # Output JSON
        print(json.dumps(share))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

@cli.command('create-share')
@click.option('--share-id', required=True, help='Share ID to download')
@click.option('--destination', required=True, help='Destination directory')
@click.option('--files', multiple=True, help='Specific files to download')
def download_share(share_id, destination, files):
    """Download a share"""
    try:
        app = UsenetSyncCLI()
        
        # Validate share
        is_valid, _ = app.share_generator.validate_share_id(share_id)
        if not is_valid:
            raise ValueError("Invalid share ID")
        
        # Get share details from database
        with app.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shares WHERE share_id = %s", (share_id,))
            share = cursor.fetchone()
            
            if not share:
                raise ValueError("Share not found")
        
        # Initialize download system
        download_system = EnhancedDownloadSystem(
            db_manager=app.db_manager,
            nntp_client=app._init_nntp(),
            security_system=app.security
        )
        
        # Start actual download
        import asyncio
        loop = asyncio.new_event_loop()
        success = loop.run_until_complete(download_system.download_file(share_id, destination))
        loop.close()
        if success:
            print(json.dumps({"status": "success", "message": f"Downloaded to {destination}"}))
        else:
            print(json.dumps({"status": "error", "message": "Download failed"}), file=sys.stderr)
            sys.exit(1)
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

@cli.command('create-share')
@click.option('--share-id', required=True, help='Share ID')
def share_details(share_id):
    """Get share details"""
    try:
        app = UsenetSyncCLI()
        
        # Get share from database
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
                raise ValueError("Share not found")
                
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
        client = ProductionNNTPClient(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            use_ssl=ssl
        )
        
        # Test connection
        client.connect()
        client.disconnect()
        
        print(json.dumps({"status": "success"}))
        sys.exit(0)
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    cli()
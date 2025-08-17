#!/usr/bin/env python3
"""
UsenetSync - Main Application Entry Point
One-click Usenet synchronization and sharing
"""

import os
import sys
import click
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.secure_config import SecureConfigLoader
from src.database.postgresql_manager import PostgresConfig, ShardedPostgreSQLManager
from src.security.enhanced_security_system import EnhancedSecuritySystem
from src.networking.production_nntp_client import ProductionNNTPClient
from src.monitoring.monitoring_system import MonitoringSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--config', default='config/usenet_sync_config.json', help='Configuration file path')
@click.pass_context
def cli(ctx, config):
    """UsenetSync - Secure Usenet file synchronization and sharing"""
    ctx.ensure_object(dict)
    
    # Load configuration
    config_path = Path(config)
    if not config_path.exists():
        # Use template if config doesn't exist
        template_path = Path('usenet_sync_config.template.json')
        if template_path.exists():
            import shutil
            config_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(template_path, config_path)
            click.echo(f"Created configuration file: {config_path}")
            click.echo("Please edit the configuration with your Usenet server details.")
            sys.exit(1)
    
    ctx.obj['config'] = SecureConfigLoader(str(config_path)).load_config()


@cli.command()
@click.argument('folder_path')
@click.option('--recursive', '-r', is_flag=True, help='Index recursively')
@click.pass_context
def index(ctx, folder_path, recursive):
    """Index a folder for synchronization"""
    click.echo(f"Indexing folder: {folder_path}")
    
    # Initialize database
    pg_config = PostgresConfig(
        embedded=False,
        database="usenet_sync",
        shard_count=4
    )
    
    try:
        db = ShardedPostgreSQLManager(pg_config)
        
        # Initialize indexer
        from src.indexing.parallel_indexer import ParallelIndexer
        indexer = ParallelIndexer(db, worker_count=4)
        
        # Run indexing
        stats = indexer.index_directory(folder_path)
        
        click.echo(f"\n✅ Indexing complete!")
        click.echo(f"   Files indexed: {stats['processed_files']:,}")
        click.echo(f"   Total size: {stats['total_size'] / (1024**2):.2f} MB")
        click.echo(f"   Rate: {stats['files_per_second']:.0f} files/second")
        
    except Exception as e:
        click.echo(f"❌ Indexing failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('folder_id')
@click.option('--type', 'share_type', type=click.Choice(['public', 'private', 'protected']), 
              default='public', help='Share type')
@click.option('--password', help='Password for protected shares')
@click.pass_context
def publish(ctx, folder_id, share_type, password):
    """Publish a folder to Usenet"""
    click.echo(f"Publishing folder {folder_id} as {share_type}")
    
    config = ctx.obj['config']
    
    # Initialize systems
    pg_config = PostgresConfig(
        embedded=False,
        database="usenet_sync",
        shard_count=4
    )
    
    try:
        db = ShardedPostgreSQLManager(pg_config)
        security = EnhancedSecuritySystem(db)
        
        # Initialize NNTP client
        server = config['servers'][0]
        nntp = ProductionNNTPClient(
            host=server['hostname'],
            port=server['port'],
            username=server['username'],
            password=server['password'],
            use_ssl=server['use_ssl']
        )
        
        # Test connection
        with nntp.get_connection() as conn:
            click.echo("✅ Connected to Usenet server")
        
        # Generate share
        from src.indexing.share_id_generator import ShareIDGenerator
        share_gen = ShareIDGenerator()
        
        if share_type == 'public':
            share_id = share_gen.generate_public_share()
        elif share_type == 'private':
            share_id = share_gen.generate_private_share()
        else:  # protected
            if not password:
                password = click.prompt('Enter password', hide_input=True)
            share_id = share_gen.generate_protected_share(password)
        
        click.echo(f"\n✅ Published successfully!")
        click.echo(f"   Share ID: {share_id}")
        click.echo(f"   Type: {share_type}")
        
    except Exception as e:
        click.echo(f"❌ Publishing failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('share_id')
@click.argument('destination')
@click.option('--password', help='Password for protected shares')
@click.pass_context
def download(ctx, share_id, destination, password):
    """Download a shared folder from Usenet"""
    click.echo(f"Downloading share {share_id} to {destination}")
    
    config = ctx.obj['config']
    
    # Initialize systems
    pg_config = PostgresConfig(
        embedded=False,
        database="usenet_sync",
        shard_count=4
    )
    
    try:
        db = ShardedPostgreSQLManager(pg_config)
        security = EnhancedSecuritySystem(db)
        
        # Initialize NNTP client
        server = config['servers'][0]
        nntp = ProductionNNTPClient(
            host=server['hostname'],
            port=server['port'],
            username=server['username'],
            password=server['password'],
            use_ssl=server['use_ssl']
        )
        
        # Initialize download system
        from src.download.enhanced_download_system import EnhancedDownloadSystem
        download_system = EnhancedDownloadSystem(db, nntp, security, config)
        
        # Start download
        result = download_system.download_from_access_string(
            share_id,
            destination,
            password=password
        )
        
        if result:
            click.echo(f"\n✅ Download complete!")
            click.echo(f"   Files downloaded to: {destination}")
        else:
            click.echo(f"❌ Download failed", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Download failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and statistics"""
    config = ctx.obj['config']
    
    # Initialize database
    pg_config = PostgresConfig(
        embedded=False,
        database="usenet_sync",
        shard_count=4
    )
    
    try:
        db = ShardedPostgreSQLManager(pg_config)
        
        # Get statistics
        stats = db.get_statistics()
        
        click.echo("\n📊 System Status")
        click.echo("="*40)
        click.echo(f"Database: PostgreSQL (Sharded)")
        click.echo(f"Shards: {len(stats['shards'])}")
        click.echo(f"Total Segments: {stats['total_segments']:,}")
        click.echo(f"Total Files: {stats['total_files']:,}")
        click.echo(f"Total Size: {stats['total_size'] / (1024**3):.2f} GB")
        
        # Show shard distribution
        click.echo("\nShard Distribution:")
        for shard in stats['shards']:
            click.echo(f"  Shard {shard['shard_id']}: {shard['segments']:,} segments")
        
        # Test NNTP connection
        click.echo("\nNNTP Server Status:")
        server = config['servers'][0]
        try:
            nntp = ProductionNNTPClient(
                host=server['hostname'],
                port=server['port'],
                username=server['username'],
                password=server['password'],
                use_ssl=server['use_ssl']
            )
            with nntp.get_connection() as conn:
                click.echo(f"  ✅ Connected to {server['hostname']}")
        except Exception as e:
            click.echo(f"  ❌ Connection failed: {e}")
        
    except Exception as e:
        click.echo(f"❌ Status check failed: {e}", err=True)
        sys.exit(1)


@cli.command()
def gui():
    """Launch the graphical user interface"""
    click.echo("Launching UsenetSync GUI...")
    
    # Check if Tauri app exists
    gui_path = Path("usenet-sync-app/target/release/usenet-sync-app")
    if sys.platform == "win32":
        gui_path = gui_path.with_suffix(".exe")
    
    if gui_path.exists():
        import subprocess
        subprocess.run([str(gui_path)])
    else:
        click.echo("GUI not found. Please build the Tauri application first.")
        click.echo("Run: cd usenet-sync-app && cargo tauri build")
        sys.exit(1)


@cli.command()
def setup():
    """Run initial setup wizard"""
    click.echo("\n🚀 UsenetSync Setup Wizard")
    click.echo("="*40)
    
    # Get Usenet server details
    click.echo("\nUsenet Server Configuration:")
    server = click.prompt("Server hostname", default="news.newshosting.com")
    port = click.prompt("Port", type=int, default=563)
    username = click.prompt("Username")
    password = click.prompt("Password", hide_input=True)
    use_ssl = click.confirm("Use SSL?", default=True)
    
    # Create configuration
    config = {
        "servers": [{
            "name": "Primary Server",
            "hostname": server,
            "port": port,
            "username": username,
            "password": password,
            "use_ssl": use_ssl,
            "max_connections": 4,
            "enabled": True,
            "priority": 1,
            "posting_group": "alt.binaries.test"
        }],
        "storage": {
            "database_path": "data/usenetsync.db",
            "temp_directory": "temp",
            "log_directory": "logs"
        },
        "security": {
            "encryption_algorithm": "AES-256-GCM",
            "key_derivation": "PBKDF2",
            "iterations": 100000,
            "message_id_domain": None,
            "obfuscate_headers": True
        },
        "performance": {
            "max_upload_threads": 4,
            "max_download_threads": 4,
            "segment_size": 768000,
            "compression_enabled": True
        }
    }
    
    # Save configuration
    import json
    config_path = Path("config/usenet_sync_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    click.echo(f"\n✅ Configuration saved to: {config_path}")
    
    # Initialize database
    click.echo("\nInitializing database...")
    pg_config = PostgresConfig(
        embedded=False,
        database="usenet_sync",
        shard_count=4
    )
    
    try:
        db = ShardedPostgreSQLManager(pg_config)
        stats = db.get_statistics()
        click.echo(f"✅ Database initialized with {pg_config.shard_count} shards")
    except Exception as e:
        click.echo(f"⚠️ Database initialization failed: {e}")
        click.echo("You may need to install PostgreSQL separately.")
    
    click.echo("\n✅ Setup complete! You can now use UsenetSync.")
    click.echo("\nNext steps:")
    click.echo("  1. Index a folder: usenet-sync index /path/to/folder")
    click.echo("  2. Publish it: usenet-sync publish <folder_id>")
    click.echo("  3. Share the access string with others")


if __name__ == '__main__':
    cli()
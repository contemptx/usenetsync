#!/usr/bin/env python3
"""
Command-Line Interface for UsenetSync
Complete implementation with all commands
"""

import click
import json
import sys
import os
from pathlib import Path
from typing import Optional
import logging
from tabulate import tabulate

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import UsenetSync

# Configure logging based on verbosity
def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s' if not verbose else '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

@click.group()
@click.option('-c', '--config', type=click.Path(), help='Configuration file path')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """UsenetSync - Secure Usenet folder synchronization"""
    ctx.ensure_object(dict)
    setup_logging(verbose)
    
    try:
        ctx.obj['app'] = UsenetSync(config)
    except Exception as e:
        click.echo(f"Error initializing UsenetSync: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--name', help='Display name for the user')
@click.pass_context
def init(ctx, name):
    """Initialize user profile"""
    app = ctx.obj['app']
    
    if app.user.is_initialized():
        click.echo("User already initialized!")
        user_id = app.user.get_user_id()
        click.echo(f"User ID: {user_id[:16]}...")
        return
        
    try:
        user_id = app.initialize_user(name)
        click.echo(f"✓ User initialized successfully!")
        click.echo(f"User ID: {user_id[:16]}...")
        click.echo(f"This ID is permanent - keep it safe!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--folder-id', help='Folder ID (auto-generated if not provided)')
@click.option('--reindex', is_flag=True, help='Force re-index of existing folder')
@click.pass_context
def index(ctx, path, folder_id, reindex):
    """Index a folder"""
    app = ctx.obj['app']
    
    if not app.user.is_initialized():
        click.echo("Error: User not initialized. Run 'init' first.", err=True)
        sys.exit(1)
        
    path = Path(path).resolve()
    click.echo(f"Indexing folder: {path}")
    
    # Progress callback
    def progress(info):
        if info.get('phase') == 'scanning':
            click.echo(f"  Scanning... {info.get('files_scanned', 0)} files", nl=False)
            click.echo('\r', nl=False)
        elif info.get('phase') == 'indexing':
            current = info.get('current', 0)
            total = info.get('total', 0)
            if total > 0:
                percent = (current / total) * 100
                click.echo(f"  Indexing: {current}/{total} ({percent:.1f}%)", nl=False)
                click.echo('\r', nl=False)
                
    try:
        result = app.index_folder(str(path), folder_id, progress)
        
        click.echo("\n✓ Indexing complete!")
        click.echo(f"  Folder ID: {result['folder_id']}")
        click.echo(f"  Version: {result['version']}")
        click.echo(f"  Files: {result['files_processed']}")
        click.echo(f"  Size: {result['bytes_processed'] / 1024 / 1024:.2f} MB")
        click.echo(f"  Segments: {result['segments_created']}")
        click.echo(f"  Time: {result['elapsed_time']:.1f}s")
        
        if result.get('files_failed', 0) > 0:
            click.echo(f"  ⚠ Failed files: {result['files_failed']}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('folder-id')
@click.option('--type', 'share_type', 
              type=click.Choice(['public', 'private', 'protected']),
              default='private', help='Share type')
@click.option('--users', multiple=True, help='Authorized user IDs (private shares)')
@click.option('--password', help='Password (protected shares)')
@click.option('--hint', help='Password hint')
@click.pass_context
def publish(ctx, folder_id, share_type, users, password, hint):
    """Publish indexed folder"""
    app = ctx.obj['app']
    
    if share_type == 'private' and not users:
        click.echo("Error: Private shares require --users", err=True)
        sys.exit(1)
        
    if share_type == 'protected' and not password:
        password = click.prompt('Password', hide_input=True, confirmation_prompt=True)
        
    click.echo(f"Publishing folder {folder_id} as {share_type}...")
    
    try:
        result = app.publish_folder(
            folder_id=folder_id,
            share_type=share_type,
            authorized_users=list(users) if users else None,
            password=password,
            password_hint=hint
        )
        
        if result.get('state') == 'published':
            click.echo("\n✓ Folder published successfully!")
            click.echo(f"  Share ID: {result['share_id']}")
            click.echo(f"\n  Access string:")
            click.echo(f"  {result['access_string']}")
            
            # Save to clipboard if available
            try:
                import pyperclip
                pyperclip.copy(result['access_string'])
                click.echo("\n  ✓ Copied to clipboard!")
            except:
                pass
                
        else:
            click.echo(f"Error: Publishing failed - {result.get('error')}", err=True)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('access-string')
@click.option('--dest', type=click.Path(), help='Destination directory')
@click.option('--password', help='Password for protected shares')
@click.pass_context
def download(ctx, access_string, dest, password):
    """Download shared folder"""
    app = ctx.obj['app']
    
    if not dest:
        dest = click.prompt('Destination directory', default='./downloads')
        
    dest = Path(dest).resolve()
    os.makedirs(dest, exist_ok=True)
    
    if not password:
        # Parse access string to check if password needed
        try:
            from share_id_generator import AccessStringManager
            manager = AccessStringManager(app.security)
            parsed = manager.parse_access_string(access_string)
            
            if parsed and parsed.get('share_type') == 'protected':
                if parsed.get('password_hint'):
                    click.echo(f"Password hint: {parsed['password_hint']}")
                password = click.prompt('Password', hide_input=True)
        except:
            pass
            
    click.echo(f"Downloading to: {dest}")
    
    # Progress callback
    def progress(info):
        file_progress = info.get('file_progress', 0)
        overall_progress = info.get('overall_progress', 0)
        speed = info.get('speed_mbps', 0)
        
        click.echo(
            f"  Progress: {overall_progress:.1f}% | "
            f"File: {file_progress:.1f}% | "
            f"Speed: {speed:.1f} MB/s",
            nl=False
        )
        click.echo('\r', nl=False)
        
    try:
        session_id = app.download_folder(access_string, str(dest), password, progress)
        
        # Wait for completion
        import time
        while True:
            status = app.download_system.get_session_status(session_id)
            
            if not status:
                break
                
            if status['state'] in ['completed', 'failed', 'cancelled']:
                click.echo()  # New line after progress
                
                if status['state'] == 'completed':
                    click.echo("\n✓ Download completed!")
                    click.echo(f"  Files: {status['downloaded_files']}/{status['total_files']}")
                    click.echo(f"  Size: {status['downloaded_size'] / 1024 / 1024:.2f} MB")
                else:
                    click.echo(f"\n✗ Download failed: {status.get('error')}", err=True)
                    
                break
                
            time.sleep(0.5)
            
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.pass_context
def list(ctx):
    """List indexed folders"""
    app = ctx.obj['app']
    
    try:
        folders = app.db.get_all_folders()
        
        if not folders:
            click.echo("No folders indexed yet.")
            return
            
        # Prepare table data
        table_data = []
        for folder in folders:
            table_data.append([
                folder['folder_unique_id'][:16] + '...',
                folder['display_name'],
                folder['share_type'],
                f"v{folder['current_version']}",
                f"{folder['file_count']}",
                f"{folder['total_size'] / 1024 / 1024:.1f} MB",
                folder['state']
            ])
            
        headers = ['Folder ID', 'Name', 'Type', 'Version', 'Files', 'Size', 'State']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.pass_context
def status(ctx):
    """Show system status"""
    app = ctx.obj['app']
    
    try:
        status = app.get_status()
        
        # User info
        if status['user']:
            click.echo("User Information:")
            click.echo(f"  ID: {status['user']['user_id'][:16]}...")
            click.echo(f"  Name: {status['user']['display_name']}")
            click.echo(f"  Folders: {status['user']['folders']}")
            click.echo(f"  Files: {status['user']['files']}")
            click.echo(f"  Total Size: {status['user']['total_size'] / 1024 / 1024:.1f} MB")
            
        # Upload queue
        click.echo("\nUpload Queue:")
        queue = status['upload_queue']
        click.echo(f"  Size: {queue['queue_size']}/{queue['max_size']}")
        click.echo(f"  Processed: {queue['mb_processed']:.1f} MB")
        
        # Active operations
        click.echo("\nActive Operations:")
        click.echo(f"  Uploads: {status['active_uploads']['active_sessions']}")
        click.echo(f"  Downloads: {status['active_downloads']['active_sessions']}")
        click.echo(f"  Published Shares: {status['published_shares']['active_shares']}")
        
        # NNTP servers
        click.echo("\nNNTP Servers:")
        try:
            nntp_stats = status.get('nntp_servers', {})
            if 'server_stats' in nntp_stats:
                for server, stats in nntp_stats['server_stats'].items():
                    click.echo(f"  {server}: {stats.get('status', 'unknown')}")
            elif 'connection_pool' in nntp_stats:
                pool_stats = nntp_stats['connection_pool']
                click.echo(f"  Connection Pool: {pool_stats.get('pool_size', 0)}/{pool_stats.get('max_connections', 0)} connections")
            else:
                click.echo("  Status: Ready")
        except Exception as e:
            click.echo("  Status: Connected")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.pass_context
def cleanup(ctx):
    """Clean up temporary files and old data"""
    app = ctx.obj['app']
    
    click.echo("Running cleanup...")
    
    try:
        app.cleanup()
        click.echo("✓ Cleanup complete!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
@click.option('--add', 'action', flag_value='add', help='Add server')
@click.option('--remove', 'action', flag_value='remove', help='Remove server')
@click.option('--list', 'action', flag_value='list', default=True, help='List servers')
@click.option('--hostname', help='Server hostname')
@click.option('--port', type=int, default=563, help='Server port')
@click.option('--username', help='Username')
@click.option('--password', help='Password')
@click.option('--ssl/--no-ssl', default=True, help='Use SSL')
@click.pass_context
def servers(ctx, action, hostname, port, username, password, ssl):
    """Manage NNTP servers"""
    app = ctx.obj['app']
    
    if action == 'add':
        if not hostname:
            hostname = click.prompt('Hostname')
        if not username:
            username = click.prompt('Username')
        if not password:
            password = click.prompt('Password', hide_input=True)
            
        from configuration_manager import ServerConfig
        server = ServerConfig(
            name=hostname,
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            use_ssl=ssl
        )
        
        app.config.add_server(server)
        click.echo(f"✓ Added server: {hostname}")
        
    elif action == 'remove':
        if not hostname:
            hostname = click.prompt('Hostname to remove')
            
        if app.config.remove_server(hostname):
            click.echo(f"✓ Removed server: {hostname}")
        else:
            click.echo(f"Server not found: {hostname}", err=True)
            
    else:  # list
        servers = app.config.get_enabled_servers()
        
        if not servers:
            click.echo("No servers configured.")
            return
            
        table_data = []
        for server in servers:
            table_data.append([
                server.hostname,
                f"{server.port}",
                'SSL' if server.use_ssl else 'Plain',
                f"{server.max_connections}",
                f"{server.priority}",
                '✓' if server.enabled else '✗'
            ])
            
        headers = ['Hostname', 'Port', 'Type', 'Max Conn', 'Priority', 'Enabled']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

# Add command aliases
cli.add_command(init, name='initialize')
cli.add_command(list, name='ls')

if __name__ == '__main__':
    cli()
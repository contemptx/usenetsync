#!/usr/bin/env python3
"""
Command-Line Interface for Unified UsenetSync System
Provides comprehensive CLI management tools
"""

import os
import sys
import json
import click
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
from tabulate import tabulate
import humanize

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unified.unified_system import UnifiedSystem
from unified.monitoring_system import MonitoringSystem
from unified.migration_system import MigrationSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    """Load system configuration"""
    config_file = os.environ.get('USENETSYNC_CONFIG', '/etc/usenetsync/usenetsync.conf')
    
    if not os.path.exists(config_file):
        config_file = os.path.expanduser('~/.usenetsync.conf')
    
    if not os.path.exists(config_file):
        click.echo(f"Configuration file not found: {config_file}", err=True)
        click.echo("Please set USENETSYNC_CONFIG environment variable or create ~/.usenetsync.conf", err=True)
        sys.exit(1)
    
    import configparser
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config', '-c', help='Configuration file path')
@click.pass_context
def cli(ctx, verbose, config):
    """UsenetSync - Unified file synchronization system for Usenet"""
    ctx.ensure_object(dict)
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if config:
        os.environ['USENETSYNC_CONFIG'] = config
    
    # Initialize system
    cfg = load_config()
    db_config = cfg['database']
    
    ctx.obj['system'] = UnifiedSystem(
        db_config.get('type', 'sqlite'),
        host=db_config.get('host'),
        database=db_config.get('database'),
        user=db_config.get('user'),
        password=db_config.get('password'),
        path=db_config.get('path')
    )
    
    ctx.obj['config'] = cfg

# Index commands
@cli.group()
def index():
    """File indexing operations"""
    pass

@index.command('add')
@click.argument('path', type=click.Path(exists=True))
@click.option('--recursive', '-r', is_flag=True, default=True, help='Recursively index folders')
@click.option('--segment-size', '-s', default=768*1024, help='Segment size in bytes')
@click.option('--encrypt', '-e', is_flag=True, default=True, help='Enable encryption')
@click.option('--follow-links', is_flag=True, help='Follow symbolic links')
@click.pass_context
def index_add(ctx, path, recursive, segment_size, encrypt, follow_links):
    """Index files or folders"""
    system = ctx.obj['system']
    
    click.echo(f"Indexing {path}...")
    
    with click.progressbar(length=100, label='Indexing') as bar:
        stats = system.indexer.index_folder(
            path,
            segment_size=segment_size,
            enable_encryption=encrypt
        )
        bar.update(100)
    
    click.echo(f"\n✓ Indexed {stats['files_indexed']} files")
    click.echo(f"  Created {stats['segments_created']} segments")
    click.echo(f"  Total size: {humanize.naturalsize(stats.get('total_size', 0))}")
    
    if stats.get('errors'):
        click.echo(f"  ⚠ {stats['errors']} errors occurred", err=True)

@index.command('list')
@click.option('--folder', '-f', help='Filter by folder ID')
@click.option('--state', '-s', help='Filter by state (indexed, uploaded, etc)')
@click.option('--limit', '-l', default=20, help='Maximum results')
@click.option('--format', '-F', type=click.Choice(['table', 'json', 'csv']), default='table')
@click.pass_context
def index_list(ctx, folder, state, limit, format):
    """List indexed files"""
    system = ctx.obj['system']
    
    query = "SELECT file_hash, file_path, file_size, state, modified_time FROM files WHERE 1=1"
    params = []
    
    if folder:
        query += " AND folder_id = %s"
        params.append(folder)
    
    if state:
        query += " AND state = %s"
        params.append(state)
    
    query += f" LIMIT {limit}"
    
    files = system.db_manager.fetchall(query, params)
    
    if format == 'json':
        click.echo(json.dumps([dict(f) for f in files], indent=2, default=str))
    elif format == 'csv':
        if files:
            headers = files[0].keys()
            click.echo(','.join(headers))
            for f in files:
                click.echo(','.join(str(f[h]) for h in headers))
    else:
        if files:
            # Format for table display
            table_data = []
            for f in files:
                table_data.append([
                    f['file_hash'][:8] + '...',
                    os.path.basename(f['file_path'])[:30],
                    humanize.naturalsize(f['file_size']),
                    f['state'],
                    humanize.naturaltime(f['modified_time'])
                ])
            
            headers = ['Hash', 'Filename', 'Size', 'State', 'Modified']
            click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        else:
            click.echo("No files found")

@index.command('verify')
@click.argument('file_hash')
@click.pass_context
def index_verify(ctx, file_hash):
    """Verify file integrity"""
    system = ctx.obj['system']
    
    file_info = system.db_manager.fetchone(
        "SELECT * FROM files WHERE file_hash = %s",
        (file_hash,)
    )
    
    if not file_info:
        click.echo(f"File not found: {file_hash}", err=True)
        return
    
    click.echo(f"Verifying {file_info['file_path']}...")
    
    # Verify file exists
    if not os.path.exists(file_info['file_path']):
        click.echo("✗ File not found on disk", err=True)
        return
    
    # Verify hash
    import hashlib
    hasher = hashlib.sha256()
    with open(file_info['file_path'], 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    
    calculated_hash = hasher.hexdigest()
    
    if calculated_hash == file_hash:
        click.echo("✓ File integrity verified")
    else:
        click.echo(f"✗ Hash mismatch! Expected: {file_hash}, Got: {calculated_hash}", err=True)

# Upload commands
@cli.group()
def upload():
    """Upload operations"""
    pass

@upload.command('file')
@click.argument('file_hash')
@click.option('--redundancy', '-r', default=20, help='Number of redundant copies')
@click.option('--priority', '-p', default=5, help='Upload priority (1-10)')
@click.pass_context
def upload_file(ctx, file_hash, redundancy, priority):
    """Upload a file to Usenet"""
    system = ctx.obj['system']
    
    file_info = system.db_manager.fetchone(
        "SELECT * FROM files WHERE file_hash = %s",
        (file_hash,)
    )
    
    if not file_info:
        click.echo(f"File not found: {file_hash}", err=True)
        return
    
    click.echo(f"Uploading {file_info['file_path']}...")
    click.echo(f"  Size: {humanize.naturalsize(file_info['file_size'])}")
    click.echo(f"  Segments: {file_info['segment_count']}")
    click.echo(f"  Redundancy: {redundancy} copies")
    
    with click.progressbar(length=file_info['segment_count'], label='Uploading') as bar:
        def progress_callback(current, total):
            bar.update(1)
        
        result = system.uploader.upload_file(
            file_hash,
            redundancy=redundancy,
            progress_callback=progress_callback
        )
    
    if result.get('success'):
        click.echo(f"\n✓ Upload complete")
        click.echo(f"  Duration: {result.get('duration', 0):.1f} seconds")
        click.echo(f"  Throughput: {result.get('throughput', 0):.1f} MB/s")
    else:
        click.echo(f"\n✗ Upload failed: {result.get('error', 'Unknown error')}", err=True)

@upload.command('batch')
@click.argument('input_file', type=click.File('r'))
@click.option('--redundancy', '-r', default=20, help='Number of redundant copies')
@click.option('--parallel', '-p', default=4, help='Parallel uploads')
@click.pass_context
def upload_batch(ctx, input_file, redundancy, parallel):
    """Batch upload files from list"""
    system = ctx.obj['system']
    
    file_hashes = [line.strip() for line in input_file if line.strip()]
    
    click.echo(f"Uploading {len(file_hashes)} files...")
    
    success_count = 0
    error_count = 0
    
    for file_hash in file_hashes:
        click.echo(f"\nUploading {file_hash[:16]}...")
        
        result = system.uploader.upload_file(file_hash, redundancy=redundancy)
        
        if result.get('success'):
            success_count += 1
            click.echo("  ✓ Success")
        else:
            error_count += 1
            click.echo(f"  ✗ Failed: {result.get('error', 'Unknown')}", err=True)
    
    click.echo(f"\nBatch upload complete:")
    click.echo(f"  Success: {success_count}")
    click.echo(f"  Failed: {error_count}")

# Download commands
@cli.group()
def download():
    """Download operations"""
    pass

@download.command('file')
@click.argument('file_hash')
@click.option('--output', '-o', help='Output path')
@click.option('--verify', '-v', is_flag=True, help='Verify after download')
@click.pass_context
def download_file(ctx, file_hash, output, verify):
    """Download a file from Usenet"""
    system = ctx.obj['system']
    
    click.echo(f"Downloading {file_hash}...")
    
    with click.progressbar(length=100, label='Downloading') as bar:
        def progress_callback(current, total):
            bar.update(int(current / total * 100))
        
        result = system.downloader.download_file(
            file_hash,
            output_path=output,
            progress_callback=progress_callback
        )
    
    if result.get('success'):
        click.echo(f"\n✓ Download complete")
        click.echo(f"  Saved to: {result.get('output_path', 'default location')}")
        click.echo(f"  Duration: {result.get('duration', 0):.1f} seconds")
        
        if verify:
            click.echo("Verifying integrity...")
            # Verify hash
            import hashlib
            hasher = hashlib.sha256()
            with open(result['output_path'], 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            
            if hasher.hexdigest() == file_hash:
                click.echo("  ✓ Integrity verified")
            else:
                click.echo("  ✗ Integrity check failed!", err=True)
    else:
        click.echo(f"\n✗ Download failed: {result.get('error', 'Unknown error')}", err=True)

# Publish commands
@cli.group()
def publish():
    """Publishing operations"""
    pass

@publish.command('file')
@click.argument('file_hash')
@click.option('--access', '-a', type=click.Choice(['public', 'private', 'restricted']), default='public')
@click.option('--expiry', '-e', type=int, help='Days until expiry')
@click.option('--password', '-p', help='Password for protected access')
@click.pass_context
def publish_file(ctx, file_hash, access, expiry, password):
    """Publish a file for sharing"""
    system = ctx.obj['system']
    
    result = system.publisher.publish_file(
        file_hash,
        access_level=access,
        expiry_days=expiry,
        password=password
    )
    
    if result.get('success'):
        click.echo(f"✓ File published successfully")
        click.echo(f"  Publication ID: {result['publication_id']}")
        click.echo(f"  Access level: {access}")
        if expiry:
            click.echo(f"  Expires in: {expiry} days")
        
        # Generate share URL
        base_url = ctx.obj['config'].get('publishing', {}).get('base_url', 'http://localhost:8000')
        share_url = f"{base_url}/api/v1/published/{result['publication_id']}"
        click.echo(f"  Share URL: {share_url}")
    else:
        click.echo(f"✗ Publishing failed: {result.get('error', 'Unknown error')}", err=True)

@publish.command('list')
@click.option('--access', '-a', help='Filter by access level')
@click.option('--active', is_flag=True, help='Show only active publications')
@click.pass_context
def publish_list(ctx, access, active):
    """List published files"""
    system = ctx.obj['system']
    
    query = "SELECT * FROM publications WHERE 1=1"
    params = []
    
    if access:
        query += " AND access_level = %s"
        params.append(access)
    
    if active:
        query += " AND (expiry_time IS NULL OR expiry_time > CURRENT_TIMESTAMP)"
    
    query += " ORDER BY published_time DESC LIMIT 50"
    
    publications = system.db_manager.fetchall(query, params)
    
    if publications:
        table_data = []
        for pub in publications:
            table_data.append([
                pub['publication_id'][:8] + '...',
                pub['file_hash'][:8] + '...',
                pub['access_level'],
                humanize.naturaltime(pub['published_time']),
                humanize.naturaltime(pub['expiry_time']) if pub['expiry_time'] else 'Never'
            ])
        
        headers = ['Pub ID', 'File Hash', 'Access', 'Published', 'Expires']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
    else:
        click.echo("No publications found")

# System commands
@cli.group()
def system():
    """System management operations"""
    pass

@system.command('status')
@click.pass_context
def system_status(ctx):
    """Show system status"""
    system = ctx.obj['system']
    
    stats = system.get_statistics()
    
    click.echo("System Status")
    click.echo("=" * 50)
    
    # Database info
    click.echo(f"\nDatabase:")
    click.echo(f"  Type: {system.db_type}")
    click.echo(f"  Connected: {'Yes' if system.db_manager.connection else 'No'}")
    
    # Statistics
    click.echo(f"\nStatistics:")
    click.echo(f"  Total files: {stats.get('total_files', 0):,}")
    click.echo(f"  Total size: {humanize.naturalsize(stats.get('total_size', 0))}")
    click.echo(f"  Total segments: {stats.get('total_segments', 0):,}")
    
    # State breakdown
    click.echo(f"\nFile states:")
    for state, count in stats.get('state_counts', {}).items():
        click.echo(f"  {state}: {count:,}")
    
    # Recent activity
    click.echo(f"\nRecent activity:")
    click.echo(f"  Files indexed (24h): {stats.get('recent_indexed', 0):,}")
    click.echo(f"  Files uploaded (24h): {stats.get('recent_uploaded', 0):,}")
    click.echo(f"  Files downloaded (24h): {stats.get('recent_downloaded', 0):,}")

@system.command('monitor')
@click.option('--interval', '-i', default=1, help='Update interval in seconds')
@click.pass_context
def system_monitor(ctx, interval):
    """Real-time system monitoring"""
    monitoring = MonitoringSystem()
    monitoring.start(prometheus_port=0)
    
    try:
        while True:
            os.system('clear')
            
            status = monitoring.get_system_status()
            dashboard = monitoring.get_dashboard_data()
            
            click.echo("UsenetSync System Monitor")
            click.echo("=" * 60)
            click.echo(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # System metrics
            click.echo(f"\nSystem Metrics:")
            click.echo(f"  CPU Usage: {status.get('cpu_usage', 0):.1f}%")
            click.echo(f"  Memory: {status.get('memory_mb', 0):.1f} MB")
            click.echo(f"  Threads: {status.get('threads', 0)}")
            click.echo(f"  Connections: {status.get('connections', 0)}")
            
            # Operation statistics
            ops = dashboard.get('operation_stats', {})
            if ops:
                click.echo(f"\nOperations (last hour):")
                for op_name, op_stats in ops.items():
                    click.echo(f"  {op_name.capitalize()}:")
                    click.echo(f"    Success: {op_stats.get('success', 0)}")
                    click.echo(f"    Failure: {op_stats.get('failure', 0)}")
                    click.echo(f"    Avg duration: {op_stats.get('avg_duration', 0):.2f}s")
            
            # Recent alerts
            alerts = dashboard.get('recent_alerts', [])
            if alerts:
                click.echo(f"\nRecent Alerts:")
                for alert in alerts[-5:]:
                    click.echo(f"  [{alert['severity']}] {alert['message']}")
            
            click.echo("\nPress Ctrl+C to exit")
            
            import time
            time.sleep(interval)
            
    except KeyboardInterrupt:
        monitoring.stop()
        click.echo("\nMonitoring stopped")

@system.command('optimize')
@click.pass_context
def system_optimize(ctx):
    """Optimize database performance"""
    system = ctx.obj['system']
    
    click.echo("Optimizing database...")
    
    if system.db_type == 'sqlite':
        system.db_manager.execute("VACUUM")
        system.db_manager.execute("ANALYZE")
        click.echo("✓ SQLite database optimized (VACUUM and ANALYZE completed)")
    elif system.db_type == 'postgresql':
        system.db_manager.execute("VACUUM ANALYZE")
        click.echo("✓ PostgreSQL database optimized (VACUUM ANALYZE completed)")
    
    # Get database size
    if system.db_type == 'sqlite':
        db_path = system.db_manager.db_path
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            click.echo(f"  Database size: {humanize.naturalsize(size)}")

@system.command('backup')
@click.argument('output_path', type=click.Path())
@click.option('--compress', '-c', is_flag=True, help='Compress backup')
@click.pass_context
def system_backup(ctx, output_path, compress):
    """Backup database"""
    system = ctx.obj['system']
    
    click.echo(f"Creating backup to {output_path}...")
    
    if system.db_type == 'sqlite':
        import shutil
        
        # Use SQLite backup API
        import sqlite3
        source = sqlite3.connect(system.db_manager.db_path)
        dest = sqlite3.connect(output_path)
        
        with dest:
            source.backup(dest)
        
        source.close()
        dest.close()
        
        if compress:
            import gzip
            with open(output_path, 'rb') as f_in:
                with gzip.open(f"{output_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(output_path)
            output_path = f"{output_path}.gz"
        
        size = os.path.getsize(output_path)
        click.echo(f"✓ Backup created: {output_path} ({humanize.naturalsize(size)})")
        
    elif system.db_type == 'postgresql':
        # Use pg_dump
        import subprocess
        
        cmd = [
            'pg_dump',
            '-h', system.db_manager.host,
            '-d', system.db_manager.database,
            '-U', system.db_manager.user,
            '-f', output_path
        ]
        
        if compress:
            cmd.extend(['-Z', '9'])
            output_path = f"{output_path}.gz"
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            size = os.path.getsize(output_path)
            click.echo(f"✓ Backup created: {output_path} ({humanize.naturalsize(size)})")
        else:
            click.echo(f"✗ Backup failed: {result.stderr}", err=True)

# Migration commands
@cli.group()
def migrate():
    """Data migration operations"""
    pass

@migrate.command('import')
@click.option('--old-indexing', type=click.Path(exists=True), help='Old indexing database')
@click.option('--old-upload', type=click.Path(exists=True), help='Old upload database')
@click.option('--backup-dir', type=click.Path(), help='Backup directory')
@click.pass_context
def migrate_import(ctx, old_indexing, old_upload, backup_dir):
    """Import data from old system"""
    system = ctx.obj['system']
    
    migration = MigrationSystem(
        old_indexing_db=old_indexing,
        old_upload_db=old_upload,
        target_db_type=system.db_type,
        backup_dir=backup_dir
    )
    
    click.echo("Starting migration...")
    
    with click.progressbar(length=100, label='Migrating') as bar:
        def progress_callback(current, total):
            bar.update(int(current / total * 100))
        
        stats = migration.migrate(progress_callback=progress_callback)
    
    click.echo(f"\n✓ Migration complete")
    click.echo(f"  Files migrated: {stats['files_migrated']:,}")
    click.echo(f"  Segments migrated: {stats['segments_migrated']:,}")
    click.echo(f"  Publications migrated: {stats.get('publications_migrated', 0):,}")
    
    if stats.get('errors'):
        click.echo(f"  ⚠ {len(stats['errors'])} errors occurred", err=True)

# Main entry point
def main():
    """Main CLI entry point"""
    try:
        cli(obj={})
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
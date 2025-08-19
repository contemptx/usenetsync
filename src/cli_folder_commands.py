"""
Additional folder management CLI commands
"""

import click
import json
import sys

@click.group()
def cli():
    pass

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
def delete_folder(folder_id):
    """Delete a managed folder"""
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

if __name__ == '__main__':
    cli()
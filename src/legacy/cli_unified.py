#!/usr/bin/env python3
"""
Drop-in replacement for cli.py that uses the unified backend
Maintains CLI compatibility while using the new unified system
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add to path
sys.path.insert(0, os.path.dirname(__file__))

# Import unified system
from unified.main import UnifiedSystem

# Global system instance
SYSTEM = None

def get_system():
    """Get or create system instance"""
    global SYSTEM
    if SYSTEM is None:
        SYSTEM = UnifiedSystem()
    return SYSTEM

def create_user(args):
    """Create a new user"""
    system = get_system()
    user = system.user_manager.create_user(args.username, args.email)
    return {'success': True, 'user': user}

def index_folder(args):
    """Index a folder"""
    system = get_system()
    result = system.indexing.index_folder(args.path, args.owner_id)
    return {'success': True, 'result': result}

def create_share(args):
    """Create a share"""
    system = get_system()
    
    # Convert files to list
    files = args.files if isinstance(args.files, list) else [args.files]
    
    # Create share based on type
    if args.type == 'public':
        share = system.publishing.create_public_share(files[0], args.owner_id)
    elif args.type == 'private':
        share = system.publishing.create_private_share(
            files[0], args.owner_id, 
            allowed_users=args.allowed_users.split(',') if args.allowed_users else []
        )
    elif args.type == 'protected':
        share = system.publishing.create_protected_share(
            files[0], args.owner_id, args.password
        )
    else:
        return {'success': False, 'error': f'Unknown share type: {args.type}'}
    
    # Return in expected format
    return {
        'id': share['share_id'],
        'shareId': share['share_id'],
        'type': args.type,
        'name': Path(files[0]).name,
        'size': 0,
        'fileCount': len(files),
        'folderCount': 0,
        'createdAt': share.get('created_at', ''),
        'expiresAt': share.get('expires_at', None),
        'accessCount': 0,
        'lastAccessed': None
    }

def list_shares(args):
    """List all shares"""
    system = get_system()
    shares = system.publishing.get_shares(args.owner_id if hasattr(args, 'owner_id') else None)
    
    # Convert to expected format
    formatted_shares = []
    for share in shares:
        formatted_shares.append({
            'id': share['share_id'],
            'shareId': share['share_id'],
            'type': share.get('access_level', 'public').lower(),
            'name': share.get('name', 'Unknown'),
            'size': share.get('size', 0),
            'fileCount': share.get('file_count', 0),
            'folderCount': share.get('folder_count', 0),
            'createdAt': share.get('created_at', ''),
            'expiresAt': share.get('expires_at', None),
            'accessCount': share.get('access_count', 0),
            'lastAccessed': share.get('last_accessed', None)
        })
    
    return formatted_shares

def upload_folder(args):
    """Upload a folder"""
    system = get_system()
    result = system.upload.upload_folder(args.folder_id)
    return {'success': True, 'result': result}

def download_share(args):
    """Download a share"""
    system = get_system()
    result = system.download.download_share(
        args.share_id,
        args.output_path if hasattr(args, 'output_path') else './downloads'
    )
    return {'success': True, 'result': result}

def get_status(args):
    """Get system status"""
    system = get_system()
    status = system.monitoring.get_status()
    return status

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='UsenetSync Unified CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create user
    user_parser = subparsers.add_parser('create-user', help='Create a new user')
    user_parser.add_argument('username', help='Username')
    user_parser.add_argument('--email', help='Email address')
    
    # Index folder
    index_parser = subparsers.add_parser('index-folder', help='Index a folder')
    index_parser.add_argument('path', help='Folder path')
    index_parser.add_argument('--owner-id', help='Owner user ID')
    
    # Create share
    share_parser = subparsers.add_parser('create-share', help='Create a share')
    share_parser.add_argument('--files', action='append', help='Files to share')
    share_parser.add_argument('--type', default='public', choices=['public', 'private', 'protected'])
    share_parser.add_argument('--password', help='Password for protected share')
    share_parser.add_argument('--owner-id', help='Owner user ID')
    share_parser.add_argument('--allowed-users', help='Comma-separated user IDs for private share')
    
    # List shares
    list_parser = subparsers.add_parser('list-shares', help='List shares')
    list_parser.add_argument('--owner-id', help='Filter by owner')
    
    # Upload
    upload_parser = subparsers.add_parser('upload', help='Upload folder')
    upload_parser.add_argument('folder_id', help='Folder ID to upload')
    
    # Download
    download_parser = subparsers.add_parser('download', help='Download share')
    download_parser.add_argument('share_id', help='Share ID to download')
    download_parser.add_argument('--output-path', default='./downloads', help='Output path')
    
    # Status
    status_parser = subparsers.add_parser('status', help='Get system status')
    
    args = parser.parse_args()
    
    # Route to appropriate handler
    handlers = {
        'create-user': create_user,
        'index-folder': index_folder,
        'create-share': create_share,
        'list-shares': list_shares,
        'upload': upload_folder,
        'download': download_share,
        'status': get_status
    }
    
    if args.command in handlers:
        try:
            result = handlers[args.command](args)
            print(json.dumps(result, indent=2))
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e)
            }
            print(json.dumps(error_result, indent=2))
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
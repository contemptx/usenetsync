#!/usr/bin/env python3
"""
GitHub Update Script for UsenetSync
Provides granular control over updating specific components
"""

import os
import sys
import json
import logging
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubUpdater:
    """Handles selective GitHub updates"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.modified_files = set()
        self.component_map = {
            'core': {
                'main.py',
                'cli.py',
                'setup.py',
                'requirements.txt'
            },
            'database': {
                'enhanced_database_manager.py',
                'production_db_wrapper.py',
                'database_config.py',
                'database_schema.sql'
            },
            'security': {
                'enhanced_security_system.py',
                'user_management.py'
            },
            'upload': {
                'enhanced_upload_system.py',
                'upload_queue_manager.py',
                'segment_packing_system.py'
            },
            'download': {
                'enhanced_download_system.py',
                'segment_retrieval_system.py'
            },
            'publishing': {
                'publishing_system.py',
                'versioned_core_index_system.py',
                'simplified_binary_index.py'
            },
            'networking': {
                'production_nntp_client.py'
            },
            'monitoring': {
                'monitoring_system.py'
            },
            'config': {
                'configuration_manager.py',
                'usenet_sync_config.json'
            },
            'tests': {
                'production_multi_user_test.py',
                'fixed_production_test.py',
                'integration_test_real.py'
            },
            'integration': {
                'usenet_sync_integrated.py'
            }
        }
    
    def detect_modified_files(self) -> Set[str]:
        """Detect files modified since last commit"""
        try:
            # Get modified files
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD'], 
                capture_output=True, text=True, cwd=self.project_root
            )
            
            if result.returncode == 0:
                modified = set(result.stdout.strip().split('\n'))
                modified.discard('')  # Remove empty strings
                return modified
            
            # Fallback: get all untracked and modified files
            result = subprocess.run(
                ['git', 'status', '--porcelain'], 
                capture_output=True, text=True, cwd=self.project_root
            )
            
            if result.returncode == 0:
                modified = set()
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        # Extract filename from git status output
                        filename = line[3:].strip()
                        modified.add(filename)
                return modified
            
            return set()
            
        except Exception as e:
            logger.error(f"Failed to detect modified files: {e}")
            return set()
    
    def get_components_for_files(self, files: Set[str]) -> Set[str]:
        """Get component names for given files"""
        components = set()
        
        for file_path in files:
            filename = Path(file_path).name
            for component, component_files in self.component_map.items():
                if filename in component_files:
                    components.add(component)
                    break
        
        return components
    
    def get_files_for_components(self, components: List[str]) -> Set[str]:
        """Get all files for given components"""
        files = set()
        
        for component in components:
            if component in self.component_map:
                files.update(self.component_map[component])
            else:
                logger.warning(f"Unknown component: {component}")
        
        return files
    
    def validate_files_exist(self, files: Set[str]) -> Set[str]:
        """Validate that files exist and return existing files"""
        existing_files = set()
        
        for filename in files:
            file_path = self.project_root / filename
            if file_path.exists():
                existing_files.add(filename)
            else:
                logger.warning(f"File not found: {filename}")
        
        return existing_files
    
    def update_specific_files(self, files: Set[str], commit_message: str = None) -> bool:
        """Update specific files to GitHub"""
        if not files:
            logger.warning("No files to update")
            return True
        
        try:
            # Validate files exist
            existing_files = self.validate_files_exist(files)
            if not existing_files:
                logger.error("No valid files found to update")
                return False
            
            # Add files to git
            for filename in existing_files:
                cmd = ['git', 'add', filename]
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
                if result.returncode != 0:
                    logger.error(f"Failed to add {filename}: {result.stderr}")
                    return False
            
            # Check if there are changes to commit
            result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=self.project_root)
            if result.returncode == 0:
                logger.info("No changes to commit")
                return True
            
            # Create commit message
            if not commit_message:
                components = self.get_components_for_files(existing_files)
                if components:
                    component_list = ', '.join(sorted(components))
                    commit_message = f"Update {component_list} components"
                else:
                    commit_message = f"Update {len(existing_files)} files"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_message = f"{commit_message} - {timestamp}"
            
            # Commit changes
            cmd = ['git', 'commit', '-m', full_message]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                logger.error(f"Commit failed: {result.stderr}")
                return False
            
            logger.info(f"Committed: {full_message}")
            
            # Push changes
            cmd = ['git', 'push']
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                logger.error(f"Push failed: {result.stderr}")
                return False
            
            logger.info("Changes pushed to GitHub successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update files: {e}")
            return False
    
    def update_components(self, components: List[str], commit_message: str = None) -> bool:
        """Update specific components"""
        files = self.get_files_for_components(components)
        
        if not commit_message:
            commit_message = f"Update {', '.join(components)} components"
        
        return self.update_specific_files(files, commit_message)
    
    def update_modified(self) -> bool:
        """Update only modified files"""
        modified_files = self.detect_modified_files()
        
        if not modified_files:
            logger.info("No modified files detected")
            return True
        
        logger.info(f"Detected {len(modified_files)} modified files:")
        for filename in sorted(modified_files):
            logger.info(f"  {filename}")
        
        components = self.get_components_for_files(modified_files)
        if components:
            logger.info(f"Affected components: {', '.join(sorted(components))}")
        
        return self.update_specific_files(modified_files, "Update modified files")
    
    def list_components(self):
        """List all available components"""
        print("\nAvailable components:")
        print("=" * 50)
        
        for component, files in self.component_map.items():
            print(f"\n{component}:")
            for filename in sorted(files):
                exists = "✓" if (self.project_root / filename).exists() else "✗"
                print(f"  {exists} {filename}")
        
        print(f"\nTotal: {len(self.component_map)} components")
    
    def status(self):
        """Show repository status"""
        try:
            # Git status
            result = subprocess.run(['git', 'status', '--short'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                if result.stdout.strip():
                    print("Modified files:")
                    print(result.stdout)
                else:
                    print("No modified files")
            
            # Last commit
            result = subprocess.run(['git', 'log', '-1', '--oneline'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print(f"\nLast commit: {result.stdout.strip()}")
            
            # Remote info
            result = subprocess.run(['git', 'remote', '-v'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print(f"\nRemotes:\n{result.stdout}")
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Update UsenetSync components on GitHub')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Update modified files
    modified_parser = subparsers.add_parser('modified', help='Update modified files')
    modified_parser.add_argument('--message', '-m', help='Commit message')
    
    # Update specific components
    components_parser = subparsers.add_parser('components', help='Update specific components')
    components_parser.add_argument('components', nargs='+', help='Component names')
    components_parser.add_argument('--message', '-m', help='Commit message')
    
    # Update specific files
    files_parser = subparsers.add_parser('files', help='Update specific files')
    files_parser.add_argument('files', nargs='+', help='File names')
    files_parser.add_argument('--message', '-m', help='Commit message')
    
    # List components
    subparsers.add_parser('list', help='List available components')
    
    # Show status
    subparsers.add_parser('status', help='Show repository status')
    
    # Global options
    parser.add_argument('--project-root', help='Project root directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        updater = GitHubUpdater(args.project_root)
        
        if args.command == 'modified':
            success = updater.update_modified()
        elif args.command == 'components':
            success = updater.update_components(args.components, args.message)
        elif args.command == 'files':
            files = set(args.files)
            success = updater.update_specific_files(files, args.message)
        elif args.command == 'list':
            updater.list_components()
            success = True
        elif args.command == 'status':
            updater.status()
            success = True
        else:
            logger.error(f"Unknown command: {args.command}")
            success = False
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Update interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Update failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

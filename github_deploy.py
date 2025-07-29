#!/usr/bin/env python3
"""
GitHub Deployment Script for UsenetSync
Automatically deploys all project files to GitHub with proper structure
"""

import os
import sys
import json
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubDeployer:
    """Handles GitHub deployment operations"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config_file = self.project_root / "deploy_config.json"
        self.config = self.load_config()
        
        # Core files that must be included
        self.core_files = {
            'main.py',
            'setup.py',
            'requirements.txt',
            'README.md',
            'LICENSE',
            'database_schema.sql',
            'usenet_sync_config.json',
            'cli.py'
        }
        
        # Production modules
        self.production_modules = {
            'enhanced_database_manager.py',
            'production_db_wrapper.py',
            'enhanced_security_system.py',
            'production_nntp_client.py',
            'segment_packing_system.py',
            'enhanced_upload_system.py',
            'versioned_core_index_system.py',
            'simplified_binary_index.py',
            'enhanced_download_system.py',
            'publishing_system.py',
            'user_management.py',
            'configuration_manager.py',
            'monitoring_system.py',
            'segment_retrieval_system.py',
            'upload_queue_manager.py',
            'usenet_sync_integrated.py',
            'database_config.py'
        }
        
        # Test files
        self.test_files = {
            'production_multi_user_test.py',
            'fixed_production_test.py',
            'integration_test_real.py'
        }
        
        # Documentation files
        self.doc_files = {
            'ARCHITECTURE.md',
            'API_REFERENCE.md',
            'DEPLOYMENT_GUIDE.md',
            'SECURITY_OVERVIEW.md'
        }
    
    def load_config(self) -> Dict:
        """Load deployment configuration"""
        default_config = {
            "repository": {
                "url": "",
                "branch": "main",
                "remote": "origin"
            },
            "deployment": {
                "auto_commit": True,
                "commit_message_template": "Production deployment - {timestamp}",
                "create_release": False,
                "tag_format": "v{version}",
                "exclude_patterns": [
                    "*.pyc",
                    "__pycache__",
                    "*.log",
                    ".vscode",
                    ".idea",
                    "node_modules",
                    "venv",
                    ".env",
                    "secure_config.py",
                    "*.db",
                    "data/*",
                    "logs/*",
                    "temp/*",
                    ".temp/*",
                    "upload/*",
                    "download/*"
                ]
            },
            "github": {
                "create_workflows": True,
                "create_issues_templates": True,
                "create_pr_template": True
            },
            "validation": {
                "check_syntax": True,
                "run_tests": False,
                "lint_code": False
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Could not load config: {e}, using defaults")
        else:
            # Create default config
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default config: {self.config_file}")
        
        return default_config
    
    def validate_git_repo(self) -> bool:
        """Validate Git repository setup"""
        try:
            # Check if git is installed
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode != 0:
                logger.error("Git is not installed or not in PATH")
                return False
            
            # Check if we're in a git repo
            result = subprocess.run(['git', 'status'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode != 0:
                logger.warning("Not in a Git repository, initializing...")
                return self.init_git_repo()
            
            # Check for remote
            result = subprocess.run(['git', 'remote', '-v'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if not result.stdout.strip():
                logger.warning("No remote repository configured")
                return self.setup_remote()
            
            return True
            
        except Exception as e:
            logger.error(f"Git validation failed: {e}")
            return False
    
    def init_git_repo(self) -> bool:
        """Initialize Git repository"""
        try:
            commands = [
                ['git', 'init'],
                ['git', 'config', 'user.name', 'UsenetSync Deployer'],
                ['git', 'config', 'user.email', 'deploy@usenetsync.local']
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
                if result.returncode != 0:
                    logger.error(f"Command failed: {' '.join(cmd)}: {result.stderr}")
                    return False
            
            logger.info("Git repository initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Git repo: {e}")
            return False
    
    def setup_remote(self) -> bool:
        """Setup remote repository"""
        repo_url = self.config['repository'].get('url')
        if not repo_url:
            logger.error("No repository URL configured in deploy_config.json")
            logger.info("Please set repository.url in the config file")
            return False
        
        try:
            remote_name = self.config['repository'].get('remote', 'origin')
            cmd = ['git', 'remote', 'add', remote_name, repo_url]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                logger.error(f"Failed to add remote: {result.stderr}")
                return False
            
            logger.info(f"Added remote '{remote_name}': {repo_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup remote: {e}")
            return False
    
    def collect_project_files(self) -> Dict[str, List[Path]]:
        """Collect all project files to deploy"""
        files_to_deploy = {
            'core': [],
            'modules': [],
            'tests': [],
            'docs': [],
            'config': [],
            'other': []
        }
        
        exclude_patterns = self.config['deployment']['exclude_patterns']
        
        # Scan project directory
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(self.project_root)
                
                # Check exclusion patterns
                if self.should_exclude_file(relative_path, exclude_patterns):
                    continue
                
                # Categorize files
                file_name = file_path.name
                if file_name in self.core_files:
                    files_to_deploy['core'].append(relative_path)
                elif file_name in self.production_modules:
                    files_to_deploy['modules'].append(relative_path)
                elif file_name in self.test_files:
                    files_to_deploy['tests'].append(relative_path)
                elif file_name in self.doc_files or file_path.suffix == '.md':
                    files_to_deploy['docs'].append(relative_path)
                elif file_path.suffix in ['.json', '.yml', '.yaml', '.ini', '.cfg']:
                    files_to_deploy['config'].append(relative_path)
                elif file_path.suffix == '.py':
                    files_to_deploy['other'].append(relative_path)
        
        return files_to_deploy
    
    def should_exclude_file(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if file should be excluded"""
        path_str = str(file_path).replace('\\', '/')
        
        for pattern in exclude_patterns:
            if pattern.endswith('/*'):
                # Directory pattern
                dir_pattern = pattern[:-2]
                if path_str.startswith(dir_pattern + '/'):
                    return True
            elif '*' in pattern:
                # Glob pattern (simplified check)
                if pattern.startswith('*.'):
                    ext = pattern[1:]
                    if path_str.endswith(ext):
                        return True
            elif pattern in path_str:
                return True
        
        return False
    
    def validate_python_files(self, file_list: List[Path]) -> bool:
        """Validate Python syntax"""
        if not self.config['validation']['check_syntax']:
            return True
        
        logger.info("Validating Python syntax...")
        errors = []
        
        for file_path in file_list:
            if file_path.suffix != '.py':
                continue
            
            full_path = self.project_root / file_path
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                compile(content, str(file_path), 'exec')
            except SyntaxError as e:
                errors.append(f"{file_path}: {e}")
            except UnicodeDecodeError as e:
                errors.append(f"{file_path}: Unicode decode error: {e}")
            except Exception as e:
                errors.append(f"{file_path}: {e}")
        
        if errors:
            logger.error("Syntax validation failed:")
            for error in errors:
                logger.error(f"  {error}")
            return False
        
        logger.info("Syntax validation passed")
        return True
    
    def create_github_workflows(self):
        """Create GitHub Actions workflows"""
        if not self.config['github']['create_workflows']:
            return
        
        workflows_dir = self.project_root / '.github' / 'workflows'
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # CI workflow
        ci_workflow = workflows_dir / 'ci.yml'
        ci_content = """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    
    - name: Test syntax
      run: |
        python -m py_compile *.py
"""
        
        with open(ci_workflow, 'w') as f:
            f.write(ci_content)
        
        logger.info("Created GitHub CI workflow")
    
    def create_github_templates(self):
        """Create GitHub issue and PR templates"""
        if not self.config['github']['create_issues_templates']:
            return
        
        github_dir = self.project_root / '.github'
        github_dir.mkdir(exist_ok=True)
        
        # Pull request template
        if self.config['github']['create_pr_template']:
            pr_template = github_dir / 'pull_request_template.md'
            pr_content = """## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for features
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No hardcoded values or credentials
"""
            
            with open(pr_template, 'w') as f:
                f.write(pr_content)
    
    def create_requirements_txt(self):
        """Create requirements.txt from setup.py"""
        setup_py = self.project_root / 'setup.py'
        requirements_txt = self.project_root / 'requirements.txt'
        
        if setup_py.exists() and not requirements_txt.exists():
            # Extract requirements from setup.py
            requirements = [
                "click>=8.0.0",
                "cryptography>=3.4.0",
                "psutil>=5.8.0",
                "PyYAML>=5.4.0",
                "tabulate>=0.8.0",
                "colorama>=0.4.4"
            ]
            
            with open(requirements_txt, 'w') as f:
                f.write('\n'.join(requirements))
            
            logger.info("Created requirements.txt")
    
    def create_readme(self):
        """Create comprehensive README.md"""
        readme_path = self.project_root / 'README.md'
        
        if readme_path.exists():
            return
        
        readme_content = """# UsenetSync

Secure Usenet folder synchronization system with end-to-end encryption and scalable architecture.

## Features

- **Secure Synchronization**: End-to-end encrypted folder sharing via Usenet
- **Scalable Architecture**: Handles millions of files efficiently
- **Multiple Share Types**: Public, private, and password-protected shares
- **Production Ready**: Comprehensive error handling, logging, and monitoring
- **Cross-Platform**: Works on Windows, Linux, and macOS

## Quick Start

### Installation

```bash
pip install -r requirements.txt
python setup.py install
```

### Configuration

1. Copy `usenet_sync_config.json.example` to `usenet_sync_config.json`
2. Configure your NNTP server settings
3. Set up your folders and newsgroups

### Usage

```bash
# Index a folder
usenetsync index /path/to/folder

# Publish as private share
usenetsync publish folder_id --type private --users user1,user2

# Download a share
usenetsync download SHARE_ACCESS_STRING
```

## Architecture

- **Database Layer**: SQLite with connection pooling and transaction management
- **Security Layer**: RSA/AES encryption with secure key management
- **Upload System**: Segmented file uploads with retry logic
- **Download System**: Parallel segment retrieval and reconstruction
- **Monitoring**: Comprehensive logging and performance metrics

## Security

- End-to-end encryption for all shared content
- Zero-knowledge proofs for user authorization
- Secure key exchange using RSA encryption
- AES-256 encryption for file content

## Requirements

- Python 3.8+
- NNTP server access
- SQLite 3.x

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions, please use the GitHub issue tracker.
"""
        
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        logger.info("Created README.md")
    
    def stage_and_commit_files(self, files_dict: Dict[str, List[Path]]) -> bool:
        """Stage and commit files to Git"""
        try:
            # Stage all files
            all_files = []
            for category, file_list in files_dict.items():
                all_files.extend(file_list)
            
            if not all_files:
                logger.warning("No files to deploy")
                return False
            
            # Add files to git
            for file_path in all_files:
                cmd = ['git', 'add', str(file_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
                if result.returncode != 0:
                    logger.warning(f"Could not add {file_path}: {result.stderr}")
            
            # Check if there are changes to commit
            result = subprocess.run(['git', 'diff', '--cached', '--quiet'], 
                                  cwd=self.project_root)
            if result.returncode == 0:
                logger.info("No changes to commit")
                return True
            
            # Create commit message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = self.config['deployment']['commit_message_template'].format(
                timestamp=timestamp
            )
            
            # Commit changes
            cmd = ['git', 'commit', '-m', commit_message]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                logger.error(f"Commit failed: {result.stderr}")
                return False
            
            logger.info(f"Committed changes: {commit_message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stage and commit files: {e}")
            return False
    
    def push_to_github(self) -> bool:
        """Push changes to GitHub"""
        try:
            remote = self.config['repository'].get('remote', 'origin')
            branch = self.config['repository'].get('branch', 'main')
            
            cmd = ['git', 'push', remote, branch]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                logger.error(f"Push failed: {result.stderr}")
                return False
            
            logger.info(f"Pushed to {remote}/{branch}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to push to GitHub: {e}")
            return False
    
    def deploy(self) -> bool:
        """Execute full deployment"""
        logger.info("Starting GitHub deployment...")
        
        try:
            # Validate Git setup
            if not self.validate_git_repo():
                logger.error("Git validation failed")
                return False
            
            # Create necessary files
            self.create_requirements_txt()
            self.create_readme()
            self.create_github_workflows()
            self.create_github_templates()
            
            # Collect files to deploy
            files_dict = self.collect_project_files()
            
            # Log file counts
            total_files = sum(len(files) for files in files_dict.values())
            logger.info(f"Found {total_files} files to deploy:")
            for category, files in files_dict.items():
                if files:
                    logger.info(f"  {category}: {len(files)} files")
            
            # Validate Python files
            all_files = []
            for file_list in files_dict.values():
                all_files.extend(file_list)
            
            if not self.validate_python_files(all_files):
                logger.error("Python validation failed")
                return False
            
            # Stage and commit
            if not self.stage_and_commit_files(files_dict):
                logger.error("Failed to stage and commit files")
                return False
            
            # Push to GitHub
            if not self.push_to_github():
                logger.error("Failed to push to GitHub")
                return False
            
            logger.info("Deployment completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy UsenetSync to GitHub')
    parser.add_argument('--project-root', help='Project root directory')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--dry-run', action='store_true', help='Validate only, do not deploy')
    parser.add_argument('--force', action='store_true', help='Force deployment even with warnings')
    
    args = parser.parse_args()
    
    try:
        deployer = GitHubDeployer(args.project_root)
        
        if args.dry_run:
            logger.info("Dry run mode - validating only")
            files_dict = deployer.collect_project_files()
            all_files = []
            for file_list in files_dict.values():
                all_files.extend(file_list)
            
            success = deployer.validate_python_files(all_files)
            if success:
                logger.info("Validation passed - ready for deployment")
            else:
                logger.error("Validation failed")
                sys.exit(1)
        else:
            success = deployer.deploy()
            if not success:
                sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Deployment script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
